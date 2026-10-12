"""One reviewed launch catalog, never a duplicate native tool registry."""
from __future__ import annotations
from pathlib import Path
import os
import platform
import re
from .common import ROOT, absolute, directory, encoded, digest, keys, load_json, require, sha, snapshot, text

APP_IDS = ('photocraft','vectorcraft','filmcraft','lightcraft','pdfcraft','effectcraft',
           'designcraft','gridcraft','wordcraft','deckcraft','cadcraft','soundcraft')
ROOTED = {'photocraft','vectorcraft','effectcraft'}

def load_catalog(root: Path = ROOT) -> dict[str, dict]:
    raw = keys(load_json(root/'config/apps.json'), {'schema_version','basis','apps'}, label='catalog')
    require(type(raw['schema_version']) is int and raw['schema_version']==1, 'unsupported catalog version')
    require(isinstance(raw['apps'], list), 'catalog apps must be a list')
    result = {}
    for row in raw['apps']:
        keys(row, {'id','name','purpose','executable','confinement','args','repository','documentation'}, label='app')
        app = row['id']; require(app in APP_IDS and app not in result, 'unknown/duplicate app')
        require(row['executable']==app+'-cli', 'unexpected native executable')
        require(row['repository']=='https://github.com/storytold/'+app, 'unexpected upstream repository')
        for field in ('name','purpose','documentation'): text(row[field], field, 2048)
        require(row['confinement']==('read_write' if app in ROOTED else 'single_root' if app=='pdfcraft' else 'os_only'), 'unexpected root policy')
        # Integration flags, not engine commands. Keep the authorized native mode exact.
        expected = ['mcp']
        if app=='vectorcraft': expected += ['--headless']
        if app in ROOTED: expected += ['--automation-read-root','{work}','--automation-write-root','{outputs}']
        if app=='pdfcraft': expected += ['--root','{work}','--compact']
        if app=='lightcraft': expected += ['--compact']
        require(row['args']==expected, f'{app}: launch flags need a reviewed code/catalog change')
        result[app]=row
    require(set(result)==set(APP_IDS), 'catalog must contain all twelve apps')
    return result

def selected(apps: list[str] | None) -> list[str]:
    result = list(APP_IDS) if not apps else list(apps)
    require(len(result)==len(set(result)) and bool(result), 'duplicate/empty app selection')
    require(all(a in APP_IDS for a in result), 'unknown app selected')
    return [a for a in APP_IDS if a in result]

def platform_id() -> dict[str,str]:
    return {'system':platform.system(), 'machine':platform.machine()}

def load_lock(path: Path, apps: list[str]) -> dict:
    data = keys(load_json(path), {'schema_version','platform','apps'}, label='installation lock')
    require(type(data['schema_version']) is int and data['schema_version']==1, 'unsupported lock version')
    keys(data['platform'], {'system','machine'}, label='platform')
    require(data['platform']==platform_id(), 'lock platform does not match this machine')
    require(isinstance(data['apps'],dict) and set(data['apps'])<=set(APP_IDS), 'unknown lock app')
    require(set(apps)<=set(data['apps']), 'selected app is missing from lock')
    # Validate ALL supplied entries so malformed unused entries cannot pass unnoticed.
    for app, row in data['apps'].items():
        keys(row, {'revision','version','sha256'}, label=f'pin {app}')
        require(isinstance(row['revision'],str) and re.fullmatch('[0-9a-f]{40}|[0-9a-f]{64}',row['revision']), 'source revision must be an immutable full commit hash')
        require(len(set(row['revision']))>1, 'placeholder revision is not a source pin')
        text(row['version'], 'reviewed release/build version')
        require(row['version'].lower() not in {'unknown','latest','main','todo','unverified'}, 'unverified version label')
        sha(row['sha256'])
    return data

def executable(bin_dir: Path, app: str) -> Path:
    suffix = '.exe' if os.name=='nt' else ''
    p = absolute(bin_dir / (app+'-cli'+suffix))
    require(p.is_file() and os.access(p,os.X_OK), f'{app}: missing/non-executable native binary')
    require(p.stat().st_nlink==1, f'{app}: hard-linked binary requires a standalone trusted copy')
    if os.name!='nt':
        require(p.stat().st_mode & 0o022 == 0, f'{app}: binary is writable by group/others')
    return p

def inventory(bin_dir: Path, apps: list[str], catalog: dict[str,dict]) -> dict:
    directory(bin_dir)
    rows = []
    for app in apps:
        try:
            p=executable(bin_dir,app); h,n,_=snapshot(p)
            rows.append({'app':app,'path':str(p),'sha256':h,'bytes':n,'present':True})
        except (OSError,ValueError) as exc:
            rows.append({'app':app,'present':False,'error':str(exc)})
    return {'schema_version':1,'platform':platform_id(),'apps':rows,
            'all_present':all(r['present'] for r in rows),
            'version_and_provenance_verified':False,'executed_binaries':False}

def preflight(bin_dir: Path, work: Path, outputs: Path, lock_path: Path,
              apps: list[str], catalog: dict[str,dict], acknowledge_unconfined: bool=False) -> dict:
    from .workspace import open_workspace
    bin_dir=directory(bin_dir); work=directory(work); outputs=directory(outputs)
    ws=open_workspace(work)
    require(outputs==work/'outputs', 'CRAFT_OUTPUT_ROOT must be exactly CRAFT_WORK_ROOT/outputs')
    require(not bin_dir.is_relative_to(work) and not work.is_relative_to(bin_dir), 'binary directory and workspace must not overlap')
    if os.name!='nt':
        require(bin_dir.stat().st_mode & 0o022 == 0, 'binary directory is writable by group/others')
    lock_path=absolute(lock_path)
    require(not lock_path.is_relative_to(work), 'installation lock must be outside the native workspace')
    lock=load_lock(lock_path,apps)
    rows=[]
    for app in apps:
        row=catalog[app]; pin=lock['apps'][app]; p=executable(bin_dir,app)
        h,_,_=snapshot(p); require(h==pin['sha256'], f'{app}: executable hash mismatch; stop and review the installed binary')
        if row['confinement']=='os_only':
            require(acknowledge_unconfined, f'{app}: no verified native root flags; use tested OS isolation or explicitly acknowledge non-sensitive local testing')
        args=[{'{work}':str(work),'{outputs}':str(outputs)}.get(x,x) for x in row['args']]
        launch={'app':app,'command':str(p),'args':args,'binary_sha256':h,'source_revision':pin['revision'],
                'version':pin['version'],'platform':platform_id(),'workspace_id':ws['id'],
                'catalog_entry_sha256':digest(encoded(row)),'working_directory':str(work)}
        launch['fingerprint']=digest(encoded(launch))
        rows.append(launch)
    return {'schema_version':1,'ready_to_probe':True,'native_runtime_verified':False,
            'os_isolation_verified':False,'launches':rows,
            'warnings':['Root flags are not an OS sandbox; approvals remain with the host and operator.',
                        'Pins attest local equality, not publisher authenticity. Recheck before every session.']}

def templates(catalog: dict[str,dict]) -> dict[str,bytes]:
    defs={a:{'command':'${CRAFT_BIN_DIR}/'+r['executable'],
             'args':[{'{work}':'${CRAFT_WORK_ROOT}','{outputs}':'${CRAFT_OUTPUT_ROOT}'}.get(x,x) for x in r['args']]}
          for a,r in catalog.items()}
    return {'claude.mcp.example.json':encoded({'mcpServers':defs}),
            'portable.mcp.example.json':encoded({'$schema':'https://agent-plugins.org/schemas/1.0.0/mcp.schema.json',
                                                'mcpServers':{a:{'type':'stdio',**v} for a,v in defs.items()}})}
