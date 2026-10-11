"""Bounded structural diagram contract, renderer, and editable XML adapter."""
import base64
import copy
import html
import json
import math
import re
from urllib.parse import unquote
import xml.etree.ElementTree as ET
import zlib

SYMBOLS = {"sysml.part-definition": ("part def", 0), "sysml.item-definition": ("item def", 0),
           "sysml.part-usage": ("part", 12), "sysml.item-usage": ("item", 12),
           "uml.class": ("", 0)}
KINDS = {"specialization", "composition", "connection", "association", "dependency"}


class DiagramError(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise DiagramError(message)


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def fields(obj, allowed, required, where):
    require(isinstance(obj, dict), f"{where}: expected object")
    require(not (set(obj) - set(allowed)), f"{where}: unsupported fields {set(obj) - set(allowed)}")
    require(set(required) <= set(obj), f"{where}: missing required fields")


def validate(d):
    fields(d, "formatVersion id title notation sources nodes edges extensions".split(),
           "formatVersion id title notation sources nodes edges".split(), "diagram")
    require(d["formatVersion"] == "0.1", "unsupported formatVersion")
    require(isinstance(d["id"], str) and re.fullmatch(r"[A-Za-z][\w-]*", d["id"]), "invalid diagram id")
    require(isinstance(d["title"], str), "title must be text")
    require(d["notation"] in ("sysml-2.0-structural", "uml-2.5.1-class"), "unsupported notation profile")
    for key in ("sources", "nodes", "edges"):
        require(isinstance(d[key], list), f"{key}: expected array")
    require(isinstance(d.get("extensions", {}), dict), "extensions must be an object")
    sources = set()
    for s in d["sources"]:
        fields(s, ("id", "uri", "revision"), ("id", "uri"), "source")
        require(all(isinstance(v, str) for v in s.values()), "source fields must be text")
        require(s["id"] not in sources, "duplicate source id")
        sources.add(s["id"])
    ids = set()
    def common(x):
        require(isinstance(x["id"], str) and re.fullmatch(r"[A-Za-z][\w-]*", x["id"]), "invalid element id")
        require(x["id"] not in ids, "duplicate element id")
        ids.add(x["id"])
        require(isinstance(x["label"], str), "label must be text")
        if "modelRef" in x and x["modelRef"] is not None:
            r = x["modelRef"]
            fields(r, ("source", "element"), ("source", "element"), "modelRef")
            require(r["source"] in sources and isinstance(r["element"], str), "invalid model reference")
    node_ids = set()
    node_symbols = {}
    for n in d["nodes"]:
        fields(n, "id label symbol bounds compartments modelRef".split(), "id label symbol bounds".split(), "node")
        common(n)
        require(n["symbol"] in SYMBOLS, "unsupported symbol")
        require(n["symbol"].startswith("sysml.") == d["notation"].startswith("sysml"), "symbol/profile mismatch")
        b = n["bounds"]
        require(isinstance(b, list) and len(b) == 4 and all(number(v) for v in b), "invalid bounds")
        require(b[0] >= 0 and b[1] >= 0 and b[2] >= 100 and b[3] >= 60, "bounds need nonnegative origin, width >=100, height >=60")
        compartments = n.get("compartments", [])
        require(isinstance(compartments, list), "compartments must be array")
        height = 56
        for c in compartments:
            fields(c, ("name", "lines"), ("name", "lines"), "compartment")
            require(isinstance(c["name"], str) and isinstance(c["lines"], list) and all(isinstance(v, str) for v in c["lines"]), "invalid compartment")
            height += 28 + 20 * len(c["lines"])
        require(b[3] >= height, f"{n['id']}: insufficient compartment height")
        node_ids.add(n["id"])
        node_symbols[n['id']]=n['symbol']
    require(not ({n['id']+'--compartment-'+str(i) for n in d['nodes'] for i,_ in enumerate(n.get('compartments',[]))} & ids), 'presentation ID conflicts with generated compartment ID')
    allowed_kinds = {"specialization", "composition", "connection"} if d["notation"].startswith("sysml") else KINDS - {"connection"}
    for e in d["edges"]:
        fields(e, "id label kind source target points modelRef".split(), "id label kind source target points".split(), "edge")
        common(e)
        require(e["kind"] in allowed_kinds, "unsupported relationship/profile")
        require(e["source"] in node_ids and e["target"] in node_ids, "dangling edge endpoint")
        if d['notation'].startswith('sysml'):
            if e['kind']=='composition':
                require(node_symbols[e['target']].endswith('-usage'),'SysML composition target must be a usage presentation')
            if e['kind']=='connection':
                require(all(node_symbols[e[k]].endswith('-usage') for k in ('source','target')),'SysML connection endpoints must be usage presentations')
        require(isinstance(e["points"], list) and len(e["points"]) >= 2, "edge requires at least two points")
        require(all(isinstance(p, list) and len(p) == 2 and all(number(v) and v >= 0 for v in p) for p in e["points"]), "invalid edge points")
    return d


def svg(d):
    validate(d)
    esc = html.escape
    prefix = d["id"] + "-"
    width = max([n["bounds"][0] + n["bounds"][2] for n in d["nodes"]] + [p[0] for e in d["edges"] for p in e["points"]] + [200]) + 40
    height = max([n["bounds"][1] + n["bounds"][3] for n in d["nodes"]] + [p[1] for e in d["edges"] for p in e["points"]] + [100]) + 40
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="{prefix}title {prefix}desc">',
           f'<title id="{prefix}title">{esc(d["title"])}</title><desc id="{prefix}desc">{len(d["nodes"])} elements, {len(d["edges"])} relationships. Profile {esc(d["notation"])}.</desc>',
           f'<metadata>{esc(json.dumps(d, sort_keys=True))}</metadata>', '<defs>']
    for name, shape, ref in [
        ("open", '<path d="M0 0 L10 5 L0 10" fill="none"/>', 10),
        ("triangle", '<path d="M0 0 L10 5 L0 10 Z" fill="white"/>', 10),
        ("diamond", '<path d="M0 5 L7 0 L14 5 L7 10 Z" fill="#26364a"/>', 0)]:
        out.append(f'<marker id="{prefix}{name}" viewBox="-1 -1 16 12" refX="{ref}" refY="5" markerWidth="16" markerHeight="12" markerUnits="userSpaceOnUse" orient="auto-start-reverse" stroke="#26364a" stroke-width="1.5">{shape}</marker>')
    out += ['</defs>', '<rect width="100%" height="100%" fill="#f8fafc"/>', '<g font-family="Arial, sans-serif" font-size="14" fill="#17263a">']
    for e in d["edges"]:
        marker = "triangle" if e["kind"] == "specialization" else "open" if e["kind"] in ("connection", "dependency") else None
        attrs = f' marker-end="url(#{prefix}{marker})"' if marker else ""
        if e["kind"] == "composition":
            attrs += f' marker-start="url(#{prefix}diamond)"'
        if e["kind"] == "dependency":
            attrs += ' stroke-dasharray="6 4"'
        points = " ".join(f"{x},{y}" for x,y in e["points"])
        out.append(f'<g id="{prefix}{e["id"]}"><title>{esc(e["kind"] + ": " + e["label"])}</title><polyline points="{points}" fill="none" stroke="#26364a" stroke-width="1.5"{attrs}/>')
        x,y = e["points"][len(e["points"]) // 2]
        out.append(f'<text x="{x}" y="{y-9}" text-anchor="middle" paint-order="stroke" stroke="#f8fafc" stroke-width="5" stroke-linejoin="round">{esc(e["label"])}</text></g>')
    for n in d["nodes"]:
        x,y,w,h = n["bounds"]
        keyword, radius = SYMBOLS[n["symbol"]]
        ref = n.get("modelRef")
        out.append(f'<g id="{prefix}{n["id"]}" data-model-ref="{esc(json.dumps(ref), quote=True)}"><title>{esc(json.dumps(ref) if ref else "Unbound presentation")}</title><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="white" stroke="#26364a" stroke-width="1.5"/>')
        if keyword:
            out.append(f'<text x="{x+w/2}" y="{y+20}" text-anchor="middle">«{keyword}»</text>')
        out.append(f'<text x="{x+w/2}" y="{y+42}" text-anchor="middle" font-weight="bold">{esc(n["label"])}</text>')
        offset = 56
        for c in n.get("compartments", []):
            out.append(f'<path d="M{x} {y+offset} H{x+w}" stroke="#26364a"/><text x="{x+12}" y="{y+offset+20}" font-style="italic">{esc(c["name"])}</text>')
            for i,line in enumerate(c["lines"]):
                out.append(f'<text x="{x+12}" y="{y+offset+40+20*i}">{esc(line)}</text>')
            offset += 28 + 20*len(c["lines"])
        out.append('</g>')
    return "\n".join(out + ['</g></svg>'])


def viewer(d):
    image = svg(d)
    title = html.escape(d["title"])
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{title}</title>
<style>body{{margin:0;background:#f8fafc;color:#17263a;font:16px Arial}}header{{padding:16px;display:flex;gap:12px;align-items:center;flex-wrap:wrap}}h1{{font-size:20px;margin:0;margin-right:auto}}button{{padding:8px 14px}}main{{overflow:auto;padding:20px}}svg{{width:100%;min-width:600px}}#detail{{padding:16px;white-space:pre-wrap}}[data-model-ref]{{cursor:pointer}}</style>
<header><h1>{title}</h1><button id="out" aria-label="Zoom out">−</button><button id="fit">Fit</button><button id="in" aria-label="Zoom in">+</button><button id="download">Download SVG</button></header><main>{image}</main><aside id="detail" aria-live="polite">Select an element to inspect its model reference.</aside>
<script>const svg=document.querySelector('svg');let zoom=100;function scale(){{svg.style.width=zoom+'%';}}document.querySelector('#in').onclick=()=>{{zoom=Math.min(400,zoom+25);scale()}};document.querySelector('#out').onclick=()=>{{zoom=Math.max(25,zoom-25);scale()}};document.querySelector('#fit').onclick=()=>{{zoom=100;scale()}};document.querySelectorAll('[data-model-ref]').forEach(n=>{{n.onclick=()=>document.querySelector('#detail').textContent=n.dataset.modelRef}});document.querySelector('#download').onclick=()=>{{const u=URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(svg)],{{type:'image/svg+xml'}}));const a=document.createElement('a');a.href=u;a.download='diagram.svg';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000)}};</script></html>'''


def drawio(d):
    validate(d)
    root = ET.Element('mxfile', {'host':'mbse-diagrams', 'version':'0.1'})
    diagram = ET.SubElement(root, 'diagram', {'id':d['id'], 'name':d['title']})
    model = ET.SubElement(diagram, 'mxGraphModel', {'mbseDocument':json.dumps({k:v for k,v in d.items() if k not in ('nodes','edges')})})
    cells = ET.SubElement(model, 'root')
    ET.SubElement(cells, 'mxCell', {'id':'0'})
    ET.SubElement(cells, 'mxCell', {'id':'1','parent':'0'})
    def cell(x, style, attrs):
        obj = ET.SubElement(cells, 'object', {'id':x['id'], 'label':x['label'], 'mbseElement':json.dumps(x), 'mbseDocument':model.get('mbseDocument')})
        return ET.SubElement(obj, 'mxCell', {'parent':'1','style':style, **attrs})
    for n in d['nodes']:
        keyword,radius=SYMBOLS[n['symbol']]
        # Swimlane reserves an editable header and supports native child text compartments.
        style=f'swimlane;html=0;whiteSpace=wrap;startSize=56;horizontal=1;rounded={int(bool(radius))};arcSize=10;absoluteArcSize=1;fillColor=#ffffff;strokeColor=#26364a;'
        c=cell(n,style,{'vertex':'1'})
        if keyword:
            cells[-1].set('label', '«'+keyword+'»\n'+n['label'])
        x,y,w,h=n['bounds']
        ET.SubElement(c,'mxGeometry',{'x':str(x),'y':str(y),'width':str(w),'height':str(h),'as':'geometry'})
        offset=56
        for i,comp in enumerate(n.get('compartments',[])):
            child=ET.SubElement(cells,'mxCell',{'id':f"{n['id']}--compartment-{i}",'parent':n['id'],'vertex':'1','value':comp['name']+'\n'+'\n'.join(comp['lines']),'style':'text;html=0;whiteSpace=wrap;align=left;verticalAlign=top;spacing=12;strokeColor=none;fillColor=none;','mbseCompartment':str(i)})
            ch=28+20*len(comp['lines'])
            ET.SubElement(child,'mxGeometry',{'x':'0','y':str(offset),'width':str(w),'height':str(ch),'as':'geometry'})
            offset+=ch
    bounds_by_id={n['id']:n['bounds'] for n in d['nodes']}
    for e in d['edges']:
        end='block' if e['kind']=='specialization' else 'open' if e['kind'] in ('connection','dependency') else 'none'
        style=f"html=0;endArrow={end};endFill=0;startArrow={'diamond' if e['kind']=='composition' else 'none'};startFill=1;dashed={int(e['kind']=='dependency')};rounded=0;"
        for endpoint,index,anchor in [('source',0,'exit'),('target',-1,'entry')]:
            x,y,w,h=bounds_by_id[e[endpoint]]
            px,py=e['points'][index]
            style+=f'{anchor}X={(px-x)/w};{anchor}Y={(py-y)/h};{anchor}Dx=0;{anchor}Dy=0;{anchor}Perimeter=0;'
        c=cell(e,style,{'edge':'1','source':e['source'],'target':e['target']})
        g=ET.SubElement(c,'mxGeometry',{'relative':'1','as':'geometry'})
        for label,p in [('sourcePoint',e['points'][0]),('targetPoint',e['points'][-1])]:
            ET.SubElement(g,'mxPoint',{'x':str(p[0]),'y':str(p[1]),'as':label})
        points=ET.SubElement(g,'Array',{'as':'points'})
        for x,y in e['points'][1:-1]:
            ET.SubElement(points,'mxPoint',{'x':str(x),'y':str(y)})
    return ET.tostring(root,encoding='unicode')


def import_drawio(text):
    require(len(text.encode()) <= 2_000_000, 'draw.io input exceeds 2 MB')
    require('<!DOCTYPE' not in text.upper(), 'DOCTYPE is unsupported')
    root=ET.fromstring(text)
    if root.tag=='mxfile':
        pages=root.findall('diagram'); require(len(pages)==1,'only single-page draw.io is supported')
        model=pages[0].find('mxGraphModel')
        if model is None:
            require(bool(pages[0].text),'missing diagram data')
            compressed=base64.b64decode(pages[0].text,validate=True)
            decoder=zlib.decompressobj(-15)
            raw=decoder.decompress(compressed,2_000_001)
            require(len(raw)<=2_000_000 and decoder.eof,'compressed diagram too large or truncated')
            model=ET.fromstring(unquote(raw.decode()))
    else:
        model=root
    require(model.tag=='mxGraphModel','expected mxGraphModel')
    metadata=model.get('mbseDocument') or next((o.get('mbseDocument') for o in model.findall('root/object') if o.get('mbseDocument')),None)
    require(metadata is not None,'expected an MBSE Diagrams export')
    d=json.loads(metadata); d['nodes']=[];d['edges']=[]
    cells=model.find('root');require(cells is not None,'missing cells')
    parts={}; moved={}; normalized=[]; original_points={}
    for entry in cells:
        if entry.tag=='object':
            require('mbseElement' in entry.attrib,'unbound/new objects require explicit mapping')
            x=json.loads(entry.get('mbseElement'));c=entry.find('mxCell')
            require(c is not None,'missing mxCell')
            require(entry.get('id')==x['id'],'presentation id changed')
            x['label']=entry.get('label','')
            if c.get('vertex')=='1':
                keyword=SYMBOLS[x['symbol']][0]
                if keyword:
                    require(x['label'].startswith('«'+keyword+'»\n'),'notation keyword changed')
                    x['label']=x['label'].split('\n',1)[1]
            require(c.get('parent')=='1','nested nodes unsupported in 0.1')
            require('html=0;' in c.get('style',''),'HTML labels unsupported')
            g=c.find('mxGeometry');require(g is not None,'missing geometry')
            if c.get('vertex')=='1':
                require('swimlane;' in c.get('style',''),'unsupported node shape change')
                bounds=[float(g.get(k,'0')) for k in ('x','y','width','height')]
                if bounds!=x['bounds']: moved[x['id']]=(x['bounds'],bounds)
                x['bounds']=bounds;d['nodes'].append(x)
            elif c.get('edge')=='1':
                require(c.get('source')==x['source'] and c.get('target')==x['target'],'changed semantic endpoints require model review')
                style=c.get('style','')
                expected='block' if x['kind']=='specialization' else 'open' if x['kind'] in ('connection','dependency') else 'none'
                require('endArrow='+expected+';' in style,'relationship marker changed')
                require('endFill=0;' in style,'relationship marker fill changed')
                require('startArrow='+('diamond' if x['kind']=='composition' else 'none')+';' in style,'ownership marker changed')
                x['source']=c.get('source');x['target']=c.get('target')
                def point(p): return [float(p.get('x','0')),float(p.get('y','0'))]
                a=g.find("mxPoint[@as='sourcePoint']");b=g.find("mxPoint[@as='targetPoint']")
                require(a is not None and b is not None,'explicit edge endpoint geometry missing')
                original_points[x['id']]=copy.deepcopy(x['points'])
                x['points']=[point(a)]+[point(p) for p in g.findall("Array[@as='points']/mxPoint")]+[point(b)]
                d['edges'].append(x)
            else: raise DiagramError('unsupported object')
        elif entry.tag=='mxCell' and entry.get('mbseCompartment') is not None:
            require(entry.get('style','').startswith('text;html=0;'),'unsupported compartment style')
            key=(entry.get('parent'),int(entry.get('mbseCompartment')))
            require(key not in parts,'duplicate compartment')
            parts[key]=entry.get('value','').split('\n')
        elif entry.tag!='mxCell' or entry.get('id') not in ('0','1'):
            raise DiagramError('unbound/new cells require explicit mapping')
    for n in d['nodes']:
        for i,c in enumerate(n.get('compartments',[])):
            lines=parts.pop((n['id'],i),None);require(lines is not None,'missing compartment')
            c['name']=lines[0];c['lines']=lines[1:]
    require(not parts,'orphan compartment')
    for e in d['edges']:
        for endpoint,index in [('source',0),('target',-1)]:
            if e[endpoint] in moved and e['points'][index]==original_points[e['id']][index]:
                old,new=moved[e[endpoint]]
                point=e['points'][index]
                e['points'][index]=[new[0]+(point[0]-old[0])*new[2]/old[2],new[1]+(point[1]-old[1])*new[3]/old[3]]
                normalized.append(e['id']+': '+endpoint+' endpoint follows moved/resized node')
    validate(d)
    return d, {'preserved':['presentation IDs','model references','labels','supported geometry','relationship kinds'],
               'normalized':normalized, 'unsupported':[], 'lost':['editor-only styling'], 'scope':'MBSE Diagrams single-page structural exports only; styles are not imported'}


def mermaid(d):
    validate(d)
    require(all('"' not in x['label'] and '\n' not in x['label'] for x in d['nodes']+d['edges']), 'Mermaid subset requires single-line labels without quotes')
    def label(s): return html.escape(s).replace('|','&#124;').replace('[','&#91;').replace(']','&#93;')
    out=['flowchart LR']
    for n in d['nodes']:
        out.append(f'  {n["id"]}["{label(n["label"])}"]')
    for e in d['edges']:
        out.append(f'  {e["source"]} -->|"{label(e["kind"]+": "+e["label"])}"| {e["target"]}')
    report={'preserved':['node labels','edge endpoints','relationship kinds as text'], 'normalized':['all relationships displayed as flowchart arrows'],
            'unsupported':[], 'lost':['model references','notation glyphs','compartments','layout','editable presentation IDs for edges'], 'scope':'explanatory flowchart export; not formal SysML/UML interchange'}
    return '\n'.join(out)+'\n',report
