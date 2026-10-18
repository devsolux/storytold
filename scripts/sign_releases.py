"""Rotate config/signatures.json: keep current Sigstore bundles, sign new ones, publish atomically.

Workflow/maintainer network step (`make sign-releases`), meant to run in the
daily GitHub Actions job whose OIDC identity the manifest's
`signers.sigstore_identity_regexp` names. The previous store is read with the
same shape and signer checks as at runtime, but entries the manifest no longer
pins (or whose archive hash moved) are dropped instead of rejected. Every
archive without a current bundle is downloaded, checked against the manifest
and the release's SHA256SUMS.txt, its one `<app>-cli` extracted and signed
keyless with `cosign sign-blob --yes --bundle`. Each download and each signing
is tried up to three times, so one transient Fulcio, Rekor or download failure
among the 39 archives does not cost the whole run. The complete result is
strictly validated and then written over the old file in one atomic replace;
any failure before that leaves the previous store exactly as it was. Nothing is
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
import time
from typing import Callable, Sequence, TypeVar

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from storytold_tools.catalog import load_catalog
from storytold_tools.common import ROOT, StorytoldError, encoded, load_json, require, snapshot
from storytold_tools.releases import (PLATFORMS, asset_url, load_releases, partition_signature_store, published_hash,
                                      sums_url, validate_signature_store)
from storytold_tools.setup import MAX_DOWNLOAD, extract_cli, fetch

STORE = ROOT / 'config/signatures.json'
RETRY_DELAYS = (15.0, 45.0)  # seconds slept before the second and the third attempt
COSIGN_TIMEOUT = 600  # one sign-blob round trip; a hung cosign counts as a failed attempt
Fetcher = Callable[[str, Path, int], int]
Signer = Callable[[Path], dict]
T = TypeVar('T')


def retrying(call: Callable[[], T], what: str, retry_on: tuple[type[BaseException], ...], *,
             delays: Sequence[float] = RETRY_DELAYS, sleep: Callable[[float], None] = time.sleep,
             log: Callable[[str], None] = lambda s: None) -> T:
    """Return `call()`, repeating it after each delay while it raises `retry_on`; the last attempt's error propagates."""
    for delay in delays:
        try:
            return call()
        except retry_on as exc:
            log(f'{what}: {exc}; retrying in {delay:g}s')
            sleep(delay)
    return call()


def retrying_fetch(fetch: Fetcher, **kw) -> Fetcher:
    """Network errors are retried; a size-limit refusal (StorytoldError) is final."""
    return lambda url, dest, limit: retrying(lambda: fetch(url, dest, limit), url.rsplit('/', 1)[1], (OSError,), **kw)


def cosign_sign_blob(cosign: str, *, run: Callable[..., subprocess.CompletedProcess] = subprocess.run, **kw) -> Signer:
    """Sign with up to three fresh cosign processes; each has its own ephemeral key and certificate.

    A fresh process is what clears `409 createLogEntryConflict`: cosign's own
    HTTP retry resent an entry Rekor had already committed but not answered
    (release run 39116490412). A new key makes a new, distinct log entry; the
    orphaned one is harmless because only the returned bundle is published.
    """
    def attempt(binary: Path, bundle: Path) -> dict:
        bundle.unlink(missing_ok=True)
        try:
            r = run([cosign, 'sign-blob', '--yes', '--bundle', str(bundle), str(binary)], capture_output=True, text=True,
                    check=False, timeout=COSIGN_TIMEOUT)
        except subprocess.TimeoutExpired:
            raise StorytoldError(f'{binary.name}: cosign sign-blob timed out after {COSIGN_TIMEOUT}s') from None
        require(r.returncode == 0, f'{binary.name}: cosign sign-blob failed:\n{(r.stdout + r.stderr)[-800:]}')
        data = json.loads(bundle.read_text())
        require(isinstance(data, dict) and 'verificationMaterial' in data, f'{binary.name}: cosign produced no bundle')
        return data

    def sign_blob(binary: Path) -> dict:
        bundle = binary.with_name(binary.name + '.sigstore.json')
        return retrying(lambda: attempt(binary, bundle), binary.name, (ValueError, OSError), **kw)
    return sign_blob


def rotate(releases: dict, catalog: dict, previous: dict | None, *, fetch: Fetcher, sign_blob: Signer,
           resign_all: bool = False, log: Callable[[str], None] = lambda s: None) -> tuple[dict, dict]:
    """Build the complete store for `releases` from what `previous` still covers plus fresh signatures.

    Returns (store, summary). The store is strictly validated before it is
    returned, so a caller that publishes it cannot publish an invalid one.
    """
    current, stale = partition_signature_store(previous, releases) if previous is not None else ({}, {})
    bundles = {} if resign_all else dict(current)
    signed = []
    with tempfile.TemporaryDirectory(prefix='storytold-sign-') as td:
        work = Path(td).resolve()
        for app, row in releases['apps'].items():
            for plat in PLATFORMS:
                asset = row['assets'][plat]; name = asset['name']
                if name in bundles:
                    continue
                exe = catalog[app]['executable'] + ('.exe' if plat == 'windows-x64' else '')
                tmp = work / name.replace('.', '_'); tmp.mkdir()
                archive = tmp / name
                log(f'{name}: downloading and signing')
                fetch(asset_url(app, row, plat), archive, MAX_DOWNLOAD)
                archive_sha = snapshot(archive)[0]
                require(archive_sha == asset['sha256'], f'{name}: archive hash differs from the manifest')
                fetch(sums_url(app, row), tmp / 'SHA256SUMS.txt', 1024 * 1024)
                require(published_hash((tmp / 'SHA256SUMS.txt').read_bytes(), name) == archive_sha, f'{name}: upstream SHA256SUMS.txt disagrees')
                binary = extract_cli(archive, tmp / 'extract', exe)
                bundle = sign_blob(binary)
                require(isinstance(bundle, dict) and 'mediaType' in bundle and 'verificationMaterial' in bundle, f'{name}: signer returned no Sigstore bundle')
                bundles[name] = {'binary': exe, 'binary_sha256': snapshot(binary)[0], 'archive_sha256': archive_sha, 'bundle': bundle}
                signed.append(name)
                shutil.rmtree(tmp)
    store = {'schema_version': 1, 'signed_by': releases['signers']['sigstore_identity_regexp'], 'bundles': dict(sorted(bundles.items()))}
    validate_signature_store(store, releases)
    return store, {'signed': signed, 'kept': len(bundles) - len(signed), 'dropped': sorted(stale)}


def publish(path: Path, store: dict, releases: dict) -> None:
    """Write the validated store next to the old one and swap atomically; the old file survives any earlier failure."""
    validate_signature_store(store, releases)
    data = encoded(store)
    fd, name = tempfile.mkstemp(prefix='.signatures-', suffix='.json', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        validate_signature_store(load_json(Path(name)), releases)
        os.chmod(name, 0o644); os.replace(name, path)
    except BaseException:
        Path(name).unlink(missing_ok=True); raise


def main(argv: list[str]) -> int:
    cosign = shutil.which('cosign')
    if cosign is None:
        print('storytold sign-releases: cosign is not on PATH', file=sys.stderr)
        return 1
    def log(s: str) -> None:
        print('storytold sign-releases: ' + s, file=sys.stderr)
    try:
        releases = load_releases(); catalog = load_catalog()
        previous = load_json(STORE) if STORE.is_file() else None
        store, summary = rotate(releases, catalog, previous, fetch=retrying_fetch(fetch, log=log), sign_blob=cosign_sign_blob(cosign, log=log),
                                resign_all='--all' in argv, log=log)
        publish(STORE, store, releases)
        sys.stdout.buffer.write(encoded(summary))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print('storytold sign-releases: ' + str(exc) + '; the previous signature store was left unchanged', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
