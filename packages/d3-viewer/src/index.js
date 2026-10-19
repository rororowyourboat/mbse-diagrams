import * as d3 from 'd3';
import './viewer.css';
import { resolvedModelRef } from './model-ref.js';

const SYMBOL_KEYWORDS = {
  'sysml.part-definition': 'part def',
  'sysml.item-definition': 'item def',
  'sysml.part-usage': 'part',
  'sysml.item-usage': 'item',
  'uml.class': '',
  'source.element': ''
};
const SVG_NS = 'http://www.w3.org/2000/svg';

function boundsFor(diagram) {
  const right = Math.max(600,
    ...diagram.nodes.map(node => node.bounds[0] + node.bounds[2]),
    ...diagram.edges.flatMap(edge => edge.points.map(point => point[0])));
  const bottom = Math.max(420,
    ...diagram.nodes.map(node => node.bounds[1] + node.bounds[3]),
    ...diagram.edges.flatMap(edge => edge.points.map(point => point[1])));
  return [right + 80, bottom + 80];
}

function newViewState() {
  return { hiddenNodes: [], hiddenKinds: [], positions: {}, zoom: null };
}

function loadState(key) {
  try {
    const value = JSON.parse(localStorage.getItem(key) || '{}');
    return value && typeof value === 'object' ? value : {};
  } catch {
    return {};
  }
}

function saveState(key, states, notify) {
  try { localStorage.setItem(key, JSON.stringify(states)); } catch { /* Storage may be disabled. */ }
  notify?.(structuredClone(states));
}

function el(name, attrs = {}) {
  const node = document.createElementNS(SVG_NS, name);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  return node;
}

function routedPoints(edge, nodeMap, state) {
  const source = nodeMap.get(edge.source);
  const target = nodeMap.get(edge.target);
  if (!source || !target) return [];
  const moved = Object.hasOwn(state.positions, edge.source) || Object.hasOwn(state.positions, edge.target);
  if (!moved) return edge.points;
  const a = source.bounds, b = target.bounds;
  const ac = [a[0] + a[2] / 2, a[1] + a[3] / 2];
  const bc = [b[0] + b[2] / 2, b[1] + b[3] / 2];
  const horizontal = Math.abs(bc[0] - ac[0]) >= Math.abs(bc[1] - ac[1]);
  if (edge.kind === 'composition' || !horizontal) {
    const start = [ac[0], a[1] + a[3]];
    const end = [bc[0], b[1]];
    const middle = (start[1] + end[1]) / 2;
    return [start, [start[0], middle], [end[0], middle], end];
  }
  const start = [a[0] + a[2], ac[1]];
  const end = [b[0], bc[1]];
  const middle = (start[0] + end[0]) / 2;
  return [start, [middle, start[1]], [middle, end[1]], end];
}

function edgeRoute(edge, nodeMap, state) {
  return d3.line()(routedPoints(edge, nodeMap, state));
}

function makeNode(group, diagram, node, position, onSelect) {
  const [x, y, width, height] = node.bounds;
  const keyword = SYMBOL_KEYWORDS[node.symbol] ?? '';
  group.attr('transform', `translate(${position.x},${position.y})`)
    .attr('class', `mbse-node ${node.symbol.replaceAll('.', '-')} ${node.modelRef ? '' : 'unbound'}`)
    .attr('tabindex', 0).attr('role', 'button')
    .attr('aria-label', `${keyword || 'element'} ${node.label}`)
    .attr('data-node-id', node.id);
  group.append('title').text(node.label);
  group.append('rect').attr('width', width).attr('height', height)
    .attr('rx', node.symbol.endsWith('-usage') ? 12 : 0);
  if (keyword) group.append('text').attr('class', 'mbse-keyword')
    .attr('x', width / 2).attr('y', 20).attr('text-anchor', 'middle').text(`«${keyword}»`);
  group.append('text').attr('class', 'mbse-name').attr('x', width / 2)
    .attr('y', keyword ? 42 : 24).attr('text-anchor', 'middle').text(node.label);
  let offset = keyword ? 56 : 40;
  for (const compartment of node.compartments || []) {
    group.append('path').attr('class', 'mbse-compartment-rule')
      .attr('d', `M0 ${offset} H${width}`);
    group.append('text').attr('class', 'mbse-compartment-title')
      .attr('x', 12).attr('y', offset + 20).text(compartment.name);
    compartment.lines.forEach((line, index) => group.append('text')
      .attr('class', 'mbse-compartment-line').attr('x', 12)
      .attr('y', offset + 40 + index * 20).text(line));
    offset += 28 + 20 * compartment.lines.length;
  }
  group.on('click', (event) => { if (!event.defaultPrevented) onSelect(node, diagram); })
    .on('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); onSelect(node, diagram); }
    });
}

/** Mount a reusable, multi-view MBSE diagram browser into a DOM element. */
export function mountSysmlViewer({
  element,
  diagrams,
  storageKey = 'mbse-diagrams-view-state',
  onSelectionChange,
  onStateChange
}) {
  if (!(element instanceof Element)) throw new TypeError('element must be a DOM element');
  if (!Array.isArray(diagrams) || diagrams.length === 0) throw new TypeError('diagrams must be a nonempty array');
  for (const diagram of diagrams) {
    if (diagram.formatVersion !== '0.1' || !Array.isArray(diagram.nodes) || !Array.isArray(diagram.edges)) {
      throw new TypeError(`unsupported diagram document: ${diagram.id || 'unknown'}`);
    }
  }

  const states = loadState(storageKey);
  for (const diagram of diagrams) {
    states[diagram.id] = { ...newViewState(), ...(states[diagram.id] || {}) };
    if (!Array.isArray(states[diagram.id].hiddenNodes)) states[diagram.id].hiddenNodes = [];
    if (!Array.isArray(states[diagram.id].hiddenKinds)) states[diagram.id].hiddenKinds = [];
    if (!states[diagram.id].positions || typeof states[diagram.id].positions !== 'object') states[diagram.id].positions = {};
  }
  let active = diagrams[0].id;
  let selectedKey = null;
  let selectedPresentation = null;
  const root = d3.select(element).classed('mbse-viewer', true);
  root.html('');
  const header = root.append('div').attr('class', 'mbse-viewer-bar');
  const viewNav = header.append('nav').attr('class', 'mbse-view-tabs').attr('aria-label', 'Diagram views');
  const tools = header.append('div').attr('class', 'mbse-view-tools');
  const exportButton = tools.append('button').attr('type', 'button').text('Export view settings');
  const importLabel = tools.append('label').attr('class', 'mbse-import-label').text('Import settings');
  const importInput = importLabel.append('input').attr('type', 'file').attr('accept', 'application/json');
  const resetButton = tools.append('button').attr('type', 'button').text('Reset view');
  const body = root.append('div').attr('class', 'mbse-viewer-body');
  const controlPanel = body.append('aside').attr('class', 'mbse-controls').attr('aria-label', 'View visibility controls');
  const canvas = body.append('div').attr('class', 'mbse-canvas');
  const canvasTools = canvas.append('div').attr('class', 'mbse-canvas-tools');
  const zoomOut = canvasTools.append('button').attr('type', 'button').attr('aria-label', 'Zoom out').text('−');
  const zoomFit = canvasTools.append('button').attr('type', 'button').text('Reset zoom');
  const zoomIn = canvasTools.append('button').attr('type', 'button').attr('aria-label', 'Zoom in').text('+');
  const svg = canvas.append('svg').attr('role', 'img').attr('aria-label', 'SysML diagram view');
  const graph = svg.append('g').attr('class', 'mbse-graph');
  const inspector = body.append('aside').attr('class', 'mbse-inspector').attr('aria-live', 'polite')
    .text('Select a model element or relationship to inspect its source binding.');
  const live = root.append('div').attr('class', 'mbse-live sr-only').attr('aria-live', 'polite');
  const byId = new Map(diagrams.map(diagram => [diagram.id, diagram]));
  const state = () => states[active];
  const view = () => byId.get(active);
  const notify = () => saveState(storageKey, states, onStateChange);

  function selectedKeyFor(node, diagram) {
    return resolvedModelRef(diagram, node.modelRef) || `${diagram.id}#${node.id}`;
  }

  function drawControls() {
    controlPanel.html('');
    const diagram = view(), current = state();
    controlPanel.append('h2').text('Visibility');
    const nodeSection = controlPanel.append('section');
    nodeSection.append('h3').text('Elements');
    const nodeLabels = nodeSection.selectAll('label').data(diagram.nodes, node => node.id).join('label')
      .attr('class', 'mbse-toggle');
    nodeLabels.append('input').attr('type', 'checkbox')
      .property('checked', node => !current.hiddenNodes.includes(node.id))
      .on('change', function (_event, node) {
        current.hiddenNodes = this.checked ? current.hiddenNodes.filter(id => id !== node.id)
          : [...new Set([...current.hiddenNodes, node.id])];
        draw();
      });
    nodeLabels.append('span').text(node => node.label);
    const kindSection = controlPanel.append('section');
    kindSection.append('h3').text('Relationships');
    const kinds = [...new Set(diagram.edges.map(edge => edge.kind))].sort();
    const kindLabels = kindSection.selectAll('label').data(kinds).join('label').attr('class', 'mbse-toggle');
    kindLabels.append('input').attr('type', 'checkbox')
      .property('checked', kind => !current.hiddenKinds.includes(kind))
      .on('change', function (_event, kind) {
        current.hiddenKinds = this.checked ? current.hiddenKinds.filter(item => item !== kind)
          : [...new Set([...current.hiddenKinds, kind])];
        draw();
      });
    kindLabels.append('span').text(kind => kind);
    const actions = controlPanel.append('div').attr('class', 'mbse-control-actions');
    actions.append('button').attr('type', 'button').text('Show all').on('click', () => {
      current.hiddenNodes = []; current.hiddenKinds = []; draw();
    });
    actions.append('button').attr('type', 'button').text('Hide all elements').on('click', () => {
      current.hiddenNodes = diagram.nodes.map(node => node.id); draw();
    });
  }

  function showSelection(item, diagram, kind) {
    selectedKey = kind === 'element' ? selectedKeyFor(item, diagram) : null;
    selectedPresentation = { item, diagram, kind };
    inspector.html('');
    inspector.append('div').attr('class', 'mbse-inspector-kind').text(kind);
    inspector.append('h2').text(item.label);
    if (kind === 'element') {
      inspector.append('p').text(`${item.symbol} · ${diagram.title}`);
      const ref = resolvedModelRef(diagram, item.modelRef);
      inspector.append('pre').text(ref ? `Source element\n${ref}` : 'Presentation has no source model reference.');
    } else {
      inspector.append('p').text(`${item.kind} · ${diagram.title}`);
    }
    onSelectionChange?.({ item, diagram, kind, modelKey: selectedKey });
    live.text(`Selected ${item.label} in ${diagram.title}`);
    updateSelectionStyles();
  }

  function updateSelectionStyles() {
    graph.selectAll('.mbse-node').classed('is-selected', node => selectedKey && selectedKeyFor(node, view()) === selectedKey);
  }

  function draw() {
    const diagram = view(), current = state();
    const [width, height] = boundsFor(diagram);
    svg.attr('viewBox', `0 0 ${width} ${height}`).attr('aria-label', diagram.title);
    graph.selectAll('*').remove();
    const defs = svg.append('defs');
    for (const [kind, path, refX, fill] of [
      ['connection', 'M0 0 L10 5 L0 10', 10, 'none'],
      ['specialization', 'M0 0 L10 5 L0 10 Z', 10, '#fff'],
      ['composition', 'M0 5 L7 0 L14 5 L7 10 Z', 0, '#26364a'],
      ['dependency', 'M0 0 L10 5 L0 10', 10, 'none']
    ]) {
      const marker = defs.append('marker').attr('id', `${diagram.id}-${kind}`).attr('viewBox', '-1 -1 16 12')
        .attr('refX', refX).attr('refY', 5).attr('markerWidth', 16).attr('markerHeight', 12)
        .attr('markerUnits', 'userSpaceOnUse').attr('orient', 'auto-start-reverse');
      marker.append('path').attr('d', path).attr('fill', fill).attr('stroke', '#26364a').attr('stroke-width', 1.5);
    }
    graph.append('rect').attr('class', 'mbse-background').attr('width', width).attr('height', height);
    const visible = diagram.nodes.filter(node => !current.hiddenNodes.includes(node.id));
    const nodeMap = new Map(visible.map(node => {
      const saved = current.positions[node.id];
      const [x, y, w, h] = node.bounds;
      return [node.id, { ...node, bounds: saved ? [saved.x, saved.y, w, h] : [x, y, w, h] }];
    }));
    const visibleEdges = diagram.edges.filter(edge => !current.hiddenKinds.includes(edge.kind)
      && nodeMap.has(edge.source) && nodeMap.has(edge.target));
    const edgeGroups = graph.append('g').attr('class', 'mbse-edges').selectAll('g')
      .data(visibleEdges, edge => edge.id).join('g').attr('class', edge => `mbse-edge kind-${edge.kind}`)
      .attr('data-edge-id', edge => edge.id).on('click', (_event, edge) => showSelection(edge, diagram, 'relationship'));
    edgeGroups.append('title').text(edge => `${edge.kind}: ${edge.label}`);
    edgeGroups.append('path').attr('d', edge => edgeRoute(edge, nodeMap, current))
      .attr('marker-end', edge => ({connection: `url(#${diagram.id}-connection)`, dependency: `url(#${diagram.id}-dependency)`, specialization: `url(#${diagram.id}-specialization)`}[edge.kind] || null))
      .attr('marker-start', edge => edge.kind === 'composition' ? `url(#${diagram.id}-composition)` : null);
    edgeGroups.append('text').attr('class', 'mbse-edge-label').attr('text-anchor', 'middle')
      .attr('x', edge => edge.points[Math.floor(edge.points.length / 2)][0])
      .attr('y', edge => edge.points[Math.floor(edge.points.length / 2)][1] - 8).text(edge => edge.label);

    const nodeGroups = graph.append('g').attr('class', 'mbse-nodes').selectAll('g')
      .data(visible, node => node.id).join('g');
    nodeGroups.each(function (node) {
      const [x, y] = nodeMap.get(node.id).bounds;
      makeNode(d3.select(this), diagram, node, { x, y }, (selectedNode, source) => showSelection(selectedNode, source, 'element'));
    });
    const drag = d3.drag().subject(function (_event, node) {
      const saved = current.positions[node.id];
      return saved || { x: node.bounds[0], y: node.bounds[1] };
    }).on('start', function (event) { event.sourceEvent.stopPropagation(); d3.select(this).raise(); })
      .on('drag', function (event, node) {
        current.positions[node.id] = { x: Math.max(0, event.x), y: Math.max(0, event.y) };
        d3.select(this).attr('transform', `translate(${current.positions[node.id].x},${current.positions[node.id].y})`);
        const liveMap = new Map(visible.map(item => {
          const saved = current.positions[item.id];
          const [x, y, w, h] = item.bounds;
          return [item.id, { ...item, bounds: saved ? [saved.x, saved.y, w, h] : [x, y, w, h] }];
        }));
        graph.selectAll('.mbse-edge').each(function (edge) {
          const points = routedPoints(edge, liveMap, current);
          const middle = points[Math.floor(points.length / 2)];
          const group = d3.select(this);
          group.select('path').attr('d', d3.line()(points));
          group.select('text').attr('x', middle[0]).attr('y', middle[1] - 8);
        });
        const right = Math.max(width, ...visible.map(item => {
          const saved = current.positions[item.id];
          return (saved?.x ?? item.bounds[0]) + item.bounds[2] + 80;
        }));
        const bottom = Math.max(height, ...visible.map(item => {
          const saved = current.positions[item.id];
          return (saved?.y ?? item.bounds[1]) + item.bounds[3] + 80;
        }));
        svg.attr('viewBox', `0 0 ${right} ${bottom}`);
      }).on('end', () => notify());
    nodeGroups.call(drag).on('dblclick', (event, node) => {
      event.preventDefault(); showSelection(node, diagram, 'element');
    });
    updateSelectionStyles();
    const zoom = d3.zoom().scaleExtent([0.25, 4]).on('zoom', event => graph.attr('transform', event.transform));
    svg.call(zoom);
    if (current.zoom) svg.call(zoom.transform, d3.zoomIdentity.translate(current.zoom.x, current.zoom.y).scale(current.zoom.k));
    zoom.on('end.mbse-save', () => {
      const transform = d3.zoomTransform(svg.node()); current.zoom = { x: transform.x, y: transform.y, k: transform.k }; notify();
    });
    zoomIn.on('click', () => svg.transition().call(zoom.scaleBy, 1.25));
    zoomOut.on('click', () => svg.transition().call(zoom.scaleBy, 0.8));
    zoomFit.on('click', () => svg.transition().call(zoom.transform, d3.zoomIdentity));
    drawControls();
    live.text(`${visible.length} of ${diagram.nodes.length} elements visible; ${visibleEdges.length} of ${diagram.edges.length} relationships visible.`);
    notify();
  }

  viewNav.selectAll('button').data(diagrams, diagram => diagram.id).join('button')
    .attr('type', 'button').attr('role', 'tab').attr('aria-selected', diagram => String(diagram.id === active))
    .text(diagram => diagram.title).on('click', (_event, diagram) => {
      active = diagram.id;
      viewNav.selectAll('button').attr('aria-selected', item => String(item.id === active));
      if (selectedPresentation?.kind === 'element') {
        const candidate = diagram.nodes.find(node => selectedKeyFor(node, diagram) === selectedKey);
        if (candidate) showSelection(candidate, diagram, 'element');
      }
      draw();
    });
  exportButton.on('click', () => {
    const blob = new Blob([JSON.stringify(states, null, 2)], { type: 'application/json' });
    const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = 'mbse-view-state.json'; link.click();
    setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  });
  importInput.on('change', async function () {
    const file = this.files?.[0]; if (!file) return;
    try {
      const incoming = JSON.parse(await file.text());
      for (const diagram of diagrams) if (incoming[diagram.id]) states[diagram.id] = { ...newViewState(), ...incoming[diagram.id] };
      draw();
    } catch { live.text('Could not read view settings JSON.'); }
    this.value = '';
  });
  resetButton.on('click', () => { states[active] = newViewState(); draw(); });
  draw();
  return {
    destroy() { root.html(''); root.classed('mbse-viewer', false); },
    getState() { return structuredClone(states); },
    setView(id) {
      if (!byId.has(id)) throw new RangeError(`unknown view ${id}`);
      active = id;
      viewNav.selectAll('button').attr('aria-selected', diagram => String(diagram.id === active));
      draw();
    }
  };
}

export { resolvedModelRef };
