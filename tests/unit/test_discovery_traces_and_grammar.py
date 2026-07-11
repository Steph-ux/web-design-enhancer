"""P5 traces + P6 grammar diversity tests."""

from __future__ import annotations

from pathlib import Path

from wde.discovery.grammar import (
    asserts_no_universal_bugatti,
    diversity_report,
    generate_from_grammar,
    pick_divergent_triplet,
    structural_distance_territories,
)
from wde.discovery.interpret import interpret_request
from wde.discovery.orchestrator import run_discovery
from wde.discovery.territories import generate_territories, territories_are_structurally_divergent
from wde.discovery.traces import run_all_traces, run_code_trace, run_contract_trace


def test_contract_trace_passes_after_discover(tmp_path: Path):
    r = run_discovery(
        tmp_path,
        "modern premium website for a hospitality branding agency",
        try_getdesign=False,
    )
    assert r.ok, r.errors
    report = run_contract_trace(tmp_path)
    assert report.ok, [f.to_dict() for f in report.findings if not f.ok]
    assert (tmp_path / ".wde" / "discovery" / "traces.json").is_file()


def test_code_trace_soft_without_implementation(tmp_path: Path):
    run_discovery(tmp_path, "saas api product landing", try_getdesign=False)
    report = run_code_trace(tmp_path)
    assert report.ok
    assert any(f.check == "code.absent" for f in report.findings)


def test_code_trace_detects_signature_when_present(tmp_path: Path):
    r = run_discovery(
        tmp_path,
        "boutique hotel brand site",
        try_getdesign=False,
    )
    assert r.ok
    winner_id = r.selection["winner_id"]
    sig = f"{winner_id.lower()}-signature"
    src = tmp_path / "src"
    src.mkdir()
    import json

    terr = json.loads((tmp_path / ".wde" / "research" / "territories.json").read_text(encoding="utf-8"))
    w = next(t for t in terr["territories"] if t["id"] == winner_id)
    bg = (w.get("tokens") or {}).get("background") or "#0A0A0A"
    accent = (w.get("tokens") or {}).get("accent") or "#C4A35A"
    (src / "index.html").write_text(
        f'<!doctype html><html><head><meta name="viewport" content="width=device-width"></head>'
        f'<body><div class="{sig}" data-wde-signature="{sig}">Book now</div>'
        f"<style>:root{{--bg:{bg};--accent:{accent}}} "
        f"@media(max-width:600px){{body{{padding:8px}}}}</style></body></html>",
        encoding="utf-8",
    )
    code = run_code_trace(tmp_path)
    assert code.ok, [f.to_dict() for f in code.findings if not f.ok]
    payload = run_all_traces(tmp_path)
    assert payload["traces"]["render_trace"]["ok"]


def test_grammar_triplet_divergent():
    interp = interpret_request("a wine tasting room reservation site")
    territories = generate_from_grammar(interp)
    assert len(territories) == 3
    assert territories_are_structurally_divergent(territories)
    assert asserts_no_universal_bugatti(territories)
    d01 = structural_distance_territories(territories[0], territories[1])
    d02 = structural_distance_territories(territories[0], territories[2])
    d12 = structural_distance_territories(territories[1], territories[2])
    assert d01 >= 5 and d02 >= 5 and d12 >= 5


def test_grammar_different_requests_different_metaphors():
    a = generate_from_grammar(interpret_request("museum of contemporary ceramics"))
    b = generate_from_grammar(interpret_request("freight logistics operator handbook"))
    ma = {t.metaphor for t in a}
    mb = {t.metaphor for t in b}
    # Not required to be fully disjoint, but should not be identical sets
    assert ma != mb or {t.structure for t in a} != {t.structure for t in b}


def test_generate_territories_grammar_mode():
    interp = interpret_request("unknown sector quirky request xyz")
    t = generate_territories(interp, use_grammar=True)
    assert territories_are_structurally_divergent(t)
    assert all(t_.archetype_hint.startswith("grammar:") for t_ in t)


def test_diversity_across_many_sectors():
    requests = [
        "hotel boutique agency",
        "saas api metrics dashboard landing",
        "portfolio for product designer",
        "ecommerce for artisanal coffee",
        "museum exhibition site",
        "winery tasting reservations",
        "architecture studio portfolio",
        "logistics runbook product",
        "theatre company season site",
        "cartography publisher",
        "independent bookstore",
        "ceramics atelier",
        "shipping manifest tool",
        "audio label roster",
        "landscape architecture firm",
        "culinary school admissions",
        "bicycle frame builder",
        "observatory public visits",
        "letterpress print shop",
        "alpine refuge booking",
    ]
    runs = []
    for req in requests:
        interp = interpret_request(req)
        runs.append(generate_from_grammar(interp))
    rep = diversity_report(runs)
    assert rep["unique_metaphors"] >= 6
    # No single metaphor dominates more than ~40% of all slots
    assert rep["max_metaphor_share"] <= 0.45
    for territories in runs:
        assert asserts_no_universal_bugatti(territories)


def test_pick_triplet_fast():
    # Regression: must not hang on cartesian product
    t = pick_divergent_triplet(42)
    assert len(t) == 3
    assert len({x.metaphor for x in t}) >= 2


def test_playwright_render_probe_when_available(tmp_path: Path):
    """If Playwright+Chromium are installed, full render_trace must pass."""
    pytest = __import__("pytest")
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except ImportError:
        pytest.skip("playwright not installed")

    r = run_discovery(tmp_path, "boutique hotel brand site", try_getdesign=False)
    assert r.ok
    winner_id = r.selection["winner_id"]
    sig = f"{winner_id.lower()}-signature"
    src = tmp_path / "src"
    src.mkdir()
    import json

    terr = json.loads((tmp_path / ".wde" / "research" / "territories.json").read_text(encoding="utf-8"))
    w = next(t for t in terr["territories"] if t["id"] == winner_id)
    bg = (w.get("tokens") or {}).get("background") or "#0A0A0A"
    (src / "index.html").write_text(
        f"""<!doctype html>
<html><head><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body>
  <button class="{sig}" data-wde-signature="{sig}" style="padding:24px 48px;min-width:200px;min-height:48px">Book</button>
  <style>
    :root {{ --bg: {bg}; }}
    body {{ background: var(--bg); margin: 0; }}
    .{sig} {{ display:block; margin: 40px; }}
    @media (max-width: 600px) {{ .{sig} {{ margin: 16px; }} }}
  </style>
</body></html>""",
        encoding="utf-8",
    )
    from wde.discovery.traces import run_render_trace
    from wde.runners.browser_runner import run_discovery_render_probe

    probe = run_discovery_render_probe(
        root=tmp_path, target=str((src / "index.html").resolve()), signature_id=sig
    )
    if not probe.get("playwright"):
        pytest.skip(probe.get("error") or "playwright/chromium unavailable")
    report = run_render_trace(tmp_path, require_browser=True)
    assert report.ok, [f.to_dict() for f in report.findings if not f.ok]
    assert (tmp_path / ".wde" / "discovery" / "render" / "desktop-1280.png").is_file()
    assert (tmp_path / ".wde" / "discovery" / "render" / "mobile-375.png").is_file()
