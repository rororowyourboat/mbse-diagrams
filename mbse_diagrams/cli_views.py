"""CLI handlers for native SysML view projection."""
import argparse
import html
import json
from pathlib import Path
import re
import tempfile

from .core import drawio, svg, viewer
from .opensysml import extract_view, extract_views


def main(argv=None):
    parser = argparse.ArgumentParser(description='Project declared SysML v2 views')
    commands = parser.add_subparsers(dest='command', required=True)
    one = commands.add_parser('view')
    one.add_argument('input', type=Path, nargs='+')
    one.add_argument('--view', required=True)
    one.add_argument('--engine', type=Path, required=True)
    one.add_argument('--flatten', action='store_true')
    one.add_argument('--presentation', choices=['structure', 'declarations'], default='structure')
    one.add_argument('--timeout', type=float, default=30)
    one.add_argument('-o', '--output', type=Path)
    one.add_argument('--report', type=Path, required=True)
    many = commands.add_parser('views')
    many.add_argument('input', type=Path, nargs='+')
    many.add_argument('--view', action='append', required=True, metavar='QUALIFIED_NAME')
    many.add_argument('--engine', type=Path, required=True)
    many.add_argument('--flatten', action='store_true')
    many.add_argument('--presentation', choices=['auto', 'structure', 'declarations'], default='auto')
    many.add_argument('--timeout', type=float, default=30)
    many.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args(argv)

    if args.command == 'view':
        diagram, receipt = extract_view(args.input, args.view, args.engine,
                                        flatten=args.flatten, presentation=args.presentation,
                                        timeout=args.timeout)
        output = json.dumps(diagram, indent=2) + '\n'
        if args.output:
            args.output.write_text(output, encoding='utf-8')
        else:
            print(output, end='')
        args.report.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
        return 0

    destination = args.output_dir.resolve(strict=False)
    if destination.exists() or not destination.parent.is_dir():
        parser.error('--output-dir must be a new path with an existing parent')
    rendered = extract_views(args.input, args.view, args.engine, flatten=args.flatten,
                              presentation=args.presentation, timeout=args.timeout)
    files = {}
    used = {'index.html'}
    links = []
    for name, (diagram, receipt) in rendered.items():
        stem = re.sub(r'[^A-Za-z0-9._-]+', '-', name.replace('::', '-')).strip('-.')
        names = {stem, *(f'{stem}.{ext}' for ext in ('json', 'svg', 'html', 'drawio')),
                 f'{stem}-report.json'}
        if not stem or stem in ('.', '..') or used.intersection(names):
            parser.error(f'view names produce an invalid or duplicate output name: {name}')
        used.update(names)
        files[f'{stem}.json'] = json.dumps(diagram, indent=2) + '\n'
        files[f'{stem}-report.json'] = json.dumps(receipt, indent=2) + '\n'
        files[f'{stem}.svg'] = svg(diagram)
        files[f'{stem}.html'] = viewer(diagram)
        files[f'{stem}.drawio'] = drawio(diagram)
        links.append((name, f'{stem}.html'))
    listing = ['<!doctype html><html lang="en"><meta charset="utf-8">',
               '<meta name="viewport" content="width=device-width,initial-scale=1">',
               '<title>SysML views</title><h1>SysML views</h1><ul>']
    listing.extend(f'<li><a href="{html.escape(path, quote=True)}">{html.escape(name)}</a></li>'
                   for name, path in links)
    listing.append('</ul></html>')
    files['index.html'] = '\n'.join(listing) + '\n'
    with tempfile.TemporaryDirectory(prefix=f'.{destination.name}.', dir=destination.parent) as staging:
        stage = Path(staging)
        for filename, content in files.items():
            (stage / filename).write_text(content, encoding='utf-8')
        stage.rename(destination)
    print(f'Rendered {len(rendered)} views to {destination}')
    return 0
