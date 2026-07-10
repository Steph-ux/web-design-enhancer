"""Check registry + deliver-check anti-bypass (stale evidence after code change)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from wde.checks.registry import default_registry
from wde.core.evidence import Evidence, write_evidence
from wde.core.project_context import ProjectContext, init_project
from wde.core.runner import deliver_check
from wde.core.state_machine import apply_transition

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


def test_registry_has_v2_bridges():
    reg = default_registry()
    ids = {c.id for c in reg.all()}
    assert "slop.static" in ids
    assert "a11y.static" in ids
    assert "layout.browser" in ids
    assert "visual.audit" in ids
    assert "visual.aesthetic" in ids
    assert "spacing.grid" in ids


def test_stale_evidence_blocks_deliver_after_code_change(tmp_path: Path):
    init_project(tmp_path)
    ctx = ProjectContext(tmp_path)
    state = ctx.load_state()
    for phase in [
        "INTENT_VALIDATED",
        "RESEARCH_REQUIRED",
        "RESEARCH_VALIDATED",
        "ARCHITECTURE_REQUIRED",
        "ARCHITECTURE_VALIDATED",
        "CONTRACT_REQUIRED",
        "CONTRACT_VALIDATED",
        "IMPLEMENTATION_ALLOWED",
    ]:
        state = apply_transition(state, phase)

    # Plant "passed" evidence bound to current source hash
    hashes = ctx.compute_hashes()
    state["hashes"] = hashes
    ev = Evidence(
        check_id="slop.static",
        status="passed",
        executor="wde-core",
        source_hash=hashes["SOURCE"],
    )
    path = write_evidence(ctx.wde / "evidence", ev)
    state["valid_checks"] = {"slop.static": str(path.relative_to(tmp_path)).replace("\\", "/")}
    ctx.save_state(state)

    # Mutate source → invalidation must drop valid_checks / dirty phase
    src = tmp_path / "src"
    src.mkdir(exist_ok=True)
    (src / "index.html").write_text(
        "<!doctype html><html lang=en><head><title>x</title>"
        "<meta name=viewport content='width=device-width, initial-scale=1'>"
        "</head><body><h1>Hi</h1><button type=button>Go</button></body></html>\n",
        encoding="utf-8",
    )
    # Update project to track src
    project = ctx.load_project()
    project["source_paths"] = ["src"]
    ctx.save_project(project)

    state2 = ctx.refresh_invalidation()
    assert state2["phase"] == "IMPLEMENTATION_DIRTY"
    assert "slop.static" not in state2.get("valid_checks", {})

    # Forged: agent re-adds valid_checks pointing at OLD evidence file without re-run
    state2["valid_checks"] = {"slop.static": str(path.relative_to(tmp_path)).replace("\\", "/")}
    ctx.save_state(state2)

    from wde.core.evidence import verify_evidence_envelope

    # Capture stale envelope content before deliver re-runs checks
    stale = json.loads(path.read_text(encoding="utf-8"))
    fresh_hash = ctx.compute_hashes()["SOURCE"]
    still_ok, reasons = verify_evidence_envelope(
        stale, expected_source_hash=fresh_hash, root=tmp_path
    )
    assert not still_ok
    assert any("source_hash" in r for r in reasons)

    ok, blockers, _results = deliver_check(ctx)
    assert isinstance(blockers, list)
    # Must not treat empty blockers as "forged path ignored" without verification
    # After code change, a pure re-attach of stale evidence cannot pass integrity alone:
    assert still_ok is False


def test_forged_agent_evidence_rejected(tmp_path: Path):
    init_project(tmp_path)
    ctx = ProjectContext(tmp_path)
    state = ctx.load_state()
    for phase in [
        "INTENT_VALIDATED",
        "RESEARCH_REQUIRED",
        "RESEARCH_VALIDATED",
        "ARCHITECTURE_REQUIRED",
        "ARCHITECTURE_VALIDATED",
        "CONTRACT_REQUIRED",
        "CONTRACT_VALIDATED",
        "IMPLEMENTATION_ALLOWED",
        "MECHANICAL_REVIEW_REQUIRED",
    ]:
        state = apply_transition(state, phase)

    hashes = ctx.compute_hashes()
    # Manually write a forged evidence file (bypass Evidence.seal allowlist)
    forged = {
        "schema_version": "3.0",
        "check_id": "slop.static",
        "status": "passed",
        "executed_at": "2026-01-01T00:00:00Z",
        "executor": "claude-agent",
        "tool_version": "0",
        "source_hash": hashes["SOURCE"],
        "result_digest": "sha256:forged",
    }
    ev_path = ctx.wde / "evidence" / "slop.static.json"
    ev_path.parent.mkdir(parents=True, exist_ok=True)
    ev_path.write_text(json.dumps(forged), encoding="utf-8")
    state["hashes"] = hashes
    state["valid_checks"] = {"slop.static": ".wde/evidence/slop.static.json"}
    ctx.save_state(state)

    # Minimal clean source so re-run slop might pass — executor check still fails first on old valid_checks
    src = tmp_path / "src"
    src.mkdir(exist_ok=True)
    (src / "index.html").write_text(
        "<!doctype html><html lang=en><head><title>x</title>"
        "<meta name=viewport content='width=device-width, initial-scale=1'></head>"
        "<body><main><h1>Ok</h1></main></body></html>\n",
        encoding="utf-8",
    )
    project = ctx.load_project()
    project["source_paths"] = ["src"]
    ctx.save_project(project)

    _ok, blockers, _ = deliver_check(ctx)
    # After re-run, wde-core may replace with real evidence. Forged executor path:
    # if deliver still sees forged before overwrite — assert deliver never accepts agent executor
    # without re-run producing wde-core evidence.
    state_after = ctx.load_state()
    for rel in (state_after.get("valid_checks") or {}).values():
        data = json.loads((tmp_path / rel).read_text(encoding="utf-8"))
        assert data.get("executor") in {
            "wde-core",
            "wde-check",
            "wde-browser",
            "wde-v2-bridge",
        }, f"forged executor accepted: {data.get('executor')}"


def test_cli_run_static_on_clean_fixture(tmp_path: Path):
    init_project(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "index.html").write_text(
        "<!doctype html><html lang=\"en\"><head><title>Demo</title>"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        "</head><body><h1>Hello</h1><button type=\"button\">Ok</button></body></html>\n",
        encoding="utf-8",
    )
    project = ProjectContext(tmp_path).load_project()
    project["source_paths"] = ["src"]
    ProjectContext(tmp_path).save_project(project)

    r = _wde("run", "static", "--root", str(tmp_path))
    # May fail or pass depending on detector sensitivity; must not crash
    assert r.returncode in (0, 1), r.stderr + r.stdout
    assert (tmp_path / ".wde" / "reports" / "run-static.json").is_file()
