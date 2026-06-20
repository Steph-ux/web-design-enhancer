"""Tests for scripts/audit_wow.py — opt-in deliberate-excess (WOW) audit."""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "scripts" / "audit_wow.py"

BRIEF_TYPO_EXTREME = """# CREATIVE-BRIEF.md
## Hero Dimension
- [x] Typography
## Design Dials
- VARIANCE: **9**
- MOTION: **2**
- DENSITY: **6**
"""

BRIEF_TYPO_MID = """# CREATIVE-BRIEF.md
## Hero Dimension
- [x] Typography
## Design Dials
- VARIANCE: 7
- MOTION: 5
- DENSITY: 4
"""

CSS_HUGE = ".h{font-size:clamp(48px,11vw,132px);font-family:'Playfair Display'}.m{masthead}p{max-width:65ch}a{text-underline-offset:.18em}.x::first-letter{float:left}"
CSS_SMALL = ".h{font-size:24px;font-family:'Playfair Display'}"

DESIGN_SIG = """## 11. Signature Gesture
- **Grep signature**: `text-underline-offset`
"""


def run(tmp_path, css, brief, design=None, *args):
    (tmp_path / "styles.css").write_text(css, encoding="utf-8")
    (tmp_path / "CREATIVE-BRIEF.md").write_text(brief, encoding="utf-8")
    dpath = tmp_path / "DESIGN.md"
    dpath.write_text(design or "", encoding="utf-8")
    cmd = [sys.executable, str(SCRIPT), "--code", str(tmp_path),
           "--brief", str(tmp_path / "CREATIVE-BRIEF.md"), "--design", str(dpath),
           "--archetype", "02 Editorial", *args]
    return subprocess.run(cmd, capture_output=True, text=True)


def test_typography_excess_detected(tmp_path):
    r = run(tmp_path, CSS_HUGE, BRIEF_TYPO_EXTREME, DESIGN_SIG, "--json")
    data = json.loads(r.stdout)
    w1 = next(l for l in data["levers"] if l["id"] == "W1")
    assert w1["points"] == w1["max"]


def test_no_excess_when_type_small(tmp_path):
    r = run(tmp_path, CSS_SMALL, BRIEF_TYPO_EXTREME, DESIGN_SIG, "--json")
    data = json.loads(r.stdout)
    w1 = next(l for l in data["levers"] if l["id"] == "W1")
    assert w1["points"] == 0


def test_extreme_dial_rewarded(tmp_path):
    r = run(tmp_path, CSS_HUGE, BRIEF_TYPO_EXTREME, DESIGN_SIG, "--json")
    data = json.loads(r.stdout)
    w3 = next(l for l in data["levers"] if l["id"] == "W3")
    assert w3["points"] == w3["max"]


def test_mid_dials_not_rewarded(tmp_path):
    r = run(tmp_path, CSS_HUGE, BRIEF_TYPO_MID, DESIGN_SIG, "--json")
    data = json.loads(r.stdout)
    w3 = next(l for l in data["levers"] if l["id"] == "W3")
    assert w3["points"] < w3["max"]


def test_full_wow_passes(tmp_path):
    # Huge type + all 3 editorial gestures + extreme dial + signature in code -> high.
    r = run(tmp_path, CSS_HUGE, BRIEF_TYPO_EXTREME, DESIGN_SIG)
    assert r.returncode == 0
    assert "REACHES FOR WAOUH" in r.stdout


def test_competent_blocks(tmp_path):
    r = run(tmp_path, CSS_SMALL, BRIEF_TYPO_MID)
    assert r.returncode == 1
    assert "BELOW WAOUH" in r.stdout
