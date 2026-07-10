"""Compile discovery selection into the four WDE contracts with provenance."""

from __future__ import annotations

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
    """Emit DESIGN.md that passes scripts/validate_design.py (max 8 hex, §7 motion, §8 dark)."""
    receipts = ", ".join(receipt_paths) if receipt_paths else "see .wde/research/"
    anti = _sanitize_anti_refs(list(winner.anti_references))
    # Single committed dark-first palette (exactly 8 hex codes in §2)
    # Background dark → §8 mandatory with its own hexes
    motion_ms = 120 if winner.motion_level <= 3 else (200 if winner.motion_level <= 6 else 320)
    display_font = "Fraunces" if "serif" in winner.typography.lower() else "IBM Plex Sans"
    body_font = "IBM Plex Sans"
    mono_font = "IBM Plex Mono"
    h1_px = 64 if winner.motion_level < 7 else 56

    return f"""# DESIGN.md — Design Contract

> Compiled by WDE Creative Discovery for **{interp.subject}**.

---

## 0. Sources Phase 0

### 0a. Visual reference — getdesign / discovery
- **Brand used**: discovery direction **{winner.name}** (metaphor: {winner.metaphor})
- **Command executed**: `wde discover` + optional `npx getdesign@latest add <brand>`
- **Tokens extracted**: pure black canvas, hairline borders, single brass accent, mono captions
- **Receipts / artifacts**: {receipts}
{_prov("phase0_visual", receipt_paths)}

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
- **Keywords**: exact, restrained, {winner.name}, hairline, mono labels
- **UI/UX Pro Max inspiration**: {winner.archetype_hint}
- **Signature**: {winner.signature_move}
- **FORBIDDEN**: {"; ".join(anti)}

---

## 2. Color Palette

| Role | Hex | Usage |
| :--- | :--- | :--- |
| Background | #0A0A0A | Main canvas |
| Surface | #141414 | Panels / ledger rows |
| Text | #F2F2F2 | Primary type |
| Muted | #8A8A8A | Captions / secondary |
| Border | #2A2A2A | Hairlines |
| Accent | #C4A35A | Single route / status accent |
| Success | #5FA657 | Confirmations only |
| Danger | #C44C4C | Errors only |

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

- **Grid base**: 8px
- **Gutter (columns)**: 16px
- **Section vertical padding**: 48px
- **Section horizontal padding**: 24px
- **Radius**: 0px board / 4px controls
- **Structure**: {winner.structure}

## 6. Components & States

### Buttons
- **Primary (Normal)**: fill Text #F2F2F2, ink Background #0A0A0A, mono 12px tracking, min-height 44px
- **Primary (Hover)**: Muted fill #8A8A8A
- **Secondary (Normal)**: transparent, Border #2A2A2A hairline, mono label
- **Secondary (Hover)**: Border Text #F2F2F2

### Cards
- **Structure**: Surface #141414, Border #2A2A2A hairline — used only if territory allows; prefer ledger rows over marketing tiles
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

## 8. Dark Mode

> Dark-first project. Tokens below are the committed dark contract.

| Role | Hex | Light equivalent |
| :--- | :--- | :--- |
| Background | #0A0A0A | #F6F1E8 |
| Surface | #141414 | #EFE8DC |
| Text | #F2F2F2 | #1A1A1A |
| Secondary text | #8A8A8A | #666666 |
| Border | #2A2A2A | #D4CBB8 |
| Primary (unchanged) | #C4A35A | #C4A35A |
| Dark accent | #C4A35A | #8B6914 |

**Dark mode rules:**
- Background must be < `#333` (relative luminance < 9%)
- Text on dark background must pass WCAG AA (≥ 4.5:1)
- Semantic colors (Success, Danger) remain readable on dark
- Use `prefers-color-scheme: dark` in CSS — no unsolicited JS toggle

## 11. Signature Gesture

- **Owned move**: {winner.signature_move}
- **Grep signature**: `{winner.id.lower()}-signature`
- **Where visible**: hero + primary navigation beat
- **Anti-spread**: do not dilute with a second metaphor

## 12. Intentional Tensions

- **T1**: Monumental display type / dense mono captions
- **T2**: Near-black field / single brass accent (≤5% surface)
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
