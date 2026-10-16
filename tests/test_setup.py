"""Setup, upgrade and removal on three simulated platforms with injected network, signing tools and host CLIs.

Nothing real runs: downloads, notarization, cosign, probes and the codex/claude
CLIs are all fakes recording what was asked of them.
"""
import io
import json
import os
from pathlib import Path
import stat
import tarfile
import tempfile
import unittest
import urllib.request
import zipfile
from storytold_tools import setup as s
from storytold_tools.catalog import load_catalog
from storytold_tools.common import StorytoldError, digest, encoded, load_json
from storytold_tools.releases import load_releases

SIGNER='^https://github\\.com/devsolux/storytold/\\.github/workflows/releases\\.yml@refs/heads/main$'

def synthetic_zip(exe,body=b'SYNTHETIC CLI; MUST NOT EXECUTE',extra=()):
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w') as z:
        for name,mode,data in ((f'{exe}-0.0.1/{exe}',0o755,body),(f'{exe}-0.0.1/README.md',0o644,b'readme'),(f'{exe}-0.0.1/{exe.replace("-cli","")}',0o755,b'GUI'),*extra):
            info=zipfile.ZipInfo(name);info.external_attr=(stat.S_IFREG|mode)<<16;z.writestr(info,data)
    return out.getvalue()

def synthetic_tar(exe,body=b'SYNTHETIC CLI; MUST NOT EXECUTE',extra=()):
    out=io.BytesIO()
    with tarfile.open(fileobj=out,mode='w:gz') as t:
        for name,mode,data in ((f'{exe}-0.0.1/bin/{exe}',0o755,body),(f'{exe}-0.0.1/bin/{exe.replace("-cli","")}',0o755,b'GUI'),(f'{exe}-0.0.1/share/x.txt',0o644,b'x'),*extra):
            info=tarfile.TarInfo(name);info.size=len(data);info.mode=mode;t.addfile(info,io.BytesIO(data))
    return out.getvalue()

class FakeWorld:
    """Injected network, provenance tools and host CLIs for one simulated platform."""
    def __init__(self,system='Darwin',machine='arm64',home=None):
        self.system=system;self.machine=machine;self.plat=s.platform_key(system,machine);self.home=home
        self.catalog=load_catalog();self.releases=json.loads(json.dumps(load_releases()))
        self.releases['signers']={'apple_team_id':'TESTTEAM00','sigstore_identity_regexp':SIGNER,'sigstore_oidc_issuer':'https://token.actions.githubusercontent.com'}
        self.signatures={'schema_version':1,'signed_by':SIGNER,'bundles':{}}
        self.archives={};self.hosts={'codex':{},'claude':{}};self.available={'codex','claude'};self.calls=[];self.logs=[]
        self.notarized=True;self.team='TESTTEAM00';self.cosign_ok=True;self.probe_status='discovery_and_call_passed';self.sums_override=None
        self.fail_fetch=set();self.fail_add=set();self.fail_add_once=set();self.fail_remove=set();self.claude_json=True;self.claude_text_omits_command=False
        self.claude_scope='User config (available in all your projects)';self.codex_cwd=None;self.probe_fail_bin_dirs=set()
        for app in self.releases['apps']:
            self.set_archive(app,b'SYNTHETIC '+app.encode())
    def set_archive(self,app,body):
        """Point every platform asset of `app` at a synthetic archive carrying `body` as the CLI."""
        for plat,asset in self.releases['apps'][app]['assets'].items():
            member=app+'-cli'+('.exe' if plat=='windows-x64' else '')
            data=synthetic_tar(member,body) if asset['name'].endswith('.tar.gz') else synthetic_zip(member,body)
            self.archives[asset['name']]=data;asset.update(sha256=digest(data),bytes=len(data))
    def cli_body(self,app):
        asset=self.releases['apps'][app]['assets'][self.plat];data=self.archives[asset['name']];member=app+'-cli'+('.exe' if self.plat=='windows-x64' else '')
        if asset['name'].endswith('.tar.gz'):
            with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as t: return next(t.extractfile(m).read() for m in t if m.name.endswith('/'+member))
        with zipfile.ZipFile(io.BytesIO(data)) as z: return next(z.read(n) for n in z.namelist() if n.endswith('/'+member))
    def sign(self,app):
        asset=self.releases['apps'][app]['assets'][self.plat]
        self.signatures['bundles'][asset['name']]={'binary':app+'-cli'+('.exe' if self.plat=='windows-x64' else ''),'binary_sha256':digest(self.cli_body(app)),'archive_sha256':asset['sha256'],
            'bundle':{'mediaType':'application/vnd.dev.sigstore.bundle.v0.3+json','verificationMaterial':{'x':1},'messageSignature':{'y':2}}}
    def fetch(self,url,dest,limit):
        s.check_url(url);name=url.rsplit('/',1)[1];self.calls.append(['fetch',url])
        if name in self.fail_fetch: raise StorytoldError('synthetic network failure for '+name)
        data=(self.sums_override or ''.join(f'{digest(b)}  {n}\n' for n,b in self.archives.items())).encode() if name=='SHA256SUMS.txt' else self.archives[name]
        dest.write_bytes(data);return len(data)
    def which(self,name):
        if name=='cosign': return '/fake/bin/cosign' if self.cosign_ok is not None else None
        if name in self.available: return ('C:\\fake\\'+name+'.cmd') if self.system=='Windows' else '/fake/bin/'+name
        return None
    def _sync_claude_json(self):
        if self.home is None or not self.claude_json: return
        p=self.home/'.claude.json';data=load_json(p) if p.is_file() else {'oauthAccount':{'emailAddress':'secret@example.invalid'}}
        data['mcpServers']={app:{'type':'stdio','command':row['command'],'args':row['args'],'env':{}} for app,row in self.hosts['claude'].items()}
        p.write_bytes(encoded(data))
    def _sync_codex_toml(self):
        if self.home is None: return
        p=self.home/'.codex/config.toml';p.parent.mkdir(exist_ok=True)
        lines=['[other]\nkeep = true\n']
        for app,row in self.hosts['codex'].items():
            lines.append(f'[mcp_servers.{app}]\ncommand = {json.dumps(row["command"])}\nargs = {json.dumps(row["args"])}\n'+(f'cwd = {json.dumps(self.codex_cwd)}\n' if self.codex_cwd else ''))
        p.write_text('\n'.join(lines))
    def run(self,argv):
        self.calls.append(argv);tool=Path(argv[0]).name.lower()
        if tool=='cmd.exe': argv=argv[3:];tool=argv[0].rsplit('\\',1)[-1].lower().removesuffix('.cmd')
        if tool=='spctl': return (0,'','accepted\nsource=Notarized Developer ID\n') if self.notarized else (3,'','rejected\nsource=no usable signature\n')
        if tool=='codesign': return (0,'',f'Identifier=test\nTeamIdentifier={self.team}\n')
        if tool=='cosign':
            bundle=json.loads(Path(argv[argv.index('--bundle')+1]).read_text())
            ok=self.cosign_ok and bundle.get('verificationMaterial')=={'x':1} and argv[argv.index('--certificate-identity-regexp')+1]==SIGNER
            return (0,'Verified OK\n','') if ok else (1,'','Error: no matching signatures')
        if tool in ('codex','claude'):
            store=self.hosts[tool];sub=argv[2]
            if sub=='get':
                app=argv[3];row=store.get(app)
                if row is None: return (1,'',f'No MCP server named {app}')
                if tool=='codex': return (0,json.dumps({'name':app,'transport':{'type':'stdio','command':row['command'],'args':row['args'],'env':None,'cwd':self.codex_cwd}}),'')
                lines=[f'{app}:',f'  Scope: {self.claude_scope}','  Status: ✔ Connected','  Type: stdio']
                if not self.claude_text_omits_command: lines.append(f"  Command: {row['command']}")
                lines.append(f"  Args: {' '.join(row['args'])}");lines.append('  Environment:')
                return (0,'\n'.join(lines)+'\n','')
            if sub=='add':
                if tool in self.fail_add: return (1,'','synthetic host failure')
                if tool in self.fail_add_once: self.fail_add_once.discard(tool);return (1,'','synthetic transient host failure')
                i=argv.index('--');app=argv[i-1];store[app]={'command':argv[i+1],'args':argv[i+2:]}
                self._sync_claude_json() if tool=='claude' else self._sync_codex_toml()
                return (0,'','')
            if sub=='remove':
                if tool in self.fail_remove: return (1,'','synthetic removal failure')
                store.pop(argv[-1],None)
                self._sync_claude_json() if tool=='claude' else self._sync_codex_toml()
                return (0,'','')
        if 'probe' in argv and any(a.endswith('storytold.py') for a in argv):
            out=Path(argv[argv.index('--output')+1]);app=argv[argv.index('--app')+1]
            if self.catalog[app]['confinement']=='os_only' and '--acknowledge-unconfined' not in argv:
                return (1,'',f'storytold: {app}: no verified native root flags; use tested OS isolation or explicitly acknowledge non-sensitive local testing')
            bin_dir=argv[argv.index('--bin-dir')+1];status=('failed' if bin_dir in self.probe_fail_bin_dirs else self.probe_status)
            report={'status':status,'tools':[{'name':'x'}],'protocol_version':'2025-11-25','server_info':{'name':app},
                    'probed_bin_dir':bin_dir,'error':None if status.endswith('passed') else {'type':'Synthetic','message':'synthetic failure'}}
            out.write_text(json.dumps(report));return (0 if status.endswith('passed') else 1,'','')
        if argv[1:3]==['-m','venv'] or argv[1:3]==['-m','pip']: return (0,'','')
        if argv[1]=='-c': return (0,'2.3.0\n','')
        raise AssertionError('unexpected command: '+' '.join(argv))

class SetupCase(unittest.TestCase):
    system='Darwin';machine='arm64';home_name='home'
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix='storytold-setup-');self.addCleanup(temp.cleanup)
        self.home=Path(temp.name).resolve()/self.home_name;self.home.mkdir();self.world=FakeWorld(self.system,self.machine,self.home);self.env={}
    def setup(self,apps,**kw):
        w=self.world
        options=dict(acknowledge_unconfined=False,hosts=None,skip_probe=False,upgrade=False,replace=False,dry_run=False,timeout=5,
                     env=self.env,home=self.home,system=w.system,machine=w.machine,fetch=w.fetch,run=w.run,which=w.which,log=w.logs.append,
                     releases=w.releases,signatures=w.signatures,catalog=w.catalog)
        options.update(kw);return s.setup(apps,**options)
    def remove(self,apps,**kw):
        w=self.world
        options=dict(hosts=None,env=self.env,home=self.home,system=w.system,run=w.run,which=w.which,log=w.logs.append,catalog=w.catalog)
        options.update(kw);return s.remove(apps,**options)
    @property
    def paths(self): return s.resolve_paths(self.env,self.home,self.world.system)
    @property
    def bin(self): return self.paths['bin_dir']
    @property
    def lock(self): return self.paths['lock']
    def installed(self,app): return self.bin/(app+'-cli'+('.exe' if os.name=='nt' else ''))
    def snapshot_state(self):
        """Everything a removal or a failed upgrade must leave alone."""
        files={str(p):digest(p.read_bytes()) for base in (self.bin,self.paths['evidence_dir']) if base.is_dir() for p in sorted(base.rglob('*')) if p.is_file()}
        return {'files':files,'lock':self.lock.read_bytes() if self.lock.is_file() else None,'hosts':json.loads(json.dumps(self.world.hosts))}
    def mcp_mutations(self): return [c for c in self.world.calls if len(c)>2 and c[1]=='mcp' and c[2] in ('add','remove')]

class MacSetupTests(SetupCase):
    def test_dry_run_touches_nothing(self):
        r=self.setup(['cadcraft','photocraft'],dry_run=True)
        self.assertTrue(r['dry_run']);self.assertEqual(r['platform_key'],'macos');self.assertEqual([a['needs_acknowledge_unconfined'] for a in r['apps']],[True,False])
        self.assertEqual(sorted(p.name for p in self.home.iterdir()),[]);self.assertEqual(self.world.calls,[])

    def test_confined_app_installs_pins_probes_and_registers(self):
        r=self.setup(['photocraft']);entry=r['apps'][0]
        self.assertEqual(r['status'],'passed',entry);self.assertEqual(entry['status'],'registered')
        binary=self.installed('photocraft');self.assertTrue(binary.is_file())
        if os.name!='nt': self.assertEqual(binary.stat().st_mode&0o777,0o755)
        self.assertEqual(binary.read_bytes(),b'SYNTHETIC photocraft')
        lock=load_json(self.lock);self.assertEqual(lock['apps']['photocraft']['revision'],self.world.releases['apps']['photocraft']['commit'])
        self.assertIn('notarized TESTTEAM00',lock['apps']['photocraft']['version']);self.assertNotIn('sigstore',lock['apps']['photocraft']['version'])
        self.assertEqual(entry['probe']['status'],'discovery_and_call_passed')
        evidence=load_json(self.paths['evidence_dir']/'photocraft.json');self.assertEqual(evidence['probed_bin_dir'],str(self.bin))  # the active launch
        candidate=load_json(self.paths['evidence_dir']/'photocraft-candidate.json');self.assertEqual(candidate['probed_bin_dir'],str(self.paths['state_dir']/'staging/photocraft/bin'))
        self.assertEqual(entry['candidate_probe']['bin_dir'],str(self.paths['state_dir']/'staging/photocraft/bin'));self.assertEqual(entry['probe']['bin_dir'],str(self.bin))
        self.assertFalse((self.paths['state_dir']/'staging/photocraft').exists());self.assertFalse(s.recovery_marker(self.paths,'photocraft').exists())
        work=self.home/'craft-work-storytold';expected=['mcp','--automation-read-root',str(work),'--automation-write-root',str(work/'outputs')]
        for host in ('codex','claude'):
            self.assertEqual(self.world.hosts[host]['photocraft'],{'command':str(binary),'args':expected})
        self.assertEqual(sorted(x['host'] for x in entry['registrations']),['claude','codex'])
        self.assertEqual(s.load_state(self.env,self.home,self.world.system)['bin_dir'],str(self.bin));self.assertTrue((work/'outputs').is_dir())

    def test_macos_verifies_sigstore_bundle_when_present(self):
        self.world.sign('photocraft')
        r=self.setup(['photocraft']);self.assertEqual(r['status'],'passed',r['apps'][0])
        self.assertTrue(r['apps'][0]['install']['sigstore']);self.assertIn('sigstore',load_json(self.lock)['apps']['photocraft']['version'])
        self.world.cosign_ok=False
        r=self.setup(['vectorcraft']);self.assertEqual(r['status'],'passed')  # no bundle for vectorcraft: notarization alone
        self.world.sign('vectorcraft');self.world.releases['apps']['vectorcraft']['commit']='b2c3d4e5'*5
        r=self.setup(['vectorcraft'],upgrade=True)
        self.assertEqual(r['status'],'failed');self.assertIn('Sigstore verification failed',r['apps'][0]['error'])

    def test_unacknowledged_app_is_skipped_and_the_rest_still_processed(self):
        r=self.setup(['cadcraft','photocraft']);rows={a['app']:a for a in r['apps']}
        self.assertEqual(rows['cadcraft']['status'],'needs_acknowledgement');self.assertEqual(rows['photocraft']['status'],'registered')
        self.assertEqual(r['status'],'failed');self.assertFalse(self.installed('cadcraft').exists());self.assertTrue(self.installed('photocraft').exists())
    def test_a_held_lock_marker_stops_the_writer_instead_of_losing_pins(self):
        self.setup(['photocraft']);marker=self.lock.with_name(self.lock.name+'.writing');marker.write_text('4242')
        with self.assertRaisesRegex(StorytoldError,'another setup run is changing'):
            s.pin(self.lock,'cadcraft',{'commit':'c'*40},'d'*64,'0.1.0 (test)')
        self.assertNotIn('cadcraft',load_json(self.lock)['apps']);marker.unlink()
        s.pin(self.lock,'cadcraft',{'commit':'c'*40},'d'*64,'0.1.0 (test)')
        self.assertIn('cadcraft',load_json(self.lock)['apps']);self.assertFalse(marker.exists())
    def test_unconfined_app_needs_acknowledgement_before_any_download(self):
        r=self.setup(['cadcraft']);entry=r['apps'][0]
        self.assertEqual(entry['status'],'needs_acknowledgement');self.assertIn('--acknowledge-unconfined',entry['error']);self.assertEqual(r['status'],'failed')
        self.assertFalse(self.installed('cadcraft').exists());self.assertFalse(any(c[0]=='fetch' for c in self.world.calls))
        r=self.setup(['cadcraft'],acknowledge_unconfined=True)
        self.assertEqual(r['apps'][0]['status'],'registered');self.assertEqual(self.world.hosts['codex']['cadcraft']['args'],['mcp'])
        r=self.setup(['cadcraft']);self.assertEqual(r['apps'][0]['status'],'installed_not_registered')  # installed earlier: honest, no probe without the flag

    def test_manifest_hash_mismatch_aborts_before_install(self):
        self.world.releases['apps']['photocraft']['assets']['macos']['sha256']='0'*64
        r=self.setup(['photocraft']);self.assertEqual(r['status'],'failed');self.assertIn('config/releases.json',r['apps'][0]['error'])
        self.assertFalse(self.installed('photocraft').exists());self.assertFalse((self.paths['state_dir']/'staging/photocraft').exists())

    def test_upstream_sums_disagreement_aborts(self):
        name=self.world.releases['apps']['photocraft']['assets']['macos']['name'];self.world.sums_override='f'*64+'  '+name+'\n'
        r=self.setup(['photocraft']);self.assertEqual(r['status'],'failed');self.assertIn('SHA256SUMS',r['apps'][0]['error'])

    def test_notarization_failure_installs_nothing(self):
        self.world.notarized=False
        r=self.setup(['photocraft']);self.assertEqual(r['status'],'failed');self.assertIn('notarized',r['apps'][0]['error'])
        self.assertFalse(self.installed('photocraft').exists());self.assertFalse((self.paths['state_dir']/'staging/photocraft').exists())

    def test_wrong_signing_team_is_refused(self):
        self.world.team='OTHERTEAM1'
        r=self.setup(['photocraft']);self.assertEqual(r['status'],'failed');self.assertIn('OTHERTEAM1',r['apps'][0]['error'])

    def test_rerun_is_idempotent_and_resumes_without_upgrade(self):
        self.setup(['photocraft']);self.world.calls.clear()
        r=self.setup(['photocraft','cadcraft'],acknowledge_unconfined=True);self.assertEqual(r['status'],'passed',r['apps'])
        self.assertTrue(r['apps'][0]['install']['unchanged']);self.assertEqual(r['apps'][0]['registrations'][0]['status'],'already_registered')
        self.assertFalse(any(c[0]=='fetch' and 'photocraft' in c[1] for c in self.world.calls));self.assertEqual(r['apps'][1]['status'],'registered')
        self.assertTrue(all(c[2]=='add' and c[-1*len(c)+3]!='photocraft' for c in self.mcp_mutations()))  # only cadcraft was added

    def test_existing_binary_with_different_pin_needs_upgrade_flag(self):
        self.setup(['photocraft']);self.world.releases['apps']['photocraft']['commit']='a1b2c3d4'*5
        r=self.setup(['photocraft']);self.assertEqual(r['status'],'failed');self.assertIn('--upgrade',r['apps'][0]['error'])
        self.world.set_archive('photocraft',b'SYNTHETIC v2')
        r=self.setup(['photocraft'],upgrade=True);entry=r['apps'][0]
        self.assertEqual(entry['status'],'registered');self.assertEqual(entry['install']['previous_sha256'],digest(b'SYNTHETIC photocraft'))
        self.assertEqual(self.installed('photocraft').read_bytes(),b'SYNTHETIC v2');self.assertEqual(entry['registrations'][0]['status'],'already_registered')
        self.assertEqual(load_json(self.lock)['apps']['photocraft']['sha256'],digest(b'SYNTHETIC v2'))

    def test_identical_bytes_at_new_commit_update_only_the_pin(self):
        self.setup(['photocraft']);before=self.installed('photocraft').stat().st_ino
        self.world.releases['apps']['photocraft']['commit']='c3d4e5f6'*5
        r=self.setup(['photocraft'],upgrade=True);entry=r['apps'][0];self.assertEqual(r['status'],'passed',entry)
        self.assertEqual(entry['install']['previous_sha256'],entry['install']['sha256']);self.assertEqual(self.installed('photocraft').stat().st_ino,before)
        self.assertEqual(load_json(self.lock)['apps']['photocraft']['revision'],'c3d4e5f6'*5);self.assertTrue(any('file unchanged' in l for l in self.world.logs))

    def test_failed_probe_preserves_the_working_installation(self):
        self.setup(['photocraft']);before=self.snapshot_state();self.world.calls.clear()
        self.world.releases['apps']['photocraft']['commit']='d4e5f6a7'*5;self.world.set_archive('photocraft',b'SYNTHETIC v2 broken');self.world.probe_status='failed'
        r=self.setup(['photocraft'],upgrade=True);entry=r['apps'][0]
        self.assertEqual(r['status'],'failed');self.assertIn('native probe failed',entry['error'])
        after=self.snapshot_state();candidate=str(self.paths['evidence_dir']/'photocraft-candidate.json')
        self.assertEqual({k:v for k,v in after['files'].items() if k!=candidate},{k:v for k,v in before['files'].items() if k!=candidate})
        self.assertEqual(self.installed('photocraft').read_bytes(),b'SYNTHETIC photocraft');self.assertEqual(after['lock'],before['lock'])
        self.assertEqual(after['hosts'],before['hosts']);self.assertEqual(self.mcp_mutations(),[])
        self.assertEqual(load_json(self.paths['evidence_dir']/'photocraft.json')['probed_bin_dir'],str(self.bin))  # active evidence untouched
        self.assertEqual(load_json(Path(candidate))['status'],'failed');self.assertFalse((self.paths['state_dir']/'staging/photocraft').exists())
        self.assertFalse(s.recovery_marker(self.paths,'photocraft').exists())

    def test_failed_download_and_failed_provenance_preserve_the_working_installation(self):
        self.setup(['photocraft']);before=self.snapshot_state()
        self.world.releases['apps']['photocraft']['commit']='e5f6a7b8'*5;self.world.set_archive('photocraft',b'SYNTHETIC v2')
        self.world.fail_fetch={self.world.releases['apps']['photocraft']['assets']['macos']['name']}
        r=self.setup(['photocraft'],upgrade=True);self.assertEqual(r['status'],'failed');self.assertIn('synthetic network failure',r['apps'][0]['error'])
        self.assertEqual(self.snapshot_state(),before)
        self.world.fail_fetch=set();self.world.notarized=False
        r=self.setup(['photocraft'],upgrade=True);self.assertEqual(r['status'],'failed');self.assertIn('notarized',r['apps'][0]['error'])
        self.assertEqual(self.snapshot_state(),before);self.assertFalse((self.paths['state_dir']/'staging/photocraft').exists())

    def test_unmanaged_file_at_the_install_path_is_never_overwritten(self):
        self.setup(['vectorcraft'])  # creates the layout
        foreign=self.installed('photocraft');foreign.write_bytes(b'SOMEBODY ELSE');foreign.chmod(0o755)
        for upgrade in (False,True):
            r=self.setup(['photocraft'],upgrade=upgrade);self.assertEqual(r['status'],'failed');self.assertIn('move it aside',r['apps'][0]['error'])
        self.assertEqual(foreign.read_bytes(),b'SOMEBODY ELSE');self.assertNotIn('photocraft',load_json(self.lock)['apps'])
        # a managed binary whose bytes were changed behind Storytold's back is treated the same way
        self.installed('vectorcraft').write_bytes(b'TAMPERED')
        r=self.setup(['vectorcraft'],upgrade=True);self.assertEqual(r['status'],'failed');self.assertIn('differ from the SHA-256',r['apps'][0]['error'])
        self.assertEqual(self.installed('vectorcraft').read_bytes(),b'TAMPERED')

    def test_interrupted_promotion_is_completed_on_the_next_run(self):
        self.setup(['photocraft']);new=b'SYNTHETIC promoted but not pinned';old_pin=load_json(self.lock)['apps']['photocraft']
        marker=s.recovery_marker(self.paths,'photocraft');marker.parent.mkdir(exist_ok=True)
        marker.write_bytes(encoded({'schema_version':1,'app':'photocraft','candidate_sha256':digest(new),'previous_sha256':old_pin['sha256'],'previous_pin':old_pin,
                                    'commit':old_pin['revision'],'label':'0.7.0 (test, promoted)','written_at':'2026-10-12T00:00:00+00:00'}))
        self.installed('photocraft').write_bytes(new)  # the crash happened between os.replace and the lock rewrite
        self.assertEqual(s.recovery_state(self.paths,self.world.catalog,'photocraft')['state'],'completable')
        r=self.setup(['photocraft']);entry=r['apps'][0];self.assertEqual(r['status'],'passed',entry);self.assertEqual(entry['recovery'],'completable')
        self.assertTrue(any('completed an interrupted upgrade' in l for l in self.world.logs))
        self.assertEqual(load_json(self.lock)['apps']['photocraft']['sha256'],digest(new));self.assertTrue(entry['install']['unchanged']);self.assertFalse(marker.exists())

    def test_partial_host_registration_failure_is_reported_not_hidden(self):
        self.world.fail_add={'claude'}
        r=self.setup(['photocraft']);entry=r['apps'][0]
        self.assertEqual(r['status'],'failed');self.assertEqual(entry['status'],'partially_registered')
        self.assertEqual({x['host']:x['status'] for x in entry['registrations']},{'codex':'registered','claude':'failed'});self.assertIn('claude',entry['next'])
        self.assertTrue(self.installed('photocraft').is_file());self.assertIn('photocraft',load_json(self.lock)['apps'])
        self.world.fail_add=set();r=self.setup(['photocraft']);self.assertEqual(r['status'],'passed')
        self.assertEqual({x['host']:x['status'] for x in r['apps'][0]['registrations']},{'codex':'already_registered','claude':'registered'})

    def test_unreadable_registration_is_left_alone(self):
        self.setup(['photocraft']);self.world.claude_text_omits_command=True;self.world.calls.clear()
        r=self.setup(['photocraft'],replace=True);row=[x for x in r['apps'][0]['registrations'] if x['host']=='claude'][0]
        self.assertEqual(row['status'],'failed');self.assertIn('named no command',row['error']);self.assertEqual(self.mcp_mutations(),[])

    def test_lock_merge_keeps_other_apps(self):
        self.setup(['photocraft']);self.setup(['vectorcraft'])
        self.assertEqual(sorted(load_json(self.lock)['apps']),['photocraft','vectorcraft'])

    def test_differing_registration_refused_without_replace(self):
        self.world.hosts['codex']['photocraft']={'command':'/elsewhere/photocraft-cli','args':['mcp']}
        r=self.setup(['photocraft']);row=r['apps'][0]['registrations'][0]
        self.assertEqual(r['status'],'failed');self.assertEqual(row['status'],'failed');self.assertIn('--replace',row['error']);self.assertEqual(self.world.hosts['codex']['photocraft']['command'],'/elsewhere/photocraft-cli')
        r=self.setup(['photocraft'],replace=True);self.assertEqual(r['apps'][0]['status'],'registered')
        self.assertEqual(self.world.hosts['codex']['photocraft']['command'],str(self.installed('photocraft')))

    def test_only_hosts_on_path_are_registered(self):
        self.world.available={'codex'}
        r=self.setup(['photocraft']);self.assertEqual([x['host'] for x in r['apps'][0]['registrations']],['codex']);self.assertEqual(self.world.hosts['claude'],{})
        self.world.available=set();r=self.setup(['vectorcraft']);self.assertEqual(r['apps'][0]['status'],'installed_no_host_cli')

    def test_skip_probe_marks_binary_unverified(self):
        r=self.setup(['photocraft'],skip_probe=True)
        self.assertEqual(r['apps'][0]['probe'],{'status':'skipped','native_runtime_verified':False})
        self.assertFalse(any('probe' in c for c in self.world.calls));self.assertTrue(self.installed('photocraft').is_file())

    def test_first_failure_stops_the_batch(self):
        self.world.releases['apps']['photocraft']['assets']['macos']['sha256']='0'*64
        r=self.setup(['photocraft','vectorcraft']);self.assertEqual([a['status'] for a in r['apps']],['failed'])

    def test_remove_dry_run_mutates_nothing(self):
        self.setup(['photocraft']);before=self.snapshot_state();self.world.calls.clear()
        r=self.remove(['photocraft'],dry_run=True);entry=r['apps'][0]
        self.assertTrue(r['dry_run']);self.assertEqual(r['status'],'ok')
        self.assertEqual([x['action'] for x in entry['registrations']],['would unregister','would unregister'])
        self.assertEqual(entry['binary']['action'],'would delete');self.assertEqual(entry['pin']['action'],'would drop');self.assertEqual(entry['evidence']['action'],'would archive')
        self.assertEqual(self.snapshot_state(),before);self.assertEqual(self.mcp_mutations(),[])

    def test_remove_managed_app_unregisters_deletes_and_keeps_workspace(self):
        self.setup(['photocraft'])
        r=self.remove(['photocraft']);entry=r['apps'][0];self.assertEqual(r['status'],'ok')
        self.assertEqual([x['action'] for x in entry['registrations']],['unregister','unregister']);self.assertEqual(entry['binary']['action'],'delete')
        self.assertFalse(self.installed('photocraft').exists());self.assertEqual(load_json(self.lock)['apps'],{})
        self.assertTrue((self.home/'craft-work-storytold/outputs').is_dir());self.assertEqual(self.world.hosts,{'codex':{},'claude':{}})
        self.assertFalse((self.paths['evidence_dir']/'photocraft.json').exists());self.assertTrue(any((self.paths['evidence_dir']/'archive').iterdir()))

    def test_remove_keeps_a_binary_storytold_cannot_prove_it_owns(self):
        self.setup(['photocraft']);self.installed('photocraft').write_bytes(b'TAMPERED');self.world.calls.clear()
        r=self.remove(['photocraft']);entry=r['apps'][0]
        self.assertEqual(r['status'],'attention');self.assertEqual(entry['binary']['action'],'kept');self.assertIn('differ from the SHA-256',entry['binary']['reason'])
        self.assertEqual(self.installed('photocraft').read_bytes(),b'TAMPERED');self.assertIn('photocraft',load_json(self.lock)['apps']);self.assertEqual(entry['pin']['action'],'kept')
        self.assertEqual([x['action'] for x in entry['registrations']],['kept','kept']);self.assertIn('not provably',entry['registrations'][0]['reason'])
        self.assertEqual(self.mcp_mutations(),[])  # a registration pointing at a binary Storytold cannot vouch for is left for the operator
        # no lock entry at all: same protection
        self.setup(['vectorcraft']);lock=load_json(self.lock);del lock['apps']['vectorcraft'];self.lock.write_bytes(encoded(lock))
        r=self.remove(['vectorcraft']);self.assertEqual(r['apps'][0]['binary']['action'],'kept');self.assertIn('no lock entry',r['apps'][0]['binary']['reason']);self.assertTrue(self.installed('vectorcraft').is_file())

    def test_remove_keeps_an_unrelated_same_name_registration(self):
        self.world.hosts['codex']['photocraft']={'command':'/elsewhere/photocraft-cli','args':['mcp']}
        r=self.remove(['photocraft']);entry=r['apps'][0]
        self.assertEqual(r['status'],'attention');self.assertEqual(entry['registrations'][0]['action'],'kept');self.assertIn('/elsewhere/photocraft-cli',entry['registrations'][0]['reason'])
        self.assertEqual(self.world.hosts['codex']['photocraft']['command'],'/elsewhere/photocraft-cli');self.assertEqual(self.mcp_mutations(),[])
        self.world.claude_text_omits_command=True;self.world.hosts['claude']['photocraft']={'command':'/x','args':[]}
        r=self.remove(['photocraft']);self.assertEqual([x['action'] for x in r['apps'][0]['registrations']],['kept','kept']);self.assertEqual(self.mcp_mutations(),[])

    def test_status_lists_all_thirteen(self):
        self.setup(['photocraft'])
        r=s.status(hosts=None,env=self.env,home=self.home,system='Darwin',run=self.world.run,which=self.world.which,releases=self.world.releases,catalog=self.world.catalog)
        rows={a['app']:a for a in r['apps']};self.assertEqual(len(rows),13)
        self.assertTrue(rows['photocraft']['installed'] and rows['photocraft']['owned'] and rows['photocraft']['pinned_hash_matches'] and rows['photocraft']['manifest_commit_pinned'])
        self.assertEqual(sorted(rows['photocraft']['registered']),['claude','codex']);self.assertFalse(rows['cadcraft']['installed']);self.assertEqual(rows['photocraft']['recovery'],'none')

    def test_recorded_state_and_environment_precedence(self):
        self.setup(['photocraft'])
        self.assertEqual(s.resolve_paths(self.env,self.home,'Darwin')['bin_dir'],self.bin)
        other=self.home/'elsewhere';other.mkdir()
        self.assertEqual(s.resolve_paths({'CRAFT_BIN_DIR':str(other)},self.home,'Darwin')['bin_dir'],other)
        self.assertEqual(s.resolve_paths(self.env,self.home,'Darwin',bin_dir=str(other))['bin_dir'],other)

class PathsWithSpacesTests(SetupCase):
    home_name='home with spaces'
    def test_claude_user_scope_arguments_keep_their_boundaries(self):
        r=self.setup(['photocraft']);entry=r['apps'][0];self.assertEqual(r['status'],'passed',entry)
        self.assertIn(' ',str(self.home));self.assertEqual(entry['registrations'][1]['status'],'registered')
        current=s.host_get('claude','photocraft',self.world.run,self.world.which,self.env,self.home)
        self.assertEqual(current['args'],['mcp','--automation-read-root',str(self.home/'craft-work-storytold'),'--automation-write-root',str(self.home/'craft-work-storytold/outputs')])
        r=self.setup(['photocraft']);self.assertEqual(r['apps'][0]['registrations'][1]['status'],'already_registered')
    def test_text_only_claude_output_is_compared_whole_not_split(self):
        self.world.claude_json=False
        r=self.setup(['photocraft']);self.assertEqual(r['status'],'passed',r['apps'][0])
        current=s.host_get('claude','photocraft',self.world.run,self.world.which,self.env,self.home)
        self.assertIsNone(current['args']);self.assertIn('--automation-read-root '+str(self.home/'craft-work-storytold'),current['args_text'])
        launch={'command':str(self.installed('photocraft')),'args':['mcp','--automation-read-root',str(self.home/'craft-work-storytold'),'--automation-write-root',str(self.home/'craft-work-storytold/outputs')]}
        self.assertTrue(s.registration_matches(current,launch['command'],launch['args']))
        self.assertFalse(s.registration_matches(current,launch['command'],launch['args'][:-1]))
        # Setup stays idempotent on the whole-line match, but removal needs exact argument identity, which text output cannot prove.
        r=self.remove(['photocraft'],dry_run=True);rows={x['host']:x for x in r['apps'][0]['registrations']}
        self.assertEqual(rows['codex']['action'],'would unregister');self.assertEqual(rows['claude']['action'],'kept');self.assertIn('scope cannot be confirmed',rows['claude']['reason'])
        self.assertEqual(r['status'],'attention');self.assertIn('photocraft',self.world.hosts['claude'])

class LinuxSetupTests(SetupCase):
    system='Linux';machine='x86_64'
    def test_tarball_cli_is_extracted_and_sigstore_verified(self):
        self.world.sign('photocraft')
        r=self.setup(['photocraft']);entry=r['apps'][0];self.assertEqual(r['status'],'passed',entry)
        self.assertEqual(r['platform_key'],'linux-x86_64');self.assertTrue(entry['install']['sigstore']);self.assertNotIn('notarized',entry['install'])
        self.assertEqual(self.installed('photocraft').read_bytes(),b'SYNTHETIC photocraft');self.assertIn('sigstore',load_json(self.lock)['apps']['photocraft']['version'])
        self.assertTrue(any(c[0]=='fetch' and c[1].endswith('linux-x86_64.tar.gz') for c in self.world.calls))
        self.assertTrue(any(Path(c[0]).name=='cosign' and c[1]=='verify-blob' for c in self.world.calls))

    def test_missing_bundle_fails_closed_unless_upstream_sums_trusted(self):
        r=self.setup(['photocraft']);self.assertEqual(r['status'],'failed');self.assertIn('--trust-upstream-sums',r['apps'][0]['error'])
        self.assertFalse(self.installed('photocraft').exists())
        r=self.setup(['photocraft'],trust_upstream_sums=True);self.assertEqual(r['status'],'passed',r['apps'][0])
        self.assertEqual(r['apps'][0]['install']['provenance'],'upstream_sums_only');self.assertIn('upstream sums only',load_json(self.lock)['apps']['photocraft']['version'])
        self.assertTrue(any('WARNING' in line for line in self.world.logs))

    def test_missing_cosign_fails_closed(self):
        self.world.sign('photocraft');self.world.cosign_ok=None
        r=self.setup(['photocraft']);self.assertEqual(r['status'],'failed');self.assertIn('cosign is not on PATH',r['apps'][0]['error'])

    def test_tampered_binary_is_refused_before_cosign(self):
        self.world.sign('photocraft');self.world.signatures['bundles'][self.world.releases['apps']['photocraft']['assets']['linux-x86_64']['name']]['binary_sha256']='e'*64
        r=self.setup(['photocraft']);self.assertEqual(r['status'],'failed');self.assertIn('differs from the one the workflow signed',r['apps'][0]['error'])
        self.assertFalse(any(Path(c[0]).name=='cosign' for c in self.world.calls))

    def test_xdg_state_home_is_honored(self):
        xdg=self.home/'xdg';xdg.mkdir()
        self.assertEqual(s.state_dir({'XDG_STATE_HOME':str(xdg)},self.home,'Linux'),xdg/'storytold')

class WindowsSetupTests(SetupCase):
    system='Windows';machine='AMD64'
    def test_windows_paths_shims_and_venv(self):
        local=self.home/'AppData/Local';local.mkdir(parents=True);self.env={'LOCALAPPDATA':str(local)}
        self.world.sign('photocraft')
        r=self.setup(['photocraft']);entry=r['apps'][0];self.assertEqual(r['status'],'passed',entry)
        self.assertEqual(r['platform_key'],'windows-x64');self.assertEqual(self.bin,local/'Storytold/craft/bin');self.assertTrue(self.lock.is_relative_to(local/'Storytold/state'))
        self.assertTrue(any(c[0]=='fetch' and c[1].endswith('windows-x64-portable.zip') for c in self.world.calls))
        self.assertTrue(any(c[:3]==['cmd.exe','/d','/c'] and c[3].endswith('codex.cmd') for c in self.world.calls))
        import importlib.metadata,sys
        try: has_sdk=importlib.metadata.version('mcp')==s.SDK_VERSION
        except importlib.metadata.PackageNotFoundError: has_sdk=False
        probe_python=[c[0] for c in self.world.calls if 'probe' in c][0]
        self.assertEqual(probe_python,sys.executable) if has_sdk else self.assertTrue(probe_python.endswith(os.path.join('Scripts','python.exe')))
        self.assertEqual(self.world.hosts['claude']['photocraft']['command'],str(self.installed('photocraft')))

class PlatformTests(unittest.TestCase):
    def test_platform_keys(self):
        self.assertEqual(s.platform_key('Darwin','arm64'),'macos');self.assertEqual(s.platform_key('Darwin','x86_64'),'macos')
        self.assertEqual(s.platform_key('Linux','x86_64'),'linux-x86_64');self.assertEqual(s.platform_key('Windows','AMD64'),'windows-x64')
        for system,machine in (('Linux','aarch64'),('Windows','ARM64'),('FreeBSD','amd64')):
            with self.assertRaises(StorytoldError): s.platform_key(system,machine)
    def test_host_argv_wraps_cmd_shims_only(self):
        self.assertEqual(s.host_argv('codex',lambda h:'C:\\x\\codex.CMD'),['cmd.exe','/d','/c','C:\\x\\codex.CMD'])
        self.assertEqual(s.host_argv('codex',lambda h:'/usr/local/bin/codex'),['/usr/local/bin/codex']);self.assertIsNone(s.host_argv('codex',lambda h:None))
    def test_cmd_shim_refuses_paths_cmd_would_reinterpret(self):
        calls=[];run=lambda argv:(calls.append(argv),(0,'',''))[1]
        with self.assertRaisesRegex(StorytoldError,'cmd.exe would interpret'):
            s.host_add('codex','photocraft','C:\\Users\\a&b\\bin\\photocraft-cli.exe',['mcp'],run,lambda h:'C:\\x\\codex.cmd')
        self.assertEqual(calls,[])
        s.host_add('codex','photocraft','C:\\Users\\ab\\bin\\photocraft-cli.exe',['mcp'],run,lambda h:'C:\\x\\codex.cmd')
        self.assertEqual(calls[0][:4],['cmd.exe','/d','/c','C:\\x\\codex.cmd'])
    def test_probe_sdk_installs_only_hash_locked_wheels(self):
        from unittest import mock
        calls=[];state={'installed':False}
        def run(argv):
            calls.append(argv)
            if argv[1:3]==['-m','pip']: state['installed']=True;return (0,'','')
            if argv[1:2]==['-c']: return (0,s.SDK_VERSION+'\n','') if state['installed'] else (1,'','')
            return (0,'','')
        with tempfile.TemporaryDirectory() as d, mock.patch.object(s.importlib.metadata,'version',side_effect=s.importlib.metadata.PackageNotFoundError):
            s.probe_python(Path(d),run,lambda m:None,'Darwin')
        pip=[c for c in calls if c[1:3]==['-m','pip']][0]
        for flag in ('--isolated','--require-hashes','--only-binary=:all:'): self.assertIn(flag,pip)
        self.assertEqual(Path(pip[pip.index('-r')+1]).name,'requirements-probe.lock');self.assertNotIn(f'mcp=={s.SDK_VERSION}',pip)
    def test_mcp_get_failure_is_not_absence(self):
        broken=lambda argv:(1,'','Error: failed to parse config.toml')
        for host in ('codex','claude'):
            with self.assertRaisesRegex(StorytoldError,'could not be inspected'): s.host_get(host,'photocraft',broken,lambda h:'/fake/'+h)
            for answer in ("Error: No MCP server named 'photocraft' found.",'No MCP server named "photocraft". Configured servers: x'):
                self.assertIsNone(s.host_get(host,'photocraft',lambda argv,a=answer:(1,'',a),lambda h:'/fake/'+h))
    def test_codex_get_with_broken_json_is_a_parse_error_not_absence(self):
        current=s.host_get('codex','photocraft',lambda argv:(0,'not json',''),lambda h:'/fake/codex')
        self.assertIsNotNone(current);self.assertTrue(current['parse_error']);self.assertFalse(s.registration_matches(current,'/x',['mcp']))

class DownloadGuardTests(unittest.TestCase):
    def test_only_github_release_hosts(self):
        s.check_url('https://github.com/storytold/x/releases/download/v1/x.zip');s.check_url('https://objects.githubusercontent.com/a')
        for url in ('http://github.com/x','https://evil.example/x','https://github.com.evil.example/x'):
            with self.assertRaises(StorytoldError): s.check_url(url)
    def test_redirect_to_foreign_host_is_refused(self):
        guard=s._RedirectGuard();req=urllib.request.Request('https://github.com/storytold/x/releases/download/v1/x.zip')
        with self.assertRaises(StorytoldError): guard.redirect_request(req,None,302,'Found',{},'https://evil.example/x.zip')

class ExtractTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix='storytold-extract-');self.addCleanup(temp.cleanup);self.base=Path(temp.name).resolve();self.n=0
    def extract(self,data,suffix='.zip'):
        self.n+=1;archive=self.base/f'a{self.n}{suffix}';archive.write_bytes(data)
        return s.extract_cli(archive,self.base/f'out{self.n}','photocraft-cli')
    def test_takes_exactly_the_cli_and_ignores_the_desktop_binary(self):
        for data,suffix in ((synthetic_zip('photocraft-cli'),'.zip'),(synthetic_tar('photocraft-cli'),'.tar.gz')):
            p=self.extract(data,suffix);self.assertEqual(p.read_bytes(),b'SYNTHETIC CLI; MUST NOT EXECUTE');self.assertEqual(sorted(x.name for x in p.parent.iterdir()),['photocraft-cli'])
    def test_refuses_traversal_duplicates_and_links(self):
        with self.assertRaises(StorytoldError): self.extract(synthetic_zip('photocraft-cli',extra=[('../escape.txt',0o644,b'x')]))
        with self.assertRaises(StorytoldError): self.extract(synthetic_zip('photocraft-cli',extra=[('other/photocraft-cli',0o644,b'x')]))
        with self.assertRaises(StorytoldError): self.extract(synthetic_tar('photocraft-cli',extra=[('x/../../escape',0o644,b'x')]),'.tar.gz')
        out=io.BytesIO()
        with tarfile.open(fileobj=out,mode='w:gz') as t:
            info=tarfile.TarInfo('bin/photocraft-cli');info.type=tarfile.SYMTYPE;info.linkname='/bin/sh';t.addfile(info)
        with self.assertRaises(StorytoldError): self.extract(out.getvalue(),'.tar.gz')
    def test_unknown_archive_type_is_refused(self):
        with self.assertRaises(StorytoldError): self.extract(b'x','.rar')
