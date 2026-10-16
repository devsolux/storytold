from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest
from storytold_tools.catalog import APP_IDS,load_catalog,selected,load_lock,inventory,templates,preflight
from storytold_tools.common import ROOT,encoded,StorytoldError
from tests.support import WorkspaceCase

class CatalogTests(WorkspaceCase):
    def test_catalog_has_all_thirteen(self):
        self.assertEqual(set(self.catalog),set(APP_IDS))
    def test_native_root_flags_exact(self):
        self.assertEqual(sum(a['confinement']=='read_write' for a in self.catalog.values()),5)
        self.assertEqual(sum(a['confinement']=='os_only' for a in self.catalog.values()),7)
        self.assertIn('--headless',self.catalog['vectorcraft']['args'])
    def test_roots_need_a_release_that_honours_them(self):
        # SoundCraft before 0.7.0 ignores unknown mcp flags, so an older or unreadable pin must not launch with roots.
        for label in ('0.6.1 (v0.6.1, synthetic)','synthetic-test-only','v0.6.9','0.7.0-rc1','٠.٧.٠','0.7.0abc'):
            self.pins['apps']['soundcraft']['version']=label;self.save_pins()
            with self.assertRaisesRegex(StorytoldError,'--upgrade --replace'): self.pf(['soundcraft'],ack=False)
        for label in ('0.7.0 (v0.7.0, synthetic)','v0.10.2'):
            self.pins['apps']['soundcraft']['version']=label;self.save_pins()
            x=self.pf(['soundcraft'],ack=False)['launches'][0]
            self.assertEqual(x['args'],['mcp','--automation-read-root',str(self.work),'--automation-write-root',str(self.work/'outputs')])
    def test_only_documented_compact_flags(self):
        self.assertEqual({a for a,r in self.catalog.items() if '--compact' in r['args']},{'pdfcraft','lightcraft'})
    def test_no_live_or_http_flags(self):
        for row in self.catalog.values():
            self.assertNotIn('--connect',row['args']);self.assertNotIn('--bridge',row['args'])
    def test_selection_rejects_duplicates_and_unknown(self):
        for value in (['gridcraft','gridcraft'],['unknown']):
            with self.assertRaises(StorytoldError): selected(value)
    def test_inventory_does_not_execute(self):
        r=inventory(self.bin,list(APP_IDS),self.catalog)
        self.assertTrue(r['all_present']);self.assertFalse(r['executed_binaries'])
    def test_inventory_reports_missing_independently(self):
        (self.bin/('gridcraft-cli'+('.exe' if os.name=='nt' else ''))).unlink()
        r=inventory(self.bin,['gridcraft','photocraft'],self.catalog)
        self.assertFalse(r['all_present']);self.assertTrue(r['apps'][1]['present'])
    def test_preflight_contains_absolute_exact_argv(self):
        pf=self.pf(['vectorcraft']);x=pf['launches'][0]
        self.assertEqual(x['args'][0:2],['mcp','--headless'])
        self.assertEqual(x['working_directory'],str(self.work))
        self.assertFalse(pf['native_runtime_verified'])
    def test_example_lock_is_not_accepted(self):
        with self.assertRaises(StorytoldError): load_lock(ROOT/'config/installations.lock.example.json',['photocraft'])
    def test_platform_mismatch_rejected(self):
        self.pins['platform']['system']='DifferentOS';self.save_pins()
        with self.assertRaises(StorytoldError): self.pf()
    def test_hash_mismatch_rejected(self):
        self.pins['apps']['photocraft']['sha256']='a'*64;self.save_pins()
        with self.assertRaises(StorytoldError): self.pf()
    def test_mutable_or_placeholder_revision_rejected(self):
        for revision in ('main','latest','0'*40):
            self.pins['apps']['photocraft']['revision']=revision;self.save_pins()
            with self.assertRaises(StorytoldError): self.pf()
    def test_unknown_and_malformed_unused_lock_entries_rejected(self):
        self.pins['apps']['gridcraft']['version']=None;self.save_pins()
        with self.assertRaises(StorytoldError): self.pf(['photocraft'])
    def test_unconfined_needs_explicit_ack(self):
        with self.assertRaises(StorytoldError): self.pf(['gridcraft'],ack=False)
        pf=self.pf(['gridcraft'],ack=True);self.assertFalse(pf['os_isolation_verified'])
    def test_wrong_output_root_rejected(self):
        with self.assertRaises(StorytoldError): preflight(self.bin,self.work,self.work/'inputs',self.lock,['photocraft'],self.catalog)
    def test_binary_group_write_rejected(self):
        if os.name=='nt': self.skipTest('POSIX mode check')
        (self.bin/'photocraft-cli').chmod(0o775)
        with self.assertRaises(StorytoldError): self.pf()
    def test_hardlinked_binary_rejected(self):
        p=self.bin/('photocraft-cli'+('.exe' if os.name=='nt' else ''))
        os.link(p,self.base/'binary-link')
        with self.assertRaises(StorytoldError): self.pf()
    def test_catalog_mutation_requires_reviewed_implementation(self):
        root=self.base/'catalog-copy';(root/'config').mkdir(parents=True)
        c=json.loads((ROOT/'config/apps.json').read_text());c['apps'][1]['args']=['mcp']
        (root/'config/apps.json').write_bytes(encoded(c))
        with self.assertRaises(StorytoldError): load_catalog(root)
    def test_templates_contain_only_direct_native_stdio(self):
        d=templates(self.catalog)
        for body in d.values():
            v=json.loads(body);self.assertEqual(set(v['mcpServers']),set(APP_IDS))
            for app,s in v['mcpServers'].items():
                self.assertIn(app+'-cli',s['command']);self.assertNotIn('url',s)
    def test_fingerprint_changes_with_workspace(self):
        from storytold_tools.workspace import init_workspace
        first=self.pf()['launches'][0]['fingerprint']
        w=self.base/'other';init_workspace(w)
        pf=preflight(self.bin,w,w/'outputs',self.lock,['photocraft'],self.catalog)
        self.assertNotEqual(first,pf['launches'][0]['fingerprint'])

    def test_lock_in_native_workspace_rejected(self):
        self.lock=self.work/'outputs/untrusted-lock.json'
        self.save_pins()
        with self.assertRaises(StorytoldError):
            self.pf()
