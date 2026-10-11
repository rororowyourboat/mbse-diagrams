"""Optional bridge to an explicitly selected diagramatic source checkout.

No dependency installation, code vendoring, or source-model changes.
"""
import copy
import hashlib
import importlib
from pathlib import Path
import subprocess
import sys
from .core import DiagramError, require, validate

TESTED_COMMIT = 'baba9c95ea4b2783ae77d205bd958745d6eb9b83'


def layout(d, checkout, direction='TB', layers=None):
    validate(d)
    require(direction in ('TB','BT','LR','RL'),'unsupported layout direction')
    checkout=Path(checkout).resolve()
    require((checkout/'diagramatic/layout/grid.py').is_file(),'expected a diagramatic source checkout')
    commit=subprocess.check_output(['git','-C',str(checkout),'rev-parse','HEAD'],text=True).strip()
    dirty=bool(subprocess.check_output(['git','-C',str(checkout),'status','--porcelain','--untracked-files=no'],text=True).strip())
    require(commit==TESTED_COMMIT and not dirty,'diagramatic must be at the tested commit with no tracked changes')
    # Importing a checkout executes its code: caller must explicitly select a trusted source.
    sys.path.insert(0,str(checkout))
    try:
        package=importlib.import_module('diagramatic')
        require(Path(package.__file__).resolve().parent==checkout/'diagramatic','another diagramatic installation is already loaded')
        grid=importlib.import_module('diagramatic.layout.grid')
        spatial=importlib.import_module('diagramatic.core.spatial')
    finally:
        sys.path.remove(str(checkout))
    layers=layers or {}
    node_ids={n['id'] for n in d['nodes']}
    require(set(layers)<=node_ids,'layer assignment references an unknown node')
    order=list(dict.fromkeys(layers.get(n['id'],'default') for n in d['nodes']))
    nodes=[package.LayoutNode(id=n['id'],label=n['label'],layer=layers.get(n['id'],'default'),width=n['bounds'][2],height=n['bounds'][3]) for n in d['nodes']]
    spec=package.DiagramSpec(title=d['title'],direction=direction,nodes=nodes,layers=order)
    positions=grid.grid_layout(spec)
    require({n.id for n in positions}==node_ids and len(positions)==len(node_ids),'layout did not preserve all nodes')
    result=copy.deepcopy(d)
    bounds={n.id:[n.x,n.y,n.width,n.height] for n in positions}
    for n in result['nodes']:n['bounds']=bounds[n['id']]
    for e in result['edges']:
        sx,sy,sw,sh=bounds[e['source']];tx,ty,tw,th=bounds[e['target']]
        if e['source']==e['target']:
            start=[sx+sw,sy+sh/3];end=[sx+sw,sy+2*sh/3]
            e['points']=[start,[sx+sw+40,start[1]],[sx+sw+40,end[1]],end]
        elif direction in ('TB','BT'):
            down=ty>=sy
            start=[sx+sw/2,sy+sh if down else sy];end=[tx+tw/2,ty if down else ty+th]
            mid=(start[1]+end[1])/2
            e['points']=[start,[start[0],mid],[end[0],mid],end]
        else:
            right=tx>=sx
            start=[sx+sw if right else sx,sy+sh/2];end=[tx if right else tx+tw,ty+th/2]
            mid=(start[0]+end[0])/2
            e['points']=[start,[mid,start[1]],[mid,end[1]],end]
    validate(result)
    shapes=[{'id':n['id'],'type':'rectangle','x':n['bounds'][0],'y':n['bounds'][1],'width':n['bounds'][2],'height':n['bounds'][3]} for n in result['nodes']]
    overlaps=spatial.detect_overlaps(shapes)
    require(not overlaps,'diagramatic returned overlapping node bounds')
    hashes={name:hashlib.sha256((checkout/name).read_bytes()).hexdigest() for name in ('diagramatic/layout/grid.py','diagramatic/core/spatial.py')}
    receipt={'engine':{'repository':'https://github.com/rororowyourboat/diagramatic','commit':commit,'trackedChanges':dirty,'sourceHashes':hashes},
             'preserved':['node/edge IDs','model references','symbols','relationship kinds','endpoints','labels','compartments','node sizes'],
             'normalized':['node positions from diagramatic grid','edge endpoints and orthogonal routing from MBSE adapter'],
             'unsupported':[], 'lost':['previous layout and routing'], 'checks':{'nodeOverlap':'passed','edgeNodeCrossings':'not checked','textOverflow':'not checked'},
             'direction':direction,'layerAssignments':layers,'scope':'layout only; not notation or model conformance'}
    return result,receipt
