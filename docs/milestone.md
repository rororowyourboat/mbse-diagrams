# First milestone: communication diagram round trip

## Deliverables

- Original SVG symbol catalog for the communication example's definitions, usages, compartments, specialization and ownership/connection relationships.
- Standards provenance records for the included notation.
- Versioned JSON Schema and one source-linked example.
- JSON-to-SVG renderer with deterministic output.
- JSON-to-draw.io exporter, draw.io-to-JSON importer, and editable custom library.

## Acceptance

1. Render the fixture without missing or invented model relationships.
2. Export native editable draw.io nodes, labels and connectors.
3. Move a node and edit a display label in draw.io, then import the saved XML.
4. Confirm stable presentation IDs and model references survive unchanged.
5. Confirm endpoints, relationship kinds, nesting, compartments and supported geometry survive; document any normalization.
6. Confirm the edited display label does not rename the source model element.
7. Diagnose unsupported shapes and dangling references explicitly.
8. Render the imported JSON and visually inspect text, compartments and markers.

Record tool versions, fixture hashes, commands and observed results. Browser/editor execution is necessary to substantiate the manual-edit portion; XML-only tests are insufficient evidence of that step.

## Current evidence

No implementation or round-trip checks have run. Existing communication diagrams are candidate fixtures, not evidence that this milestone passes.
