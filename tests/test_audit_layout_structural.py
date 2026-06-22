"""
tests/test_audit_layout_structural.py

Measured structural-slop regression for audit_layout.py (checks L6-L9).

These run the REAL _JS_LAYOUT against a REAL rendered DOM (headless Chromium via
Playwright), exactly as production does — but the page is a `data:` URL fixture
instead of a localhost server, so no server is needed.

The lexical detector (detect_ai_slop.py) is blind to these — they are geometric,
not token-based. measure_recall.py flagged them as OOD misses:

  L6  identical N-column feature grid      (ood-feature-grid-3col)
  L7  uniform section-padding rhythm        (ood-generic-spacing)
  L8  rounded-2xl + shadow-xl card cliche    (ood-rounded-shadow-card)
  L9  uniform hover-lift translateY          (ood-hover-lift-card)

Contract for each check:
  1. POSITIVE: a fixture exhibiting the cliche fires exactly that warning code.
  2. NEGATIVE: a deliberately varied / human fixture does NOT fire it
     (no false positive — the whole point of MEASURING instead of keyword-matching).

All four are WARN severity: they land in `warnings`, never `errors`, so they only
block with --strict (same policy as L4/L5).
"""
import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(_SCRIPTS))

# Skip the whole module gracefully if Chromium can't launch in this environment.
playwright = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright  # noqa: E402

import audit_layout  # noqa: E402


def _can_launch_chromium() -> bool:
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            b.close()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _can_launch_chromium(), reason="headless chromium unavailable"
)


def _eval(html: str, viewport=(1280, 800)) -> dict:
    """Render `html` in real Chromium at one viewport and run the prod JS once."""
    cfg = {
        "overflowTol": audit_layout.OVERFLOW_TOL,
        "baselineTol": audit_layout.BASELINE_TOL,
        "heightTol": audit_layout.HEIGHT_TOL,
        "rowBucket": audit_layout.ROW_BUCKET,
    }
    w, h = viewport
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": w, "height": h})
        page.set_content(html, wait_until="load")
        page.wait_for_timeout(120)
        data = page.evaluate(audit_layout._JS_LAYOUT, cfg)
        browser.close()
    return data


def _codes(data: dict) -> set:
    return {x["code"] for x in data["errors"]} | {x["code"] for x in data["warnings"]}


_DOC = "<!doctype html><html><head><meta charset='utf-8'>{style}</head><body>{body}</body></html>"


# ---------------------------------------------------------------------------
# L6 — identical N-column feature grid
# ---------------------------------------------------------------------------

_L6_SLOP = _DOC.format(
    style="<style>.features{display:grid;grid-template-columns:repeat(3,1fr);gap:24px}"
          ".feature{padding:24px;border:1px solid #eee}</style>",
    body="<section class='features'>"
         "<div class='feature'><h3>Fast</h3><p>Very fast indeed.</p></div>"
         "<div class='feature'><h3>Secure</h3><p>Very secure indeed.</p></div>"
         "<div class='feature'><h3>Simple</h3><p>Very simple indeed.</p></div>"
         "</section>",
)

# Human/varied: 3 columns but the cards differ structurally (one has an image,
# widths differ via col-span, child counts differ) — should NOT fire L6.
_L6_OK = _DOC.format(
    style="<style>.features{display:grid;grid-template-columns:2fr 1fr 1fr;gap:24px}"
          ".feature{padding:24px}</style>",
    body="<section class='features'>"
         "<div class='feature'><img src='data:image/gif;base64,R0lGODlhAQABAAAAACw=' "
         "width='80' height='80' alt=''><h3>Lead</h3><p>Long lead paragraph here.</p>"
         "<a href='#'>More</a></div>"
         "<div class='feature'><h3>Two</h3></div>"
         "<div class='feature'><p>Just prose, no heading at all here.</p></div>"
         "</section>",
)


def test_L6_identical_feature_grid_fires():
    assert "L6" in _codes(_eval(_L6_SLOP))


def test_L6_varied_grid_does_not_fire():
    assert "L6" not in _codes(_eval(_L6_OK))


# ---------------------------------------------------------------------------
# L7 — uniform section-padding rhythm
# ---------------------------------------------------------------------------

_L7_SLOP = _DOC.format(
    style="<style>section{padding:80px 0}</style>",
    body="<section><h2>One</h2></section><section><h2>Two</h2></section>"
         "<section><h2>Three</h2></section><section><h2>Four</h2></section>",
)

# Human: intentional vertical rhythm variation (hero breathes more than footer).
_L7_OK = _DOC.format(
    style="<style>.a{padding:140px 0}.b{padding:64px 0}.c{padding:32px 0}"
          ".d{padding:96px 0}</style>",
    body="<section class='a'><h2>Hero</h2></section>"
         "<section class='b'><h2>Body</h2></section>"
         "<section class='c'><h2>Note</h2></section>"
         "<section class='d'><h2>CTA</h2></section>",
)


def test_L7_uniform_section_padding_fires():
    assert "L7" in _codes(_eval(_L7_SLOP))


def test_L7_varied_section_padding_does_not_fire():
    assert "L7" not in _codes(_eval(_L7_OK))


# ---------------------------------------------------------------------------
# L8 — rounded-2xl + shadow-xl card cliche
# ---------------------------------------------------------------------------

_L8_SLOP = _DOC.format(
    style="<style>.wrap{display:flex;gap:24px}"
          ".card{border-radius:16px;box-shadow:0 20px 25px -5px rgba(0,0,0,.1);"
          "padding:32px;width:280px}</style>",
    body="<div class='wrap'>"
         "<div class='card'>One</div><div class='card'>Two</div>"
         "<div class='card'>Three</div></div>",
)

# Human: cards with real differentiation — sharp corners, varied treatment.
_L8_OK = _DOC.format(
    style="<style>.wrap{display:flex;gap:24px}"
          ".card{border-radius:0;padding:32px;width:280px;border-top:3px solid #111}</style>",
    body="<div class='wrap'>"
         "<div class='card'>One</div><div class='card'>Two</div>"
         "<div class='card'>Three</div></div>",
)


def test_L8_rounded_shadow_card_fires():
    assert "L8" in _codes(_eval(_L8_SLOP))


def test_L8_flat_card_does_not_fire():
    assert "L8" not in _codes(_eval(_L8_OK))


# ---------------------------------------------------------------------------
# L9 — uniform hover-lift translateY
# ---------------------------------------------------------------------------

_L9_SLOP = _DOC.format(
    style="<style>.wrap{display:flex;gap:24px}"
          ".card{padding:32px;width:240px;transition:transform .3s}"
          ".card:hover{transform:translateY(-8px)}</style>",
    body="<div class='wrap'>"
         "<div class='card'>One</div><div class='card'>Two</div>"
         "<div class='card'>Three</div></div>",
)

# Human: no hover-lift at all.
_L9_OK = _DOC.format(
    style="<style>.wrap{display:flex;gap:24px}.card{padding:32px;width:240px}</style>",
    body="<div class='wrap'>"
         "<div class='card'>One</div><div class='card'>Two</div>"
         "<div class='card'>Three</div></div>",
)


def test_L9_uniform_hover_lift_fires():
    assert "L9" in _codes(_eval(_L9_SLOP))


def test_L9_no_hover_lift_does_not_fire():
    assert "L9" not in _codes(_eval(_L9_OK))


# ---------------------------------------------------------------------------
# Severity contract: L6-L9 are WARN, never ERROR (block only with --strict).
# ---------------------------------------------------------------------------

def test_structural_checks_are_warn_severity():
    data = _eval(_L6_SLOP)
    err_codes = {x["code"] for x in data["errors"]}
    for code in ("L6", "L7", "L8", "L9"):
        assert code not in err_codes, f"{code} must be WARN, not ERROR"
