import json
import os
from pathlib import Path
import tempfile
import unittest
from storytold_tools.doctor import report

class DoctorTests(unittest.TestCase):
    """Synthetic files only; doctor must never execute anything it finds."""
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix='storytold-doctor-');self.addCleanup(temp.cleanup)
        self.base=Path(temp.name).resolve()
        self.home=self.base/'home';self.cwd=self.base/'project';self.apps=self.base/'Applications'
        for d in (self.home/'.codex',self.cwd,self.apps,self.base/'bin'): d.mkdir(parents=True)
        self.env={'PATH':''}
    def binary(self,name):
        p=self.base/'bin'/(name+('.exe' if os.name=='nt' else ''));p.write_bytes(b'SYNTHETIC; MUST NOT EXECUTE');p.chmod(0o755);return p
    def codex(self,body): (self.home/'.codex/config.toml').write_text(body)
    def run_report(self):
        r=report(self.env,self.cwd,self.home,[self.apps])
        return r,{a['app']:a for a in r['apps']}

    def test_desktop_app_without_cli_points_to_cli_asset(self):
        (self.apps/'PhotoCraft.app').mkdir()
        _,apps=self.run_report()
        self.assertEqual(apps['photocraft']['status'],'desktop_app_only')
        self.assertIn('setup --app photocraft`',apps['photocraft']['next']);self.assertNotIn('--acknowledge-unconfined',apps['photocraft']['next'])
        self.assertEqual(apps['vectorcraft']['status'],'not_installed')
        self.assertIn('setup --app cadcraft --acknowledge-unconfined',apps['cadcraft']['next'])
        from storytold_tools.releases import load_releases
        self.assertEqual(apps['cadcraft']['manifest_release'],load_releases()['apps']['cadcraft']['tag']);self.assertIsNone(apps['cadcraft']['pinned_version'])

    def test_cli_found_but_unregistered(self):
        cmd=self.binary('photocraft-cli');self.env['CRAFT_BIN_DIR']=str(self.base/'bin')
        _,apps=self.run_report()
        self.assertEqual(apps['photocraft']['status'],'cli_not_registered')
        self.assertEqual(apps['photocraft']['cli'],str(cmd))

    def test_recorded_setup_state_locates_cli_and_pin(self):
        from storytold_tools.setup import state_dir
        cmd=self.binary('gridcraft-cli');state=state_dir(self.env,self.home);state.mkdir(parents=True)
        (state/'setup.json').write_text(json.dumps({'schema_version':1,'bin_dir':str(self.base/'bin'),'work_root':str(self.base/'w'),
            'output_root':str(self.base/'w/outputs'),'lock':str(state/'installations.lock.json'),'evidence_dir':str(state/'evidence'),'updated_at':'2026-10-12T00:00:00+00:00'}))
        (state/'installations.lock.json').write_text(json.dumps({'schema_version':1,'platform':{},'apps':{'gridcraft':{'revision':'x','version':'0.5.0 (test)','sha256':'y'}}}))
        r,apps=self.run_report()
        self.assertTrue(r['setup_state_recorded']);self.assertEqual(apps['gridcraft']['status'],'cli_not_registered')
        self.assertEqual(apps['gridcraft']['cli'],str(cmd));self.assertEqual(apps['gridcraft']['pinned_version'],'0.5.0 (test)')
        # A plain setup refuses a binary at another pin, so the step it names must carry --upgrade.
        self.assertIs(apps['gridcraft']['up_to_date'],False);self.assertIn('setup --app gridcraft --acknowledge-unconfined --upgrade`',apps['gridcraft']['next'])
        self.assertIsNone(apps['photocraft']['up_to_date'])

    def recorded(self,app,revision,label):
        """Setup state whose lock pins `app` at `revision`, and a Claude registration of its binary."""
        from storytold_tools.setup import state_dir
        cmd=self.binary(app+'-cli');state=state_dir(self.env,self.home);state.mkdir(parents=True)
        (state/'setup.json').write_text(json.dumps({'schema_version':1,'bin_dir':str(self.base/'bin'),'work_root':str(self.base/'w'),
            'output_root':str(self.base/'w/outputs'),'lock':str(state/'installations.lock.json'),'evidence_dir':str(state/'evidence'),'updated_at':'2026-11-13T00:00:00+00:00'}))
        (state/'installations.lock.json').write_text(json.dumps({'schema_version':1,'platform':{},'apps':{app:{'revision':revision,'version':label,'sha256':'y'}}}))
        (self.home/'.claude.json').write_text(json.dumps({'mcpServers':{app:{'command':str(cmd),'args':['mcp']}}}))

    def test_registered_at_an_older_pin_is_reported_outdated(self):
        self.recorded('photocraft','0'*40,'0.7.0 (v0.7.0, test)')
        from storytold_tools.releases import load_releases
        tag=load_releases()['apps']['photocraft']['tag']
        _,apps=self.run_report();row=apps['photocraft']
        self.assertEqual(row['status'],'registered_outdated');self.assertIs(row['up_to_date'],False)
        self.assertIn('0.7.0 (v0.7.0, test)',row['next']);self.assertIn(tag,row['next'])
        self.assertIn('setup --app photocraft --upgrade`',row['next']);self.assertNotIn('--upgrade',row['setup_command'])

    def test_registered_at_the_manifest_pin_is_up_to_date(self):
        from storytold_tools.releases import load_releases
        row=load_releases()['apps']['photocraft']
        self.recorded('photocraft',row['commit'],row['version']+' ('+row['tag']+', test)')
        _,apps=self.run_report()
        self.assertEqual(apps['photocraft']['status'],'registered');self.assertIs(apps['photocraft']['up_to_date'],True)

    def test_manifest_commit_with_a_label_before_root_flags_is_outdated(self):
        # setup refuses such a pin without --upgrade (honours_roots), so doctor must not call it current.
        from storytold_tools.catalog import ROOTS_SINCE
        from storytold_tools.releases import load_releases
        app=sorted(ROOTS_SINCE)[0];row=load_releases()['apps'][app]
        self.recorded(app,row['commit'],'0.0.1 (v0.0.1, test)')
        _,apps=self.run_report()
        self.assertEqual(apps[app]['status'],'registered_outdated');self.assertIs(apps[app]['up_to_date'],False)

    def test_registration_without_a_lock_entry_stays_registered(self):
        # A CLI installed by hand has no lock entry: doctor cannot tell its release, so it does not guess.
        self.test_codex_registration_with_runnable_command()
        _,apps=self.run_report()
        self.assertEqual(apps['photocraft']['status'],'registered');self.assertIsNone(apps['photocraft']['up_to_date'])

    def test_cli_on_path_is_found(self):
        self.binary('photocraft-cli');self.env['PATH']=str(self.base/'bin')
        _,apps=self.run_report()
        self.assertEqual(apps['photocraft']['status'],'cli_not_registered')

    def test_codex_registration_with_runnable_command(self):
        cmd=self.binary('photocraft-cli')
        self.codex('[mcp_servers.photocraft]\ncommand = '+json.dumps(str(cmd))+'\nargs = ["mcp"]\n'
                   '[mcp_servers.unrelated]\ncommand = "x"\n')
        r,apps=self.run_report()
        self.assertEqual(apps['photocraft']['status'],'registered')
        self.assertEqual([x['host'] for x in apps['photocraft']['registrations']],['codex'])
        self.assertEqual(r['host_config_errors'],[])

    def test_codex_home_env_overrides_default(self):
        other=self.base/'codex-home';other.mkdir()
        (other/'config.toml').write_text('[mcp_servers.photocraft]\ncommand = "/missing/photocraft-cli"\n')
        self.env['CODEX_HOME']=str(other)
        _,apps=self.run_report()
        self.assertEqual(apps['photocraft']['status'],'registered_command_missing')

    def test_project_configs_are_read(self):
        cmd=self.binary('pdfcraft-cli')
        (self.cwd/'.mcp.json').write_text(json.dumps({'mcpServers':{'pdfcraft':{'command':str(cmd),'args':['mcp']}}}))
        (self.cwd/'.codex').mkdir()
        (self.cwd/'.codex/config.toml').write_text('[mcp_servers.gridcraft]\ncommand = "relative-cli"\n')
        _,apps=self.run_report()
        self.assertEqual(apps['pdfcraft']['status'],'registered')
        self.assertEqual(apps['pdfcraft']['registrations'][0]['host'],'claude_project')
        self.assertEqual(apps['gridcraft']['status'],'registered_command_missing')

    def test_claude_user_scope_is_seen_and_secrets_are_not_reported(self):
        cmd=self.binary('photocraft-cli')
        (self.home/'.claude.json').write_text(json.dumps({'oauthAccount':{'emailAddress':'secret@example.invalid','accessToken':'SECRET-TOKEN'},
            'mcpServers':{'photocraft':{'type':'stdio','command':str(cmd),'args':['mcp'],'env':{}}},'projects':{}}))
        r,apps=self.run_report()
        self.assertEqual(apps['photocraft']['status'],'registered');self.assertEqual([x['host'] for x in apps['photocraft']['registrations']],['claude_user'])
        self.assertNotIn('SECRET',json.dumps(r));self.assertNotIn('secret@example.invalid',json.dumps(r));self.assertIn('claude_user',r['scopes_inspected'])

    def test_claude_config_dir_override_and_paths_with_spaces(self):
        other=self.base/'claude config dir';other.mkdir();bindir=self.base/'bin with spaces';bindir.mkdir()
        cmd=bindir/('gridcraft-cli'+('.exe' if os.name=='nt' else ''));cmd.write_bytes(b'SYNTHETIC');cmd.chmod(0o755)
        (other/'.claude.json').write_text(json.dumps({'mcpServers':{'gridcraft':{'command':str(cmd),'args':['mcp']}}}))
        self.env['CLAUDE_CONFIG_DIR']=str(other)
        _,apps=self.run_report()
        self.assertEqual(apps['gridcraft']['status'],'registered');self.assertEqual(apps['gridcraft']['registrations'][0]['command'],str(cmd))
        self.assertTrue(apps['gridcraft']['registrations'][0]['command_runnable'])

    def test_registration_collisions_across_scopes_are_all_reported(self):
        cmd=self.binary('pdfcraft-cli')
        self.codex('[mcp_servers.pdfcraft]\ncommand = '+json.dumps(str(cmd))+'\n')
        (self.home/'.claude.json').write_text(json.dumps({'mcpServers':{'pdfcraft':{'command':'/elsewhere/pdfcraft-cli','args':['mcp']}}}))
        (self.cwd/'.mcp.json').write_text(json.dumps({'mcpServers':{'pdfcraft':{'command':str(cmd),'args':['mcp']}}}))
        _,apps=self.run_report();regs={x['host']:x for x in apps['pdfcraft']['registrations']}
        self.assertEqual(sorted(regs),['claude_project','claude_user','codex']);self.assertFalse(regs['claude_user']['command_runnable'])
        self.assertEqual(apps['pdfcraft']['status'],'registered_command_missing')  # one of the three points nowhere runnable

    def test_malformed_config_is_reported_not_raised(self):
        self.codex('[mcp_servers.photocraft\n')
        (self.cwd/'.mcp.json').write_text('{"mcpServers": []}')
        (self.home/'.claude.json').write_text('{not json')
        r,apps=self.run_report()
        self.assertEqual({e['host'] for e in r['host_config_errors']},{'codex','claude_project','claude_user'})
        # An unreadable host file may hold the registration: unknown, never "not installed" or "not registered".
        self.assertEqual(apps['photocraft']['status'],'registration_unknown');self.assertIn('could not be read',apps['photocraft']['next'])

    def test_corrupt_lock_is_reported_not_swallowed(self):
        from storytold_tools.setup import state_dir
        state=state_dir(self.env,self.home);state.mkdir(parents=True)
        (state/'installations.lock.json').write_text('{truncated')
        r,apps=self.run_report()
        self.assertEqual([e['host'] for e in r['host_config_errors']],['installation_lock'])
        self.assertIsNone(apps['gridcraft']['pinned_version']);self.assertEqual(apps['gridcraft']['status'],'not_installed')
