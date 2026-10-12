"""Allowlisted, deterministic packaging; no host/network execution.

Generated file ownership, staged replacement, read-only drift checking,
explicit disposable trees and reproducible ZIPs.
"""
from __future__ import annotations
from contextlib import contextmanager
import io
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile
import zipfile
from .common import ROOT,absolute,child,create_new,digest,directory,encoded,keys,load_json,require,snapshot
from .catalog import load_catalog,templates

BUILD_MARKER='.storytold-build.json'
DISPOSABLE_MARKER='.storytold-disposable.json'
FIXED_TIME=(2026,10,12,0,0,0)


def project(root: Path=ROOT) -> dict:
    p=keys(load_json(root/'packaging/project.json'),{'name','version','marketplace','repository','description','license'},label='project')
    require(p['name']=='storytold' and p['marketplace']=='devsolux-storytold' and p['repository']=='devsolux/storytold','project identity mismatch')
    require(isinstance(p['version'],str) and re.fullmatch(r'\d+\.\d+\.\d+',p['version']),'expected semantic release version')
    return p

def allowlist(root: Path=ROOT) -> dict:
    data=keys(load_json(root/'packaging/files.json'),{'schema_version','source','plugin'},label='file allowlist')
    require(type(data['schema_version']) is int and data['schema_version']==1,'unsupported file allowlist')
    for key in ('source','plugin'):
        require(isinstance(data[key],list) and len(data[key])==len(set(data[key])),'invalid/duplicate file allowlist')
        for name in data[key]:
            require(isinstance(name,str),'allowlist names must be strings');child(root,name)
            require(not name.startswith(('plugins/','dist/','.build/','.venv/')),'generated/private path in source allowlist')
            require(not Path(name).name.startswith('.env') and not name.endswith(('.key','.pem','.whl','.pyc')),'private/binary dependency input rejected')
    require(set(data['plugin'])<=set(data['source']),'plugin inputs must be canonical source files')
    return data

def source_map(root: Path=ROOT) -> dict[str,bytes]:
    result={}
    allowed = allowlist(root)['source']
    # A new test/helper must not silently disappear from isolated runs or archives.
    # Other unlisted files (customer material, .env, private state) stay excluded.
    for folder in ('storytold_tools', 'scripts', 'tests'):
        for file in (root / folder).rglob('*.py'):
            name = file.relative_to(root).as_posix()
            require(name in allowed, 'unlisted canonical Python file; review packaging/files.json: ' + name)
    for name in allowed:
        result[name]=snapshot(child(root,name),limit=8*1024*1024,body=True)[2] or b''
    return result

def render(root: Path=ROOT) -> dict[str,bytes]:
    p=project(root);inputs=source_map(root)
    result={name:inputs[name] for name in allowlist(root)['plugin']}
    result['README.md']=inputs['packaging/README.plugin.md.in']
    for name,data in templates(load_catalog(root)).items():
        result['config/'+name]=data
    url='https://github.com/'+p['repository']
    common={'name':p['name'],'version':p['version'],'description':p['description'],
            'author':{'name':'devsolux'},'homepage':url,'license':p['license'],
            'repository':url,'keywords':['craft','native-mcp','local','headless','workflows']}
    interface={'displayName':'Storytold','shortDescription':'Local native Craft workflows and integration checks',
               'longDescription':'One craft Skill for twelve local, headless Craft MCP servers: staged copies, '
                                 'native edits, deliberate exports and verified files. Craft apps are not bundled.',
               'developerName':'devsolux','category':'Productivity','websiteURL':url}
    # Portable root manifest; Codex reads extensions.com.openai, so no .codex-plugin overlay is emitted.
    result['plugin.json']=encoded({'$schema':'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json',**common,
                                  'extensions':{'com.openai':{'interface':interface}}})
    result['.claude-plugin/plugin.json']=encoded(common)
    require('.mcp.json' not in result and 'mcp.json' not in result,'unverified native config cannot auto-activate in the distributed plugin')
    result[BUILD_MARKER]=encoded({'schema_version':1,'generator':'storytold_tools.build','version':p['version'],
                                 'files':{name:digest(body) for name,body in sorted(result.items())}})
    return result

def tree(root: Path) -> dict[str,bytes]:
    directory(root);result={}
    for p in sorted(root.rglob('*')):
        absolute(p)
        if p.is_dir(): continue
        require(p.is_file() and p.stat().st_nlink==1,'non-regular or hard-linked build file')
        result[p.relative_to(root).as_posix()]=snapshot(p,limit=32*1024*1024,body=True)[2] or b''
    return result

def ensure_owned(target: Path) -> None:
    absolute(target)
    if not target.exists(): return
    actual=tree(target)
    require(BUILD_MARKER in actual,'refusing unowned generated directory')
    m=keys(load_json(target/BUILD_MARKER),{'schema_version','generator','version','files'},label='build marker')
    require(type(m['schema_version']) is int and m['schema_version']==1 and m['generator']=='storytold_tools.build','unrecognized build ownership')
    require(isinstance(m['files'],dict),'invalid ownership files')
    require(set(actual)==set(m['files'])|{BUILD_MARKER},'unexpected/missing generated files; preserve local edits')
    expected_dirs=set()
    for name,h in m['files'].items():
        child(target,name)
        require(digest(actual[name])==h,f'locally modified generated file: {name}')
        expected_dirs.update(p.as_posix() for p in Path(name).parents if p!=Path('.'))
    for p in target.rglob('*'):
        if p.is_dir(): require(p.relative_to(target).as_posix() in expected_dirs,'unexpected generated directory; preserve it')

@contextmanager
def build_lock(root: Path):
    p=absolute(root/'.storytold-build.lock')
    fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        os.write(fd,str(os.getpid()).encode());os.close(fd);fd=-1
        yield
    finally:
        if fd>=0: os.close(fd)
        p.unlink()

def build(root: Path=ROOT,check: bool=False) -> Path:
    root=directory(root);target=absolute(root/'plugins/storytold');desired=render(root)
    if check:
        require(target.is_dir() and tree(target)==desired,'generated plugin drift; run make build and review changes')
        ensure_owned(target);return target
    with build_lock(root):
        ensure_owned(target)
        target.parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.storytold-stage-',dir=target.parent) as td:
            stage=Path(td)/'next';stage.mkdir()
            for name,data in desired.items():
                p=child(stage,name);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);p.chmod(0o644)
            ensure_owned(target)
            backup=Path(td)/'previous'
            if target.exists(): target.rename(backup)
            try: stage.rename(target)
            except BaseException:
                if backup.exists(): backup.rename(target)
                raise
    return target

def disposable(root: Path,name: str) -> Path:
    require(name in {'.build','dist'},'not a disposable build path')
    target=absolute(root/name)
    if not target.exists():
        target.mkdir(mode=0o700)
        create_new(target/DISPOSABLE_MARKER,encoded({'schema_version':1,'owner':'storytold','kind':name}))
    else:
        directory(target)
        marker=load_json(target/DISPOSABLE_MARKER)
        require(marker=={'schema_version':1,'owner':'storytold','kind':name},'unowned build output directory')
    return target

def clean(root: Path=ROOT) -> list[str]:
    targets=[]
    # Validate ALL targets before deleting any, including nested symlinks.
    for name in ('.build','dist'):
        target=absolute(root/name)
        if not target.exists(): continue
        directory(target)
        require(load_json(target/DISPOSABLE_MARKER)=={'schema_version':1,'owner':'storytold','kind':name},'refusing to clean unowned output')
        for p in target.rglob('*'): absolute(p)
        targets.append(target)
    for target in targets: shutil.rmtree(target)
    return [str(p) for p in targets]

def zip_bytes(files: dict[str,bytes]) -> bytes:
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(files.items()):
            require(not name.startswith('/') and '..' not in name.split('/') and '\\' not in name,'unsafe archive member')
            info=zipfile.ZipInfo(name,FIXED_TIME);info.create_system=3
            info.external_attr=(stat.S_IFREG|0o644)<<16;info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,data,compresslevel=9)
    return out.getvalue()

def publish_or_identical(path: Path,data: bytes) -> None:
    absolute(path)
    if path.exists():
        require(snapshot(path,limit=64*1024*1024,body=True)[2]==data,'different archive/output exists; preserve it or explicitly make clean')
    else: create_new(path,data,mode=0o644)

def package(root: Path=ROOT,kind: str='plugin') -> Path:
    require(kind in {'plugin','source'},'unknown package kind');p=project(root)
    plugin=tree(build(root,check=True))
    if kind=='plugin': files=plugin
    else:
        files={'storytold/'+name:body for name,body in source_map(root).items()}
        files.update({'storytold/plugins/storytold/'+name:body for name,body in plugin.items()})
    path=disposable(root,'dist')/f'storytold-{p["version"]}-{kind}.zip'
    data=zip_bytes(files);publish_or_identical(path,data)
    publish_or_identical(path.with_suffix('.zip.sha256'),(digest(data)+'  '+path.name+'\n').encode())
    return path
