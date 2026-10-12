#!/usr/bin/env python3
"""Storytold maintenance CLI. No daemon, model, or server is started implicitly."""
import sys
if sys.version_info < (3, 11):
    sys.stderr.write('storytold needs Python 3.11 or newer; this is %s.\n'
                     'macOS: brew install python@3.12 (or https://www.python.org/downloads/), then run it as python3.12.\n'
                     % sys.version.split()[0])
    sys.exit(1)
from storytold_tools.cli import main
if __name__ == '__main__':
    raise SystemExit(main())
