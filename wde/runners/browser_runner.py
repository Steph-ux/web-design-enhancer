"""Browser-side helpers: URL probe + V2 visual_audit invocation."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from wde.runners.subprocess_runner import run_python_script


@dataclass
class UrlProbe:
    ok: bool
    status: int | None
    error: str = ""


def probe_url(url: str, timeout: float = 5.0) -> UrlProbe:
    try:
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "wde-v3"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return UrlProbe(ok=200 <= resp.status < 400, status=resp.status)
    except urllib.error.HTTPError as e:
        return UrlProbe(ok=False, status=e.code, error=str(e))
    except Exception as e:  # noqa: BLE001 — surface any network failure
        return UrlProbe(ok=False, status=None, error=str(e))


def run_visual_audit(
    *,
    root: Path,
    url: str,
    output: Path,
) -> dict[str, Any]:
    """Run scripts/visual_audit.py; return structured summary."""
    output.mkdir(parents=True, exist_ok=True)
    res = run_python_script(
        "visual_audit.py",
        ["--url", url, "--output", str(output)],
        cwd=root,
        timeout=300,
    )
    report_path = output / "audit_report.json"
    report: dict[str, Any] = {}
    if report_path.is_file():
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            report = {}
    return {
        "returncode": res.returncode,
        "stdout": res.stdout[-2000:] if res.stdout else "",
        "stderr": res.stderr[-1000:] if res.stderr else "",
        "report_path": str(report_path) if report_path.is_file() else "",
        "report": report,
        "ok": res.returncode == 0 and report_path.is_file(),
    }
