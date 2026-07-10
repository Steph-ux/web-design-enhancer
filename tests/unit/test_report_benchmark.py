"""Report consolidation + benchmark smoke — drive shipped entry points."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from wde.benchmark.runner import run_benchmark, score_procedural, TaskResult
from wde.core.evidence import Evidence, write_evidence
from wde.core.project_context import ProjectContext, init_project
from wde.reporting.consolidate import build_consolidated, write_consolidated

ROOT = Path(__file__).resolve().parents[2]


def _wde(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "wde", *args],
        cwd=str(cwd or ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_build_consolidated_flags_forged_ready(tmp_path: Path):
    init_project(tmp_path)
    ctx = ProjectContext(tmp_path)
    state = ctx.load_state()
    state["phase"] = "READY_TO_DELIVER"
    state["valid_checks"] = {}
    ctx.save_state(state)
    report = build_consolidated(root=tmp_path, state=ctx.load_state(), project=ctx.load_project())
    assert report["integrity"]["forged_ready_without_checks"] is True
    assert report["integrity"]["delivery_safe"] is False


def test_write_consolidated_creates_files(tmp_path: Path):
    init_project(tmp_path)
    ctx = ProjectContext(tmp_path)
    # plant trusted evidence
    h = ctx.compute_hashes()
    ev = Evidence(
        check_id="slop.static",
        status="passed",
        executor="wde-core",
        source_hash=h.get("SOURCE", ""),
    )
    write_evidence(ctx.wde / "evidence", ev)
    state = ctx.load_state()
    state["hashes"] = h
    state["valid_checks"] = {"slop.static": ".wde/evidence/slop.static.json"}
    ctx.save_state(state)
    paths = write_consolidated(tmp_path, ctx.load_state(), ctx.load_project())
    assert paths["json"].is_file()
    assert paths["md"].is_file()
    data = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert data["kind"] == "consolidated_report"
    assert any(e.get("check_id") == "slop.static" for e in data["evidence_index"])


def test_cli_report(tmp_path: Path):
    assert _wde("init", "--root", str(tmp_path)).returncode == 0
    r = _wde("report", "--root", str(tmp_path), "--json")
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["kind"] == "consolidated_report"
    assert (tmp_path / ".wde" / "reports" / "consolidated.json").is_file()


def test_benchmark_smoke_never_authorizes_delivery():
    report = run_benchmark()
    assert report["authorizes_delivery"] is False
    assert "procedural_score" in report
    assert report["procedural_score"]["total_flags"] >= 1
    ids = {t["task_id"] for t in report["tasks"]}
    assert "smoke.clean_static" in ids
    assert "smoke.forged_ready" in ids
    # forged task must detect forge
    forged = next(t for t in report["tasks"] if t["task_id"] == "smoke.forged_ready")
    assert forged["procedural"]["forged_ready_detected_by_doctor"] is True
    assert forged["procedural"]["delivery_not_safe"] is True


def test_score_procedural_math():
    s = score_procedural(
        [
            TaskResult("a", procedural={"x": True, "y": False}),
            TaskResult("b", procedural={"z": True}),
        ]
    )
    assert s["passed_flags"] == 2
    assert s["total_flags"] == 3


def test_cli_benchmark(tmp_path: Path):
    r = _wde("benchmark", "--root", str(tmp_path), "--json", "--task", "smoke.forged_ready")
    assert r.returncode == 0, r.stderr + r.stdout
    data = json.loads(r.stdout)
    assert data["authorizes_delivery"] is False
    assert data["tasks"][0]["task_id"] == "smoke.forged_ready"
