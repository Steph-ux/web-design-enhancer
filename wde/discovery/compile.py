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


def compile_design_md(
    interp: Interpretation,
    winner: Territory,
    receipt_paths: list[str],
) -> str:
    receipts = ", ".join(receipt_paths) if receipt_paths else "see .wde/research/"
    return f"""# DESIGN.md — Design Contract

> Compiled by WDE Creative Discovery. Catalogue of decisions for **{interp.subject}**.

---

## 0. Sources Phase 0

### 0a. Visual reference — getdesign / discovery
- **Direction**: {winner.name}
- **Metaphor**: {winner.metaphor}
- **Receipts / artifacts**: {receipts}
{_prov("phase0_visual", receipt_paths)}

### 0b. Design intelligence — UI/UX Pro Max
- **Product description**: {interp.subject} / {interp.page_kind}
- **Query**: see research receipts path_kind=promax|sector
- **Style chosen**: {winner.archetype_hint} — reject generic agency card grids
- **Antipatterns**: {", ".join(winner.anti_references)}

### 0c. Rationale
{winner.signature_move}. Motion dial ≈ {winner.motion_level}/10. Image: {winner.image_treatment}.

---

## 1. Theme & Visual Concept

- **Concept**: {winner.metaphor}
- **Keywords**: {winner.name}, {winner.palette_role}
- **Archetype**: {winner.archetype_hint}
- **Signature**: {winner.signature_move}
- **FORBIDDEN**: {", ".join(winner.anti_references)}; product-card grids; blue→purple gradients

---

## 2. Color Palette

| Role | Hex | Usage |
| :--- | :--- | :--- |
| Background | `#0A0A0A` or `#F6F1E8` | Follow territory palette role: {winner.palette_role} |
| Surface | `#141414` / `#EFE8DC` | Sections / ledger rows |
| Text | `#F5F5F5` / `#1A1A1A` | Primary type |
| Muted | `#8A8A8A` | Captions |
| Border | `#2A2A2A` | Hairlines |
| Accent | `#C4A35A` | Single status/route accent only |
| Success | `#5FA657` | Confirmation only |
| Danger | `#C44` | Errors only |

---

## 3. Typography

- {winner.typography}
- Display: wide tracking where institutional; serif only if editorial territory
- Body: readable 15–16px equivalent; no px on body if fluid

## 4. Typography Hierarchy

- **H1**: clamp large / 500–600 / tight leading — hero excess on chosen dimension
- **H2**: section titles
- **P**: dense body
- **Small**: mono tracked labels

## 5. Spacing & Grid

- **Grid base**: 8px
- **Structure**: {winner.structure}
- **Radius**: 0–4px (no pill spam)

## 6. Components & States

### Buttons
- Primary: high contrast, short mono label for CTA ({interp.primary_action})
- Secondary: hairline

### Signature component
- {winner.signature_move}
- Interaction: {winner.primary_interaction}

### Motion
- Level {winner.motion_level}/10 — prefer transform/opacity; respect prefers-reduced-motion

## 7. Anti-patterns (project)

{chr(10).join(f"- {a}" for a in winner.anti_references)}
- Invented metrics / testimonials / trusted-by
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
