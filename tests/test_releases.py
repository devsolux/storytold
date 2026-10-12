import json
from pathlib import Path
import tempfile
import unittest
from storytold_tools.catalog import APP_IDS,load_catalog
from storytold_tools.common import ROOT,StorytoldError,encoded
from storytold_tools.releases import asset_url,load_releases,published_hash,sums_url

class ReleaseManifestTests(unittest.TestCase):
    def test_manifest_covers_twelve_apps_with_cli_assets(self):
        m=load_releases();catalog=load_catalog();self.assertEqual(set(m['apps']),set(APP_IDS))
        for app,row in m['apps'].items():
            self.assertEqual(row['assets']['macos']['name'],f"{catalog[app]['executable']}-{row['version']}-macos-universal.zip")
            self.assertTrue(asset_url(app,row,'macos').startswith(f'https://github.com/storytold/{app}/releases/download/{row["tag"]}/'))
            self.assertEqual(sums_url(app,row).rsplit('/',1)[1],'SHA256SUMS.txt')
    def test_manifest_is_canonical_json(self):
        self.assertEqual((ROOT/'config/releases.json').read_bytes(),encoded(load_releases()))
    def test_published_hash_accepts_both_sum_formats(self):
        h='a'*64;sums=(f'{h}  one.zip\n{"b"*64} *two.zip\n').encode()
        self.assertEqual(published_hash(sums,'one.zip'),h);self.assertEqual(published_hash(sums,'two.zip'),'b'*64)
        with self.assertRaises(StorytoldError): published_hash(sums,'three.zip')
        with self.assertRaises(StorytoldError): published_hash(sums+sums,'one.zip')
    def rewritten(self,mutate):
        m=json.loads(json.dumps(load_releases()));mutate(m)
        temp=tempfile.TemporaryDirectory(prefix='storytold-manifest-');self.addCleanup(temp.cleanup)
        root=Path(temp.name).resolve();(root/'config').mkdir();(root/'config/releases.json').write_bytes(encoded(m));return root
    def test_rejects_tag_version_and_asset_drift(self):
        for mutate in (lambda m:m['apps']['cadcraft'].update(tag='v9.9.9'),
                       lambda m:m['apps']['cadcraft']['assets']['macos'].update(name='cadcraft-cli-9.9.9-macos-universal.zip'),
                       lambda m:m['apps']['cadcraft'].update(commit='main'),
                       lambda m:m['apps'].pop('soundcraft'),
                       lambda m:m.update(apple_team_id='short')):
            with self.assertRaises(StorytoldError): load_releases(self.rewritten(mutate))
