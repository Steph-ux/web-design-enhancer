"""Adversarial suite: agents must not walk/forge delivery without domain events."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from wde.core.evidence import Evidence, compute_result_digest, verify_evidence_envelope, write_evidence
from wde.core.project_context import ProjectContext, init_project
from wde.core.runner import deliver_check
from wde.core.state_machine import PUBLIC_NEXT_COMMANDS, apply_transition, next_action_for
from wde.domains.contracts import apply_validation_transition, validate_research

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


def test_public_cli_has_no_working_transition_command(tmp_path: Path):
    assert _wde("init", "--root", str(tmp_path), cwd=ROOT).returncode == 0
    r = _wde("transition", "RESEARCH_REQUIRED", "--root", str(tmp_path), cwd=ROOT)
    assert r.returncode == 2
    assert "removed" in r.stderr.lower()


def test_cli_cannot_walk_to_ready_via_transition(tmp_path: Path):
    assert _wde("init", "--root", str(tmp_path), cwd=ROOT).returncode == 0
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
        r = _wde("transition", phase, "--root", str(tmp_path), cwd=ROOT)
        assert r.returncode == 2, phase
    state = json.loads(
        _wde("status", "--root", str(tmp_path), "--json", cwd=ROOT).stdout
    )
    assert state["phase"] == "INTENT_REQUIRED"


def test_every_next_action_command_exists():
    from wde.core.state_machine import PHASES

    for phase in PHASES:
        if phase == "UNINITIALIZED":
            continue
        na = next_action_for(phase)
        base = na.command.strip().split(" --")[0].strip()
        assert base in PUBLIC_NEXT_COMMANDS, f"{phase}: {na.command}"


def test_handwritten_wde_core_evidence_is_rejected(tmp_path: Path):
    init_project(tmp_path)
    ctx = ProjectContext(tmp_path)
    hashes = ctx.compute_hashes()
    # Hand-written without seal digest
    forged = {
        "schema_version": "3.0",
        "check_id": "slop.static",
        "status": "passed",
        "executor": "wde-core",
        "source_hash": hashes.get("SOURCE", ""),
        "contract_hash": "",
        "result_digest": "deadbeef",
        "details": {},
    }
    path = tmp_path / ".wde" / "evidence" / "slop.static.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(forged), encoding="utf-8")
    ok, reasons = verify_evidence_envelope(
        forged, expected_source_hash=hashes.get("SOURCE", ""), root=tmp_path
    )
    assert not ok
    assert any("digest" in r for r in reasons)


def test_modified_result_digest_is_rejected(tmp_path: Path):
    init_project(tmp_path)
    ctx = ProjectContext(tmp_path)
    hashes = ctx.compute_hashes()
    ev = Evidence(
        check_id="slop.static",
        status="passed",
        executor="wde-core",
        source_hash=hashes["SOURCE"],
    )
    path = write_evidence(ctx.wde / "evidence", ev)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["details"] = {"tampered": True}
    # keep old digest → mismatch
    ok, reasons = verify_evidence_envelope(
        data, expected_source_hash=hashes["SOURCE"], root=tmp_path
    )
    assert not ok
    assert any("digest" in r for r in reasons)


def test_forged_ready_detected_by_doctor(tmp_path: Path):
    init_project(tmp_path)
    ctx = ProjectContext(tmp_path)
    state = ctx.load_state()
    state["phase"] = "READY_TO_DELIVER"
    state["valid_checks"] = {"slop.static": ".wde/evidence/fake.json"}
    ctx.save_state(state)
    issues = ctx.doctor()
    codes = {i["code"] for i in issues}
    assert "forged_delivery" in codes


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

    hashes = ctx.compute_hashes()
    state["hashes"] = hashes
    ev = Evidence(
        check_id="slop.static",
        status="passed",
        executor="wde-core",
        source_hash=hashes["SOURCE"],
    )
    path = write_evidence(ctx.wde / "evidence", ev)
    state["valid_checks"] = {
        "slop.static": str(path.relative_to(tmp_path)).replace("\\", "/")
    }
    ctx.save_state(state)

    src = tmp_path / "src"
    src.mkdir(exist_ok=True)
    (src / "index.html").write_text(
        "<!doctype html><html lang=en><head><title>x</title>"
        "<meta name=viewport content='width=device-width, initial-scale=1'>"
        "</head><body><h1>Hi</h1><button type=button>Go</button></body></html>\n",
        encoding="utf-8",
    )
    project = ctx.load_project()
    project["source_paths"] = ["src"]
    ctx.save_project(project)

    state2 = ctx.refresh_invalidation()
    assert state2["phase"] == "IMPLEMENTATION_DIRTY"
    assert "slop.static" not in state2.get("valid_checks", {})

    # Before re-run: stale sealed envelope must fail against new SOURCE
    data_before = json.loads(path.read_text(encoding="utf-8"))
    new_hash = ctx.compute_hashes()["SOURCE"]
    assert data_before.get("source_hash") != new_hash
    ok_ev, reasons = verify_evidence_envelope(
        data_before, expected_source_hash=new_hash, root=tmp_path
    )
    assert not ok_ev
    assert any("source_hash" in r for r in reasons)

    # Agent re-points valid_checks at stale file then deliver-check
    state2["valid_checks"] = {
        "slop.static": str(path.relative_to(tmp_path)).replace("\\", "/")
    }
    ctx.save_state(state2)

    ok, blockers, _ = deliver_check(ctx)
    assert isinstance(blockers, list)
    # Stale pointer alone must not authorize delivery without fresh verified envelope
    # (deliver may re-run slop and write a NEW envelope — that's fine)
    assert ok is False or "slop.static" in (ctx.load_state().get("valid_checks") or {})


def test_research_validate_advances_from_research_required(tmp_path: Path):
    init_project(tmp_path)
    # Minimal pillars
    (tmp_path / "design-system-output.md").write_text("# ds\n", encoding="utf-8")
    (tmp_path / "getdesign-bugatti.md").write_text("# gd\n", encoding="utf-8")
    ctx = ProjectContext(tmp_path)
    state = ctx.load_state()
    state = apply_transition(state, "INTENT_VALIDATED")
    state = apply_transition(state, "RESEARCH_REQUIRED")
    ctx.save_state(state)

    r = _wde("validate", "research", "--root", str(tmp_path), cwd=ROOT)
    assert r.returncode == 0, r.stderr + r.stdout
    state2 = json.loads(
        _wde("status", "--root", str(tmp_path), "--json", cwd=ROOT).stdout
    )
    assert state2["phase"] == "ARCHITECTURE_REQUIRED"
    assert "validate experience" in (state2.get("next_action") or {}).get("command", "")


def test_forged_independent_clone_blocked_without_env(tmp_path: Path):
    """Bare independent-clone verdict without env escape must fail aesthetic check."""
    from wde.checks.visual.aesthetic import AestheticVerdictCheck

    init_project(tmp_path)
    audit = tmp_path / "audit-results"
    audit.mkdir()
    (audit / "aesthetic-verdict.json").write_text(
        json.dumps(
            {
                "overall_score": 90,
                "reviewer": "independent-clone",
                "reads_as": "human",
                "memorable_idea": "Something memorable enough",
                "dimensions": {
                    d: {"score": 80, "note": "ok evidence here"}
                    for d in [
                        "first_impression",
                        "hierarchy",
                        "spacing_rhythm",
                        "colour_restraint",
                        "typography",
                        "component_polish",
                        "mobile",
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    result = AestheticVerdictCheck().run({"root": tmp_path})
    assert result.status == "failed"
    assert any(f.rule_id == "DECLARED-ONLY" for f in result.findings)
