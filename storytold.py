#!/usr/bin/env python3
"""Storytold maintenance CLI. No daemon, model, or server is started implicitly."""
from storytold_tools.cli import main
if __name__ == '__main__':
    raise SystemExit(main())
