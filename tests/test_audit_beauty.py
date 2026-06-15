"""
tests/test_audit_beauty.py
Tests for the Beauty Score auditor (audit_beauty.py) — the positive mirror of
the Generic AI Template detector. Each test validates that a craft marker is
correctly rewarded, or that its absence is correctly penalised / blocked.
"""
import tempfile
import textwrap
from pathlib import Path

import pytest
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from audit_beauty import (
    BeautyAuditor,
    _is_neutral,
    _is_default_blue,
    _rgb_to_hsl,
    _hex_to_rgb,
    _to_px,
)


# ─── Helpers ────────────────────────────────────────────────────────────────

def _make_project(files: dict[str, str]) -> Path:
    tmp = Path(tempfile.mkdtemp())
    for fname, content in files.items():
        fp = tmp / fname
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(textwrap.dedent(content), encoding="utf-8")
    return tmp


def _audit(files: dict[str, str], floor=50, passing=70) -> BeautyAuditor:
    root = _make_project(files)
    a = BeautyAuditor(root_path=root, threshold_floor=floor, threshold_pass=passing)
    a.scan()
    return a


FLAT_CSS = """
    body { font-size: 16px; color: #333333; }
    h1 { font-size: 20px; }
    .card { padding: 16px; margin: 16px; background: #ffffff; }
    .btn { padding: 16px; background: #888888; }
"""

CRAFTED_CSS = """
    :root { --ink:#1a1a1a; --paper:#faf7f0; --accent:#c1440e; }
    body { font-size: 1rem; line-height: 1.6; color: var(--ink); background: var(--paper); }
    h1 { font-size: 4.5rem; letter-spacing: -0.02em; font-weight: 800; }
    h2 { font-size: 2.5rem; }
    h3 { font-size: 1.5rem; }
    small { font-size: 0.8rem; }
    .section { padding: 96px 24px; }
    .card { padding: 32px; gap: 24px; transition: transform 0.25s ease; }
    .btn { padding: 12px 24px; background: var(--accent); transition: background 0.2s; }
    .btn:hover { background: #a23409; }
    .btn:focus-visible { outline: 2px solid var(--accent); }
    @media (prefers-reduced-motion: reduce) { * { transition: none; } }
"""


# ─── End-to-end discrimination ───────────────────────────────────────────────

class TestEndToEnd:
    def test_flat_design_is_blocked(self):
        a = _audit({"styles.css": FLAT_CSS})
        assert a.score < a.threshold_floor
        assert a._exit_code() == 2

    def test_crafted_design_passes(self):
        a = _audit({"styles.css": CRAFTED_CSS})
        assert a.score >= a.threshold_pass
        assert a._exit_code() == 0

    def test_crafted_scores_much_higher_than_flat(self):
        flat = _audit({"a.css": FLAT_CSS}).score
        crafted = _audit({"b.css": CRAFTED_CSS}).score
        assert crafted - flat >= 40

    def test_empty_project_blocks(self):
        a = _audit({"readme.txt": "no css here"})
        assert a._exit_code() == 2


# ─── D1: Typographic scale contrast ──────────────────────────────────────────

class TestD1TypeContrast:
    def test_strong_contrast_full_marks(self):
        a = _audit({"s.css": "body{font-size:16px} h1{font-size:64px}"})
        assert a.dimension_scores["D1"] == 25

    def test_flat_scale_zero(self):
        a = _audit({"s.css": "body{font-size:16px} h1{font-size:18px}"})
        assert a.dimension_scores["D1"] == 0

    def test_rem_units_converted(self):
        a = _audit({"s.css": "body{font-size:1rem} h1{font-size:3rem}"})
        assert a.dimension_scores["D1"] == 25

    def test_tailwind_classes_detected(self):
        a = _audit({"page.tsx": '<h1 className="text-6xl">Hi</h1><p className="text-base">x</p>'})
        assert a.dimension_scores["D1"] >= 18


# ─── D2: Hierarchy richness ──────────────────────────────────────────────────

class TestD2Hierarchy:
    def test_five_sizes_full_marks(self):
        css = "body{font-size:16px}h1{font-size:48px}h2{font-size:32px}h3{font-size:24px}small{font-size:12px}"
        a = _audit({"s.css": css})
        assert a.dimension_scores["D2"] == 15

    def test_single_size_zero(self):
        a = _audit({"s.css": "body{font-size:16px} p{font-size:16px}"})
        assert a.dimension_scores["D2"] == 0


# ─── D3: Colour intentionality ───────────────────────────────────────────────

class TestD3Color:
    def test_signature_accent_rewarded(self):
        a = _audit({"s.css": ".btn{background:#c1440e} body{color:#1a1a1a}"})
        assert a.dimension_scores["D3"] >= 12

    def test_default_blue_not_signature(self):
        a = _audit({"s.css": ".btn{background:#3B82F6} body{color:#111111}"})
        # blue is excluded as signature → no +12 signature bonus
        assert a.dimension_scores["D3"] < 12

    def test_neutral_only_palette_weak(self):
        a = _audit({"s.css": "body{color:#333} .x{background:#fff} .y{color:#888}"})
        assert a.dimension_scores["D3"] == 0

    def test_noisy_palette_penalised(self):
        css = ".a{color:#c1440e}.b{color:#1b9e77}.c{color:#d95f02}.d{color:#7570b3}.e{color:#e7298a}.f{color:#66a61e}.g{color:#e6ab02}.h{color:#a6761d}"
        a = _audit({"s.css": css})
        assert a.dimension_scores["D3"] < 20


# ─── D4: Spacing rhythm ──────────────────────────────────────────────────────

class TestD4Spacing:
    def test_varied_spacing_with_large_rhythm(self):
        css = ".a{padding:8px}.b{padding:16px}.c{gap:24px}.d{margin:32px}.e{padding:96px}"
        a = _audit({"s.css": css})
        assert a.dimension_scores["D4"] == 15

    def test_uniform_spacing_penalised(self):
        a = _audit({"s.css": ".a{padding:16px}.b{margin:16px}.c{gap:16px}"})
        assert a.dimension_scores["D4"] < 10


# ─── D5: Finition / interaction depth ────────────────────────────────────────

class TestD5Finition:
    def test_full_finish(self):
        css = """
        .b:hover{color:red}
        .b:focus-visible{outline:2px solid}
        .b{transition:all .2s}
        @media (prefers-reduced-motion: reduce){*{transition:none}}
        """
        a = _audit({"s.css": css})
        assert a.dimension_scores["D5"] == 25

    def test_no_interactions_zero(self):
        a = _audit({"s.css": "body{color:#111}"})
        assert a.dimension_scores["D5"] == 0

    def test_focus_without_focus_visible_partial(self):
        a = _audit({"s.css": ".b:focus{outline:1px}"})
        # gets the smaller :focus credit, not the full focus-visible one
        assert 0 < a.dimension_scores["D5"] < 10


# ─── Colour helpers ──────────────────────────────────────────────────────────

class TestColorHelpers:
    def test_neutral_detection(self):
        assert _is_neutral("#333333")
        assert _is_neutral("#ffffff")
        assert not _is_neutral("#c1440e")

    def test_default_blue_detection(self):
        assert _is_default_blue("#3B82F6")
        assert not _is_default_blue("#c1440e")
        assert not _is_default_blue("#1a1a1a")

    def test_hex_shorthand_expands(self):
        assert _hex_to_rgb("#fff") == (255, 255, 255)

    def test_rem_to_px(self):
        assert _to_px(2.0, "rem") == 32.0
        assert _to_px(24, "px") == 24


# ─── JSON contract ───────────────────────────────────────────────────────────

class TestJsonOutput:
    def test_to_dict_shape(self):
        a = _audit({"s.css": CRAFTED_CSS})
        d = a.to_dict()
        assert set(d) >= {
            "beauty_score", "label", "threshold_floor", "threshold_pass",
            "exit_code", "dimensions", "findings", "weaknesses",
        }
        assert set(d["dimensions"]) == {"D1", "D2", "D3", "D4", "D5"}
        assert 0 <= d["beauty_score"] <= 100


VAR_TOKEN_CSS = """
    :root {
      --accent:#c1440e; --ink:#1a1a1a;
      --step-0:1rem; --step-1:1.25rem; --step-3:2.1rem;
      --step-5:clamp(2.8rem,6vw,4.6rem);
      --space-2:16px; --space-3:24px; --space-5:64px; --space-6:96px;
    }
    body { font-size:var(--step-0); color:var(--ink); }
    h1 { font-size:var(--step-5); }
    h2 { font-size:var(--step-3); }
    h3 { font-size:var(--step-1); }
    .section { padding:var(--space-6) var(--space-3); }
    .card { padding:var(--space-3); gap:var(--space-2); transition:transform .2s; }
    .btn:hover { color:var(--accent); }
    .btn:focus-visible { outline:2px solid var(--accent); }
    @media (prefers-reduced-motion: reduce){ *{ transition:none; } }
"""


class TestCssVarResolution:
    def test_var_based_tokens_are_resolved_and_score_high(self):
        a = _audit({"styles.css": VAR_TOKEN_CSS})
        # var(--step-5) clamp max 4.6rem=73.6px vs body 16px -> strong contrast
        assert a.dimension_scores["D1"] == 25
        assert a.dimension_scores["D2"] >= 12
        assert a.dimension_scores["D4"] >= 11  # large spacing (96px) resolved from var(); rhythm picked up
        assert a.score >= a.threshold_pass

    def test_clamp_uses_largest_value(self):
        a = _audit({"s.css": ":root{--d:clamp(2rem,5vw,4rem)} body{font-size:1rem} h1{font-size:var(--d)}"})
        assert a.dimension_scores["D1"] == 25
