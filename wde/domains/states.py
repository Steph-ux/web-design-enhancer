"""Interaction state coverage — static markers."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def audit_interaction_states(root: Path) -> dict[str, Any]:
    texts: list[str] = []
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in {".html", ".jsx", ".tsx", ".vue", ".svelte"}:
            continue
        if any(x in p.parts for x in (".wde", "node_modules", ".git")):
            continue
        texts.append(p.read_text(encoding="utf-8", errors="replace"))
    blob = "\n".join(texts).lower()
    return {
        "has_empty": bool(re.search(r"data-state\s*=\s*[\"']empty[\"']|empty state|no items|nothing here", blob)),
        "has_error": bool(re.search(r"data-state\s*=\s*[\"']error[\"']|could not|try again|retry|error", blob)),
        "has_loading": bool(re.search(r"data-state\s*=\s*[\"']loading[\"']|loading|spinner|aria-busy", blob)),
        "has_success": bool(re.search(r"data-state\s*=\s*[\"']success[\"']|success|saved|done", blob)),
    }
