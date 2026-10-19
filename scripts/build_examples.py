"""Rebuild committed example exports using only the standard library."""
from pathlib import Path
from html import escape
import hashlib
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mbse_diagrams.core import svg,viewer,drawio,mermaid
ROOT=Path(__file__).resolve().parents[1]
for folder in ('communication','uml'):
    target=ROOT/'examples'/folder
    d=json.loads((target/'diagram.json').read_text())
    for name,render in [('diagram.svg',svg),('index.html',viewer),('diagram.drawio',drawio)]:
        (target/name).write_text(render(d))
    text,report=mermaid(d)
    (target/'diagram.mmd').write_text(text)
    (target/'mermaid-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(folder+': SVG, HTML, draw.io, Mermaid and conversion receipt')

target=ROOT/'examples/native-views'
for stem in ('diagram','baseline','analyses'):
    d=json.loads((target/(stem+'.json')).read_text())
    for source in d['sources']:
        import hashlib
        actual='sha256:'+hashlib.sha256((target/source['uri']).read_bytes()).hexdigest()
        if actual!=source['revision']:
            raise SystemExit('Native view snapshot is stale: '+source['uri'])
    for extension,render in [('svg',svg),('html',viewer),('drawio',drawio)]:
        name='index.html' if stem=='diagram' and extension=='html' else stem+'.'+extension
        (target/name).write_text(render(d))
print('native-views: structural view and two source-declaration views rebuilt from retained JSON')

gallery=target/'multiview'
entries=[]
for report_path in sorted(gallery.glob('*-report.json')):
    stem=report_path.name.removesuffix('-report.json')
    receipt=json.loads(report_path.read_text())
    d=json.loads((gallery/(stem+'.json')).read_text())
    for source in d['sources']:
        actual='sha256:'+hashlib.sha256((target/source['uri']).read_bytes()).hexdigest()
        if actual!=source['revision']:
            raise SystemExit('Multi-view snapshot is stale: '+source['uri'])
    for extension,render in [('svg',svg),('html',viewer),('drawio',drawio)]:
        (gallery/(stem+'.'+extension)).write_text(render(d))
    entries.append((receipt['view'],stem+'.html',receipt['counts']))
listing=['<!doctype html><html lang="en"><meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width,initial-scale=1">',
         '<title>SysML model views</title><h1>Views of one SysML model</h1><ul>']
listing.extend(f'<li><a href="{escape(path,quote=True)}">{escape(name)}</a> '
               f'({counts["drawnNodes"]} elements, {counts["relationships"]} relationships)</li>'
               for name,path,counts in entries)
listing.append('</ul></html>')
(gallery/'index.html').write_text('\n'.join(listing)+'\n')
print(f'native-views/multiview: rebuilt {len(entries)} JSON-backed view exports')
