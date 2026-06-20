"""Tests for scripts/audit_gestures.py — Gate 9 signature-gesture enforcement."""
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "scripts" / "audit_gestures.py"


def run(tmp_path, files: dict, *args):
    """Write {relpath: content} into tmp_path and run the gate over it."""
    for rel, content in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    cmd = [sys.executable, str(SCRIPT), "--code", str(tmp_path), *args]
    return subprocess.run(cmd, capture_output=True, text=True)


# Editorial fixtures ---------------------------------------------------------
EDITORIAL_NONE = {"styles.css": "body{font-family:'Playfair Display',serif;color:#111}"
                                 "h1{font-size:48px;font-weight:700}"}
EDITORIAL_FULL = {
    "styles.css": (
        ".masthead{line-height:0.95;font-family:'Playfair Display'}"
        ".lead::first-letter{float:left;font-size:3.2em}"
        "p{max-width:65ch}"
        "a{text-underline-offset:0.18em}"
    )
}


def test_editorial_no_gestures_blocks(tmp_path):
    r = run(tmp_path, EDITORIAL_NONE, "--archetype", "02 Editorial")
    assert r.returncode == 1
    assert "BLOCKED" in r.stdout
    assert "TOKENS WITHOUT GESTURES" in r.stdout


def test_editorial_full_gestures_passes(tmp_path):
    r = run(tmp_path, EDITORIAL_FULL, "--archetype", "editorial")
    assert r.returncode == 0
    assert "PASSED" in r.stdout


def test_autodetect_from_font_pairing(tmp_path):
    # No --archetype; Editorial must be inferred from the Playfair/Source Serif pairing.
    files = dict(EDITORIAL_FULL)
    files["DESIGN.md"] = "Display: Playfair Display\nBody: Source Serif 4\n"
    # write DESIGN.md at tmp root and point --design at it
    (tmp_path / "DESIGN.md").write_text(files.pop("DESIGN.md"), encoding="utf-8")
    r = run(tmp_path, files, "--design", str(tmp_path / "DESIGN.md"))
    assert r.returncode == 0
    assert "auto-detected" in r.stdout
    assert "Editorial" in r.stdout


def test_unknown_archetype_non_blocking(tmp_path):
    # Point --design at a non-existent file so no font pairing can be auto-detected.
    r = run(tmp_path, {"styles.css": "body{color:#000}"}, "--design", str(tmp_path / "none.md"))
    assert r.returncode == 0
    assert "not determined" in r.stdout


def test_unknown_archetype_strict_blocks(tmp_path):
    r = run(tmp_path, {"styles.css": "body{color:#000}"}, "--design", str(tmp_path / "none.md"), "--strict")
    assert r.returncode == 1


def test_brutalist_hard_offset_shadow(tmp_path):
    files = {"styles.css": ".card{box-shadow:8px 8px 0 #000;border:2px solid #000}"
                           ".card:hover{background:#000;color:#fff}"}
    r = run(tmp_path, files, "--archetype", "4")
    assert r.returncode == 0
    assert "Brutalist" in r.stdout


def test_threshold_three_requires_all(tmp_path):
    # Editorial with only 2/3 gestures fails when threshold is raised to 3.
    files = {"styles.css": ".masthead{line-height:0.95}p{max-width:65ch}"
                           "h1{font-family:'Playfair Display'}"}
    r = run(tmp_path, files, "--archetype", "02", "--threshold", "3")
    assert r.returncode == 1


def test_json_output_shape(tmp_path):
    import json
    r = run(tmp_path, EDITORIAL_FULL, "--archetype", "02", "--json")
    data = json.loads(r.stdout)
    assert data["archetype"].startswith("02")
    assert data["total"] == 3
    assert isinstance(data["gestures"], list)
