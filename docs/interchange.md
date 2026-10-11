# Experimental diagram contract

Draft version: 0.1. This is a design contract, not a published standard or implemented schema.

| Field | Meaning |
| --- | --- |
| formatVersion | Version of this interchange contract |
| id | Stable diagram identifier |
| notation | Profile identifier and version |
| sources | Source URI, revision and model identity |
| nodes | Presentation ID, model reference, symbol type, parent, bounds, compartments and labels |
| ports | Presentation ID, owner node, model reference, side and position |
| edges | Presentation ID, model reference, relationship kind, source/target presentation IDs, waypoints and labels |
| extensions | Namespaced adapter data that can survive a round trip |

Geometry uses diagram coordinates in SVG user units with x increasing rightward and y downward. Bounds and waypoint positions must be finite numbers. A draft should explicitly choose text metrics and scaling conventions before freezing its schema.

References must resolve within the document. Parent nesting must be acyclic. IDs must be unique across nodes, ports and edges. Unknown notation or relationship kinds must yield diagnostics rather than a guessed glyph.

Adapters must report preserved, normalized, unsupported and lost fields. An editor-created element lacking a model reference remains explicitly unbound. Deleting a presentation does not delete its source model element.

The first version supports a documented subset of draw.io. Arbitrary draw.io diagrams are outside the initial round-trip promise.
