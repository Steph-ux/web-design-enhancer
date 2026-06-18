"""
tests/test_creative_brief.py
Recommendation #1 — Phase -1 Creative Brief enforces a point of view BEFORE
Phase 0. A getdesign reference says what a design *looks like*; it never says
what it must make someone *feel*. A model cannot invent a point of view, so the
user imposes one. The gate validates *presence and structure* (BLOCK), never
quality, with a WARN nudge for vague-but-present content.
"""
import importlib.util
import os
from pathlib import Path

import pytest

_CHECK = Path(__file__).parent.parent / "scripts" / "check.py"
_TEMPLATE = Path(__file__).parent.parent / "templates" / "creative-brief-template.md"


def _load():
    spec = importlib.util.spec_from_file_location("check_brief", _CHECK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_GOOD = """# CREATIVE-BRIEF.md
## Emotional Intent
Like walking into a Zurich architect studio, quiet and precise and expensive.
## The One Unexpected Thing
The only imagery is the developer's own ASCII commit-graph rendered huge as hero.
## Hero Dimension
- [ ] Typography
- [x] Negative space
- [ ] Colour
- [ ] Motion
- [ ] Illustration
## The Broken Rule
We ignore the 8px grid on the H1 because the tension with 15px body IS the design.
## Design Read
Reading this as: a developer portfolio for hiring managers, with an editorial / kinetic-type language, leaning toward native CSS + scroll-driven motion.
## Design Dials
- VARIANCE: 8
- MOTION: 4
- DENSITY: 3
## The Cross-Domain Steal
Stealing from Penguin Books' 1960s paperback grid: the three-band horizontal colour split as the hero composition.
"""


@pytest.fixture
def in_tmp(tmp_path):
    """Run inside a temp cwd (the check reads CREATIVE-BRIEF.md from cwd)."""
    prev = os.getcwd()
    os.chdir(tmp_path)
    try:
        yield tmp_path
    finally:
        os.chdir(prev)


def _write(tmp_path, text):
    (tmp_path / "CREATIVE-BRIEF.md").write_text(text, encoding="utf-8")


# --- presence / structure (BLOCK) ------------------------------------------

def test_missing_file_blocks(in_tmp):
    c = _load()
    errors, _ = c.check_creative_brief()
    assert any("missing" in e for e in errors)


def test_fully_filled_passes(in_tmp):
    c = _load()
    _write(in_tmp, _GOOD)
    errors, warnings = c.check_creative_brief()
    assert errors == []
    assert warnings == []


def test_unfilled_emotional_intent_blocks(in_tmp):
    c = _load()
    _write(in_tmp, _GOOD.replace(
        "Like walking into a Zurich architect studio, quiet and precise and expensive.", "___"))
    errors, _ = c.check_creative_brief()
    assert any("Emotional Intent unfilled" in e for e in errors)


def test_unfilled_unexpected_thing_blocks(in_tmp):
    c = _load()
    _write(in_tmp, _GOOD.replace(
        "The only imagery is the developer's own ASCII commit-graph rendered huge as hero.", "___"))
    errors, _ = c.check_creative_brief()
    assert any("Unexpected Thing unfilled" in e for e in errors)


def test_no_hero_dimension_ticked_blocks(in_tmp):
    c = _load()
    _write(in_tmp, _GOOD.replace("- [x] Negative space", "- [ ] Negative space"))
    errors, _ = c.check_creative_brief()
    assert any("Hero Dimension not selected" in e for e in errors)


def test_multiple_hero_dimensions_block(in_tmp):
    c = _load()
    _write(in_tmp, _GOOD.replace("- [ ] Typography", "- [x] Typography"))
    errors, _ = c.check_creative_brief()
    assert any("more than one Hero Dimension" in e for e in errors)


def test_broken_rule_without_because_blocks(in_tmp):
    c = _load()
    _write(in_tmp, _GOOD.replace(
        "We ignore the 8px grid on the H1 because the tension with 15px body IS the design.",
        "We ignore the 8px grid on the H1 hero, it sits at 97px."))
    errors, _ = c.check_creative_brief()
    assert any("Broken Rule has no rationale" in e for e in errors)


def test_unfilled_broken_rule_blocks(in_tmp):
    c = _load()
    _write(in_tmp, _GOOD.replace(
        "We ignore the 8px grid on the H1 because the tension with 15px body IS the design.", "___"))
    errors, _ = c.check_creative_brief()
    assert any("Broken Rule unfilled" in e for e in errors)


# --- quality (WARN only, never blocks) -------------------------------------

def test_vague_emotional_intent_warns_does_not_block(in_tmp):
    c = _load()
    _write(in_tmp, _GOOD.replace(
        "Like walking into a Zurich architect studio, quiet and precise and expensive.",
        "Professional and modern."))
    errors, warnings = c.check_creative_brief()
    assert errors == []  # presence is satisfied
    assert any("vague" in w for w in warnings)


def test_concrete_long_intent_with_a_buzzword_not_flagged(in_tmp):
    # A long, specific sentence that happens to contain one buzzword is fine.
    c = _load()
    _write(in_tmp, _GOOD.replace(
        "Like walking into a Zurich architect studio, quiet and precise and expensive.",
        "The quiet confidence of a premium Swiss watch boutique at closing time, "
        "lights low, every object deliberately placed and nothing for sale on display."))
    errors, warnings = c.check_creative_brief()
    assert errors == []
    assert warnings == []


# --- the shipped template must not pass verbatim ---------------------------

def test_blank_template_blocks(in_tmp):
    # A user who copies the template without filling it must be blocked.
    c = _load()
    _write(in_tmp, _TEMPLATE.read_text(encoding="utf-8"))
    errors, _ = c.check_creative_brief()
    assert errors  # unfilled ___ and no ticked box


# --- Dials + Cross-Domain Steal (taste-skill bridge) -----------------------

def test_missing_dials_blocks(in_tmp):
    c = _load()
    _write(in_tmp, _GOOD.replace("- VARIANCE: 8\n", ""))
    errors, _ = c.check_creative_brief()
    assert any("Design Dials incomplete" in e for e in errors)


def test_balanced_dials_warn_not_block(in_tmp):
    c = _load()
    flat = _GOOD.replace("- VARIANCE: 8", "- VARIANCE: 5") \
                .replace("- MOTION: 4", "- MOTION: 5") \
                .replace("- DENSITY: 3", "- DENSITY: 4")
    _write(in_tmp, flat)
    errors, warnings = c.check_creative_brief()
    assert errors == []
    assert any("too balanced" in w for w in warnings)


def test_cross_domain_steal_unfilled_blocks(in_tmp):
    c = _load()
    no_steal = _GOOD.replace(
        "Stealing from Penguin Books' 1960s paperback grid: the three-band horizontal colour split as the hero composition.",
        "___")
    _write(in_tmp, no_steal)
    errors, _ = c.check_creative_brief()
    assert any("Cross-Domain Steal unfilled" in e for e in errors)


def test_tech_cross_domain_steal_warns(in_tmp):
    c = _load()
    techy = _GOOD.replace(
        "Stealing from Penguin Books' 1960s paperback grid: the three-band horizontal colour split as the hero composition.",
        "Stealing Linear's website hero layout and Stripe's gradient.")
    _write(in_tmp, techy)
    errors, warnings = c.check_creative_brief()
    assert errors == []
    assert any("still a tech reference" in w for w in warnings)
