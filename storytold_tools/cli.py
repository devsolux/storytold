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
from .doctor import default_app_dirs,report as connection_report
from .setup import load_state,remove as setup_remove,setup as run_setup,status as setup_status
from .probe import probe
from .workspace import init_workspace,stage,verify_inputs,verify_artifact


def recorded_state() -> dict:
    # Paths chosen by an earlier explicit `setup` run; CRAFT_* variables and flags still win.
    try: return load_state(dict(os.environ),Path.home())
    except (OSError,ValueError): return {}

def probe_timeout(value: str) -> float:
    """The probe accepts (0, 120] seconds; refuse anything else before setup downloads and stages."""
    try:
        seconds = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError('expected seconds') from exc
    if not 0 < seconds <= 120:
        raise argparse.ArgumentTypeError('must be more than 0 and at most 120 seconds')
    return seconds

def parser() -> argparse.ArgumentParser:
    st=recorded_state()
    def default(env: str,key: str) -> str | None: return os.getenv(env) or st.get(key)
    p=argparse.ArgumentParser(description='Local Craft integration helpers. No MCP server; apps are installed only by the explicit setup command.')
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('doctor',help='Report capabilities and per-app MCP connection gaps without executing or installing hosts/apps')
    sub.add_parser('apps',help='Show the thirteen source-documented app entries')
    s=sub.add_parser('setup',help='Explicit install (macOS, Linux x86_64, Windows x64): download reviewed <app>-cli releases, verify, pin, probe and register with codex/claude')
    s.add_argument('--app',action='append',help='App to set up (repeatable)');s.add_argument('--all',action='store_true',help='All thirteen apps')
    s.add_argument('--acknowledge-unconfined',action='store_true',help='Also register apps without file-root flags; NOT evidence of isolation')
    s.add_argument('--host',action='append',choices=['codex','claude'],help='Limit registration to one host (default: every host CLI on PATH)')
    s.add_argument('--skip-probe',action='store_true',help='Register without the official-SDK native probe (binary stays unverified)')
    s.add_argument('--trust-upstream-sums',action='store_true',help='Linux/Windows: proceed on the manifest and SHA256SUMS.txt when no Sigstore bundle or cosign is available')
    s.add_argument('--upgrade',action='store_true',help='Replace an already installed binary with the manifest release')
    s.add_argument('--replace',action='store_true',help='Replace a differing existing host registration of the same name; the previous entry is restored if the new one cannot be added')
    s.add_argument('--dry-run',action='store_true',help='Preview: with install, the downloads, paths and registrations; with --remove, exactly what would be unregistered or deleted. Changes nothing')
    s.add_argument('--remove',action='store_true',help='Unregister and delete the selected apps that Storytold provably manages (workspace is kept); combine with --dry-run for a read-only preview')
    s.add_argument('--list',action='store_true',help='Show manifest, installed, pinned and registered state')
    s.add_argument('--timeout',type=probe_timeout,default=60,help='Probe timeout in seconds, at most 120')
    for flag,key in (('--bin-dir','bin_dir'),('--work-root','work_root'),('--lock','lock'),('--evidence-dir','evidence_dir')):
        s.add_argument(flag,help=f'Override the recorded/default {key}')
    s=sub.add_parser('workspace-init',help='Create a NEW private inputs/outputs workspace')
    s.add_argument('--root',required=True)
    s=sub.add_parser('inventory',help='Hash installed binaries without executing them')
    s.add_argument('--bin-dir',default=default('CRAFT_BIN_DIR','bin_dir'));s.add_argument('--app',action='append')
    for name in ('preflight','probe','configure'):
        s=sub.add_parser(name,help={'preflight':'Validate roots and reviewed binary pins; no execution',
                                   'probe':'Explicit native initialize/tools-list and optional single smoke call',
                                   'configure':'Create NEW host config after matching native discovery+call evidence'}[name])
        s.add_argument('--bin-dir',default=default('CRAFT_BIN_DIR','bin_dir'))
        s.add_argument('--work-root',default=default('CRAFT_WORK_ROOT','work_root'))
        s.add_argument('--output-root',default=os.getenv('CRAFT_OUTPUT_ROOT'),help='Default: CRAFT_OUTPUT_ROOT, else <work root>/outputs')
        s.add_argument('--lock',default=default('CRAFT_LOCK','lock'),help='Installation lock (default: CRAFT_LOCK or the path recorded by setup)')
        s.add_argument('--app',action='append')
        s.add_argument('--acknowledge-unconfined',action='store_true',help='Explicitly acknowledge OS-only scope; NOT evidence of isolation')
        if name=='probe':
            s.add_argument('--confirm-execution',action='store_true')
            s.add_argument('--timeout',type=probe_timeout,default=20)
            s.add_argument('--call-json',help='One operator-reviewed, fixture-only native tools/call request')
            s.add_argument('--approve-call',action='store_true',help='Approve that exact call; annotations alone never authorize it')
            s.add_argument('--output',required=True,help='New evidence file, never overwritten')
        if name=='configure':
            s.add_argument('--host',choices=['claude','codex'],required=True)
            s.add_argument('--evidence-dir',default=default('CRAFT_EVIDENCE_DIR','evidence_dir'))
            s.add_argument('--output',required=True)
    for name in ('stage','verify-inputs','verify-artifact'):
        s=sub.add_parser(name)
        s.add_argument('--work-root',default=default('CRAFT_WORK_ROOT','work_root'))
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
                    'connections':connection_report(os.environ,Path.cwd(),Path.home(),default_app_dirs(Path.home())),
                    'native_apps_executed':False,'network_used':False}
        elif cmd=='apps': result={'apps':list(load_catalog().values())}
        elif cmd=='setup':
            common=dict(hosts=args.host,env=dict(os.environ),home=Path.home(),bin_dir=args.bin_dir,work_root=args.work_root,
                        lock=args.lock,evidence_dir=args.evidence_dir)
            chosen={name for name in ('app','all','remove','dry_run','upgrade','replace','skip_probe','trust_upstream_sums','acknowledge_unconfined')
                    if getattr(args,name)}
            if args.list:
                require(not chosen,'--list is read-only and takes no other setup flags')
                result=setup_status(**common)
            else:
                require(args.app or args.all,'choose --app <name> (repeatable) or --all')
                require(not (args.app and args.all),'--all and --app select differently; choose one')
                apps=selected(args.app)
                if args.remove:
                    clash=sorted(chosen&{'upgrade','replace','skip_probe','trust_upstream_sums','acknowledge_unconfined'})
                    require(not clash,'--remove cannot be combined with --'+', --'.join(c.replace('_','-') for c in clash))
                    result=setup_remove(apps,dry_run=args.dry_run,**common)
                    code=0 if result['status']=='ok' else 1
                else:
                    result=run_setup(apps,acknowledge_unconfined=args.acknowledge_unconfined,skip_probe=args.skip_probe,upgrade=args.upgrade,
                                     replace=args.replace,dry_run=args.dry_run,timeout=args.timeout,trust_upstream_sums=args.trust_upstream_sums,**common)
                    code=0 if result.get('status','passed')=='passed' else 1
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
            # The output root is always <work root>/outputs, so a --work-root override must not pair with a recorded one.
            output_root=args.output_root or (str(Path(args.work_root)/'outputs') if args.work_root else None)
            pf=preflight(required_path(args.bin_dir,'CRAFT_BIN_DIR'),required_path(args.work_root,'CRAFT_WORK_ROOT'),
                         required_path(output_root,'CRAFT_OUTPUT_ROOT'),required_path(args.lock,'CRAFT_LOCK (--lock)'),apps,load_catalog(),args.acknowledge_unconfined)
            if cmd=='preflight': result=pf
            elif cmd=='configure': result=write_config(pf,required_path(args.evidence_dir,'CRAFT_EVIDENCE_DIR (--evidence-dir)'),args.host,local(args.output))
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
