"""Short-lived official-SDK conformance client, never a gateway or tool router.

Only discovery is performed by default. One explicitly approved, discovered
native tool can be exercised using a non-sensitive fixture. No mutation retry,
server-side sampling, elicitation, or arbitrary process selection is implemented.
"""
from __future__ import annotations
import asyncio
from datetime import datetime, timezone
import importlib.metadata
from typing import Any, Callable
from .common import MAX_JSON, StorytoldError, digest, encoded, keys, require, snapshot, text

SDK_VERSION='2.3.0'
MAX_TOOLS=10000
MAX_PAGES=100

def sdk_factory(launch: dict):
    try:
        require(importlib.metadata.version('mcp')==SDK_VERSION,
                f'probe requires the reviewed mcp=={SDK_VERSION}; run make setup-probe in the source repository')
        from mcp import Client, StdioServerParameters
    except (ImportError,importlib.metadata.PackageNotFoundError) as exc:
        raise StorytoldError('optional MCP SDK is missing; install requirements-probe.txt explicitly') from exc
    params=StdioServerParameters(command=launch['command'],args=launch['args'],cwd=launch['working_directory'])
    # Native plan explicitly calls for initialize negotiation. Do not hard-code a
    # wire version or manually implement the stdio transport.
    return Client(params,mode='legacy')

def serialized(value: Any) -> Any:
    if value is None: return None
    # Official SDK protocol models are Pydantic models. Preserve wire aliases and
    # typed content instead of converting every result to an untyped string.
    result=value.model_dump(mode='json',by_alias=True,exclude_none=True)
    require(len(encoded(result))<=MAX_JSON,'native message exceeds snapshot limit')
    return result

def validate_call(call: Any) -> dict:
    keys(call,{'name','arguments'},label='approved probe call')
    text(call['name'],'native tool name',256)
    require(isinstance(call['arguments'],dict),'native tool arguments must be an object')
    require(len(encoded(call))<=65536,'probe call exceeds argument limit')
    return call

async def probe(launch: dict, *, timeout: float=20, call: dict | None=None,
                factory: Callable | None=None) -> dict:
    require(type(timeout) in {int,float} and 0<timeout<=120,'probe timeout must be in (0,120] seconds')
    if call is not None: validate_call(call)
    result={'schema_version':1,'kind':'native_mcp_probe','app':launch['app'],
            'launch_fingerprint':launch['fingerprint'],'binary_sha256':launch['binary_sha256'],
            'source_revision':launch['source_revision'],'platform':launch['platform'],
            'working_directory':launch['working_directory'],
            'captured_at':datetime.now(timezone.utc).isoformat(),'sdk_version':SDK_VERSION,
            'probe_origin':'native' if factory is None else 'synthetic_test',
            'checks':{'initialize':False,'tools_list':False,'tool_call':False,'sdk_context_exit':False,'binary_unchanged':False},
            'call':None,'tools':[],'status':'failed','retry_safe':False,
            'acceptance_gates_passed':[], 'os_isolation_verified':False,'headless_behavior_verified':False}
    call_started=False
    try:
        # Check equality immediately before launch as well as in preflight.
        if factory is None:
            require(snapshot(launch['command'])[0]==launch['binary_sha256'],'binary changed since preflight')
        async with asyncio.timeout(timeout):
            async with (factory or sdk_factory)(launch) as client:
                result['protocol_version']=client.protocol_version
                text(result['protocol_version'],'negotiated protocol version',64)
                result['server_info']=serialized(client.server_info)
                result['server_capabilities']=serialized(client.server_capabilities)
                result['checks']['initialize']=True
                cursor=None; cursors=set(); names=set(); byte_count=0
                for _ in range(MAX_PAGES):
                    page=await client.list_tools(cursor=cursor)
                    for tool in page.tools:
                        wire=serialized(tool)
                        require(isinstance(wire,dict),'native tool is not an object')
                        name=text(wire.get('name'),'native tool name',256)
                        require(name not in names,'duplicate native tool name across pages')
                        require(isinstance(wire.get('inputSchema'),dict),'native tool has no input schema')
                        names.add(name); result['tools'].append(wire)
                        byte_count+=len(encoded(wire))
                        require(len(names)<=MAX_TOOLS and byte_count<=MAX_JSON//2,'tool discovery limit exceeded')
                    cursor=page.next_cursor
                    if cursor is None: break
                    text(cursor,'pagination cursor',4096)
                    require(cursor not in cursors,'native tools/list pagination loop')
                    cursors.add(cursor)
                else:
                    raise StorytoldError('native tools/list page limit exceeded')
                require(bool(names),'native server listed no tools')
                result['checks']['tools_list']=True
                result['tools_sha256']=digest(encoded(result['tools']))
                if call is not None:
                    require(call['name'] in names,'requested probe tool is absent from live discovery')
                    call_started=True
                    native=await client.call_tool(call['name'],call['arguments'])
                    wire_result=serialized(native)
                    require(isinstance(wire_result,dict) and isinstance(wire_result.get('content'),list),
                            'native tool result must preserve a content list')
                    result['call']={'request':call,'result':wire_result}
                    result['call_sha256']=digest(encoded(result['call']))
                    require(native.is_error is False,'native tool returned isError=true or missing error state')
                    result['checks']['tool_call']=True
            result['checks']['sdk_context_exit']=True
        if factory is None:
            require(snapshot(launch['command'])[0]==launch['binary_sha256'],'binary changed during probe')
        result['checks']['binary_unchanged']=True
        result['status']='discovery_and_call_passed' if call is not None else 'discovery_passed'
    except Exception as exc:
        result['error']={'type':type(exc).__name__,'message':str(exc)[:1000]}
        result['status']='indeterminate' if call_started else 'failed'
        if result['call'] is not None and result['call']['result'].get('isError') is True:
            result['status']='tool_error'
    # This does not measure stdout purity, actual EOF exit code, OS isolation,
    # GUI non-attachment, export correctness or original preservation.
    return result
