# Using the first implementation

Run commands from the repository root with Python 3.10 or later. No package installation is required.

## View the examples

Open [communication viewer](../examples/communication/index.html) or [UML viewer](../examples/uml/index.html) in a browser. Both work offline. SVG, draw.io XML, Mermaid source and the Mermaid loss report are alongside each viewer.

## Render a diagram

```bash
python3 -m mbse_diagrams validate examples/communication/diagram.json
python3 -m mbse_diagrams svg examples/communication/diagram.json -o /tmp/communication.svg
python3 -m mbse_diagrams html examples/communication/diagram.json -o /tmp/communication.html
```

## Extract the supported SysML subset

```bash
python3 -m mbse_diagrams sysml examples/communication/communication.sysml -o /tmp/extracted.json --report /tmp/extraction-report.json
python3 -m mbse_diagrams svg /tmp/extracted.json -o /tmp/extracted.svg
```

The strict extractor rejects unsupported constructs. It does not validate the full SysML language. Inspect its receipt and generated layout before sharing.

## Edit in draw.io

```bash
python3 -m mbse_diagrams drawio examples/communication/diagram.json -o /tmp/communication.drawio
# Open the file in draw.io; edit a display label or move a node; save as XML.
python3 -m mbse_diagrams import-drawio /tmp/communication.drawio -o /tmp/edited.json --report /tmp/import-report.json
python3 -m mbse_diagrams html /tmp/edited.json -o /tmp/edited.html
```

Display edits retain the source model reference. Changing relationship endpoints or markers is rejected because that changes engineering meaning. Inspect the import receipt for normalizations and lost styling.

For manual drawing, choose File → Open Library in draw.io and load [the custom library](../notation/mbse.drawio-library.xml). Its five native templates are editable; arbitrary diagrams drawn with the library do not automatically acquire valid model references or an importable interchange document.

## Export Mermaid

```bash
python3 -m mbse_diagrams mermaid examples/communication/diagram.json -o /tmp/communication.mmd --report /tmp/mermaid-report.json
```

This is an explanatory flowchart conversion. The receipt identifies the formal notation and metadata lost.

## Rebuild and check

```bash
python3 scripts/build_examples.py
python3 scripts/build_library.py
python3 scripts/check_docs.py
python3 -m unittest discover -s tests -v
git diff --check
```

The JSON Schema documents structure. The Python validator additionally checks references, profile compatibility, finite coordinates and minimum compartment height. No third-party schema validator is bundled.

## Optional browser checks

With an existing Playwright installation and Chromium, run `node scripts/check_browser.cjs`. Set `PLAYWRIGHT_MODULE` to an existing module path if it is outside this repository. The checker does not install dependencies. It checks both local HTML examples; it does not exercise the draw.io editor.

## Optional automatic layout

Use the [diagramatic integration](diagramatic-integration.md) for grid layout backed by the older toolkit. No dependency installation is required for its supported grid backend.
