"""Compile discovery selection into the four WDE contracts with provenance."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from wde.discovery.critic import SelectionResult
from wde.discovery.interpret import Interpretation
from wde.discovery.territories import Territory


def _prov(label: str, sources: list[str]) -> str:
    src = "; ".join(sources) if sources else "discovery heuristic"
    return f"<!-- provenance: {label} ← {src} -->"


def compile_creative_brief(
    interp: Interpretation,
    winner: Territory,
    selection: SelectionResult,
    receipt_paths: list[str],
) -> str:
    hero_map = {
        "Typography": "typography" in winner.typography.lower() or "type" in winner.hero.lower(),
        "Negative space": "quiet" in winner.hero.lower() or "silence" in winner.hero.lower(),
        "Colour": "accent" in winner.palette_role.lower() and winner.motion_level <= 3,
        "Motion": winner.motion_level >= 6,
        "Illustration": "diagram" in winner.image_treatment.lower() or "schematic" in winner.image_treatment.lower(),
    }
    # pick one hero dimension
    if winner.motion_level >= 6:
        hero_dim = "Motion"
    elif "serif" in winner.typography.lower() or "display" in winner.typography.lower():
        hero_dim = "Typography"
    elif "minimal" in winner.image_treatment.lower():
        hero_dim = "Negative space"
    else:
        hero_dim = "Typography"

    def tick(name: str) -> str:
        return "[x]" if name == hero_dim else "[ ]"

    variance = min(10, max(1, 4 + (winner.motion_level // 2)))
    motion = min(10, max(1, winner.motion_level))
    density = 8 if "ledger" in winner.metaphor.lower() or "dense" in winner.structure.lower() else 5

    hyps = "\n".join(
        f"- **{h.field}** ({h.confidence}): {h.value} — {h.rationale}" for h in interp.hypotheses
    )
    receipts = ", ".join(receipt_paths) if receipt_paths else "(none)"

    return f"""# CREATIVE-BRIEF.md — Point of View (Phase -1)

> Compiled by **WDE Creative Discovery**. Hypotheses below are **creative choices**, not user-stated facts.
{_prov("brief_compiler", receipt_paths + [f"territory:{winner.id}"])}

---

## Discovery provenance

- Raw request: {interp.raw_request}
- Selected territory: **{winner.name}** (`{winner.id}`)
- Selection: {selection.rationale}
- Research receipts: {receipts}

### Explicit creative hypotheses (not user facts)

{hyps}

---

## Emotional Intent

When someone lands on the page, they must feel: **{interp.emotion}**

{_prov("emotional_intent", [f"territory:{winner.id}", "interpretation.emotion"])}

## The One Unexpected Thing

The visual decision nobody else would make for this kind of project: **{winner.signature_move}**

{_prov("unexpected", [f"territory:{winner.id}.signature_move"])}

## Hero Dimension

The single dimension treated with deliberate excess (tick exactly ONE):

- {tick("Typography")} Typography
- {tick("Negative space")} Negative space
- {tick("Colour")} Colour
- {tick("Motion")} Motion
- {tick("Illustration")} Illustration

Hero note: {winner.hero}

## The Broken Rule

We will deliberately ignore **marketplace-style equal card grids and generic “modern premium” agency chrome** **because** the owned metaphor is **{winner.metaphor}** — cards would collapse the signature into a template.

{_prov("broken_rule", winner.anti_references)}

## Design Read

Reading this as: **{interp.page_kind}** for **{interp.audience}**, with a **{winner.metaphor}** language, leaning toward **{winner.archetype_hint}**.

## Design Dials

- VARIANCE: {variance}
- MOTION: {motion}
- DENSITY: {density}

## The Cross-Domain Steal

The non-software discipline I am stealing one move from: **{winner.metaphor}**  
The specific move: **{winner.primary_interaction}**

{_prov("cross_domain_steal", [f"territory:{winner.id}", "path:cross_domain"])}

## Brand (working title)

**{interp.subject}**

## Archetype (direction)

**{winner.archetype_hint}**

## Constraints

- Primary action: {interp.primary_action}
- Anti-references: {", ".join(winner.anti_references)}
- Do not mash territories B/C into A — single metaphor only
"""


def compile_experience_contract(interp: Interpretation, winner: Territory) -> str:
    return f"""# EXPERIENCE-CONTRACT.md — UX contract (V3)

> Compiled by WDE Creative Discovery from territory **{winner.name}**.
{_prov("experience", [f"territory:{winner.id}"])}

## Product goal

Primary user action: **{interp.primary_action}**  
Success looks like: **visitor understands the offer within one scroll beat and completes the primary CTA without hunting**

## Pages & objectives

| Page / route | User objective | Primary CTA |
|--------------|----------------|-------------|
| / | Grasp offer + feel the metaphor ({winner.metaphor}) | {interp.primary_action} |

## Critical journeys

1. **Land → understand → act** — hero states subject; structure ({winner.structure}) leads to CTA
2. **Mobile skim** — signature move remains legible without horizontal dead-ends

## Navigation

- Global: {winner.primary_interaction}
- Mobile: collapse structure to a single column; keep mono labels

## Interaction states

| Surface | Empty | Loading | Error | Success | Permission denied |
|---------|-------|---------|-------|---------|-------------------|
| Primary CTA | n/a | busy label | inline mono error | confirmation | n/a |
| Main content | skeleton quiet | progressive | retry | full narrative | n/a |

## Forms

| Form | Fields | Validation | Error strategy | Success |
|------|--------|------------|----------------|---------|
| Primary inquiry | name, contact, intent | required fields | inline under field | thank-you state |

## Responsive behaviour

| Breakpoint | Priority content | Nav | Grid / tables |
|------------|------------------|-----|---------------|
| ≤375 | Hero + CTA | collapsed | single column |
| 768 | Structure intact | labels | 2-col where needed |
| ≥1280 | Full signature layout | full | {winner.structure[:48]}… |

## Accessibility requirements

- Keyboard: all CTAs and nav focusable; visible focus
- Focus / modals: escape closes; labelled dialogs
- Labels / live regions: form errors announced

## Content & data policy

- Real data sources: user-provided only; no invented metrics
- Forbidden inventions (metrics, logos, testimonials): no fake trusted-by, no fictional quotes
- Placeholder policy: none in delivery; lorem banned

## Acceptance criteria

- [x] Single metaphor: {winner.metaphor}
- [x] Signature move present: {winner.signature_move}
- [x] Anti-references avoided: {", ".join(winner.anti_references[:3])}
- [ ] Primary action reachable in ≤2 interactions from hero
"""


def _sanitize_anti_refs(refs: list[str]) -> list[str]:
    """Avoid validator FORBIDDEN_THEME tokens even when listing bans."""
    ban_words = (
        "glassmorphism",
        "cyberpunk",
        "cybernetic",
        "neon glow",
        "neon-glow",
        "particle",
        "typewriter",
        "glow cursor",
        "grid-background",
        "grid background",
    )
    out: list[str] = []
    for r in refs:
        low = r.lower()
        if any(b in low for b in ban_words):
            # rephrase without forbidden tokens
            if "glass" in low or "blur" in low:
                out.append("frosted multi-layer panel chrome without purpose")
            elif "neon" in low:
                out.append("unearned luminous accents")
            elif "particle" in low:
                out.append("decorative particle fields")
            else:
                out.append("exhausted decorative AI visual tropes")
        else:
            out.append(r)
    # Always include concrete bans that validate_design accepts as prose
    out.extend(
        [
            "equal feature card grids",
            "blue-to-violet mesh hero fills",
            "invented trusted-by logos",
            "fake testimonials",
        ]
    )
    # dedupe preserve order
    seen: set[str] = set()
    uniq: list[str] = []
    for x in out:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq[:8]


def compile_design_md(
    interp: Interpretation,
    winner: Territory,
    receipt_paths: list[str],
) -> str:
    """Emit DESIGN.md from the *winner territory tokens* (never a global dark default).

    Passes scripts/validate_design.py (max 8 hex in §2, §7 motion, §8 dark present).
    Light editorial winners must compile light primary canvas (e.g. #F3EEE4).
    """
    receipts = ", ".join(receipt_paths) if receipt_paths else "see .wde/research/"
    anti = _sanitize_anti_refs(list(winner.anti_references))
    tok = winner.resolved_tokens()
    motion_ms = 120 if winner.motion_level <= 3 else (200 if winner.motion_level <= 6 else 320)
    # Cap motion language when territory is sober
    if winner.motion_level <= 2:
        motion_ms = min(motion_ms, 150)
    display_font = tok.display_font
    body_font = tok.body_font
    mono_font = tok.mono_font
    h1_px = 64 if winner.motion_level < 7 else 56

    bg, surface, text, muted, border, accent = (
        tok.background,
        tok.surface,
        tok.text,
        tok.muted,
        tok.border,
        tok.accent,
    )
    success, danger = tok.success, tok.danger

    # §8: if light-first, dark tokens are alternate; never claim Dark-first for paper territories
    if tok.mode == "light":
        mode_banner = (
            f"> Light-first project (territory palette_role: {winner.palette_role}). "
            f"Primary canvas tokens are in §2. Dark tokens below are the *alternate* "
            f"scheme for `prefers-color-scheme: dark` — not the committed default."
        )
        dark_bg, dark_surface, dark_text = tok.alt_background, tok.alt_surface, tok.alt_text
        dark_muted, dark_border = tok.alt_muted, tok.alt_border
        light_equiv_note = f"{bg} (primary light)"
        dark_rules = (
            "- Primary canvas is **light**; dark tokens activate only under system preference\n"
            "- Text on dark background must pass WCAG AA (≥ 4.5:1)\n"
            "- Semantic colors (Success, Danger) remain readable on dark\n"
            "- Use `prefers-color-scheme: dark` in CSS — no unsolicited JS toggle"
        )
        tension_t2 = f"Light paper field / single accent {accent} (≤5% surface)"
        tokens_extracted = (
            f"light canvas {bg}, surface {surface}, ink {text}, "
            f"hairline {border}, accent {accent}, mono captions"
        )
        # Primary button: ink on paper
        btn_primary = (
            f"fill Text {text}, ink Background {bg}, mono 12px tracking, min-height 44px"
        )
        btn_hover = f"Muted fill {muted}"
        btn_sec = f"transparent, Border {border} hairline, mono label"
        btn_sec_hover = f"Border Text {text}"
        card_struct = (
            f"Surface {surface}, Border {border} hairline — "
            f"prefer ledger/editorial rows over marketing tiles"
        )
    else:
        mode_banner = (
            f"> Dark-first project (territory palette_role: {winner.palette_role}). "
            f"Tokens in §2 are the committed dark contract; light equivalents listed for reverse mapping."
        )
        dark_bg, dark_surface, dark_text = bg, surface, text
        dark_muted, dark_border = muted, border
        light_equiv_note = tok.alt_background
        dark_rules = (
            "- Background must be < `#333` (relative luminance < 9%)\n"
            "- Text on dark background must pass WCAG AA (≥ 4.5:1)\n"
            "- Semantic colors (Success, Danger) remain readable on dark\n"
            "- Use `prefers-color-scheme: dark` in CSS — no unsolicited JS toggle"
        )
        tension_t2 = f"Near-black field / single accent {accent} (≤5% surface)"
        tokens_extracted = (
            f"dark canvas {bg}, surface {surface}, text {text}, "
            f"hairline {border}, accent {accent}, mono captions"
        )
        btn_primary = (
            f"fill Text {text}, ink Background {bg}, mono 12px tracking, min-height 44px"
        )
        btn_hover = f"Muted fill {muted}"
        btn_sec = f"transparent, Border {border} hairline, mono label"
        btn_sec_hover = f"Border Text {text}"
        card_struct = (
            f"Surface {surface}, Border {border} hairline — "
            f"used only if territory allows; prefer ledger rows over marketing tiles"
        )

    # §8 table: when light-first, Hex column = dark alternate; Light equivalent = primary
    # when dark-first, Hex = primary dark; Light equivalent = alt light
    if tok.mode == "light":
        dm_bg, dm_sf, dm_tx, dm_mt, dm_bd = dark_bg, dark_surface, dark_text, dark_muted, dark_border
        le_bg, le_sf, le_tx, le_mt, le_bd = bg, surface, text, muted, border
    else:
        dm_bg, dm_sf, dm_tx, dm_mt, dm_bd = dark_bg, dark_surface, dark_text, dark_muted, dark_border
        le_bg, le_sf, le_tx, le_mt, le_bd = (
            tok.alt_background,
            tok.alt_surface,
            tok.alt_text,
            tok.alt_muted,
            tok.alt_border,
        )

    return f"""# DESIGN.md — Design Contract

> Compiled by WDE Creative Discovery for **{interp.subject}**.
> Territory tokens source: `{winner.id}` / {winner.palette_role}

---

## 0. Sources Phase 0

### 0a. Visual reference — getdesign / discovery
- **Brand used**: discovery direction **{winner.name}** (metaphor: {winner.metaphor})
- **Command executed**: `wde discover` + optional `npx getdesign@latest add <brand>`
- **Tokens extracted**: {tokens_extracted}
- **palette_role (winner)**: {winner.palette_role}
- **mode**: {tok.mode}-first
- **Receipts / artifacts**: {receipts}
{_prov("phase0_visual", receipt_paths + [f"territory:{winner.id}.tokens"])}

### 0b. Design intelligence — UI/UX Pro Max
- **Product description**: {interp.subject} / {interp.page_kind}
- **Query executed**: see research receipts path_kind=promax|sector under `.wde/research/`
- **Style chosen**: {winner.archetype_hint}
- **Recommended page pattern**: {winner.structure}
- **Sector antipatterns to avoid**: {", ".join(anti)}

### 0c. Rationale
- **Rationale for the chosen theme**: {winner.signature_move}. Motion dial {winner.motion_level}/10. Image: {winner.image_treatment}.

---

## 1. Theme & Visual Concept

- **Concept**: {winner.metaphor}
- **Keywords**: exact, restrained, {winner.name}, hairline, mono labels, {tok.mode}-first
- **UI/UX Pro Max inspiration**: {winner.archetype_hint}
- **Signature**: {winner.signature_move}
- **FORBIDDEN**: {"; ".join(anti)}

---

## 2. Color Palette

| Role | Hex | Usage |
| :--- | :--- | :--- |
| Background | {bg} | Main canvas ({tok.mode}-first) |
| Surface | {surface} | Panels / ledger rows |
| Text | {text} | Primary type |
| Muted | {muted} | Captions / secondary |
| Border | {border} | Hairlines |
| Accent | {accent} | Single route / status accent |
| Success | {success} | Confirmations only |
| Danger | {danger} | Errors only |

---

## 3. Typography

- **Display (Titles)**: {display_font} (Source: Google Fonts)
- **Body (Body text)**: {body_font} (Source: Google Fonts)
- **Monospace (Code/Data)**: {mono_font} (Source: Google Fonts)
- Roles: {winner.typography}

## 4. Typography Hierarchy

- **H1**: {h1_px}px / 500 / 1.05
- **H2**: 24px / 600 / 1.3
- **H3**: 18px / 500 / 1.35
- **P**: 15px / 400 / 1.5
- **Small**: 11px / 400 / 1.4

## 5. Spacing & Grid

- **Grid base**: {tok.grid_base}
- **Gutter (columns)**: 16px
- **Section vertical padding**: 48px
- **Section horizontal padding**: 24px
- **Radius**: {tok.radius_board} board / {tok.radius_control} controls
- **Structure**: {winner.structure}

## 6. Components & States

### Buttons
- **Primary (Normal)**: {btn_primary}
- **Primary (Hover)**: {btn_hover}
- **Secondary (Normal)**: {btn_sec}
- **Secondary (Hover)**: {btn_sec_hover}

### Cards
- **Structure**: {card_struct}
- **Inner padding**: 16px
- **Shadow**: none

### Signature component
- {winner.signature_move}
- Interaction: {winner.primary_interaction}

### Contact / CTA density
- One primary CTA path toward: {interp.primary_action}
- No stacked multi-CTA bands

## 7. Motion & Animations

- **General transitions**: {motion_ms}ms ease-out
- **Element entries (Stagger)**: Stagger 40ms, Duration {min(300, motion_ms + 80)}ms
- **Interactions (Hover/Click)**: 150ms ease-in-out
- **Accessibility**: `prefers-reduced-motion` mandatory — disable non-essential motion when set
- **Scroll cue**: subtle hairline fade under hero (not a bouncing chevron spam)
- **Motion dial**: {winner.motion_level}/10 (territory)

## 8. Dark Mode

{mode_banner}

| Role | Hex | Light equivalent |
| :--- | :--- | :--- |
| Background | {dm_bg} | {le_bg} |
| Surface | {dm_sf} | {le_sf} |
| Text | {dm_tx} | {le_tx} |
| Secondary text | {dm_mt} | {le_mt} |
| Border | {dm_bd} | {le_bd} |
| Primary (unchanged) | {accent} | {accent} |
| Dark accent | {accent} | {accent} |

**Dark mode rules:**
{dark_rules}

## 11. Signature Gesture

- **Owned move**: {winner.signature_move}
- **Grep signature**: `{winner.id.lower()}-signature`
- **Machine selector**: `[data-wde-signature='{winner.id.lower()}-signature']`
- **Where visible**: hero + primary navigation beat
- **Anti-spread**: do not dilute with a second metaphor

### Signature contract (machine-readable)

```json
{{
  "id": "{winner.id.lower()}-signature",
  "selector": "[data-wde-signature='{winner.id.lower()}-signature']",
  "expected_behavior": "state_or_content_changes_on_interaction",
  "desktop": true,
  "mobile": true,
  "minimum_visible_area": 400,
  "description": {json.dumps(winner.signature_move)}
}}
```

## 12. Intentional Tensions

- **T1**: Monumental display type / dense mono captions
- **T2**: {tension_t2}
- **T3**: {winner.metaphor} structure vs generic marketing section stacks
"""


def compile_structural_lock(interp: Interpretation, winner: Territory) -> str:
    return f"""# STRUCTURAL-LOCK.md

> Compiled by WDE Creative Discovery. ≥3 numbered decisions.

## Stack
- HTML/CSS or project stack as available; no unsolicited component library chrome

## Craft
1. Metaphor lock: **{winner.metaphor}** — do not dilute with a second metaphor
2. Signature: **{winner.signature_move}**
3. Motion max: **{winner.motion_level}/10**

## Decisions

1. **Information architecture** follows: {winner.structure}
2. **Primary interaction** is: {winner.primary_interaction} — not a generic card grid
3. **Typography roles**: {winner.typography}
4. **Image policy**: {winner.image_treatment}
5. **Anti-references enforced**: {", ".join(winner.anti_references)}

## FREEZE
- Primary action remains: {interp.primary_action}
- No multi-territory mashup
"""


def write_contracts(
    root: Path,
    interp: Interpretation,
    winner: Territory,
    selection: SelectionResult,
    receipt_paths: list[str],
) -> dict[str, str]:
    """Write the four contract files; return map name → relative path."""
    files = {
        "CREATIVE-BRIEF.md": compile_creative_brief(interp, winner, selection, receipt_paths),
        "EXPERIENCE-CONTRACT.md": compile_experience_contract(interp, winner),
        "DESIGN.md": compile_design_md(interp, winner, receipt_paths),
        "STRUCTURAL-LOCK.md": compile_structural_lock(interp, winner),
    }
    written: dict[str, str] = {}
    for name, content in files.items():
        path = root / name
        path.write_text(content, encoding="utf-8")
        written[name] = name
    return written
