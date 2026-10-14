"""Offline structural checks. No native/host execution or remote schema fetches."""
from __future__ import annotations

import ast
import json
from pathlib import Path, PurePosixPath
import re
import sys
import tomllib
from urllib.parse import unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from storytold_tools.build import allowlist, project, render, source_map
from storytold_tools.catalog import APP_IDS, load_catalog, templates
from storytold_tools.releases import load_releases, load_signatures
from storytold_tools.common import ROOT, StorytoldError, digest, encoded, parse_json, require

ORIGINAL_HASHES = {
    'Claude_Code_Craft_Native_MCP_Project_Plan.md':
        'fabea9691589f563c6f9f7a8df89d2d8b835ea933315ad4d6c1ad5b8dfd0cbc1',
    'Crafting_Apps_CLI_MCP_Integration_Reference.md':
        '3f0ec5724b801db503d10947c2e06c5a0c79e68f0996cb7684f10a77ef92f45c',
}


def local_links(files: dict[str, bytes]) -> list[str]:
    """Validate file targets, not remote URLs or Markdown renderer anchor rules."""
    checked = []
    for name, data in sorted(files.items()):
        if not name.endswith('.md'):
            continue
        lines = data.decode('utf-8').splitlines()
        prose = []
        fence = None
        for line in lines:
            if line.lstrip().startswith(('```', '~~~')):
                marker = line.lstrip()[:3]
                fence = None if fence == marker else marker
                continue
            if fence is None:
                prose.append(line)
        for target in re.findall(r'\[[^\]\n]+\]\(([^\s)]+)(?:[^)]*)\)', '\n'.join(prose)):
            parsed = urlsplit(target.strip('<>'))
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            path = unquote(parsed.path)
            require(not path.startswith('/') and '\\' not in path, f'{name}: nonportable link {target}')
            parts = list(PurePosixPath(name).parent.parts)
            for part in path.split('/'):
                if part in ('', '.'):
                    continue
                if part == '..':
                    require(bool(parts), f'{name}: link escapes package: {target}')
                    parts.pop()
                else:
                    parts.append(part)
            resolved = '/'.join(parts)
            require(resolved in files or any(n.startswith(resolved.rstrip('/') + '/') for n in files),
                    f'{name}: missing local link {target}')
            checked.append(name + ' -> ' + resolved)
    return checked


def check() -> dict:
    files = source_map()
    names = set(files)
    manifest = allowlist()
    checks = []
    parsed_counts = {'python': 0, 'json': 0, 'toml': 0}
    for name, data in sorted(files.items()):
        if name.endswith('.py'):
            ast.parse(data, filename=name)
            parsed_counts['python'] += 1
        elif name.endswith('.json'):
            parse_json(data)
            parsed_counts['json'] += 1
        elif name.endswith('.toml'):
            tomllib.loads(data.decode('utf-8'))
            parsed_counts['toml'] += 1
        else:
            continue
        checks.append('parse:' + name)
    require(manifest['source'] == sorted(manifest['source']) and manifest['plugin'] == sorted(manifest['plugin']),
            'packaging allowlists must be sorted')
    checks.append('sorted-explicit-allowlists')
    p = project()
    catalog = load_catalog()
    require(len(catalog) == 13, 'expected thirteen native apps')
    checks.append('thirteen-native-apps-exact-reviewed-flags')
    for name, data in templates(catalog).items():
        require(files['config/' + name] == data, f'launch template drift: {name}')
        checks.append('template:' + name)
    releases = load_releases()
    require(files['config/releases.json'] == encoded(releases),
            'config/releases.json must be canonical JSON; regenerate it with scripts/refresh_releases.py')
    for app, row in releases['apps'].items():
        for asset in row['assets'].values():
            require(asset['name'].startswith(app + '-'), f'{app}: manifest asset belongs to another app')
    checks.append('release-manifest-thirteen-reviewed-pins-three-platforms')
    signatures = load_signatures(releases=releases)
    require(files['config/signatures.json'] == encoded(signatures), 'config/signatures.json must be canonical JSON; regenerate it with scripts/sign_releases.py')
    checks.append('signature-store-matches-manifest')
    refresh = files['.github/workflows/releases.yml'].decode('utf-8')
    uses = re.findall(r'uses:\s*(\S+)', refresh)
    require(uses and all(re.fullmatch(r'[a-z-]+/[a-z-]+@[0-9a-f]{40}', x) for x in uses), 'release workflow actions must be full-commit pinned')
    require('persist-credentials: false' in refresh and 'id-token: write' in refresh, 'release workflow must not persist credentials and must request an OIDC token for keyless signing')
    require('pull_request_target' not in refresh and 'write-all' not in refresh and 'secrets.' not in refresh, 'release workflow must stay on github.token with scoped permissions')
    require('cosign-release:' in refresh and 'bot/releases' in refresh, 'release workflow must pin cosign and publish through the bot/releases pull request')
    verify_section = refresh[refresh.index('verify:'):refresh.index('merge:')]
    require('--trust-upstream-sums' not in verify_section, 'release verification must not fall back to checksum-only trust')
    require(0 <= verify_section.index('scripts/check_bundles.py') < verify_section.index('storytold.py setup'),
            'release verification must assert complete Sigstore bundles before running setup')
    checks.append('release-verification-strict-provenance-after-bundle-check')
    for filename, expected in ORIGINAL_HASHES.items():
        require(digest(files['docs/sources/' + filename]) == expected, 'supplied source modified: ' + filename)
        checks.append('source-sha256:' + filename)
    for path in ('.claude-plugin/marketplace.json', '.agents/plugins/marketplace.json'):
        value = parse_json(files[path])
        require(value['name'] == p['marketplace'], 'marketplace identity drift')
        entries = value['plugins']
        require(len(entries) == 1 and entries[0]['name'] == p['name'], 'plugin identity drift')
        source = entries[0]['source']
        require((source if isinstance(source, str) else source['path']) == './plugins/storytold',
                'marketplaces must use the same generated runtime')
        require(entries[0].get('description', p['description']) == p['description'],
                'marketplace plugin description must match packaging/project.json')
        checks.append('marketplace:' + path)
    readme = files['README.md'].decode('utf-8')
    plugin_id = p['name'] + '@' + p['marketplace']
    for command in ('claude plugin marketplace add https://github.com/' + p['repository'],
                    'claude plugin install ' + plugin_id,
                    'codex plugin marketplace add ' + p['repository'],
                    'codex plugin add ' + plugin_id):
        require(command in readme, 'README install command drift: ' + command)
    checks.append('readme-install-commands-plugin@marketplace')
    for script in sorted(set(re.findall(r'\bscripts/[A-Za-z0-9_]+\.py\b', files['Makefile'].decode('utf-8')))):
        require(script in names, 'Makefile references a missing script: ' + script)
    checks.append('makefile-script-references')
    require('.mcp.json' not in names and 'mcp.json' not in names, 'inactive examples only before native proof')
    skills = [n for n in names if n.startswith('skills/') and n.endswith('/SKILL.md')]
    require(skills == ['skills/craft/SKILL.md'], 'one canonical craft Skill required')
    skill = files[skills[0]].decode('utf-8')
    require(skill.startswith('---\nname: craft\n') and '\ndescription: ' in skill, 'Skill metadata drift')
    require('allowed-tools:' not in skill and 'hooks:' not in skill, 'Skill must not grant execution privileges')
    require(len(skill) < 10000, 'Skill entry must stay compact; use on-demand references')
    cards = {PurePosixPath(n).stem for n in names if n.startswith('skills/craft/references/apps/') and n.endswith('.md')}
    require(cards == set(APP_IDS), 'thirteen app cards required')
    checks += ['one-compact-skill-no-auto-grants', 'thirteen-on-demand-app-cards', 'no-active-native-config']
    scenarios = parse_json(files['tests/native/acceptance.json'])['scenarios']
    require(len(scenarios) == 15 and len({s['id'] for s in scenarios}) == 15, 'fifteen unique native scenario definitions required')
    require({s['app'] for s in scenarios if 'app' in s} == set(APP_IDS), 'scenario app coverage incomplete')
    require(all(s['status'] == 'not_run' and len(s['required_evidence']) >= 5 for s in scenarios),
            'scenario definitions are not execution evidence')
    checks.append('native-scenarios-remain-unexecuted-definitions')
    workflow = files['.github/workflows/ci.yml'].decode('utf-8')
    uses = re.findall(r'uses:\s*(\S+)', workflow)
    require(len(uses) == 4 and all(re.fullmatch(r'actions/[a-z-]+@[0-9a-f]{40}', x) for x in uses),
            'CI actions must be full-commit pinned')
    require('contents: read' in workflow and 'persist-credentials: false' in workflow,
            'CI must retain read-only repository authority')
    require('pull_request_target' not in workflow and 'write-all' not in workflow and 'secrets.' not in workflow,
            'CI must not acquire publishing/secrets authority')
    checks.append('ci-policy-subset-pinned-read-only-no-secrets')
    source_links = local_links(files)
    generated = render()
    plugin_links = local_links(generated)
    require(not any(n.startswith(('tests/', 'scripts/')) for n in generated), 'developer tests/tools must not enter plugin')
    require('storytold_tools/build.py' not in generated, 'maintenance builder is source-only')
    require('LICENSE' in names and 'LICENSE' in generated, 'LICENSE must ship in source and plugin')
    checks.append('license-file-in-source-and-plugin')
    for name in ('plugin.json', '.claude-plugin/plugin.json'):
        value = parse_json(generated[name])
        require(value['name'] == p['name'] and value['version'] == p['version'] and value['license'] == p['license'],
                'manifest identity/version/license drift')
        require('mcpServers' not in value and 'mcp' not in value, 'no active native registration in default manifest')
        checks.append('generated-manifest:' + name)
    # Root plugin.json's com.openai extension replaces the .codex-plugin compatibility overlay.
    require(not any(n.startswith('.codex-plugin/') for n in generated), 'legacy .codex-plugin overlay must not ship')
    interface = parse_json(generated['plugin.json'])['extensions']['com.openai']['interface']
    require(interface['displayName'] == 'Storytold' and interface['developerName'] == 'devsolux',
            'OpenAI interface metadata missing from root plugin.json')
    checks.append('openai-extension-in-portable-manifest')
    checks += ['packaged-runtime-boundary', 'source-local-links', 'plugin-local-links']
    return {'schema_version': 1, 'status': 'passed', 'checks_passed': len(checks),
            'checks': checks, 'parsed_files': parsed_counts, 'canonical_files': len(files),
            'plugin_files': len(generated), 'local_links_checked': len(source_links) + len(plugin_links),
            'native_scenario_definitions': len(scenarios), 'native_scenarios_executed': 0,
            'remote_schema_validation': False, 'full_ci_yaml_validation': False}


def main() -> int:
    try:
        sys.stdout.buffer.write(encoded(check()))
        return 0
    except (OSError, ValueError, TypeError, KeyError, SyntaxError) as exc:
        print('storytold check: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
