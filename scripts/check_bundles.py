"""Strict release policy gate: refuse to verify a manifest whose archives lack Sigstore bundles.

Run by the release workflow before the real `setup` on each OS, so the
cross-platform verification never has to fall back to checksum-only trust.
Offline and read-only: it loads config/releases.json and config/signatures.json
through the same validators `setup` uses.
"""
from __future__ import annotations
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from storytold_tools.common import encoded
from storytold_tools.releases import load_releases, load_signatures, require_complete_bundles


def main() -> int:
    try:
        releases = load_releases()
        bundles = require_complete_bundles(load_signatures(releases=releases), releases)
        sys.stdout.buffer.write(encoded({'status': 'passed', 'bundles': len(bundles), 'apps': len(releases['apps'])}))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print('storytold check-bundles: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
