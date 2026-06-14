"""
tests/test_aesthetic_calibration.py
Anti-inflation calibration for the vision verdict. Because the agent often grades
its OWN work, a self-flattered near-perfect verdict must be discounted and a
verdict without concrete critiques must be treated as un-calibrated (blocked).
"""
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

_AR = Path(__file__).parent.parent / "scripts" / "aesthetic_review.py"


def _load():
    spec = importlib.util.spec_from_file_location("ar_mod", _AR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _verdict(score, dim, fixes):
    return {
        "overall_score": score,
        "reads_as": "human",
        "dimensions": {k: {"score": dim, "note": "n"} for k in
                       ["first_impression", "visual_hierarchy", "whitespace_balance",
                        "typography_craft", "colour_harmony", "finish_consistency", "human_vs_ai"]},
        "top_fixes": fixes,
    }


def test_prompt_has_calibration_anchors():
    mod = _load()
    p = mod.build_prompt("§6 Technical", ["desktop", "mobile"])
    assert "Calibration anchors" in p
    assert "90-100" in p
    assert "AT LEAST 2" in p


def test_selfflattery_98_zerofix_is_penalised_and_uncalibrated():
    mod = _load()
    eff, flags = mod.calibrate_verdict(_verdict(98, 98, []), 60, 75)
    assert eff == 80  # 98 - 18
    assert any(f.startswith("INFLATION GUARD") for f in flags)
    assert any(f.startswith("UNCALIBRATED") for f in flags)


def test_98_with_three_fixes_penalised_but_passes():
    mod = _load()
    eff, flags = mod.calibrate_verdict(
        _verdict(98, 97, ["fix alpha aa", "fix beta bb", "fix gamma cc"]), 60, 75)
    assert eff == 88  # 98 - 10
    assert not any(f.startswith("UNCALIBRATED") for f in flags)


def test_honest_80_two_fixes_no_penalty():
    mod = _load()
    eff, flags = mod.calibrate_verdict(
        _verdict(80, 82, ["Fill the empty right half of the hero", "Differentiate project cards"]), 60, 75)
    assert eff == 80
    assert flags == []


def test_uniform_perfect_dims_trigger_guard_even_if_overall_modest():
    mod = _load()
    eff, flags = mod.calibrate_verdict(
        _verdict(80, 96, ["aaaaaaaa", "bbbbbbbb"]), 60, 75)
    assert eff < 80
    assert any(f.startswith("INFLATION GUARD") for f in flags)


def _cli(verdict):
    f = tempfile.mktemp(suffix=".json")
    Path(f).write_text(json.dumps(verdict))
    r = subprocess.run([sys.executable, str(_AR), "--verdict", f, "--json"],
                       capture_output=True, text=True)
    out = json.loads(r.stdout)
    return r.returncode, out["effective_score"]


def test_cli_blocks_selfflattered_verdict():
    code, eff = _cli(_verdict(98, 98, []))
    assert code == 2  # uncalibrated -> blocked
    assert eff == 80


def test_cli_passes_honest_high_with_fixes():
    code, eff = _cli(_verdict(98, 97, ["fix alpha aa", "fix beta bb", "fix gamma cc"]))
    assert code == 0
    assert eff == 88
