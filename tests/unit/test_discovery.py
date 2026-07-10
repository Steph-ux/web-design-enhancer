"""Creative Discovery — pure stages + real CLI entry (no reimplementation)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from wde.discovery.critic import select_territory
from wde.discovery.interpret import interpret_request
from wde.discovery.orchestrator import run_discovery
from wde.discovery.receipts import discovery_receipts_satisfy_research, load_receipts
from wde.discovery.territories import generate_territories, territories_are_structurally_divergent
from wde.core.state_machine import PUBLIC_NEXT_COMMANDS, next_action_for

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


def test_interpret_labels_hypotheses_as_assumptions():
    # Fully vague: no sector keyword → all subject fields are assumed creative choices
    vague = interpret_request("Fais-moi un site moderne et premium.")
    assert vague.subject
    assert any(h.confidence == "assumed" for h in vague.hypotheses)
    assumed = next(h for h in vague.hypotheses if h.confidence == "assumed")
    assert "not" in assumed.rationale.lower() or "hypothesis" in assumed.rationale.lower() or "creative" in assumed.rationale.lower()
    # Sector keyword present → inferred is allowed, still labeled
    with_sector = interpret_request("Fais-moi un site moderne pour une agence.")
    assert any(h.confidence in {"assumed", "inferred"} for h in with_sector.hypotheses)
    assert with_sector.search_queries.get("sector")
    assert with_sector.search_queries.get("anti_reference")


def test_three_territories_structurally_divergent():
    interp = interpret_request("agency for independent hotels")
    territories = generate_territories(interp)
    assert len(territories) == 3
    assert territories_are_structurally_divergent(territories)
    # not palette-only: metaphors must differ
    assert len({t.metaphor for t in territories}) == 3
    assert len({t.primary_interaction for t in territories}) == 3


def test_selector_picks_one_no_mashup():
    interp = interpret_request("boutique hotel brand site")
    territories = generate_territories(interp)
    sel = select_territory(territories, interp)
    assert sel.winner_id in {t.id for t in territories}
    assert sel.rejected_mashup is True
    assert len(sel.scores) == 3
    assert "mashup" in sel.rationale.lower() or "Rejected" in sel.rationale


def test_run_discovery_writes_contracts_and_receipts(tmp_path: Path):
    result = run_discovery(
        tmp_path,
        "modern premium website for a hospitality branding agency",
        try_getdesign=False,
    )
    assert result.ok, result.errors
    assert (tmp_path / "CREATIVE-BRIEF.md").is_file()
    assert (tmp_path / "EXPERIENCE-CONTRACT.md").is_file()
    assert (tmp_path / "DESIGN.md").is_file()
    assert (tmp_path / "STRUCTURAL-LOCK.md").is_file()
    assert (tmp_path / ".wde" / "research" / "interpretation.json").is_file()
    assert (tmp_path / ".wde" / "research" / "territories.json").is_file()
    receipts = load_receipts(tmp_path)
    assert len(receipts) >= 2
    assert any(r.get("status") == "success" and r.get("digest") for r in receipts)
    brief = (tmp_path / "CREATIVE-BRIEF.md").read_text(encoding="utf-8")
    assert "provenance" in brief.lower() or "receipt" in brief.lower()
    ok, problems = discovery_receipts_satisfy_research(tmp_path)
    assert ok, problems


def test_discover_cli_entry(tmp_path: Path):
    r = _wde(
        "discover",
        "--root",
        str(tmp_path),
        "--request",
        "a modern premium site for an independent hotel brand agency",
        "--skip-getdesign",
        cwd=ROOT,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    assert "discover: OK" in r.stdout or "OK" in r.stdout
    assert (tmp_path / "CREATIVE-BRIEF.md").is_file()
    # intent + research validators accept discovery output
    r2 = _wde("validate", "intent", "--root", str(tmp_path), cwd=ROOT)
    assert r2.returncode == 0, r2.stderr + r2.stdout
    r3 = _wde("validate", "research", "--root", str(tmp_path), cwd=ROOT)
    assert r3.returncode == 0, r3.stderr + r3.stdout


def test_discovery_contracts_pass_design_experience_lock(tmp_path: Path):
    """Criterion 4: compiled contracts must pass wde validate design/experience/lock."""
    from wde.domains.contracts import (
        validate_design,
        validate_experience,
        validate_lock,
    )

    result = run_discovery(
        tmp_path,
        "modern premium website for a hospitality branding agency",
        try_getdesign=False,
    )
    assert result.ok, result.errors
    # Direct domain validators (same path as CLI)
    exp = validate_experience(tmp_path)
    assert exp.ok, [i.message for i in exp.issues]
    des = validate_design(tmp_path)
    assert des.ok, [i.message for i in des.issues] + [
        # surface validate_design remediation if present
        *( [i.remediation] if i.remediation else [] for i in des.issues )
    ]
    lock = validate_lock(tmp_path)
    assert lock.ok, [i.message for i in lock.issues]
    # CLI entry for design (real shipped path)
    r = _wde("validate", "design", "--root", str(tmp_path), cwd=ROOT)
    assert r.returncode == 0, r.stderr + r.stdout


def test_discover_in_public_next_commands():
    assert "wde discover" in PUBLIC_NEXT_COMMANDS
    na = next_action_for("INTENT_REQUIRED")
    assert na.command == "wde discover"
