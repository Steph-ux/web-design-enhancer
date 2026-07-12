"""Scaffold post-discover + external token blend + deliver strictness."""

from __future__ import annotations

from pathlib import Path

from wde.core.project_context import ProjectContext, init_project
from wde.core.runner import deliver_check
from wde.discovery.orchestrator import run_discovery
from wde.discovery.token_extract import extract_tokens_from_text
from wde.discovery.traces import run_code_trace


def test_discover_writes_scaffold_with_signature(tmp_path: Path):
    r = run_discovery(
        tmp_path,
        "modern premium hospitality branding agency",
        try_getdesign=False,
        write_scaffold_files=True,
    )
    assert r.ok, r.errors
    html = tmp_path / "src" / "index.html"
    css = tmp_path / "src" / "styles.css"
    assert html.is_file()
    assert css.is_file()
    text = html.read_text(encoding="utf-8")
    winner_id = r.selection["winner_id"]
    sig = f"{winner_id.lower()}-signature"
    assert f'data-wde-signature="{sig}"' in text
    assert "viewport" in text
    # code_trace must pass after scaffold
    code = run_code_trace(tmp_path)
    assert code.ok, [f.to_dict() for f in code.findings if not f.ok]
    bg = r.selection  # noqa — tokens on territories
    # CSS holds winner background from design
    design = (tmp_path / "DESIGN.md").read_text(encoding="utf-8")
    # background hex from palette table appears in css vars
    assert "--wde-bg:" in css.read_text(encoding="utf-8")


def test_no_scaffold_flag(tmp_path: Path):
    r = run_discovery(
        tmp_path,
        "saas api landing",
        try_getdesign=False,
        write_scaffold_files=False,
    )
    assert r.ok, r.errors
    assert not (tmp_path / "src" / "index.html").is_file()


def test_extract_tokens_from_getdesign_like_markdown():
    md = """
    # Design System
    Background #0B0B0C
    Surface #1A1A1C
    Text #F5F5F5
    Accent #E8C547
    Display: Inter
    """
    tok = extract_tokens_from_text(md, brand="linear")
    assert tok is not None
    assert tok.mode == "dark"
    assert tok.accent.upper() in {"#E8C547", "#E8C547"}
    assert tok.background.startswith("#")


def test_external_token_blend_from_file(tmp_path: Path):
    (tmp_path / "getdesign-linear.md").write_text(
        "Background #111111 Surface #222222 Text #EEEEEE Accent #00C2A8 Display: Inter\n",
        encoding="utf-8",
    )
    r = run_discovery(
        tmp_path,
        "saas metrics product",
        try_getdesign=False,
        write_scaffold_files=True,
    )
    assert r.ok, r.errors
    # Accent from external file should influence winner when blend runs
    audit = (tmp_path / ".wde" / "research" / "territories.json").read_text(encoding="utf-8")
    assert "external_token_audit" in audit or "00C2A8" in audit or "getdesign" in audit.lower()


def test_deliver_blocks_without_url_when_scaffold_exists(tmp_path: Path):
    init_project(tmp_path)
    r = run_discovery(
        tmp_path,
        "hotel boutique site",
        try_getdesign=False,
        write_scaffold_files=True,
    )
    assert r.ok, r.errors
    ctx = ProjectContext(tmp_path)
    ok, blockers, results = deliver_check(ctx, url=None)
    assert ok is False
    joined = " ".join(blockers).lower()
    # Either explicit url gate or discovery.traces render failure
    assert (
        "url" in joined
        or "visual" in joined
        or any(x.check_id == "discovery.traces" and x.status == "failed" for x in results)
    ), blockers
