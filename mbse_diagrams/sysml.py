"""Strict extractor for a tiny, documented SysML v2 definition-view subset.

Not a language validator or modeling engine. Unsupported constructs fail.
"""
import hashlib
import re
from .core import require, validate


def extract(text, uri):
    original=text
    text=re.sub(r'/\*.*?\*/','',text,flags=re.S)
    text=re.sub(r'//[^\n]*','',text)
    tokens=re.findall(r':>|[A-Za-z_]\w*|[{};:]|\S',text)
    position=0
    def take(expected=None):
        nonlocal position
        require(position<len(tokens),'unexpected end of SysML subset input')
        token=tokens[position];position+=1
        require(expected is None or token==expected,f'expected {expected}, got {token}; outside supported SysML subset')
        return token
    def name():
        result=take();require(bool(re.fullmatch(r'[A-Za-z_]\w*',result)),'expected simple name');return result
    take('package');package=name();take('{');definitions=[]
    while position<len(tokens) and tokens[position]!='}':
        kind=take();require(kind in ('part','item'),'only part/item definitions supported')
        take('def');identifier=name();parent=None;members=[]
        if position<len(tokens) and tokens[position]==':>':take(':>');parent=name()
        body=take();require(body in (';','{'),'definition must end with ; or a supported body')
        if body=='{':
            while position<len(tokens) and tokens[position]!='}':
                member_kind=take();require(member_kind in ('part','item'),'only typed part/item usages supported in bodies')
                member=name();take(':');typ=name();take(';')
                require(member not in [m[1] for m in members],'duplicate member')
                members.append((member_kind,member,typ))
            take('}')
        definitions.append((kind,identifier,parent,members))
    take('}');require(position==len(tokens),'trailing input outside supported subset')
    ids=[x[1] for x in definitions];require(len(ids)==len(set(ids)),'duplicate definition names')
    for kind,identifier,parent,members in definitions:
        require(parent is None or parent in ids,'unresolved specialization')
        require(all(m[2] in ids for m in members),'unresolved usage type')
    parents={identifier:parent for _,identifier,parent,_ in definitions}
    kinds={identifier:kind for kind,identifier,_,_ in definitions}
    for kind,identifier,parent,members in definitions:
        require(parent is None or kinds[parent]==kind,'specialization kind mismatch')
        require(all(kinds[m[2]]==m[0] or m[0]=='item' for m in members),'usage type kind mismatch')
        visited=set();cursor=identifier
        while cursor is not None:
            require(cursor not in visited,'cyclic specialization')
            visited.add(cursor);cursor=parents[cursor]
    d={'formatVersion':'0.1','id':'sysml-view','title':package+' — definition view','notation':'sysml-2.0-structural',
       'sources':[{'id':'model','uri':uri,'revision':'sha256:'+hashlib.sha256(original.encode()).hexdigest()}], 'nodes':[],'edges':[]}
    def ref(s):return {'source':'model','element':package+'::'+s}
    layout={}
    for i,(kind,identifier,parent,members) in enumerate(definitions):
        width=300;height=90 if not members else 84+20*len(members)
        x=40+(i%3)*380;y=40+(i//3)*260
        layout[identifier]=[x,y,width,height]
        compartments=[]
        for member_kind in ('part','item'):
            lines=[m[1]+' : '+m[2] for m in members if m[0]==member_kind]
            if lines:compartments.append({'name':member_kind+'s','lines':lines})
        if len(compartments)>1:height+=28
        d['nodes'].append({'id':identifier,'label':identifier,'symbol':'sysml.'+kind+'-definition','bounds':[x,y,width,height], 'compartments':compartments,'modelRef':ref(identifier)})
    for kind,identifier,parent,members in definitions:
        if parent:
            x,y,w,h=layout[identifier];tx,ty,tw,th=layout[parent]
            d['edges'].append({'id':identifier+'-specialization','label':'','kind':'specialization','source':identifier,'target':parent,
                              'points':[[x+w/2,y],[x+w/2,max(0,y-20)],[tx+tw/2,max(0,y-20)],[tx+tw/2,ty+th]], 'modelRef':ref(identifier+'::specialization')})
    validate(d)
    return d,{'scope':'single package; part/item definitions, simple specialization and typed part/item usages',
              'preserved':['definition names','specialization','typed usages as compartment lines','source byte hash'],
              'normalized':['simple grid layout','textual qualified names used as local model references'], 'unsupported':[], 'lost':[],
              'languageValidation':'not run: extractor is not a SysML modeling engine'}
