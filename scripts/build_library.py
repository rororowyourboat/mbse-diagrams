"""Generate a draw.io custom library of editable structural templates."""
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mbse_diagrams.core import SYMBOLS, drawio
ROOT=Path(__file__).resolve().parents[1]
entries=[]
for i,(symbol,(keyword,radius)) in enumerate(SYMBOLS.items()):
    d={'formatVersion':'0.1','id':'template','title':symbol,'notation':'sysml-2.0-structural' if symbol.startswith('sysml') else 'uml-2.5.1-class', 'sources':[], 'nodes':[{'id':'Element','label':'name : Type','symbol':symbol,'bounds':[0,0,260,124],'compartments':[{'name':'compartment','lines':['member : Type']}]}], 'edges':[]}
    model=ET.fromstring(drawio(d)).find('diagram/mxGraphModel')
    entries.append({'xml':ET.tostring(model,encoding='unicode'),'w':260,'h':124,'title':symbol})
root=ET.Element('mxlibrary');root.text=json.dumps(entries)
(ROOT/'notation/mbse.drawio-library.xml').write_text(ET.tostring(root,encoding='unicode'))
print('Generated five native editable structural templates.')
