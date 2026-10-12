"""Setup flow with injected network, macOS tools and host CLIs. Nothing real runs."""
import io
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
import urllib.request
import zipfile
from storytold_tools import setup as s
from storytold_tools.catalog import load_catalog
from storytold_tools.common import StorytoldError, digest, load_json
from storytold_tools.releases import load_releases

def synthetic_zip(exe, body=b'SYNTHETIC CLI; MUST NOT EXECUTE', extra=()):
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w') as z:
        for name,mode,data in ((f'{exe}-0.0.1-macos-universal/{exe}',0o755,body),(f'{exe}-0.0.1-macos-universal/README.md',0o644,b'readme'),*extra):
            info=zipfile.ZipInfo(name);info.external_attr=(stat.S_IFREG|mode)<<16;z.writestr(info,data)
    return out.getvalue()

class FakeWorld:
    def __init__(self):
        self.catalog=load_catalog();self.releases=json.loads(json.dumps(load_releases()));self.releases['apple_team_id']='TESTTEAM00'
        self.zips={};self.hosts={'codex':{},'claude':{}};self.available={'codex','claude'};self.calls=[];self.logs=[]
        self.notarized=True;self.team='TESTTEAM00';self.probe_status='discovery_and_call_passed';self.sums_override=None
        for app,row in self.releases['apps'].items():
            name=row['assets']['macos']['name'];data=synthetic_zip(app+'-cli',b'SYNTHETIC '+app.encode())
            self.zips[name]=data;row['assets']['macos'].update(sha256=digest(data),bytes=len(data))
    def fetch(self,url,dest,limit):
        s.check_url(url);name=url.rsplit('/',1)[1];self.calls.append(['fetch',url])
        data=(self.sums_override or ''.join(f'{digest(b)}  {n}\n' for n,b in self.zips.items())).encode() if name=='SHA256SUMS.txt' else self.zips[name]
        dest.write_bytes(data);return len(data)
    def which(self,host): return '/fake/bin/'+host if host in self.available else None
    def run(self,argv):
        self.calls.append(argv);tool=Path(argv[0]).name
        if tool=='spctl': return (0,'','accepted\nsource=Notarized Developer ID\n') if self.notarized else (3,'','rejected\nsource=no usable signature\n')
        if tool=='codesign': return (0,'',f'Identifier=test\nTeamIdentifier={self.team}\n')
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

class SetupTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix='storytold-setup-');self.addCleanup(temp.cleanup)
        self.home=Path(temp.name).resolve()/'home';self.home.mkdir();self.world=FakeWorld();self.env={}
    def setup(self,apps,**kw):
        w=self.world
        options=dict(acknowledge_unconfined=False,hosts=None,skip_probe=False,upgrade=False,replace=False,dry_run=False,timeout=5,
                     env=self.env,home=self.home,system='Darwin',fetch=w.fetch,run=w.run,which=w.which,log=w.logs.append,
                     releases=w.releases,catalog=w.catalog)
        options.update(kw);return s.setup(apps,**options)
    @property
    def bin(self): return self.home/'.local/opt/craft/bin'
    @property
    def lock(self): return self.home/'.local/state/storytold/installations.lock.json'

    def test_dry_run_touches_nothing(self):
        r=self.setup(['cadcraft','photocraft'],dry_run=True)
        self.assertTrue(r['dry_run']);self.assertEqual([a['needs_acknowledge_unconfined'] for a in r['apps']],[True,False])
        self.assertEqual(sorted(p.name for p in self.home.iterdir()),[]);self.assertEqual(self.world.calls,[])

    def test_confined_app_installs_pins_probes_and_registers(self):
        r=self.setup(['photocraft']);entry=r['apps'][0]
        self.assertEqual(r['status'],'passed',entry);self.assertEqual(entry['status'],'registered')
        binary=self.bin/'photocraft-cli';self.assertTrue(binary.is_file());self.assertEqual(binary.stat().st_mode&0o777,0o755)
        self.assertEqual(binary.read_bytes(),b'SYNTHETIC photocraft')
        lock=load_json(self.lock);self.assertEqual(lock['apps']['photocraft']['revision'],self.world.releases['apps']['photocraft']['commit'])
        self.assertEqual(lock['apps']['photocraft']['sha256'],digest(b'SYNTHETIC photocraft'))
        self.assertEqual(entry['probe']['status'],'discovery_and_call_passed');self.assertTrue((self.home/'.local/state/storytold/evidence/photocraft.json').is_file())
        work=self.home/'craft-work-storytold';expected=['mcp','--automation-read-root',str(work),'--automation-write-root',str(work/'outputs')]
        for host in ('codex','claude'):
            self.assertEqual(self.world.hosts[host]['photocraft'],{'command':str(binary),'args':expected})
        self.assertEqual(sorted(x['host'] for x in entry['registrations']),['claude','codex'])
        self.assertEqual(s.load_state(self.env,self.home)['bin_dir'],str(self.bin));self.assertTrue((work/'outputs').is_dir())

    def test_unconfined_app_needs_explicit_acknowledgement(self):
        r=self.setup(['cadcraft']);entry=r['apps'][0]
        self.assertEqual(entry['status'],'installed_not_registered');self.assertIn('--acknowledge-unconfined',entry['next'])
        self.assertTrue((self.bin/'cadcraft-cli').is_file());self.assertEqual(self.world.hosts,{'codex':{},'claude':{}})
        r=self.setup(['cadcraft'],acknowledge_unconfined=True,upgrade=True)
        self.assertEqual(r['apps'][0]['status'],'registered');self.assertEqual(self.world.hosts['codex']['cadcraft']['args'],['mcp'])

    def test_manifest_hash_mismatch_aborts_before_install(self):
        self.world.releases['apps']['photocraft']['assets']['macos']['sha256']='0'*64
        r=self.setup(['photocraft']);self.assertEqual(r['status'],'failed');self.assertIn('config/releases.json',r['apps'][0]['error'])
        self.assertFalse((self.bin/'photocraft-cli').exists())

    def test_upstream_sums_disagreement_aborts(self):
        name=self.world.releases['apps']['photocraft']['assets']['macos']['name']
        self.world.sums_override='f'*64+'  '+name+'\n'
        r=self.setup(['photocraft']);self.assertEqual(r['status'],'failed');self.assertIn('SHA256SUMS',r['apps'][0]['error'])

    def test_notarization_failure_installs_nothing(self):
        self.world.notarized=False
        r=self.setup(['photocraft']);self.assertEqual(r['status'],'failed');self.assertIn('notarized',r['apps'][0]['error'])
        self.assertFalse((self.bin/'photocraft-cli').exists())
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
        self.world.zips[name]=data=synthetic_zip('photocraft-cli',b'SYNTHETIC v2')
        self.world.releases['apps']['photocraft']['assets']['macos'].update(sha256=digest(data),bytes=len(data))
        r=self.setup(['photocraft'],upgrade=True);entry=r['apps'][0]
        self.assertEqual(entry['status'],'registered');self.assertEqual(entry['install']['previous_sha256'],digest(b'SYNTHETIC photocraft'))
        self.assertEqual((self.bin/'photocraft-cli').read_bytes(),b'SYNTHETIC v2');self.assertEqual(entry['registrations'][0]['status'],'already_registered')

    def test_lock_merge_keeps_other_apps(self):
        self.setup(['photocraft']);self.setup(['vectorcraft'])
        self.assertEqual(sorted(load_json(self.lock)['apps']),['photocraft','vectorcraft'])

    def test_differing_registration_refused_without_replace(self):
        self.world.hosts['codex']['photocraft']={'command':'/elsewhere/photocraft-cli','args':['mcp']}
        r=self.setup(['photocraft']);self.assertEqual(r['status'],'failed');self.assertIn('--replace',r['apps'][0]['error'])
        r=self.setup(['photocraft'],upgrade=True,replace=True);self.assertEqual(r['apps'][0]['status'],'registered')
        self.assertEqual(self.world.hosts['codex']['photocraft']['command'],str(self.bin/'photocraft-cli'))

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
        r=s.remove(['photocraft'],hosts=None,env=self.env,home=self.home,run=self.world.run,which=self.world.which,log=self.world.logs.append,catalog=self.world.catalog)
        entry=r['apps'][0];self.assertEqual(sorted(entry['hosts']),['claude','codex']);self.assertTrue(entry['binary_removed'] and entry['pin_removed'])
        self.assertFalse((self.bin/'photocraft-cli').exists());self.assertEqual(load_json(self.lock)['apps'],{})
        self.assertTrue((self.home/'craft-work-storytold/outputs').is_dir());self.assertEqual(self.world.hosts,{'codex':{},'claude':{}})

    def test_status_lists_all_twelve(self):
        self.setup(['photocraft'])
        r=s.status(hosts=None,env=self.env,home=self.home,run=self.world.run,which=self.world.which,releases=self.world.releases,catalog=self.world.catalog)
        rows={a['app']:a for a in r['apps']};self.assertEqual(len(rows),12)
        self.assertTrue(rows['photocraft']['installed'] and rows['photocraft']['pinned_hash_matches']);self.assertEqual(sorted(rows['photocraft']['registered']),['claude','codex'])
        self.assertFalse(rows['cadcraft']['installed']);self.assertEqual(rows['cadcraft']['registered'],[])

    def test_non_macos_is_refused_in_this_release(self):
        with self.assertRaises(StorytoldError): self.setup(['photocraft'],system='Linux')

    def test_recorded_state_and_environment_precedence(self):
        self.setup(['photocraft'])
        self.assertEqual(s.resolve_paths(self.env,self.home)['bin_dir'],self.bin)
        other=self.home/'elsewhere';other.mkdir()
        self.assertEqual(s.resolve_paths({'CRAFT_BIN_DIR':str(other)},self.home)['bin_dir'],other)
        self.assertEqual(s.resolve_paths(self.env,self.home,bin_dir=str(other))['bin_dir'],other)

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
        temp=tempfile.TemporaryDirectory(prefix='storytold-extract-');self.addCleanup(temp.cleanup);self.base=Path(temp.name).resolve()
    def extract(self,data):
        n=len(list(self.base.iterdir()));archive=self.base/f'a{n}.zip';archive.write_bytes(data)
        return s.extract_cli(archive,self.base/f'out{n}','photocraft-cli')
    def test_takes_exactly_the_cli(self):
        p=self.extract(synthetic_zip('photocraft-cli'));self.assertEqual(p.read_bytes(),b'SYNTHETIC CLI; MUST NOT EXECUTE');self.assertEqual(sorted(x.name for x in p.parent.iterdir()),['photocraft-cli'])
    def test_refuses_extra_executable(self):
        with self.assertRaises(StorytoldError): self.extract(synthetic_zip('photocraft-cli',extra=[('helper.sh',0o755,b'#!/bin/sh')]))
    def test_refuses_traversal_and_duplicates(self):
        with self.assertRaises(StorytoldError): self.extract(synthetic_zip('photocraft-cli',extra=[('../escape.txt',0o644,b'x')]))
        with self.assertRaises(StorytoldError): self.extract(synthetic_zip('photocraft-cli',extra=[('other/photocraft-cli',0o644,b'x')]))
