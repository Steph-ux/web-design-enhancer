"""
tests/test_hierarchy_excess.py
Task 7 — Display type excess exemption for Typography hero.

H1 may exceed 80px only when CREATIVE-BRIEF.md commits Typography as the
Hero Dimension and documents "because" (in the brief Broken Rule and/or
DESIGN.md §11). Absolute safety cap: H1 > 200px remains ERROR always.
"""
import importlib.util
from pathlib import Path

import pytest

_VD = Path(__file__).parent.parent / "scripts" / "validate_design.py"


def _load():
    spec = importlib.util.spec_from_file_location("vd_hier", _VD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _hierarchy(design: str, cwd=None, monkeypatch=None):
    """Run only _validate_hierarchy after setting content."""
    if cwd is not None and monkeypatch is not None:
        monkeypatch.chdir(cwd)
    vd = _load()
    v = vd.DesignValidator("x", False, None)
    v.content = design
    v._parse_sections()
    v._validate_hierarchy()
    return v


_HIER_120 = (
    "## 4. Typography Hierarchy\n"
    "- **H1**: 120px / 700 / 1.0\n"
    "- **P**: 16px / 400 / 1.5\n"
)

_HIER_220 = (
    "## 4. Typography Hierarchy\n"
    "- **H1**: 220px / 700 / 1.0\n"
    "- **P**: 16px / 400 / 1.5\n"
)

_HIER_48 = (
    "## 4. Typography Hierarchy\n"
    "- **H1**: 48px / 700 / 1.2\n"
    "- **P**: 16px / 400 / 1.5\n"
)

_BRIEF_TYPO_HERO = (
    "# Brief\n"
    "## Hero Dimension\n"
    "- [x] Typography\n"
    "## The Broken Rule\n"
    "We ignore the 80px H1 cap because the hero type IS the product identity.\n"
)

_SIG_WITH_BECAUSE = (
    "## 11. Signature Gesture\n"
    "Full-bleed 120px display name because body stays 16px for tension.\n"
)


def _errors_lower(v):
    return [str(e).lower() for e in v.errors]


def _has_h1_too_large(errors_lower):
    return any("too large" in e and "h1" in e for e in errors_lower)


class TestHierarchyExcess:
    def test_h1_over_80_blocked_without_typography_hero(self):
        v = _hierarchy(_HIER_120)
        assert _has_h1_too_large(_errors_lower(v)), (
            f"Expected H1 120px too-large ERROR without hero; got: {v.errors}"
        )

    def test_h1_over_80_allowed_with_typography_hero_and_because(
        self, tmp_path, monkeypatch
    ):
        (tmp_path / "CREATIVE-BRIEF.md").write_text(
            _BRIEF_TYPO_HERO, encoding="utf-8"
        )
        design = _HIER_120 + "\n" + _SIG_WITH_BECAUSE
        v = _hierarchy(design, cwd=tmp_path, monkeypatch=monkeypatch)
        assert not _has_h1_too_large(_errors_lower(v)), (
            f"Expected no H1 too-large ERROR with Typography hero; got: {v.errors}"
        )

    def test_h1_over_80_allowed_with_hero_and_because_in_brief_only(
        self, tmp_path, monkeypatch
    ):
        """Because in Broken Rule alone is enough (no §11 required)."""
        (tmp_path / "CREATIVE-BRIEF.md").write_text(
            _BRIEF_TYPO_HERO, encoding="utf-8"
        )
        v = _hierarchy(_HIER_120, cwd=tmp_path, monkeypatch=monkeypatch)
        assert not _has_h1_too_large(_errors_lower(v)), (
            f"Expected exemption from brief 'because' alone; got: {v.errors}"
        )

    def test_h1_over_200_still_error_with_hero(self, tmp_path, monkeypatch):
        (tmp_path / "CREATIVE-BRIEF.md").write_text(
            _BRIEF_TYPO_HERO, encoding="utf-8"
        )
        design = _HIER_220 + "\n" + _SIG_WITH_BECAUSE
        v = _hierarchy(design, cwd=tmp_path, monkeypatch=monkeypatch)
        assert _has_h1_too_large(_errors_lower(v)), (
            f"Expected H1 > 200px still ERROR even with hero; got: {v.errors}"
        )
        # Safety cap message should mention absolute limit when relevant
        joined = "\n".join(v.errors).lower()
        assert "too large" in joined and "h1" in joined

    def test_h1_in_range_no_excess_error(self):
        v = _hierarchy(_HIER_48)
        assert not _has_h1_too_large(_errors_lower(v))
