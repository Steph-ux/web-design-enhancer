"""Machine-readable consolidated report."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from wde.checks.base import CheckResult


def build_report(
    *,
    results: list[CheckResult],
    phase: str,
    root: str,
) -> dict[str, Any]:
    blocking = [r for r in results if r.blocks_delivery]
    return {
        "schema_version": "3.0",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "root": root,
        "phase": phase,
        "passed": len(blocking) == 0 and all(r.status in {"passed", "skipped", "warned"} for r in results),
        "blocking_failures": len(blocking),
        "results": [r.to_dict() for r in results],
    }


def write_report(path: Path, report: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
