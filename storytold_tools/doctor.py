"""Read-only connection diagnostics: why a host may lack a Craft MCP server.

Nothing is executed, installed, downloaded or edited. Host configuration is only
parsed to list which Craft servers are registered and whether their commands
exist. A registration found here is not proof that the host loaded or approved it.
Every `next` step is the explicit setup command; doctor never runs it.
"""
from __future__ import annotations
import os
from pathlib import Path
import platform
import shutil
import tomllib
from typing import Mapping
from .catalog import APP_IDS, load_catalog
from .common import MAX_JSON, ROOT, parse_json, require, snapshot
from .releases import load_releases
from .setup import load_state, resolve_paths

NEXT = {
    'registered': 'Registered. If the host still lacks its tools, start a new host session and check its MCP list.',
    'registered_command_missing': 'The registered command is missing or not executable; re-run `{cmd}` (add --upgrade if a stale file is in the way).',
    'cli_not_registered': 'CLI found but no host registration; run `{cmd}` (or follow docs/operations.md sections 1-5).',
    'desktop_app_only': 'The macOS desktop app contains no MCP server; run `{cmd}` to install the notarized {exe} and register it.',
    'not_installed': 'Not installed; run `{cmd}`.',
}

def setup_command(plugin_root: Path, app: str, unconfined: bool) -> str:
    return f'python3 {plugin_root/"storytold.py"} setup --app {app}' + (' --acknowledge-unconfined' if unconfined else '')

def default_app_dirs(home: Path) -> list[Path]:
    return [Path('/Applications'), home/'Applications'] if platform.system()=='Darwin' else []

def host_configs(env: Mapping[str,str], cwd: Path, home: Path) -> list[tuple[str,Path,str]]:
    codex_home = Path(env['CODEX_HOME']) if env.get('CODEX_HOME') else home/'.codex'
    return [('codex', codex_home/'config.toml', 'mcp_servers'),
            ('codex_project', cwd/'.codex'/'config.toml', 'mcp_servers'),
            ('claude_project', cwd/'.mcp.json', 'mcpServers')]

def registrations(path: Path, key: str) -> dict[str,object]:
    """Server name -> configured command, from one TOML or JSON host config."""
    data = snapshot(path, limit=MAX_JSON, body=True)[2] or b''
    parsed = tomllib.loads(data.decode('utf-8')) if path.suffix=='.toml' else parse_json(data)
    require(isinstance(parsed, dict), 'host config must be an object/table')
    servers = parsed.get(key, {})
    require(isinstance(servers, dict), f'{key} must be an object/table')
    return {name: row.get('command') if isinstance(row, dict) else None for name, row in servers.items()}

def runnable(command: object) -> bool:
    return isinstance(command, str) and Path(command).is_absolute() and Path(command).is_file() and os.access(command, os.X_OK)

def pins(lock_path: Path) -> dict:
    if not lock_path.is_file(): return {}
    try:
        lock = parse_json(snapshot(lock_path, limit=MAX_JSON, body=True)[2] or b'')
    except (OSError, ValueError):
        return {}
    apps = lock.get('apps') if isinstance(lock, dict) else None
    return {a: r.get('version') for a, r in apps.items() if isinstance(r, dict)} if isinstance(apps, dict) else {}

def report(env: Mapping[str,str], cwd: Path, home: Path, app_dirs: list[Path], plugin_root: Path = ROOT) -> dict:
    catalog = load_catalog(); releases = load_releases(); found = {}; errors = []
    for host, path, key in host_configs(env, cwd, home):
        if not path.is_file(): continue
        try:
            found[host] = (path, registrations(path, key))
        except (OSError, ValueError) as exc:
            errors.append({'host': host, 'config': str(path), 'error': str(exc)[:300]})
    try:
        paths = resolve_paths(dict(env), home); state = load_state(dict(env), home)
    except (OSError, ValueError) as exc:
        errors.append({'host': 'setup_state', 'config': '', 'error': str(exc)[:300]}); paths = None; state = {}
    bin_dir = env.get('CRAFT_BIN_DIR') or (paths and str(paths['bin_dir']))
    pinned = pins(paths['lock']) if paths else {}
    rows = []
    for app in APP_IDS:
        exe = catalog[app]['executable'] + ('.exe' if os.name=='nt' else '')
        cli = None
        if bin_dir and runnable(str(Path(bin_dir)/exe)): cli = str(Path(bin_dir)/exe)
        cli = cli or shutil.which(exe, path=env.get('PATH', ''))
        desktop = next((str(d/(catalog[app]['name']+'.app')) for d in app_dirs if (d/(catalog[app]['name']+'.app')).is_dir()), None)
        regs = [{'host': host, 'config': str(path), 'command': servers[app], 'command_runnable': runnable(servers[app])}
                for host, (path, servers) in found.items() if app in servers]
        status = ('registered' if regs and all(r['command_runnable'] for r in regs) else
                  'registered_command_missing' if regs else
                  'cli_not_registered' if cli else
                  'desktop_app_only' if desktop else 'not_installed')
        unconfined = catalog[app]['confinement']=='os_only'
        cmd = setup_command(plugin_root, app, unconfined)
        rows.append({'app': app, 'desktop_app': desktop, 'cli': cli, 'registrations': regs, 'status': status,
                     'manifest_release': releases['apps'][app]['tag'], 'pinned_version': pinned.get(app),
                     'setup_command': cmd, 'next': NEXT[status].format(cmd=cmd, exe=catalog[app]['executable'])})
    return {'apps': rows, 'host_config_errors': errors, 'setup_state_recorded': bool(state),
            'notice': 'Static view of files only; a host loads MCP servers at session start and may still need approval.'}
