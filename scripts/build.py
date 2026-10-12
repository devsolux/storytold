#!/usr/bin/env python3
"""Generate, check, package, or clean owned outputs; never install a host."""
from pathlib import Path
import argparse
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from storytold_tools.build import build,clean,package
from storytold_tools.common import ROOT,local

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['build','check','plugin','source','clean'])
    p.add_argument('--root',default=str(ROOT));a=p.parse_args()
    try:
        r=local(a.root)
        if a.action=='clean': print('\n'.join(clean(r)))
        elif a.action in {'plugin','source'}: print(package(r,a.action))
        else: print(build(r,check=a.action=='check'))
        return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print('build: '+str(exc),file=sys.stderr);return 1
if __name__=='__main__': raise SystemExit(main())
