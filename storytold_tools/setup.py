"""Explicit one-command Craft CLI setup: stage, verify, probe, promote, pin, register.

Nothing here runs unless an operator invokes `storytold.py setup`. The command
downloads only the reviewed release archives named in config/releases.json,
checks each archive against the manifest and the release's own SHA256SUMS.txt,
takes exactly one `<app>-cli` out of it, checks provenance (Apple notarization
by the pinned team on macOS; the Sigstore bundle the daily workflow signed on
Linux and Windows, and on macOS too when cosign is present), runs the existing
preflight and official-SDK probe against that staged candidate, and only then
promotes it, pins it in the private lock and registers it through the host's
own CLI. A candidate that fails any step leaves the active binary, its pin and
the host registrations untouched. Removal deletes only binaries the lock proves
Storytold installed and unregisters only entries that point at them. It never
edits host configuration files itself, starts no daemon, keeps one
registration per server name and never retries a write.
"""
from __future__ import annotations
from datetime import datetime, timezone
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
from typing import Callable
from urllib.parse import urlsplit
import urllib.request
import zipfile
from .catalog import APP_IDS, load_catalog, platform_id, preflight
from .common import ROOT, StorytoldError, absolute, create_new, directory, encoded, keys, load_json, require, snapshot
from .probe import SDK_VERSION
from .releases import asset_url, load_releases, load_signatures, published_hash, sums_url
from .workspace import MARKER, init_workspace, open_workspace

ALLOWED_HOSTS = {'github.com', 'objects.githubusercontent.com', 'release-assets.githubusercontent.com'}
MAX_DOWNLOAD = 512 * 1024 * 1024
STATE_FILE = 'setup.json'
PROMOTE_MARKER = 'promote.json'
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

def replace_file(path: Path, data: bytes, mode: int = 0o600) -> None:
    """Atomic rewrite of operator-owned state (lock, setup state); never partial."""
    absolute(path); directory(path.parent)
    fd, name = tempfile.mkstemp(prefix='.storytold-replace-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        os.chmod(name, mode); os.replace(name, path)
    except BaseException:
        Path(name).unlink(missing_ok=True); raise

def ensure_layout(paths: dict, log: Logger) -> None:
    for key in ('state_dir', 'evidence_dir'):
        p = paths[key]
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True); p.mkdir(mode=0o700); log(f'created {p}')
        if os.name != 'nt':
            require(p.stat().st_mode & 0o077 == 0, f'{p} must be owner-only (chmod 700)')
    bin_dir = paths['bin_dir']
    if not bin_dir.exists():
        bin_dir.parent.mkdir(parents=True, exist_ok=True); bin_dir.mkdir(mode=0o755); log(f'created {bin_dir}')
    directory(bin_dir)
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

def default_runner(argv: list[str]) -> tuple[int, str, str]:
    r = subprocess.run(argv, capture_output=True, text=True, check=False)
    return r.returncode, r.stdout, r.stderr

# ---------------------------------------------------------------- provenance
def check_notarization(binary: Path, team: str, run: Runner) -> dict:
    code, out, err = run(['spctl', '--assess', '--type', 'install', '-vv', str(binary)])
    combined = out + err
    require(code==0 and 'source=Notarized Developer ID' in combined, f'{binary.name}: not accepted as a notarized Developer ID binary:\n{combined.strip()[:500]}')
    code, out, err = run(['codesign', '-dv', '--verbose=2', str(binary)])
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
    if not info['exists']:
        info['reason'] = 'not installed'; return info
    pinned = pinned_entry(paths['lock'], app)
    info['pin'] = pinned
    if pinned is None or not isinstance(pinned.get('sha256'), str):
        info['reason'] = 'no lock entry records this file, so Storytold cannot prove it installed it'; return info
    try:
        sha, _, _ = snapshot(target)
        require(target.stat().st_nlink==1, 'the file has more than one hard link')
    except (OSError, ValueError) as exc:
        info['reason'] = f'not a plain regular file Storytold would have written: {exc}'; return info
    info['sha256'] = sha
    if sha != pinned['sha256']:
        info['reason'] = 'the installed bytes differ from the SHA-256 recorded in the lock'; return info
    info['owned'] = True
    return info

# ------------------------------------------------------------------- staging
def staging_dir(paths: dict, app: str) -> Path:
    p = paths['state_dir']/'staging'/app
    require(absolute(p).is_relative_to(paths['state_dir']), 'staging must stay inside the state directory')
    return p

def clear_staging(paths: dict, app: str, log: Logger) -> None:
    p = staging_dir(paths, app)
    if p.exists():
        shutil.rmtree(p); log(f'{app}: removed leftover staging from an earlier run')

def resume_interrupted_promotion(paths: dict, catalog: dict, app: str, log: Logger) -> bool:
    """A promote marker survives only between replacing the binary and rewriting the lock.

    If the active binary carries the marker's hash, finish the pin; otherwise
    the marker is stale and is discarded. Either way the next step sees a
    consistent binary/lock pair.
    """
    marker = staging_dir(paths, app)/PROMOTE_MARKER
    if not marker.is_file(): return False
    data = load_json(marker)
    target = paths['bin_dir']/exe_name(catalog, app)
    finished = False
    if isinstance(data, dict) and target.is_file():
        try:
            if snapshot(target)[0]==data.get('sha256'):
                pin(paths['lock'], app, {'commit': data['commit']}, data['sha256'], data['label'])
                log(f'{app}: completed an interrupted upgrade; the lock now records the promoted binary'); finished = True
        except (OSError, ValueError, KeyError):
            finished = False
    clear_staging(paths, app, log)
    return finished

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
        sha, nbytes, body = snapshot(extracted, body=True)
        provenance = check_provenance(extracted, sha, asset['name'], plat, releases, signatures, run=run, which=which,
                                      trust_upstream_sums=trust_upstream_sums, tmp=tmp, log=log)
        candidate = create_new(bin_dir/exe, body or b'', mode=0o755)
    label = f"{row['version']} ({row['tag']}, {asset['name']}, {provenance_label(provenance, releases['signers'])})"
    lock = staging/'lock.json'
    replace_file(lock, encoded({'schema_version': 1, 'platform': platform_id(),
                                'apps': {app: {'revision': row['commit'], 'version': label, 'sha256': sha}}}))
    return {'candidate': str(candidate), 'bin_dir': str(bin_dir), 'lock': str(lock), 'sha256': sha, 'bytes': nbytes,
            'archive_sha256': zip_sha, 'label': label, **provenance}

def promote(paths: dict, catalog: dict, app: str, candidate: Path, candidate_sha: str, row: dict, label: str, log: Logger) -> dict:
    """Replace or create the active binary from the verified candidate, then pin it.

    The marker written first makes the only non-atomic window (binary replaced,
    lock not yet rewritten) recoverable by `resume_interrupted_promotion`.
    """
    exe = exe_name(catalog, app); target = paths['bin_dir']/exe
    marker = staging_dir(paths, app)/PROMOTE_MARKER
    replace_file(marker, encoded({'app': app, 'sha256': candidate_sha, 'commit': row['commit'], 'label': label}))
    body = snapshot(candidate, body=True)[2] or b''
    if target.exists():
        staged = create_new(target.with_name(exe+'.storytold-new'), body, mode=0o755)
        os.replace(staged, target)
        log(f'{app}: promoted the verified candidate over the previous binary')
    else:
        create_new(target, body, mode=0o755)
        log(f'{app}: installed the verified candidate')
    require(snapshot(target)[0]==candidate_sha, f'{app}: promoted file changed during publication')
    entry = pin(paths['lock'], app, row, candidate_sha, label)
    marker.unlink()
    return entry

def pin(lock_path: Path, app: str, row: dict, binary_sha: str, label: str) -> dict:
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
        log(f'creating {venv} and installing the reviewed mcp=={SDK_VERSION} from PyPI (network)')
        code, _, err = run([sys.executable, '-m', 'venv', str(venv)])
        require(code==0, 'could not create the probe virtual environment:\n'+err.strip()[:500]+'\nUse --skip-probe to register without a native probe')
        code, _, err = run([str(py), '-m', 'pip', 'install', '--disable-pip-version-check', '--quiet', f'mcp=={SDK_VERSION}'])
        require(code==0 and ok(), 'could not install the probe SDK:\n'+err.strip()[:500]+'\nUse --skip-probe to register without a native probe')
    return str(py)

def archive_evidence(evidence_dir: Path, app: str) -> None:
    p = evidence_dir/(app+'.json')
    if p.exists():
        old = evidence_dir/'archive'; old.mkdir(mode=0o700, exist_ok=True)
        p.rename(old/f"{app}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json")

def run_probe(app: str, smoke_tool: str, paths: dict, python_exe: str, run: Runner, timeout: float, log: Logger,
              acknowledge_unconfined: bool = False, *, bin_dir: Path | None = None, lock: Path | None = None,
              output: Path | None = None) -> dict:
    """Probe the binary in `bin_dir` under `lock` (defaults: the active ones) into `output`."""
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
            'protocol_version': report.get('protocol_version'), 'server_info': report.get('server_info'), 'command': str(bin_dir)}

# ------------------------------------------------------------------ register
def host_argv(host: str, which: Which) -> list[str] | None:
    """Resolved host CLI; Windows .cmd shims run through cmd.exe, never by name."""
    path = which(host)
    if path is None: return None
    if path.lower().endswith(('.cmd', '.bat')): return ['cmd.exe', '/d', '/c', path]
    return [path]

def _claude_user_entry(app: str, env: dict | None, home: Path | None) -> dict | None:
    """Structured user-scope registration from .claude.json; only `command` and `args` are read."""
    if env is None or home is None: return None
    p = claude_user_config(env, home)
    if not p.is_file(): return None
    try:
        data = load_json(p)
    except (OSError, ValueError):
        return None
    servers = data.get('mcpServers') if isinstance(data, dict) else None
    row = servers.get(app) if isinstance(servers, dict) else None
    if not isinstance(row, dict) or not isinstance(row.get('command'), str): return None
    args = row.get('args', [])
    if not (isinstance(args, list) and all(isinstance(a, str) for a in args)): return None
    return {'command': row['command'], 'args': list(args)}

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
        code, out, _ = run([*base, 'mcp', 'get', app, '--json'])
        if code!=0: return None
        try:
            transport = json.loads(out).get('transport', {})
            command, args = transport.get('command'), transport.get('args')
        except (ValueError, AttributeError):
            command, args = None, None
        ok = isinstance(command, str) and isinstance(args, list) and all(isinstance(a, str) for a in args)
        return {'command': command if ok else None, 'args': list(args) if ok else None, 'args_text': None, 'scope': None, 'parse_error': not ok}
    code, out, _ = run([*base, 'mcp', 'get', app])
    if code!=0: return None
    command = args_text = scope = None
    for line in out.splitlines():
        s = line.strip()
        if s.startswith('Scope:'): scope = s.split(':', 1)[1].strip()
        elif s.startswith('Command:'): command = s.split(':', 1)[1].strip()
        elif s.startswith('Args:'): args_text = s.split(':', 1)[1].strip()
    result = {'command': command or None, 'args': None, 'args_text': args_text, 'scope': scope, 'parse_error': not command}
    if command and scope and scope.lower().startswith('user'):
        structured = _claude_user_entry(app, env, home)
        if structured is not None and structured['command']==command:
            result['args'] = structured['args']
    return result

def registration_matches(current: dict | None, command: str, args: list[str]) -> bool:
    if current is None or current.get('parse_error'): return False
    if current.get('command') != command: return False
    if current.get('args') is not None: return current['args']==list(args)
    return current.get('args_text')==' '.join(args)

def host_add(host: str, app: str, command: str, args: list[str], run: Runner, which: Which = shutil.which) -> None:
    base = host_argv(host, which) or [host]
    argv = ([*base, 'mcp', 'add', app, '--', command, *args] if host=='codex'
            else [*base, 'mcp', 'add', '--scope', 'user', '--transport', 'stdio', app, '--', command, *args])
    code, out, err = run(argv)
    require(code==0, f'{host}: registration failed:\n{(out+err).strip()[:800]}')

def host_remove(host: str, app: str, run: Runner, which: Which = shutil.which) -> None:
    base = host_argv(host, which) or [host]
    argv = [*base, 'mcp', 'remove', app] if host=='codex' else [*base, 'mcp', 'remove', '--scope', 'user', app]
    code, out, err = run(argv)
    require(code==0, f'{host}: removal failed:\n{(out+err).strip()[:800]}')

def register(app: str, launch: dict, hosts: list[str], run: Runner, replace: bool, log: Logger, which: Which = shutil.which,
             env: dict | None = None, home: Path | None = None) -> list[dict]:
    """One row per host; a failing host is reported, never hidden, and does not stop the others."""
    rows = []
    for host in hosts:
        row = {'host': host, 'command': launch['command'], 'args': launch['args']}
        try:
            current = host_get(host, app, run, which, env, home)
            if current is not None and current.get('parse_error'):
                raise StorytoldError(f"{host}: '{app}' is registered but `{host} mcp get` named no command; not touching it. Inspect it by hand.")
            matches = registration_matches(current, launch['command'], launch['args'])
            if current is not None and not matches:
                require(replace, f"{host}: '{app}' is already registered with a different command ({current.get('command')}); pass --replace to re-register it")
                host_remove(host, app, run, which); log(f'{host}: removed previous {app} registration')
            if not matches:
                host_add(host, app, launch['command'], launch['args'], run, which)
                after = host_get(host, app, run, which, env, home)
                require(registration_matches(after, launch['command'], launch['args']), f'{host}: {app} is not visible as registered after `mcp add`')
                log(f'{host}: registered {app} (user scope)')
            row['status'] = 'already_registered' if matches else 'registered'
        except (OSError, ValueError) as exc:
            row['status'] = 'failed'; row['error'] = str(exc)[:600]; log(f'{host}: {app}: FAILED: {exc}')
        rows.append(row)
    return rows

# ---------------------------------------------------------------------- flow
def plan_hosts(requested: list[str] | None, which: Which = shutil.which) -> list[str]:
    hosts = [h for h in HOSTS if (not requested or h in requested)]
    return [h for h in hosts if which(h) is not None]

def default_log(message: str) -> None:
    print('storytold setup: '+message, file=sys.stderr)

def setup(apps: list[str], *, acknowledge_unconfined: bool, hosts: list[str] | None, skip_probe: bool, upgrade: bool,
          replace: bool, dry_run: bool, timeout: float, env: dict, home: Path, trust_upstream_sums: bool = False,
          system: str = platform.system(), machine: str = platform.machine(), fetch: Fetcher = fetch, run: Runner = default_runner,
          which: Which = shutil.which, log: Logger = default_log, releases: dict | None = None, signatures: dict | None = None,
          catalog: dict | None = None, **overrides: str | None) -> dict:
    releases = releases or load_releases(); catalog = catalog or load_catalog()
    signatures = signatures if signatures is not None else load_signatures(releases=releases)
    plat = platform_key(system, machine)
    paths = resolve_paths(env, home, system, **overrides)
    require(not paths['lock'].is_relative_to(paths['work_root']) and not paths['evidence_dir'].is_relative_to(paths['work_root']),
            'lock and evidence must stay outside the native workspace')
    targets = plan_hosts(hosts, which)
    report = {'schema_version': 1, 'dry_run': dry_run, 'platform': platform_id(), 'platform_key': plat, 'cosign': which('cosign'),
              'paths': {k: str(v) for k, v in paths.items()}, 'hosts': targets, 'apps': [],
              'notice': 'Hosts load MCP servers when a session starts: open a new Claude Code or Codex session afterwards.'}
    if hosts and not targets:
        report['warnings'] = [f'requested host CLI not on PATH: {", ".join(hosts)}']
    if dry_run:
        for app in apps:
            row = releases['apps'][app]; asset = row['assets'][plat]; unconfined = catalog[app]['confinement']=='os_only'
            report['apps'].append({'app': app, 'release': row['tag'], 'download': asset_url(app, row, plat), 'bytes': asset['bytes'],
                                   'install_to': str(paths['bin_dir']/exe_name(catalog, app)), 'probe': not skip_probe,
                                   'sigstore_bundle': asset['name'] in signatures.get('bundles', {}),
                                   'register': (not unconfined or acknowledge_unconfined) and bool(targets),
                                   'needs_acknowledge_unconfined': unconfined and not acknowledge_unconfined})
        return report
    ensure_layout(paths, log)
    python_exe = None
    for app in apps:
        row = releases['apps'][app]; entry = {'app': app, 'release': row['tag']}
        try:
            resume_interrupted_promotion(paths, catalog, app, log)
            current = managed_binary(paths, catalog, app)
            up_to_date = current['owned'] and current['pin'].get('revision')==row['commit']
            if current['exists'] and not current['owned']:
                raise StorytoldError(f"{app}: {current['path']} exists but {current['reason']}; move it aside before setup will touch this path")
            if current['exists'] and not up_to_date:
                require(upgrade, f"{app}: installed at a different pin ({current['pin'].get('version')}); pass --upgrade to move to {row['tag']}")
            if catalog[app]['confinement']=='os_only' and not acknowledge_unconfined:
                # Preflight, and therefore any probe, needs the acknowledgement; without it nothing is downloaded or promoted.
                if up_to_date:
                    entry['install'] = {'path': current['path'], 'sha256': current['sha256'], 'unchanged': True, 'label': current['pin'].get('version')}
                    entry['pin'] = current['pin']; entry['status'] = 'installed_not_registered'
                    entry['next'] = f'{app} is installed and pinned but has no file-root flags; re-run with --acknowledge-unconfined to register it.'
                    report['apps'].append(entry); log(f'{app}: {entry["next"]}'); continue
                raise StorytoldError(f'{app} has no file-root flags: it can read and write anywhere your user can. '
                                     f'Re-run with --acknowledge-unconfined to install and register it for non-sensitive work.')
            if up_to_date:
                log(f"{app}: already installed at {row['tag']} and pinned; skipping download")
                entry['install'] = {'path': current['path'], 'sha256': current['sha256'], 'unchanged': True, 'label': current['pin'].get('version')}
                entry['pin'] = current['pin']
                probe_bin, probe_lock, probe_output = paths['bin_dir'], paths['lock'], None
            else:
                clear_staging(paths, app, log)
                staged = stage_candidate(app, plat, releases, signatures, catalog, paths, fetch=fetch, run=run, which=which,
                                         trust_upstream_sums=trust_upstream_sums, log=log)
                entry['candidate'] = {k: staged[k] for k in ('candidate', 'sha256', 'bytes', 'archive_sha256', 'label') if k in staged}
                probe_bin, probe_lock = Path(staged['bin_dir']), Path(staged['lock'])
                probe_output = paths['evidence_dir']/(app+'-candidate.json')
            # Preflight and probe run against the candidate (or the active binary when nothing changed).
            preflight(probe_bin, paths['work_root'], paths['output_root'], probe_lock, [app], catalog, acknowledge_unconfined)
            if skip_probe:
                entry['probe'] = {'status': 'skipped', 'native_runtime_verified': False}
                log(f'{app}: probe skipped on request; the binary has not been exercised')
            else:
                python_exe = python_exe or probe_python(paths['state_dir'], run, log, system)
                entry['probe'] = run_probe(app, row['smoke_tool'], paths, python_exe, run, timeout, log, acknowledge_unconfined,
                                           bin_dir=probe_bin, lock=probe_lock, output=probe_output)
            if not up_to_date:
                staged_sha = staged['sha256']
                if current['owned'] and current['sha256']==staged_sha:
                    entry['pin'] = pin(paths['lock'], app, row, staged_sha, staged['label'])
                    log(f'{app}: installed binary already matches this release; pin updated, file unchanged')
                else:
                    entry['pin'] = promote(paths, catalog, app, Path(staged['candidate']), staged_sha, row, staged['label'], log)
                entry['install'] = {'path': str(paths['bin_dir']/exe_name(catalog, app)), 'sha256': staged_sha, 'bytes': staged['bytes'],
                                    'archive_sha256': staged['archive_sha256'], 'previous_sha256': current['sha256'], 'label': staged['label'],
                                    **{k: staged[k] for k in ('notarized', 'team', 'sigstore', 'identity', 'provenance') if k in staged}}
                if probe_output is not None and probe_output.is_file():
                    archive_evidence(paths['evidence_dir'], app); probe_output.rename(paths['evidence_dir']/(app+'.json'))
                    entry['probe']['evidence'] = str(paths['evidence_dir']/(app+'.json'))
                clear_staging(paths, app, lambda _: None)
            # The active binary and lock must agree before anything is registered.
            launch = preflight(paths['bin_dir'], paths['work_root'], paths['output_root'], paths['lock'], [app], catalog, acknowledge_unconfined)['launches'][0]
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
    report['status'] = 'passed' if all(a.get('status') not in {'failed', 'partially_registered'} for a in report['apps']) else 'failed'
    return report

def remove(apps: list[str], *, hosts: list[str] | None, env: dict, home: Path, dry_run: bool = False, system: str = platform.system(),
           run: Runner = default_runner, which: Which = shutil.which, log: Logger = default_log, catalog: dict | None = None,
           **overrides: str | None) -> dict:
    """Unregister and delete only what Storytold provably manages; preview everything with dry_run.

    A registration is removed only when it points at the managed binary path; a
    binary is deleted only when the lock proves Storytold wrote those exact
    bytes. Everything else is kept and reported, and the result is `attention`.
    """
    catalog = catalog or load_catalog(); paths = resolve_paths(env, home, system, **overrides); targets = plan_hosts(hosts, which)
    verb = 'would ' if dry_run else ''
    rows = []
    for app in apps:
        entry = {'app': app, 'registrations': [], 'binary': None, 'pin': None, 'evidence': None, 'status': 'ok'}
        managed = managed_binary(paths, catalog, app); expected = managed['path']
        for host in targets:
            current = host_get(host, app, run, which, env, home)
            if current is None:
                entry['registrations'].append({'host': host, 'action': 'none', 'reason': 'not registered'}); continue
            if current.get('parse_error'):
                entry['registrations'].append({'host': host, 'action': 'kept', 'reason': f'`{host} mcp get` named no command; inspect it by hand'})
                entry['status'] = 'attention'; continue
            if current['command'] != expected:
                entry['registrations'].append({'host': host, 'action': 'kept', 'command': current['command'],
                                               'reason': f'points at {current["command"]}, not the Storytold-managed {expected}; not Storytold\'s to remove'})
                entry['status'] = 'attention'; continue
            if not dry_run: host_remove(host, app, run, which)
            entry['registrations'].append({'host': host, 'action': verb+'unregister', 'command': current['command']})
            log(f'{host}: {verb}unregister {app}')
        if not managed['exists']:
            entry['binary'] = {'action': 'none', 'path': expected, 'reason': 'not installed'}
        elif not managed['owned']:
            entry['binary'] = {'action': 'kept', 'path': expected, 'reason': managed['reason']}; entry['status'] = 'attention'
            log(f'{app}: kept {expected}: {managed["reason"]}')
        else:
            if not dry_run: Path(expected).unlink()
            entry['binary'] = {'action': verb+'delete', 'path': expected, 'sha256': managed['sha256']}
            log(f'{app}: {verb}delete {expected}')
        pinned = managed['pin']
        if pinned is not None and (not managed['exists'] or managed['owned']):
            if not dry_run:
                lock = load_json(paths['lock']); del lock['apps'][app]; replace_file(paths['lock'], encoded(lock))
            entry['pin'] = {'action': verb+'drop', 'version': pinned.get('version')}
        elif pinned is not None:
            entry['pin'] = {'action': 'kept', 'reason': 'the binary at that path was kept, so its pin stays with it'}
        evidence = paths['evidence_dir']/(app+'.json')
        if evidence.is_file() and (not managed['exists'] or managed['owned']):
            if not dry_run: archive_evidence(paths['evidence_dir'], app)
            entry['evidence'] = {'action': verb+'archive', 'path': str(evidence)}
        rows.append(entry)
    status = 'ok' if all(r['status']=='ok' for r in rows) else 'attention'
    return {'schema_version': 1, 'dry_run': dry_run, 'status': status, 'apps': rows, 'workspace_kept': str(paths['work_root']),
            'notice': 'Only Storytold-managed binaries and registrations pointing at them are removed; anything kept is listed with its reason.'}

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
                     'probe_evidence': evidence.is_file(),
                     'interrupted_upgrade': (staging_dir(paths, app)/PROMOTE_MARKER).is_file(),
                     'registered': [h for h in targets if host_get(h, app, run, which, env, home) is not None]})
    return {'schema_version': 1, 'paths': {k: str(v) for k, v in paths.items()}, 'hosts': targets, 'cosign': which('cosign'), 'apps': rows}
