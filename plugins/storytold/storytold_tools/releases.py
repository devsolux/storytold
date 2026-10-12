"""Reviewed upstream release manifest: pins users do not have to invent.

config/releases.json records, per app, the latest reviewed release tag, its
commit, the macOS CLI zip name/size/SHA-256 copied from the release's
SHA256SUMS.txt, and the read-only tool used for the smoke call. It is reviewed
source data, not evidence that a binary ran. scripts/refresh_releases.py
regenerates it for review; nothing at runtime fetches it from the network.
"""
from __future__ import annotations
from pathlib import Path
import re
from .catalog import APP_IDS
from .common import ROOT, keys, load_json, require, sha, text

PLATFORMS = {'macos': 'macos-universal.zip'}
MAX_ASSET = 512 * 1024 * 1024

def load_releases(root: Path = ROOT) -> dict:
    data = keys(load_json(root/'config/releases.json'), {'schema_version','basis','reviewed','apple_team_id','apps'}, label='release manifest')
    require(type(data['schema_version']) is int and data['schema_version']==1, 'unsupported release manifest version')
    text(data['basis'], 'manifest basis', 1024)
    require(re.fullmatch(r'\d{4}-\d{2}-\d{2}', text(data['reviewed'], 'review date', 10)), 'review date must be YYYY-MM-DD')
    require(re.fullmatch(r'[A-Z0-9]{10}', text(data['apple_team_id'], 'Apple team id', 10)), 'Apple team id must be ten characters')
    require(isinstance(data['apps'], dict) and set(data['apps'])==set(APP_IDS), 'release manifest must list exactly the twelve apps')
    require(list(data['apps'])==sorted(data['apps']), 'release manifest apps must be sorted')
    for app, row in data['apps'].items():
        keys(row, {'tag','commit','version','smoke_tool','assets'}, label=f'release {app}')
        version = text(row['version'], 'version', 32)
        require(re.fullmatch(r'\d+\.\d+\.\d+', version), f'{app}: semantic version required')
        require(row['tag']=='v'+version, f'{app}: tag must be v<version>')
        require(isinstance(row['commit'], str) and re.fullmatch('[0-9a-f]{40}', row['commit']), f'{app}: tag commit must be a full lowercase SHA-1')
        require(re.fullmatch(r'[a-z][a-z0-9_]*', text(row['smoke_tool'], 'smoke tool', 128)), f'{app}: smoke tool must be a plain tool name')
        require(isinstance(row['assets'], dict) and row['assets'] and set(row['assets'])<=set(PLATFORMS), f'{app}: unknown asset platform')
        for plat, asset in row['assets'].items():
            keys(asset, {'name','sha256','bytes'}, label=f'{app} {plat} asset')
            require(asset['name']==f'{app}-cli-{version}-{PLATFORMS[plat]}', f'{app}: asset name must be the CLI archive for {version}')
            sha(asset['sha256'])
            require(type(asset['bytes']) is int and 0<asset['bytes']<=MAX_ASSET, f'{app}: asset size out of range')
    return data

def asset_url(app: str, row: dict, plat: str) -> str:
    return f"https://github.com/storytold/{app}/releases/download/{row['tag']}/{row['assets'][plat]['name']}"

def sums_url(app: str, row: dict) -> str:
    return f"https://github.com/storytold/{app}/releases/download/{row['tag']}/SHA256SUMS.txt"

def published_hash(sums: bytes, name: str) -> str:
    """The SHA-256 that upstream's SHA256SUMS.txt publishes for one asset name."""
    found = []
    for line in sums.decode('utf-8', 'replace').splitlines():
        parts = line.split()
        if len(parts)==2 and parts[1].lstrip('*')==name:
            found.append(parts[0].lower())
    require(len(found)==1, f'SHA256SUMS.txt must list {name} exactly once')
    return sha(found[0])
