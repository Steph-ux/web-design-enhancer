"""Project maintainability heuristics."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def audit_maintainability(root: Path) -> dict[str, Any]:
    code_files = [
        p
        for p in root.rglob("*")
        if p.is_file()
        and p.suffix.lower() in {".js", ".jsx", ".ts", ".tsx", ".css", ".html", ".vue", ".svelte"}
        and not any(x in p.parts for x in (".wde", "node_modules", "dist", ".git"))
    ]
    large = []
    for p in code_files:
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").count("\n") + 1
        except OSError:
            continue
        if lines > 800:
            large.append({"path": str(p.as_posix()), "lines": lines})
    css_files = [p for p in code_files if p.suffix.lower() == ".css"]
    magic_hex = 0
    for p in css_files:
        text = p.read_text(encoding="utf-8", errors="replace")
        magic_hex += text.count("#")
    return {
        "code_files": len(code_files),
        "large_files_over_800_lines": large[:20],
        "css_hash_mentions": magic_hex,
        "uses_css_variables": any(
            ":root" in p.read_text(encoding="utf-8", errors="replace") or "--" in p.read_text(encoding="utf-8", errors="replace")
            for p in css_files[:20]
        ) if css_files else False,
    }
