"""Explicit one-command Craft CLI setup: download, verify, pin, probe, register.

Nothing here runs unless an operator invokes `storytold.py setup`. The command
downloads only the reviewed release archives named in config/releases.json,
checks each archive against the manifest and the release's own SHA256SUMS.txt,
takes exactly one `<app>-cli` out of it, checks provenance (Apple notarization
by the pinned team on macOS; the Sigstore bundle the daily workflow signed on
Linux and Windows, and on macOS too when cosign is present), pins the binary in
the private lock, runs the existing preflight and probe, and registers the
server through the host's own CLI. It never edits host configuration files
itself, starts no daemon, keeps one registration per server name and never
retries a write.
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
    return catalog[app]['executable'] + ('.exe' if os.name=='nt' else '')

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

def extract_cli(archive: Path, dest_dir: Path, exe: str) -> Path:
    """Take exactly the one regular `<app>-cli` member; ignore the rest, refuse anything unsafe.

    Full-application archives (Linux tarballs, Windows portable zips) also carry
    the desktop binary; only the CLI is copied out.
    """
    dest_dir.mkdir(mode=0o700)
    target = dest_dir/exe
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

# ------------------------------------------------------------------- install
def pinned_entry(lock_path: Path, app: str) -> dict | None:
    if not lock_path.is_file(): return None
    lock = load_json(lock_path)
    entry = lock.get('apps', {}).get(app) if isinstance(lock, dict) and isinstance(lock.get('apps'), dict) else None
    return entry if isinstance(entry, dict) else None

def install_app(app: str, plat: str, releases: dict, signatures: dict, catalog: dict, paths: dict, *, fetch: Fetcher, run: Runner,
                which: Which, upgrade: bool, trust_upstream_sums: bool, log: Logger) -> dict:
    row = releases['apps'][app]; asset = row['assets'][plat]; exe = exe_name(catalog, app)
    target = paths['bin_dir']/exe
    previous = None
    if target.exists():
        previous = snapshot(target)[0]
        pinned = pinned_entry(paths['lock'], app)
        if pinned and pinned.get('sha256')==previous and pinned.get('revision')==row['commit']:
            log(f"{app}: already installed at {row['tag']} and pinned; skipping download")
            return {'path': str(target), 'sha256': previous, 'bytes': target.stat().st_size, 'archive_sha256': asset['sha256'],
                    'previous_sha256': previous, 'unchanged': True, 'label': pinned.get('version')}
        require(upgrade, f'{app}: {target} already exists with a different pin; pass --upgrade to replace it')
    with tempfile.TemporaryDirectory(prefix='storytold-download-', dir=paths['state_dir']) as td:
        tmp = Path(td); archive = tmp/asset['name']
        log(f"{app}: downloading {asset['name']} ({asset['bytes']} bytes) from GitHub release {row['tag']}")
        n = fetch(asset_url(app, row, plat), archive, MAX_DOWNLOAD)
        require(n==asset['bytes'], f"{app}: downloaded {n} bytes; the manifest expects {asset['bytes']}")
        zip_sha = snapshot(archive)[0]
        require(zip_sha==asset['sha256'], f'{app}: archive SHA-256 differs from config/releases.json; review the release before refreshing the manifest')
        fetch(sums_url(app, row), tmp/'SHA256SUMS.txt', 1024*1024)
        published = published_hash((tmp/'SHA256SUMS.txt').read_bytes(), asset['name'])
        require(published==zip_sha, f"{app}: upstream SHA256SUMS.txt disagrees with the manifest for {asset['name']}; stop and review the release")
        binary = extract_cli(archive, tmp/'extract', exe)
        sha, nbytes, body = snapshot(binary, body=True)
        provenance = check_provenance(binary, sha, asset['name'], plat, releases, signatures, run=run, which=which,
                                      trust_upstream_sums=trust_upstream_sums, tmp=tmp, log=log)
        if previous is None:
            create_new(target, body or b'', mode=0o755)
        elif previous == sha:
            log(f'{app}: installed binary already matches this release; unchanged')
        else:
            staged = create_new(target.with_name(exe+'.storytold-new'), body or b'', mode=0o755)
            os.replace(staged, target)
            log(f'{app}: replaced {previous[:12]}… with {sha[:12]}…')
    require(snapshot(target)[0]==sha, f'{app}: installed file changed during publication')
    label = f"{row['version']} ({row['tag']}, {asset['name']}, {provenance_label(provenance, releases['signers'])})"
    return {'path': str(target), 'sha256': sha, 'bytes': nbytes, 'archive_sha256': zip_sha, 'previous_sha256': previous,
            'label': label, **provenance}

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
              acknowledge_unconfined: bool = False) -> dict:
    archive_evidence(paths['evidence_dir'], app)
    call = paths['evidence_dir']/(app+'-call.json')
    replace_file(call, encoded({'name': smoke_tool, 'arguments': {}}))
    output = paths['evidence_dir']/(app+'.json')
    log(f'{app}: probing initialize, tools/list and read-only {smoke_tool} through the official SDK')
    code, out, err = run([python_exe, str(ROOT/'storytold.py'), 'probe', '--bin-dir', str(paths['bin_dir']), '--work-root', str(paths['work_root']),
                          '--output-root', str(paths['output_root']), '--lock', str(paths['lock']), '--app', app, '--confirm-execution',
                          '--timeout', str(timeout), '--call-json', str(call), '--approve-call', '--output', str(output),
                          *(['--acknowledge-unconfined'] if acknowledge_unconfined else [])])
    require(output.is_file(), f'{app}: probe wrote no evidence:\n{err.strip()[:800]}')
    report = load_json(output)
    require(code==0 and report.get('status')=='discovery_and_call_passed',
            f"{app}: native probe {report.get('status')}: {report.get('error')}; evidence kept at {output}")
    return {'evidence': str(output), 'status': report['status'], 'tools': len(report.get('tools', [])),
            'protocol_version': report.get('protocol_version'), 'server_info': report.get('server_info')}

# ------------------------------------------------------------------ register
def host_argv(host: str, which: Which) -> list[str] | None:
    """Resolved host CLI; Windows .cmd shims run through cmd.exe, never by name."""
    path = which(host)
    if path is None: return None
    if path.lower().endswith(('.cmd', '.bat')): return ['cmd.exe', '/d', '/c', path]
    return [path]

def host_get(host: str, app: str, run: Runner, which: Which = shutil.which) -> dict | None:
    """Current registration as the host reports it, or None when absent."""
    base = host_argv(host, which) or [host]
    if host=='codex':
        code, out, _ = run([*base, 'mcp', 'get', app, '--json'])
        if code!=0: return None
        try:
            transport = json.loads(out).get('transport', {})
        except ValueError:
            return {'command': None, 'args': None}
        return {'command': transport.get('command'), 'args': transport.get('args')}
    code, out, _ = run([*base, 'mcp', 'get', app])
    if code!=0: return None
    command = args = None
    for line in out.splitlines():
        s = line.strip()
        if s.startswith('Command:'): command = s.split(':', 1)[1].strip()
        elif s.startswith('Args:'): args = s.split(':', 1)[1].split()
    return {'command': command, 'args': args}

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

def register(app: str, launch: dict, hosts: list[str], run: Runner, replace: bool, log: Logger, which: Which = shutil.which) -> list[dict]:
    rows = []
    for host in hosts:
        current = host_get(host, app, run, which)
        matches = current is not None and current['command']==launch['command'] and current['args']==launch['args']
        if current is not None and not matches:
            require(replace, f"{host}: '{app}' is already registered with a different command; pass --replace to re-register it")
            host_remove(host, app, run, which); log(f'{host}: removed previous {app} registration')
        if not matches:
            host_add(host, app, launch['command'], launch['args'], run, which)
            after = host_get(host, app, run, which)
            require(after is not None and after['command']==launch['command'], f'{host}: {app} is not visible after registration')
            log(f'{host}: registered {app} (user scope)')
        rows.append({'host': host, 'status': 'already_registered' if matches else 'registered', 'command': launch['command'], 'args': launch['args']})
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
            entry['install'] = install_app(app, plat, releases, signatures, catalog, paths, fetch=fetch, run=run, which=which,
                                           upgrade=upgrade, trust_upstream_sums=trust_upstream_sums, log=log)
            entry['pin'] = pin(paths['lock'], app, row, entry['install']['sha256'], entry['install']['label'])
            if catalog[app]['confinement']=='os_only' and not acknowledge_unconfined:
                entry['status'] = 'installed_not_registered'
                entry['next'] = (f'{app} has no file-root flags: it can read and write anywhere your user can. '
                                 f'Re-run with --acknowledge-unconfined to register it for non-sensitive work.')
                report['apps'].append(entry); log(f'{app}: installed; not registered ({entry["next"]})'); continue
            pf = preflight(paths['bin_dir'], paths['work_root'], paths['output_root'], paths['lock'], [app], catalog, acknowledge_unconfined)
            launch = pf['launches'][0]
            if skip_probe:
                entry['probe'] = {'status': 'skipped', 'native_runtime_verified': False}
                log(f'{app}: probe skipped on request; the binary has not been exercised')
            else:
                python_exe = python_exe or probe_python(paths['state_dir'], run, log, system)
                entry['probe'] = run_probe(app, row['smoke_tool'], paths, python_exe, run, timeout, log, acknowledge_unconfined)
            entry['registrations'] = register(app, launch, targets, run, replace, log, which) if targets else []
            entry['status'] = 'registered' if targets else 'installed_no_host_cli'
            if not targets: entry['next'] = 'No codex/claude CLI on PATH: install one, then re-run setup to register.'
        except (OSError, ValueError, TypeError, KeyError, tarfile.TarError, zipfile.BadZipFile) as exc:
            entry['status'] = 'failed'; entry['error'] = str(exc)[:1000]
            report['apps'].append(entry); log(f'{app}: FAILED: {exc}')
            break
        report['apps'].append(entry)
    report['status'] = 'passed' if all(a.get('status')!='failed' for a in report['apps']) else 'failed'
    return report

def remove(apps: list[str], *, hosts: list[str] | None, env: dict, home: Path, system: str = platform.system(), run: Runner = default_runner,
           which: Which = shutil.which, log: Logger = default_log, catalog: dict | None = None, **overrides: str | None) -> dict:
    catalog = catalog or load_catalog(); paths = resolve_paths(env, home, system, **overrides); targets = plan_hosts(hosts, which)
    rows = []
    for app in apps:
        entry = {'app': app, 'hosts': [], 'binary_removed': False, 'pin_removed': False}
        for host in targets:
            if host_get(host, app, run, which) is not None:
                host_remove(host, app, run, which); entry['hosts'].append(host); log(f'{host}: removed {app}')
        target = paths['bin_dir']/exe_name(catalog, app)
        if target.is_file() and target.stat().st_nlink==1:
            target.unlink(); entry['binary_removed'] = True; log(f'{app}: removed {target}')
        if paths['lock'].exists():
            lock = load_json(paths['lock'])
            if isinstance(lock, dict) and isinstance(lock.get('apps'), dict) and app in lock['apps']:
                del lock['apps'][app]; replace_file(paths['lock'], encoded(lock)); entry['pin_removed'] = True
        if paths['evidence_dir'].is_dir(): archive_evidence(paths['evidence_dir'], app)
        rows.append(entry)
    return {'schema_version': 1, 'apps': rows, 'workspace_kept': str(paths['work_root'])}

def status(*, hosts: list[str] | None, env: dict, home: Path, system: str = platform.system(), run: Runner = default_runner,
           which: Which = shutil.which, releases: dict | None = None, catalog: dict | None = None, **overrides: str | None) -> dict:
    releases = releases or load_releases(); catalog = catalog or load_catalog()
    paths = resolve_paths(env, home, system, **overrides); targets = plan_hosts(hosts, which)
    lock = load_json(paths['lock']) if paths['lock'].is_file() else {}
    pins = lock.get('apps', {}) if isinstance(lock, dict) and isinstance(lock.get('apps'), dict) else {}
    rows = []
    for app in APP_IDS:
        target = paths['bin_dir']/exe_name(catalog, app); pinned = pins.get(app) if isinstance(pins.get(app), dict) else None
        evidence = paths['evidence_dir']/(app+'.json')
        rows.append({'app': app, 'manifest': releases['apps'][app]['tag'], 'installed': target.is_file(), 'path': str(target),
                     'pinned_version': pinned.get('version') if pinned else None,
                     'pinned_hash_matches': bool(target.is_file() and pinned and snapshot(target)[0]==pinned.get('sha256')),
                     'manifest_commit_pinned': bool(pinned and pinned.get('revision')==releases['apps'][app]['commit']),
                     'probe_evidence': evidence.is_file(),
                     'registered': [h for h in targets if host_get(h, app, run, which) is not None]})
    return {'schema_version': 1, 'paths': {k: str(v) for k, v in paths.items()}, 'hosts': targets, 'cosign': which('cosign'), 'apps': rows}
