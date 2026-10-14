"""v1.3.1 lifecycle guarantees: promotion recovery, removal ownership, host replacement restore, evidence identity, strict CI provenance.

Everything runs against synthetic state in temporary directories with the
injected FakeWorld; fault injection patches the exact boundaries (binary
replace, lock write, marker cleanup, host add/remove) without touching real
applications or host configurations.
"""
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import unittest
from unittest import mock
from storytold_tools import setup as s
from storytold_tools.catalog import preflight
from storytold_tools.common import ROOT, StorytoldError, digest, encoded, load_json
from storytold_tools.configuration import generate
from storytold_tools.releases import load_releases, require_complete_bundles
from tests.support import successful_report
from tests.test_setup import SetupCase

def mark(case, app, candidate, previous_pin, commit=None, label='test label'):
    marker=s.recovery_marker(case.paths,app);marker.parent.mkdir(exist_ok=True)
    marker.write_bytes(encoded({'schema_version':1,'app':app,'candidate_sha256':candidate,'previous_sha256':previous_pin['sha256'] if previous_pin else None,
                                'previous_pin':previous_pin,'commit':commit or (previous_pin or {}).get('revision') or 'a'*40,'label':label,'written_at':'2026-10-12T00:00:00+00:00'}))
    return marker

class PromotionRecoveryTests(SetupCase):
    def upgrade_target(self,body=b'SYNTHETIC v2'):
        self.world.releases['apps']['photocraft']['commit']='f0e1d2c3'*5;self.world.set_archive('photocraft',body)

    def test_failure_before_promotion_leaves_no_marker_and_no_change(self):
        self.setup(['photocraft']);before=self.snapshot_state();self.upgrade_target()
        self.world.fail_fetch={self.world.releases['apps']['photocraft']['assets']['macos']['name']}
        r=self.setup(['photocraft'],upgrade=True);self.assertEqual(r['status'],'failed')
        self.assertEqual(self.snapshot_state(),before);self.assertFalse(s.recovery_marker(self.paths,'photocraft').exists())
        self.assertEqual(s.recovery_state(self.paths,self.world.catalog,'photocraft'),{'state':'none'})

    def test_failure_during_binary_replace_is_reverted_on_the_next_run(self):
        self.setup(['photocraft']);before=self.snapshot_state();self.upgrade_target();target=str(self.installed('photocraft'))
        real_replace=s.os.replace
        def failing_replace(src,dst):
            if str(dst)==target: raise OSError('synthetic rename failure')
            return real_replace(src,dst)
        with mock.patch.object(s.os,'replace',failing_replace):
            r=self.setup(['photocraft'],upgrade=True)
        self.assertEqual(r['status'],'failed');self.assertIn('synthetic rename failure',r['apps'][0]['error'])
        self.assertEqual(self.installed('photocraft').read_bytes(),b'SYNTHETIC photocraft');self.assertEqual(self.lock.read_bytes(),before['lock'])
        marker=s.recovery_marker(self.paths,'photocraft');self.assertTrue(marker.is_file())  # kept: the exception path clears staging only
        self.assertEqual(s.recovery_state(self.paths,self.world.catalog,'photocraft')['state'],'reverted')
        r=self.setup(['photocraft'],upgrade=True);self.assertEqual(r['status'],'passed',r['apps'][0]);self.assertEqual(r['apps'][0]['recovery'],'reverted')
        self.assertEqual(self.installed('photocraft').read_bytes(),b'SYNTHETIC v2');self.assertFalse(marker.exists())
        exe=self.installed('photocraft');self.assertFalse(exe.with_name(exe.name+'.storytold-new').exists())

    def test_failure_while_writing_the_lock_keeps_the_marker_and_completes_later(self):
        self.setup(['photocraft']);old_lock=self.lock.read_bytes();self.upgrade_target();self.world.calls.clear()
        with mock.patch.object(s,'pin',side_effect=OSError('synthetic lock write failure')):
            r=self.setup(['photocraft'],upgrade=True)
        self.assertEqual(r['status'],'failed');self.assertIn('synthetic lock write failure',r['apps'][0]['error'])
        self.assertEqual(self.installed('photocraft').read_bytes(),b'SYNTHETIC v2');self.assertEqual(self.lock.read_bytes(),old_lock)  # binary new, lock old
        marker=s.recovery_marker(self.paths,'photocraft');self.assertTrue(marker.is_file());self.assertFalse((self.paths['state_dir']/'staging/photocraft').exists())
        self.assertEqual(self.mcp_mutations(),[]);self.assertEqual(s.recovery_state(self.paths,self.world.catalog,'photocraft')['state'],'completable')
        self.assertFalse(s.managed_binary(self.paths,self.world.catalog,'photocraft')['owned'])
        r=self.setup(['photocraft']);entry=r['apps'][0];self.assertEqual(r['status'],'passed',entry);self.assertEqual(entry['recovery'],'completable')
        self.assertTrue(any('completed an interrupted upgrade' in l for l in self.world.logs))
        self.assertEqual(load_json(self.lock)['apps']['photocraft']['sha256'],digest(b'SYNTHETIC v2'));self.assertEqual(load_json(self.lock)['apps']['photocraft']['revision'],'f0e1d2c3'*5)
        self.assertFalse(marker.exists());self.assertTrue(entry['install']['unchanged']);self.assertEqual(entry['registrations'][0]['status'],'already_registered')
        r=self.setup(['photocraft']);self.assertNotIn('recovery',r['apps'][0])  # idempotent: nothing left to reconcile

    def test_failure_finalizing_the_marker_leaves_a_consistent_state(self):
        self.setup(['photocraft']);self.upgrade_target()
        with mock.patch.object(s,'clear_recovery_marker',side_effect=OSError('synthetic unlink failure')):
            r=self.setup(['photocraft'],upgrade=True)
        self.assertEqual(r['status'],'failed');self.assertIn('synthetic unlink failure',r['apps'][0]['error'])
        self.assertTrue(s.managed_binary(self.paths,self.world.catalog,'photocraft')['owned']);self.assertTrue(s.recovery_marker(self.paths,'photocraft').is_file())
        self.assertEqual(s.recovery_state(self.paths,self.world.catalog,'photocraft')['state'],'consistent')
        r=self.setup(['photocraft']);self.assertEqual(r['status'],'passed');self.assertEqual(r['apps'][0]['recovery'],'consistent');self.assertFalse(s.recovery_marker(self.paths,'photocraft').exists())

    def test_marker_with_active_matching_neither_refuses_and_keeps_everything(self):
        self.setup(['photocraft']);old_pin=load_json(self.lock)['apps']['photocraft'];old_lock=self.lock.read_bytes()
        marker=mark(self,'photocraft',digest(b'candidate never seen'),old_pin);self.installed('photocraft').write_bytes(b'SOMETHING ELSE');self.world.calls.clear()
        for _ in range(2):
            r=self.setup(['photocraft'],upgrade=True);self.assertEqual(r['status'],'failed');self.assertIn('matches neither',r['apps'][0]['error'])
            self.assertEqual(self.installed('photocraft').read_bytes(),b'SOMETHING ELSE');self.assertEqual(self.lock.read_bytes(),old_lock);self.assertTrue(marker.is_file())
        r=self.remove(['photocraft']);self.assertEqual(r['status'],'attention');self.assertEqual(r['apps'][0]['recovery'],'ambiguous');self.assertEqual(self.mcp_mutations(),[])
        self.assertTrue(self.installed('photocraft').exists());self.assertTrue(marker.is_file());self.assertEqual(self.lock.read_bytes(),old_lock)
        st=s.status(hosts=None,env=self.env,home=self.home,system='Darwin',run=self.world.run,which=self.world.which,releases=self.world.releases,catalog=self.world.catalog)
        self.assertEqual([a['recovery'] for a in st['apps'] if a['app']=='photocraft'],['ambiguous'])

    def test_corrupt_marker_refuses_without_deleting_it(self):
        self.setup(['photocraft']);marker=s.recovery_marker(self.paths,'photocraft');marker.parent.mkdir(exist_ok=True);marker.write_bytes(b'{not json')
        r=self.setup(['photocraft']);self.assertEqual(r['status'],'failed');self.assertIn('unreadable',r['apps'][0]['error']);self.assertTrue(marker.is_file())
        marker.write_bytes(encoded({'schema_version':1,'app':'vectorcraft'}))  # wrong app, missing fields
        r=self.setup(['photocraft']);self.assertEqual(r['status'],'failed');self.assertIn('unreadable',r['apps'][0]['error']);self.assertTrue(marker.is_file())
        self.assertTrue(s.managed_binary(self.paths,self.world.catalog,'photocraft')['owned'])  # the installation itself was not touched

    def test_stale_marker_with_untouched_installation_is_cleared(self):
        self.setup(['photocraft']);old_pin=load_json(self.lock)['apps']['photocraft']
        marker=mark(self,'photocraft',digest(b'never promoted'),old_pin)
        self.assertEqual(s.recovery_state(self.paths,self.world.catalog,'photocraft')['state'],'reverted')
        r=self.setup(['photocraft']);self.assertEqual(r['status'],'passed');self.assertEqual(r['apps'][0]['recovery'],'reverted');self.assertFalse(marker.exists())

    def test_installation_works_again_after_recovery(self):
        self.setup(['photocraft']);self.upgrade_target()
        with mock.patch.object(s,'pin',side_effect=OSError('synthetic')): self.setup(['photocraft'],upgrade=True)
        self.assertEqual(self.setup(['photocraft'])['status'],'passed')  # recovery
        self.world.releases['apps']['photocraft']['commit']='0a1b2c3d'*5;self.world.set_archive('photocraft',b'SYNTHETIC v3')
        r=self.setup(['photocraft'],upgrade=True);self.assertEqual(r['status'],'passed',r['apps'][0])
        self.assertEqual(self.installed('photocraft').read_bytes(),b'SYNTHETIC v3');self.assertTrue(s.managed_binary(self.paths,self.world.catalog,'photocraft')['owned'])

class RemovalOwnershipTests(SetupCase):
    def test_registration_with_same_path_but_different_arguments_is_kept(self):
        self.setup(['photocraft']);self.world.hosts['codex']['photocraft']['args']=['mcp','--extra'];self.world._sync_codex_toml()
        r=self.remove(['photocraft']);rows={x['host']:x for x in r['apps'][0]['registrations']}
        self.assertEqual(rows['codex']['action'],'kept');self.assertIn('arguments',rows['codex']['reason']);self.assertEqual(rows['claude']['action'],'unregister')
        self.assertEqual(r['status'],'attention');self.assertIn('photocraft',self.world.hosts['codex'])

    def test_registration_in_another_scope_is_kept(self):
        self.setup(['photocraft']);self.world.claude_scope='Project config (shared via .mcp.json)'
        r=self.remove(['photocraft']);rows={x['host']:x for x in r['apps'][0]['registrations']}
        self.assertEqual(rows['claude']['action'],'kept');self.assertIn('scope',rows['claude']['reason']);self.assertIn('photocraft',self.world.hosts['claude'])

    def test_registration_absent_from_the_user_scope_file_is_kept(self):
        self.setup(['photocraft']);(self.home/'.codex/config.toml').write_text('[other]\nkeep = true\n')
        r=self.remove(['photocraft']);rows={x['host']:x for x in r['apps'][0]['registrations']}
        self.assertEqual(rows['codex']['action'],'kept');self.assertIn('scope cannot be confirmed',rows['codex']['reason'])

    def test_registration_with_cwd_or_env_is_kept(self):
        self.world.codex_cwd='/somewhere';self.setup(['photocraft'])
        r=self.remove(['photocraft']);rows={x['host']:x for x in r['apps'][0]['registrations']}
        self.assertEqual(rows['codex']['action'],'kept');self.assertIn('cwd or env',rows['codex']['reason'])

    def test_missing_pin_keeps_registration_and_binary(self):
        self.setup(['photocraft']);lock=load_json(self.lock);del lock['apps']['photocraft'];self.lock.write_bytes(encoded(lock));self.world.calls.clear()
        r=self.remove(['photocraft']);entry=r['apps'][0]
        self.assertEqual([x['action'] for x in entry['registrations']],['kept','kept']);self.assertIn('no pin',entry['registrations'][0]['reason'])
        self.assertEqual(entry['binary']['action'],'kept');self.assertEqual(self.mcp_mutations(),[]);self.assertTrue(self.installed('photocraft').exists())

    def test_missing_host_cli_is_reported_not_guessed(self):
        self.setup(['photocraft']);self.world.available={'codex'}
        r=self.remove(['photocraft']);rows={x['host']:x for x in r['apps'][0]['registrations']}
        self.assertEqual(rows['claude']['action'],'none');self.assertIn('not inspected',rows['claude']['reason']);self.assertEqual(r['status'],'ok')
        self.setup(['vectorcraft'],hosts=['codex']);r=self.remove(['vectorcraft'],hosts=['claude']);self.assertEqual(r['status'],'attention')
        self.assertEqual(r['apps'][0]['registrations'][0]['action'],'kept')

    def test_removal_is_idempotent(self):
        self.setup(['photocraft']);first=self.remove(['photocraft']);self.assertEqual(first['status'],'ok')
        second=self.remove(['photocraft']);self.assertEqual(second['status'],'ok')
        self.assertEqual([x['action'] for x in second['apps'][0]['registrations']],['none','none']);self.assertEqual(second['apps'][0]['binary']['action'],'none');self.assertIsNone(second['apps'][0]['pin'])

    def test_dangling_registration_after_a_deleted_binary_is_still_removed(self):
        self.setup(['photocraft']);self.installed('photocraft').unlink()  # binary gone, pin and registration remain
        r=self.remove(['photocraft']);entry=r['apps'][0];self.assertEqual(r['status'],'ok')
        self.assertEqual([x['action'] for x in entry['registrations']],['unregister','unregister']);self.assertEqual(entry['pin']['action'],'drop');self.assertEqual(self.world.hosts,{'codex':{},'claude':{}})

class ReplacementTests(SetupCase):
    def stale_codex(self,args=('mcp',)):
        self.world.hosts['codex']['photocraft']={'command':'/elsewhere/photocraft-cli','args':list(args)};self.world._sync_codex_toml()
    def codex_row(self,r): return [x for x in r['apps'][0]['registrations'] if x['host']=='codex'][0]
    def codex_adds(self): return [c for c in self.mcp_mutations() if c[2]=='add' and Path(c[0]).name=='codex']

    def test_successful_replacement(self):
        self.stale_codex();r=self.setup(['photocraft'],replace=True);self.assertEqual(self.codex_row(r)['status'],'registered')
        self.assertEqual(self.world.hosts['codex']['photocraft']['command'],str(self.installed('photocraft')))

    def test_failure_while_removing_keeps_the_original(self):
        self.stale_codex(('mcp','--flag','/path with spaces/x'));self.world.fail_remove={'codex'}
        r=self.setup(['photocraft'],replace=True);row=self.codex_row(r)
        self.assertEqual(row['status'],'failed');self.assertIn('removal failed',row['error']);self.assertEqual(self.world.hosts['codex']['photocraft']['args'],['mcp','--flag','/path with spaces/x'])
        self.assertEqual(self.codex_adds(),[])

    def test_failure_while_adding_restores_the_original_and_verifies_it(self):
        original=('mcp','--flag','/path with spaces/x','--two');self.stale_codex(original);self.world.fail_add_once={'codex'};self.world.calls.clear()
        r=self.setup(['photocraft'],replace=True);row=self.codex_row(r)
        self.assertEqual(row['status'],'failed');self.assertIn('was restored and verified',row['error']);self.assertNotIn('registration_lost',row)
        self.assertEqual(self.world.hosts['codex']['photocraft'],{'command':'/elsewhere/photocraft-cli','args':list(original)})
        last=self.codex_adds()[-1];self.assertEqual(last[last.index('--')+1:],['/elsewhere/photocraft-cli',*original])  # argv restored verbatim, spaces intact

    def test_failed_restoration_is_reported_with_the_manual_command(self):
        self.stale_codex(('mcp','--flag','/path with spaces/x'));self.world.fail_add={'codex'}
        r=self.setup(['photocraft'],replace=True);row=self.codex_row(r)
        self.assertEqual(row['status'],'failed');self.assertTrue(row.get('registration_lost'));self.assertIn('Re-add it by hand',row['error'])
        self.assertIn('codex mcp add photocraft -- /elsewhere/photocraft-cli mcp --flag "/path with spaces/x"',row['error']);self.assertNotIn('photocraft',self.world.hosts['codex'])
        self.assertEqual(r['status'],'failed');self.assertEqual(r['apps'][0]['status'],'partially_registered')

    def test_scope_mismatch_and_unrestorable_entries_refuse_before_removal(self):
        self.world.hosts['claude']['photocraft']={'command':'/elsewhere/photocraft-cli','args':['mcp']};self.world._sync_claude_json();self.world.claude_scope='Local config'
        r=self.setup(['photocraft'],replace=True);row=[x for x in r['apps'][0]['registrations'] if x['host']=='claude'][0]
        self.assertEqual(row['status'],'failed');self.assertIn('not user scope',row['error']);self.assertIn('photocraft',self.world.hosts['claude'])
        self.world.claude_scope='User config (available in all your projects)';self.world.claude_json=False;(self.home/'.claude.json').unlink()  # text only: args cannot be recovered
        r=self.setup(['photocraft'],replace=True);row=[x for x in r['apps'][0]['registrations'] if x['host']=='claude'][0]
        self.assertEqual(row['status'],'failed');self.assertIn('cannot be recovered',row['error']);self.assertIn('photocraft',self.world.hosts['claude'])
        self.world.claude_json=True;self.world.codex_cwd='/custom';self.stale_codex()
        r=self.setup(['photocraft'],replace=True);self.assertIn('cannot restore',self.codex_row(r)['error']);self.assertIn('photocraft',self.world.hosts['codex'])
        self.assertFalse(any(c[2]=='remove' for c in self.mcp_mutations()))

    def test_normal_registration_stays_idempotent(self):
        self.setup(['photocraft']);self.world.calls.clear();r=self.setup(['photocraft'],replace=True)
        self.assertEqual({x['status'] for x in r['apps'][0]['registrations']},{'already_registered'});self.assertEqual(self.mcp_mutations(),[])

class EvidenceIdentityTests(SetupCase):
    def active_preflight(self,app='photocraft'):
        return preflight(self.bin,self.paths['work_root'],self.paths['output_root'],self.lock,[app],self.world.catalog,False)

    def test_candidate_and_active_evidence_describe_their_own_launch(self):
        r=self.setup(['photocraft']);entry=r['apps'][0]
        cand=load_json(self.paths['evidence_dir']/'photocraft-candidate.json');active=load_json(self.paths['evidence_dir']/'photocraft.json')
        self.assertEqual(cand['probed_bin_dir'],str(self.paths['state_dir']/'staging/photocraft/bin'));self.assertEqual(active['probed_bin_dir'],str(self.bin))
        self.assertEqual(entry['candidate_probe']['status'],'discovery_and_call_passed');self.assertEqual(entry['probe']['status'],'discovery_and_call_passed')
        self.assertEqual(entry['probe']['evidence'],str(self.paths['evidence_dir']/'photocraft.json'))

    def test_failed_active_probe_after_promotion_is_reported_and_not_registered(self):
        self.world.probe_fail_bin_dirs={str(self.bin)}
        r=self.setup(['photocraft']);entry=r['apps'][0]
        self.assertEqual(r['status'],'failed');self.assertEqual(entry['status'],'promoted_unverified');self.assertNotIn('registrations',entry)
        self.assertTrue(s.managed_binary(self.paths,self.world.catalog,'photocraft')['owned']);self.assertEqual(self.world.hosts,{'codex':{},'claude':{}})
        self.assertEqual(load_json(self.paths['evidence_dir']/'photocraft.json')['status'],'failed');self.assertEqual(entry['candidate_probe']['status'],'discovery_and_call_passed')
        self.world.probe_fail_bin_dirs=set();r=self.setup(['photocraft']);self.assertEqual(r['status'],'passed');self.assertEqual(r['apps'][0]['status'],'registered')

    def test_archived_evidence_is_never_overwritten(self):
        evidence_dir=self.paths['evidence_dir'];evidence_dir.mkdir(parents=True);fixed=datetime(2026,10,12,19,19,36,tzinfo=timezone.utc)
        with mock.patch.object(s,'datetime',mock.Mock(now=lambda tz=None: fixed)):  # several runs inside one timestamp
            for i in range(3):
                (evidence_dir/'photocraft.json').write_bytes(encoded({'run':i}));s.archive_evidence(evidence_dir,'photocraft')
        archived=sorted((evidence_dir/'archive').iterdir())
        self.assertEqual([p.name for p in archived],['photocraft-20261012T191936.000000Z-1.json','photocraft-20261012T191936.000000Z-2.json','photocraft-20261012T191936.000000Z.json'])
        self.assertEqual(sorted(load_json(p)['run'] for p in archived),[0,1,2]);self.assertFalse((evidence_dir/'photocraft.json').exists())
        s.archive_evidence(evidence_dir,'photocraft');self.assertEqual(len(list((evidence_dir/'archive').iterdir())),3)  # nothing to archive: no-op

    def test_skip_probe_leaves_no_evidence_and_configure_refuses(self):
        self.setup(['photocraft'],skip_probe=True);self.assertFalse((self.paths['evidence_dir']/'photocraft.json').exists())
        with self.assertRaises((StorytoldError,OSError)): generate(self.active_preflight(),self.paths['evidence_dir'],'claude')

    def test_configure_accepts_only_evidence_for_the_active_launch(self):
        self.setup(['photocraft'],skip_probe=True);pf=self.active_preflight();evidence=self.paths['evidence_dir']/'photocraft.json'
        active=asyncio.run(successful_report(pf['launches'][0]));evidence.write_bytes(encoded(active))
        out=json.loads(generate(pf,self.paths['evidence_dir'],'claude'));self.assertEqual(out['mcpServers']['photocraft']['command'],str(self.installed('photocraft')))
        # the same report made for the staged path is refused: its fingerprint names another launch
        staging=self.paths['state_dir']/'staging/photocraft';(staging/'bin').mkdir(parents=True);exe=self.installed('photocraft').name
        (staging/'bin'/exe).write_bytes(self.installed('photocraft').read_bytes());(staging/'bin'/exe).chmod(0o755);(staging/'lock.json').write_bytes(self.lock.read_bytes())
        staged=preflight(staging/'bin',self.paths['work_root'],self.paths['output_root'],staging/'lock.json',['photocraft'],self.world.catalog,False)['launches'][0]
        self.assertNotEqual(staged['fingerprint'],pf['launches'][0]['fingerprint'])
        evidence.write_bytes(encoded(asyncio.run(successful_report(staged))))
        with self.assertRaises(StorytoldError) as cm: generate(pf,self.paths['evidence_dir'],'claude')
        self.assertIn('launch_fingerprint',str(cm.exception))
        stale=dict(active);stale['binary_sha256']='0'*64;evidence.write_bytes(encoded(stale))  # evidence from a previous binary
        with self.assertRaises(StorytoldError) as cm: generate(pf,self.paths['evidence_dir'],'claude')
        self.assertIn('binary_sha256',str(cm.exception))

class StrictProvenanceTests(unittest.TestCase):
    def test_require_complete_bundles(self):
        releases=load_releases();name=releases['apps']['cadcraft']['assets']['macos']['name']
        full={'bundles':{a['name']:{} for row in releases['apps'].values() for a in row['assets'].values()}}
        self.assertEqual(len(require_complete_bundles(full,releases)),39)
        partial={'bundles':{k:v for k,v in full['bundles'].items() if k!=name}}
        with self.assertRaises(StorytoldError) as cm: require_complete_bundles(partial,releases)
        self.assertIn(name,str(cm.exception))
    def test_release_workflow_verifies_strictly_after_the_bundle_check(self):
        text=(ROOT/'.github/workflows/releases.yml').read_text();verify=text[text.index('verify:'):text.index('merge:')]
        self.assertNotIn('--trust-upstream-sums',verify);self.assertLess(verify.index('scripts/check_bundles.py'),verify.index('storytold.py setup'))
        self.assertIn('sigstore/cosign-installer@',verify);self.assertLess(text.index('scripts/sign_releases.py'),text.index('verify:'))
        self.assertTrue(re.search(r'needs:\s*refresh',verify))
