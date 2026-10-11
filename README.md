# MBSE Diagrams

Reusable engineering diagram notation, editable diagram interchange, and rendering tools.

Status: design scaffold. No renderer or adapter is implemented yet. Repository: [rororowyourboat/mbse-diagrams](https://github.com/rororowyourboat/mbse-diagrams).

## Goals

- Let people draw SysML v2 diagrams using reusable symbols with standards provenance.
- Let agents generate source-linked diagrams from engineering models.
- Preserve editable diagram structure and layout across supported tools.

Start with SysML v2; keep other engineering notations as future extensions. This is an independent supporting project, without OMG or OpenMBEE endorsement.

## Architecture

1. Notation catalog: SVG assets plus machine-readable notation metadata.
2. Experimental diagram JSON: model references, displayed elements, relationships and geometry.
3. Tools: SVG renderer and bidirectional draw.io adapter.

The engineering model remains authoritative for semantics. Diagram edits change presentation; they do not silently modify the source model.

## First milestone

Use the communication theory model as the first fixture. Generate a diagram, edit positions and labels in draw.io, import it back, and check preservation of identifiers, relationships and layout.

See [design](docs/design.md), [interchange contract](docs/interchange.md), and [milestone acceptance](docs/milestone.md).

## Development

Documentation only at present. No dependencies, installation steps, executable commands, or passing implementation checks are claimed. Establish the implementation language and tooling when the first renderer is added.

## License and provenance

No reuse license has been selected yet. Record origin and redistribution terms for every imported asset. Create original geometry from notation requirements rather than copying standards illustrations without permission.
