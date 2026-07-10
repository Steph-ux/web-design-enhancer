"""Drive real CLI against in-repo examples/v3-fixture."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "examples" / "v3-fixture"


def _wde(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "wde.cli.main", *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_fixture_exists():
    assert (FIXTURE / "src" / "index.html").is_file()


def test_fixture_cli_sequence_no_silent_ready():
    assert FIXTURE.is_dir(), "examples/v3-fixture missing"
    r = _wde("init", "--root", str(FIXTURE), "--force")
    assert r.returncode == 0, r.stderr

    # point sources at src
    ctx_project = FIXTURE / ".wde" / "project.json"
    data = json.loads(ctx_project.read_text(encoding="utf-8"))
    data["source_paths"] = ["src"]
    ctx_project.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    r = _wde("run", "static", "--root", str(FIXTURE))
    assert r.returncode in (0, 1), r.stderr + r.stdout
    assert (FIXTURE / ".wde" / "reports" / "run-static.json").is_file()

    r = _wde("deliver-check", "--root", str(FIXTURE), "--json")
    assert r.returncode in (0, 1), r.stderr + r.stdout
    deliver = json.loads(r.stdout)
    assert "results" in deliver or "deliver_ok" in deliver

    r = _wde("report", "--root", str(FIXTURE), "--json")
    assert r.returncode == 0, r.stderr
    report = json.loads(r.stdout)
    assert report["kind"] == "consolidated_report"
    assert (FIXTURE / ".wde" / "reports" / "consolidated.json").is_file()

    r = _wde("status", "--root", str(FIXTURE), "--json")
    assert r.returncode == 0, r.stderr
    state = json.loads(r.stdout)
    # Must not silently be READY without independent review evidence
    if state.get("phase") == "READY_TO_DELIVER":
        assert "review.independent" in (state.get("valid_checks") or {})

    # Evidence if any passed must be trusted executor
    ev_dir = FIXTURE / ".wde" / "evidence"
    if ev_dir.is_dir():
        for p in ev_dir.glob("*.json"):
            ev = json.loads(p.read_text(encoding="utf-8"))
            if ev.get("status") == "passed":
                assert ev.get("executor") in {
                    "wde-core",
                    "wde-check",
                    "wde-browser",
                    "wde-v2-bridge",
                }, p
