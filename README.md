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

### Rendering Example: NOIRÉ Maison de Beauté (§3 Luxury/Restrained Archetype)

A real end-to-end run of the V2.1 pipeline for a small-batch cosmetics house — dark-first onyx, a two-font hierarchy (Fraunces display / Inter body), a single champagne accent, and a signature self-drawing hairline. Zero generic template, and it clears every hard gate (slop **99/100**, beauty **96/100**, composition **74/100** on rendered DOM geometry):

![Hero — "Beauty kept deliberately quiet."](assets/noire-hero.png)

![Collection — four products, single-accent grid](assets/noire-collection.png)

![The Ritual — editorial rhythm and the signature champagne hairline](assets/noire-ritual.png)

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

### Web3 / crypto: which archetype, and why a flashy "wow" gets blocked

There is no dedicated crypto archetype, on purpose. For serious web3 — infrastructure, an L2, a wallet, a protocol — the right fit is **§6 Technical/Monochrome** (the Linear / Vercel register): zinc, dense, precise, tabular figures.

The reason there is no "crypto" archetype is that the usual crypto visual language *is* the AI-slop palette. The glow, the blue→purple / cyan→blue mesh gradients, the glassmorphism and the gradient-clipped text are exactly what gates B7, B8, B9 and B12 already forbid. A generic "web3" hero gets blocked by design.

That is a deliberate tension. The lazy crypto "wow" (glow + gradient + glass) is precisely the slop the skill refuses. The legitimate web3 wow is the real kind — a true 3D object (`three.js` / WebGL), disciplined scroll-driven motion (`gsap` / `ScrollTrigger`), oversized type — which `audit_wow.py` already rewards. The skill closes the clinquant shortcut and pushes you toward genuine ambition.

The verbal tells are covered too: `detect_ai_slop.py` now flags crypto-copy slop — staccato taglines ("Decentralized. Trustless. Permissionless."), and hype filler ("The future of finance", "Be your own bank", "Powered by blockchain", WAGMI). State concretely what the protocol does and for whom instead.

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

```text
# Web3 protocol / L2 — §6 Technical/Monochrome, anchor: linear.app
Build a landing page for a Layer-2 rollup that reads like precision infrastructure,
not a token launch. Zinc monochrome, mono kickers, tabular gas / latency figures. The
unexpected move: the hero is a single live three.js object — the rollup batch tree
rotating slowly — and nothing glows. No gradient, no glassmorphism, no "Decentralized.
Trustless. Permissionless." Hero dimension: motion (real 3D), not colour. Anchor on
`linear.app`, never a crypto template.
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

## What's new in V2 (beauty enhancement)

V2 replaces fragile binary regex scoring with **graduated, ratio-based measurement** and adds a true **iterative enhancement loop**.

| # | Improvement | Module | What changed |
|---|---|---|---|
| 1 | **Ratio-based scoring** | `scripts/wde_measure.py` | Shared primitives: type-scale jump ratios, whitespace ratios, graded ramps. No more 80px=40pts / 78px=0pts cliffs. |
| 2 | **Composition layer** | `scripts/audit_composition.py` | Real DOM geometry — focal dominance, whitespace breath, rhythm regularity, grid alignment. Static-CSS fallback when no render. |
| 3 | **Hardened vision judge** | `scripts/aesthetic_harden.py` | Variance across N runs (median + uncertainty flag), comparative anchors instead of absolute scores, mandatory per-dimension evidence. |
| 4 | **Anti-gaming coherence** | `scripts/audit_beauty.py` | Craft markers only count when consistent with the declared Design Dials (e.g. MOTION 8 with zero transitions is flagged). No-op without a brief. |
| 5 | **Calibration corpus** | `references/calibration_corpus.json` | Labeled reference designs as comparison anchors; `calibrate_against_corpus()` turns A-vs-B verdicts into a score band. |
| 6 | **Two-axis WOW** | `scripts/audit_wow.py` | Ambition × execution (not additive) + graded W1 — diagnoses "ambitious but botched" vs "timid but clean". |
| 7 | **Refinement loop** | `scripts/refine_loop.py` | measure → prioritise by leverage → checkpoint to `.refine-log.json` → detect convergence / plateau / regression / max-iter. Turns the validator into an enhancer. |

All V2 changes are **backward compatible** — the existing JSON contracts and 382 prior tests are preserved; V2 adds 48 new tests (430 total).

---

## Craft references (vendored from open-design)

V2.1 vendors the **brand-agnostic craft layer** of
[`nexu-io/open-design`](https://github.com/nexu-io/open-design) (Apache-2.0,
pinned at `009ff65`) into `references/craft/`. These are dense, human-maintained
craft guides — typography, color, motion discipline, **Laws of UX**, state
coverage, form validation, accessibility baseline, RTL/bidi — that enrich the
agent's reference set (Pillar 2) without overlapping getdesign.

> **What is *not* vendored, on purpose:** open-design's per-brand
> `design-systems/`. web-design-enhancer-pro already sources brand references
> **live** via `getdesign` (Pillar 1, kept fresh by `sync_references.py`);
> snapshotting 150 brands would duplicate that and go stale.

| Vendored | Role |
|---|---|
| `references/craft/*.md` | Brand-agnostic craft knowledge (typography, color, UX laws, a11y, RTL, states, forms, motion) |
| `references/craft/anti-ai-slop.md` | **Source of truth** for `detect_ai_slop.py` — the default-AI indigo palette is mirrored as `CANON_DEFAULT_INDIGO` and kept in lock-step by `tests/test_anti_slop_canon_sync.py` |

Attribution lives in `NOTICE`, `LICENSES/open-design-APACHE-2.0.txt`, and
`references/craft/ATTRIBUTION.md`. A `references/craft/_manifest.txt` +
the documented re-sync snippet keep the vendored copy reproducible against a
pinned commit. This integration also hardened the detector itself: `detect_ai_slop.py`
now forces UTF-8 stdout so the indigo→violet gradient message can no longer crash
a real run on a Windows cp1252 console.

## FAQ

### What is web-design-enhancer-pro?

web-design-enhancer-pro is an open-source AI skill that eliminates generic "AI slop" in web design and enforces premium UI/UX. It automatically validates, blocks, and fixes generic AI model outputs before delivery, on both web and native mobile, through a sequence of automatic quality gates.

### How is it different from a normal AI design prompt?

By default, almost every AI generates the same website: a dark hero, a blue-to-purple gradient, a 3-column card grid and a blue CTA. This skill makes that impossible to deliver. An anti-template gate penalises generic slop while a Beauty Score gate rewards genuine craft, and a final vision pass judges whether the rendered result actually reads as human-made.

### What do I have to do myself?

One thing the skill cannot do for you: write a short Creative Brief (CREATIVE-BRIEF.md, four fields) that sets the point of view - what the page must make someone feel, the one unexpected bet, the hero dimension, and the rule you deliberately break. Everything after the brief is automatic.

### Which frameworks and platforms does it support?

Web stacks (HTML/CSS/JS, shadcn/ui, GSAP, Three.js) and native mobile: SwiftUI, Jetpack Compose, Flutter and React Native. Native audits hard-block touch targets under 44pt and missing safe-area handling.

### Does it require an API key?

No. The vision aesthetic review runs in agent mode using the executing model's own vision, with no API key required. An optional API mode (OpenAI or Anthropic) is available if you prefer.

### What are the quality gates?

Seven automatic gates run before each delivery: AI-slop detection, 8px spacing grid, WCAG 2.1 AA contrast, design-vs-code drift, accessibility, style-uniqueness (blocked above 65/100) and Beauty Score (blocked below 50/100). A mandatory rendered vision gate (gate 8) captures the live page with Playwright and cannot be bypassed.

### Is it free and open source?

Yes. It is open source on GitHub and vendors the brand-agnostic craft layer of nexu-io/open-design (Apache-2.0). It ships with 434 tests.

---

## Project structure

```
web-design-enhancer-pro/
├── SKILL.md                          # Full skill instructions
├── CHANGELOG.md                      # Version history
├── NOTICE                            # Third-party attribution (open-design, Apache-2.0)
├── LICENSES/
│   └── open-design-APACHE-2.0.txt    # Full Apache-2.0 license text
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
│   ├── visual_audit.py               # Playwright 4 breakpoints capture
│   ├── wde_measure.py                # V2 shared ratio/measurement primitives (DRY core)
│   ├── audit_composition.py          # V2 geometry layer — focal/whitespace/rhythm/alignment
│   ├── aesthetic_harden.py           # V2 vision-judge reliability harness (variance/anchors/evidence)
│   └── refine_loop.py                # V2 iterative enhancement loop (measure→prioritise→converge)
├── references/
│   ├── design-archetypes.md          # The 10 archetypes — full CSS tokens
│   ├── beauty-gestures.md            # Signature gestures + font pairings per archetype
│   ├── mobile-beauty.md              # Mobile craft & native conventions
│   ├── gsap-best-practices.md        # GSAP animations
│   ├── threejs-best-practices.md     # WebGL scenes
│   ├── calibration_corpus.json       # V2 labeled reference designs (vision-judge anchors, #5)
│   └── craft/                        # V2.1 vendored craft refs from open-design (Apache-2.0)
│       ├── anti-ai-slop.md           #   -> source of truth for detect_ai_slop.py
│       ├── typography*.md, color.md, animation-discipline.md
│       ├── laws-of-ux.md, state-coverage.md, form-validation.md
│       ├── accessibility-baseline.md, rtl-and-bidi.md
│       ├── ATTRIBUTION.md, _manifest.txt   # provenance + re-sync manifest
│       └── README.md, FUTURE_SECTIONS.md   # upstream index (informational)
├── templates/
│   ├── creative-brief-template.md    # Phase -1 point-of-view brief
│   └── design-md-template.md         # DESIGN.md skeleton
└── tests/                            # 434 tests (1 skipped)
    ├── test_audit_accessibility.py
    ├── test_audit_style_uniqueness.py
    ├── test_audit_beauty.py
    ├── test_audit_mobile.py
    ├── test_aesthetic_review.py
    ├── test_detect_domain.py
    ├── test_detect_slop_falsepos.py  # Calibration wave 3 regression suite
    ├── test_wde_measure.py           # V2 ratio primitives
    ├── test_wow_v2.py                # V2 graded W1 + two-axis wow
    ├── test_beauty_coherence.py      # V2 dial-coherence anti-gaming
    ├── test_audit_composition.py     # V2 geometry metrics
    ├── test_refine_loop.py           # V2 loop decision engine
    ├── test_aesthetic_harden.py      # V2 vision-judge harness + calibration corpus
    └── test_anti_slop_canon_sync.py  # V2.1 canon<->detector sync guard (open-design)
```

---

## Running the tests

```bash
py -m pytest tests/ -v
# 434 tests — should display 434 passed (1 skipped)
```