"""
tests/test_detect_slop_falsepos.py
Regression tests for two detect_ai_slop false positives found during
real-conditions validation:
  1. The viewport-meta regex flagged pages that DID have the meta
     (broken variable-length negative lookahead).
  2. The ALL_CAPS badge/button patterns were scanned with re.IGNORECASE,
     so they matched ordinary mixed-case text (any page tripped them).
Both must stay fixed while genuine ALL_CAPS / missing-viewport cases still fire.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "scripts" / "detect_ai_slop.py")

_CLEAN_HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Relay</title></head>
<body>
<header><span>relay</span><nav><a href="#">How it works</a><a href="#">Pricing</a></nav></header>
<main><h1>Structured logs, without the dashboard tax.</h1>
<p>Relay parses every line into typed events and answers questions in plain SQL.</p>
<a class="btn" href="#">Start free</a></main>
</body></html>
"""

_BAD_HTML = """<!DOCTYPE html>
<html><head><title>x</title></head>
<body><span>SYS_ACTIVE</span><button>GET STARTED NOW</button></body></html>
"""

_DESIGN = "# DESIGN.md\n## 0. Sources Phase 0\n- Brand used: Relay\n## 8. Dark Mode\ndark-bg: #0b0c0e\n"


def _run(html: str) -> list[str]:
    d = Path(tempfile.mkdtemp())
    (d / "index.html").write_text(html, encoding="utf-8")
    (d / "DESIGN.md").write_text(_DESIGN, encoding="utf-8")
    r = subprocess.run(
        [sys.executable, SCRIPT, "--design", str(d / "DESIGN.md"), "--code", str(d), "--json"],
        capture_output=True, text=True,
    )
    data = json.loads(r.stdout)
    return [v.get("message", "") for v in data.get("violations", [])]


class TestViewportFalsePositive:
    def test_clean_page_with_viewport_not_flagged(self):
        msgs = _run(_CLEAN_HTML)
        assert not any("viewport" in m.lower() for m in msgs)

    def test_page_without_viewport_is_flagged(self):
        msgs = _run(_BAD_HTML)
        assert any("viewport" in m.lower() for m in msgs)


class TestAllCapsCaseSensitivity:
    def test_mixed_case_text_not_flagged_as_allcaps(self):
        msgs = _run(_CLEAN_HTML)
        assert not any("ALL_CAPS" in m or "ALL CAPS" in m for m in msgs)

    def test_real_allcaps_button_is_flagged(self):
        msgs = _run(_BAD_HTML)
        assert any("ALL_CAPS" in m or "ALL CAPS" in m for m in msgs)

    def test_real_sys_badge_still_flagged(self):
        msgs = _run(_BAD_HTML)
        assert any("SYS_ACTIVE" in m or "system status badge" in m.lower() for m in msgs)
