"""Regenerate config/releases.json from the latest GitHub releases, for review.

Maintainer/workflow network step (`make refresh-releases`). It reads each app's
latest release, the tag's commit and the published SHA256SUMS.txt, keeps the
reviewed smoke tools and signers, and rewrites the manifest in canonical JSON
for all supported platforms. Review the diff and rerun make check before
committing; nothing is downloaded or executed beyond those small metadata files.
"""
from __future__ import annotations
from datetime import date
import json
import os
from pathlib import Path
import sys
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from storytold_tools.catalog import APP_IDS
from storytold_tools.common import ROOT, encoded, require
from storytold_tools.releases import PLATFORMS, asset_names, load_releases, published_hash

API = 'https://api.github.com/repos/storytold/'


def get(url: str, token: str | None) -> bytes:
    headers = {'User-Agent': 'storytold-refresh-releases', 'Accept': 'application/vnd.github+json'}
    if token and url.startswith(API):
        headers['Authorization'] = 'Bearer ' + token
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as response:
        data = response.read(4 * 1024 * 1024)
        require(len(data) < 4 * 1024 * 1024, 'unexpectedly large metadata response: ' + url)
        return data


def refresh(token: str | None) -> dict:
    current = load_releases()
    apps = {}
    changed = []
    for app in APP_IDS:
        release = json.loads(get(API + app + '/releases/latest', token))
        tag = release['tag_name']
        require(tag.startswith('v'), f'{app}: unexpected tag {tag}')
        version = tag[1:]
        by_name = {a['name']: int(a['size']) for a in release['assets']}
        sums = get(f'https://github.com/storytold/{app}/releases/download/{tag}/SHA256SUMS.txt', token)
        assets = {}
        for plat in PLATFORMS:
            name = next((n for n in asset_names(app, version, plat) if n in by_name), None)
            require(name is not None, f'{app}: release {tag} has no {plat} CLI archive')
            assets[plat] = {'name': name, 'sha256': published_hash(sums, name), 'bytes': by_name[name]}
        commit = json.loads(get(API + app + '/commits/' + tag, token))['sha']
        row = {'tag': tag, 'commit': commit, 'version': version, 'smoke_tool': current['apps'][app]['smoke_tool'], 'assets': assets}
        if row != current['apps'][app]:
            changed.append(app)
        apps[app] = row
    manifest = {'schema_version': 2, 'basis': current['basis'], 'reviewed': date.today().isoformat(),
                'signers': current['signers'], 'apps': dict(sorted(apps.items()))}
    (ROOT / 'config/releases.json').write_bytes(encoded(manifest))
    load_releases()
    return {'reviewed': manifest['reviewed'], 'changed': changed,
            'note': 'Review the diff. A changed app needs its card and smoke tool rechecked at the new tag; run sign_releases.py next.'}


def main() -> int:
    try:
        sys.stdout.buffer.write(encoded(refresh(os.getenv('GITHUB_TOKEN'))))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print('storytold refresh-releases: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
