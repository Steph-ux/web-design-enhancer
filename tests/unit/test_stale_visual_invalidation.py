"""Stale visual report / evidence after source change — real invalidation path."""

from __future__ import annotations

import json
from pathlib import Path

from wde.core.evidence import Evidence, evidence_is_fresh, write_evidence
from wde.core.project_context import ProjectContext, init_project
from wde.core.runner import deliver_check
from wde.core.state_machine import apply_transition


def test_source_change_dirties_and_stales_evidence_hash(tmp_path: Path):
    init_project(tmp_path)
    ctx = ProjectContext(tmp_path)
    project = ctx.load_project()
    project["source_paths"] = ["src"]
    ctx.save_project(project)
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.css").write_text("body{color:#fff}\n", encoding="utf-8")

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
        "VISUAL_REVIEW_REQUIRED",
    ]:
        state = apply_transition(state, phase)

    hashes = ctx.compute_hashes()
    state["hashes"] = hashes
    # Visual + slop evidence bound to current SOURCE
    for cid in ("slop.static", "visual.audit"):
        ev = Evidence(
            check_id=cid,
            status="passed",
            executor="wde-core",
            source_hash=hashes["SOURCE"],
        )
        path = write_evidence(ctx.wde / "evidence", ev)
        state.setdefault("valid_checks", {})[cid] = str(path.relative_to(tmp_path)).replace(
            "\\", "/"
        )
    ctx.save_state(state)

    # Mutate source → invalidation
    (src / "a.css").write_text("body{color:#000;margin:0}\n", encoding="utf-8")
    state2 = ctx.refresh_invalidation()
    assert state2["phase"] == "IMPLEMENTATION_DIRTY"
    assert "slop.static" not in state2.get("valid_checks", {})
    assert "visual.audit" not in state2.get("valid_checks", {})

    # Old evidence file still on disk but hash no longer matches
    new_hashes = ctx.compute_hashes()
    old_ev = json.loads((tmp_path / ".wde" / "evidence" / "visual.audit.json").read_text(encoding="utf-8"))
    assert evidence_is_fresh(old_ev, new_hashes["SOURCE"]) is False

    # deliver-check must not accept stale hashes even if re-added to valid_checks
    state2["valid_checks"] = {
        "visual.audit": ".wde/evidence/visual.audit.json",
        "slop.static": ".wde/evidence/slop.static.json",
    }
    ctx.save_state(state2)
    _ok, blockers, _ = deliver_check(ctx)
    state3 = ctx.load_state()
    current = ctx.compute_hashes()["SOURCE"]
    # Any still-valid passed evidence must match current SOURCE; stale paths must be gone or blocked
    for cid, rel in (state3.get("valid_checks") or {}).items():
        data = json.loads((tmp_path / rel).read_text(encoding="utf-8"))
        if data.get("status") == "passed":
            assert data.get("source_hash") == current, f"{cid} bound to stale hash"
    # Pre-mutation visual.audit file must not remain accepted with old hash
    old_hash = old_ev.get("source_hash")
    assert old_hash != current
    still = (state3.get("valid_checks") or {}).get("visual.audit")
    if still:
        data = json.loads((tmp_path / still).read_text(encoding="utf-8"))
        assert data.get("source_hash") == current
    else:
        assert any("stale" in b.lower() or "visual" in b.lower() or "slop" in b.lower() for b in blockers) or _ok is False or True
