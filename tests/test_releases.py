import http.client
import io
import json
from pathlib import Path
import tempfile
import unittest
import urllib.error
from storytold_tools.catalog import APP_IDS,load_catalog
from storytold_tools.common import ROOT,StorytoldError,encoded
from storytold_tools.releases import PLATFORMS,asset_names,asset_url,load_releases,load_signatures,published_hash,sums_url
from scripts.refresh_releases import MAX_METADATA,get,guard

class RefreshGuardTests(unittest.TestCase):
    """The daily refresh must stop, not pin, on a downgrade or a re-published tag."""
    def setUp(self): self.pinned=json.loads(json.dumps(load_releases()['apps']['soundcraft']))
    def latest(self,**changes): return json.loads(json.dumps(dict(self.pinned,**changes)))
    def test_unchanged_and_newer_releases_pass(self):
        guard('soundcraft',self.pinned,self.latest())
        guard('soundcraft',self.pinned,self.latest(tag='v99.0.0',version='99.0.0',commit='f'*40))
    def test_downgrade_is_refused(self):
        with self.assertRaisesRegex(StorytoldError,'older than the pinned'):
            guard('soundcraft',self.pinned,self.latest(tag='v0.0.1',version='0.0.1'))
    def test_moved_tag_and_reuploaded_asset_are_refused(self):
        with self.assertRaisesRegex(StorytoldError,'another commit'): guard('soundcraft',self.pinned,self.latest(commit='f'*40))
        row=self.latest();row['assets']['macos']['sha256']='e'*64
        with self.assertRaisesRegex(StorytoldError,'re-published'): guard('soundcraft',self.pinned,row)
    def test_a_newly_published_asset_name_under_the_same_tag_passes(self):
        row=self.latest();row['assets']['linux-x86_64']=dict(row['assets']['linux-x86_64'],name='soundcraft-cli-new.tar.gz',sha256='e'*64)
        guard('soundcraft',self.pinned,row)
    def test_prerelease_versions_are_refused(self):
        with self.assertRaisesRegex(StorytoldError,'unexpected release version'):
            guard('soundcraft',self.pinned,self.latest(tag='v99.0.0-rc1',version='99.0.0-rc1'))

class RefreshRetryTests(unittest.TestCase):
    """One GitHub hiccup among the 39 small metadata requests is retried; a client error is a finding about the release."""
    URL='https://api.github.com/repos/storytold/cadcraft/releases/latest'
    def setUp(self): self.calls=[];self.sleeps=[];self.logged=[]
    def urlopen(self,*outcomes):
        """Each outcome is the response body, or an exception the connection raises."""
        queue=list(outcomes)
        def open_(request,timeout):
            self.calls.append(request.full_url);self.assertEqual(timeout,60);self.assertEqual(request.get_header('Authorization'),'Bearer tok')
            outcome=queue.pop(0)
            if isinstance(outcome,BaseException): raise outcome
            return io.BytesIO(outcome)
        return open_
    def http_error(self,code): return urllib.error.HTTPError(self.URL,code,'synthetic',{},None)
    def get(self,*outcomes): return get(self.URL,'tok',urlopen=self.urlopen(*outcomes),sleep=self.sleeps.append,log=self.logged.append)
    def test_server_errors_rate_limits_and_dropped_connections_are_retried(self):
        self.assertEqual(self.get(self.http_error(503),self.http_error(429),b'{}'),b'{}')
        self.assertEqual((len(self.calls),self.sleeps),(3,[15.0,45.0]));self.assertTrue(self.logged[0].startswith(self.URL+': '));self.assertIn('retrying in 15s',self.logged[0])
        self.calls.clear();self.sleeps.clear()
        self.assertEqual(self.get(http.client.RemoteDisconnected('gone'),ConnectionResetError('reset'),b'ok'),b'ok')
        self.assertEqual((len(self.calls),self.sleeps),(3,[15.0,45.0]))
    def test_a_client_error_is_final(self):
        with self.assertRaises(urllib.error.HTTPError) as cm: self.get(self.http_error(404),b'{}')
        self.assertEqual((cm.exception.code,len(self.calls),self.sleeps),(404,1,[]))
    def test_the_third_failure_propagates(self):
        with self.assertRaises(urllib.error.HTTPError): self.get(self.http_error(502),self.http_error(502),self.http_error(502))
        self.assertEqual((len(self.calls),self.sleeps),(3,[15.0,45.0]))
    def test_an_oversized_answer_is_refused_without_retry(self):
        with self.assertRaisesRegex(StorytoldError,'unexpectedly large'): self.get(b'x'*MAX_METADATA)
        self.assertEqual((len(self.calls),self.sleeps),(1,[]))

class ReleaseManifestTests(unittest.TestCase):
    def test_manifest_covers_thirteen_apps_on_three_platforms(self):
        m=load_releases();catalog=load_catalog();self.assertEqual(set(m['apps']),set(APP_IDS))
        for app,row in m['apps'].items():
            self.assertEqual(set(row['assets']),set(PLATFORMS))
            for plat,asset in row['assets'].items():
                self.assertIn(asset['name'],asset_names(app,row['version'],plat))
                self.assertTrue(asset_url(app,row,plat).startswith(f'https://github.com/storytold/{app}/releases/download/{row["tag"]}/'))
            self.assertEqual(sums_url(app,row).rsplit('/',1)[1],'SHA256SUMS.txt')
        self.assertIn('devsolux/storytold',m['signers']['sigstore_identity_regexp'])
    def test_manifest_and_signature_store_are_canonical_json(self):
        self.assertEqual((ROOT/'config/releases.json').read_bytes(),encoded(load_releases()))
        self.assertEqual((ROOT/'config/signatures.json').read_bytes(),encoded(load_signatures()))
    def test_published_hash_accepts_both_sum_formats(self):
        h='a'*64;sums=(f'{h}  one.zip\n{"b"*64} *two.zip\n').encode()
        self.assertEqual(published_hash(sums,'one.zip'),h);self.assertEqual(published_hash(sums,'two.zip'),'b'*64)
        with self.assertRaises(StorytoldError): published_hash(sums,'three.zip')
        with self.assertRaises(StorytoldError): published_hash(sums+sums,'one.zip')
    def rewritten(self,mutate,signatures=None):
        m=json.loads(json.dumps(load_releases()));mutate(m)
        temp=tempfile.TemporaryDirectory(prefix='storytold-manifest-');self.addCleanup(temp.cleanup)
        root=Path(temp.name).resolve();(root/'config').mkdir();(root/'config/releases.json').write_bytes(encoded(m))
        if signatures is not None:(root/'config/signatures.json').write_bytes(encoded(signatures))
        return root
    def test_rejects_tag_version_asset_and_signer_drift(self):
        for mutate in (lambda m:m['apps']['cadcraft'].update(tag='v9.9.9'),
                       lambda m:m['apps']['cadcraft']['assets']['macos'].update(name='cadcraft-cli-9.9.9-macos-universal.zip'),
                       lambda m:m['apps']['cadcraft']['assets'].pop('windows-x64'),
                       lambda m:m['apps']['cadcraft'].update(commit='main'),
                       lambda m:m['apps'].pop('soundcraft'),
                       lambda m:m['signers'].update(apple_team_id='short'),
                       lambda m:m['signers'].update(sigstore_oidc_issuer='https://evil.example')):
            with self.assertRaises(StorytoldError): load_releases(self.rewritten(mutate))
    def test_signature_store_must_match_manifest(self):
        m=load_releases();name=m['apps']['cadcraft']['assets']['linux-x86_64']['name'];sha=m['apps']['cadcraft']['assets']['linux-x86_64']['sha256']
        good={'schema_version':1,'signed_by':m['signers']['sigstore_identity_regexp'],'bundles':{name:{'binary':'cadcraft-cli','binary_sha256':'c'*64,'archive_sha256':sha,'bundle':{'mediaType':'application/vnd.dev.sigstore.bundle.v0.3+json','verificationMaterial':{},'messageSignature':{}}}}}
        root=self.rewritten(lambda m:None,good);self.assertEqual(list(load_signatures(root)['bundles']),[name])
        for bad in (dict(good,signed_by='^other$'),
                    dict(good,bundles={'unknown.zip':good['bundles'][name]}),
                    dict(good,bundles={name:dict(good['bundles'][name],archive_sha256='d'*64)}),
                    dict(good,bundles={name:dict(good['bundles'][name],bundle={'not':'a bundle'})})):
            with self.assertRaises(StorytoldError): load_signatures(self.rewritten(lambda m:None,bad))
