"""Post-discover scaffold: minimal HTML/CSS implementing winner tokens + signature contract."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from wde.discovery.interpret import Interpretation
from wde.discovery.territories import Territory


def _escape(s: str) -> str:
    return (
        (s or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def write_scaffold(
    root: Path,
    interp: Interpretation,
    winner: Territory,
    *,
    force: bool = False,
) -> dict[str, str]:
    """Write ``src/index.html`` + ``src/styles.css`` from the winner territory.

    Does not overwrite existing non-empty scaffold unless ``force=True``.
    Returns map of written relative paths.
    """
    root = root.resolve()
    src = root / "src"
    html_path = src / "index.html"
    css_path = src / "styles.css"

    written: dict[str, str] = {}
    if not force:
        if html_path.is_file() and html_path.stat().st_size > 50:
            return written

    tok = winner.resolved_tokens()
    sig_id = f"{winner.id.lower()}-signature"
    title = _escape(interp.subject or "WDE Discovery Scaffold")
    action = _escape(interp.primary_action or "Get started")
    metaphor = _escape(winner.metaphor)
    signature = _escape(winner.signature_move)
    structure = _escape(winner.structure)
    mode = tok.mode

    css = f"""/* WDE discovery scaffold — compiled from territory {winner.id} */
/* palette_role: {winner.palette_role} */
:root {{
  --wde-bg: {tok.background};
  --wde-surface: {tok.surface};
  --wde-text: {tok.text};
  --wde-muted: {tok.muted};
  --wde-border: {tok.border};
  --wde-accent: {tok.accent};
  --wde-success: {tok.success};
  --wde-danger: {tok.danger};
  --wde-font-display: "{tok.display_font}", Georgia, serif;
  --wde-font-body: "{tok.body_font}", system-ui, sans-serif;
  --wde-font-mono: "{tok.mono_font}", ui-monospace, monospace;
  --wde-radius-board: {tok.radius_board};
  --wde-radius-control: {tok.radius_control};
  --wde-grid: {tok.grid_base};
}}

*, *::before, *::after {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{
  margin: 0;
  min-height: 100vh;
  background: var(--wde-bg);
  color: var(--wde-text);
  font-family: var(--wde-font-body);
  font-size: 15px;
  line-height: 1.5;
}}

.wde-shell {{
  max-width: 1100px;
  margin: 0 auto;
  padding: 48px 24px 80px;
}}

.wde-eyebrow {{
  font-family: var(--wde-font-mono);
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--wde-muted);
  margin: 0 0 16px;
}}

h1 {{
  font-family: var(--wde-font-display);
  font-weight: 500;
  font-size: clamp(2.25rem, 5vw, 4rem);
  line-height: 1.05;
  margin: 0 0 16px;
  max-width: 18ch;
}}

.wde-lede {{
  color: var(--wde-muted);
  max-width: 42ch;
  margin: 0 0 32px;
}}

/* Signature gesture — machine contract selector required */
[data-wde-signature="{sig_id}"] {{
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-height: 48px;
  min-width: 200px;
  padding: 12px 28px;
  border: 1px solid var(--wde-border);
  border-radius: var(--wde-radius-control);
  background: var(--wde-text);
  color: var(--wde-bg);
  font-family: var(--wde-font-mono);
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  text-decoration: none;
  cursor: pointer;
  transition: transform 150ms ease, background 150ms ease, border-color 150ms ease;
}}

[data-wde-signature="{sig_id}"]:hover,
[data-wde-signature="{sig_id}"].is-active {{
  background: var(--wde-accent);
  border-color: var(--wde-accent);
  color: var(--wde-bg);
  transform: translateY(-1px);
}}

[data-wde-signature="{sig_id}"] .wde-sig-state {{
  font-variant-numeric: tabular-nums;
  opacity: 0.85;
}}

.wde-rail {{
  margin-top: 64px;
  border-top: 1px solid var(--wde-border);
  padding-top: 24px;
  display: grid;
  gap: 12px;
}}

.wde-rail-item {{
  display: grid;
  grid-template-columns: 48px 1fr;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid var(--wde-border);
  font-family: var(--wde-font-mono);
  font-size: 12px;
}}

.wde-rail-item span:first-child {{ color: var(--wde-muted); }}

.wde-meta {{
  margin-top: 48px;
  padding: 16px;
  background: var(--wde-surface);
  border: 1px solid var(--wde-border);
  border-radius: var(--wde-radius-board);
  font-family: var(--wde-font-mono);
  font-size: 11px;
  color: var(--wde-muted);
}}

@media (max-width: 600px) {{
  .wde-shell {{ padding: 32px 16px 64px; }}
  h1 {{ font-size: 2rem; max-width: none; }}
  [data-wde-signature="{sig_id}"] {{
    width: 100%;
    justify-content: center;
  }}
}}
"""

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <link rel="stylesheet" href="./styles.css" />
</head>
<body data-wde-mode="{mode}" data-wde-territory="{winner.id}">
  <main class="wde-shell">
    <p class="wde-eyebrow">{_escape(winner.name)} · {metaphor}</p>
    <h1>{title}</h1>
    <p class="wde-lede">{signature}</p>

    <!-- Signature contract: data-wde-signature must match DESIGN.md §11 -->
    <button
      type="button"
      class="{sig_id}"
      id="{sig_id}"
      data-wde-signature="{sig_id}"
      data-wde-behavior="state_or_content_changes_on_interaction"
      aria-label="{action}"
    >
      <span class="wde-sig-label">{action}</span>
      <span class="wde-sig-state" data-state="0">00</span>
    </button>

    <section class="wde-rail" aria-label="Structure">
      <div class="wde-rail-item"><span>01</span><span>{structure}</span></div>
      <div class="wde-rail-item"><span>02</span><span>{_escape(winner.primary_interaction)}</span></div>
      <div class="wde-rail-item"><span>03</span><span>{_escape(winner.typography)}</span></div>
    </section>

    <aside class="wde-meta">
      scaffold from territory {winner.id} · tokens {mode}-first · bg {tok.background} · accent {tok.accent}
    </aside>
  </main>
  <script>
    (function () {{
      var el = document.querySelector('[data-wde-signature="{sig_id}"]');
      if (!el) return;
      var state = el.querySelector('[data-state]');
      var n = 0;
      el.addEventListener('click', function () {{
        n = (n + 1) % 100;
        el.classList.toggle('is-active', n % 2 === 1);
        if (state) {{
          state.setAttribute('data-state', String(n));
          state.textContent = (n < 10 ? '0' : '') + n;
        }}
      }});
    }})();
  </script>
</body>
</html>
"""

    src.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html, encoding="utf-8")
    css_path.write_text(css, encoding="utf-8")
    written["src/index.html"] = "src/index.html"
    written["src/styles.css"] = "src/styles.css"

    # Machine-readable pointer for traces / agents
    meta = {
        "schema_version": "1.0",
        "territory_id": winner.id,
        "signature_id": sig_id,
        "selector": f"[data-wde-signature='{sig_id}']",
        "tokens": tok.to_dict(),
        "files": list(written.keys()),
    }
    meta_path = root / ".wde" / "discovery" / "scaffold.json"
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    written[".wde/discovery/scaffold.json"] = ".wde/discovery/scaffold.json"
    return written


def load_winner_from_research(root: Path) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    terr = root / ".wde" / "research" / "territories.json"
    interp = root / ".wde" / "research" / "interpretation.json"
    if not terr.is_file():
        return None, None
    try:
        tdata = json.loads(terr.read_text(encoding="utf-8"))
        idata = json.loads(interp.read_text(encoding="utf-8")) if interp.is_file() else {}
    except (OSError, json.JSONDecodeError):
        return None, None
    wid = (tdata.get("selection") or {}).get("winner_id")
    winner = next((t for t in tdata.get("territories") or [] if t.get("id") == wid), None)
    return winner, idata
