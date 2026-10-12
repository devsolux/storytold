"""Generate new local host config from pins and matching native evidence.

No global settings merge, plugin auto-enablement, permission grants, or shell
startup modifications. Evidence is a consistency gate, not an authenticity root.
"""
from __future__ import annotations
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from .common import create_new,directory,digest,encoded,keys,load_json,require,text
from .probe import SDK_VERSION

MAX_EVIDENCE_AGE_DAYS=30

def validate_evidence(report: dict, launch: dict) -> None:
    require(isinstance(report,dict),'probe evidence must be an object')
    require(type(report.get('schema_version')) is int and report['schema_version']==1,'invalid probe schema')
    require(report.get('kind')=='native_mcp_probe' and report.get('probe_origin')=='native','synthetic or unrecognized evidence cannot activate native apps')
    for field,expected in [('app',launch['app']),('launch_fingerprint',launch['fingerprint']),
                           ('binary_sha256',launch['binary_sha256']),('source_revision',launch['source_revision']),
                           ('platform',launch['platform']),('working_directory',launch['working_directory']),
                           ('sdk_version',SDK_VERSION)]:
        require(report.get(field)==expected,f'stale/mismatched probe field: {field}')
    require(report.get('status')=='discovery_and_call_passed','initialize, discovery AND one approved smoke call must pass before config generation')
    checks=keys(report.get('checks'),{'initialize','tools_list','tool_call','sdk_context_exit','binary_unchanged'},label='probe checks')
    require(all(v is True for v in checks.values()),'probe contains incomplete/failed checks')
    captured=datetime.fromisoformat(text(report.get('captured_at'),'probe timestamp'))
    require(captured.tzinfo is not None,'probe timestamp must include timezone')
    age=(datetime.now(timezone.utc)-captured).total_seconds()
    require(0<=age<=MAX_EVIDENCE_AGE_DAYS*86400,'probe evidence is future-dated or older than thirty days')
    tools=report.get('tools');require(isinstance(tools,list) and bool(tools),'missing tools snapshot')
    require(digest(encoded(tools))==report.get('tools_sha256'),'modified tools snapshot')
    names=[]
    for tool in tools:
        require(isinstance(tool,dict),'invalid tool snapshot');names.append(text(tool.get('name'),'tool name',256))
        require(isinstance(tool.get('inputSchema'),dict),'missing input schema')
    require(len(names)==len(set(names)),'duplicate tool snapshot')
    call=keys(report.get('call'),{'request','result'},label='probe call evidence')
    require(digest(encoded(call))==report.get('call_sha256'),'modified call snapshot')
    keys(call['request'],{'name','arguments'},label='probe request')
    require(call['request']['name'] in names and isinstance(call['request']['arguments'],dict),'undiscovered/invalid probe request')
    require(isinstance(call['result'],dict) and call['result'].get('isError') is False,'native call error')
    require(isinstance(call['result'].get('content'),list),'missing native call content')
    require(isinstance(report.get('protocol_version'),str) and report['protocol_version'],'missing negotiated protocol')
    require(report.get('error') is None,'probe retained an unresolved error')

def generate(preflight: dict, evidence_dir: Path, host: str) -> bytes:
    directory(evidence_dir)
    if os.name != 'nt':
        require(evidence_dir.stat().st_mode & 0o077 == 0, 'probe evidence directory must be owner-only')
    launches=preflight.get('launches',[])
    require(preflight.get('ready_to_probe') is True and bool(launches),'missing successful preflight')
    require(len({x['app'] for x in launches})==len(launches),'duplicate launch')
    for launch in launches:
        require(not evidence_dir.is_relative_to(Path(launch['working_directory'])),
                'probe evidence must be outside the native workspace')
        validate_evidence(load_json(evidence_dir/(launch['app']+'.json')),launch)
    if host=='claude':
        return encoded({'mcpServers':{x['app']:{'command':x['command'],'args':x['args']} for x in launches}})
    require(host=='codex','only local Claude Code and Codex config are supported')
    out=['# Generated local native MCP entries; review before installing.\n',
         '# No plugin, permissions, global settings or unrelated servers are changed.\n']
    # JSON strings/arrays are compatible with TOML basic strings for these paths.
    for x in launches:
        out += ['\n[mcp_servers.'+x['app']+']\n',
                'command = '+json.dumps(x['command'],ensure_ascii=False)+'\n',
                'args = '+json.dumps(x['args'],ensure_ascii=False)+'\n',
                'cwd = '+json.dumps(x['working_directory'],ensure_ascii=False)+'\n']
    return ''.join(out).encode('utf-8')

def write_config(preflight: dict, evidence_dir: Path, host: str, output: Path) -> dict:
    data=generate(preflight,evidence_dir,host)
    if host=='claude':
        require(all(str(output.parent)==x['working_directory'] for x in preflight['launches']),
                'Claude config must be generated in the probed workspace; launch Claude Code there')
        require(output.name=='.mcp.json','Claude project config must be named .mcp.json')
    create_new(output,data)
    return {'output':str(output),'host':host,'servers':[x['app'] for x in preflight['launches']],
            'host_installation_verified':False,'os_isolation_verified':False,
            'notice':'New config only. Keep one registration per server. Complete native/host acceptance before business data.'}
