# Contributing

Start with the [first milestone](docs/milestone.md). Discuss broader features in an issue before adding dependencies or new adapters.

## Local checks

Run `python3 scripts/check_docs.py` and `git diff --check` from the repository root. The documentation check uses Python's standard library and needs no package installation. It checks local Markdown link targets, not remote URL availability.

If using the author's direnv helpers, review `.envrc` and explicitly approve it yourself. It selects personal context and contains no secrets; it is optional for other contributors.

## Changes and evidence

Keep changes focused. Include reproduction steps, actual validation results and limitations in pull requests. Do not describe a diagram as standards compliant without identifying the notation version, applicable rules and checks performed.

For symbols, record source, license, standard version, clause, supported variants and review status. For adapters, document supported fields and diagnose lossy conversions. Preserve model references independently of presentation labels.

Original contributions use the repository's MIT license. Third-party assets retain their own licenses; record attribution and redistribution terms before adding them. Do not copy standards illustrations on the assumption that this repository's license covers them.

No implementation language or production dependencies have been selected. The Python documentation checker does not determine the future renderer's language.
