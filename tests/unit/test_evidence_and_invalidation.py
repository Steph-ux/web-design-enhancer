"""Evidence writer restrictions + source-hash invalidation."""

import json
from pathlib import Path

import pytest

from wde.core.evidence import ALLOWED_EXECUTORS, Evidence, evidence_is_fresh, write_evidence
from wde.core.invalidation import apply_invalidation, checks_invalidated_by
from wde.core.project_context import ProjectContext, init_project


def test_agent_cannot_seal_passed_evidence():
    ev = Evidence(check_id="fake", status="passed", executor="claude-agent")
    with pytest.raises(PermissionError):
        ev.seal()


def test_wde_core_can_seal_passed():
    ev = Evidence(
        check_id="slop.static",
        status="passed",
        executor="wde-core",
        source_hash="sha256:abc",
    ).seal()
    assert ev.result_digest.startswith("sha256:")
    assert "wde-core" in ALLOWED_EXECUTORS


def test_source_change_invalidates_deliver():
    doomed = checks_invalidated_by(["SOURCE"])
    assert "deliver.final" in doomed
    assert "slop.static" in doomed
    valid = {"slop.static": "x", "intent.brief": "y"}
    kept, inv = apply_invalidation(valid, ["SOURCE"])
    assert "slop.static" in inv
    assert "intent.brief" in kept


def test_refresh_invalidation_dirties_on_source_edit(tmp_path: Path):
    init_project(tmp_path)
    ctx = ProjectContext(tmp_path)
    state = ctx.load_state()
    # Advance to implementation allowed via legal transitions
    from wde.core.state_machine import apply_transition

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
        "VISUAL_REVIEW_REQUIRED",
        "INDEPENDENT_REVIEW_REQUIRED",
        "READY_TO_DELIVER",
    ]:
        state = apply_transition(state, phase)
    # Plant a fake valid check
    state["valid_checks"] = {"slop.static": "evidence/slop.json"}
    state["hashes"] = ctx.compute_hashes()
    ctx.save_state(state)

    # Modify source
    src = tmp_path / "src"
    src.mkdir(exist_ok=True)
    (src / "App.jsx").write_text("export default function App(){return null}\n", encoding="utf-8")

    state2 = ctx.refresh_invalidation()
    assert state2["phase"] == "IMPLEMENTATION_DIRTY"
    assert "slop.static" not in state2.get("valid_checks", {})
    assert "slop.static" in state2.get("invalidated_checks", [])


def test_write_evidence_roundtrip(tmp_path: Path):
    ev = Evidence(
        check_id="demo.check",
        status="passed",
        executor="wde-core",
        source_hash="sha256:1",
    )
    path = write_evidence(tmp_path / "evidence", ev)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert evidence_is_fresh(data, "sha256:1")
    assert not evidence_is_fresh(data, "sha256:other")
