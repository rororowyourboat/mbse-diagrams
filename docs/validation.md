# Version 0.1 validation scope

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
