"""
tests/test_check_visual_gate.py
Phase 4 is now non-bypassable: check.py --final cannot reach DELIVERY
AUTHORIZED without (a) a fresh visual_audit report with a clean rendered DOM
and (b) a passing aesthetic (vision) verdict. These tests exercise
evaluate_visual_gate() directly.
"""
import importlib.util
import json
import time
from pathlib import Path

_CHECK = Path(__file__).parent.parent / "scripts" / "check.py"


def _load():
    spec = importlib.util.spec_from_file_location("check_mod", _CHECK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _clean_report(audit_dir, breakpoints=2):
    audit_dir.mkdir(parents=True, exist_ok=True)
    (audit_dir / "audit_report.json").write_text(json.dumps({
        "screenshots": {f"bp{i}": f"{i}.png" for i in range(breakpoints)},
        "ai_slop_detected": [],
        "a_group_slop": [],
        "spacing_errors": [],
    }))


def _passing_verdict(audit_dir):
    (audit_dir / "aesthetic-verdict.json").write_text(json.dumps({
        "overall_score": 88,
        "verdict": "Confident, restrained, clearly human-designed.",
        "reads_as": "human",
        # Delivery now requires INDEPENDENT/human provenance and a named signature idea.
        "reviewer": "independent",
        "memorable_idea": "Oversized off-white serif headline anchored to a single acid-green rule.",
        "dimensions": {k: {"score": 85, "note": "ok"} for k in [
            "first_impression", "typography", "colour", "spacing",
            "hierarchy", "polish", "human_signal"]},
        "top_fixes": ["Balance the empty right half of the hero", "Give project cards a signature accent"],
    }))


def test_both_artifacts_missing_blocks(tmp_path):
    mod = _load()
    errors, _, _ = mod.evaluate_visual_gate(audit_output=str(tmp_path / "audit-results"))
    assert len(errors) == 2
    assert any("visual audit missing" in e.lower() for e in errors)
    assert any("aesthetic vision review missing" in e.lower() for e in errors)


def test_clean_report_without_verdict_still_blocks(tmp_path):
    mod = _load()
    aud = tmp_path / "audit-results"
    _clean_report(aud)
    errors, _, infos = mod.evaluate_visual_gate(audit_output=str(aud))
    assert any("aesthetic" in e.lower() for e in errors)
    assert not any("visual audit missing" in e.lower() for e in errors)
    assert any("rendered dom clean" in i.lower() for i in infos)


def test_rendered_slop_blocks(tmp_path):
    mod = _load()
    aud = tmp_path / "audit-results"
    aud.mkdir(parents=True)
    (aud / "audit_report.json").write_text(json.dumps({
        "screenshots": {}, "ai_slop_detected": [{"sel": ".x"}],
        "a_group_slop": [], "spacing_errors": [3, 5],
    }))
    errors, warnings, _ = mod.evaluate_visual_gate(audit_output=str(aud))
    assert any("rendered dom" in e.lower() for e in errors)
    assert any("8px grid" in w for w in warnings)


def test_stale_report_blocks(tmp_path):
    mod = _load()
    aud = tmp_path / "audit-results"
    src = tmp_path / "src"
    src.mkdir()
    _clean_report(aud)
    time.sleep(1.2)
    (src / "index.html").write_text("<html></html>")
    errors, _, _ = mod.evaluate_visual_gate(audit_output=str(aud), code_path=str(src))
    assert any("stale" in e.lower() for e in errors)


def test_clean_report_and_passing_verdict_passes(tmp_path):
    mod = _load()
    aud = tmp_path / "audit-results"
    _clean_report(aud)
    _passing_verdict(aud)
    errors, _, _ = mod.evaluate_visual_gate(audit_output=str(aud))
    assert errors == []


# --- Provenance + signature enforcement (hardening: self-review can't deliver) ---

def _verdict(audit_dir, **overrides):
    base = {
        "overall_score": 88,
        "verdict": "Confident, restrained, clearly human-designed.",
        "reads_as": "human",
        "reviewer": "independent",
        "memorable_idea": "Oversized off-white serif headline anchored to a single acid-green rule.",
        "dimensions": {k: {"score": 85, "note": "ok"} for k in [
            "first_impression", "typography", "colour", "spacing",
            "hierarchy", "polish", "human_signal"]},
        "top_fixes": ["Balance the hero", "Give cards a signature accent"],
    }
    base.update(overrides)
    (audit_dir / "aesthetic-verdict.json").write_text(json.dumps(base))


def test_self_review_cannot_authorize_delivery(tmp_path):
    mod = _load()
    aud = tmp_path / "audit-results"
    _clean_report(aud)
    _verdict(aud, reviewer="self")
    errors, _, _ = mod.evaluate_visual_gate(audit_output=str(aud))
    assert any("PROVENANCE" in e for e in errors)


def test_missing_reviewer_field_blocks(tmp_path):
    mod = _load()
    aud = tmp_path / "audit-results"
    _clean_report(aud)
    v = {
        "overall_score": 90, "verdict": "x", "reads_as": "human",
        "memorable_idea": "A real owned idea worth naming here.",
        "dimensions": {k: {"score": 88, "note": "ok"} for k in [
            "first_impression", "typography", "colour", "spacing",
            "hierarchy", "polish", "human_signal"]},
        "top_fixes": ["a", "b"],
    }
    (aud / "aesthetic-verdict.json").write_text(json.dumps(v))
    errors, _, _ = mod.evaluate_visual_gate(audit_output=str(aud))
    assert any("PROVENANCE" in e for e in errors)


def test_no_memorable_idea_blocks(tmp_path):
    mod = _load()
    aud = tmp_path / "audit-results"
    _clean_report(aud)
    _verdict(aud, memorable_idea=None)
    errors, _, _ = mod.evaluate_visual_gate(audit_output=str(aud))
    assert any("NO SIGNATURE" in e for e in errors)


def test_reads_as_ai_blocks(tmp_path):
    mod = _load()
    aud = tmp_path / "audit-results"
    _clean_report(aud)
    _verdict(aud, reads_as="ai")
    errors, _, _ = mod.evaluate_visual_gate(audit_output=str(aud))
    assert any("READS AS AI" in e for e in errors)


def test_independent_with_signature_passes(tmp_path):
    mod = _load()
    aud = tmp_path / "audit-results"
    _clean_report(aud)
    _verdict(aud)  # independent + named idea + reads_as human + score 88
    errors, _, _ = mod.evaluate_visual_gate(audit_output=str(aud))
    assert errors == []
