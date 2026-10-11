# Design decisions

## Scope

One repository, three independently usable layers: notation assets, interchange contract, and rendering/adapters. First editor: draw.io. First output: standalone SVG. First notation profile: SysML 2.0 Language graphical notation.

## Symbol design

Keep geometric primitives, relationship markers and complete element templates distinct. A template includes keyword, name/type label, compartments and applicable connection anchors. Store standards version, clause, supported variations and review status with each symbol. Review status is evidence of an individual check, not certification.

Generate draw.io native shapes from the same notation definitions where practical. Importing an SVG as an image does not provide editable compartments or meaningful diagram connections.

## Interchange boundaries

Stable diagram identifiers differ from model identifiers. A model reference contains a source URI, source revision when available, and element identifier. Nodes may be repeated presentations of the same model element.

Store semantic relationship type separately from routing and arrow geometry. Select glyphs through a versioned notation profile. Version 0.1 preserves explicit waypoint geometry and labels. Nested ownership, ports and independent label positioning are deferred.

Use draw.io XML for editable editor exchange. SVG is a view export; embedded metadata can assist traceability but is not the canonical interchange file.

## Sources

- [OMG SysML 2.0](https://www.omg.org/spec/SysML/2.0), Language specification section 8.2.3.
- [draw.io custom library format](https://www.drawio.com/docs/reference/format-custom-shape-library/).
- [draw.io file format](https://github.com/jgraph/drawio/wiki/File-Format).

## Deferred

General SysML parsing beyond the strict implemented subset, model write-back, arbitrary SVG import, automatic layout, collaboration services, other editor adapters, and claims of full standards coverage.
