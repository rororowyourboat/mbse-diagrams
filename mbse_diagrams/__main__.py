"""Run from the repository root: python3 -m mbse_diagrams --help."""
import argparse
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zlib
from .sysml import extract
from .core import validate, svg, viewer, drawio, import_drawio, mermaid


def main():
    parser = argparse.ArgumentParser(description="Structural diagram rendering and interchange")
    parser.add_argument('command', choices=['validate','svg','html','drawio','import-drawio','mermaid','sysml'])
    parser.add_argument('input', type=Path)
    parser.add_argument('-o','--output',type=Path)
    parser.add_argument('--report',type=Path,help='Required conversion receipt for import-drawio, mermaid, or sysml')
    args=parser.parse_args()
    try:
        text=args.input.read_text()
        if args.command in ('import-drawio','mermaid','sysml') and not args.report:
            parser.error('--report is required for conversions')
        if args.command=='sysml':
            d,report=extract(text,args.input.name);output=json.dumps(d,indent=2)+'\n'
        elif args.command=='import-drawio':
            d,report=import_drawio(text);output=json.dumps(d,indent=2)+'\n'
        else:
            d=validate(json.loads(text))
            if args.command=='validate': output=f"Valid: {len(d['nodes'])} nodes, {len(d['edges'])} edges\n"
            elif args.command=='mermaid': output,report=mermaid(d)
            else: output={'svg':svg,'html':viewer,'drawio':drawio}[args.command](d)
        if args.output: args.output.write_text(output)
        else: print(output,end='')
        if args.report:
            require_report = args.command in ('import-drawio','mermaid','sysml')
            if require_report: args.report.write_text(json.dumps(report,indent=2)+'\n')
    except (ValueError, KeyError, TypeError, OSError, ET.ParseError, zlib.error) as exc:
        print(f'Error: {exc}',file=sys.stderr);return 1
    return 0


if __name__=='__main__':
    sys.exit(main())
