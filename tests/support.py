"""Synthetic fixtures only. Never evidence about installed Craft binaries."""
from __future__ import annotations
import asyncio
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from storytold_tools.catalog import APP_IDS,load_catalog,platform_id,preflight
from storytold_tools.common import encoded,digest
from storytold_tools.workspace import init_workspace

class WorkspaceCase(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='storytold-test-')
        self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name).resolve()
        self.bin=self.base/'native binaries';self.bin.mkdir(mode=0o755)
        self.work=self.base/'work with spaces';init_workspace(self.work)
        self.evidence=self.base/'evidence';self.evidence.mkdir(mode=0o700)
        self.lock=self.base/'pins.json'
        self.catalog=load_catalog()
        self.pins={'schema_version':1,'platform':platform_id(),'apps':{}}
        import hashlib,os
        for app in APP_IDS:
            name=app+'-cli'+('.exe' if os.name=='nt' else '')
            p=self.bin/name;p.write_bytes(b'SYNTHETIC; MUST NOT EXECUTE '+app.encode());p.chmod(0o755)
            self.pins['apps'][app]={'revision':hashlib.sha1(app.encode()).hexdigest(),'version':'synthetic-test-only','sha256':digest(p.read_bytes())}
        self.save_pins()
    def save_pins(self): self.lock.write_bytes(encoded(self.pins))
    def pf(self,apps=None,ack=True):
        return preflight(self.bin,self.work,self.work/'outputs',self.lock,apps or ['photocraft'],self.catalog,ack)

class Model:
    def __init__(self,**value): self.value=value
    def model_dump(self,**kwargs):
        assert kwargs=={'mode':'json','by_alias':True,'exclude_none':True}
        return deepcopy(self.value)

class Page:
    def __init__(self,tools,next_cursor=None): self.tools=tools;self.next_cursor=next_cursor

class Result(Model):
    def __init__(self,error=False):
        super().__init__(content=[{'type':'text','text':'synthetic fixture'}],
                         structuredContent={'count':3,'ok':True,'missing':None},isError=error)
        self.is_error=error

class FakeClient:
    """SDK shape stub; not a server, not a real transport test."""
    protocol_version='2025-11-25'
    server_info=Model(name='synthetic-fixture',version='not-a-Craft-binary')
    server_capabilities=Model(tools={})
    def __init__(self,pages=None,error=False,delay=0,fail_exit=False):
        self.pages=pages if pages is not None else [Page([Model(name='inspect_fixture',inputSchema={'type':'object'})])]
        self.error=error;self.delay=delay;self.fail_exit=fail_exit;self.calls=[];self.cursors=[];self.closed=False
    async def __aenter__(self): return self
    async def __aexit__(self,*args):
        self.closed=True
        if self.fail_exit: raise RuntimeError('synthetic exit failure')
    async def list_tools(self,cursor=None):
        self.cursors.append(cursor)
        return self.pages[min(len(self.cursors)-1,len(self.pages)-1)]
    async def call_tool(self,name,arguments):
        self.calls.append((name,arguments))
        if self.delay: await asyncio.sleep(self.delay)
        return Result(self.error)

async def successful_report(launch):
    from storytold_tools.probe import probe
    c=FakeClient()
    r=await probe(launch,call={'name':'inspect_fixture','arguments':{}},factory=lambda _:c)
    # For parser rejection tests ONLY, emulate the native-origin shape. This is
    # never written into the shipped runtime or reported as actual native proof.
    r['probe_origin']='native'
    return r
