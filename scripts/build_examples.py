"""Rebuild committed example exports using only the standard library."""
from pathlib import Path
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
