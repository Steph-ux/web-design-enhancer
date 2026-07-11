"""P0: territory tokens must compile into DESIGN.md (no dark-first override)."""

from __future__ import annotations

from pathlib import Path

from wde.discovery.compile import compile_design_md
from wde.discovery.interpret import interpret_request
from wde.discovery.orchestrator import run_discovery
from wde.discovery.receipts import receipt_is_valid
from wde.discovery.synthesis import synthesize_research
from wde.discovery.territories import Territory, generate_territories
from wde.discovery.tokens import DesignTokens


def test_light_editorial_territory_does_not_compile_dark_first():
    """Winner with paper ivory tokens must not emit global dark-first DESIGN.md."""
    interp = interpret_request("modern premium website for a hospitality branding agency")
    territories = generate_territories(interp)
    # Force light editorial winner (territory A for hospitality)
    winner = next(t for t in territories if t.id == "A")
    assert winner.resolved_tokens().mode == "light"
    assert winner.resolved_tokens().background == "#F3EEE4"

    design = compile_design_md(interp, winner, receipt_paths=[".wde/research/sector-notes.json"])
    assert "#F3EEE4" in design
    assert "Dark-first project" not in design
    assert "Light-first project" in design
    assert winner.resolved_tokens().accent in design
    assert "Fraunces" in design or winner.resolved_tokens().display_font in design


def test_dark_territory_still_compiles_dark_first():
    interp = interpret_request("modern premium website for a hospitality branding agency")
    territories = generate_territories(interp)
    winner = next(t for t in territories if t.id == "B")
    assert winner.resolved_tokens().mode == "dark"
    design = compile_design_md(interp, winner, [])
    assert "Dark-first project" in design
    assert winner.resolved_tokens().background in design


def test_winner_palette_role_tokens_in_discovery_design_md(tmp_path: Path):
    result = run_discovery(
        tmp_path,
        "modern premium website for a hospitality branding agency",
        try_getdesign=False,
    )
    assert result.ok, result.errors
    design = (tmp_path / "DESIGN.md").read_text(encoding="utf-8")
    # Hospitality A usually wins on sobriety — if light, must carry paper token
    winner_id = result.selection["winner_id"]
    winner = next(t for t in result.territories if t["id"] == winner_id)
    tokens = winner.get("tokens") or {}
    bg = tokens.get("background")
    mode = tokens.get("mode")
    if mode == "light" and bg:
        assert bg in design
        assert "Dark-first project" not in design or "Light-first project" in design
    elif bg:
        assert bg in design


def test_research_synthesis_consumes_receipts(tmp_path: Path):
    result = run_discovery(
        tmp_path,
        "boutique hotel brand site for independent hospitality",
        try_getdesign=False,
    )
    assert result.ok, result.errors
    assert (tmp_path / ".wde" / "research" / "research-synthesis.json").is_file()
    assert (tmp_path / ".wde" / "research" / "research-coverage.txt").is_file()
    assert result.synthesis.get("confidence") in {"limited", "medium", "high", "none"}
    # Internal sector should be covered
    assert result.synthesis.get("coverage", {}).get("internal_sector") is True
    cov = (tmp_path / ".wde" / "research" / "research-coverage.txt").read_text(encoding="utf-8")
    assert "Research coverage" in cov
    assert "Confidence:" in cov


def test_decision_graph_written(tmp_path: Path):
    result = run_discovery(
        tmp_path,
        "agency for independent hotels",
        try_getdesign=False,
    )
    assert result.ok, result.errors
    graph_path = tmp_path / ".wde" / "discovery" / "decision-graph.json"
    assert graph_path.is_file()
    import json

    g = json.loads(graph_path.read_text(encoding="utf-8"))
    kinds = {n["kind"] for n in g["nodes"]}
    assert "transformation" in kinds
    assert "contract" in kinds
    assert g["winner_id"] in {"A", "B", "C"}


def test_receipts_carry_source_type(tmp_path: Path):
    result = run_discovery(
        tmp_path,
        "saas product landing page for api metrics",
        try_getdesign=False,
    )
    assert result.ok, result.errors
    import json

    from wde.discovery.receipts import load_receipts

    receipts = load_receipts(tmp_path)
    sector = next((r for r in receipts if r.get("path_kind") == "sector"), None)
    assert sector is not None, receipts
    assert sector.get("source_type") == "internal_knowledge"
    assert sector.get("network_used") is False
    assert sector.get("executor") == "wde-core"
    assert sector.get("digest")
    assert receipt_is_valid(sector, root=tmp_path)


def test_tokens_from_palette_role_light():
    t = DesignTokens.from_palette_role("Paper ivory + ink black + ochre")
    assert t.mode == "light"
    assert t.background == "#F3EEE4"
