"""Setup flow on three simulated platforms with injected network, signing tools and host CLIs. Nothing real runs."""
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
from storytold_tools.common import StorytoldError, digest, load_json
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
    def __init__(self,system='Darwin',machine='arm64'):
        self.system=system;self.machine=machine;self.plat=s.platform_key(system,machine)
        self.catalog=load_catalog();self.releases=json.loads(json.dumps(load_releases()))
        self.releases['signers']={'apple_team_id':'TESTTEAM00','sigstore_identity_regexp':SIGNER,'sigstore_oidc_issuer':'https://token.actions.githubusercontent.com'}
        self.signatures={'schema_version':1,'signed_by':SIGNER,'bundles':{}}
        self.archives={};self.hosts={'codex':{},'claude':{}};self.available={'codex','claude'};self.calls=[];self.logs=[]
        self.notarized=True;self.team='TESTTEAM00';self.cosign_ok=True;self.probe_status='discovery_and_call_passed';self.sums_override=None
        for app,row in self.releases['apps'].items():
            for plat,asset in row['assets'].items():
                member=app+'-cli'+('.exe' if plat=='windows-x64' else '')
                data=synthetic_tar(member,b'SYNTHETIC '+app.encode()) if asset['name'].endswith('.tar.gz') else synthetic_zip(member,b'SYNTHETIC '+app.encode())
                self.archives[asset['name']]=data;asset.update(sha256=digest(data),bytes=len(data))
    def sign(self,app):
        asset=self.releases['apps'][app]['assets'][self.plat]
        self.signatures['bundles'][asset['name']]={'binary':app+'-cli'+('.exe' if self.plat=='windows-x64' else ''),'binary_sha256':digest(b'SYNTHETIC '+app.encode()),'archive_sha256':asset['sha256'],
            'bundle':{'mediaType':'application/vnd.dev.sigstore.bundle.v0.3+json','verificationMaterial':{'x':1},'messageSignature':{'y':2}}}
    def fetch(self,url,dest,limit):
        s.check_url(url);name=url.rsplit('/',1)[1];self.calls.append(['fetch',url])
        data=(self.sums_override or ''.join(f'{digest(b)}  {n}\n' for n,b in self.archives.items())).encode() if name=='SHA256SUMS.txt' else self.archives[name]
        dest.write_bytes(data);return len(data)
    def which(self,name):
        if name=='cosign': return '/fake/bin/cosign' if self.cosign_ok is not None else None
        if name in self.available: return ('C:\\fake\\'+name+'.cmd') if self.system=='Windows' else '/fake/bin/'+name
        return None
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
                if tool=='codex': return (0,json.dumps({'name':app,'transport':{'type':'stdio','command':row['command'],'args':row['args']}}),'')
                return (0,f"{app}:\n  Scope: User config\n  Command: {row['command']}\n  Args: {' '.join(row['args'])}\n",'')
            if sub=='add':
                i=argv.index('--');app=argv[i-1];store[app]={'command':argv[i+1],'args':argv[i+2:]};return (0,'','')
            if sub=='remove': store.pop(argv[-1],None);return (0,'','')
        if 'probe' in argv and any(a.endswith('storytold.py') for a in argv):
            out=Path(argv[argv.index('--output')+1]);app=argv[argv.index('--app')+1]
            if self.catalog[app]['confinement']=='os_only' and '--acknowledge-unconfined' not in argv:
                return (1,'',f'storytold: {app}: no verified native root flags; use tested OS isolation or explicitly acknowledge non-sensitive local testing')
            report={'status':self.probe_status,'tools':[{'name':'x'}],'protocol_version':'2025-11-25','server_info':{'name':app},'error':None if self.probe_status.endswith('passed') else {'type':'Synthetic','message':'synthetic failure'}}
            out.write_text(json.dumps(report));return (0 if self.probe_status.endswith('passed') else 1,'','')
        if argv[1:3]==['-m','venv'] or argv[1:3]==['-m','pip']: return (0,'','')
        if argv[1]=='-c': return (0,'2.3.0\n','')
        raise AssertionError('unexpected command: '+' '.join(argv))

class SetupCase(unittest.TestCase):
    system='Darwin';machine='arm64'
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix='storytold-setup-');self.addCleanup(temp.cleanup)
        self.home=Path(temp.name).resolve()/'home';self.home.mkdir();self.world=FakeWorld(self.system,self.machine);self.env={}
    def setup(self,apps,**kw):
        w=self.world
        options=dict(acknowledge_unconfined=False,hosts=None,skip_probe=False,upgrade=False,replace=False,dry_run=False,timeout=5,
                     env=self.env,home=self.home,system=w.system,machine=w.machine,fetch=w.fetch,run=w.run,which=w.which,log=w.logs.append,
                     releases=w.releases,signatures=w.signatures,catalog=w.catalog)
        options.update(kw);return s.setup(apps,**options)
    @property
    def bin(self): return s.resolve_paths(self.env,self.home,self.world.system)['bin_dir']
    def installed(self,app): return self.bin/(app+'-cli'+('.exe' if os.name=='nt' else ''))
    @property
    def lock(self): return s.resolve_paths(self.env,self.home,self.world.system)['lock']

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
        self.assertEqual(entry['probe']['status'],'discovery_and_call_passed');self.assertTrue((self.home/'.local/state/storytold/evidence/photocraft.json').is_file())
        work=self.home/'craft-work-storytold';expected=['mcp','--automation-read-root',str(work),'--automation-write-root',str(work/'outputs')]
        for host in ('codex','claude'):
            self.assertEqual(self.world.hosts[host]['photocraft'],{'command':str(binary),'args':expected})
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

    def test_unconfined_app_needs_explicit_acknowledgement(self):
        r=self.setup(['cadcraft']);entry=r['apps'][0]
        self.assertEqual(entry['status'],'installed_not_registered');self.assertIn('--acknowledge-unconfined',entry['next'])
        self.assertTrue((self.installed('cadcraft')).is_file());self.assertEqual(self.world.hosts,{'codex':{},'claude':{}})
        r=self.setup(['cadcraft'],acknowledge_unconfined=True)
        self.assertEqual(r['apps'][0]['status'],'registered');self.assertEqual(self.world.hosts['codex']['cadcraft']['args'],['mcp'])

    def test_manifest_hash_mismatch_aborts_before_install(self):
        self.world.releases['apps']['photocraft']['assets']['macos']['sha256']='0'*64
        r=self.setup(['photocraft']);self.assertEqual(r['status'],'failed');self.assertIn('config/releases.json',r['apps'][0]['error'])
        self.assertFalse((self.installed('photocraft')).exists())

    def test_upstream_sums_disagreement_aborts(self):
        name=self.world.releases['apps']['photocraft']['assets']['macos']['name'];self.world.sums_override='f'*64+'  '+name+'\n'
        r=self.setup(['photocraft']);self.assertEqual(r['status'],'failed');self.assertIn('SHA256SUMS',r['apps'][0]['error'])

    def test_notarization_failure_installs_nothing(self):
        self.world.notarized=False
        r=self.setup(['photocraft']);self.assertEqual(r['status'],'failed');self.assertIn('notarized',r['apps'][0]['error'])
        self.assertFalse((self.installed('photocraft')).exists())
        self.assertEqual([p.name for p in (self.home/'.local/state/storytold').iterdir() if p.name.startswith('storytold-download-')],[])

    def test_wrong_signing_team_is_refused(self):
        self.world.team='OTHERTEAM1'
        r=self.setup(['photocraft']);self.assertEqual(r['status'],'failed');self.assertIn('OTHERTEAM1',r['apps'][0]['error'])

    def test_rerun_is_idempotent_and_resumes_without_upgrade(self):
        self.setup(['photocraft']);self.world.calls.clear()
        r=self.setup(['photocraft','cadcraft'],acknowledge_unconfined=True);self.assertEqual(r['status'],'passed',r['apps'])
        self.assertTrue(r['apps'][0]['install']['unchanged']);self.assertEqual(r['apps'][0]['registrations'][0]['status'],'already_registered')
        self.assertFalse(any(c[0]=='fetch' and 'photocraft' in c[1] for c in self.world.calls));self.assertEqual(r['apps'][1]['status'],'registered')

    def test_existing_binary_with_different_pin_needs_upgrade_flag(self):
        self.setup(['photocraft']);self.world.releases['apps']['photocraft']['commit']='a1b2c3d4'*5
        r=self.setup(['photocraft']);self.assertEqual(r['status'],'failed');self.assertIn('--upgrade',r['apps'][0]['error'])
        name=self.world.releases['apps']['photocraft']['assets']['macos']['name']
        self.world.archives[name]=data=synthetic_zip('photocraft-cli',b'SYNTHETIC v2')
        self.world.releases['apps']['photocraft']['assets']['macos'].update(sha256=digest(data),bytes=len(data))
        r=self.setup(['photocraft'],upgrade=True);entry=r['apps'][0]
        self.assertEqual(entry['status'],'registered');self.assertEqual(entry['install']['previous_sha256'],digest(b'SYNTHETIC photocraft'))
        self.assertEqual((self.installed('photocraft')).read_bytes(),b'SYNTHETIC v2');self.assertEqual(entry['registrations'][0]['status'],'already_registered')

    def test_lock_merge_keeps_other_apps(self):
        self.setup(['photocraft']);self.setup(['vectorcraft'])
        self.assertEqual(sorted(load_json(self.lock)['apps']),['photocraft','vectorcraft'])

    def test_differing_registration_refused_without_replace(self):
        self.world.hosts['codex']['photocraft']={'command':'/elsewhere/photocraft-cli','args':['mcp']}
        r=self.setup(['photocraft']);self.assertEqual(r['status'],'failed');self.assertIn('--replace',r['apps'][0]['error'])
        r=self.setup(['photocraft'],replace=True);self.assertEqual(r['apps'][0]['status'],'registered')
        self.assertEqual(self.world.hosts['codex']['photocraft']['command'],str(self.installed('photocraft')))

    def test_only_hosts_on_path_are_registered(self):
        self.world.available={'codex'}
        r=self.setup(['photocraft']);self.assertEqual([x['host'] for x in r['apps'][0]['registrations']],['codex']);self.assertEqual(self.world.hosts['claude'],{})
        self.world.available=set();r=self.setup(['vectorcraft']);self.assertEqual(r['apps'][0]['status'],'installed_no_host_cli')

    def test_skip_probe_marks_binary_unverified(self):
        r=self.setup(['photocraft'],skip_probe=True)
        self.assertEqual(r['apps'][0]['probe'],{'status':'skipped','native_runtime_verified':False})
        self.assertFalse(any('probe' in c for c in self.world.calls))

    def test_probe_failure_stops_before_registration(self):
        self.world.probe_status='failed'
        r=self.setup(['photocraft']);self.assertEqual(r['status'],'failed');self.assertIn('native probe failed',r['apps'][0]['error'])
        self.assertEqual(self.world.hosts['codex'],{});self.assertTrue((self.home/'.local/state/storytold/evidence/photocraft.json').is_file())

    def test_first_failure_stops_the_batch(self):
        self.world.releases['apps']['photocraft']['assets']['macos']['sha256']='0'*64
        r=self.setup(['photocraft','vectorcraft']);self.assertEqual([a['status'] for a in r['apps']],['failed'])

    def test_remove_unregisters_and_deletes_but_keeps_workspace(self):
        self.setup(['photocraft'])
        r=s.remove(['photocraft'],hosts=None,env=self.env,home=self.home,system='Darwin',run=self.world.run,which=self.world.which,log=self.world.logs.append,catalog=self.world.catalog)
        entry=r['apps'][0];self.assertEqual(sorted(entry['hosts']),['claude','codex']);self.assertTrue(entry['binary_removed'] and entry['pin_removed'])
        self.assertFalse((self.installed('photocraft')).exists());self.assertEqual(load_json(self.lock)['apps'],{})
        self.assertTrue((self.home/'craft-work-storytold/outputs').is_dir());self.assertEqual(self.world.hosts,{'codex':{},'claude':{}})

    def test_status_lists_all_twelve(self):
        self.setup(['photocraft'])
        r=s.status(hosts=None,env=self.env,home=self.home,system='Darwin',run=self.world.run,which=self.world.which,releases=self.world.releases,catalog=self.world.catalog)
        rows={a['app']:a for a in r['apps']};self.assertEqual(len(rows),12)
        self.assertTrue(rows['photocraft']['installed'] and rows['photocraft']['pinned_hash_matches'] and rows['photocraft']['manifest_commit_pinned'])
        self.assertEqual(sorted(rows['photocraft']['registered']),['claude','codex']);self.assertFalse(rows['cadcraft']['installed'])

    def test_recorded_state_and_environment_precedence(self):
        self.setup(['photocraft'])
        self.assertEqual(s.resolve_paths(self.env,self.home,'Darwin')['bin_dir'],self.bin)
        other=self.home/'elsewhere';other.mkdir()
        self.assertEqual(s.resolve_paths({'CRAFT_BIN_DIR':str(other)},self.home,'Darwin')['bin_dir'],other)
        self.assertEqual(s.resolve_paths(self.env,self.home,'Darwin',bin_dir=str(other))['bin_dir'],other)

class LinuxSetupTests(SetupCase):
    system='Linux';machine='x86_64'
    def test_tarball_cli_is_extracted_and_sigstore_verified(self):
        self.world.sign('photocraft')
        r=self.setup(['photocraft']);entry=r['apps'][0];self.assertEqual(r['status'],'passed',entry)
        self.assertEqual(r['platform_key'],'linux-x86_64');self.assertTrue(entry['install']['sigstore']);self.assertNotIn('notarized',entry['install'])
        self.assertEqual((self.installed('photocraft')).read_bytes(),b'SYNTHETIC photocraft');self.assertIn('sigstore',load_json(self.lock)['apps']['photocraft']['version'])
        self.assertTrue(any(c[0]=='fetch' and c[1].endswith('linux-x86_64.tar.gz') for c in self.world.calls))
        self.assertTrue(any(Path(c[0]).name=='cosign' and c[1]=='verify-blob' for c in self.world.calls))

    def test_missing_bundle_fails_closed_unless_upstream_sums_trusted(self):
        r=self.setup(['photocraft']);self.assertEqual(r['status'],'failed');self.assertIn('--trust-upstream-sums',r['apps'][0]['error'])
        self.assertFalse((self.installed('photocraft')).exists())
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
