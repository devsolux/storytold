"""Discover all core unittest suites in an isolated canonical source copy."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from storytold_tools.build import disposable, source_map
from storytold_tools.common import ROOT, create_new, encoded, load_json, require


def worker(result_path: Path) -> int:
    started = time.monotonic()
    tests = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern='test_*.py', top_level_dir=str(ROOT))
    count = tests.countTestCases()
    require(count > 0, 'test discovery found no tests')
    result = unittest.TextTestRunner(verbosity=2, stream=sys.stderr).run(tests)
    report = {
        'schema_version': 1,
        'scope': 'isolated_offline_core',
        'origin': 'executed_unittest_with_synthetic_fixtures',
        'captured_at': datetime.now(timezone.utc).isoformat(),
        'python': sys.version.split()[0],
        'tests_run': result.testsRun,
        'discovered': count,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'skips': len(result.skipped),
        'expected_failures': len(result.expectedFailures),
        'unexpected_successes': len(result.unexpectedSuccesses),
        'seconds': round(time.monotonic() - started, 3),
        'status': 'passed' if result.wasSuccessful() and result.testsRun == count else 'failed',
        'failed_tests': [str(test) for test, _ in result.failures + result.errors],
        'skipped_tests': [{'test': str(test), 'reason': reason} for test, reason in result.skipped],
        'native_apps_executed': False,
        'official_sdk_executed': False,
        'host_installation_executed': False,
        'network_required': False,
    }
    create_new(result_path, encoded(report))
    return 0 if report['status'] == 'passed' else 1


def run() -> int:
    run_id = uuid.uuid4().hex
    output = disposable(ROOT, '.build')
    with tempfile.TemporaryDirectory(prefix='storytold-core-') as td:
        temporary = Path(td).resolve()
        source = temporary / 'source'
        source.mkdir()
        for name, data in source_map().items():
            target = source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        home = temporary / 'home'
        home.mkdir()
        env = os.environ.copy()
        for key in list(env):
            # Host config locations too: tests must never read or write the operator's real Claude Code or Codex settings.
            if key.startswith(('CRAFT_', 'STORYTOLD_')) or key in {'CLAUDE_CONFIG_DIR', 'CODEX_HOME'}:
                env.pop(key, None)
        env.update({'HOME': str(home), 'USERPROFILE': str(home),
                    'XDG_CONFIG_HOME': str(home / '.config'), 'XDG_CACHE_HOME': str(home / '.cache'),
                    'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONPATH': str(source)})
        result_path = temporary / 'results.json'
        command = [sys.executable, str(source / 'scripts/test.py'), '--worker', str(result_path)]
        try:
            process = subprocess.run(command, cwd=source, env=env, capture_output=True,
                                     timeout=180, check=False)
        except subprocess.TimeoutExpired as exc:
            log = (exc.stdout or b'') + (exc.stderr or b'')
            create_new(output / ('tests-' + run_id + '.log'), log)
            sys.stderr.write('storytold tests: timed out; no successful test report\n')
            return 1
        create_new(output / ('tests-' + run_id + '.log'), process.stdout + process.stderr)
        sys.stderr.buffer.write(process.stderr)
        if not result_path.is_file():
            sys.stderr.write('storytold tests: worker produced no result; suite/import failure\n')
            return 1
        report = load_json(result_path)
        create_new(output / ('tests-' + run_id + '.json'), encoded(report))
        sys.stdout.buffer.write(encoded(report))
        return 0 if process.returncode == 0 and report['status'] == 'passed' else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        return worker(args.worker) if args.worker else run()
    except (OSError, ValueError, TypeError, KeyError) as exc:
        sys.stderr.write('storytold tests: ' + str(exc) + '\n')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
