"""Optional native-view adapter using OpenSysML's structured service over pipes.

No SysML parsing or engine installation happens here. The selected executable
resolves all documents together; this adapter projects a bounded rendering.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import queue
import subprocess
import threading

from .core import DiagramError, require, validate


class Engine:
    """One private, sequential JSON-RPC session with bounded frames and waits."""

    def __init__(self, executable, timeout=30):
        self.path = Path(executable).resolve(strict=True)
        require(math.isfinite(timeout) and timeout > 0, 'timeout must be positive and finite')
        self.timeout = timeout
        self.process = None
        self.answers = queue.Queue()
        self.sequence = 0

    def __enter__(self):
        environment = dict(os.environ)
        environment.pop('OPENSYSML_LIBRARY_PATH', None)
        self.process = subprocess.Popen(
            [str(self.path), '-transport', 'stdio', '-log-level', 'error'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            env=environment,
        )
        threading.Thread(target=self._read, daemon=True).start()
        return self

    def _read(self):
        try:
            while True:
                headers = {}
                total = 0
                while True:
                    line = self.process.stdout.readline(8193)
                    require(bool(line), 'engine closed its output; check the executable and stdio support')
                    total += len(line)
                    require(total <= 8192, 'engine response headers exceed 8 KiB')
                    if line == b'\r\n':
                        break
                    key, value = line.decode('ascii').split(':', 1)
                    require(key.lower() not in headers, 'duplicate engine response header')
                    headers[key.lower()] = value.strip()
                length = int(headers.get('content-length', '-1'))
                require(0 <= length <= 64 * 1024 * 1024, 'invalid or excessive engine response length')
                body = self.process.stdout.read(length)
                require(len(body) == length, 'truncated engine response')
                self.answers.put(json.loads(body))
        except (OSError, ValueError, TypeError) as exc:
            self.answers.put(DiagramError(str(exc)))

    def call(self, method, params):
        self.sequence += 1
        message = {'jsonrpc': '2.0', 'id': self.sequence, 'method': method, 'params': params}
        body = json.dumps(message, ensure_ascii=False).encode('utf-8')
        require(len(body) <= 64 * 1024 * 1024, 'engine request exceeds 64 MiB')
        self.process.stdin.write(
            f'Content-Length: {len(body)}\r\nContent-Type: application/json\r\n\r\n'.encode('ascii') + body)
        self.process.stdin.flush()
        try:
            response = self.answers.get(timeout=self.timeout)
        except queue.Empty as exc:
            raise DiagramError(f'engine {method} timed out after {self.timeout:g}s') from exc
        if isinstance(response, Exception):
            raise response
        require(isinstance(response, dict) and response.get('jsonrpc') == '2.0'
                and response.get('id') == self.sequence, 'unexpected engine response identity')
        require(not response.get('error'), f"engine {method} failed: {response.get('error')}")
        require(isinstance(response.get('result'), dict), 'engine result must be an object')
        return response['result']

    def __exit__(self, *_):
        try:
            self.process.stdin.close()
        except OSError:
            pass
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        self.process.stdout.close()


def read_sources(paths):
    """Freeze bytes once; portable document names are relative to a common root."""
    paths = [Path(p).resolve(strict=True) for p in paths]
    require(bool(paths) and len(set(paths)) == len(paths), 'need distinct source files')
    require(all(p.is_file() and p.suffix in ('.sysml', '.kerml') for p in paths),
            'view inputs must be .sysml or .kerml files')
    root = Path(os.path.commonpath([str(p.parent) for p in paths]))
    return {p.relative_to(root).as_posix(): p.read_bytes().decode('utf-8') for p in sorted(paths)}


def _binding(origin, source_ids):
    require(isinstance(origin, dict) and origin.get('file') in source_ids,
            'rendered element has no location in the supplied sources')
    coordinates = [origin.get(k) for k in ('startLine', 'startCol', 'endLine', 'endCol')]
    require(all(isinstance(v, int) and not isinstance(v, bool) and v > 0 for v in coordinates),
            'rendered element has an invalid source span')
    return {'source': source_ids[origin['file']],
            'element': 'span:' + ':'.join(str(v) for v in coordinates)}


def _declaration(origin, texts):
    # OpenSysML spans use one-based UTF-8 byte columns and an exclusive end.
    lines = texts[origin['file']].encode('utf-8').splitlines(keepends=True)
    start, end = origin['startLine'] - 1, origin['endLine'] - 1
    require(0 <= start <= end < len(lines), 'source span is outside its document')
    fragment = b''.join(lines[start:end + 1])
    end_offset = sum(len(line) for line in lines[start:end]) + origin['endCol'] - 1
    require(origin['startCol'] - 1 <= end_offset <= len(fragment), 'source columns are outside their lines')
    return fragment[origin['startCol'] - 1:end_offset].decode('utf-8').strip()


def project(data, texts, *, flatten=False, presentation='structure'):
    """Project resolved selection, retaining all selected elements in a receipt map.

    Structure uses existing structural symbols. Declarations uses neutral source
    cards, which deliberately make no formal graphical-notation claim.
    """
    require(presentation in ('structure', 'declarations'), 'unknown view presentation')
    require(isinstance(data, dict) and data.get('kind') in ('tree', 'interconnection'),
            'only tree and interconnection renderings are supported')
    require(not data.get('notices'), f"engine reported incomplete rendering: {data.get('notices')}")
    require(not data.get('notes'), 'rendering notes need an explicit supported projection')
    native = data.get('nodes', [])
    require(isinstance(native, list) and bool(native), 'view selection is empty')
    require(all(isinstance(n, dict) for n in native), 'engine nodes must be objects')
    require(isinstance(data.get('edges', []), list)
            and all(isinstance(e, dict) for e in data.get('edges', [])), 'engine edges must be objects')
    require(not any(n.get('standIn') for n in native), 'stand-in elements need an explicit supported projection')
    ids = [n['id'] for n in native]
    require(len(ids) == len(set(ids)), 'duplicate engine node IDs')
    by_id = {n['id']: n for n in native}
    require(all(not n.get('parent') or n['parent'] in by_id for n in native), 'unknown engine parent')
    require(flatten or not any(n.get('parent') or n.get('ports') for n in native),
            'nested elements or ports require --flatten; the receipt records presentation loss')
    sources = [{'id': f'source-{i}', 'uri': name,
                'revision': 'sha256:' + hashlib.sha256(text.encode('utf-8')).hexdigest()}
               for i, (name, text) in enumerate(sorted(texts.items()))]
    source_ids = {s['uri']: s['id'] for s in sources}
    bindings = {n['id']: {'modelRef': _binding(n.get('origin'), source_ids),
                          'kind': n['kind'], 'name': n['name'], 'parent': n.get('parent', ''),
                          **{k: n[k] for k in ('type', 'nameSynthesized', 'detail', 'text') if k in n}}
                for n in native}
    symbols = {'part def': 'sysml.part-definition', 'part': 'sysml.part-usage',
               'item def': 'sysml.item-definition', 'item': 'sysml.item-usage'}
    if presentation == 'declarations':
        require(data['kind'] == 'tree' and not data.get('edges'),
                'declaration cards require a tree with no relationship edges')
        shown = [n for n in native if not n.get('parent')]
        require(all(not n.get('parent') or not by_id[n['parent']].get('parent') for n in native),
                'declaration cards currently support one level of selected members')
    else:
        shown = [n for n in native if n['kind'] != 'attribute']
        require(all(n['kind'] in symbols for n in shown),
                'unsupported structural element kind; use declaration cards for a source listing')
        require(all(n['kind'] != 'attribute' or n.get('parent') in {s['id'] for s in shown}
                    for n in native), 'standalone attributes need a declaration-card view')
    node_ids = {n['id']: f'node-{i}' for i, n in enumerate(shown)}
    nodes, port_map = [], {}
    for native_node in shown:
        node_id = node_ids[native_node['id']]
        label = native_node['name']
        if native_node.get('type'):
            label += ' : ' + native_node['type']
        compartments = []
        members = [n for n in native if n.get('parent') == native_node['id']
                   and (presentation == 'declarations' or n['kind'] == 'attribute')]
        if presentation == 'declarations':
            label = native_node['kind'] + ' ' + label
        if members:
            compartments.append({'name': 'source declarations',
                                 'lines': [line for n in members
                                           for line in _declaration(n['origin'], texts).splitlines()]})
        ports = native_node.get('ports', [])
        if ports:
            for port in ports:
                require(port['id'] not in port_map, 'duplicate engine port ID')
                port_map[port['id']] = {'node': node_id, 'name': port['name'],
                                        'type': port.get('type', ''), 'direction': port.get('direction', '')}
            compartments.append({'name': 'ports (listed)', 'lines': [p['name'] +
                                 (' : ' + p['type'] if p.get('type') else '') for p in ports]})
        longest = max([len(label)] + [len(line) for c in compartments for line in c['lines']])
        nodes.append({'id': node_id, 'label': label,
                      'symbol': 'source.element' if presentation == 'declarations' else symbols[native_node['kind']],
                      'bounds': [0, 0, max(240, longest * 8 + 40),
                                 max(80, 56 + sum(28 + 20 * len(c['lines']) for c in compartments))],
                      'compartments': compartments, 'modelRef': bindings[native_node['id']]['modelRef']})
        bindings[native_node['id']]['presentation'] = node_id
    edges, endpoints = [], {}
    for i, edge in enumerate(data.get('edges', [])):
        require(edge['kind'] in ('connection', 'composition', 'specialization'),
                f"unsupported structural relationship: {edge['kind']}")
        require(edge['from'] in node_ids and edge['to'] in node_ids,
                'relationship endpoint was not projected; refusing to drop an edge')
        a, b = node_ids[edge['from']], node_ids[edge['to']]
        endpoint = {}
        for field, owner in (('fromPort', a), ('toPort', b)):
            if edge.get(field):
                require(edge[field] in port_map and port_map[edge[field]]['node'] == owner,
                        'unknown port or wrong endpoint owner')
                endpoint[field] = edge[field]
        edge_id = f'edge-{i}'
        label = edge.get('label', '')
        if endpoint:
            label = ' / '.join(port_map[endpoint[f]]['name'] if f in endpoint else ''
                               for f in ('fromPort', 'toPort'))
        edges.append({'id': edge_id, 'label': label, 'kind': edge['kind'],
                      'source': a, 'target': b, 'points': [[0, 0], [0, 0]],
                      'modelRef': _binding(edge.get('origin'), source_ids)})
        endpoints[edge_id] = endpoint
    _arrange(nodes, edges)
    normalized = ['source spans are local references within the recorded source byte hashes',
                  'deterministic diagram layout replaces engine geometry',
                  'selected attributes/members are source text, not evaluated values']
    lost = []
    if any(n.get('parent') for n in native):
        lost.append('nested visual containment; engine parent bindings remain in metadata')
    if port_map:
        lost.append('port glyphs and native anchors; port identities and edge endpoints remain in metadata')
    if (any(n.get('geometry') or n.get('style') for n in native) or data.get('canvas')
            or any(e.get('route') or e.get('style') for e in data.get('edges', []))):
        lost.append('engine layout, canvas and styling')
    diagram = {'formatVersion': '0.1', 'id': 'view-' + hashlib.sha256(data['view'].encode()).hexdigest()[:12],
               'title': data['view'], 'notation': 'source-declarations' if presentation == 'declarations'
               else 'sysml-2.0-structural', 'sources': sources, 'nodes': nodes, 'edges': edges,
               'extensions': {'mbse-diagrams.native-view': {'view': data['view'], 'kind': data['kind'],
                              'stated': data.get('stated', ''), 'elements': bindings,
                              'ports': port_map, 'endpoints': endpoints}}}
    validate(diagram)
    report = {'scope': 'resolved native tree/interconnection view projected to flat diagram JSON 0.1',
              'view': data['view'], 'presentation': presentation, 'sources': sources,
              'resolvedView': data,
              'preserved': ['selected element source bindings', 'connection endpoint identities',
                            'engine port identities/types/directions', 'selected member declarations'],
              'normalized': normalized, 'lost': lost, 'unsupported': [],
              'counts': {'selectedElements': len(native), 'drawnNodes': len(nodes),
                         'listedPorts': len(port_map), 'relationships': len(edges)}}
    diagram['extensions']['mbse-diagrams.native-view']['projection'] = {
        'presentation': presentation, 'lost': lost, 'counts': report['counts']}
    return diagram, report


def _arrange(nodes, edges):
    """Order acyclic endpoints in rows; cyclic graphs keep source order.

    This uses endpoint order for presentation, not to infer tensor/data flow.
    Bypasses stay outside node rows. Geometry remains editable in draw.io.
    """
    require(bool(nodes), 'projection has no drawable elements')
    by_id = {n['id']: n for n in nodes}
    incoming = {key: [] for key in by_id}
    outgoing = {key: [] for key in by_id}
    for edge in edges:
        incoming[edge['target']].append(edge)
        outgoing[edge['source']].append(edge)
    connected = {key for key in by_id if incoming[key] or outgoing[key]}
    remaining = {key: len(incoming[key]) for key in connected}
    ranks = {key: 0 for key in connected}
    ready = [key for key in by_id if key in connected and not remaining[key]]
    visited = []
    for key in ready:
        visited.append(key)
        for edge in outgoing[key]:
            target = edge['target']
            ranks[target] = max(ranks[target], ranks[key] + 1)
            remaining[target] -= 1
            if remaining[target] == 0:
                ready.append(target)
    if len(visited) != len(connected):
        ranks = {key: i for i, key in enumerate(by_id) if key in connected}
    detached = [n for n in nodes if n['id'] not in connected]
    rows = [detached[i:i + 3] for i in range(0, len(detached), 3)]
    for rank in sorted(set(ranks.values())):
        rows.append([n for n in nodes if ranks.get(n['id']) == rank])
    content_width = max(sum(n['bounds'][2] for n in row) + 120 * (len(row) - 1) for row in rows)
    y, row_bottom = 40, {}
    for row in rows:
        row_width = sum(n['bounds'][2] for n in row) + 120 * (len(row) - 1)
        x = 40 + (content_width - row_width) / 2
        bottom = y + max(n['bounds'][3] for n in row)
        for node in row:
            node['bounds'][:2] = [x, y]
            row_bottom[node['id']] = bottom
            x += node['bounds'][2] + 120
        y = bottom + 100
    bounds = {n['id']: n['bounds'] for n in nodes}
    bypasses = 0
    for i, edge in enumerate(edges):
        x, y, w, h = bounds[edge['source']]
        tx, ty, tw, th = bounds[edge['target']]
        out_index = outgoing[edge['source']].index(edge)
        in_index = incoming[edge['target']].index(edge)
        sx = x + w * (out_index + 1) / (len(outgoing[edge['source']]) + 1)
        dx = tx + tw * (in_index + 1) / (len(incoming[edge['target']]) + 1)
        start_y = row_bottom[edge['source']] + 28 + 12 * out_index
        end_y = ty - 28 - 12 * in_index
        if ranks[edge['target']] == ranks[edge['source']] + 1:
            edge['points'] = [[sx, y + h], [sx, start_y], [dx, start_y], [dx, ty]]
        else:
            lane = 40 + content_width + 100 + 80 * bypasses
            bypasses += 1
            edge['points'] = [[sx, y + h], [sx, start_y], [lane, start_y],
                              [lane, (start_y + end_y) / 2], [lane, end_y], [dx, end_y], [dx, ty]]


def extract_view(paths, view, executable, *, flatten=False, presentation='structure', timeout=30):
    result = extract_views(paths, [view], executable, flatten=flatten,
                           presentation=presentation, timeout=timeout)
    return result[view]


def extract_views(paths, views, executable, *, flatten=False, presentation='auto', timeout=30):
    """Resolve one SysML model once and project each declared view in order.

    ``auto`` maps native interconnection views to structural notation and native
    tree views to neutral declaration cards. Callers can choose one explicit
    presentation for every requested view when needed.
    """
    require(isinstance(views, (list, tuple)) and bool(views), 'name at least one declared SysML view')
    require(all(isinstance(view, str) and bool(view.strip()) and not view.startswith('#')
                for view in views), 'name declared SysML views, not pseudo-views')
    require(len(views) == len(set(views)), 'duplicate SysML view name')
    require(presentation in ('auto', 'structure', 'declarations'), 'unknown view presentation')
    texts = read_sources(paths)
    results = {}
    with Engine(executable, timeout) as engine:
        info = engine.call('GetServerInfo', {})
        require({'parse_sources', 'render_view', 'strict_conformance'} <= set(info.get('capabilities', [])),
                'engine lacks parse_sources, render_view or strict_conformance capability')
        parsed = engine.call('ParseSources', {'documents': [
            {'name': name, 'content': text, 'language': 'kerml' if name.endswith('.kerml') else 'sysml'}
            for name, text in texts.items()], 'strictConformance': True})
        require(not parsed.get('error'), f"engine parse failed: {parsed.get('error')}")
        errors = [d for d in parsed.get('diagnostics', []) if d.get('severity') == 'error']
        require(not errors, 'engine validation failed: ' + '; '.join(d.get('message', '') for d in errors))
        require(bool(parsed.get('modelHash')), 'engine did not return a model identity')
        engine_identity = {'name': 'OpenSysML', 'version': info.get('version', ''),
                           'binarySHA256': hashlib.sha256(engine.path.read_bytes()).hexdigest(),
                           'transport': 'stdio JSON-RPC (upstream evaluation prototype)',
                           'standardLibrary': 'embedded in the selected executable',
                           'modelHash': parsed['modelHash']}
        validation = {'strictConformance': True, 'diagnostics': parsed.get('diagnostics', [])}
        for view in views:
            data = engine.call('RenderView', {'modelHash': parsed['modelHash'], 'view': view, 'ports': 'full'})
            require(data.get('view') == view, 'engine returned a different view identity')
            mode = presentation
            if mode == 'auto':
                mode = 'structure' if data.get('kind') == 'interconnection' else 'declarations'
            diagram, report = project(data, texts, flatten=flatten, presentation=mode)
            report['engine'] = engine_identity
            report['languageValidation'] = validation
            diagram['extensions']['mbse-diagrams.native-view']['engine'] = engine_identity
            results[view] = (diagram, report)
    return results
