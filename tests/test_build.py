from pathlib import Path
import io
import json
import os
import shutil
import subprocess
import sys
import unittest
import zipfile
from storytold_tools.build import source_map,render,build,package,clean,disposable,allowlist,ensure_owned
from storytold_tools.common import ROOT,StorytoldError
from tests.support import WorkspaceCase

class BuildTests(WorkspaceCase):
    def setUp(self):
        super().setUp();self.repo=self.base/'repository with spaces';self.repo.mkdir()
        for name,data in source_map().items():
            p=self.repo/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    def test_shared_manifest_identity_and_skill(self):
        target=build(self.repo)
        for name in ('plugin.json','.claude-plugin/plugin.json'):
            manifest=json.loads((target/name).read_text())
            self.assertEqual((manifest['name'],manifest['license']),('storytold','MIT'))
        self.assertTrue((target/'LICENSE').read_text().startswith('MIT License'))
        # Root plugin.json carries the OpenAI extension; the legacy overlay is not shipped.
        self.assertFalse((target/'.codex-plugin').exists())
        interface=json.loads((target/'plugin.json').read_text())['extensions']['com.openai']['interface']
        self.assertEqual((interface['displayName'],interface['developerName']),('Storytold','devsolux'))
        self.assertTrue((target/'skills/craft/SKILL.md').exists())
        self.assertFalse((target/'.mcp.json').exists());self.assertFalse((target/'mcp.json').exists())
    def test_generated_drift_is_detected(self):
        build(self.repo);p=self.repo/'skills/craft/SKILL.md';p.write_text(p.read_text()+'\nSource change.\n')
        with self.assertRaises(StorytoldError): build(self.repo,check=True)
        build(self.repo);build(self.repo,check=True)
    def test_user_edit_in_generated_file_preserved(self):
        target=build(self.repo);p=target/'README.md';p.write_text('user edit')
        with self.assertRaises(StorytoldError): build(self.repo)
        self.assertEqual(p.read_text(),'user edit')
    def test_unowned_target_not_adopted(self):
        p=self.repo/'plugins/storytold';p.mkdir(parents=True);(p/'mine').write_text('keep')
        with self.assertRaises(StorytoldError): build(self.repo)
        self.assertEqual((p/'mine').read_text(),'keep')
    def test_unexpected_generated_empty_directory_preserved(self):
        p=build(self.repo);(p/'user-created').mkdir()
        with self.assertRaises(StorytoldError): build(self.repo)
        self.assertTrue((p/'user-created').exists())
    def test_private_unlisted_files_never_packaged(self):
        (self.repo/'.env').write_text('NOT_A_REAL_SECRET=test')
        (self.repo/'client-private.txt').write_text('private fixture')
        build(self.repo);p=package(self.repo,'source')
        with zipfile.ZipFile(p) as z:
            self.assertNotIn('storytold/.env',z.namelist());self.assertNotIn('storytold/client-private.txt',z.namelist())
    def test_reproducible_archives(self):
        build(self.repo)
        for kind in ('source','plugin'):
            first=package(self.repo,kind).read_bytes()
            self.assertEqual(first,package(self.repo,kind).read_bytes())
    def test_archive_has_valid_sorted_confined_members(self):
        build(self.repo)
        with zipfile.ZipFile(package(self.repo,'plugin')) as z:
            self.assertIsNone(z.testzip());self.assertEqual(z.namelist(),sorted(z.namelist()))
            self.assertTrue(all('..' not in Path(n).parts and not n.startswith('/') for n in z.namelist()))
    def test_relocation_and_packaged_cli(self):
        build(self.repo);new=self.repo.with_name('relocated');self.repo.rename(new)
        build(new,check=True)
        r=subprocess.run([sys.executable,str(new/'plugins/storytold/storytold.py'),'doctor'],capture_output=True,text=True,check=False)
        self.assertEqual(r.returncode,0,r.stderr)
        version=json.loads((new/'packaging/project.json').read_text())['version']
        self.assertEqual(json.loads(r.stdout)['storytold'],version)
    def test_archive_change_is_not_silent_overwrite(self):
        build(self.repo);p=package(self.repo);p.write_bytes(b'user changed archive')
        with self.assertRaises(StorytoldError): package(self.repo)
        self.assertEqual(p.read_bytes(),b'user changed archive')
    def test_clean_preserves_workspace_venv_and_plugin(self):
        build(self.repo)
        (self.repo/'.venv').mkdir();(self.repo/'.venv/keep').write_text('keep')
        disposable(self.repo,'.build');disposable(self.repo,'dist')
        clean(self.repo)
        self.assertTrue((self.repo/'.venv/keep').exists());self.assertTrue((self.repo/'plugins/storytold').exists())
        self.assertTrue(self.work.exists())
    def test_clean_validates_all_targets_before_deleting(self):
        disposable(self.repo,'.build');(self.repo/'dist').mkdir();(self.repo/'dist/keep').write_text('keep')
        with self.assertRaises((OSError,StorytoldError)): clean(self.repo)
        self.assertTrue((self.repo/'.build').exists());self.assertTrue((self.repo/'dist/keep').exists())
    def test_source_symlink_rejected(self):
        p=self.repo/'README.md';p.unlink()
        try:p.symlink_to(ROOT/'README.md')
        except OSError as e:self.skipTest('OS symlinks unavailable: '+str(e))
        with self.assertRaises(StorytoldError): render(self.repo)
    def test_install_commands_are_correct_and_opt_in(self):
        if not shutil.which('make'):self.skipTest('GNU make unavailable')
        r=subprocess.run(['make','-n','install-claude','install-codex','PYTHON='+sys.executable],cwd=self.repo,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn('claude plugin install storytold@devsolux-storytold',r.stdout)
        self.assertIn('codex plugin add storytold@devsolux-storytold',r.stdout)
        r=subprocess.run(['make','-n','build','PYTHON='+sys.executable],cwd=self.repo,capture_output=True,text=True)
        self.assertNotIn('plugin install',r.stdout);self.assertNotIn('pip install',r.stdout)
        # Release and the push gate are offline; only explicit github-* targets publish.
        r=subprocess.run(['make','-n','release','publish-check','PYTHON='+sys.executable],cwd=self.repo,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        for word in ('git push','git commit','gh repo','plugin install','plugin add'):
            self.assertNotIn(word,r.stdout)

    def test_new_test_must_not_silently_escape_discovery(self):
        (self.repo/'tests/test_unlisted.py').write_text('def test_regression(): pass\n')
        with self.assertRaises(StorytoldError):
            source_map(self.repo)
