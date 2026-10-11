# MBSE Diagrams

Reusable engineering diagram notation, editable diagram interchange, and rendering tools.

Status: experimental version 0.1. Structural SVG/HTML rendering, bounded SysML v2 extraction, UML class-view notation, draw.io interchange and Mermaid flowchart export are implemented. Repository: [rororowyourboat/mbse-diagrams](https://github.com/rororowyourboat/mbse-diagrams).

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

Run from the repository root with Python 3.10 or later; no package installation or third-party runtime dependencies are required. See [usage](docs/usage.md) and the explicit [support matrix](docs/support.md).

Try [the communication viewer](examples/communication/index.html) or [the UML viewer](examples/uml/index.html), or open their `.drawio` files in draw.io.

Run `python3 scripts/check_docs.py`, `python3 -m unittest discover -s tests -v`, and `git diff --check`. GitHub Actions also checks reproducible example exports.

See [contribution guidance](CONTRIBUTING.md). The initial CLI uses Python’s standard library. Future dependencies require a concrete need.

## License and provenance

Original repository content is licensed under the [MIT License](LICENSE). Third-party material retains its own license. Record origin and redistribution terms for every imported asset. Create original geometry from notation requirements rather than copying standards illustrations without permission.
