import json
import os
import subprocess
import sys
from pathlib import Path
from storytold_tools.common import ROOT
from tests.support import WorkspaceCase

class CliTests(WorkspaceCase):
    def run_cli(self,*args,extra_env=None):
        env=os.environ.copy();env.update(extra_env or {})
        for key in ('CRAFT_BIN_DIR','CRAFT_WORK_ROOT','CRAFT_OUTPUT_ROOT'):env.pop(key,None)
        env['CODEX_HOME']=str(self.base/'codex-home')  # never read the operator's real Codex config
        env['STORYTOLD_STATE_DIR']=str(self.base/'state')  # nor the paths recorded by a real setup run
        return subprocess.run([sys.executable,str(ROOT/'storytold.py'),*args],capture_output=True,text=True,env=env)
    def test_doctor_never_executes(self):
        r=self.run_cli('doctor');self.assertEqual(r.returncode,0,r.stderr)
        report=json.loads(r.stdout);self.assertFalse(report['native_apps_executed'])
        self.assertEqual(report['storytold'],json.loads((ROOT/'packaging/project.json').read_text())['version'])
        self.assertEqual(len(report['connections']['apps']),12)
    def test_setup_refuses_contradictory_flags(self):
        for argv,needle in ((('setup','--remove','--all','--upgrade'),'--remove cannot be combined with --upgrade'),
                            (('setup','--remove','--all','--skip-probe','--replace'),'--replace, --skip-probe'),
                            (('setup','--list','--app','photocraft'),'--list is read-only')):
            r=self.run_cli(*argv);self.assertNotEqual(r.returncode,0,argv);self.assertEqual(r.stdout,'');self.assertIn(needle,r.stderr)
    def test_remove_dry_run_reaches_the_preview_and_changes_nothing(self):
        env_path=str(self.base/'empty-path');(self.base/'empty-path').mkdir()
        r=self.run_cli('setup','--remove','--dry-run','--app','photocraft','--bin-dir',str(self.base/'bin'),extra_env={'PATH':env_path})
        self.assertEqual(r.returncode,0,r.stderr);report=json.loads(r.stdout)
        self.assertTrue(report['dry_run']);self.assertEqual(report['status'],'ok');self.assertEqual(report['apps'][0]['binary']['action'],'none')
        self.assertEqual(report['hosts'] if 'hosts' in report else [],[]);self.assertEqual(sorted(p.name for p in self.base.iterdir() if p.name=='state'),[])
    def test_setup_requires_an_explicit_selection(self):
        r=self.run_cli('setup');self.assertNotEqual(r.returncode,0);self.assertEqual(r.stdout,'');self.assertIn('--app',r.stderr)
    def test_setup_dry_run_plans_without_touching_anything(self):
        import platform
        from storytold_tools.common import StorytoldError
        from storytold_tools.setup import platform_key
        r=self.run_cli('setup','--dry-run','--app','cadcraft','--bin-dir',str(self.base/'bin'))
        try: platform_key(platform.system(),platform.machine())
        except StorytoldError:
            self.assertNotEqual(r.returncode,0);self.assertIn('setup supports',r.stderr);return
        self.assertEqual(r.returncode,0,r.stderr);plan=json.loads(r.stdout)
        self.assertTrue(plan['dry_run']);self.assertEqual(plan['apps'][0]['install_to'],str(self.base/'bin'/('cadcraft-cli'+('.exe' if os.name=='nt' else ''))))
        self.assertTrue(plan['apps'][0]['needs_acknowledge_unconfined']);self.assertFalse((self.base/'state').exists())
    def test_apps_lists_twelve(self):
        r=self.run_cli('apps');self.assertEqual(len(json.loads(r.stdout)['apps']),12)
    def test_missing_env_fails_closed(self):
        r=self.run_cli('preflight','--lock',str(self.lock),'--app','photocraft')
        self.assertNotEqual(r.returncode,0);self.assertEqual(r.stdout,'');self.assertIn('missing CRAFT_BIN_DIR',r.stderr)
    def test_probe_requires_explicit_execution(self):
        r=self.run_cli('probe','--lock',str(self.lock),'--app','photocraft','--output',str(self.evidence/'new.json'))
        self.assertNotEqual(r.returncode,0);self.assertIn('confirm-execution',r.stderr)
    def test_probe_requires_call_approval(self):
        r=self.run_cli('probe','--lock',str(self.lock),'--app','photocraft','--confirm-execution',
                       '--call-json','no-file','--output',str(self.evidence/'new.json'))
        self.assertNotEqual(r.returncode,0);self.assertIn('supplied together',r.stderr)
    def test_probe_output_collision_precedes_launch(self):
        out=self.evidence/'existing.json';out.write_text('keep')
        r=self.run_cli('probe','--lock',str(self.lock),'--app','photocraft','--confirm-execution','--output',str(out))
        self.assertNotEqual(r.returncode,0);self.assertEqual(out.read_text(),'keep');self.assertIn('new file',r.stderr)
    def test_invalid_json_output_has_clean_diagnostic(self):
        (self.work/'outputs/bad.json').write_bytes(b'{')
        r=self.run_cli('verify-artifact','--work-root',str(self.work),'--path','outputs/bad.json','--format','json')
        self.assertNotEqual(r.returncode,0);self.assertNotIn('Traceback',r.stderr)

    def test_corrupt_container_audio_xml_has_clean_diagnostic(self):
        for fmt,content in [('docx',b'not a zip'),('wav',b'RIFFbad'),('svg',b'<svg>')]:
            with self.subTest(format=fmt):
                filename='bad.'+fmt
                (self.work/'outputs'/filename).write_bytes(content)
                result=self.run_cli('verify-artifact','--work-root',str(self.work),
                                    '--path','outputs/'+filename,'--format',fmt)
                self.assertNotEqual(result.returncode,0)
                self.assertEqual(result.stdout,'')
                self.assertNotIn('Traceback',result.stderr)

    def test_corrupt_ooxml_deflate_stream_has_clean_diagnostic(self):
        import io,random,zipfile
        rng=random.Random(1)
        body='<doc>'+''.join(rng.choice('abcdefgh ') for _ in range(20000))+'</doc>'
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('[Content_Types].xml','<Types/>');z.writestr('word/document.xml',body)
        data=bytearray(out.getvalue())
        # Damage compressed member bytes, not the ZIP directory, so zlib sees the corruption.
        start=data.find(b'word/document.xml')+len('word/document.xml')+200
        for i in range(start,start+16): data[i]^=0xA5
        (self.work/'outputs/corrupt.docx').write_bytes(bytes(data))
        r=self.run_cli('verify-artifact','--work-root',str(self.work),'--path','outputs/corrupt.docx','--format','docx')
        self.assertNotEqual(r.returncode,0);self.assertEqual(r.stdout,'');self.assertNotIn('Traceback',r.stderr)
