import asyncio
from copy import deepcopy
from datetime import datetime,timezone,timedelta
import json
import unittest
from unittest.mock import patch
from storytold_tools.probe import probe
from storytold_tools.configuration import validate_evidence,generate,write_config
from storytold_tools.common import encoded,StorytoldError
from tests.support import WorkspaceCase,FakeClient,Model,Page,successful_report

class ProbeTests(WorkspaceCase):
    def run_probe(self,client=None,call=True,timeout=1):
        c=client or FakeClient()
        return asyncio.run(probe(self.pf()['launches'][0],factory=lambda _:c,
                         call={'name':'inspect_fixture','arguments':{}} if call else None,timeout=timeout)),c
    def test_discovery_only_has_no_call(self):
        r,c=self.run_probe(call=False)
        self.assertEqual(r['status'],'discovery_passed');self.assertEqual(c.calls,[])
        self.assertFalse(r['checks']['tool_call'])
    def test_success_preserves_typed_result(self):
        r,c=self.run_probe()
        self.assertEqual(r['status'],'discovery_and_call_passed')
        self.assertIs(r['call']['result']['structuredContent']['ok'],True)
        self.assertEqual(r['probe_origin'],'synthetic_test');self.assertTrue(c.closed)
    def test_tool_error_never_retried(self):
        r,c=self.run_probe(FakeClient(error=True))
        self.assertEqual(r['status'],'tool_error');self.assertEqual(len(c.calls),1)
        self.assertFalse(r['retry_safe'])
    def test_timeout_marks_indeterminate_without_retry(self):
        r,c=self.run_probe(FakeClient(delay=0.2),timeout=0.01)
        self.assertEqual(r['status'],'indeterminate');self.assertEqual(len(c.calls),1);self.assertTrue(c.closed)
    def test_pagination_followed(self):
        pages=[Page([Model(name='other',inputSchema={})],'page2'),Page([Model(name='inspect_fixture',inputSchema={})])]
        r,c=self.run_probe(FakeClient(pages=pages));self.assertEqual(c.cursors,[None,'page2'])
        self.assertEqual(len(r['tools']),2)
    def test_pagination_cycle_fails(self):
        c=FakeClient(pages=[Page([Model(name='other',inputSchema={})],'same'),Page([],'same')])
        r,_=self.run_probe(c,call=False);self.assertEqual(r['status'],'failed')
    def test_duplicate_tools_fail(self):
        c=FakeClient(pages=[Page([Model(name='same',inputSchema={}),Model(name='same',inputSchema={})])])
        r,_=self.run_probe(c,call=False);self.assertEqual(r['status'],'failed')
    def test_empty_discovery_fails(self):
        r,_=self.run_probe(FakeClient(pages=[Page([])]),call=False);self.assertEqual(r['status'],'failed')
    def test_missing_tool_schema_fails(self):
        r,_=self.run_probe(FakeClient(pages=[Page([Model(name='a')])]),call=False);self.assertEqual(r['status'],'failed')
    def test_unknown_tool_not_called(self):
        c=FakeClient(pages=[Page([Model(name='other',inputSchema={})])])
        r,_=self.run_probe(c);self.assertEqual(c.calls,[]);self.assertEqual(r['status'],'failed')
    def test_sdk_context_failure_not_success(self):
        r,_=self.run_probe(FakeClient(fail_exit=True));self.assertNotIn(r['status'],['discovery_passed','discovery_and_call_passed'])
    def test_real_adapter_missing_sdk_not_stub_success(self):
        with patch('storytold_tools.probe.importlib.metadata.version',side_effect=__import__('importlib').metadata.PackageNotFoundError):
            r=asyncio.run(probe(self.pf()['launches'][0]))
        self.assertEqual(r['status'],'failed');self.assertIn('missing',r['error']['message'])
    def test_call_shape_rejects_extra_fields(self):
        with self.assertRaises(StorytoldError):
            asyncio.run(probe(self.pf()['launches'][0],call={'name':'inspect','arguments':{},'shell':'bad'},factory=lambda _:FakeClient()))
    def test_invalid_timeout_rejected(self):
        for value in (0,-1,121,float('inf'),float('nan')):
            with self.subTest(timeout=value),self.assertRaises(StorytoldError):
                asyncio.run(probe(self.pf()['launches'][0],timeout=value,factory=lambda _:FakeClient()))

class ConfigurationTests(WorkspaceCase):
    def report(self):
        launch=self.pf()['launches'][0];r=asyncio.run(successful_report(launch));return launch,r
    def test_valid_structural_evidence_accepted(self):
        x,r=self.report();validate_evidence(r,x)
    def test_synthetic_evidence_cannot_activate(self):
        x,r=self.report();r['probe_origin']='synthetic_test'
        with self.assertRaises(StorytoldError): validate_evidence(r,x)
    def test_stale_fingerprint_rejected(self):
        x,r=self.report();r['launch_fingerprint']='0'*64
        with self.assertRaises(StorytoldError): validate_evidence(r,x)
    def test_mismatched_binary_rejected(self):
        x,r=self.report();r['binary_sha256']='0'*64
        with self.assertRaises(StorytoldError): validate_evidence(r,x)
    def test_missing_call_rejected(self):
        x,r=self.report();r['status']='discovery_passed';r['call']=None
        with self.assertRaises(StorytoldError): validate_evidence(r,x)
    def test_old_and_future_evidence_rejected(self):
        x,r=self.report()
        for days in (-31,1):
            r['captured_at']=(datetime.now(timezone.utc)+timedelta(days=days)).isoformat()
            with self.subTest(days=days),self.assertRaises(StorytoldError): validate_evidence(r,x)
    def test_changed_tools_snapshot_rejected(self):
        x,r=self.report();r['tools'][0]['description']='modified'
        with self.assertRaises(StorytoldError): validate_evidence(r,x)
    def test_false_or_string_check_rejected(self):
        x,r=self.report()
        for value in (False,'true',1):
            r['checks']['tool_call']=value
            with self.subTest(value=value),self.assertRaises(StorytoldError): validate_evidence(r,x)
    def test_native_error_rejected(self):
        x,r=self.report();r['call']['result']['isError']=True
        with self.assertRaises(StorytoldError): validate_evidence(r,x)
    def test_claude_config_direct_and_no_grants(self):
        x,r=self.report();(self.evidence/'photocraft.json').write_bytes(encoded(r))
        data=generate(self.pf(),self.evidence,'claude');v=json.loads(data)
        self.assertEqual(set(v),{'mcpServers'})
        self.assertEqual(v['mcpServers']['photocraft']['command'],x['command'])
    def test_codex_config_is_valid_toml(self):
        import tomllib
        x,r=self.report();(self.evidence/'photocraft.json').write_bytes(encoded(r))
        v=tomllib.loads(generate(self.pf(),self.evidence,'codex').decode())
        self.assertEqual(v['mcp_servers']['photocraft']['cwd'],str(self.work))
        self.assertNotIn('permissions',v)
    def test_config_never_overwrites_existing_file(self):
        x,r=self.report();(self.evidence/'photocraft.json').write_bytes(encoded(r))
        p=self.work/'.mcp.json';p.write_bytes(b'preserve settings')
        with self.assertRaises(StorytoldError): write_config(self.pf(),self.evidence,'claude',p)
        self.assertEqual(p.read_bytes(),b'preserve settings')
    def test_claude_wrong_workspace_rejected(self):
        x,r=self.report();(self.evidence/'photocraft.json').write_bytes(encoded(r))
        with self.assertRaises(StorytoldError): write_config(self.pf(),self.evidence,'claude',self.base/'.mcp.json')


class EvidenceIntegrityTests(WorkspaceCase):
    def test_changed_successful_call_snapshot_rejected(self):
        launch=self.pf()['launches'][0]
        report=asyncio.run(successful_report(launch))
        report['call']['result']['structuredContent']['count']=999
        with self.assertRaises(StorytoldError):
            validate_evidence(report,launch)

    def test_omitted_native_error_indicator_rejected(self):
        from storytold_tools.common import digest
        launch=self.pf()['launches'][0]
        report=asyncio.run(successful_report(launch))
        del report['call']['result']['isError']
        report['call_sha256']=digest(encoded(report['call']))
        with self.assertRaises(StorytoldError):
            validate_evidence(report,launch)

    def test_evidence_in_native_workspace_rejected(self):
        launch=self.pf()['launches'][0]
        report=asyncio.run(successful_report(launch))
        (self.work/'receipts/photocraft.json').write_bytes(encoded(report))
        with self.assertRaises(StorytoldError):
            generate(self.pf(),self.work/'receipts','claude')

    def test_world_readable_evidence_directory_rejected(self):
        import os
        if os.name=='nt':
            self.skipTest('POSIX permission test; Windows requires ACL acceptance')
        launch=self.pf()['launches'][0]
        report=asyncio.run(successful_report(launch))
        (self.evidence/'photocraft.json').write_bytes(encoded(report))
        self.evidence.chmod(0o755)
        with self.assertRaises(StorytoldError):
            generate(self.pf(),self.evidence,'claude')
