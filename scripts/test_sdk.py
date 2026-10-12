"""Explicit optional-SDK integration test. Only starts the synthetic test peer."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import importlib.metadata
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from storytold_tools.common import ROOT, StorytoldError, digest, encoded, require, snapshot
from storytold_tools.probe import SDK_VERSION, probe


async def exercise() -> list[str]:
    checks = []
    with tempfile.TemporaryDirectory(prefix='storytold-sdk-') as td:
        work = Path(td).resolve()
        executable = Path(sys.executable).resolve()
        fixture = ROOT / 'tests/fixtures/mcp_stdio_fixture.py'
        launch = {'app': 'synthetic-sdk-fixture', 'command': str(executable),
                  'args': [str(fixture), '--synthetic-sdk-fixture'],
                  'working_directory': str(work), 'binary_sha256': snapshot(executable)[0],
                  'source_revision': 'synthetic-fixture-not-a-Craft-commit',
                  'platform': {'system': 'synthetic-test', 'machine': 'synthetic-test'}}
        launch['fingerprint'] = digest(encoded(launch))
        discovery = await probe(launch, timeout=15)
        discovery['probe_origin'] = 'synthetic_sdk_fixture'
        require(discovery['status'] == 'discovery_passed', 'SDK discovery failed: ' + str(discovery.get('error')))
        require(len(discovery['tools']) == 2, 'SDK pagination contract failed')
        require(discovery['server_info']['name'] == 'storytold-synthetic-sdk-fixture', 'SDK identity alias failed')
        checks += ['official-sdk-initialize', 'two-page-tools-list', 'server-model-wire-aliases']
        success = await probe(launch, timeout=15, call={'name': 'inspect_fixture', 'arguments': {}})
        success['probe_origin'] = 'synthetic_sdk_fixture'
        require(success['status'] == 'discovery_and_call_passed', 'SDK tool call failed: ' + str(success.get('error')))
        content = success['call']['result']
        require(content['structuredContent'] == {'count': 3, 'ok': True, 'missing': None}, 'SDK typed result changed')
        require(content['isError'] is False, 'SDK isError alias contract changed')
        require(success['checks']['sdk_context_exit'] is True, 'SDK context cleanup failed')
        checks += ['typed-structured-content', 'isError-wire-alias', 'sdk-context-exit']
        failure = await probe(launch, timeout=15, call={'name': 'fail_fixture', 'arguments': {}})
        failure['probe_origin'] = 'synthetic_sdk_fixture'
        require(failure['status'] == 'tool_error' and failure['retry_safe'] is False, 'native error was hidden/retried')
        checks.append('native-tool-error-not-success')
    return checks


def main() -> int:
    base = {'schema_version': 1, 'scope': 'official_sdk_synthetic_stdio_fixture',
            'captured_at': datetime.now(timezone.utc).isoformat(), 'required_sdk': SDK_VERSION,
            'native_craft_apps_executed': False, 'native_acceptance_gates_passed': []}
    try:
        try:
            installed = importlib.metadata.version('mcp')
        except importlib.metadata.PackageNotFoundError:
            installed = None
        base['installed_sdk'] = installed
        require(installed == SDK_VERSION,
                'Install the reviewed optional requirements-probe.txt explicitly; missing/wrong SDK is not a passing skip.')
        checks = asyncio.run(exercise())
        base.update({'status': 'passed', 'checks_passed': len(checks), 'checks': checks})
        code = 0
    except Exception as exc:
        base.update({'status': 'blocked' if base.get('installed_sdk') != SDK_VERSION else 'failed',
                     'checks_passed': 0, 'error': {'type': type(exc).__name__, 'message': str(exc)}})
        code = 1
    sys.stdout.buffer.write(encoded(base))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
