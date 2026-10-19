# Experimental diagram contract

Draft version: 0.1. This is an experimental implemented structural subset, not a published standard. See [JSON Schema](../schemas/diagram.schema.json) and [supported operations](support.md).

| Field | Meaning |
| --- | --- |
| formatVersion | Version of this interchange contract |
| id | Stable diagram identifier |
| notation | `sysml-2.0-structural` or `uml-2.5.1-class` |
| sources | Source URI, revision and model identity |
| nodes | Presentation ID, model reference, symbol type, bounds, named text compartments and label |
| edges | Presentation ID, model reference, relationship kind, source/target node IDs, explicit point list and label |
| extensions | Namespaced adapter data that can survive a round trip |

Geometry uses diagram coordinates in SVG user units with x increasing rightward and y downward. Bounds and waypoint positions must be finite numbers. Rendering uses Arial or the browser’s sans-serif fallback, 14-unit text and 20-unit compartment line spacing. Bounds are `[x, y, width, height]`; edges include source and target points. Text metrics can vary by host; inspect exports.

References must resolve within the document. Nesting and ports are deferred and rejected rather than ignored. IDs must be unique across nodes and edges. Unknown notation or relationship kinds must yield diagnostics rather than a guessed glyph.

The `source-declarations` profile uses only `source.element` cards and no relationship edges. It displays selected source declarations rather than claiming formal graphical glyphs. The [native view adapter](native-views.md) can also explicitly flatten engine-selected parents and ports into the existing structural profile: its namespaced extension retains source and endpoint bindings, while its receipt reports the lost nested/port notation. Neither operation adds native ports or nesting fields to JSON 0.1.

Adapters must report preserved, normalized, unsupported and lost fields. Unbound nodes are allowed in JSON; new editor-created cells are rejected until mapped explicitly. Deleting a presentation does not delete its source model element.

The first version supports a documented subset of draw.io. Arbitrary draw.io diagrams are outside the initial round-trip promise.
