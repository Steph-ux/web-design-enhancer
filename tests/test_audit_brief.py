"""Tests for scripts/audit_brief.py — Creative-Brief quality scorer."""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "scripts" / "audit_brief.py"

SHARP = """# CREATIVE-BRIEF.md

## Emotional Intent
When someone lands they must feel like walking into a Zurich architect studio at
midnight, cold concrete and a single warm lamp, expensive restraint.

## The One Unexpected Thing
The lead story has no image at all; the headline itself, set huge, is the only
artwork on the page and that is the whole bet.

## Hero Dimension
- [x] Typography
- [ ] Colour

## The Broken Rule
We ignore the 8px grid on the H1 because the violent jump from 120px to 16px body
IS the broadsheet personality; soften it and it becomes a blog.

## Design Read
A long-form journalism front page for general readers, editorial language.

## Design Dials
- VARIANCE: **9**
- MOTION: **2**
- DENSITY: **6**

## The Cross-Domain Steal
The non-software discipline I am stealing from: print editorial, the front page of
a broadsheet newspaper. The specific move: vertical hairline column rules splitting
the page into unequal columns with a dominating lead above the fold.
"""

FILLER = """# CREATIVE-BRIEF.md

## Emotional Intent
Professional and modern, a clean elegant experience.

## The One Unexpected Thing
A sleek hero like Stripe with a nice gradient.

## Hero Dimension
- [x] Typography
- [x] Colour

## The Broken Rule
We will ignore some grid rules.

## Design Read
A modern website for users.

## Design Dials
- VARIANCE: 8

## The Cross-Domain Steal
Stealing from another SaaS landing page, the app dashboard layout.
"""


def run(tmp_path, text, *args):
    p = tmp_path / "CREATIVE-BRIEF.md"
    p.write_text(text, encoding="utf-8")
    return subprocess.run([sys.executable, str(SCRIPT), "--brief", str(p), *args],
                          capture_output=True, text=True)


def test_sharp_brief_scores_high(tmp_path):
    r = run(tmp_path, SHARP)
    assert r.returncode == 0
    assert "SHARP" in r.stdout


def test_filler_brief_blocked(tmp_path):
    r = run(tmp_path, FILLER)
    assert r.returncode == 1
    assert "BLOCKED" in r.stdout


def test_missing_file_exit_2():
    r = subprocess.run([sys.executable, str(SCRIPT), "--brief", "/nope/none.md"],
                       capture_output=True, text=True)
    assert r.returncode == 2


def test_software_steal_scores_zero(tmp_path):
    r = run(tmp_path, FILLER, "--json")
    data = json.loads(r.stdout)
    b4 = next(d for d in data["dimensions"] if d["id"] == "B4")
    assert b4["points"] == 0


def test_nonsoftware_label_not_false_flagged(tmp_path):
    # "non-software discipline" must NOT trip the software blacklist.
    r = run(tmp_path, SHARP, "--json")
    data = json.loads(r.stdout)
    b4 = next(d for d in data["dimensions"] if d["id"] == "B4")
    assert b4["points"] == b4["max"]


def test_bold_markdown_dials_parsed(tmp_path):
    # **9** / **2** / **6** must parse, and the extreme (9) must be rewarded.
    r = run(tmp_path, SHARP, "--json")
    data = json.loads(r.stdout)
    b5 = next(d for d in data["dimensions"] if d["id"] == "B5")
    assert b5["points"] == b5["max"]


def test_two_hero_dims_penalised(tmp_path):
    r = run(tmp_path, FILLER, "--json")
    data = json.loads(r.stdout)
    b6 = next(d for d in data["dimensions"] if d["id"] == "B6")
    assert b6["points"] < b6["max"]
