# MBSE Diagrams D3 viewer

An interactive browser viewer for one or more MBSE Diagrams JSON 0.1 documents. It provides model-view tabs, element and relationship-kind visibility controls, pan/zoom, draggable presentation nodes, selection, and separate import/export of view state.

The input diagram documents remain unchanged. Node positions, visibility, and camera state are stored per view in browser storage and can be exported to JSON for review or version control. Selection across views uses each element's source URI and source element reference where available.

## Run the example

From this directory:

```bash
npm install
npm run dev
```

Open the local address printed by Vite. The example uses retained JSON views from `../../examples/native-views/multiview/`.

## Use the package

Install the package in a JavaScript host and provide an HTML mount point plus one or more validated diagram documents:

```js
import { mountSysmlViewer } from '@mbse-diagrams/d3-viewer';
import '@mbse-diagrams/d3-viewer/style.css';

const viewer = mountSysmlViewer({
  element: document.querySelector('#viewer'),
  diagrams: [architectureDiagram, analysisDiagram],
  storageKey: 'my-study-view-state',
  onSelectionChange: ({ item, diagram, kind, modelKey }) => {
    // Connect this to the host application's inspector or model browser.
  },
  onStateChange: state => {
    // Optional host persistence; the viewer also saves locally in the browser.
  }
});
```

The returned handle provides `getState()`, `setView(id)`, and `destroy()`. View state is presentation data; it does not update SysML or diagram semantics.

## Current limits

This is an experimental first version. It renders the current flat JSON contract; nested ownership, graphical SysML ports/anchors, edge waypoint editing, shared collaboration, and automatic layout are not included. When a node is dragged, incident edges are rerouted with a simple orthogonal route. The host can add ELK.js layout separately in a later iteration.

Dependency license details are in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## Checks

```bash
npm test
npm run build
```
