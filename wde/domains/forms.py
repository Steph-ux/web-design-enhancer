"""Lightweight forms audit (static HTML)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def audit_forms(root: Path) -> dict[str, Any]:
    html_files = list(root.rglob("*.html")) + list(root.rglob("*.jsx")) + list(root.rglob("*.tsx"))
    forms = 0
    inputs = 0
    labeled = 0
    issues: list[str] = []
    for p in html_files:
        if any(x in p.parts for x in (".wde", "node_modules", ".git")):
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        forms += len(re.findall(r"<form\b", text, re.I))
        for m in re.finditer(r"<input\b([^>]*)>", text, re.I):
            inputs += 1
            attrs = m.group(1)
            id_m = re.search(r'\bid\s*=\s*["\']([^"\']+)["\']', attrs, re.I)
            aria = re.search(r"aria-label\s*=", attrs, re.I)
            if id_m and re.search(rf'<label[^>]+for\s*=\s*["\']{re.escape(id_m.group(1))}["\']', text, re.I):
                labeled += 1
            elif aria:
                labeled += 1
            else:
                issues.append(f"{p.name}: input without label/aria-label")
    return {
        "forms": forms,
        "inputs": inputs,
        "labeled": labeled,
        "labels_ok": inputs == 0 or labeled >= inputs,
        "issues": issues[:20],
    }
