"""The workflow's own patch release after a pin move: version bump, changelog section and the jobs around them. Offline."""
from pathlib import Path
import tempfile
import unittest
from storytold_tools.catalog import load_catalog
from storytold_tools.common import ROOT,StorytoldError
from scripts.bump_release import bump,changelog,next_version,pin_moves

NAMES={app:row['name'] for app,row in load_catalog().items()}
REPORT={'reviewed':'2026-10-24','changed':['pdfcraft','cadcraft'],
        'moves':{'pdfcraft':{'from':'0.11.0','to':'0.11.1'},'cadcraft':{'from':'0.11.0','to':'0.11.0'}}}
PROJECT='{\n  "name": "storytold",\n  "version": "1.5.5",\n  "license": "MIT"\n}\n'
PREVIOUS='## 1.5.5 — 2026-10-23\n\nSummary.\n\n- Old entry.\n'
PINS='- Pins moved: CADCraft 0.11.0 (assets re-published), PdfCraft 0.11.0 → 0.11.1.\n'

class VersionTests(unittest.TestCase):
    def test_patch_bump(self):
        self.assertEqual(next_version('1.5.5'),'1.5.6');self.assertEqual(next_version('1.5.9'),'1.5.10')
    def test_malformed_versions_refused(self):
        for v in ('1.5','1.5.5-rc1','v1.5.5','1.5.x','1.5.5.1'):
            with self.assertRaisesRegex(StorytoldError,'unexpected project version'): next_version(v)

class PinMoveTests(unittest.TestCase):
    def test_sorted_by_display_name_and_republished_assets_named(self):
        self.assertEqual(pin_moves(REPORT,NAMES),['CADCraft 0.11.0 (assets re-published)','PdfCraft 0.11.0 → 0.11.1'])
    def test_no_move_unknown_app_or_malformed_move_refused(self):
        for report in ({'changed':[]},{'moves':{}},{'moves':[]},'not a report'):
            with self.assertRaisesRegex(StorytoldError,'no moved pin'): pin_moves(report,NAMES)
        with self.assertRaisesRegex(StorytoldError,'unknown app'): pin_moves({'moves':{'nope':{'from':'1','to':'2'}}},NAMES)
        with self.assertRaisesRegex(StorytoldError,'malformed move'): pin_moves({'moves':{'cadcraft':{'from':'1'}}},NAMES)

class BumpTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='storytold-bump-');self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();(self.root/'packaging').mkdir()
        self.project=self.root/'packaging/project.json';self.project.write_text(PROJECT,encoding='utf-8')
        self.log=self.root/'CHANGELOG.md'
    def test_unreleased_entries_follow_the_pins(self):
        self.log.write_text('# Changelog\n\n## Unreleased\n\n- Pending entry.\n  Continued.\n\n'+PREVIOUS,encoding='utf-8')
        result=bump(self.root,REPORT,NAMES,'2026-10-24','123')
        self.assertEqual((result['previous'],result['version'],result['changelog']),('1.5.5','1.5.6','unreleased_entries_kept'))
        self.assertEqual(result['pins'],['CADCraft 0.11.0 (assets re-published)','PdfCraft 0.11.0 → 0.11.1'])
        self.assertEqual(self.project.read_text(encoding='utf-8'),PROJECT.replace('1.5.5','1.5.6'))
        text=self.log.read_text(encoding='utf-8');flat=' '.join(text.split())
        self.assertTrue(text.startswith('# Changelog\n\n## 1.5.6 — 2026-10-24\n\nAutomated release by the daily Craft release refresh (run 123): 2 pins'),text)
        self.assertIn('2 pins moved on 2026-10-24. Each moved app needs its card and smoke tool rechecked at the new tag.',flat)
        self.assertNotIn('Unreleased',text);self.assertTrue(all(len(line)<=78 for line in text.splitlines()),text)
        self.assertTrue(text.endswith('\n\n'+PINS+'- Pending entry.\n  Continued.\n\n'+PREVIOUS),text)
    def test_new_section_without_unreleased(self):
        self.log.write_text('# Changelog\n\n'+PREVIOUS,encoding='utf-8')
        result=bump(self.root,REPORT,NAMES,'2026-10-24',None)
        self.assertEqual(result['changelog'],'new_section');text=self.log.read_text(encoding='utf-8')
        self.assertNotIn('run ',text);self.assertIn('refresh: 2 pins',text)
        self.assertTrue(text.startswith('# Changelog\n\n## 1.5.6 — 2026-10-24\n\n'));self.assertTrue(text.endswith('\n\n'+PINS+'\n'+PREVIOUS),text)
    def test_empty_unreleased_section_is_replaced(self):
        self.log.write_text('# Changelog\n\n## Unreleased\n\n'+PREVIOUS,encoding='utf-8')
        self.assertEqual(bump(self.root,REPORT,NAMES,'2026-10-24',None)['changelog'],'new_section')
        text=self.log.read_text(encoding='utf-8');self.assertNotIn('Unreleased',text);self.assertTrue(text.endswith(PINS+'\n'+PREVIOUS),text)
    def test_one_moved_pin_reads_singular(self):
        self.log.write_text('# Changelog\n\n'+PREVIOUS,encoding='utf-8')
        bump(self.root,{'moves':{'wordcraft':{'from':'0.9.0','to':'0.9.1'}}},NAMES,'2026-10-24','7')
        text=self.log.read_text(encoding='utf-8');self.assertIn('(run 7): 1 pin moved on 2026-10-24.',' '.join(text.split()));self.assertIn('- Pins moved: WordCraft 0.9.0 → 0.9.1.\n',text)
    def test_refusals_leave_both_files_unchanged(self):
        cases=(('## Unreleased\n','must start with'),('# Changelog\n\n## 1.5.6 — 2026-10-24\n\nTaken.\n','already has a 1.5.6 section'),
               ('# Changelog\n\nprose first\n','unexpected changelog layout'))
        for text,message in cases:
            self.log.write_text(text,encoding='utf-8')
            with self.assertRaisesRegex(StorytoldError,message): bump(self.root,REPORT,NAMES,'2026-10-24',None)
            self.assertEqual((self.project.read_text(encoding='utf-8'),self.log.read_text(encoding='utf-8')),(PROJECT,text))
        self.log.write_text('# Changelog\n\n'+PREVIOUS,encoding='utf-8')
        with self.assertRaisesRegex(StorytoldError,'no moved pin'): bump(self.root,{'moves':{}},NAMES,'2026-10-24',None)
        with self.assertRaises(ValueError): bump(self.root,REPORT,NAMES,'24.10.2026',None)
        self.project.write_text('{"version": "1.5.5", "nested": {"version": "1.5.5"}}',encoding='utf-8')
        with self.assertRaisesRegex(StorytoldError,'exactly once'): bump(self.root,REPORT,NAMES,'2026-10-24',None)
        self.project.write_text('{"version": 155}',encoding='utf-8')
        with self.assertRaisesRegex(StorytoldError,'must be a string'): bump(self.root,REPORT,NAMES,'2026-10-24',None)
        self.assertEqual(self.log.read_text(encoding='utf-8'),'# Changelog\n\n'+PREVIOUS)

class WorkflowTests(unittest.TestCase):
    """The refresh job bumps before it builds and checks; only the merge job, with gh alone, publishes the release."""
    def test_refresh_bumps_before_build_and_merge_publishes_after_the_merge(self):
        text=(ROOT/'.github/workflows/releases.yml').read_text(encoding='utf-8')
        refresh=text[text.index('\n  refresh:'):text.index('\n  publish:')];publish=text[text.index('\n  publish:'):text.index('\n  verify:')]
        merge=text[text.index('\n  merge:'):]
        self.assertLess(refresh.index('scripts/refresh_releases.py'),refresh.index('scripts/bump_release.py'))
        self.assertLess(refresh.index('scripts/bump_release.py'),refresh.index('scripts/build.py build'))
        self.assertLess(refresh.index('scripts/build.py build'),refresh.index('scripts/check.py'))
        for name in ('packaging/project.json','CHANGELOG.md'):
            self.assertIn(name,refresh);self.assertIn(name,publish)
        self.assertEqual(text.count('gh release create'),1);self.assertIn('gh release create',merge)
        self.assertNotIn('python',merge);self.assertNotIn('actions/checkout',merge)
        self.assertLess(merge.index('--match-head-commit'),merge.index('gh release create'))
        self.assertIn("needs.refresh.outputs.version != ''",merge);self.assertIn('--target "$MERGED_SHA"',merge)
    def test_ci_ignores_the_files_the_workflow_owns(self):
        text=(ROOT/'.github/workflows/ci.yml').read_text(encoding='utf-8');ignore=text[text.index('paths-ignore:'):text.index('workflow_dispatch:')]
        for name in ('config/releases.json','config/signatures.json','plugins/storytold/**','packaging/project.json','CHANGELOG.md'):
            self.assertIn('- '+name+'\n',ignore)
