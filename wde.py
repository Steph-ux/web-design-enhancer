#!/usr/bin/env python3
"""Repo-root launcher so `python wde.py …` works without PATH setup.

Preferred after install: `wde …`  (console_scripts)
Fallback anywhere:      `python -m wde …`
"""

from __future__ import annotations

from wde.cli.main import main

if __name__ == "__main__":
    raise SystemExit(main())
