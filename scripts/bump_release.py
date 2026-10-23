"""Open the next patch release after the daily refresh moved a pin: version and changelog section.

Workflow step, no network. After scripts/refresh_releases.py rewrote
config/releases.json, this moves packaging/project.json to the next patch
version and gives CHANGELOG.md that version's section, headed by the pin
moves from the refresh report; an existing Unreleased section becomes that
section, its entries kept below the pins. The workflow rebuilds the plugin
afterwards so its manifests carry the version, runs the checks, and its merge
job publishes the GitHub release from that section once the pull request is
merged. A release an operator cuts by hand still writes its own summary; this
script serves the workflow's pin releases only.
"""
from __future__ import annotations
import argparse
from datetime import date
from pathlib import Path
import sys
import textwrap

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from storytold_tools.catalog import load_catalog
from storytold_tools.common import ROOT, encoded, parse_json, require

HEAD = '# Changelog\n\n'
UNRELEASED = '## Unreleased\n'
WIDTH = 78


def next_version(version: str) -> str:
    parts = version.split('.')
    require(len(parts) == 3 and all(p.isascii() and p.isdigit() for p in parts), 'unexpected project version ' + version)
    return '.'.join(parts[:2] + [str(int(parts[2]) + 1)])


def pin_moves(report: dict, names: dict[str, str]) -> list[str]:
    """One 'Name old → new' per moved app, by display name; an accepted re-publication under the same version says so."""
    moves = report.get('moves') if isinstance(report, dict) else None
    require(isinstance(moves, dict) and moves, 'the refresh report names no moved pin; nothing to release')
    require(set(moves) <= set(names), 'the refresh report names an unknown app')
    lines = []
    for app in sorted(moves, key=lambda a: names[a]):
        move = moves[app]
        require(isinstance(move, dict) and isinstance(move.get('from'), str) and isinstance(move.get('to'), str), app + ': malformed move')
        lines.append(f"{names[app]} {move['to']} (assets re-published)" if move['from'] == move['to']
                     else f"{names[app]} {move['from']} → {move['to']}")
    return lines


def section(version: str, day: str, moves: list[str], run: str | None) -> str:
    where = f' (run {run})' if run else ''
    summary = (f'Automated release by the daily Craft release refresh{where}: {len(moves)} pin'
               f'{"s" if len(moves) != 1 else ""} moved on {day}. Each moved app needs its card and smoke tool rechecked at the new tag.')
    bullet = textwrap.fill('- Pins moved: ' + ', '.join(moves) + '.', WIDTH, subsequent_indent='  ')
    return f'## {version} — {day}\n\n{textwrap.fill(summary, WIDTH)}\n\n{bullet}\n'


def changelog(text: str, version: str, day: str, moves: list[str], run: str | None) -> tuple[str, str]:
    """The changelog with the new section first; says whether Unreleased entries were kept under it."""
    require(text.startswith(HEAD), 'CHANGELOG.md must start with "# Changelog"')
    require(f'\n## {version} ' not in text, f'CHANGELOG.md already has a {version} section')
    body = text[len(HEAD):]
    new = section(version, day, moves, run)
    if not body.startswith(UNRELEASED):
        require(body.startswith('## '), 'unexpected changelog layout: a section heading must follow the title')
        return HEAD + new + '\n' + body, 'new_section'
    after = body[len(UNRELEASED):]
    cut = after.find('\n## ')
    pending, tail = (after, '') if cut < 0 else (after[:cut], after[cut + 1:])
    pending = pending.strip('\n')
    if not pending:
        return HEAD + new + ('\n' + tail if tail else ''), 'new_section'
    return HEAD + new + pending + '\n' + ('\n' + tail if tail else ''), 'unreleased_entries_kept'


def bump(root: Path, report: dict, names: dict[str, str], day: str, run: str | None) -> dict:
    """Rewrite packaging/project.json and CHANGELOG.md together; a refusal leaves both unchanged."""
    date.fromisoformat(day)
    project_path = root / 'packaging/project.json'
    raw = project_path.read_text(encoding='utf-8')
    current = parse_json(raw.encode('utf-8'))['version']
    require(isinstance(current, str), 'packaging/project.json version must be a string')
    version = next_version(current)
    needle = f'"version": "{current}"'
    require(raw.count(needle) == 1, 'packaging/project.json must name its version exactly once')
    moves = pin_moves(report, names)
    changelog_path = root / 'CHANGELOG.md'
    updated, how = changelog(changelog_path.read_text(encoding='utf-8'), version, day, moves, run)
    project_path.write_text(raw.replace(needle, f'"version": "{version}"', 1), encoding='utf-8')
    changelog_path.write_text(updated, encoding='utf-8')
    return {'previous': current, 'version': version, 'date': day, 'pins': moves, 'changelog': how,
            'note': 'Rebuild the plugin so its manifests carry the version; the merge job publishes the release from this section.'}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description='Bump the patch version and open its changelog section after a pin move.')
    p.add_argument('--report', required=True, type=Path, help='JSON report written by scripts/refresh_releases.py')
    p.add_argument('--date', default=date.today().isoformat(), help='release date, YYYY-MM-DD (default: today)')
    p.add_argument('--run', default=None, help='workflow run id named in the changelog section')
    args = p.parse_args(argv)
    try:
        report = parse_json(args.report.read_bytes())
        names = {app: row['name'] for app, row in load_catalog().items()}
        sys.stdout.buffer.write(encoded(bump(ROOT, report, names, args.date, args.run)))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print('storytold bump-release: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
