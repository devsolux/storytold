"""Safe staging and explicitly limited independent artifact checks, not app engines."""
from __future__ import annotations
from datetime import datetime, timezone
import io
import os
from pathlib import Path
import struct
import uuid
import wave
import xml.etree.ElementTree as ET
import zipfile
import zlib
from .common import absolute,child,create_new,digest,directory,encoded,keys,load_json,parse_json,regular,require,sha,snapshot,text,StorytoldError

MARKER='.storytold-workspace.json'
STAGE_LIMIT=128*1024*1024

def init_workspace(root: Path) -> dict:
    root=absolute(root); directory(root.parent)
    require(not root.exists(), 'workspace must be a new directory; existing folders are never adopted')
    require(root!=Path.home() and root!=Path(root.anchor), 'refusing home/filesystem root')
    root.mkdir(mode=0o700)
    # A partial failure leaves a clearly incomplete directory, never deletes user data.
    for part in ('inputs','outputs','receipts'): (root/part).mkdir(mode=0o700)
    marker={'schema_version':1,'id':str(uuid.uuid4()),'created_at':datetime.now(timezone.utc).isoformat()}
    create_new(root/MARKER,encoded(marker))
    return {'root':str(root),'output_root':str(root/'outputs'),**marker}

def open_workspace(root: Path) -> dict:
    directory(root)
    marker=keys(load_json(root/MARKER), {'schema_version','id','created_at'}, label='workspace marker')
    require(type(marker['schema_version']) is int and marker['schema_version']==1, 'unsupported workspace version')
    require(str(uuid.UUID(marker['id']))==marker['id'], 'invalid workspace id')
    dt=datetime.fromisoformat(marker['created_at']); require(dt.tzinfo is not None,'workspace timestamp must include timezone')
    for path in (root,root/'inputs',root/'outputs',root/'receipts'):
        directory(path)
        if os.name!='nt': require(path.stat().st_mode & 0o077 == 0, 'workspace directories must be owner-only')
    return marker

def stage(root: Path, source: Path, name: str | None=None) -> dict:
    ws=open_workspace(root); source=regular(source)
    require(not source.is_relative_to(root), 'stage originals from outside this workspace')
    name=text(name or source.name,'staged filename',255)
    require('/' not in name and '\\' not in name and not name.startswith('.'), 'staged filename must be one visible basename')
    dest=child(root/'inputs',name)
    h,n,data=snapshot(source,limit=STAGE_LIMIT,body=True)
    require(n>0,'empty input')
    create_new(dest,data or b'',mode=0o400)
    receipt={'schema_version':1,'kind':'staged_input','workspace_id':ws['id'],'source':str(source),
             'staged_path':'inputs/'+name,'sha256':h,'bytes':n}
    receipt_path=root/'receipts'/('input-'+uuid.uuid4().hex+'.json')
    try:
        create_new(receipt_path,encoded(receipt))
    except (OSError, ValueError) as exc:
        raise StorytoldError(f'copy preserved at {dest}; staging receipt failed, so staging is incomplete') from exc
    return {**receipt,'receipt':str(receipt_path),'os_immutable':False}

def verify_inputs(root: Path) -> dict:
    ws=open_workspace(root); rows=[]; tracked=set()
    receipts = list((root/'receipts').glob('input-*.json'))
    require(len(receipts) <= 4096, 'input receipt count exceeds limit')
    for p in sorted(receipts):
        r=keys(load_json(p),{'schema_version','kind','workspace_id','source','staged_path','sha256','bytes'},label='input receipt')
        require(type(r['schema_version']) is int and r['schema_version']==1 and r['kind']=='staged_input','invalid receipt')
        require(r['workspace_id']==ws['id'],'cross-workspace input receipt')
        sha(r['sha256']); require(type(r['bytes']) is int and r['bytes']>0,'invalid receipt size')
        require(r['staged_path'].startswith('inputs/'),'staged receipt is outside inputs')
        require(len(r['staged_path'].split('/'))==2,'staged input must be a basename')
        require(r['staged_path'] not in tracked, 'duplicate receipt for one staged input')
        tracked.add(r['staged_path'])
        original=absolute(r['source']); require(not original.is_relative_to(root),'original must remain outside workspace')
        for label,path in [('original',original),('copy',child(root,r['staged_path']))]:
            h,n,_=snapshot(path)
            require((h,n)==(r['sha256'],r['bytes']),f'{label} changed: {path.name}')
        rows.append({'staged_path':r['staged_path'],'unchanged':True})
    require(bool(rows),'no staged input receipts; nothing was checked')
    actual=set()
    for file in (root/'inputs').iterdir():
        regular(file, multiple_links=False)
        actual.add('inputs/'+file.name)
    require(actual==tracked, 'staged input files and receipts differ; an input/receipt may be missing or untracked')
    return {'schema_version':1,'workspace_id':ws['id'],'inputs':rows,'all_unchanged':True}

def xml_root(data: bytes) -> ET.Element:
    require(len(data) <= 8 * 1024 * 1024, 'XML byte limit exceeded')
    # Restrict this independent structural check to UTF-8. This rejects UTF-16/32
    # NUL-interleaved declarations that would evade a raw ASCII DTD scan.
    decoded = data.decode('utf-8-sig')
    require('\x00' not in decoded, 'XML structural inspection requires UTF-8 without NUL')
    require(b'<!DOCTYPE' not in data.upper() and b'<!ENTITY' not in data.upper(),'DTD/entity XML is not accepted')
    try:
        return ET.fromstring(data)
    except ET.ParseError as exc:
        raise StorytoldError('malformed XML document') from exc

def inspect_bytes(data: bytes, fmt: str) -> tuple[str,dict]:
    """Return the limited check level and observed facts. Never claim fidelity."""
    if fmt=='json':
        obj=parse_json(data);return 'parsed',{'json_type':type(obj).__name__}
    if fmt in {'txt','md','csv'}:
        s=data.decode('utf-8');require('\x00' not in s,'NUL in text');return 'utf8_only',{'characters':len(s)}
    if fmt=='svg':
        root=xml_root(data)
        require(root.tag in {'svg','{http://www.w3.org/2000/svg}svg'},'not an SVG document')
        return 'structural_only',{'root':root.tag,'width':root.get('width'),'height':root.get('height')}
    if fmt=='wav':
        with wave.open(io.BytesIO(data),'rb') as f:
            channels,rate,frames=f.getnchannels(),f.getframerate(),f.getnframes()
            require(channels>0 and rate>0 and frames>0,'invalid/empty WAV')
            expected=frames*channels*f.getsampwidth()
            require(len(f.readframes(frames))==expected,'truncated WAV')
        return 'parsed_pcm',{'channels':channels,'sample_rate':rate,'frames':frames,'duration_seconds':frames/rate}
    if fmt in {'docx','xlsx','pptx'}:
        expected={'docx':'word/document.xml','xlsx':'xl/workbook.xml','pptx':'ppt/presentation.xml'}[fmt]
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            infos=z.infolist(); names=[i.filename for i in infos]
            require(len(infos)<=4096 and len(names)==len(set(names)), 'ZIP member limit or duplicate name')
            require(sum(i.file_size for i in infos)<=64*1024*1024,'ZIP expansion limit')
            require(all(i.file_size<=8*1024*1024 for i in infos),'ZIP member byte limit')
            require(all(not i.flag_bits & 1 for i in infos),'encrypted ZIP not accepted')
            for name in names:
                require(not name.startswith('/') and '\\' not in name and '..' not in name.split('/'),'unsafe ZIP path')
            require('[Content_Types].xml' in names and expected in names,'not the expected OOXML package')
            require(z.testzip() is None,'ZIP CRC failure')
            for info in infos:
                if info.filename.endswith(('.xml','.rels')): xml_root(z.read(info))
        return 'structural_only',{'zip_members':len(names),'main_part':expected}
    if fmt=='png':
        require(len(data)>=33 and data[:8]==b'\x89PNG\r\n\x1a\n' and data[12:16]==b'IHDR','not PNG')
        width,height=struct.unpack('>II',data[16:24]);require(width>0 and height>0,'invalid PNG dimensions')
        return 'signature_only',{'width':width,'height':height}
    if fmt=='pdf':
        require(data.startswith(b'%PDF-') and b'%%EOF' in data[-2048:], 'missing PDF header/end marker')
        return 'signature_only',{}
    if fmt in {'jpeg','jpg'}:
        require(data.startswith(b'\xff\xd8\xff') and data.endswith(b'\xff\xd9'),'missing JPEG markers')
        return 'signature_only',{}
    require(fmt=='bytes','unsupported format; use bytes for a hash-only check and a real native verifier')
    return 'hash_only',{}

def verify_artifact(root: Path, relative: str, fmt: str, expected_sha256: str | None=None) -> dict:
    ws=open_workspace(root)
    require(relative.startswith('outputs/'),'only exported files in outputs/ may be verified')
    p=regular(child(root,relative),multiple_links=False)
    h,n,data=snapshot(p,limit=STAGE_LIMIT,body=True);require(n>0,'missing/empty output')
    if expected_sha256: require(h==sha(expected_sha256),'artifact digest mismatch')
    try:
        level,facts=inspect_bytes(data or b'',fmt)
    except (zipfile.BadZipFile, zipfile.LargeZipFile, zlib.error, wave.Error, EOFError, RuntimeError, NotImplementedError) as exc:
        raise StorytoldError('invalid or unsupported artifact container/audio encoding') from exc
    return {'schema_version':1,'workspace_id':ws['id'],'path':relative,'bytes':n,'sha256':h,
            'requested_checks_passed':True,'check_level':level,'facts':facts,
            'native_reopen_verified':False,'visual_review_verified':False,'format_fidelity_verified':False,
            'warnings':['These checks do not prove edit correctness, safe active content, or format fidelity.']}
