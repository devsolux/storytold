"""Explicit one-command Craft CLI setup: stage, verify, probe, promote, pin, probe again, register.

Nothing here runs unless an operator invokes `storytold.py setup`. The command
downloads only the reviewed release archives named in config/releases.json,
checks each archive against the manifest and the release's own SHA256SUMS.txt,
takes exactly one `<app>-cli` out of it, checks provenance (Apple notarization
by the pinned team on macOS; the Sigstore bundle the daily workflow signed on
Linux and Windows, and on macOS too when cosign is present), runs the existing
preflight and official-SDK probe against that staged candidate, and only then
promotes it, pins it in the private lock, probes the active launch so the
evidence describes what hosts will run, and registers it through the host's
own CLI. A candidate that fails any step before promotion leaves the active
binary, its pin and the host registrations untouched; a failure after the
binary was replaced leaves a recovery marker that the next run reconciles.
Removal deletes only binaries the lock proves Storytold installed and no
host still launches, and unregisters only entries that are, in full, the
registration Storytold wrote. One changing run holds the state directory at a
time. It never edits host configuration files itself, starts no daemon, keeps
one registration per server name and never retries a write.
"""
from __future__ import annotations
from contextlib import contextmanager, nullcontext
from datetime import datetime, timezone
import errno
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import tomllib
from typing import Callable, Iterator
from urllib.parse import urlsplit
import urllib.request
import zipfile
from .catalog import APP_IDS, honours_roots, load_catalog, platform_id, preflight
from .common import MAX_JSON, ROOT, StorytoldError, absolute, create_new, directory, encoded, keys, load_json, parse_json, require, sha, snapshot
from .probe import SDK_VERSION
from .releases import asset_url, load_releases, load_signatures, published_hash, sums_url
from .workspace import MARKER, init_workspace, open_workspace

ALLOWED_HOSTS = {'github.com', 'objects.githubusercontent.com', 'release-assets.githubusercontent.com'}
MAX_DOWNLOAD = 512 * 1024 * 1024
STATE_FILE = 'setup.json'
RECOVERY_DIR = 'recovery'
HOSTS = ('codex', 'claude')
Runner = Callable[[list[str]], tuple[int, str, str]]
Fetcher = Callable[[str, Path, int], int]
Logger = Callable[[str], None]
Which = Callable[[str], str | None]

def platform_key(system: str = platform.system(), machine: str = platform.machine()) -> str:
    if system=='Darwin': return 'macos'
    if system=='Linux' and machine in {'x86_64', 'amd64'}: return 'linux-x86_64'
    if system=='Windows' and machine.lower() in {'amd64', 'x86_64'}: return 'windows-x64'
    raise StorytoldError(f'setup supports macOS (universal), Linux x86_64 and Windows x64; this is {system} {machine}. '
                         'Install the CLI by hand and follow docs/operations.md sections 1-5.')

def exe_name(catalog: dict, app: str) -> str:
    """Installed file name on this OS."""
    return catalog[app]['executable'] + ('.exe' if os.name=='nt' else '')

def member_name(catalog: dict, app: str, plat: str) -> str:
    """CLI file name inside an archive built for `plat`."""
    return catalog[app]['executable'] + ('.exe' if plat=='windows-x64' else '')

def launch_args(catalog: dict, app: str, paths: dict) -> list[str]:
    """The exact arguments Storytold registers for `app`, from the reviewed catalog."""
    return [{'{work}': str(paths['work_root']), '{outputs}': str(paths['output_root'])}.get(x, x) for x in catalog[app]['args']]

# ---------------------------------------------------------------- state/paths
def state_dir(env: dict, home: Path, system: str = platform.system()) -> Path:
    if env.get('STORYTOLD_STATE_DIR'): return absolute(env['STORYTOLD_STATE_DIR'])
    if system=='Windows': return absolute(Path(env.get('LOCALAPPDATA') or home/'AppData/Local')/'Storytold/state')
    if system=='Linux' and env.get('XDG_STATE_HOME'): return absolute(Path(env['XDG_STATE_HOME'])/'storytold')
    return absolute(home/'.local/state/storytold')

def load_state(env: dict, home: Path, system: str = platform.system()) -> dict:
    p = state_dir(env, home, system)/STATE_FILE
    if not p.is_file(): return {}
    data = keys(load_json(p), {'schema_version','bin_dir','work_root','output_root','lock','evidence_dir','updated_at'}, label='setup state')
    require(data['schema_version']==1, 'unsupported setup state')
    return data

def resolve_paths(env: dict, home: Path, system: str = platform.system(), **override: str | None) -> dict:
    """Flags, then CRAFT_* environment, then recorded state, then per-OS conventions."""
    st = load_state(env, home, system); sd = state_dir(env, home, system)
    if system=='Windows':
        bin_default = Path(env.get('LOCALAPPDATA') or home/'AppData/Local')/'Storytold/craft/bin'
    else:
        bin_default = home/'.local/opt/craft/bin'
    defaults = {'bin_dir': bin_default, 'work_root': home/'craft-work-storytold',
                'lock': sd/'installations.lock.json', 'evidence_dir': sd/'evidence'}
    envkeys = {'bin_dir': 'CRAFT_BIN_DIR', 'work_root': 'CRAFT_WORK_ROOT', 'lock': 'CRAFT_LOCK', 'evidence_dir': 'CRAFT_EVIDENCE_DIR'}
    paths = {}
    for key, default in defaults.items():
        value = override.get(key) or env.get(envkeys[key]) or st.get(key) or default
        paths[key] = absolute(value)
    paths['output_root'] = paths['work_root']/'outputs'
    paths['state_dir'] = sd
    return paths

def claude_user_config(env: dict, home: Path) -> Path:
    """Where Claude Code keeps user-scope MCP registrations (`claude mcp add --scope user`)."""
    base = Path(env['CLAUDE_CONFIG_DIR']) if env.get('CLAUDE_CONFIG_DIR') else home
    return base/'.claude.json'

def codex_user_config(env: dict, home: Path) -> Path:
    """Where Codex keeps user-scope MCP registrations (`codex mcp add`)."""
    base = Path(env['CODEX_HOME']) if env.get('CODEX_HOME') else home/'.codex'
    return base/'config.toml'

def replace_file(path: Path, data: bytes, mode: int = 0o600) -> None:
    """Atomic rewrite of operator-owned state (lock, markers, setup state); never partial."""
    absolute(path); directory(path.parent)
    fd, name = tempfile.mkstemp(prefix='.storytold-replace-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        os.chmod(name, mode); os.replace(name, path)
    except BaseException:
        Path(name).unlink(missing_ok=True); raise

def private_dir(p: Path, log: Logger) -> None:
    if not p.exists():
        # exist_ok: two first runs may race to create it; the loser then meets the run lock, not a raw FileExistsError.
        p.parent.mkdir(parents=True, exist_ok=True); p.mkdir(mode=0o700, exist_ok=True); log(f'created {p}')
    if os.name != 'nt':
        require(p.stat().st_mode & 0o077 == 0, f'{p} must be owner-only (chmod 700)')

def writing_marker(lock_path: Path) -> Path:
    return lock_path.with_name(lock_path.name + '.writing')

def layout_problems(paths: dict) -> list[str]:
    """Why setup would refuse to start with these paths. Read-only, so a real run checks it before creating anything and --dry-run reports the same."""
    problems = []
    if os.name != 'nt':
        for key in ('state_dir', 'evidence_dir'):
            if paths[key].is_dir() and paths[key].stat().st_mode & 0o077: problems.append(f'{paths[key]} must be owner-only (chmod 700)')
        # preflight refuses this too, but only after a candidate was promoted and pinned; say it before anything is downloaded.
        if paths['bin_dir'].is_dir() and paths['bin_dir'].stat().st_mode & 0o022:
            problems.append(f"{paths['bin_dir']} is writable by group/others (chmod go-w), so another account could swap the installed binaries")
    marker = writing_marker(paths['lock'])
    if marker.exists() or marker.is_symlink():
        problems.append(f'{marker} is left over from an interrupted run, or another setup is rewriting the lock; delete it once no setup is running')
    work = workspace_problem(paths['work_root'])
    if work: problems.append(work)
    return problems

def workspace_problem(work: Path) -> str | None:
    """Why `ensure_layout` would refuse this work root, without creating or changing anything."""
    if not work.exists():
        return None if work.parent.is_dir() else f'the parent of {work} does not exist'
    if not (work/MARKER).is_file(): return f'{work} exists but is not a Storytold workspace; choose another --work-root'
    try:
        open_workspace(work)
    except (OSError, ValueError) as exc:
        return f'{work}: {exc}'
    return None

def ensure_layout(paths: dict, log: Logger) -> None:
    for key in ('state_dir', 'evidence_dir'): private_dir(paths[key], log)
    bin_dir = paths['bin_dir']
    if not bin_dir.exists():
        bin_dir.parent.mkdir(parents=True, exist_ok=True); bin_dir.mkdir(mode=0o755); log(f'created {bin_dir}')
    directory(bin_dir)
    if os.name != 'nt':
        require(bin_dir.stat().st_mode & 0o022 == 0, f'{bin_dir} is writable by group/others (chmod go-w); nothing was installed')
    work = paths['work_root']
    if not work.exists():
        directory(work.parent); init_workspace(work); log(f'created workspace {work}')
    else:
        require((work/MARKER).is_file(), f'{work} exists but is not a Storytold workspace; choose another --work-root')
        open_workspace(work)
    state = {'schema_version': 1, 'bin_dir': str(bin_dir), 'work_root': str(work), 'output_root': str(paths['output_root']),
             'lock': str(paths['lock']), 'evidence_dir': str(paths['evidence_dir']),
             'updated_at': datetime.now(timezone.utc).isoformat()}
    replace_file(paths['state_dir']/STATE_FILE, encoded(state))

# ------------------------------------------------------------------ download
def check_url(url: str) -> None:
    p = urlsplit(url)
    require(p.scheme=='https' and p.hostname in ALLOWED_HOSTS, f'refusing download outside GitHub release hosts: {url}')

class _RedirectGuard(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        check_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def fetch(url: str, dest: Path, limit: int = MAX_DOWNLOAD) -> int:
    check_url(url)
    opener = urllib.request.build_opener(_RedirectGuard())
    request = urllib.request.Request(url, headers={'User-Agent': 'storytold-setup'})
    total = 0
    with opener.open(request, timeout=120) as response, open(dest, 'wb') as f:
        while chunk := response.read(1024*1024):
            total += len(chunk)
            require(total <= limit, f'download exceeds {limit} bytes: {url}')
            f.write(chunk)
    return total

def _safe_member(name: str) -> None:
    require(name and not name.startswith('/') and '\\' not in name and '..' not in name.split('/') and ':' not in name.split('/')[0],
            f'unsafe archive path: {name}')

def extract_cli(archive: Path, dest_dir: Path, exe: str, out_name: str | None = None) -> Path:
    """Take exactly the one regular `exe` member; ignore the rest, refuse anything unsafe.

    Full-application archives (Linux tarballs, Windows portable zips) also carry
    the desktop binary; only the CLI is copied out, as `out_name` (default `exe`).
    """
    dest_dir.mkdir(mode=0o700)
    target = dest_dir/(out_name or exe)
    name = archive.name
    if name.endswith('.zip'):
        with zipfile.ZipFile(archive) as z:
            infos = z.infolist()
            require(0 < len(infos) <= 4096, 'unexpected archive member count')
            found = []
            for info in infos:
                _safe_member(info.filename)
                require((info.external_attr >> 16) & 0o170000 != stat.S_IFLNK, f'symlink in archive: {info.filename}')
                if not info.is_dir() and info.filename.split('/')[-1]==exe:
                    require(info.file_size <= MAX_DOWNLOAD, 'archive member too large'); found.append(info)
            require(len(found)==1, f'archive must contain exactly one {exe}')
            with z.open(found[0]) as src, open(target, 'wb') as out:
                shutil.copyfileobj(src, out, 1024*1024)
    elif name.endswith(('.tar.gz', '.tgz')):
        with tarfile.open(archive, 'r:gz') as t:
            found = []
            count = 0
            for member in t:
                count += 1; require(count <= 4096, 'unexpected archive member count')
                _safe_member(member.name)
                require(not member.issym() and not member.islnk() and not member.isdev(), f'link/device in archive: {member.name}')
                if member.isfile() and member.name.split('/')[-1]==exe:
                    require(member.size <= MAX_DOWNLOAD, 'archive member too large'); found.append(member)
            require(len(found)==1, f'archive must contain exactly one {exe}')
            src = t.extractfile(found[0]); require(src is not None, 'unreadable archive member')
            with src, open(target, 'wb') as out:
                shutil.copyfileobj(src, out, 1024*1024)
    else:
        raise StorytoldError(f'unsupported archive type: {name}')
    target.chmod(0o700)
    return target

RUN_TIMEOUT = 1800  # seconds; no verifier, host CLI, pip or probe child may hang setup silently

def default_runner(argv: list[str]) -> tuple[int, str, str]:
    try:
        r = subprocess.run(argv, capture_output=True, text=True, check=False, timeout=RUN_TIMEOUT)
    except subprocess.TimeoutExpired as exc:
        raise StorytoldError(f'{Path(argv[0]).name} did not finish within {RUN_TIMEOUT} s; nothing after it was attempted') from exc
    return r.returncode, r.stdout, r.stderr

# ---------------------------------------------------------------- provenance
def check_notarization(binary: Path, team: str, run: Runner) -> dict:
    # The system verifiers by absolute path: a PATH shim that exits 0 must not pass for notarization.
    code, out, err = run(['/usr/sbin/spctl', '--assess', '--type', 'install', '-vv', str(binary)])
    combined = out + err
    require(code==0 and 'source=Notarized Developer ID' in combined, f'{binary.name}: not accepted as a notarized Developer ID binary:\n{combined.strip()[:500]}')
    code, out, err = run(['/usr/bin/codesign', '-dv', '--verbose=2', str(binary)])
    found = [line.split('=', 1)[1].strip() for line in (out + err).splitlines() if line.startswith('TeamIdentifier=')]
    require(code==0 and found==[team], f'{binary.name}: signing team {found or "unknown"} is not the reviewed team {team}')
    return {'notarized': True, 'team': team}

def check_sigstore(binary: Path, binary_sha: str, entry: dict, signers: dict, run: Runner, cosign: str, tmp: Path) -> dict:
    require(entry['binary_sha256']==binary_sha, f'{binary.name}: extracted binary differs from the one the workflow signed')
    bundle = tmp/(binary.name+'.sigstore.json')
    bundle.write_bytes(encoded(entry['bundle']))
    code, out, err = run([cosign, 'verify-blob', '--bundle', str(bundle), '--certificate-identity-regexp', signers['sigstore_identity_regexp'],
                          '--certificate-oidc-issuer', signers['sigstore_oidc_issuer'], str(binary)])
    require(code==0, f'{binary.name}: Sigstore verification failed:\n{(out+err).strip()[:800]}')
    return {'sigstore': True, 'identity': signers['sigstore_identity_regexp']}

def check_provenance(binary: Path, binary_sha: str, asset_name: str, plat: str, releases: dict, signatures: dict, *, run: Runner,
                     which: Which, trust_upstream_sums: bool, tmp: Path, log: Logger) -> dict:
    signers = releases['signers']; result = {}
    if plat=='macos':
        result.update(check_notarization(binary, signers['apple_team_id'], run))
    entry = signatures.get('bundles', {}).get(asset_name)
    cosign = which('cosign')
    if entry is not None and cosign:
        result.update(check_sigstore(binary, binary_sha, entry, signers, run, cosign, tmp))
    elif plat=='macos':
        result['sigstore'] = False
        log(f'{binary.name}: notarization verified; Sigstore bundle ' + ('not verified (cosign not on PATH)' if entry else 'not yet published for this release'))
    else:
        reason = ('no Sigstore bundle has been published for this release yet' if entry is None
                  else 'cosign is not on PATH (install it: https://docs.sigstore.dev/cosign/system_config/installation/)')
        require(trust_upstream_sums, f'{binary.name}: {reason}. Pass --trust-upstream-sums to rely on the manifest and SHA256SUMS.txt alone.')
        result['sigstore'] = False; result['provenance'] = 'upstream_sums_only'
        log(f'{binary.name}: WARNING {reason}; proceeding on the manifest and SHA256SUMS.txt only, as requested')
    return result

def provenance_label(info: dict, signers: dict) -> str:
    parts = []
    if info.get('notarized'): parts.append('notarized '+signers['apple_team_id'])
    if info.get('sigstore'): parts.append('sigstore')
    if info.get('provenance')=='upstream_sums_only': parts.append('upstream sums only')
    return ', '.join(parts) or 'unverified'

# ----------------------------------------------------------------- ownership
def pinned_entry(lock_path: Path, app: str) -> dict | None:
    if not lock_path.is_file(): return None
    lock = load_json(lock_path)
    entry = lock.get('apps', {}).get(app) if isinstance(lock, dict) and isinstance(lock.get('apps'), dict) else None
    return entry if isinstance(entry, dict) else None

def managed_binary(paths: dict, catalog: dict, app: str) -> dict:
    """The installed CLI, and whether the lock proves Storytold put exactly these bytes there.

    Ownership means: a regular, non-linked file at the managed path whose
    SHA-256 equals the lock entry Storytold wrote. Anything else is reported
    with a reason and is never deleted or overwritten.
    """
    target = paths['bin_dir']/exe_name(catalog, app)
    info = {'path': str(target), 'exists': target.exists() or target.is_symlink(), 'owned': False, 'reason': None, 'sha256': None, 'pin': None}
    pinned = pinned_entry(paths['lock'], app)
    info['pin'] = pinned
    if not info['exists']:
        info['reason'] = 'not installed'; return info
    if pinned is None or not isinstance(pinned.get('sha256'), str):
        info['reason'] = 'no lock entry records this file, so Storytold cannot prove it installed it'; return info
    try:
        sha256, _, _ = snapshot(target)
        require(target.stat().st_nlink==1, 'the file has more than one hard link')
    except (OSError, ValueError) as exc:
        info['reason'] = f'not a plain regular file Storytold would have written: {exc}'; return info
    info['sha256'] = sha256
    if sha256 != pinned['sha256']:
        info['reason'] = 'the installed bytes differ from the SHA-256 recorded in the lock'; return info
    info['owned'] = True
    return info

# ------------------------------------------------------------------ recovery
def recovery_marker(paths: dict, app: str) -> Path:
    """Lives outside staging, so cleaning staging can never discard recovery information."""
    return paths['state_dir']/RECOVERY_DIR/(app+'.json')

def clear_recovery_marker(marker: Path) -> None:
    marker.unlink(missing_ok=True)

def recovery_state(paths: dict, catalog: dict, app: str) -> dict:
    """Read-only classification of a promotion that may have been interrupted.

    `none`: no marker. `consistent`: the active binary is the recorded candidate
    and the lock already pins it. `completable`: the active binary is the
    candidate but the lock still needs rewriting. `reverted`: the active binary
    (or its absence) is what the marker recorded as previous, so the replace
    never happened. `ambiguous`: the active binary matches neither; nothing may
    change it automatically. `corrupt`: the marker itself is unreadable.
    """
    marker = recovery_marker(paths, app)
    if not marker.is_file(): return {'state': 'none'}
    try:
        data = keys(load_json(marker), {'schema_version','app','candidate_sha256','previous_sha256','previous_pin','commit','label','written_at'}, label='recovery marker')
        require(data['schema_version']==1 and data['app']==app, 'recovery marker belongs to another app or version')
        sha(data['candidate_sha256'])
        require(data['previous_sha256'] is None or sha(data['previous_sha256'])!=data['candidate_sha256'], 'recovery marker records no change')
        require(data['previous_pin'] is None or isinstance(data['previous_pin'], dict), 'invalid previous pin in recovery marker')
    except (OSError, ValueError, TypeError) as exc:
        return {'state': 'corrupt', 'marker': str(marker), 'reason': str(exc)[:300]}
    target = paths['bin_dir']/exe_name(catalog, app)
    active = None
    if target.exists() or target.is_symlink():
        try:
            active, _, _ = snapshot(target)
        except (OSError, ValueError) as exc:
            return {'state': 'ambiguous', 'marker': str(marker), 'reason': f'active file is not a plain regular file: {exc}', 'data': data}
    pinned = pinned_entry(paths['lock'], app)
    pinned_sha = pinned.get('sha256') if isinstance(pinned, dict) else None
    if active==data['candidate_sha256']:
        return {'state': 'consistent' if pinned_sha==active else 'completable', 'marker': str(marker), 'data': data, 'active_sha256': active}
    if active==data['previous_sha256']:
        previous_pin_sha = data['previous_pin'].get('sha256') if data['previous_pin'] else None
        if pinned_sha==previous_pin_sha:
            return {'state': 'reverted', 'marker': str(marker), 'data': data, 'active_sha256': active}
        return {'state': 'ambiguous', 'marker': str(marker), 'reason': 'the active binary is the previous one but the lock no longer records it', 'data': data}
    return {'state': 'ambiguous', 'marker': str(marker), 'reason': 'the active binary matches neither the previous pin nor the verified candidate', 'data': data,
            'active_sha256': active}

def reconcile(paths: dict, catalog: dict, app: str, log: Logger) -> dict:
    """Bring an interrupted promotion to a consistent state, or refuse with the marker kept.

    Idempotent: a second call finds `none` after success, and the same refusal
    after an ambiguous or corrupt state. Only the lock is ever written here;
    the active binary is never replaced during recovery.
    """
    st = recovery_state(paths, catalog, app)
    marker = recovery_marker(paths, app)
    if st['state']=='none': return st
    if st['state']=='corrupt':
        raise StorytoldError(f"{app}: recovery marker {marker} is unreadable ({st['reason']}). Inspect the installed binary and the lock; "
                             f"delete the marker only once they are what you expect. Nothing was changed.")
    if st['state']=='ambiguous':
        raise StorytoldError(f"{app}: an earlier upgrade was interrupted and {st['reason']} (marker {marker}). Nothing was changed. "
                             f"Move the installed file aside or restore a known binary, delete the marker, then run setup again.")
    data = st['data']
    if st['state']=='completable':
        pin(paths['lock'], app, {'commit': data['commit']}, data['candidate_sha256'], data['label'])
        finished = managed_binary(paths, catalog, app)
        require(finished['owned'], f"{app}: lock rewritten but the binary still does not match it: {finished['reason']}")
        log(f'{app}: completed an interrupted upgrade; the lock now records the promoted binary')
    elif st['state']=='reverted':
        log(f'{app}: an earlier upgrade stopped before the binary was replaced; the previous installation is intact')
    else:
        log(f'{app}: an earlier upgrade had already finished; clearing its recovery marker')
    clear_recovery_marker(marker)
    return st

# ------------------------------------------------------------------- staging
def staging_dir(paths: dict, app: str) -> Path:
    p = paths['state_dir']/'staging'/app
    require(absolute(p).is_relative_to(paths['state_dir']), 'staging must stay inside the state directory')
    return p

def clear_staging(paths: dict, app: str, log: Logger) -> None:
    """Remove candidate files only; recovery markers live elsewhere and are never touched here."""
    p = staging_dir(paths, app)
    if p.exists():
        shutil.rmtree(p); log(f'{app}: removed staging files')

def stage_candidate(app: str, plat: str, releases: dict, signatures: dict, catalog: dict, paths: dict, *, fetch: Fetcher, run: Runner,
                    which: Which, trust_upstream_sums: bool, log: Logger) -> dict:
    """Download, verify, extract and provenance-check into staging; nothing active changes."""
    row = releases['apps'][app]; asset = row['assets'][plat]; exe = exe_name(catalog, app); member = member_name(catalog, app, plat)
    staging = staging_dir(paths, app)
    staging.mkdir(parents=True, mode=0o700)
    bin_dir = staging/'bin'; bin_dir.mkdir(mode=0o755)
    with tempfile.TemporaryDirectory(prefix='download-', dir=staging) as td:
        tmp = Path(td); archive = tmp/asset['name']
        log(f"{app}: downloading {asset['name']} ({asset['bytes']} bytes) from GitHub release {row['tag']}")
        n = fetch(asset_url(app, row, plat), archive, MAX_DOWNLOAD)
        require(n==asset['bytes'], f"{app}: downloaded {n} bytes; the manifest expects {asset['bytes']}")
        zip_sha = snapshot(archive)[0]
        require(zip_sha==asset['sha256'], f'{app}: archive SHA-256 differs from config/releases.json; review the release before refreshing the manifest')
        fetch(sums_url(app, row), tmp/'SHA256SUMS.txt', 1024*1024)
        published = published_hash((tmp/'SHA256SUMS.txt').read_bytes(), asset['name'])
        require(published==zip_sha, f"{app}: upstream SHA256SUMS.txt disagrees with the manifest for {asset['name']}; stop and review the release")
        extracted = extract_cli(archive, tmp/'extract', member, exe)
        sha256, nbytes, body = snapshot(extracted, body=True)
        provenance = check_provenance(extracted, sha256, asset['name'], plat, releases, signatures, run=run, which=which,
                                      trust_upstream_sums=trust_upstream_sums, tmp=tmp, log=log)
        candidate = create_new(bin_dir/exe, body or b'', mode=0o755)
    label = f"{row['version']} ({row['tag']}, {asset['name']}, {provenance_label(provenance, releases['signers'])})"
    lock = staging/'lock.json'
    replace_file(lock, encoded({'schema_version': 1, 'platform': platform_id(),
                                'apps': {app: {'revision': row['commit'], 'version': label, 'sha256': sha256}}}))
    return {'candidate': str(candidate), 'bin_dir': str(bin_dir), 'lock': str(lock), 'sha256': sha256, 'bytes': nbytes,
            'archive_sha256': zip_sha, 'label': label, **provenance}

def promote(paths: dict, catalog: dict, app: str, candidate: Path, candidate_sha: str, row: dict, label: str, previous: dict, log: Logger) -> dict:
    """Replace or create the active binary from the verified candidate, then pin it.

    The binary replace and the lock rewrite are two writes, not one
    transaction. The recovery marker, written first and cleared last (only
    after the binary and the lock are seen to agree), is what makes a failure
    anywhere in between reconcilable by the next run.
    """
    exe = exe_name(catalog, app); target = paths['bin_dir']/exe
    marker = recovery_marker(paths, app)
    marker.parent.mkdir(mode=0o700, exist_ok=True)
    stale = target.with_name(exe+'.storytold-new')
    if stale.is_file() and not stale.is_symlink():
        stale.unlink(); log(f'{app}: removed a leftover temporary file from an earlier run')
    replace_file(marker, encoded({'schema_version': 1, 'app': app, 'candidate_sha256': candidate_sha, 'previous_sha256': previous.get('sha256'),
                                  'previous_pin': previous.get('pin'), 'commit': row['commit'], 'label': label,
                                  'written_at': datetime.now(timezone.utc).isoformat()}))
    read_sha, _, body = snapshot(candidate, body=True)
    # Check the bytes about to be published, not only the file after it replaced the live binary.
    require(read_sha==candidate_sha and body is not None, f'{app}: staged candidate changed after verification; nothing was replaced')
    if target.exists():
        staged = create_new(stale, body, mode=0o755)
        os.replace(staged, target)
        log(f'{app}: promoted the verified candidate over the previous binary')
    else:
        create_new(target, body, mode=0o755)
        log(f'{app}: installed the verified candidate')
    require(snapshot(target)[0]==candidate_sha, f'{app}: promoted file changed during publication')
    entry = pin(paths['lock'], app, row, candidate_sha, label)
    finished = managed_binary(paths, catalog, app)
    require(finished['owned'], f"{app}: binary and lock disagree after promotion: {finished['reason']}")
    clear_recovery_marker(marker)
    return entry

@contextmanager
def exclusive(lock_path: Path) -> Iterator[None]:
    """One writer of the installation lock at a time, so parallel setup runs cannot drop each other's pins."""
    marker = writing_marker(lock_path)
    try:
        fd = os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise StorytoldError(f'another setup run is changing {lock_path} (marker {marker}); wait for it to finish, '
                             'or delete the marker if no setup is running') from exc
    try:
        os.write(fd, str(os.getpid()).encode()); os.close(fd); fd = -1
        yield
    finally:
        if fd != -1: os.close(fd)
        marker.unlink(missing_ok=True)

RUN_LOCK = 'setup.lock'
# The errors a lock held elsewhere raises: flock's EWOULDBLOCK/EAGAIN, msvcrt's EACCES (EDEADLK after retries). Anything else is not contention.
BUSY = {errno.EAGAIN, errno.EWOULDBLOCK, errno.EACCES, errno.EDEADLK}

@contextmanager
def single_run(state_dir: Path) -> Iterator[None]:
    """One changing `setup` or `setup --remove` per state directory, held for the whole run.

    The `.writing` marker guards only the lock rewrite; two runs could still
    clear each other's staging, overwrite a recovery marker or delete a binary
    the other just promoted. This is an OS advisory lock on `setup.lock`, not
    a marker file: the operating system releases it when the process ends,
    however it ends (on Windows possibly a moment later), so a killed run never
    blocks the next one for good. The file holds no data.
    """
    # absolute() refuses a symlinked or reparse-point lock file (Windows has no O_NOFOLLOW); fstat refuses anything but a regular file.
    path = absolute(state_dir/RUN_LOCK)
    fd = os.open(path, os.O_RDWR | os.O_CREAT | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_BINARY', 0), 0o600)
    locked = False
    try:
        require(stat.S_ISREG(os.fstat(fd).st_mode), f'{path} is not a regular file; remove it')
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            locked = True
        except OSError as exc:
            if exc.errno not in BUSY:
                raise StorytoldError(f'could not lock {path} ({exc}); keep the Storytold state directory on a local filesystem '
                                     'that supports file locks. Nothing was changed.') from exc
            raise StorytoldError(f'another setup run (install, upgrade or --remove) is using {state_dir}; '
                                 'wait for it to finish, then run this command again. Nothing was changed.') from exc
        yield
    finally:
        try:
            if locked and os.name=='nt':
                import msvcrt
                os.lseek(fd, 0, os.SEEK_SET); msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        finally:
            os.close(fd)

def pin(lock_path: Path, app: str, row: dict, binary_sha: str, label: str) -> dict:
    with exclusive(lock_path):
        if lock_path.exists():
            lock = keys(load_json(lock_path), {'schema_version','platform','apps'}, label='installation lock')
            require(lock['schema_version']==1 and lock['platform']==platform_id() and isinstance(lock['apps'], dict), 'existing lock is not for this machine; move it aside')
        else:
            lock = {'schema_version': 1, 'platform': platform_id(), 'apps': {}}
        lock['apps'][app] = {'revision': row['commit'], 'version': label, 'sha256': binary_sha}
        lock['apps'] = dict(sorted(lock['apps'].items()))
        replace_file(lock_path, encoded(lock))
        return lock['apps'][app]

# --------------------------------------------------------------------- probe
def probe_python(sd: Path, run: Runner, log: Logger, system: str = platform.system()) -> str:
    try:
        if importlib.metadata.version('mcp')==SDK_VERSION: return sys.executable
    except importlib.metadata.PackageNotFoundError:
        pass
    venv = sd/'venv'; py = venv/('Scripts/python.exe' if system=='Windows' else 'bin/python')
    def ok() -> bool:
        code, out, _ = run([str(py), '-c', "import importlib.metadata as m; print(m.version('mcp'))"])
        return code==0 and out.strip()==SDK_VERSION
    if not (py.exists() and ok()):
        lock = ROOT/'requirements-probe.lock'
        require(lock.is_file(), f'{lock} is missing; reinstall the plugin, or use --skip-probe to register without a native probe')
        log(f'creating {venv} and installing the hash-locked mcp=={SDK_VERSION} and its dependencies from PyPI (network)')
        code, _, err = run([sys.executable, '-m', 'venv', str(venv)])
        require(code==0, 'could not create the probe virtual environment:\n'+err.strip()[:500]+'\nUse --skip-probe to register without a native probe')
        # Only the reviewed wheels, each matched to its locked SHA-256: no sdist builds, no PIP_* or pip.conf redirection.
        code, _, err = run([str(py), '-m', 'pip', 'install', '--isolated', '--disable-pip-version-check', '--quiet',
                            '--require-hashes', '--only-binary=:all:', '-r', str(lock)])
        require(code==0 and ok(), 'could not install the probe SDK:\n'+err.strip()[:500]+'\nUse --skip-probe to register without a native probe')
    return str(py)

def archive_evidence(evidence_dir: Path, app: str, name: str | None = None) -> None:
    """Move `name` (default `<app>.json`) into `archive/` under a name never used before; earlier archives are kept, not overwritten."""
    p = evidence_dir/(name or app+'.json')
    if not p.exists(): return
    old = evidence_dir/'archive'; old.mkdir(mode=0o700, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    for n in range(10000):
        target = old/f"{p.stem}-{stamp}{'' if n==0 else f'-{n}'}.json"
        if target.exists() or target.is_symlink(): continue
        try:
            os.rename(p, target)  # Windows refuses an existing target; POSIX was guarded by the check above
        except FileExistsError:
            continue
        return
    raise StorytoldError(f'{app}: could not find a free archive name for earlier evidence under {old}')

def run_probe(app: str, smoke_tool: str, paths: dict, python_exe: str, run: Runner, timeout: float, log: Logger,
              acknowledge_unconfined: bool = False, *, bin_dir: Path | None = None, lock: Path | None = None,
              output: Path | None = None) -> dict:
    """Probe the binary in `bin_dir` under `lock` into `output`.

    With the defaults this is the active launch and the evidence becomes
    `evidence/<app>.json` (the previous one is archived). A candidate probe
    passes the staging directory, its one-app lock and `<app>-candidate.json`;
    that evidence keeps describing the staged path and is never renamed.
    """
    bin_dir = bin_dir or paths['bin_dir']; lock = lock or paths['lock']
    call = paths['evidence_dir']/(app+'-call.json')
    replace_file(call, encoded({'name': smoke_tool, 'arguments': {}}))
    if output is None:
        archive_evidence(paths['evidence_dir'], app); output = paths['evidence_dir']/(app+'.json')
    else:
        output.unlink(missing_ok=True)
    log(f'{app}: probing initialize, tools/list and read-only {smoke_tool} through the official SDK ({bin_dir})')
    code, out, err = run([python_exe, str(ROOT/'storytold.py'), 'probe', '--bin-dir', str(bin_dir), '--work-root', str(paths['work_root']),
                          '--output-root', str(paths['output_root']), '--lock', str(lock), '--app', app, '--confirm-execution',
                          '--timeout', str(timeout), '--call-json', str(call), '--approve-call', '--output', str(output),
                          *(['--acknowledge-unconfined'] if acknowledge_unconfined else [])])
    require(output.is_file(), f'{app}: probe wrote no evidence:\n{err.strip()[:800]}')
    report = load_json(output)
    require(code==0 and report.get('status')=='discovery_and_call_passed',
            f"{app}: native probe {report.get('status')}: {report.get('error')}; evidence kept at {output}")
    return {'evidence': str(output), 'status': report['status'], 'tools': len(report.get('tools', [])),
            'protocol_version': report.get('protocol_version'), 'server_info': report.get('server_info'), 'bin_dir': str(bin_dir)}

# ------------------------------------------------------------------ register
def host_argv(host: str, which: Which) -> list[str] | None:
    """Resolved host CLI; Windows .cmd shims run through cmd.exe, never by name."""
    path = which(host)
    if path is None: return None
    if path.lower().endswith(('.cmd', '.bat')): return ['cmd.exe', '/d', '/c', path]
    return [path]

def _string_list(value: object) -> list[str] | None:
    return list(value) if isinstance(value, list) and all(isinstance(a, str) for a in value) else None

def user_scope_servers(host: str, env: dict, home: Path) -> dict | None:
    """The server table of the host's user-scope file (.claude.json, $CODEX_HOME/config.toml), read without running the host.

    None when the file is absent. A file that exists but cannot be read or
    parsed raises, so callers can tell "no registration" from "unknown".
    """
    parsed = host_document(host, env, home)
    if parsed is None: return None
    key = 'mcp_servers' if host=='codex' else 'mcpServers'
    servers = parsed.get(key, {})
    require(isinstance(servers, dict), f'{key} in the {host} user-scope file is not an object/table')
    return servers

def host_document(host: str, env: dict, home: Path) -> dict | None:
    """The whole parsed user-scope file, or None when absent. Its contents never reach a message: these files also hold account data."""
    p = codex_user_config(env, home) if host=='codex' else claude_user_config(env, home)
    if not (p.exists() or p.is_symlink()): return None
    data = snapshot(p, limit=MAX_JSON, body=True)[2] or b''
    try:
        parsed = tomllib.loads(data.decode('utf-8')) if host=='codex' else parse_json(data)
    except (ValueError, RecursionError):
        # A fixed message: a parser's own text can quote keys or bytes of the file.
        raise StorytoldError(f"{p} is not valid {'TOML' if host=='codex' else 'JSON'} (or is nested too deeply)") from None
    require(isinstance(parsed, dict), f'{p} is not an object/table')
    return parsed

# The fields `codex mcp add` and `claude mcp add --transport stdio` write; anything else is the operator's own tuning.
WRITTEN_FIELDS = {'codex': {'command', 'args', 'env'}, 'claude': {'type', 'command', 'args', 'env'}}

def user_scope_entry(host: str, app: str, env: dict | None, home: Path | None) -> dict | None:
    """User-scope registration from the host's own file: `command`, `args`, `env`, `cwd`, and whether it carries other settings. None when absent or unreadable."""
    if env is None or home is None: return None
    try:
        servers = user_scope_servers(host, env, home)
    except (OSError, ValueError):
        return None
    row = servers.get(app) if servers else None
    if not isinstance(row, dict) or not isinstance(row.get('command'), str): return None
    args = _string_list(row.get('args', []))
    if args is None: return None
    extra = bool(set(row) - WRITTEN_FIELDS[host] - {'cwd'}) or row.get('type', 'stdio')!='stdio'
    return {'command': row['command'], 'args': args, 'env': row.get('env') or {}, 'cwd': row.get('cwd'), 'extra_settings': extra}

def user_scope_command(host: str, app: str, env: dict, home: Path) -> tuple[str, str | None]:
    """('absent', None), ('present', command or None) or ('unreadable', reason) for `app` in the host's user-scope file."""
    try:
        servers = user_scope_servers(host, env, home)
    except (OSError, ValueError) as exc:
        return 'unreadable', str(exc)[:300]
    if not servers or app not in servers: return 'absent', None
    command = servers[app].get('command') if isinstance(servers[app], dict) else None
    return 'present', command if isinstance(command, str) else None

def same_binary(command: object, expected: str) -> bool:
    """Whether a registered command starts the managed binary: the same path, or another spelling or link of that file."""
    if not isinstance(command, str): return False
    if command==expected: return True
    try:
        return Path(command).is_absolute() and os.path.samefile(command, expected)
    except (OSError, ValueError):
        return False

def binary_references(expected: str, env: dict, home: Path, skip: set[tuple[str, str]]) -> list[str]:
    """Every registration in the hosts' own files that still starts `expected`, under any server name; an unreadable file counts.

    Covers each host's user scope and the per-project local scope Claude Code
    keeps in the same file, so an alias, a second name or a shadowing local
    entry cannot be left pointing at a deleted binary. `skip` holds the
    (host, name) user-scope entries a dry run would unregister. Only host,
    scope and server name are reported, never a project path or other content.
    """
    found = []
    for host in HOSTS:
        try:
            parsed = host_document(host, env, home)
        except (OSError, ValueError) as exc:
            found.append(f'{host}: {str(exc)[:200]}'); continue
        if parsed is None: continue
        key = 'mcp_servers' if host=='codex' else 'mcpServers'
        tables = [('user', parsed.get(key))]
        projects = parsed.get('projects') if host=='claude' else None
        if isinstance(projects, dict):
            tables += [('local', row.get('mcpServers')) for row in projects.values() if isinstance(row, dict)]
        for scope, servers in tables:
            if not isinstance(servers, dict): continue
            for name, row in servers.items():
                if scope=='user' and (host, name) in skip: continue
                if same_binary(row.get('command') if isinstance(row, dict) else None, expected):
                    found.append(f"{host} {scope}-scope entry '{str(name)[:64]}'")
    return sorted(set(found))

NOT_REGISTERED = 'no mcp server named'  # codex and claude both answer an unknown name with this (exit 1)

def absent_or_raise(host: str, app: str, code: int, out: str, err: str) -> None:
    """Only the host's own not-found answer means "not registered"; any other failure must not read as absence."""
    if NOT_REGISTERED in (out + err).lower(): return
    raise StorytoldError(f'{host}: `{host} mcp get {app}` failed (exit {code}), so its registration could not be inspected:\n'
                         f'{(out + err).strip()[:500]}')

def host_get(host: str, app: str, run: Runner, which: Which = shutil.which, env: dict | None = None, home: Path | None = None) -> dict | None:
    """Current registration as the host reports it, or None when absent.

    Codex answers in JSON. Claude Code prints text with `Args:` joined by
    spaces, which cannot recover boundaries inside paths; for user scope the
    structured `.claude.json` entry is used, otherwise `args_text` is kept
    verbatim for whole-line comparison. `parse_error` marks output that names
    no command: such a registration exists but is never modified.
    """
    base = host_argv(host, which) or [host]
    if host=='codex':
        code, out, err = run([*base, 'mcp', 'get', app, '--json'])
        if code!=0: absent_or_raise(host, app, code, out, err); return None
        try:
            transport = json.loads(out).get('transport', {})
            command, args = transport.get('command'), _string_list(transport.get('args'))
            env_vars, cwd = transport.get('env'), transport.get('cwd')
        except (ValueError, AttributeError):
            command, args, env_vars, cwd = None, None, None, None
        ok = isinstance(command, str) and args is not None
        return {'command': command if ok else None, 'args': args if ok else None, 'args_text': None, 'scope': 'user' if ok else None,
                'env': env_vars or {}, 'cwd': cwd, 'parse_error': not ok}
    code, out, err = run([*base, 'mcp', 'get', app])
    if code!=0: absent_or_raise(host, app, code, out, err); return None
    command = args_text = scope = None
    for line in out.splitlines():
        s = line.strip()
        if s.startswith('Scope:'): scope = s.split(':', 1)[1].strip()
        elif s.startswith('Command:'): command = s.split(':', 1)[1].strip()
        elif s.startswith('Args:'): args_text = s.split(':', 1)[1].strip()
    result = {'command': command or None, 'args': None, 'args_text': args_text, 'scope': scope, 'env': None, 'cwd': None, 'parse_error': not command}
    if command and scope and scope.lower().startswith('user'):
        structured = user_scope_entry('claude', app, env, home)
        if structured is not None and structured['command']==command:
            result['args'] = structured['args']; result['env'] = structured['env']; result['cwd'] = structured['cwd']
    return result

def registration_matches(current: dict | None, command: str, args: list[str]) -> bool:
    if current is None or current.get('parse_error'): return False
    if current.get('command') != command: return False
    if current.get('args') is not None: return current['args']==list(args)
    return current.get('args_text')==' '.join(args)

def registration_ownership(host: str, app: str, current: dict | None, command: str, args: list[str], env: dict | None, home: Path | None) -> tuple[bool, str]:
    """Whether the effective registration is, in full, the one Storytold writes for `app`.

    Name and path alone prove nothing. The command, every argument, the user
    scope and the host's own user-scope file must all agree; anything the host
    cannot describe, or any field Storytold never writes (cwd, env), keeps the
    entry out of Storytold's hands.
    """
    if current is None: return False, 'not registered'
    if current.get('parse_error'): return False, f'`{host} mcp get` named no command; inspect it by hand'
    if current.get('command') != command: return False, f"points at {current.get('command')}, not the Storytold-managed {command}"
    if current.get('args') is not None:
        if current['args'] != list(args): return False, 'its arguments are not the catalog launch Storytold registers'
    elif current.get('args_text') != ' '.join(args):
        return False, 'its arguments are not the catalog launch Storytold registers'
    scope = current.get('scope') or ''
    if not scope.lower().startswith('user'): return False, f"its scope is '{scope or 'unknown'}', not user scope (which setup writes)"
    entry = user_scope_entry(host, app, env, home)
    if entry is None: return False, f"the user-scope {'config.toml' if host=='codex' else '.claude.json'} has no readable entry for it, so its scope cannot be confirmed"
    if entry['command'] != command or entry['args'] != list(args): return False, 'the user-scope file disagrees with what the host CLI reports'
    if entry.get('cwd') is not None or entry.get('env'): return False, 'it carries cwd or env settings Storytold never writes'
    if entry.get('extra_settings'): return False, 'it carries settings beyond command, args and an empty env, which Storytold never writes'
    return True, ''

def restorable_original(host: str, app: str, current: dict, env: dict | None, home: Path | None) -> dict:
    """The exact registration to re-add if a replacement fails; refuses what cannot be re-added faithfully."""
    require(not current.get('parse_error'), f"{host}: '{app}' is registered but `{host} mcp get` named no command; not touching it")
    scope = current.get('scope') or ''
    require(scope.lower().startswith('user'), f"{host}: '{app}' is registered in scope '{scope or 'unknown'}', not user scope; replace it by hand")
    args = current.get('args')
    require(args is not None, f"{host}: '{app}' arguments cannot be recovered exactly from `{host} mcp get` text; replace it by hand")
    require(not current.get('env') and current.get('cwd') is None,
            f"{host}: '{app}' carries env or cwd settings that `{host} mcp add` cannot restore; replace it by hand")
    entry = user_scope_entry(host, app, env, home)
    require(not (entry and entry.get('extra_settings')),
            f"{host}: '{app}' carries settings that `{host} mcp add` cannot restore; replace it by hand")
    return {'command': current['command'], 'args': list(args)}

def host_add(host: str, app: str, command: str, args: list[str], run: Runner, which: Which = shutil.which) -> None:
    base = host_argv(host, which) or [host]
    argv = ([*base, 'mcp', 'add', app, '--', command, *args] if host=='codex'
            else [*base, 'mcp', 'add', '--scope', 'user', '--transport', 'stdio', app, '--', command, *args])
    if base[0]=='cmd.exe':
        # cmd.exe re-parses its command line: these characters would split or expand a path.
        bad = sorted({c for a in argv[3:] for c in a if c in '&|<>^%!"'})
        require(not bad, f'{host}: a path contains {"".join(bad)}, which cmd.exe would interpret; register it by hand: '
                         f'{manual_add_command(host, app, command, args)}')
    code, out, err = run(argv)
    require(code==0, f'{host}: registration failed:\n{(out+err).strip()[:800]}')

def host_remove(host: str, app: str, run: Runner, which: Which = shutil.which) -> None:
    base = host_argv(host, which) or [host]
    argv = [*base, 'mcp', 'remove', app] if host=='codex' else [*base, 'mcp', 'remove', '--scope', 'user', app]
    code, out, err = run(argv)
    require(code==0, f'{host}: removal failed:\n{(out+err).strip()[:800]}')

def manual_add_command(host: str, app: str, command: str, args: list[str]) -> str:
    quoted = ' '.join(json.dumps(a) if ' ' in a else a for a in [command, *args])
    return f'{host} mcp add {app} -- {quoted}' if host=='codex' else f'{host} mcp add --scope user {app} -- {quoted}'

def register(app: str, launch: dict, hosts: list[str], run: Runner, replace: bool, log: Logger, which: Which = shutil.which,
             env: dict | None = None, home: Path | None = None) -> list[dict]:
    """One row per host; a failing host is reported, never hidden, and does not stop the others.

    Replacement removes the old entry only after it is known to be restorable;
    if adding the new one fails, the old one is re-added and that restoration
    is verified. A lost registration is reported as such with the exact
    command to re-add it.
    """
    rows = []
    for host in hosts:
        row = {'host': host, 'command': launch['command'], 'args': launch['args']}
        try:
            current = host_get(host, app, run, which, env, home)
            if current is not None and current.get('parse_error'):
                raise StorytoldError(f"{host}: '{app}' is registered but `{host} mcp get` named no command; not touching it. Inspect it by hand.")
            matches = registration_matches(current, launch['command'], launch['args'])
            original = None
            if current is not None and not matches:
                what = (f"different arguments ({' '.join(current['args'])})" if current.get('command')==launch['command'] and current.get('args') is not None
                        else 'different arguments' if current.get('command')==launch['command'] else f"a different command ({current.get('command')})")
                require(replace, f"{host}: '{app}' is already registered with {what}; pass --replace to re-register it")
                original = restorable_original(host, app, current, env, home)
                host_remove(host, app, run, which); log(f'{host}: removed previous {app} registration')
            if not matches:
                try:
                    host_add(host, app, launch['command'], launch['args'], run, which)
                    after = host_get(host, app, run, which, env, home)
                    require(registration_matches(after, launch['command'], launch['args']), f'{host}: {app} is not visible as registered after `mcp add`')
                except (OSError, ValueError) as exc:
                    if original is None: raise
                    try:
                        host_add(host, app, original['command'], original['args'], run, which)
                        restored = host_get(host, app, run, which, env, home)
                        require(registration_matches(restored, original['command'], original['args']), 'the restored entry is not visible')
                        raise StorytoldError(f'{exc}; the previous registration ({original["command"]}) was restored and verified') from exc
                    except (OSError, ValueError) as exc2:
                        if exc2.__cause__ is exc: raise
                        row['registration_lost'] = True; row['original'] = original
                        raise StorytoldError(f'{exc}; restoring the previous registration also failed ({exc2}). Re-add it by hand: '
                                             f'{manual_add_command(host, app, original["command"], original["args"])}') from exc2
                log(f'{host}: registered {app} (user scope)')
            row['status'] = 'already_registered' if matches else 'registered'
            if matches:
                # Same command and arguments do not make it Storytold's entry: say what remove would refuse.
                owned, reason = registration_ownership(host, app, current, launch['command'], launch['args'], env, home)
                if not owned:
                    row['warning'] = f'registered, but not as Storytold writes it: {reason}'; log(f"{host}: {app}: {row['warning']}")
        except (OSError, ValueError) as exc:
            row['status'] = 'failed'; row['error'] = str(exc)[:800]; log(f'{host}: {app}: FAILED: {exc}')
        rows.append(row)
    return rows

# ---------------------------------------------------------------------- flow
def plan_hosts(requested: list[str] | None, which: Which = shutil.which) -> list[str]:
    hosts = [h for h in HOSTS if (not requested or h in requested)]
    return [h for h in hosts if which(h) is not None]

def default_log(message: str) -> None:
    print('storytold setup: '+message, file=sys.stderr)

# An allow-list: a status this code does not know can never read as success.
SUCCESS = {'registered', 'installed_no_host_cli', 'installed_not_registered'}

def binary_decision(app: str, current: dict, row: dict, catalog: dict, *, upgrade: bool, acknowledge_unconfined: bool) -> dict:
    """What setup does with an app's binary. The real run and --dry-run share it, so the preview cannot drift.

    `keep`: installed and pinned at this release. `install` / `upgrade`: stage
    and verify a candidate. `skip`: an app without root flags and no
    --acknowledge-unconfined; it is never touched and the batch goes on.
    `refuse`: the batch stops here with `reason`.
    """
    # A pin whose label cannot show the root flags apply is stale even at the manifest commit; --upgrade rewrites it.
    up_to_date = bool(current['owned'] and current['pin'].get('revision')==row['commit'] and honours_roots(app, current['pin'].get('version')))
    blocked = (f"{app}: {current['path']} exists but {current['reason']}; move it aside before setup will touch this path"
               if current['exists'] and not current['owned'] else
               f"{app}: installed at a different pin ({current['pin'].get('version')}); pass --upgrade to move to {row['tag']}"
               if current['exists'] and not up_to_date and not upgrade else None)
    if catalog[app]['confinement']=='os_only' and not acknowledge_unconfined:
        # Decided first: an app the operator has not acknowledged is skipped whatever its path holds, and never stops the batch.
        return {'action': 'skip', 'up_to_date': up_to_date, 'also': blocked}
    if blocked: return {'action': 'refuse', 'reason': blocked}
    return {'action': 'keep' if up_to_date else 'upgrade' if current['exists'] else 'install'}

def predicted_binary(paths: dict, catalog: dict, app: str) -> tuple[str, dict]:
    """The recovery state, and the binary as the real run finds it once `reconcile` has run; read-only."""
    st = recovery_state(paths, catalog, app); current = managed_binary(paths, catalog, app)
    if st['state']=='completable':
        d = st['data']
        current = {**current, 'owned': True, 'reason': None, 'sha256': d['candidate_sha256'],
                   'pin': {'revision': d['commit'], 'version': d['label'], 'sha256': d['candidate_sha256']}}
    return st['state'], current

def registration_preview(host: str, app: str, command: str, args: list[str], replace: bool, env: dict, home: Path) -> str:
    """What registering would do, judged from the host's user-scope file alone; the real run asks the host CLI.

    `add`, `already_registered` and `replace` are the outcomes that pass;
    `refuse: …` and `unknown: …` are not.
    """
    try:
        servers = user_scope_servers(host, env, home)
    except (OSError, ValueError):
        return 'unknown: its user-scope file could not be read'
    if not servers or app not in servers: return 'add'
    entry = user_scope_entry(host, app, env, home)
    if entry is not None and entry['command']==command and entry['args']==list(args): return 'already_registered'
    if not replace: return 'refuse: registered differently; needs --replace'
    # --replace removes the old entry only once it can be re-added exactly (restorable_original).
    if entry is None: return 'refuse: its command and arguments cannot be read back exactly, so --replace leaves it alone'
    if entry['env'] or entry['cwd'] is not None or entry['extra_settings']:
        return f'refuse: it carries env, cwd or other settings that `{host} mcp add` cannot restore, so --replace leaves it alone'
    return 'replace'

def provenance_gate(plat: str, bundled: bool, cosign: str | None, trust_upstream_sums: bool) -> str | None:
    """Why check_provenance would refuse a download on this platform, or None; notarization itself cannot be previewed."""
    if plat=='macos' or trust_upstream_sums or (bundled and cosign): return None
    why = 'no Sigstore bundle has been published for this release yet' if not bundled else 'cosign is not on PATH'
    return f'{why}, so the provenance check refuses it unless --trust-upstream-sums is passed'

def preview(apps: list[str], report: dict, paths: dict, plat: str, targets: list[str], *, releases: dict, signatures: dict, catalog: dict,
            acknowledge_unconfined: bool, skip_probe: bool, upgrade: bool, replace: bool, trust_upstream_sums: bool, env: dict, home: Path) -> dict:
    """--dry-run: the same decisions as a real run from read-only checks, with each app's predicted status. Nothing is created or run."""
    problems = layout_problems(paths)
    report.setdefault('warnings', []).extend('the real run would stop before any app: '+p for p in problems)
    if not report['warnings']: del report['warnings']
    stopped = bool(problems)
    for app in apps:
        row = releases['apps'][app]; asset = row['assets'][plat]; unconfined = catalog[app]['confinement']=='os_only'
        item = {'app': app, 'release': row['tag'], 'install_to': str(paths['bin_dir']/exe_name(catalog, app)), 'probe': not skip_probe,
                'sigstore_bundle': asset['name'] in signatures.get('bundles', {}), 'needs_acknowledge_unconfined': unconfined and not acknowledge_unconfined}
        try:
            recovery, current = predicted_binary(paths, catalog, app)
            decision = ({'action': 'refuse', 'reason': f'{app}: an interrupted upgrade left its recovery marker {recovery}; setup refuses until that is resolved'}
                        if recovery in {'ambiguous', 'corrupt'} else
                        binary_decision(app, current, row, catalog, upgrade=upgrade, acknowledge_unconfined=acknowledge_unconfined))
        except (OSError, ValueError) as exc:
            recovery, decision = 'unknown', {'action': 'refuse', 'reason': f'{app}: {str(exc)[:300]}'}
        fetches = decision['action'] in {'install', 'upgrade'}
        gate = provenance_gate(plat, item['sigstore_bundle'], report['cosign'], trust_upstream_sums) if fetches else None
        registers = decision['action'] in {'install', 'upgrade', 'keep'} and bool(targets) and not gate
        regs = ({h: registration_preview(h, app, item['install_to'], launch_args(catalog, app, paths), replace, env, home) for h in targets}
                if registers else {})
        predicted = ('not_reached' if stopped else 'failed' if decision['action']=='refuse' or gate else
                     ('installed_not_registered' if decision['up_to_date'] else 'needs_acknowledgement') if decision['action']=='skip' else
                     'installed_no_host_cli' if not targets else
                     'partially_registered' if any(v.startswith('refuse') for v in regs.values()) else
                     'registration_unknown' if any(v.startswith('unknown') for v in regs.values()) else 'registered')
        item.update({'binary': decision['action'], 'download': asset_url(app, row, plat) if fetches else None, 'bytes': asset['bytes'] if fetches else 0,
                     'register': registers, 'registrations': regs, 'predicted_status': predicted})
        if recovery!='none': item['recovery'] = recovery
        reason = decision.get('reason') or decision.get('also') or (f'{app}: {gate}' if gate else None)
        if reason: item['reason'] = reason
        report['apps'].append(item)
        stopped = stopped or decision['action']=='refuse' or bool(gate)  # the real run stops at its first failure
    report['would_pass'] = not report.get('warnings') and all(a['predicted_status'] in SUCCESS for a in report['apps'])
    report['preview_limits'] = ('Registrations are judged from the hosts\' user-scope files; downloads, notarization, Sigstore verification '
                                'and probes are not attempted, so a real run can still fail there.')
    return report

def setup(apps: list[str], *, acknowledge_unconfined: bool, hosts: list[str] | None, skip_probe: bool, upgrade: bool,
          replace: bool, dry_run: bool, timeout: float, env: dict, home: Path, trust_upstream_sums: bool = False,
          system: str = platform.system(), machine: str = platform.machine(), fetch: Fetcher = fetch, run: Runner = default_runner,
          which: Which = shutil.which, log: Logger = default_log, releases: dict | None = None, signatures: dict | None = None,
          catalog: dict | None = None, **overrides: str | None) -> dict:
    releases = releases or load_releases(); catalog = catalog or load_catalog()
    signatures = signatures if signatures is not None else load_signatures(releases=releases)
    plat = platform_key(system, machine)
    paths = resolve_paths(env, home, system, **overrides)
    # Staging, the probe venv and the binaries are as sensitive as the lock: none may sit where the apps can write.
    require(not any(paths[k].is_relative_to(paths['work_root']) for k in ('lock', 'evidence_dir', 'state_dir', 'bin_dir')),
            'lock, evidence, setup state and binaries must stay outside the native workspace')
    targets = plan_hosts(hosts, which)
    report = {'schema_version': 1, 'dry_run': dry_run, 'platform': platform_id(), 'platform_key': plat, 'cosign': which('cosign'),
              'paths': {k: str(v) for k, v in paths.items()}, 'hosts': targets, 'apps': [],
              'notice': 'Hosts load MCP servers when a session starts: open a new Claude Code or Codex session afterwards.'}
    # An explicitly named host that cannot be registered is an unmet request, so the run cannot pass (other hosts are still registered).
    missing_hosts = [h for h in hosts or [] if h not in targets]
    if missing_hosts:
        report['warnings'] = [f'requested host CLI not on PATH, so nothing was registered there: {", ".join(missing_hosts)}']
    if dry_run:
        return preview(apps, report, paths, plat, targets, releases=releases, signatures=signatures, catalog=catalog,
                       acknowledge_unconfined=acknowledge_unconfined, skip_probe=skip_probe, upgrade=upgrade, replace=replace,
                       trust_upstream_sums=trust_upstream_sums, env=env, home=home)
    # Checked before the state directory, bin directory or anything else is created; ensure_layout checks again under the lock.
    problems = layout_problems(paths)
    require(not problems, '; '.join(problems) + '; nothing was changed')
    private_dir(paths['state_dir'], log)
    with single_run(paths['state_dir']):
        ensure_layout(paths, log)
        python_exe = None
        for app in apps:
            row = releases['apps'][app]; entry = {'app': app, 'release': row['tag']}
            try:
                recovered = reconcile(paths, catalog, app, log)
                if recovered['state']!='none': entry['recovery'] = recovered['state']
                current = managed_binary(paths, catalog, app)
                decision = binary_decision(app, current, row, catalog, upgrade=upgrade, acknowledge_unconfined=acknowledge_unconfined)
                if decision['action']=='refuse': raise StorytoldError(decision['reason'])
                if decision['action']=='skip':
                    # Preflight, and therefore any probe, needs the acknowledgement; without it nothing is downloaded or promoted.
                    if decision['up_to_date']:
                        entry['install'] = {'path': current['path'], 'sha256': current['sha256'], 'unchanged': True, 'label': current['pin'].get('version')}
                        entry['pin'] = current['pin']; entry['status'] = 'installed_not_registered'
                        entry['next'] = f'{app} is installed and pinned but runs without file-root flags; re-run with --acknowledge-unconfined to register it.'
                        report['apps'].append(entry); log(f'{app}: {entry["next"]}'); continue
                    # Skip, do not stop: the other selected apps (the confined ones included) still get processed.
                    entry['status'] = 'needs_acknowledgement'
                    entry['error'] = (f'{app} runs without file-root flags: it can read and write anywhere your user can. '
                                      f'Re-run with --acknowledge-unconfined to install and register it for non-sensitive work.'
                                      + (f' Setup would then also stop on: {decision["also"]}' if decision['also'] else ''))
                    report['apps'].append(entry); log(f"{app}: skipped: {entry['error']}"); continue
                if decision['action']=='keep':
                    log(f"{app}: already installed at {row['tag']} and pinned; skipping download")
                    entry['install'] = {'path': current['path'], 'sha256': current['sha256'], 'unchanged': True, 'label': current['pin'].get('version')}
                    entry['pin'] = current['pin']
                else:
                    clear_staging(paths, app, log)
                    staged = stage_candidate(app, plat, releases, signatures, catalog, paths, fetch=fetch, run=run, which=which,
                                             trust_upstream_sums=trust_upstream_sums, log=log)
                    entry['candidate'] = {k: staged[k] for k in ('candidate', 'sha256', 'bytes', 'archive_sha256', 'label') if k in staged}
                    # Candidate verification: preflight and probe against the staged path; this evidence stays the candidate's.
                    preflight(Path(staged['bin_dir']), paths['work_root'], paths['output_root'], Path(staged['lock']), [app], catalog, acknowledge_unconfined)
                    if skip_probe:
                        entry['candidate_probe'] = {'status': 'skipped', 'native_runtime_verified': False}
                    else:
                        python_exe = python_exe or probe_python(paths['state_dir'], run, log, system)
                        entry['candidate_probe'] = run_probe(app, row['smoke_tool'], paths, python_exe, run, timeout, log, acknowledge_unconfined,
                                                             bin_dir=Path(staged['bin_dir']), lock=Path(staged['lock']),
                                                             output=paths['evidence_dir']/(app+'-candidate.json'))
                    staged_sha = staged['sha256']
                    if current['owned'] and current['sha256']==staged_sha:
                        entry['pin'] = pin(paths['lock'], app, row, staged_sha, staged['label'])
                        log(f'{app}: installed binary already matches this release; pin updated, file unchanged')
                    else:
                        entry['pin'] = promote(paths, catalog, app, Path(staged['candidate']), staged_sha, row, staged['label'], current, log)
                    entry['install'] = {'path': str(paths['bin_dir']/exe_name(catalog, app)), 'sha256': staged_sha, 'bytes': staged['bytes'],
                                        'archive_sha256': staged['archive_sha256'], 'previous_sha256': current['sha256'], 'label': staged['label'],
                                        **{k: staged[k] for k in ('notarized', 'team', 'sigstore', 'identity', 'provenance') if k in staged}}
                    clear_staging(paths, app, lambda _: None)
                # Active-launch verification: the binary and lock must agree, and the evidence must describe this very launch.
                launch = preflight(paths['bin_dir'], paths['work_root'], paths['output_root'], paths['lock'], [app], catalog, acknowledge_unconfined)['launches'][0]
                if skip_probe:
                    entry['probe'] = {'status': 'skipped', 'native_runtime_verified': False}
                    log(f'{app}: probe skipped on request; the binary has not been exercised')
                else:
                    try:
                        python_exe = python_exe or probe_python(paths['state_dir'], run, log, system)
                        entry['probe'] = run_probe(app, row['smoke_tool'], paths, python_exe, run, timeout, log, acknowledge_unconfined)
                    except (OSError, ValueError) as exc:
                        entry['status'] = 'promoted_unverified'; entry['error'] = str(exc)[:1000]
                        entry['next'] = (f'{app} is installed and pinned but failed the probe at its active path; it was not registered. '
                                         f'Re-run setup to probe again, or `setup --remove --app {app}`.')
                        report['apps'].append(entry); log(f'{app}: FAILED after promotion: {exc}')
                        break
                entry['registrations'] = register(app, launch, targets, run, replace, log, which, env, home) if targets else []
                failed_hosts = [r['host'] for r in entry['registrations'] if r['status']=='failed']
                entry['status'] = ('installed_no_host_cli' if not targets else 'partially_registered' if failed_hosts else 'registered')
                if not targets: entry['next'] = 'No codex/claude CLI on PATH: install one, then re-run setup to register.'
                if failed_hosts: entry['next'] = f"binary and pin are current; registration failed for {', '.join(failed_hosts)}; fix the message above and re-run setup"
            except (OSError, ValueError, TypeError, KeyError, tarfile.TarError, zipfile.BadZipFile) as exc:
                entry['status'] = 'failed'; entry['error'] = str(exc)[:1000]
                report['apps'].append(entry); log(f'{app}: FAILED: {exc}')
                try: clear_staging(paths, app, lambda _: None)
                except OSError: pass
                break
            report['apps'].append(entry)
        # The run stops at its first failure; the apps it never attempted are listed, not left out.
        attempted = {a['app'] for a in report['apps']}
        report['apps'] += [{'app': a, 'release': releases['apps'][a]['tag'], 'status': 'not_reached',
                            'next': 'not attempted because an earlier app failed; fix that and run setup again'} for a in apps if a not in attempted]
    report['status'] = 'passed' if not missing_hosts and all(a.get('status') in SUCCESS for a in report['apps']) else 'failed'
    return report

def shown(command: object) -> str | None:
    """A registered command as reports show it: text only, bounded."""
    return command[:300] if isinstance(command, str) else None

def unrun_host(host: str, app: str, expected: str, hosts: list[str] | None, env: dict, home: Path) -> tuple[dict, bool, bool]:
    """The row for a host whose CLI this removal does not run, whether that host may still launch `expected`, and whether it needs attention.

    Nothing is unregistered there, but its user-scope file, where `setup`
    wrote the entry, is still read: deleting the binary under a registration
    that launches it would leave that host with a dangling server.
    """
    selected = not hosts or host in hosts
    why = 'host CLI not on PATH' if selected else 'not selected with --host'
    state, command = user_scope_command(host, app, env, home)
    if state=='unreadable':
        return {'host': host, 'action': 'kept', 'reason': f'{why}, and {command}, so it may still launch the binary'}, True, True
    if state=='absent':
        if hosts and host in hosts:  # named explicitly, but the host itself could not be asked
            return {'host': host, 'action': 'kept', 'reason': f'{why}, so its registration could not be inspected; its user-scope file has no entry for {app}'}, False, True
        return {'host': host, 'action': 'none', 'reason': f'{why}; its user-scope file has no entry for {app}'}, False, False
    if same_binary(command, expected):
        fix = f'run --remove again with {host} on PATH' if selected else f'run --remove with --host {host} as well'
        return ({'host': host, 'action': 'kept', 'command': shown(command),
                 'reason': f'{why}, but its user-scope file still registers {app} at the managed binary; {fix}, or `{host} mcp remove {app}` by hand'},
                True, True)
    return {'host': host, 'action': 'kept' if selected else 'none', 'command': shown(command),
            'reason': f'{why}; its user-scope file registers {app} with a different command'}, False, selected

def may_launch(current: dict, expected: str) -> bool:
    """Whether a registration a host CLI described, and that Storytold keeps, may still start `expected`: it names that binary, or names no readable command."""
    return bool(current.get('parse_error')) or not isinstance(current.get('command'), str) or same_binary(current['command'], expected)

def remove_app(app: str, paths: dict, catalog: dict, targets: list[str], hosts: list[str] | None, *, dry_run: bool,
               run: Runner, which: Which, log: Logger, env: dict, home: Path) -> dict:
    verb = 'would ' if dry_run else ''
    entry = {'app': app, 'registrations': [], 'binary': None, 'pin': None, 'evidence': None, 'status': 'ok'}
    recovery = recovery_state(paths, catalog, app)
    if recovery['state']!='none':
        entry['status'] = 'attention'; entry['recovery'] = recovery['state']
        entry['binary'] = {'action': 'kept', 'path': str(paths['bin_dir']/exe_name(catalog, app)),
                           'reason': f"an interrupted upgrade left recovery marker {recovery['marker']}; run setup --app {app} first"}
        return entry
    managed = managed_binary(paths, catalog, app); expected = managed['path']; expected_args = launch_args(catalog, app, paths)
    pinned = managed['pin']; still_launched = []
    def keep(row: dict, launches: bool) -> None:
        entry['registrations'].append(row); entry['status'] = 'attention'
        if launches: still_launched.append(row['host'])
    for host in HOSTS:
        if host not in targets:
            row, launches, attention = unrun_host(host, app, expected, hosts, env, home)
            entry['registrations'].append(row)
            if attention: entry['status'] = 'attention'
            if launches: still_launched.append(host)
            continue
        try:
            current = host_get(host, app, run, which, env, home)
        except (OSError, ValueError) as exc:
            # Uninspectable: it may still launch the binary, so it and everything it needs stay.
            keep({'host': host, 'action': 'kept', 'reason': str(exc)[:500]}, True); continue
        if current is None:
            entry['registrations'].append({'host': host, 'action': 'none', 'reason': 'not registered'}); continue
        owned, reason = registration_ownership(host, app, current, expected, expected_args, env, home)
        if not owned:
            # One whose command the host does not show may still launch the binary, just like one that names it.
            keep({'host': host, 'action': 'kept', 'command': shown(current.get('command')), 'reason': reason}, may_launch(current, expected)); continue
        if pinned is None:
            keep({'host': host, 'action': 'kept', 'command': current['command'],
                  'reason': 'the lock has no pin for this app, so Storytold cannot confirm it created this registration'}, False); continue
        if managed['exists'] and not managed['owned']:
            keep({'host': host, 'action': 'kept', 'command': current['command'],
                  'reason': f"the binary it points at is not provably Storytold's ({managed['reason']}); unregister by hand with `{host} mcp remove {app}` once you have inspected it"}, False)
            continue
        if not dry_run:
            try:
                host_remove(host, app, run, which)
            except (OSError, ValueError) as exc:
                # The entry may still be there: report it, keep what it launches, and go on with the other hosts and apps.
                keep({'host': host, 'action': 'kept', 'command': current['command'], 'reason': str(exc)[:500]}, True)
                log(f'{host}: {app}: FAILED: {exc}'); continue
            # Trust the file the host keeps, not only its exit status.
            state, left = user_scope_command(host, app, env, home)
            if state=='unreadable' or (state=='present' and same_binary(left, expected)):
                keep({'host': host, 'action': 'kept', 'command': current['command'],
                      'reason': f'`{host} mcp remove {app}` reported success, but ' + (left if state=='unreadable' else 'its user-scope file still registers it')}, True)
                continue
        entry['registrations'].append({'host': host, 'action': verb+'unregister', 'command': current['command']})
        log(f'{host}: {verb}unregister {app}')
    # Any other registration in the hosts' files that starts this binary (another name, an alias of the path, a Claude local-scope entry) counts too.
    skip = {(r['host'], app) for r in entry['registrations'] if r['action']=='would unregister'}
    references = [r for r in binary_references(expected, env, home, skip)
                  if not any(r==f"{h} user-scope entry '{app}'" for h in still_launched)]
    if references: entry['references'] = references; entry['status'] = 'attention'
    # A kept registration that may still launch the managed binary must not be left pointing at a deleted file,
    # and the pin is what lets a later --remove prove such a registration is Storytold's, so both stay while one remains.
    blocked = bool(still_launched or references)
    releasable = not blocked and (managed['owned'] or not managed['exists'])
    if not managed['exists']:
        entry['binary'] = {'action': 'none', 'path': expected, 'reason': 'not installed'}
    elif not managed['owned']:
        entry['binary'] = {'action': 'kept', 'path': expected, 'reason': managed['reason']}; entry['status'] = 'attention'
        log(f'{app}: kept {expected}: {managed["reason"]}')
    elif blocked:
        reason = 'registrations still launch it; ' + '; '.join(
            ([f'unregister them by hand ({"; ".join(f"`{h} mcp remove {app}`" for h in dict.fromkeys(still_launched))})'] if still_launched else [])
            + ([f'also remove {", ".join(references)}'] if references else [])) + ', then run --remove again'
        entry['binary'] = {'action': 'kept', 'path': expected, 'reason': reason}; entry['status'] = 'attention'
        log(f'{app}: kept {expected}: {reason}')
    else:
        try:
            if not dry_run: Path(expected).unlink()
            entry['binary'] = {'action': verb+'delete', 'path': expected, 'sha256': managed['sha256']}
            log(f'{app}: {verb}delete {expected}')
        except OSError as exc:
            entry['binary'] = {'action': 'kept', 'path': expected, 'reason': f'could not delete it: {exc}'}; entry['status'] = 'attention'; releasable = False
    if pinned is not None and releasable:
        marker = writing_marker(paths['lock'])
        try:
            if dry_run:
                require(not (marker.exists() or marker.is_symlink()), f'the leftover {marker} would block the pin rewrite; delete it once no setup is running')
            else:
                with exclusive(paths['lock']):
                    lock = load_json(paths['lock']); lock['apps'].pop(app, None); replace_file(paths['lock'], encoded(lock))
            entry['pin'] = {'action': verb+'drop', 'version': pinned.get('version')}
        except (OSError, ValueError) as exc:
            entry['pin'] = {'action': 'kept', 'reason': str(exc)[:500]}; entry['status'] = 'attention'; releasable = False
    elif pinned is not None:
        entry['pin'] = {'action': 'kept', 'reason': ("registrations that may still launch the managed path were kept; the pin stays so a later --remove can prove they are Storytold's"
                                                    if blocked else 'the binary at that path was kept, so its pin stays with it')}
    evidence = paths['evidence_dir']/(app+'.json')
    # Active, candidate (a failed run's record) and approved-call files are all kept, in archive/.
    names = [app+'.json', app+'-candidate.json', app+'-call.json']
    if any((paths['evidence_dir']/n).is_file() for n in names) and releasable:
        try:
            if not dry_run:
                for n in names: archive_evidence(paths['evidence_dir'], app, n)
            entry['evidence'] = {'action': verb+'archive', 'path': str(evidence)}
        except (OSError, ValueError) as exc:
            entry['evidence'] = {'action': 'kept', 'path': str(evidence), 'reason': str(exc)[:500]}; entry['status'] = 'attention'
    return entry

def remove(apps: list[str], *, hosts: list[str] | None, env: dict, home: Path, dry_run: bool = False, system: str = platform.system(),
           run: Runner = default_runner, which: Which = shutil.which, log: Logger = default_log, catalog: dict | None = None,
           **overrides: str | None) -> dict:
    """Unregister and delete only what Storytold provably manages; preview everything with dry_run.

    Two separate decisions per app. The binary is deleted only when the lock
    proves Storytold wrote exactly those bytes. A registration is removed only
    when it is, in full, the user-scope entry Storytold writes (command,
    arguments, scope, no other settings in the user-scope file) and the pinned
    binary is either owned or already gone. Every host gets a row: one whose
    CLI is not run (not on PATH, or left out by --host) is read from its
    user-scope file, and while any registration in the hosts' files may still
    launch the binary, the binary, its pin and its evidence stay. Everything
    else is kept and reported; `attention` says so. One app's unexpected error
    becomes its row, and the other apps still run.
    """
    catalog = catalog or load_catalog(); paths = resolve_paths(env, home, system, **overrides); targets = plan_hosts(hosts, which)
    # setup creates the state directory before it takes the run lock, so without one no run can be holding it; a preview changes nothing.
    with single_run(paths['state_dir']) if not dry_run and paths['state_dir'].is_dir() else nullcontext():
        marker = writing_marker(paths['lock'])
        # Refused before anything changes: a pin rewrite would fail only after binaries were already deleted.
        require(dry_run or not (marker.exists() or marker.is_symlink()),
                f'{marker} is left over from an interrupted run, or another setup is rewriting the lock; delete it once no setup is running. Nothing was changed.')
        rows = []
        for app in apps:
            try:
                rows.append(remove_app(app, paths, catalog, targets, hosts, dry_run=dry_run, run=run, which=which, log=log, env=env, home=home))
            except (OSError, ValueError, TypeError, KeyError) as exc:
                rows.append({'app': app, 'status': 'attention', 'error': str(exc)[:800], 'registrations': [], 'binary': None, 'pin': None, 'evidence': None,
                             'next': f'this app may be partly removed; `setup --remove --dry-run --app {app}` shows what is left'})
                log(f'{app}: FAILED: {exc}')
    status_value = 'ok' if all(r['status']=='ok' for r in rows) else 'attention'
    return {'schema_version': 1, 'dry_run': dry_run, 'status': status_value, 'apps': rows, 'workspace_kept': str(paths['work_root']),
            'notice': 'Only Storytold-managed binaries and the registrations Storytold wrote for them are removed; anything kept is listed with its reason. '
                      '`claude mcp get` starts the registered server for its health check, as a Claude Code session does.'}

def evidence_status(path: Path) -> str | None:
    """The recorded probe status (None when absent), never a bare "a file exists"."""
    if not path.is_file(): return None
    try:
        value = load_json(path).get('status')
    except (OSError, ValueError, AttributeError):
        return 'unreadable'
    return value if isinstance(value, str) else 'unreadable'

def registration_state(targets: list[str], app: str, run: Runner, which: Which, env: dict, home: Path) -> dict:
    registered, unknown = [], []
    for host in targets:
        try:
            if host_get(host, app, run, which, env, home) is not None: registered.append(host)
        except (OSError, ValueError):
            unknown.append(host)
    return {'registered': registered, 'registration_unknown': unknown}

def status(*, hosts: list[str] | None, env: dict, home: Path, system: str = platform.system(), run: Runner = default_runner,
           which: Which = shutil.which, releases: dict | None = None, catalog: dict | None = None, **overrides: str | None) -> dict:
    releases = releases or load_releases(); catalog = catalog or load_catalog()
    paths = resolve_paths(env, home, system, **overrides); targets = plan_hosts(hosts, which)
    rows = []
    for app in APP_IDS:
        managed = managed_binary(paths, catalog, app); pinned = managed['pin']
        evidence = paths['evidence_dir']/(app+'.json')
        rows.append({'app': app, 'manifest': releases['apps'][app]['tag'], 'installed': managed['exists'], 'path': managed['path'],
                     'owned': managed['owned'], 'reason': managed['reason'],
                     'pinned_version': pinned.get('version') if pinned else None,
                     'pinned_hash_matches': managed['owned'],
                     'manifest_commit_pinned': bool(pinned and pinned.get('revision')==releases['apps'][app]['commit']),
                     'probe_evidence': evidence_status(evidence),
                     'recovery': recovery_state(paths, catalog, app)['state'],
                     **registration_state(targets, app, run, which, env, home)})
    return {'schema_version': 1, 'paths': {k: str(v) for k, v in paths.items()}, 'hosts': targets, 'cosign': which('cosign'), 'apps': rows}
