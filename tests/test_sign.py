"""Signature-store rotation with injected downloads and a fake signer; no network, no cosign."""
import json
from pathlib import Path
import tempfile
import unittest
from scripts.sign_releases import publish, rotate
from storytold_tools.catalog import load_catalog
from storytold_tools.common import StorytoldError, digest, encoded, load_json
from storytold_tools.releases import load_releases, partition_signature_store, validate_signature_store
from tests.test_setup import SIGNER, synthetic_tar, synthetic_zip

def bundle_for(name): return {'mediaType':'application/vnd.dev.sigstore.bundle.v0.3+json','verificationMaterial':{'for':name},'messageSignature':{}}

class Upstream:
    """Synthetic releases: every manifest asset maps to an archive whose CLI body is `<app> <tag>`."""
    def __init__(self):
        self.catalog=load_catalog();self.releases=json.loads(json.dumps(load_releases()))
        self.releases['signers']['sigstore_identity_regexp']=SIGNER;self.archives={};self.signed=[];self.fail_sign=False
        for app in self.releases['apps']: self.set_release(app,self.releases['apps'][app]['tag'])
    def set_release(self,app,tag,commit=None):
        row=self.releases['apps'][app];row['tag']=tag;row['version']=tag[1:];row['commit']=commit or row['commit']
        for plat,asset in row['assets'].items():
            suffix={'macos':f'-cli-{row["version"]}-macos-universal.zip','linux-x86_64':f'-{row["version"]}-linux-x86_64.tar.gz','windows-x64':f'-{row["version"]}-windows-x64-portable.zip'}[plat]
            member=app+'-cli'+('.exe' if plat=='windows-x64' else '');body=f'{app} {tag}'.encode()
            data=synthetic_tar(member,body) if suffix.endswith('.tar.gz') else synthetic_zip(member,body)
            asset.update(name=app+suffix,sha256=digest(data),bytes=len(data));self.archives[asset['name']]=data
    def fetch(self,url,dest,limit):
        name=url.rsplit('/',1)[1]
        data=''.join(f'{digest(b)}  {n}\n' for n,b in self.archives.items()).encode() if name=='SHA256SUMS.txt' else self.archives[name]
        dest.write_bytes(data);return len(data)
    def sign_blob(self,binary):
        if self.fail_sign: raise StorytoldError('synthetic signing failure')
        self.signed.append(binary.name);return bundle_for(binary.name+':'+digest(binary.read_bytes())[:8])
    def rotate(self,previous,**kw):
        return rotate(self.releases,self.catalog,previous,fetch=self.fetch,sign_blob=self.sign_blob,**kw)

class RotationTests(unittest.TestCase):
    def setUp(self): self.up=Upstream()
    def test_fresh_store_signs_every_pinned_archive(self):
        store,summary=self.up.rotate(None)
        self.assertEqual(len(store['bundles']),36);self.assertEqual(summary['kept'],0);self.assertEqual(len(summary['signed']),36);self.assertEqual(summary['dropped'],[])
        validate_signature_store(store,self.up.releases)
        entry=store['bundles'][self.up.releases['apps']['cadcraft']['assets']['macos']['name']]
        self.assertEqual(entry['binary'],'cadcraft-cli');self.assertEqual(entry['binary_sha256'],digest(b'cadcraft '+self.up.releases['apps']['cadcraft']['tag'].encode()))
    def test_repeated_rotation_with_no_changes_is_idempotent(self):
        store,_=self.up.rotate(None);self.up.signed.clear()
        again,summary=self.up.rotate(store)
        self.assertEqual(again,store);self.assertEqual(summary,{'signed':[],'kept':36,'dropped':[]});self.assertEqual(self.up.signed,[])
    def test_old_to_new_manifest_keeps_current_drops_stale_signs_new(self):
        store,_=self.up.rotate(None);old=dict(store['bundles'])
        for app,tag in (('cadcraft','v9.1.0'),('wordcraft','v9.2.0'),('soundcraft','v9.3.0')): self.up.set_release(app,tag)
        self.up.signed.clear();new,summary=self.up.rotate(store)
        self.assertEqual(len(new['bundles']),36);self.assertEqual(summary['kept'],27);self.assertEqual(len(summary['signed']),9)
        self.assertEqual(len(summary['dropped']),9);self.assertTrue(all(n in old and n not in new['bundles'] for n in summary['dropped']))
        for app in ('photocraft','gridcraft'):
            name=self.up.releases['apps'][app]['assets']['macos']['name'];self.assertEqual(new['bundles'][name],old[name])
        validate_signature_store(new,self.up.releases)
    def test_changed_archive_hash_with_same_name_is_resigned(self):
        store,_=self.up.rotate(None);name=self.up.releases['apps']['gridcraft']['assets']['linux-x86_64']['name']
        self.up.archives[name]=synthetic_tar('gridcraft-cli',b'rebuilt bytes');asset=self.up.releases['apps']['gridcraft']['assets']['linux-x86_64']
        asset.update(sha256=digest(self.up.archives[name]),bytes=len(self.up.archives[name]))  # upstream re-uploaded the archive under the same name
        with self.assertRaises(StorytoldError): validate_signature_store(store,self.up.releases)  # the strict runtime loader refuses the stale hash
        current,stale=partition_signature_store(store,self.up.releases);self.assertEqual(list(stale),[name]);self.assertEqual(len(current),35)
        self.up.signed.clear();new,summary=self.up.rotate(store)
        self.assertEqual(summary['signed'],[name]);self.assertEqual(summary['dropped'],[name]);self.assertEqual(new['bundles'][name]['binary_sha256'],digest(b'rebuilt bytes'))
    def test_malformed_cached_bundle_and_signer_drift_are_refused(self):
        store,_=self.up.rotate(None);name=next(iter(store['bundles']))
        broken=json.loads(json.dumps(store));broken['bundles'][name]['bundle']={'not':'a bundle'}
        with self.assertRaises(StorytoldError): self.up.rotate(broken)
        drift=json.loads(json.dumps(store));drift['signed_by']='^https://github\\.com/someone-else/.*$'
        with self.assertRaises(StorytoldError): self.up.rotate(drift)
        missing=json.loads(json.dumps(store));del missing['bundles'][name]['binary_sha256']
        with self.assertRaises(StorytoldError): self.up.rotate(missing)
    def test_signing_failure_publishes_nothing_and_keeps_the_previous_store(self):
        store,_=self.up.rotate(None)
        temp=tempfile.TemporaryDirectory(prefix='storytold-store-');self.addCleanup(temp.cleanup);path=Path(temp.name).resolve()/'signatures.json'
        publish(path,store,self.up.releases);before=path.read_bytes();self.assertEqual(before,encoded(store))
        self.up.set_release('deckcraft','v9.9.9');self.up.fail_sign=True
        with self.assertRaises(StorytoldError): self.up.rotate(store)
        self.assertEqual(path.read_bytes(),before);self.assertEqual([p.name for p in path.parent.iterdir()],['signatures.json'])
        with self.assertRaises(StorytoldError): publish(path,{'schema_version':1,'signed_by':SIGNER,'bundles':{'x.zip':{}}},self.up.releases)
        self.assertEqual(path.read_bytes(),before);self.assertEqual([p.name for p in path.parent.iterdir()],['signatures.json'])
    def test_resign_all_ignores_the_previous_store(self):
        store,_=self.up.rotate(None);self.up.signed.clear()
        _,summary=self.up.rotate(store,resign_all=True);self.assertEqual(len(summary['signed']),36);self.assertEqual(summary['kept'],0)
    def test_published_store_round_trips_through_the_strict_loader(self):
        store,_=self.up.rotate(None)
        temp=tempfile.TemporaryDirectory(prefix='storytold-store-');self.addCleanup(temp.cleanup);path=Path(temp.name).resolve()/'signatures.json'
        publish(path,store,self.up.releases);self.assertEqual(validate_signature_store(load_json(path),self.up.releases),store)
