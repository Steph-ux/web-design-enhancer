"""
Regression tests for scripts.core.detect_domain.

Locks the query -> domain routing contract. Any change to the
domain_keywords dict (additions, reordering, removals) must keep
these cases green. New domains or new aliases should add cases here.
"""

import sys
from pathlib import Path

import pytest

# Make scripts/ importable without installing the package
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from core import detect_domain  # noqa: E402


# Format: (query, expected_domain, why)
CASES = [
    # --- color ----------------------------------------------------------
    ("#FF0000 palette", "color", "hex with # — regression for plain \\b bug"),
    ("#abc123", "color", "short hex"),
    ("brand accent color", "color", "plain color keyword"),
    ("destructive token foreground", "color", "semantic tokens"),
    ("rgb gradient palette", "color", "rgb keyword"),

    # --- chart ----------------------------------------------------------
    ("best chart for trends over time", "chart", "chart keyword"),
    ("heatmap visualization", "chart", "heatmap keyword"),
    ("funnel graph", "chart", "funnel keyword"),

    # --- landing --------------------------------------------------------
    ("landing page hero section", "landing", "landing keyword"),
    ("CTA conversion testimonial", "landing", "landing keywords"),

    # --- page-flows (must beat pttrns on flow phrases) ------------------
    ("onboarding flow", "page-flows", "tie-breaking — page-flows wins over pttrns"),
    ("checkout flow", "page-flows"),
    ("login flow", "page-flows"),
    ("verify email", "page-flows"),
    ("cancel subscription", "page-flows"),
    ("reset password", "page-flows"),
    ("delete account", "page-flows"),
    ("user journey for booking", "page-flows", "user journey keyword"),

    # --- product --------------------------------------------------------
    ("e-commerce checkout", "product", "regression — hyphenated keyword"),
    ("saas dashboard pricing", "product"),
    ("fintech crm invoice", "product"),
    ("crypto wallet app", "product"),
    ("real estate marketplace", "product", "two-word product keyword"),

    # --- style ----------------------------------------------------------
    ("glassmorphism dark mode design", "style"),
    ("brutalism aurora style", "style"),
    ("tailwind variable checklist", "style"),

    # --- ux -------------------------------------------------------------
    ("wcag accessibility keyboard navigation", "ux"),
    ("scroll usability animation", "ux"),

    # --- typography (font pairings) -------------------------------------
    ("font pairing serif body", "typography", "font pairing wins over google-fonts"),
    ("heading font and body font", "typography"),

    # --- google-fonts ---------------------------------------------------
    ("google font noto subset", "google-fonts"),
    ("monospace font for code", "google-fonts"),
    ("variable font display", "google-fonts"),

    # --- icons ----------------------------------------------------------
    ("lucide icon library", "icons"),
    ("heroicons svg icon", "icons"),
    ("pictogram glyph", "icons"),

    # --- react ----------------------------------------------------------
    ("react useEffect rerender", "react"),
    ("next.js server component suspense", "react"),
    ("dynamic import bundle waterfall", "react"),

    # --- web ------------------------------------------------------------
    ("aria focus outline form", "web"),
    ("autocomplete input type preconnect", "web"),

    # --- apple-hig ------------------------------------------------------
    ("tab bar ios navigation bar", "apple-hig"),
    ("ipados swiftui action sheet", "apple-hig"),
    ("dynamic island live activity", "apple-hig"),
    ("sf symbols widget", "apple-hig"),

    # --- material-design-3 ----------------------------------------------
    ("navigation drawer android", "material-design-3"),
    ("jetpack compose fab snackbar", "material-design-3"),
    ("bottom sheet chip tonal m3", "material-design-3"),

    # --- pttrns (mobile patterns that are NOT flows) --------------------
    ("empty state design", "pttrns"),
    ("pull to refresh", "pttrns"),
    ("swipe action side menu", "pttrns"),
    ("splash screen walkthrough", "pttrns"),

    # --- fallback -------------------------------------------------------
    ("zzzzz qqqqq", "style", "no match -> default fallback"),
]


@pytest.mark.parametrize("query,expected", [(c[0], c[1]) for c in CASES])
def test_detect_domain(query, expected):
    """Routing contract — each query must resolve to the expected domain."""
    actual = detect_domain(query)
    assert actual == expected, (
        f"Query {query!r}: expected domain {expected!r}, got {actual!r}"
    )


def test_hash_keyword_matches():
    """Explicit regression for the \\b regex bug — hex queries route to color."""
    assert detect_domain("#FF0000") == "color"
    assert detect_domain("color #abc") == "color"


def test_hyphenated_keyword_matches():
    """Explicit regression — e-commerce must route to product."""
    assert detect_domain("e-commerce") == "product"
    assert detect_domain("an e-commerce shop") == "product"


def test_page_flows_beats_pttrns_on_onboarding():
    """Tie-breaking contract — page-flows is declared before pttrns."""
    assert detect_domain("onboarding flow") == "page-flows"


def test_case_insensitive():
    """detect_domain lowercases the query."""
    assert detect_domain("ONBOARDING FLOW") == "page-flows"
    assert detect_domain("Tab Bar iOS") == "apple-hig"
