"""Localization resilience — static heuristics."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def audit_i18n(root: Path) -> dict[str, Any]:
    html_files = [p for p in root.rglob("*.html") if ".wde" not in p.parts and "node_modules" not in p.parts]
    lang_ok = False
    dir_attrs = 0
    fragile = 0
    for p in html_files:
        text = p.read_text(encoding="utf-8", errors="replace")
        if re.search(r"<html[^>]+lang\s*=", text, re.I):
            lang_ok = True
        dir_attrs += len(re.findall(r"\bdir\s*=\s*[\"'](ltr|rtl)[\"']", text, re.I))
        # fragile concat patterns in templates
        fragile += len(re.findall(r"""['"]\s*\+\s*\w+\s*\+\s*['"]""", text))
    return {
        "lang_ok": lang_ok or not html_files,
        "dir_attrs": dir_attrs,
        "fragile_concat": fragile,
        "rtl_ready_hint": dir_attrs > 0,
    }
