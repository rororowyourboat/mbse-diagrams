# SysML-authored multi-view example

One five-file SysML v2 model, eight named view selections:

- [Transformer structure](index.html): nine components, 19 listed ports and ten connections, plus the enclosing definition as a context card.
- [Multi-view gallery](multiview/index.html): browse the structural, component, baseline, analysis, role, domain, parameter-influence and hypothesis-traceability views together.
- [Baseline declarations](baseline.html): source settings for modulo 113 and 40,000 training steps.
- [Analysis declarations](analyses.html): subjects and input/output signatures for spectrum, mechanism and ablation analyses. No analysis executes here.

The structural view inherits its rendering from a view definition. `views.sysml` exercises a parts-only filter and an empty selection; `perspectives.sysml` adds role/domain selections and two explicitly connected relationship maps. The parameter links describe the intended mapping from task modulus to output class space. The trace links record planned hypothesis coverage. Neither graph is evidence of a measured effect or completed analysis.

The [batch `views` command](../../docs/native-views.md#render-several-views-together) parses this source set once and emits every selected view. The generated JSON diagrams and receipts in `multiview/` retain engine selections, source hashes, engine identity and explicit presentation losses. SVG, HTML and draw.io exports sit alongside them. The earlier `diagram.json`, `baseline.json` and `analyses.json` remain single-view examples; `resolved-view.json` is the architecture response used for engine-free projection checks.

The port glyphs and nested shapes are deliberately flattened. Engine port identities and endpoints remain in metadata; source cards are declaration text, not evaluated results. In the two graph views, `modelElement` text is author-entered and not resolved by the current engine adapter; each graph node still links to its own source declaration.

See [commands, regeneration and support limits](../../docs/native-views.md).
