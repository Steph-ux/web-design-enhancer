# web-design-enhancer-pro

**Eliminates AI bad habits in web design — and enforces beauty.** Automatically validates, blocks, and fixes generic AI model outputs before delivery, on both web and mobile.

---

## What it does

By default, every AI generates the same website: dark hero + blue→purple gradient + 3-column card grid + testimonials + blue CTA. This skill makes that **impossible to deliver**.

It forces the AI to:
1. **Choose a visual style** adapted to the project (not the default template)
2. **Validate the design** against a DESIGN.md contract
3. **Block delivery** if the result looks like a generic template — *or* if it is technically clean but flat and soulless

The two sides work together: an **anti-template** gate penalises generic slop, and a **Beauty Score** gate rewards genuine craft. A vision pass then judges whether the rendered result actually *reads as human-made*.

---

## Usage — what you do

You do **one** thing the skill cannot do for you: write a short **Creative Brief** (`CREATIVE-BRIEF.md`, four fields) that sets the point of view — what the page must make someone *feel*, the one unexpected bet, the hero dimension, the rule you deliberately break. A model can pick a style; it cannot invent intent. This is the one genuinely human-in-the-loop step.

Then you use the AI normally:

```
"Create a website for my premium cosmetics agency"
```

The skill forces the AI to respond first with:

```
Selected Archetype: §3 Luxury/Restrained
Reasoning: premium cosmetics → whitespace, thin typography,
ivory + black palette, no blue/purple gradients.
```

Then it codes with that precise style. At the end, it runs automatic validations — and if the result looks too much like a generic template, it is **blocked**.

**Everything after the brief is automatic.** You set the intent; the skill enforces the craft.

---

## Same brief, different styles

To illustrate: a "personal finance app" brief yields completely different results depending on the archetype.

| Archetype | Output | Looks like |
|---|---|---|
| *(without skill — AI default)* | Dark + blue-500 + gradient + 3 columns | Identical to 1000 other fintechs |
| **§6 Technical/Monochrome** | Zinc/monochrome, dense, tabular numbers | Linear, Vercel |
| **§3 Luxury/Restrained** | Ivory, thin typography, 0 bright colors | Private practice, Aesop |
| **§8 Data/Dashboard** | Dark background, semantic colors, charts first | Clean Grafana, Amplitude |

### Rendering Example: FC Méridien (§7 Playful/Expressive Archetype)

Here is the result generated with this skill for a football club (zero generic AI template, strong display typography, custom palette):

![Hero Section](assets/football-hero.png)

![Match Section](assets/football-match.png)

![Players Section](assets/football-players.png)

---

## The 10 archetypes

| # | Name | For which project |
|---|---|---|
| §1 | Swiss/Typographic | Agency, culture, print-to-web |
| §2 | Editorial/Magazine | Media, premium blog, newspaper |
| §3 | Luxury/Restrained | Fashion, cosmetics, premium B2C |
| §4 | Brutalist/Raw | Art, niches, cultural, avant-garde |
| §5 | Organic/Hand-crafted | Wellness, artisan, food, nature |
| §6 | Technical/Monochrome | Dev SaaS, API, CLI, B2B tools |
| §7 | Playful/Expressive | Consumer app, education, community |
| §8 | Data/Dashboard | Analytics, monitoring, BI, fintech |
| §9 | Retro/Nostalgic | Gaming, niche, culture, experimental |
| §10 | Material/Tactile | OS app, design system, productivity |

→ Full details: [`references/design-archetypes.md`](references/design-archetypes.md)

---

## Example prompts

The way you brief the model **compresses or decompresses** its output. A vague brief pulls it toward the statistical default (the SaaS template everyone has seen). A brief that imposes a point of view pushes it out of its approval distribution — that is where un-generic results live.

### Compression in action — same app, two briefs

| Brief | What you get |
|---|---|
| `Create a developer portfolio with a modern, professional design` | Dark hero, blue→purple gradient, 3-column card grid. Identical to 10 000 others. |
| `Create a developer portfolio as if Dieter Rams worked in 2026 and decided typography IS the interface. Zero illustration, zero icons. Two colours: off-white and one acid colour you must justify. The name in the hero is 140px, everything else is 15px, nothing in between.` | A page nobody has seen — because the brief forced it out of the default. |

Both produce a portfolio. Only the second is memorable. **Write the second kind.**

### Ready-to-use prompts (mapped to archetype + a verified reference)

Each prompt names a feeling, one unexpected move, and a hero dimension — the same four things `CREATIVE-BRIEF.md` will ask you to commit to (Phase -1). The reference is a real `npx getdesign@latest add <brand>` from `data/getdesign-references.csv`.

```text
# Editorial / news app — §2 Editorial, anchor: wired
Build a long-form tech journalism site. It must feel like a printed broadsheet
that happens to be on a screen — ink-dense, custom serif display, mono kickers.
The unexpected move: no hero image at all; the opening is a 96px pull-quote.
Hero dimension: typography. Anchor on `wired`, not on any SaaS blog template.
```

```text
# Personal finance dashboard — §6 Technical/Monochrome, anchor: linear.app
Build a budgeting dashboard that feels like a precision instrument, not a bank.
Zinc monochrome, tabular figures, dense but calm. The unexpected move: the only
colour in the entire UI is a single semantic green that appears nowhere except
a positive balance. Hero dimension: negative space. Anchor on `linear.app`.
```

```text
# Wellness / booking site — §5 Organic/Hand-crafted, anchor: clay
Build a spa booking site that feels like stepping onto warm stone at dawn.
Hand-drawn asymmetry, paper texture, no hard rectangles. The unexpected move:
the booking calendar is laid out as a horizontal sun-path, not a grid.
Hero dimension: illustration. Anchor on `clay` (art-directed, organic), not a
wellness-app template — and avoid every cliché (no soft gradients).
```

```text
# Indie game landing — §9 Retro/Nostalgic, anchor: nintendo-2001
Build a landing page for a roguelike that feels like a Y2K console boot screen —
brushed-metal panels, dotted carbon bars, outlined box-art type. The unexpected
move: the navigation is a fake cartridge-select carousel. Hero dimension: motion.
Anchor on `nintendo-2001`. This is the opposite of a clean modern SaaS page.
```

```text
# Football / sports club — §7 Playful/Expressive, anchor: nike
Build a site for a local football club that feels like the tunnel walk before
kickoff — loud display type, full-bleed photography, one electric accent. The
unexpected move: match scores are set in 120px condensed type as the hero, stats
before any prose. Hero dimension: typography. Anchor on `nike`, not a SaaS grid.
```

```text
# Luxury cosmetics — §3 Luxury/Restrained, anchor: ferrari (for cinematic restraint)
Build a cosmetics brand site that feels like a private atelier at closing time —
ivory, thin type, vast whitespace, zero bright colour. The unexpected move: the
product grid is a single column, one product per full viewport, scrolled slowly.
Hero dimension: negative space. Break the rule that e-commerce needs a dense grid.
```

> **The pattern:** name the feeling, the one unexpected move, the hero dimension, and the rule you break — then anchor on a non-SaaS reference. That is exactly what Phase -1 (`CREATIVE-BRIEF.md`) and Phase 0 (anti-monoculture) enforce. These prompts just front-load it.


---

## The 7 automatic validation gates

Before each delivery, the AI runs:

```bash
python3 scripts/check.py --final --code ./src
```

| Gate | Tool | What it blocks |
|---|---|---|
| 1 | `detect_ai_slop.py` | Emojis, fake stats, invented testimonials, system badges, glassmorphism, blue/purple gradients... |
| 2 | `audit_spacing.py` | Spacings that are not multiples of 8px |
| 3 | `validate_design.py` | WCAG AA contrast failures, off-spec typography, incomplete DESIGN.md |
| 4 | `diff_design_vs_code.py` | Colors/fonts/animations that drift from DESIGN.md |
| 5 | `audit_accessibility.py` | `<img>` without alt, `<button>` without type, inputs without labels, missing viewport meta... |
| 6 | `audit_style_uniqueness.py` | **Score > 65/100 = delivery blocked** — design too close to the generic template |
| 7 | `audit_beauty.py` | **Score < 50/100 = delivery blocked** — design is technically clean but flat and soulless (the positive mirror of gate 6) |

---

## Mobile & vision (incl. the mandatory rendered gate 8)

| Tool | What it does |
|---|---|
| `audit_mobile.py` | Native mobile audit (SwiftUI / Jetpack Compose / Flutter / React Native). **Hard-blocks** touch targets < 44pt (M1) and missing safe-area handling (M2). |
| `aesthetic_review.py` | Vision judgment of the rendered design — 7 dimensions including a human-vs-AI tell. Runs in `--mode agent` (the executing model uses its own vision, no API key) or `--mode api` (OpenAI / Anthropic). |
| `visual_audit.py` | Playwright capture at 4 breakpoints, feeding the vision review. |

→ References: [`references/beauty-gestures.md`](references/beauty-gestures.md) · [`references/mobile-beauty.md`](references/mobile-beauty.md)

> **The rendered visual + vision pass is now gate 8 of `check.py --final` and cannot be bypassed.** Run `visual_audit.py` against your live server to produce `audit-results/audit_report.json`, write the aesthetic verdict to `audit-results/aesthetic-verdict.json`, then run `check.py --final --code ./src --url http://localhost:PORT`. Delivery is blocked unless both artifacts exist, are fresh (re-render after any source change), and pass.

---

## Forbidden patterns (§0b)

The AI can **never** produce these elements, regardless of the project:

| Code | Pattern | Forbidden Example |
|---|---|---|
| G1 | System badges | `SYS_STATUS: ONLINE`, `NODE_STATUS` |
| G7 | Unrequested animations | `@keyframes float`, `@keyframes pulse` |
| A1 | Emojis in the UI | `✨ Our features`, `🚀 Get started` |
| A3 | Invented "trusted by" section | Fictional client logos |
| A4 | Hardcoded testimonials | `<blockquote>` with fictional "Sarah, CEO" |
| B7 | Blue→purple gradient on hero | `linear-gradient(135deg, #3B82F6, #8B5CF6)` |
| B8 | Glassmorphism everywhere | `backdrop-filter: blur()` on 3+ elements |
| C7 | `font-size` in px on `body` | `body { font-size: 16px }` — breaks WCAG zoom |
| H1 | Missing viewport meta | `<head>` without `<meta name="viewport">` |

→ Full list: [`SKILL.md §0b`](SKILL.md)

---

## Project structure

```
web-design-enhancer-pro/
├── SKILL.md                          # Full skill instructions
├── CHANGELOG.md                      # Version history
├── scripts/
│   ├── check.py                      # Orchestrator for the 7 gates (+ mobile & vision)
│   ├── detect_ai_slop.py             # AI pattern detector (G/A/B/C/D/H)
│   ├── audit_accessibility.py        # WCAG 2.1 AA
│   ├── audit_spacing.py              # 8px grid
│   ├── audit_style_uniqueness.py     # Generic AI Template detector (T1–T12)
│   ├── audit_beauty.py               # Beauty Score — positive craft floor (D1–D5)
│   ├── audit_mobile.py               # Native mobile audit (SwiftUI/Compose/Flutter/RN)
│   ├── aesthetic_review.py           # Vision aesthetic judgment (agent or API mode)
│   ├── validate_design.py            # DESIGN.md contract validation
│   ├── diff_design_vs_code.py        # Drift code vs DESIGN.md
│   ├── sync_references.py            # Keep getdesign-references.csv in sync with getdesign
│   └── visual_audit.py               # Playwright 4 breakpoints capture
├── references/
│   ├── design-archetypes.md          # The 10 archetypes — full CSS tokens
│   ├── beauty-gestures.md            # Signature gestures + font pairings per archetype
│   ├── mobile-beauty.md              # Mobile craft & native conventions
│   ├── gsap-best-practices.md        # GSAP animations
│   └── threejs-best-practices.md     # WebGL scenes
├── templates/
│   ├── creative-brief-template.md    # Phase -1 point-of-view brief
│   └── design-md-template.md         # DESIGN.md skeleton
└── tests/                            # 277 tests
    ├── test_audit_accessibility.py
    ├── test_audit_style_uniqueness.py
    ├── test_audit_beauty.py
    ├── test_audit_mobile.py
    ├── test_aesthetic_review.py
    ├── test_detect_domain.py
    └── test_detect_slop_falsepos.py  # Calibration wave 3 regression suite
```

---

## Running the tests

```bash
py -m pytest tests/ -v
# 277 tests — should display 277 passed
```
