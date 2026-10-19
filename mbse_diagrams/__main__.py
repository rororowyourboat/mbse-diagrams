"""Run from the repository root: python3 -m mbse_diagrams --help."""
import argparse
import json
from pathlib import Path
import sys
import subprocess
import xml.etree.ElementTree as ET
import zlib
from .sysml import extract
from .diagramatic import layout
from .core import validate, svg, viewer, drawio, import_drawio, mermaid


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv and argv[0] in ('view', 'views'):
        from .cli_views import main as view_main
        return view_main(argv[1:])
    parser = argparse.ArgumentParser(description="Structural diagram rendering and interchange")
    parser.add_argument('command', choices=['validate','svg','html','drawio','import-drawio','mermaid','sysml','layout'])
    parser.add_argument('input', type=Path)
    parser.add_argument('-o','--output',type=Path)
    parser.add_argument('--report',type=Path,help='Required conversion receipt for import-drawio, mermaid, sysml, or layout')
    parser.add_argument('--diagramatic-path',type=Path,help='Trusted source checkout at the tested diagramatic commit')
    parser.add_argument('--direction',choices=['TB','BT','LR','RL'],default='TB')
    parser.add_argument('--layer',action='append',default=[],metavar='NODE=LAYER')
    args=parser.parse_args(argv)
    try:
        text=args.input.read_text()
        if args.command in ('import-drawio','mermaid','sysml','layout') and not args.report:
            parser.error('--report is required for conversions')
        if args.command=='sysml':
            d,report=extract(text,args.input.name);output=json.dumps(d,indent=2)+'\n'
        elif args.command=='import-drawio':
            d,report=import_drawio(text);output=json.dumps(d,indent=2)+'\n'
        else:
            d=validate(json.loads(text))
            if args.command=='layout':
                if not args.diagramatic_path: parser.error('--diagramatic-path is required for layout')
                layers={}
                for item in args.layer:
                    if '=' not in item: parser.error('--layer requires NODE=LAYER')
                    node,layer=item.split('=',1)
                    if not node or not layer or node in layers: parser.error('invalid or duplicate --layer assignment')
                    layers[node]=layer
                d,report=layout(d,args.diagramatic_path,args.direction,layers)
                output=json.dumps(d,indent=2)+'\n'
            elif args.command=='validate': output=f"Valid: {len(d['nodes'])} nodes, {len(d['edges'])} edges\n"
            elif args.command=='mermaid': output,report=mermaid(d)
            else: output={'svg':svg,'html':viewer,'drawio':drawio}[args.command](d)
        if args.output: args.output.write_text(output)
        else: print(output,end='')
        if args.report:
            require_report = args.command in ('import-drawio','mermaid','sysml','layout')
            if require_report: args.report.write_text(json.dumps(report,indent=2)+'\n')
    except (ValueError, KeyError, TypeError, OSError, ET.ParseError, zlib.error, subprocess.SubprocessError, ImportError) as exc:
        print(f'Error: {exc}',file=sys.stderr);return 1
    return 0


if __name__=='__main__':
    sys.exit(main())
