"""Sign every pinned CLI binary keyless with Sigstore cosign; store the bundles.

Workflow/maintainer network step (`make sign-releases`), meant to run in the
daily GitHub Actions job whose OIDC identity the manifest's
`signers.sigstore_identity_regexp` names. For each archive in
config/releases.json that has no current bundle, it downloads the archive,
checks it against the manifest and the release's SHA256SUMS.txt, extracts the
one `<app>-cli`, records its SHA-256 and runs `cosign sign-blob --yes --bundle`
on it. Bundles for archives the manifest no longer pins are dropped. Nothing is
executed except cosign; the binaries are never run here.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from storytold_tools.catalog import load_catalog
from storytold_tools.common import ROOT, encoded, load_json, require, snapshot
from storytold_tools.releases import PLATFORMS, asset_url, load_releases, load_signatures, published_hash, sums_url
from storytold_tools.setup import MAX_DOWNLOAD, extract_cli, fetch

STORE = ROOT / 'config/signatures.json'


def sign(cosign: str, only_missing: bool = True) -> dict:
    releases = load_releases(); catalog = load_catalog()
    store = load_signatures(releases=releases) if STORE.is_file() else {'schema_version': 1, 'signed_by': releases['signers']['sigstore_identity_regexp'], 'bundles': {}}
    require(store['signed_by'] == releases['signers']['sigstore_identity_regexp'], 'signature store identity drift')
    bundles = {}
    signed = []
    with tempfile.TemporaryDirectory(prefix='storytold-sign-') as td:
        work = Path(td).resolve()
        for app, row in releases['apps'].items():
            for plat in PLATFORMS:
                asset = row['assets'][plat]; name = asset['name']
                existing = store['bundles'].get(name)
                if only_missing and existing and existing['archive_sha256'] == asset['sha256']:
                    bundles[name] = existing
                    continue
                exe = catalog[app]['executable'] + ('.exe' if plat == 'windows-x64' else '')
                tmp = work / name.replace('.', '_'); tmp.mkdir()
                archive = tmp / name
                fetch(asset_url(app, row, plat), archive, MAX_DOWNLOAD)
                archive_sha = snapshot(archive)[0]
                require(archive_sha == asset['sha256'], f'{name}: archive hash differs from the manifest')
                fetch(sums_url(app, row), tmp / 'SHA256SUMS.txt', 1024 * 1024)
                require(published_hash((tmp / 'SHA256SUMS.txt').read_bytes(), name) == archive_sha, f'{name}: upstream SHA256SUMS.txt disagrees')
                binary = extract_cli(archive, tmp / 'extract', exe)
                binary_sha = snapshot(binary)[0]
                bundle = tmp / (exe + '.sigstore.json')
                r = subprocess.run([cosign, 'sign-blob', '--yes', '--bundle', str(bundle), str(binary)], capture_output=True, text=True, check=False)
                require(r.returncode == 0, f'{name}: cosign sign-blob failed:\n{(r.stdout + r.stderr)[-800:]}')
                data = json.loads(bundle.read_text())
                require(isinstance(data, dict) and 'verificationMaterial' in data, f'{name}: cosign produced no bundle')
                bundles[name] = {'binary': exe, 'binary_sha256': binary_sha, 'archive_sha256': archive_sha, 'bundle': data}
                signed.append(name)
                shutil.rmtree(tmp)
    out = {'schema_version': 1, 'signed_by': releases['signers']['sigstore_identity_regexp'], 'bundles': dict(sorted(bundles.items()))}
    STORE.write_bytes(encoded(out))
    load_signatures(releases=releases)
    dropped = sorted(set(store['bundles']) - set(bundles))
    return {'signed': signed, 'kept': len(bundles) - len(signed), 'dropped': dropped}


def main() -> int:
    cosign = shutil.which('cosign')
    if cosign is None:
        print('storytold sign-releases: cosign is not on PATH', file=sys.stderr)
        return 1
    try:
        sys.stdout.buffer.write(encoded(sign(cosign, only_missing='--all' not in sys.argv[1:])))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print('storytold sign-releases: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
