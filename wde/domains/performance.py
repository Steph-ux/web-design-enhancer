"""Lab performance heuristics (not field RUM)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def audit_performance(root: Path) -> dict[str, Any]:
    src_paths = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {
        ".js", ".jsx", ".ts", ".tsx", ".css", ".html", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"
    } and not any(x in p.parts for x in (".wde", "node_modules", "dist", ".git"))]
    total = sum(p.stat().st_size for p in src_paths)
    images = [p for p in src_paths if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp"}]
    large_images = [str(p) for p in images if p.stat().st_size > 500_000]
    fonts = [p for p in src_paths if "font" in p.name.lower()]
    return {
        "lab_only": True,
        "tracked_bytes": total,
        "image_count": len(images),
        "large_images_over_500kb": large_images[:10],
        "font_files": len(fonts),
        "budget_js_hint_bytes": 250_000,
        "within_simple_budget": total < 2_000_000 and not large_images,
    }
