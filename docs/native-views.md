# Native SysML v2 views

The `view` command resolves a complete set of model files with an explicitly selected OpenSysML service executable, selects a declared SysML view, and produces diagram JSON plus a projection receipt. The existing commands then export SVG, offline HTML and editable draw.io.

The native view controls selection. Diagram JSON controls presentation. Editing a display label or position does not write back to SysML.

## Run the structural example

Use a trusted `sysml-grpc` executable with `parse_sources`, `strict_conformance` and `render_view` capabilities. This is a different executable from the `sysml` CLI. The adapter installs nothing and starts one private child using stdin/stdout; it opens no network listener. It has no third-party Python runtime dependencies.

```bash
python3 -m mbse_diagrams view examples/native-views/*.sysml \
  --engine /absolute/path/to/sysml-grpc \
  --view NativeViews::architecture --flatten \
  -o tmp/architecture.json --report tmp/architecture-report.json
python3 -m mbse_diagrams html tmp/architecture.json -o tmp/architecture.html
python3 -m mbse_diagrams svg tmp/architecture.json -o tmp/architecture.svg
python3 -m mbse_diagrams drawio tmp/architecture.json -o tmp/architecture.drawio
```

Create the output directory first. Commands can also run through the project's existing `uv` environment, for example `uv run --locked --no-sync python -m mbse_diagrams ...`. No new production dependency is required.

The example's [view definitions](../examples/native-views/views.sysml) include an inherited rendering:

```sysml
view def ArchitectureView {
    render Views::asInterconnectionDiagram;
}
view architecture : ArchitectureView {
    expose NativeNetwork::Transformer;
}
```

## Render several views together

Keep each view definition in the SysML model and ask the CLI to render a set of qualified view usages. The command parses the source files once, resolves each requested view against that same model hash, then writes JSON, receipts, SVG, HTML and draw.io files into a new output directory. `auto` uses structural notation for interconnection renderings and neutral declaration cards for tree renderings.

```bash
python3 -m mbse_diagrams views examples/native-views/*.sysml \
  --engine /absolute/path/to/sysml-grpc --flatten \
  --view NativeViews::architecture \
  --view NativeViews::components \
  --view NativeViews::baseline \
  --view NativeViews::analyses \
  --view ResearchPerspectives::byRole \
  --view ResearchPerspectives::byDomain \
  --view ResearchPerspectives::parameterInfluence \
  --view ResearchPerspectives::analysisTraceability \
  --output-dir /tmp/modulo-study-views
```

Open the generated `index.html` to browse the set. The retained [multi-view example](../examples/native-views/multiview/index.html) is generated from the same five SysML files. `byRole` shows component usages with their types; `byDomain` brings network and experiment declarations together. The parameter map encodes an explicit design dependency through typed ports. The trace map links three hypotheses to planned analyses and planned observations. Those links are model statements; they do not establish measured effects or successful hypotheses.

For now, each graph node carries a source binding to its own SysML declaration. The `modelElement` qualified-name attributes in the influence map are author-entered labels; OpenSysML does not resolve them to target element identities. The declared port connections are explicit and preserved, while their scientific interpretation remains the model author's responsibility.

OpenSysML, rather than this adapter, resolves imports, selection filters and inherited rendering. The fixture also includes a filtered parts-only view: it produces nine component presentations and no invented connection edges.

## Baseline and analysis signatures

For a native tree view, `--presentation declarations` displays neutral source cards. It can show experiment values and analysis subjects/parameters without inventing a computation workflow or claiming a formal analysis-case glyph.

```bash
python3 -m mbse_diagrams view examples/native-views/*.sysml \
  --engine /absolute/path/to/sysml-grpc \
  --view NativeViews::baseline --flatten --presentation declarations \
  -o tmp/baseline.json --report tmp/baseline-report.json
python3 -m mbse_diagrams html tmp/baseline.json -o tmp/baseline.html
```

Use `NativeViews::analyses` in the same command for the three analysis signatures. These declarations describe interfaces. Their values are copied from the frozen source locations; they are not evaluated results or evidence of successful training.

## What survives

- Every supplied file has a portable document name and a SHA-256 of the exact UTF-8 input bytes. Those bytes are sent together in one strict parse.
- Nodes and relationships carry source-span references within those file revisions. These are local textual references, not engine-assigned UUIDs or permanent element IDs across edits.
- `extensions["mbse-diagrams.native-view"]` retains the qualified view name, rendering kind, selected element names/kinds/parents, model references, engine port identities/types/directions and each edge's port endpoints.
- Selected attribute/member declarations become compartment text. Their independent source references remain in the extension even though they are not separate shapes.
- The receipt records the original resolved rendering under `resolvedView`, engine version, executable SHA-256, engine model hash, diagnostics, counts, normalization and losses. The adapter uses the executable's embedded standard library, excluding `OPENSYSML_LIBRARY_PATH`; supply domain libraries as explicit input files.
- SVG/HTML retain metadata. The viewer can inspect node and connection source references, including file revision and port endpoint information. Our draw.io round trip preserves these bindings through presentation edits.

## Explicit boundaries

The adapter projects into the existing **flat JSON 0.1** contract. `--flatten` is required when selected elements have parents or ports. Nested shapes and native port glyphs/anchors are not drawn: ports appear in compartments, and endpoint names label the edges. The receipt records this loss. The enclosing transformer definition remains a separate context card, so the example draws ten nodes: its definition and nine components.

Structural presentation supports resolved part/item definitions and usages, their selected attributes, and connection/composition/specialization relationships. Declaration cards support a tree with selected roots and one level of members, without relationship edges. Unknown kinds, unknown endpoints, unresolved source locations, rendering notices, notes needing an unsupported projection, empty selections and engine errors are rejected rather than silently omitted.

The default layout is a small deterministic layout based on endpoint ordering. It is not a data-flow analysis. Supplied engine styling/geometry is replaced and reported; connector crossing minimization and independent label positioning are not guaranteed. Use draw.io or the existing optional diagramatic bridge to curate presentation; that bridge also does not guarantee crossing-free routing.

OpenSysML's stdin/stdout transport is described upstream as an evaluation prototype. This adapter was exercised with release **v0.10.1**, commit `1c45b6e1749fc8adc9b82d4af22fbe180b56a0e2`, whose Linux AMD64 service binary SHA-256 was `1469eb7516a439fc372bc99812bf8bb5b4d2fb1b7279af29b2f055d6edbd1134`. Capability checks precede parsing. This is an optional experimental integration, not a claim of general engine/version compatibility, full SysML coverage, or Kotar UI interoperability.

## Checks and retained example

```bash
uv run --locked --no-sync python -m unittest discover -s tests -v
OPENSYSML_ENGINE=/absolute/path/to/sysml-grpc \
  uv run --locked --no-sync python -m unittest discover -s tests -v
python3 scripts/build_examples.py
python3 scripts/check_docs.py
git diff --check
```

Without `OPENSYSML_ENGINE`, native engine integration tests skip explicitly. Ordinary tests replay the retained [resolved view](../examples/native-views/resolved-view.json), verify exact connection/port endpoint sets and source hashes, compare the frozen projection, reject unsupported content, and check draw.io binding preservation. Engine tests exercise multi-file imports, inherited rendering, filtered selection, declaration views, invalid models, and missing/empty views.

The fixture and retained exports are under [examples/native-views](../examples/native-views/). Rebuild rendering from the retained JSON with `scripts/build_examples.py`; that command checks source hashes and requires no engine. To refresh native selection after changing the fixture, rerun `view` for `architecture`, `baseline` and `analyses`, preserving their receipts. The corresponding retained filenames are `diagram.json`/`diagram-report.json`, `baseline.json`/`baseline-report.json` and `analyses.json`/`analyses-report.json`. Refresh the raw architecture fixture from its receipt with:

```bash
jq '.resolvedView' examples/native-views/diagram-report.json \
  > examples/native-views/resolved-view.json
```

Do not hand-edit engine evidence to make a test pass.

The initial integration is tracked in [issue #1](https://github.com/rororowyourboat/mbse-diagrams/issues/1). Native port/nesting glyphs can evolve separately from this explicit flat projection.

## Source basis

- [SysML 2.0 Language specification, section 7.26](https://www.omg.org/spec/SysML/2.0/Language/PDF): view usages, exposure, filters and rendering.
- [OpenSysML v0.10.1 service protocol](https://github.com/Open-MBEE/OpenSysML/blob/v0.10.1/api/proto/sysml.proto): `ParseSources`, `GetServerInfo`, `RenderView`, source spans and port endpoints.
- [OpenSysML stdin/stdout protocol](https://github.com/Open-MBEE/OpenSysML/blob/v0.10.1/internal/frontend/stdiorpc/server.go): JSON-RPC framing used by the optional child process.
