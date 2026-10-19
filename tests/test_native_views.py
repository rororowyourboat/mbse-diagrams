"""Native selection is resolved by the engine, never inferred from source regexes."""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from mbse_diagrams.core import DiagramError, drawio, import_drawio, mermaid, svg, validate, viewer
from mbse_diagrams.opensysml import Engine, extract_view, project, read_sources

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / 'examples/native-views'
EXPECTED = {
    ('tokens', 'output', 'tokenEmbedding', 'input'),
    ('tokenEmbedding', 'output', 'embeddingAdd', 'left'),
    ('positionEmbedding', 'output', 'embeddingAdd', 'right'),
    ('embeddingAdd', 'output', 'attention', 'input'),
    ('embeddingAdd', 'output', 'attentionResidual', 'left'),
    ('attention', 'output', 'attentionResidual', 'right'),
    ('attentionResidual', 'output', 'mlp', 'input'),
    ('attentionResidual', 'output', 'mlpResidual', 'left'),
    ('mlp', 'output', 'mlpResidual', 'right'),
    ('mlpResidual', 'output', 'outputProjection', 'input'),
}


def endpoint_tuples(diagram):
    native = diagram['extensions']['mbse-diagrams.native-view']
    names = {n['id']: n['label'].split(' : ')[0] for n in diagram['nodes']}
    result = set()
    for edge in diagram['edges']:
        ports = native['endpoints'][edge['id']]
        result.add((names[edge['source']], native['ports'][ports['fromPort']]['name'],
                    names[edge['target']], native['ports'][ports['toPort']]['name']))
    return result


class NativeProjectionTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((EXAMPLE / 'resolved-view.json').read_text())
        self.texts = read_sources(EXAMPLE.glob('*.sysml'))

    def test_residual_connections_port_endpoints_and_source_bindings_survive(self):
        original = copy.deepcopy(self.data)
        diagram, report = project(self.data, self.texts, flatten=True)
        self.assertEqual(self.data, original)
        self.assertEqual(endpoint_tuples(diagram), EXPECTED)
        self.assertEqual(len(diagram['edges']), 10)
        self.assertEqual(report['counts']['listedPorts'], 19)
        self.assertEqual(len(diagram['nodes']), 10)  # enclosing definition plus nine components
        self.assertEqual(len(diagram['extensions']['mbse-diagrams.native-view']['elements']), 12)
        for source in diagram['sources']:
            self.assertEqual(source['revision'], 'sha256:' + hashlib.sha256(self.texts[source['uri']].encode()).hexdigest())
        self.assertTrue(all(e['modelRef']['element'].startswith('span:') for e in diagram['edges']))
        self.assertIn('port glyphs', ' '.join(report['lost']))
        self.assertEqual(report['resolvedView'], self.data)
        self.assertIn('native view, parent and port endpoint bindings', mermaid(diagram)[1]['lost'])

    def test_retained_snapshot_reproduces_the_projection(self):
        diagram, _ = project(self.data, self.texts, flatten=True)
        expected = json.loads((EXAMPLE / 'diagram.json').read_text())
        expected['extensions']['mbse-diagrams.native-view'].pop('engine')
        self.assertEqual(diagram, expected)

    def test_flattening_is_explicit_and_unknown_content_fails(self):
        with self.assertRaisesRegex(DiagramError, '--flatten'):
            project(self.data, self.texts)
        for mutation in (
            lambda d: d.update(kind='state'),
            lambda d: d.update(nodes=[]),
            lambda d: d.update(notices=['depth truncated']),
            lambda d: d['nodes'][3].update(kind='action'),
            lambda d: d['edges'][0].update(fromPort='missing'),
            lambda d: d['edges'][0].update(to='missing'),
            lambda d: d['edges'][0].update(kind='flow'),
            lambda d: d['nodes'][0]['origin'].update(file='unknown.sysml'),
        ):
            data = copy.deepcopy(self.data)
            mutation(data)
            with self.assertRaises(DiagramError):
                project(data, self.texts, flatten=True)

    def test_drawio_display_edits_preserve_all_native_bindings(self):
        import xml.etree.ElementTree as ET
        diagram, _ = project(self.data, self.texts, flatten=True)
        xml = ET.fromstring(drawio(diagram))
        node = xml.find(".//object[@id='node-1']")
        node.set('label', '«part»\nRenamed display')
        node.find('mxCell/mxGeometry').set('x', '80')
        restored, receipt = import_drawio(ET.tostring(xml, encoding='unicode'))
        self.assertEqual(restored['extensions'], diagram['extensions'])
        self.assertEqual([e['modelRef'] for e in restored['edges']], [e['modelRef'] for e in diagram['edges']])
        self.assertTrue(receipt['normalized'])
        self.assertEqual(restored['nodes'][1]['modelRef'], diagram['nodes'][1]['modelRef'])

    def test_source_cards_preserve_values_as_text_and_roundtrip(self):
        diagram = json.loads((EXAMPLE / 'baseline.json').read_text())
        self.assertEqual(diagram['notation'], 'source-declarations')
        self.assertEqual(diagram['nodes'][0]['symbol'], 'source.element')
        self.assertIn('attribute :>> modulus = 113;', diagram['nodes'][0]['compartments'][0]['lines'])
        self.assertEqual(import_drawio(drawio(diagram))[0], diagram)
        self.assertIn('not evaluated results', viewer(diagram))
        bad = copy.deepcopy(diagram)
        bad['nodes'][0]['symbol'] = 'uml.class'
        with self.assertRaisesRegex(DiagramError, 'profile mismatch'):
            validate(bad)

    def test_utf8_source_spans_preserve_spaces_inside_string_literals(self):
        declaration = '    attribute label : String = "a  λ b";'
        texts = {'p.sysml': 'part def P {\n' + declaration + '\n}\n'}
        origin = {'file': 'p.sysml', 'startLine': 1, 'startCol': 1, 'endLine': 3, 'endCol': 2}
        member = {'file': 'p.sysml', 'startLine': 2, 'startCol': 5,
                  'endLine': 2, 'endCol': len(declaration.encode('utf-8')) + 1}
        data = {'view': 'v', 'kind': 'tree', 'nodes': [
            {'id': 'n0', 'kind': 'part def', 'name': 'P', 'origin': origin},
            {'id': 'n1', 'kind': 'attribute', 'name': 'label', 'parent': 'n0', 'origin': member}], 'edges': []}
        diagram, _ = project(data, texts, flatten=True)
        self.assertEqual(diagram['nodes'][0]['compartments'][0]['lines'], [declaration.strip()])
        self.assertIn('xml:space="preserve"', svg(diagram))

    def test_layout_keeps_connector_segments_outside_unrelated_boxes(self):
        diagram, _ = project(self.data, self.texts, flatten=True)
        for edge in diagram['edges']:
            for a, b in zip(edge['points'], edge['points'][1:]):
                self.assertTrue(a[0] == b[0] or a[1] == b[1])
                for node in diagram['nodes']:
                    if node['id'] in (edge['source'], edge['target']):
                        continue
                    x, y, w, h = node['bounds']
                    crosses = (a[0] == b[0] and x < a[0] < x + w and max(min(a[1], b[1]), y) < min(max(a[1], b[1]), y + h)) or (a[1] == b[1] and y < a[1] < y + h and max(min(a[0], b[0]), x) < min(max(a[0], b[0]), x + w))
                    self.assertFalse(crosses, (edge['id'], node['id']))

    def test_missing_capability_prevents_parsing(self):
        with patch('mbse_diagrams.opensysml.Engine') as engine:
            session = engine.return_value.__enter__.return_value
            session.call.return_value = {'capabilities': ['parse_sources']}
            with self.assertRaisesRegex(DiagramError, 'lacks'):
                extract_view(EXAMPLE.glob('*.sysml'), 'NativeViews::architecture', 'unused')
            self.assertEqual(session.call.call_count, 1)

    def test_input_freeze_and_cli_output_alias_protection(self):
        with self.assertRaisesRegex(DiagramError, 'distinct'):
            read_sources([EXAMPLE / 'types.sysml', EXAMPLE / 'types.sysml'])
        from mbse_diagrams.__main__ import main
        with patch('sys.stderr', new=io.StringIO()), self.assertRaises(SystemExit) as failure:
            main(['view', str(EXAMPLE / 'types.sysml'), '--view', 'X', '--engine', __file__,
                  '--report', str(EXAMPLE / 'types.sysml')])
        self.assertEqual(failure.exception.code, 2)


class EngineProtocolTests(unittest.TestCase):
    def fake_process(self, body, declared=None):
        raw = json.dumps(body, ensure_ascii=False).encode()
        process = MagicMock()
        process.stdin = io.BytesIO()
        process.stdout = io.BytesIO(f'Content-Length: {len(raw) if declared is None else declared}\r\n\r\n'.encode() + raw)
        return process

    def test_utf8_byte_framing_and_embedded_library_environment(self):
        process = self.fake_process({'jsonrpc': '2.0', 'id': 1, 'result': {'value': 'λ'}})
        with patch('subprocess.Popen', return_value=process) as launch:
            with Engine(__file__) as engine:
                self.assertEqual(engine.call('GetServerInfo', {'name': 'λ'})['value'], 'λ')
                header, body = process.stdin.getvalue().split(b'\r\n\r\n', 1)
                self.assertIn(str(len(body)).encode(), header)
                self.assertEqual(json.loads(body)['params']['name'], 'λ')
            self.assertNotIn('OPENSYSML_LIBRARY_PATH', launch.call_args.kwargs['env'])
            process.wait.assert_called()

    def test_wrong_identity_truncation_and_rpc_errors_fail(self):
        for body, declared in [
            ({'jsonrpc': '2.0', 'id': 2, 'result': {}}, None),
            ({'jsonrpc': '2.0', 'id': 1, 'result': {}}, 1000),
            ({'jsonrpc': '2.0', 'id': 1, 'error': {'code': 5, 'message': 'view missing'}}, None),
        ]:
            with patch('subprocess.Popen', return_value=self.fake_process(body, declared)):
                with Engine(__file__) as engine, self.assertRaises(DiagramError):
                    engine.call('RenderView', {})

    def test_timeout_reaps_a_hung_child(self):
        process = self.fake_process({})
        process.wait.side_effect = [subprocess.TimeoutExpired('engine', 2), None]
        with patch('subprocess.Popen', return_value=process), patch.object(Engine, '_read'):
            with self.assertRaisesRegex(DiagramError, 'timed out'):
                with Engine(__file__, timeout=0.01) as engine:
                    engine.call('GetServerInfo', {})
        process.terminate.assert_called_once()


@unittest.skipUnless(os.environ.get('OPENSYSML_ENGINE'), 'requires explicit trusted OPENSYSML_ENGINE executable')
class NativeEngineIntegrationTests(unittest.TestCase):
    def extract(self, name, **kwargs):
        return extract_view(EXAMPLE.glob('*.sysml'), 'NativeViews::' + name,
                            os.environ['OPENSYSML_ENGINE'], flatten=True, **kwargs)

    def test_real_multifile_view_inherited_rendering_and_both_residual_paths(self):
        before = {p: p.read_bytes() for p in EXAMPLE.glob('*.sysml')}
        diagram, report = self.extract('architecture')
        self.assertEqual(endpoint_tuples(diagram), EXPECTED)
        self.assertEqual(report['counts']['relationships'], 10)
        self.assertEqual(report['engine']['standardLibrary'], 'embedded in the selected executable')
        self.assertEqual({p: p.read_bytes() for p in before}, before)
        self.assertEqual(import_drawio(drawio(diagram))[0], diagram)
        self.assertIn('source reference', viewer(diagram))
        self.assertIn('source-', svg(diagram))

    def test_real_filtered_selection_does_not_invent_edges(self):
        diagram, report = self.extract('components')
        self.assertEqual(len(diagram['nodes']), 9)
        self.assertEqual(diagram['edges'], [])
        self.assertEqual(report['counts']['relationships'], 0)

    def test_real_baseline_and_analysis_declaration_views(self):
        for name, count in [('baseline', 1), ('analyses', 3)]:
            diagram, _ = self.extract(name, presentation='declarations')
            self.assertEqual(len(diagram['nodes']), count)
            self.assertEqual(import_drawio(drawio(diagram))[0], diagram)
        self.assertIn('in attribute checkpointURI : String;', diagram['nodes'][0]['compartments'][0]['lines'])

    def test_empty_missing_views_and_invalid_sources_fail_before_output(self):
        for name in ('empty', 'notDeclared'):
            with self.assertRaises(DiagramError):
                self.extract(name)
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'bad.sysml'
            source.write_text('package Bad { part def Missing {')
            with self.assertRaisesRegex(DiagramError, 'validation'):
                extract_view([source], 'Bad::v', os.environ['OPENSYSML_ENGINE'])


if __name__ == '__main__':
    unittest.main()
