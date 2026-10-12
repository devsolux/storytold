"""Explicit, deterministic Storytold maintenance commands."""
from __future__ import annotations
import argparse
import asyncio
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import sys
from .catalog import load_catalog,selected,inventory,preflight
from .common import ROOT,StorytoldError,absolute,create_new,encoded,load_json,local,require
from .configuration import write_config
from .probe import probe
from .workspace import init_workspace,stage,verify_inputs,verify_artifact


def parser() -> argparse.ArgumentParser:
    p=argparse.ArgumentParser(description='Local Craft integration helpers. No MCP server or automatic host/app installation.')
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('doctor',help='Report capabilities without executing or installing hosts/apps')
    sub.add_parser('apps',help='Show the twelve source-documented app entries')
    s=sub.add_parser('workspace-init',help='Create a NEW private inputs/outputs workspace')
    s.add_argument('--root',required=True)
    s=sub.add_parser('inventory',help='Hash installed binaries without executing them')
    s.add_argument('--bin-dir',default=os.getenv('CRAFT_BIN_DIR'));s.add_argument('--app',action='append')
    for name in ('preflight','probe','configure'):
        s=sub.add_parser(name,help={'preflight':'Validate roots and reviewed binary pins; no execution',
                                   'probe':'Explicit native initialize/tools-list and optional single smoke call',
                                   'configure':'Create NEW host config after matching native discovery+call evidence'}[name])
        s.add_argument('--bin-dir',default=os.getenv('CRAFT_BIN_DIR'))
        s.add_argument('--work-root',default=os.getenv('CRAFT_WORK_ROOT'))
        s.add_argument('--output-root',default=os.getenv('CRAFT_OUTPUT_ROOT'))
        s.add_argument('--lock',required=True)
        s.add_argument('--app',action='append')
        s.add_argument('--acknowledge-unconfined',action='store_true',help='Explicitly acknowledge OS-only scope; NOT evidence of isolation')
        if name=='probe':
            s.add_argument('--confirm-execution',action='store_true')
            s.add_argument('--timeout',type=float,default=20)
            s.add_argument('--call-json',help='One operator-reviewed, fixture-only native tools/call request')
            s.add_argument('--approve-call',action='store_true',help='Approve that exact call; annotations alone never authorize it')
            s.add_argument('--output',required=True,help='New evidence file, never overwritten')
        if name=='configure':
            s.add_argument('--host',choices=['claude','codex'],required=True)
            s.add_argument('--evidence-dir',required=True)
            s.add_argument('--output',required=True)
    for name in ('stage','verify-inputs','verify-artifact'):
        s=sub.add_parser(name)
        s.add_argument('--work-root',default=os.getenv('CRAFT_WORK_ROOT'))
        if name=='stage':
            s.add_argument('--source',required=True);s.add_argument('--name')
        if name=='verify-artifact':
            s.add_argument('--path',required=True,help='outputs/... relative path')
            s.add_argument('--format',required=True,choices=['bytes','json','txt','md','csv','svg','wav','png','jpg','jpeg','pdf','docx','xlsx','pptx'])
            s.add_argument('--expected-sha256')
    return p

def required_path(value: str | None, label: str) -> Path:
    require(value is not None and value!='',f'missing {label}; no default/root is guessed')
    return absolute(value)

def storytold_version() -> str | None:
    # An installed plugin carries plugin.json; the source tree carries packaging/project.json.
    for name in ('plugin.json','packaging/project.json'):
        if (ROOT/name).is_file():
            value=load_json(ROOT/name)
            return value.get('version') if isinstance(value,dict) else None
    return None

def main(argv: list[str] | None=None) -> int:
    args=parser().parse_args(argv)
    try:
        cmd=args.command;code=0
        if cmd=='doctor':
            try: sdk=importlib.metadata.version('mcp')
            except importlib.metadata.PackageNotFoundError: sdk=None
            result={'storytold':storytold_version(),'python':sys.version.split()[0],'mcp_sdk':sdk,
                    'claude':shutil.which('claude'),'codex':shutil.which('codex'),
                    'native_apps_executed':False,'network_used':False}
        elif cmd=='apps': result={'apps':list(load_catalog().values())}
        elif cmd=='workspace-init': result=init_workspace(required_path(args.root,'root'))
        elif cmd=='inventory':
            result=inventory(required_path(args.bin_dir,'CRAFT_BIN_DIR'),selected(args.app),load_catalog())
            code=0 if result['all_present'] else 1
        elif cmd in {'preflight','probe','configure'}:
            apps=selected(args.app)
            if cmd=='probe':
                require(args.confirm_execution,'probe needs --confirm-execution; it starts one trusted native process')
                require(len(apps)==1,'probe one --app at a time so failures remain independent')
                require(bool(args.call_json)==bool(args.approve_call),'--call-json and --approve-call must be supplied together')
                # Reject destination collisions BEFORE starting a native process.
                output=local(args.output);require(output.parent.is_dir() and not output.exists(),'probe output must be a new file in an existing directory')
            pf=preflight(required_path(args.bin_dir,'CRAFT_BIN_DIR'),required_path(args.work_root,'CRAFT_WORK_ROOT'),
                         required_path(args.output_root,'CRAFT_OUTPUT_ROOT'),local(args.lock),apps,load_catalog(),args.acknowledge_unconfined)
            if cmd=='preflight': result=pf
            elif cmd=='configure': result=write_config(pf,local(args.evidence_dir),args.host,local(args.output))
            else:
                require(not output.is_relative_to(Path(pf['launches'][0]['working_directory'])),
                        'probe evidence output must be outside the native workspace')
                if args.call_json:
                    require(not local(args.call_json).is_relative_to(Path(pf['launches'][0]['working_directory'])),
                            'approved probe request must be outside the native workspace')
                call=load_json(local(args.call_json)) if args.call_json else None
                result=asyncio.run(probe(pf['launches'][0],timeout=args.timeout,call=call))
                create_new(output,encoded(result))
                code=0 if result['status'] in {'discovery_passed','discovery_and_call_passed'} else 1
        elif cmd=='stage': result=stage(required_path(args.work_root,'CRAFT_WORK_ROOT'),local(args.source),args.name)
        elif cmd=='verify-inputs': result=verify_inputs(required_path(args.work_root,'CRAFT_WORK_ROOT'))
        else: result=verify_artifact(required_path(args.work_root,'CRAFT_WORK_ROOT'),args.path,args.format,args.expected_sha256)
        sys.stdout.buffer.write(encoded(result));return code
    except (OSError,ValueError,TypeError,KeyError,OverflowError) as exc:
        print('storytold: '+str(exc),file=sys.stderr);return 1

if __name__=='__main__':
    raise SystemExit(main())
