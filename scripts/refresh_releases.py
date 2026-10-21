"""Regenerate config/releases.json from the latest GitHub releases, for review.

Maintainer/workflow network step (`make refresh-releases`). It reads each app's
latest release, the tag's commit and the published SHA256SUMS.txt, keeps the
reviewed smoke tools and signers, and rewrites the manifest in canonical JSON
for all supported platforms. Review the diff and rerun make check before
committing; nothing is downloaded or executed beyond those small metadata files.
Each of the 39 requests is tried up to three times (15 s, then 45 s apart) on a
dropped connection, a 5xx or a 429, so one GitHub hiccup does not cost the daily
run; any other HTTP error, such as a release without SHA256SUMS.txt, is final.
"""
from __future__ import annotations
import argparse
from datetime import date
import http.client
import json
import os
from pathlib import Path
import sys
from typing import Callable
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from storytold_tools.catalog import APP_IDS
from storytold_tools.common import ROOT, encoded, require
from storytold_tools.releases import PLATFORMS, asset_names, load_releases, published_hash, retrying, transient

API = 'https://api.github.com/repos/storytold/'
MAX_METADATA = 4 * 1024 * 1024
Logger = Callable[[str], None]


def get(url: str, token: str | None, *, urlopen: Callable = urllib.request.urlopen, **kw) -> bytes:
    """One small metadata file; a transient fault is retried, an HTTP client error or an oversized answer is final."""
    headers = {'User-Agent': 'storytold-refresh-releases', 'Accept': 'application/vnd.github+json'}
    if token and url.startswith(API):
        headers['Authorization'] = 'Bearer ' + token

    def once() -> bytes:
        with urlopen(urllib.request.Request(url, headers=headers), timeout=60) as response:
            data = response.read(MAX_METADATA)
            require(len(data) < MAX_METADATA, 'unexpectedly large metadata response: ' + url)
            return data
    return retrying(once, url, transient, **kw)


def version_key(app: str, version: str) -> tuple[int, ...]:
    parts = version.split('.')
    require(len(parts) == 3 and all(p.isascii() and p.isdigit() for p in parts), f'{app}: unexpected release version {version}')
    return tuple(int(p) for p in parts)


def guard(app: str, pinned: dict, latest: dict) -> None:
    """Refuse what a daily refresh must never accept unreviewed: a downgrade or a re-published tag."""
    require(version_key(app, latest['version']) >= version_key(app, pinned['version']),
            f"{app}: the latest release {latest['tag']} is older than the pinned {pinned['tag']}; review it by hand")
    if latest['tag'] != pinned['tag']:
        return
    require(latest['commit'] == pinned['commit'], f"{app}: tag {latest['tag']} now points at another commit; review it by hand")
    for plat, asset in latest['assets'].items():
        before = pinned['assets'].get(plat, {})
        if before.get('name') == asset['name']:
            require(before == asset, f"{app}: {asset['name']} was re-published under the unchanged tag {latest['tag']}; review it by hand")


def refresh(token: str | None, accept: frozenset[str] = frozenset(), *, log: Logger = lambda s: None) -> dict:
    """`accept` names apps whose guarded change a maintainer reviewed by hand; the workflow never passes it."""
    current = load_releases()
    require(accept <= set(APP_IDS), f'unknown app in --accept: {", ".join(sorted(accept - set(APP_IDS)))}')
    apps = {}
    changed = []
    for app in APP_IDS:
        release = json.loads(get(API + app + '/releases/latest', token, log=log))
        tag = release['tag_name']
        require(tag.startswith('v'), f'{app}: unexpected tag {tag}')
        version = tag[1:]
        by_name = {a['name']: int(a['size']) for a in release['assets']}
        sums = get(f'https://github.com/storytold/{app}/releases/download/{tag}/SHA256SUMS.txt', token, log=log)
        assets = {}
        for plat in PLATFORMS:
            name = next((n for n in asset_names(app, version, plat) if n in by_name), None)
            require(name is not None, f'{app}: release {tag} has no {plat} CLI archive')
            assets[plat] = {'name': name, 'sha256': published_hash(sums, name), 'bytes': by_name[name]}
        commit = json.loads(get(API + app + '/commits/' + tag, token, log=log))['sha']
        row = {'tag': tag, 'commit': commit, 'version': version, 'smoke_tool': current['apps'][app]['smoke_tool'], 'assets': assets}
        if app not in accept: guard(app, current['apps'][app], row)
        if row != current['apps'][app]:
            changed.append(app)
        apps[app] = row
    # The date moves only with a pin, so an unchanged upstream yields no diff and no pull request.
    manifest = {'schema_version': 2, 'basis': current['basis'], 'reviewed': date.today().isoformat() if changed else current['reviewed'],
                'signers': current['signers'], 'apps': dict(sorted(apps.items()))}
    path = ROOT / 'config/releases.json'
    previous = path.read_bytes()
    path.write_bytes(encoded(manifest))
    try:
        load_releases()
    except BaseException:
        path.write_bytes(previous)
        raise
    return {'reviewed': manifest['reviewed'], 'changed': changed,
            'note': 'Review the diff. A changed app needs its card and smoke tool rechecked at the new tag; run sign_releases.py next.'}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description='Rewrite config/releases.json from the latest upstream releases, for review.')
    p.add_argument('--accept', action='append', default=[], metavar='APP',
                   help='Skip the downgrade/re-publish guard for APP after reviewing that upstream change by hand (repeatable)')
    args = p.parse_args(argv)

    def log(s: str) -> None:
        print('storytold refresh-releases: ' + s, file=sys.stderr)
    try:
        sys.stdout.buffer.write(encoded(refresh(os.getenv('GITHUB_TOKEN'), frozenset(args.accept), log=log)))
        return 0
    except (OSError, ValueError, KeyError, TypeError, http.client.HTTPException) as exc:
        print('storytold refresh-releases: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
