# Supported formats and limits

Version 0.1 supports structural views only. Support means the explicit operations below, not full language or tool coverage.

| Format | Input | Output | Limits |
| --- | --- | --- | --- |
| Diagram JSON 0.1 | Yes | Yes | Flat nodes, compartments, explicit edge waypoints, source references; no ports/nesting |
| SVG | No | Yes | Original structural glyphs; standalone accessible SVG with model-reference metadata |
| HTML | No | Yes | Offline viewer with zoom, fit, selection and SVG download; no model editing |
| SysML v2 text | Bounded subset | No model write-back | One simple named package; part/item definitions; single simple specialization; typed part/item usage bodies |
| Native SysML views | OpenSysML resolved multi-file model | Diagram JSON, then SVG/HTML/draw.io | Explicit flat projection of tree/interconnection views; ports listed, nesting flattened; engine and source bindings retained |
| Source declaration cards | Native tree selection | SVG, HTML, draw.io | Neutral source-text cards, one member level, no relationship edges; not formal graphical notation or evaluated results |
| UML 2.5.1 | Class-view JSON profile | SVG, HTML, draw.io | Classes, text compartments, specialization, composition, association and dependency; no XMI or UML text parser |
| draw.io | Our exports | Native XML and shape library | Single page; compressed editor saves supported; native editable cells and labels; changed semantic endpoints/markers rejected |
| diagramatic | Explicit source checkout | Positioned JSON | Pinned grid layout; node-overlap check; engineering fields preserved |
| Mermaid | No | Explanatory flowchart | Labels/endpoints retained, relationship kind rendered as text; model refs, formal glyphs, compartments and layout lost |

Conversion commands require a receipt file. Draw.io ignores editor-only styling on import and reports that loss. Moved/resized nodes normalize edge endpoints relative to their previous bounds; interior waypoints remain explicit. This is a bounded adapter, not arbitrary draw.io interchange. New cells need explicit model mapping and are rejected in this version.

SysML extractor names are local textual references, not engine-assigned UUIDs. The source hash identifies input bytes. No engine validation, library resolution, general grammar parsing or model execution is provided. The example is an original small structural fixture inspired by the communication project, not a copy or complete export of its full theory model.

The separate [native-view adapter](native-views.md) does use explicit engine resolution and strict diagnostics. Its source-span references remain local to recorded file revisions. It requires `--flatten` for parents/ports and reports the lost visual notation. The strict small text extractor remains unchanged.

## Notation provenance

[Catalog](../notation/catalog.json) records original geometry and standards references. [SysML 2.0 Language](https://www.omg.org/spec/SysML/2.0/Language/PDF), formal/2026-03-02, section 8.2.3 supplies the notation basis; [UML 2.5.1](https://www.omg.org/spec/UML/2.5.1) supplies the UML profile basis. Current coverage is partial and has no conformance certification.

A named compartment's lines are display text, not parsed declarations. A relationship kind must be explicitly supplied in JSON or extracted from supported syntax. Composition places the diamond at `source` (owner); specialization points at `target` (general element). A SysML connection's open angle arrow indicates direction; it is not a flow arrow.

See [Mermaid flowchart syntax](https://mermaid.js.org/syntax/flowchart.html) and [draw.io file format](https://github.com/jgraph/drawio/wiki/File-Format) for target formats.
