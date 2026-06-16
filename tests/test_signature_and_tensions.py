"""
tests/test_signature_and_tensions.py
Recommendations #3 (§11 Signature Gesture) and #4 (§12 Intentional Tensions).

Both are WARN-only (never block) to avoid gate-stacking false positives. The one
piece with real teeth: if §11 declares a `Grep signature` AND a code path is
given, the gate verifies the gesture is actually implemented — a signature that
exists only on paper is flagged. Presence/structure is checked; quality is not.
"""
import importlib.util
import io
from contextlib import redirect_stdout
from pathlib import Path

import pytest

_VD = Path(__file__).parent.parent / "scripts" / "validate_design.py"


def _load():
    spec = importlib.util.spec_from_file_location("vd_sig", _VD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _warns(design, code=None, capture=False):
    vd = _load()
    v = vd.DesignValidator("x", False, code)
    v.content = design
    v._parse_sections()
    buf = io.StringIO()
    with redirect_stdout(buf):
        v._validate_signature_gesture()
        v._validate_tensions()
    return (v.warnings, buf.getvalue()) if capture else v.warnings


_SIG_DECL = ("## 11. Signature Gesture\n"
             "- Description: left accent line grows on hover\n"
             "- Grep signature: `border-left.*transition`\n")
_GOOD_TENS = ("## 12. Intentional Tensions\n"
              "- T1 Typography: H1 80px / Body 15px — ratio 5.3:1\n"
              "- T2 Density: hero 160px / feature 24px\n"
              "- T3 Colour: 97% mono / 3% accent\n")


# --- §11 Signature Gesture --------------------------------------------------

class TestSignatureGesture:
    def test_missing_section_warns(self):
        w = _warns("## 1. Theme\nfoo\n")
        assert any("11. Signature Gesture' missing" in x for x in w)

    def test_unfilled_placeholder_warns(self):
        w = _warns("## 11. Signature Gesture\n- Description: [Ex: a line]\n")
        assert any("unfilled placeholders" in x and "11" in x for x in w)

    def test_declared_without_grep_signature_warns(self):
        w = _warns("## 11. Signature Gesture\n- Description: a real owned gesture here\n")
        assert any("no `Grep signature`" in x for x in w)

    def test_declared_no_code_path_info(self):
        w = _warns(_SIG_DECL)
        assert any("Run with --code" in x for x in w)

    def test_signature_present_in_code_passes(self, tmp_path):
        (tmp_path / "a.css").write_text(".card{border-left:2px solid red;transition:.2s}")
        w, out = _warns(_SIG_DECL, str(tmp_path), capture=True)
        assert not any("NOT found" in x for x in w)
        assert "signature gesture implemented" in out

    def test_signature_absent_from_code_warns(self, tmp_path):
        (tmp_path / "a.css").write_text(".card{color:red}")
        w = _warns(_SIG_DECL, str(tmp_path))
        assert any("NOT found in" in x for x in w)

    def test_invalid_regex_warns_not_crash(self, tmp_path):
        (tmp_path / "a.css").write_text(".card{}")
        bad = "## 11. Signature Gesture\n- Description: x\n- Grep signature: `[unclosed`\n"
        w = _warns(bad, str(tmp_path))
        assert any("not a valid regex" in x for x in w)

    def test_signature_never_produces_errors(self, tmp_path):
        # §11 is WARN-only — it must never add to errors.
        vd = _load()
        v = vd.DesignValidator("x", False, str(tmp_path))
        v.content = "## 1. Theme\nfoo\n"
        v._parse_sections()
        v._validate_signature_gesture()
        assert v.errors == []


# --- §12 Intentional Tensions ----------------------------------------------

class TestTensions:
    def test_missing_section_warns(self):
        w = _warns("## 1. Theme\nfoo\n")
        assert any("12. Intentional Tensions' missing" in x for x in w)

    def test_two_sharp_tensions_pass(self):
        w = _warns(_GOOD_TENS)
        assert not any("12" in x for x in w)

    def test_single_pair_warns(self):
        w = _warns("## 12. Intentional Tensions\n- T1 Typography: H1 80px / Body 15px — 5.3:1\n")
        assert any("only 1 tension pair" in x for x in w)

    def test_uniform_moderate_warns(self):
        flat = ("## 12. Intentional Tensions\n"
                "- T1 Typography: moderate scale\n"
                "- T2 Density: balanced spacing\n")
        w = _warns(flat)
        assert any("uniformly 'moderate" in x for x in w)

    def test_unfilled_placeholder_warns(self):
        w = _warns("## 12. Intentional Tensions\n- T1 Typography: [Ex: H1 / Body]\n")
        assert any("unfilled placeholders" in x and "12" in x for x in w)

    def test_tensions_never_produces_errors(self):
        vd = _load()
        v = vd.DesignValidator("x", False, None)
        v.content = "## 1. Theme\nfoo\n"
        v._parse_sections()
        v._validate_tensions()
        assert v.errors == []
