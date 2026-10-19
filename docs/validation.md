# Version 0.1 validation scope

Native-view checks on 19 October 2026:

- Test discovery with an explicit OpenSysML v0.10.1 service executable: 33 tests, 30 passed and three existing diagramatic integration tests skipped because no trusted checkout was configured. Native engine tests cover multi-file imports, inherited rendering, filtered/empty/missing views, invalid models, declaration views and endpoint preservation.
- The portable fixture and the external six-file Fourier study both retained nine transformer components, 19 listed ports and all ten connections, including the two residual paths. Each structural diagram also contains its enclosing definition as a context card. Original Fourier source files were unchanged.
- Eight offline HTML views were checked through an isolated headless Chrome session: the existing communication/UML examples, three native-view fixtures and three Fourier previews. Zoom/fit, bound node/connection inspection, completed SVG downloads and text bounds passed; no text collisions or page exceptions were observed. Native fixture screenshots were visually inspected.
- Example exports and the five-symbol library were rebuilt. Documentation links and whitespace checks passed.
- Draw.io verification is still XML round-trip and presentation-edit testing, not a live editor session. Kotar native-view rendering and native Mermaid rendering were not verified. Nested shapes and port glyphs remain explicit projection losses.

The retained [native-view evidence](../evidence/native-views.json) identifies code/artifact hashes, the engine binary and check results. The earlier receipt below remains a historical record; its hashes are not assertions about the updated files.

Multi-view generation on 20 October 2026:

- The new `views` command parsed one five-file SysML model once and rendered eight declared views from the same model hash. The set includes structural and filtered component views, experiment declarations, an explicit parameter mapping, and planned hypothesis-to-analysis trace paths.
- SVG, HTML, draw.io, JSON and per-view receipts were generated into the retained gallery. `scripts/build_examples.py` reproduced the rendered exports from those JSON diagrams and checked the source byte hashes.
- The parameter and trace networks are explicitly authored SysML connections. Their node `modelElement` strings are labels, not engine-resolved references. The trace view records planned analysis coverage; it contains no results or evidence that a hypothesis passed.
- No test suite or browser check was run for this incremental change. The earlier native-view evidence remains a historical snapshot.

The [multi-view evidence](../evidence/multiview.json) records the engine/model identity, selected views, source hashes and generated artifact hashes.

Local checks on 11 October 2026:

- Python standard-library interchange tests: 14 passed. Covers supported export/import equality, presentation edits, moved-node endpoint normalization, compressed editor data, compartment edits, unsupported semantic changes, dangling references, escaping, accessibility, UML dependency rendering and strict SysML subset extraction.
- Browser: both generated HTML viewers checked with installed Playwright/Chromium. Zoom, fit reset, model-reference selection, SVG download and text bounds passed; no page errors observed. Screenshots visually inspected: labels, compartments, specialization and dependency markers readable.
- CLI: supported SysML extraction, JSON validation, draw.io import/export and SVG re-render exercised.
- Documentation local links and whitespace: passed.
- Live draw.io editor: two initialization attempts timed out. No manual browser edit/save round trip is claimed. XML presentation-edit tests are narrower evidence.
- Native Mermaid rendering: not run; no local Mermaid runtime available. Source is exported against documented flowchart syntax with an explicit loss receipt.
- SysML engine validation: not run. The extractor is not an engine.
- Full UML/SysML notation conformance: not established; partial glyph implementation only.

The first milestone remains incomplete until a real editor round trip is recorded. Check evidence hashes in [the receipt](../evidence/validation.json). Re-run checks when fixtures or implementation change; this record is not a certification.
