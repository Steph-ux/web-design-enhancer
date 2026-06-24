"""
tests/test_detect_slop_recall.py

Recall (true-positive) regression guard for detect_ai_slop.py — the counterpart
to test_detect_slop_falsepos.py. Fills the previously-missing "test-recall" gap:
the suite checked a couple of false-positive classes but never measured that the
detector actually CATCHES slop end-to-end through the file-dispatch pipeline.

Two contracts:
  1. Every in-distribution (ID) sample MUST be detected (ratchet at 100%). A miss
     here is a dead/broken pattern — a real bug.
  2. Out-of-distribution (OOD) recall must not regress below a documented floor.
     Raise OOD_FLOOR as coverage improves; never lower it.

Plus two pinned regression tests for the specific bugs found by measurement:
  - slop-picsum-protocol     (A6 `.{0,4}` killed real https:// URLs)
  - slop-uppercase-class-quote (uppercase-CTA-class was double-quote-only)
"""
import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(_SCRIPTS))

from measure_recall import CORPUS, detect_one  # noqa: E402


_ID = [c for c in CORPUS if c[1] == "ID"]
_OOD = [c for c in CORPUS if c[1] == "OOD"]

# OOD coverage floor. Measured baseline before coverage work = 3/20 = 15%.
# This is a RATCHET: raise it as patterns are added, never lower it.
# Progression: 15% -> 45% (CSS B9-B12) -> 80% (HTML copy-slop C1-C7).
# The 4 remaining OOD misses are geometric/structural (rounded-shadow-card,
# feature-grid-3col, generic-spacing, hover-lift-card) and are already covered
# end-to-end by audit_layout L6-L9, so the isolated detector floor caps here.
OOD_FLOOR = 0.80


@pytest.mark.parametrize("sample", _ID, ids=[c[0] for c in _ID])
def test_every_in_distribution_sample_is_detected(sample):
    sample_id, _group, ext, content, human = sample
    detected, fired = detect_one(ext, content)
    assert detected, (
        f"ID MISS — claimed pattern does not fire end-to-end: "
        f"{sample_id} ({human}). Dead/broken pattern."
    )


def test_out_of_distribution_recall_meets_floor():
    hits = sum(1 for (_id, _g, ext, content, _h) in _OOD if detect_one(ext, content)[0])
    recall = hits / len(_OOD)
    assert recall >= OOD_FLOOR, (
        f"OOD recall regressed: {hits}/{len(_OOD)} = {recall:.0%} < floor {OOD_FLOOR:.0%}"
    )


# --- Pinned regression: the two specific bugs surfaced by measurement ---------

def test_picsum_with_real_protocol_url_is_detected():
    """A6 must catch real placeholder URLs, not only protocol-less ones."""
    html = ("<head><meta name='viewport' content='x'></head>"
            "<img src=\"https://picsum.photos/seed/1/400/300\" alt='x'>")
    detected, fired = detect_one("html", html)
    assert detected, "picsum.photos with https:// must be detected (A6 length-cap bug)"


def test_uppercase_class_single_quoted_is_detected():
    """Uppercase-CTA-class must match single-quoted attributes too."""
    tsx = "export const B = () => <button className='uppercase btn'>go</button>;"
    detected, fired = detect_one("tsx", tsx)
    assert detected, "single-quoted uppercase class on a CTA must be detected"


# --- HTML copy / structure slop (C1-C7) — positive + negative per pattern -----
#
# Each soft "AI tell" is severity=1 (warning), so the discipline is strict:
# a POSITIVE proves the pattern fires, and a NEGATIVE proves a legitimate human
# page with similar-but-honest content does NOT fire. A pattern without a
# passing negative is a false-positive waiting to happen.

_HEAD = "<head><meta name='viewport' content='x'></head>"


def _fires(html, slop_type="html_copy_slop"):
    """True if the given HTML triggers at least one issue of slop_type.

    Note: _add_issue lowercases the type, so the stored value is
    'html_copy_slop' (not the HTML_COPY_SLOP constant name).
    """
    import io
    import contextlib
    import tempfile
    from pathlib import Path as _P
    from detect_ai_slop import AISloPDetector
    with tempfile.TemporaryDirectory() as td:
        (_P(td) / "index.html").write_text(html, encoding="utf-8")
        det = AISloPDetector(design_file=None, code_dir=td)
        with contextlib.redirect_stdout(io.StringIO()):
            det.run(json_mode=False)
    return any(i["type"] == slop_type for i in det.issues)


@pytest.mark.parametrize("html, label", [
    (_HEAD + "<h1>Transform Your Workflow</h1>", "C1 hero verb-phrase heading"),
    (_HEAD + "<p>Unlock the power of seamless automation.</p>", "C1 'unlock the power of'"),
    (_HEAD + "<p>The all-in-one platform for modern teams.</p>", "C2 all-in-one tagline"),
    (_HEAD + "<span>Powered by AI</span>", "C3 powered-by-AI badge"),
    (_HEAD + "<div class='hero'><a class='btn-primary'>Start</a> "
             "<a class='btn-secondary'>Demo</a></div>", "C4 dual hero CTA"),
    (_HEAD + "<div class='tier'>Starter</div><div class='tier'>Pro</div>"
             "<div class='tier'>Enterprise</div>", "C5 Starter/Pro/Enterprise"),
    (_HEAD + "<span class='badge'>New</span>", "C6 decorative New badge"),
    (_HEAD + "<ul><li>✨ Lightning fast</li></ul>", "C7 emoji li bullet"),
    (_HEAD + "<h1>Decentralized. Trustless. Permissionless.</h1>", "C8 staccato crypto tagline"),
    (_HEAD + "<h2>Fast. Secure. Decentralized.</h2>", "C8 staccato mixed crypto tagline"),
    (_HEAD + "<p>The future of finance is here.</p>", "C9 the-future-of-finance"),
    (_HEAD + "<p>Be your own bank.</p>", "C9 be-your-own-bank"),
    (_HEAD + "<span>Powered by blockchain</span>", "C9 powered-by-blockchain"),
    (_HEAD + "<p>Own your data. WAGMI.</p>", "C9 own-your-data + WAGMI"),
])
def test_html_copy_slop_positive(html, label):
    assert _fires(html), f"{label}: expected HTML_COPY_SLOP to fire"


@pytest.mark.parametrize("html, label", [
    # C1 — honest, concrete heading using none of the templated verbs
    (_HEAD + "<h1>Invoicing for freelance plumbers</h1>", "C1 concrete heading"),
    # C1 — 'power' as a real domain word (electricity), not the marketing idiom
    (_HEAD + "<p>Monitor the power draw of each circuit in real time.</p>", "C1 literal power"),
    # C2 — 'platform' used literally, not the templated tagline shape
    (_HEAD + "<p>Built on the JVM platform for predictable latency.</p>", "C2 literal platform"),
    # C3 — describing AI honestly in prose, not a decorative badge
    (_HEAD + "<p>Our ranking is improved by AI trained on your data.</p>", "C3 honest AI prose"),
    # C4 — a single, intentional primary CTA (the recommended pattern)
    (_HEAD + "<div class='hero'><a class='btn-primary'>Start now</a></div>", "C4 single CTA"),
    # C5 — pricing that does NOT use the cliché trio
    (_HEAD + "<div class='tier'>Solo</div><div class='tier'>Studio</div>"
             "<div class='tier'>Agency</div>", "C5 non-cliche tiers"),
    # C6 — a content badge that is part of real copy, not decorative chrome
    (_HEAD + "<span class='status'>In stock</span>", "C6 honest status, not badge=New"),
    # C7 — emoji mid-sentence in prose (allowed), not opening a <li>
    (_HEAD + "<li>Ships in 2 days \U0001F4E6 worldwide</li>", "C7 emoji mid-li"),
    # C8 — a real sentence containing a web3 term, not a staccato slogan
    (_HEAD + "<p>Our L2 uses a decentralized sequencer to guarantee finality.</p>", "C8 literal decentralized prose"),
    # C8 — three short Title-Case sentences with NO crypto term (generic, not crypto-copy)
    (_HEAD + "<p>Measured. Tested. Documented.</p>", "C8 generic staccato, no crypto word"),
    # C9 — blockchain described honestly in prose, not the hype tagline
    (_HEAD + "<p>We store audit logs on a private blockchain for tamper evidence.</p>", "C9 honest blockchain prose"),
])
def test_html_copy_slop_negative(html, label):
    assert not _fires(html), (
        f"{label}: HTML_COPY_SLOP false-positived on a legitimate human page"
    )