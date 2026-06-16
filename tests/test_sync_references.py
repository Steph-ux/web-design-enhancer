"""
tests/test_sync_references.py
Catalogue-drift guard for the anti-monoculture CSV (recommendation #2 upkeep).

data/getdesign-references.csv is a hand-curated snapshot of getdesign's
catalogue; getdesign adds/removes brands, so it drifts. sync_references.py
detects drift in both directions and appends new brands for review without ever
auto-deleting or auto-classifying. These tests are network-free (parsing +
drift logic + --update behaviour against an injected catalogue).
"""
import csv
import importlib.util
from pathlib import Path

import pytest

_SYNC = Path(__file__).parent.parent / "scripts" / "sync_references.py"


def _load():
    spec = importlib.util.spec_from_file_location("sync_ref", _SYNC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_LIST = """\
\033[2mstripe\033[0m - Payment infrastructure. Signature purple gradients.
linear.app - Project management. Ultra-minimal, purple accent.
wired - Tech magazine. Paper-white broadsheet, custom serif display.
nintendo-2001 - Y2K console-chrome web. Brushed-metal panels.
shopify - E-commerce platform. Dark-first cinematic, neon green.
Tell your coding agent to use this file as reference.
"""


# --- parsing ---------------------------------------------------------------

class TestParse:
    def test_parses_brand_and_description(self):
        s = _load()
        cat = s.parse_list_output(_LIST)
        assert cat["stripe"].startswith("Payment infrastructure")
        assert "linear.app" in cat
        assert "nintendo-2001" in cat

    def test_strips_ansi_codes(self):
        s = _load()
        cat = s.parse_list_output(_LIST)
        # stripe had an ANSI wrapper; the key must be clean.
        assert "stripe" in cat
        assert all("\033" not in k for k in cat)

    def test_ignores_non_brand_lines(self):
        s = _load()
        cat = s.parse_list_output(_LIST)
        assert not any("Tell your coding agent" in k for k in cat)
        assert len(cat) == 5

    def test_normalize_brand_matches_check_logic(self):
        s = _load()
        assert s.normalize_brand("linear.app") == "linear"
        assert s.normalize_brand("getdesign-nike.md") == "nike"
        assert s.normalize_brand("nintendo-2001") == "nintendo-2001"


# --- drift detection -------------------------------------------------------

class TestDrift:
    def test_detects_new_brand(self):
        s = _load()
        catalogue = {"stripe": "x", "wired": "y", "brandnew": "z"}
        rows = [{"brand": "stripe"}, {"brand": "wired"}]
        dead, new = s.compute_drift(catalogue, rows)
        assert new == ["brandnew"]
        assert dead == []

    def test_detects_dead_brand(self):
        s = _load()
        catalogue = {"stripe": "x"}
        rows = [{"brand": "stripe"}, {"brand": "deadbrand"}]
        dead, new = s.compute_drift(catalogue, rows)
        assert dead == ["deadbrand"]
        assert new == []

    def test_in_sync_no_drift(self):
        s = _load()
        catalogue = {"stripe": "x", "linear.app": "y"}
        rows = [{"brand": "stripe"}, {"brand": "linear.app"}]
        dead, new = s.compute_drift(catalogue, rows)
        assert dead == [] and new == []

    def test_normalized_match_no_false_drift(self):
        # CSV stores 'linear.app'; catalogue key 'linear.app' — must match even
        # though normalization strips the .app tail on both sides.
        s = _load()
        catalogue = {"linear.app": "y"}
        rows = [{"brand": "linear.app"}]
        dead, new = s.compute_drift(catalogue, rows)
        assert dead == [] and new == []


# --- segment hinting (advisory only) ---------------------------------------

class TestSegmentHint:
    def test_non_saas_hint(self):
        s = _load()
        assert s.suggest_segment("Luxury automotive brand, cinematic black.") == "non-saas"

    def test_saas_hint(self):
        s = _load()
        assert s.suggest_segment("Document database with developer documentation.") == "saas"

    def test_ambiguous_is_unknown(self):
        s = _load()
        assert s.suggest_segment("A brand.") == "unknown"


# --- --update behaviour ----------------------------------------------------

class TestUpdate:
    def test_append_new_brands_never_overwrites_or_deletes(self, tmp_path, monkeypatch):
        s = _load()
        csv_path = tmp_path / "refs.csv"
        csv_path.write_text(
            "brand,category,segment,note\nstripe,fintech,saas,curated\n", encoding="utf-8")
        monkeypatch.setattr(s, "REFERENCES_CSV", csv_path)

        catalogue = {"stripe": "Payment infra", "shopify": "E-commerce retail platform"}
        added = s.append_new_brands(csv_path, catalogue, ["shopify"])
        assert added == 1

        rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
        by_brand = {r["brand"]: r for r in rows}
        # Curated row untouched.
        assert by_brand["stripe"]["segment"] == "saas"
        assert by_brand["stripe"]["note"] == "curated"
        # New row added as unknown for review (never auto-classified as final).
        assert by_brand["shopify"]["segment"] == "unknown"
        assert "review" in by_brand["shopify"]["note"].lower()


# --- the shipped CSV must parse and have both segments ---------------------

def test_shipped_csv_is_wellformed():
    s = _load()
    rows = s.load_csv(s.REFERENCES_CSV)
    assert rows, "shipped CSV must not be empty"
    segs = {r["segment"] for r in rows}
    assert "saas" in segs and "non-saas" in segs
