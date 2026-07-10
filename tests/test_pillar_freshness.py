"""Gate 0 pillar freshness + lock-vs-code — anti-bypass of getdesign / structure."""
from __future__ import annotations

import importlib.util
import os
import time
from pathlib import Path

import pytest

_CHECK = Path(__file__).resolve().parents[1] / "scripts" / "check.py"


def _load():
    spec = importlib.util.spec_from_file_location("wde_check", _CHECK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_pillar_older_than_brief_is_error(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    brief = tmp_path / "CREATIVE-BRIEF.md"
    brief.write_text("# brief\n", encoding="utf-8")
    # Make brief newer than pillar
    old = tmp_path / "getdesign-bugatti.md"
    old.write_text("colors:\n  primary: '#fff'\n", encoding="utf-8")
    past = time.time() - 86400 * 30  # 30 days ago
    os.utime(old, (past, past))
    now = time.time()
    os.utime(brief, (now, now))

    mod = _load()
    errors = []
    mod._check_pillar_freshness("Pillar 1 (getdesign)", [old], errors)
    assert any("older than brief" in e or "stale" in e for e in errors)


def test_fresh_pillar_after_brief_passes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    brief = tmp_path / "CREATIVE-BRIEF.md"
    brief.write_text("# brief\n", encoding="utf-8")
    t0 = time.time() - 120
    os.utime(brief, (t0, t0))
    pillar = tmp_path / "design-system-output.md"
    pillar.write_text("# ds\n", encoding="utf-8")
    t1 = time.time() - 30
    os.utime(pillar, (t1, t1))

    mod = _load()
    errors = []
    mod._check_pillar_freshness("Pillar 2", [pillar], errors)
    assert errors == []


def test_lock_board_vs_card_grid_blocks(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "App.jsx").write_text(
        "\n".join(
            f'<div className="product-card">item {i}</div>' for i in range(6)
        ),
        encoding="utf-8",
    )
    lock = (
        "# Lock\n"
        "1. Storefront: CSS grid **departure board** NOT cards (§6)\n"
        "2. Checkout modal shell (§6)\n"
        "3. Admin dense table (§5)\n"
    )
    mod = _load()
    errors = []
    mod._check_lock_vs_code(lock, errors, code_path=str(src))
    assert any("board promised" in e for e in errors)


def test_find_design_system_accepts_master_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    master = tmp_path / "design-system" / "proj" / "MASTER.md"
    master.parent.mkdir(parents=True)
    master.write_text("# master\n", encoding="utf-8")
    mod = _load()
    found = mod._find_design_system_artifacts()
    assert any(p.name == "MASTER.md" for p in found)


def test_find_getdesign_accepts_brand_subdir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    brand = tmp_path / "ferrari" / "DESIGN.md"
    brand.parent.mkdir()
    brand.write_text("colors:\n  primary: '#000'\n", encoding="utf-8")
    # Project contract must NOT count
    (tmp_path / "DESIGN.md").write_text("# project contract\n", encoding="utf-8")
    mod = _load()
    found = mod._find_getdesign_artifacts()
    assert any(p.as_posix().endswith("ferrari/DESIGN.md") or p.name == "DESIGN.md" and p.parent.name == "ferrari" for p in found)
    assert not any(p.resolve() == (tmp_path / "DESIGN.md").resolve() for p in found)


def test_lock_board_with_board_row_passes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "App.jsx").write_text(
        '<table className="board-table"><tr className="board-row">…</tr></table>\n'
        + "\n".join(f'<div className="product-card">{i}</div>' for i in range(2)),
        encoding="utf-8",
    )
    lock = "1. departure board fixed columns NOT cards (§6)\n2. x (§6)\n3. y (§6)\n"
    mod = _load()
    errors = []
    mod._check_lock_vs_code(lock, errors, code_path=str(src))
    assert errors == []
