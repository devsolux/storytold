"""TEST ONLY: synthetic line-oriented peer for the optional official SDK test.

Not a production MCP server, proxy, app adapter or integration entrypoint.
Not included in the plugin. No files, sockets, shells or application engines.
"""
from __future__ import annotations
import json
import sys

# Tool definitions in the shape of the MCP 2026-07-28 `Tool` type. initialize stays below
# because the probe drives the SDK's legacy mode: the Craft apps speak that handshake, which
# 2026-07-28 replaced with server/discover, and 2025-11-25 is its last protocol version.
NO_ARGUMENTS = {'type': 'object', 'additionalProperties': False}
READ_ONLY = {'readOnlyHint': True, 'destructiveHint': False, 'idempotentHint': True, 'openWorldHint': False}
INSPECT_TOOL = {'name': 'inspect_fixture', 'title': 'Inspect fixture', 'description': 'Return synthetic typed values.',
                'inputSchema': NO_ARGUMENTS,
                'outputSchema': {'type': 'object', 'additionalProperties': False, 'required': ['count', 'ok', 'missing'],
                                 'properties': {'count': {'type': 'integer'}, 'ok': {'type': 'boolean'}, 'missing': {'type': 'null'}}},
                'annotations': READ_ONLY}
FAIL_TOOL = {'name': 'fail_fixture', 'title': 'Fail fixture', 'description': 'Return a synthetic native tool error.',
             'inputSchema': NO_ARGUMENTS, 'annotations': READ_ONLY}
LIST_CACHE = {'ttlMs': 0, 'cacheScope': 'private'}  # CacheableResult, required on tools/list since 2026-07-28


def main() -> int:
    if sys.argv[1:] != ['--synthetic-sdk-fixture']:
        print('Test fixture requires its explicit test-only flag.', file=sys.stderr)
        return 2
    print('Synthetic SDK fixture; not a Craft binary.', file=sys.stderr)
    for line in sys.stdin.buffer:
        if len(line) > 65536:
            return 2
        request = json.loads(line)
        if 'id' not in request:
            continue
        method = request.get('method')
        params = request.get('params', {})
        reply = {'jsonrpc': '2.0', 'id': request['id']}
        if method == 'initialize':
            reply['result'] = {'protocolVersion': '2025-11-25', 'capabilities': {'tools': {}},
                               'serverInfo': {'name': 'storytold-synthetic-sdk-fixture', 'version': '0.0.0-test'}}
        elif method == 'tools/list':
            if params.get('cursor') is None:
                reply['result'] = {'tools': [INSPECT_TOOL], 'nextCursor': 'second-page', **LIST_CACHE}
            elif params['cursor'] == 'second-page':
                reply['result'] = {'tools': [FAIL_TOOL], **LIST_CACHE}
            else:
                reply['error'] = {'code': -32602, 'message': 'Unknown synthetic cursor'}
        elif method == 'tools/call':
            name = params.get('name')
            if name == 'inspect_fixture':
                reply['result'] = {'isError': False,
                                   'content': [{'type': 'text', 'text': '{"count":3,"ok":true,"missing":null}'}],
                                   'structuredContent': {'count': 3, 'ok': True, 'missing': None}}
            else:
                reply['result'] = {'isError': True, 'content': [{'type': 'text', 'text': 'Synthetic tool failure'}]}
        elif method == 'ping':
            reply['result'] = {}
        else:
            reply['error'] = {'code': -32601, 'message': 'Method not part of the synthetic fixture'}
        sys.stdout.write(json.dumps(reply, separators=(',', ':')) + '\n')
        sys.stdout.flush()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
