import architecture from '../../../examples/native-views/multiview/NativeViews-architecture.json';
import byRole from '../../../examples/native-views/multiview/ResearchPerspectives-byRole.json';
import { mountSysmlViewer } from '../src/index.js';
import './page.css';

const viewer = mountSysmlViewer({
  element: document.querySelector('#viewer'),
  diagrams: [architecture, byRole],
  storageKey: 'mbse-diagrams-demo-view-state',
  onSelectionChange: ({ item, kind }) => {
    document.title = `${kind}: ${item.label} · MBSE Diagrams`;
  }
});

if (new URLSearchParams(location.search).has('smoke')) {
  const report = document.createElement('output');
  report.id = 'smoke-results';
  document.body.append(report);
  setTimeout(async () => { try {
    const originalX = architecture.nodes[0].bounds[0];
    const svg = document.querySelector('.mbse-canvas svg');
    const node = document.querySelector('.mbse-node');
    const point = svg.createSVGPoint();
    point.x = 12; point.y = 12;
    const start = point.matrixTransform(node.getScreenCTM());
    node.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, view: window, button: 0, buttons: 1, clientX: start.x, clientY: start.y }));
    window.dispatchEvent(new MouseEvent('mousemove', { bubbles: true, view: window, button: 0, buttons: 1, clientX: start.x + 28, clientY: start.y + 18 }));
    window.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, view: window, button: 0, buttons: 0, clientX: start.x + 28, clientY: start.y + 18 }));
    const moved = viewer.getState()[architecture.id].positions[architecture.nodes[0].id];
    if (!moved || moved.x <= originalX) throw new Error('drag did not persist a changed position');
    await new Promise(resolve => setTimeout(resolve, 100));

    const firstToggle = document.querySelector('.mbse-controls input[type=checkbox]');
    firstToggle.checked = false;
    firstToggle.dispatchEvent(new Event('change', { bubbles: true }));
    if (!viewer.getState()[architecture.id].hiddenNodes.includes(architecture.nodes[0].id)) throw new Error('element visibility was not saved');
    const selectable = document.querySelector(`[data-node-id="${architecture.nodes[1].id}"]`);
    selectable.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    document.querySelector('.mbse-view-tabs button:nth-child(2)').click();
    if (!document.querySelector('.mbse-node.is-selected')) throw new Error(`source-bound selection did not carry across views (${document.querySelector('.mbse-inspector').textContent})`);
    viewer.setView(architecture.id);
    if (document.querySelectorAll('.mbse-node').length !== architecture.nodes.length - 1) throw new Error('view switching lost visibility state');
    if (!viewer.getState()[architecture.id].positions[architecture.nodes[0].id]) throw new Error('view switching lost the moved position');
    if (architecture.nodes[0].bounds[0] !== originalX) throw new Error('viewer changed source diagram geometry');
    report.textContent = 'PASS: render, drag, visibility toggle, view switching, and source immutability';
  } catch (error) {
    report.textContent = `FAIL: ${error.message}`;
  } }, 100);
}
