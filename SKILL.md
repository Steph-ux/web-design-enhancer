---
name: web-design-enhancer
description: Validator and enforcer of the DESIGN.md contract. Pillar 3 of the design ecosystem — the two upstream pillars (getdesign.md real visual references + UI/UX Pro Max sectoral design intelligence) are MANDATORY before any code. Eliminates AI visual improvisation through 8 sequential validation gates (incl. a non-bypassable rendered visual + vision pass), GSAP, and a Playwright audit on 4 breakpoints.
---

# Web Design Enhancer

This skill is the **validator and enforcer** of the design ecosystem. It guarantees that implemented code respects the `DESIGN.md` contract established upstream by the two other pillars.

---

## The Ecosystem — 3 Pillars

```
┌─────────────────────────────────────────────────────────────────────┐
│  PILLAR 1 — getdesign.md           PILLAR 2 — UI/UX Pro Max         │
│                                                                     │
│  Real visual references            Per-industry design intelligence │
│  "What should my project          "Which decisions for my product   │
│   look like?"                       type?"                          │
│  (72 sites: Stripe, Vercel,        (161 rules, 67 styles,           │
│  Linear, Nike, Tesla...)            161 palettes, 57 typos)         │
│                    ↘                      ↙                         │
│                                                                     │
│              DESIGN.md  ←  the project's design contract            │
│                                                                     │
│                              ↓                                      │
│                                                                     │
│  PILLAR 3 — this skill  +  shadcn/ui  +  GSAP                       │
│  Implementation  →  Automated validation  →  Delivery               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Complete Workflow

### ⚡ Phase 0 — Design Anchoring (mandatory, before any code)

**Never create a DESIGN.md from scratch. Feed its creation from the two sources.**

> ## 🚫 HARD STOP — run BOTH upstream pillars before any DESIGN.md or code
>
> This skill (Pillar 3) only **validates**; it does **not** invent a look. Picking an archetype from `references/design-archetypes.md` is **NOT** a substitute for the pillars. Before writing a single line of DESIGN.md or code you MUST produce both artifacts:
>
> 1. **Pillar 2 — UI/UX Pro Max** (sectoral intelligence, built into this skill):
>    ```bash
>    python3 scripts/search.py "<product description>" --design-system -p "<Project>" --save
>    ```
>    → produces `design-system-output*.md` (page pattern, semantic palette, typography, sectoral antipatterns).
> 2. **Pillar 1 — getdesign.md** (real visual reference, external npx tool, needs Node):
>    ```bash
>    npx getdesign@latest add <brand>
>    ```
>    → produces a `getdesign-*.md` / `brand-*.md` reference at the project root. Verify the output filename matches that glob (rename it if getdesign writes plain `DESIGN.md`, so it is not confused with your project contract).
>
> **`check.py --gate 0` blocks** if either artifact (or the `## 0. Sources Phase 0` section in DESIGN.md) is missing. **Do not proceed to Phase 1 until `python3 scripts/check.py --gate 0` is green.** Skipping the pillars yields a design that is "technically correct but generic" — exactly the failure this ecosystem exists to prevent.

#### 0a. Visual reference — getdesign.md

Pick the site whose aesthetic is closest to the project. Download its DESIGN.md:

```bash
npx getdesign@latest add <brand>
```

Examples by project type:

| Project type | Recommended reference | Command |
|---|---|---|
| Fintech, payments | Stripe | `npx getdesign@latest add stripe` |
| Dev tool, infra | Vercel | `npx getdesign@latest add vercel` |
| Minimalist SaaS | Linear | `npx getdesign@latest add linear` |
| Workspace, docs | Notion | `npx getdesign@latest add notion` |
| Open-source, API | Supabase | `npx getdesign@latest add supabase` |
| Luxury e-commerce | Ferrari | `npx getdesign@latest add ferrari` |
| Crypto, trading | Binance | `npx getdesign@latest add binance` |
| AI, chatbot | Cursor | `npx getdesign@latest add cursor` |

The reference `DESIGN.md` is dropped at the project root. **It is inspiration, not copy-paste.** Extract the relevant tokens (colors, type, radii, shadows) that match the project.

#### 0b. Design intelligence — UI/UX Pro Max

Generate the design system adapted to the product type:

```bash
python3 scripts/search.py \
  "product description" --design-system -p "Project Name"
```

Examples:

```bash
# Banking app
python3 scripts/search.py \
  "fintech banking app" --design-system -p "MyBank"

# Wellness platform
python3 scripts/search.py \
  "beauty spa wellness booking" --design-system -p "Serenity"

# SaaS analytics dashboard
python3 scripts/search.py \
  "saas analytics dashboard" --design-system -p "DataFlow"
```

The output contains: recommended page pattern, priority style, palette, typography, key effects, and sectoral antipatterns to avoid at all costs.

#### 0c. Merge → project DESIGN.md

Create the project's `DESIGN.md` by combining both sources:

- **UI/UX Pro Max → structural decisions**: semantic palette, typography, page pattern, sectoral antipatterns
- **getdesign.md → stylistic refinement**: precise tokens, radii, shadows, density, visual micro-details

**Conflict rule**: UI/UX Pro Max wins (sectoral fit), getdesign.md refines visual texture.

Use `templates/design-md-template.md` as the skeleton.

#### 0d. Self-validation against AI clichés (mandatory before submitting DESIGN.md)

Before submitting the DESIGN.md, ask this question for **every theme decision**:

> *"Have I seen this concept on the last 1000 AI-generated portfolios/landing pages?"*

If the answer is yes → replace it with something specific to the real project.

**Themes and concepts strictly forbidden in DESIGN.md:**

| Forbidden concept | Why | Alternative |
|---|---|---|
| `dark cyberpunk` / `cybernetic` | AI cliché #1 for tech portfolios | Describe the real texture: "matte carbon surfaces with monospace type" |
| `glow cursor` | Overused effect, never requested | Remove — no equivalent needed |
| `grid background` | Present in 90% of AI dev portfolios | Solid background or very subtle radial gradient only if justified |
| `glassmorphism` | Exhausted trend, strong AI signal | `backdrop-filter` only on functional elements (modals, dropdowns) |
| `neon glow` / `neon accents` | Immediate AI cyberpunk signal | High-contrast colors without luminous `box-shadow` |
| `particle background` / `particles.js` | Overdone since 2018 | Static background or subtle CSS pattern |
| `typewriter effect` / `typed.js` | Dev portfolio cliché #1 | Static title — content speaks, not animation |
| `SYS_STATUS: ONLINE` / system badges | Unrequested AI injection | Remove — or justify functionally in the brief |
| Decorative `hero badge` ("SecOps & Admin") | Info is already in H1/H2 | Remove — badge info must live in copy |
| Lucide icons on **every** element | Generic, interchangeable icons | Custom SVG or icons limited to functional elements |
| `monitoring style (Grafana/Datadog)` as theme | Generic AI choice for sysadmin profiles | Identify what's unique to the project, not the sector |
| Operational status pills | `OPTIMAL`, `STABLE`, `CHARGE`, `OFFLINE`, `CRITICAL` in colored pills | Sentence-case status with semantic color: `<span class="status-ok">Optimal</span>` |
| Machine IDs in the UI | `ID: VALVE_01`, `ID: FAN_01` labels visible to users | Use human-readable device names from the data model |
| Fake system console | `[17:30:00] SYSTEM:`, `TELEMETRY:`, `AUTO-PILOT:`, `Console Système` section | Remove entirely — never in brief, always AI injection |
| ALL_CAPS operational labels | `PILOTE AUTOMATIQUE`, `AUTOMATIQUE (FERMÉ)`, `ACTIF - 40%` | Sentence case: `Pilote automatique`, `Automatique — fermé` |
| `font-family: monospace` on UI labels | Systematic AI signature on status/badge elements | Only on `<code>`, `<pre>`, `<kbd>`, `<samp>` — never on labels or cards |

**Golden rule:** if an element is not in the original brief, it does not belong in DESIGN.md.

Validate DESIGN.md before any code:

```bash
python3 scripts/check.py --gate 0   # Verify Phase 0 was executed
python3 scripts/check.py --gate 1   # Validate DESIGN.md
```

**If either command returns an error → do not move to Phase 1. Fix and rerun.**

`validate_design.py` automatically detects forbidden themes and blocks progress.

---

## §0 — Prerequisites and Mandatory Declarations

> **This section runs before any code.** Violating §0 invalidates all subsequent phases.

### §0a — Stack declaration (mandatory at session start)

Before writing any code, declare the stack explicitly in your first response:

- **Vanilla HTML/CSS/JS** → CSS custom properties mandatory (`--primary`, `--background`…), no framework, no Tailwind, no shadcn/ui
- **React / Next.js** → shadcn/ui **mandatory** for all UI primitives, Tailwind classes in multiples of 8 only (no arbitrary values like `p-[11px]`)

Any session producing code without having declared the stack first is invalid.

### §0b — Absolute interdictions (all stacks, no exception)

The following patterns are **never allowed** regardless of stack, project type, or any other justification. `detect_ai_slop.py` will catch them all as **errors**:

| Pattern group | Forbidden examples | Fix |
|---|---|---|
| **G1** System status badge | `SYS_ACTIVE`, `SYS_STATUS: ONLINE`, `NODE_STATUS` | Remove entirely |
| **G2** Operational status pills | `OPTIMAL`, `STABLE`, `CHARGE`, `OFFLINE` in pill/badge shape | Sentence-case text, no pill |
| **G3** Machine IDs in UI | `ID: VALVE_01`, `ID: FAN_01` visible to user | Human-readable name from data model |
| **G4** Fake system console | `[17:30:00] SYSTEM:`, `TELEMETRY:`, `Console Système` section | Remove whole section |
| **G5** ALL_CAPS operational labels | `PILOTE AUTOMATIQUE`, `AUTOMATIQUE (FERMÉ)`, `ACTIF - 40%` | Sentence case |
| **G6** Monospace on UI elements | `font-family: monospace` on labels, badges, cards | Only on `<code>` `<pre>` `<kbd>` `<samp>` |
| **G7** Unsolicited animations | `@keyframes pulse`, `pulse-ring`, `typewriter` | Remove unless in brief |
| **G8** Grid/particle backgrounds | `repeating-gradient` dot grid, `particles.js` | Solid background |
| **G9** AI buzzwords in copy | `premium`, `moderne`, `élégant`, `innovant`, `futuriste` | Precise descriptions with concrete benefits |
| **A1** Emojis in UI chrome | `✨ Nos fonctionnalités`, `🚀 Démarrer` in headings/buttons | Inline SVG or nothing |
| **A2** Hardcoded fake stats | `10,000+ utilisateurs`, `99.9% uptime` in HTML | Load from real API/CMS or remove |
| **A3** Invented trusted-by section | `<section class="trusted-by">` with made-up logos | Remove entire section — only with real partner data |
| **A4** Hardcoded testimonials | `<blockquote>` with fictitious Sarah CEO | Remove — only with real CMS/API data |
| **A5** Placeholder text | `Lorem ipsum`, `Votre texte ici` | Real project copy |
| **A6** Placeholder images | `src="https://picsum.photos/400/300"` | Real project asset |
| **B4** `!important` on layout | `margin: 0 !important`, `display: flex !important` | Fix cascade specificity — never patch with !important |
| **B5** Arbitrary z-index | `z-index: 9999`, `z-index: 99999` | Documented scale in DESIGN.md §5 |
| **B6** Hardcoded hex in CSS | `color: #3B82F6` bypassing custom properties | `color: var(--primary)` from DESIGN.md §2 |
| **B7** Blue→purple hero gradient | `linear-gradient(135deg, #3B82F6, #8B5CF6)` on `.hero` | Project-specific gradient from DESIGN.md §2 |
| **B8** Glassmorphism spam | `backdrop-filter: blur()` on 3+ non-modal elements | Reserve for modals/dropdowns only |
| **C1** `<img>` without `alt` | `<img src="..." />` — no alt attribute | `alt="description"` or `alt=""` for decorative |
| **C2** `<button>` without `type` | `<button>Envoyer</button>` | Always `type="button"` or `type="submit"` |
| **C5** `console.log` in delivered code | Debug logs left in production files | Remove or guard with `NODE_ENV === 'development'` |
| **C6** Unresolved `TODO`/`FIXME` | `// TODO: implémenter la vraie logique` | Resolve or document in README, remove inline comment |
| **C7** `font-size` in `px` on `body`/`html` | `body { font-size: 16px }` — WCAG 1.4.4 | `font-size: 100%` or `font-size: 1rem` |
| **H1** Missing `<meta viewport>` | `<head>` without `<meta name="viewport">` | Add `<meta name="viewport" content="width=device-width, initial-scale=1">` |
| **D1** Scope creep | Pages/features not in brief (Dashboard, Admin…) | Implement only what the brief explicitly specifies |
| **D2** Unauthorised renaming | Renaming `UserCard` → `ProfileCard` without instruction | Names defined in the brief are immutable |

### §0c — Mandatory deliverables before Phase 1

1. Read `DESIGN.md` in full
2. Declare the stack (see §0a)
3. Run `python3 scripts/check.py --gate 0`
4. Run `python3 scripts/check.py --gate 1`
5. Create `structural-lock.md` with 3 structural decisions (see Phase 2a)
6. Run `python3 scripts/check.py --gate 2`
7. Confirm scope: list every page/component you will implement and verify each one is in the brief
8. Confirm responsive: declare the breakpoints you will implement (minimum: 375px mobile + 1280px desktop)

No code before gate 2 is green and scope/responsive are declared.

### §0d — If `detect_ai_slop.py` returns violations

1. Read the full `--json` output
2. For each violation: apply `fix_instruction` precisely on the target file
3. Re-run: `python3 scripts/detect_ai_slop.py --design DESIGN.md --code . --json`
4. **Maximum 3 iterations** — if violations persist after 3 rounds: STOP, report to human

---

### §0e — Style Anti-Monotony Protocol (mandatory — run BEFORE writing any code)

> **Why this exists.** Every AI model defaults to the same visual template: dark hero with blue→purple gradient, Inter + Poppins fonts, 3-column card grid, glassmorphism panels, testimonials, blue CTA. The result is a site that looks identical to 10,000 others. This protocol is the only guard against it.

#### Step 1 — Choose a design archetype explicitly

Before any code, state which archetype from `references/design-archetypes.md` you are targeting. The choice must be justified by the brief.

Then open `references/beauty-gestures.md` and commit to that archetype's **signature gestures** + **validated font pairing** — the positive craft moves that lift the Beauty Score (gate 7). Avoiding clichés is not enough; you must add deliberate beauty:

| If the brief mentions… | Default archetype to consider |
|---|---|
| SaaS, API tool, developer product | §6 Technical/Monochrome OR §1 Swiss |
| Finance, insurance, legal | §3 Luxury/Restrained OR §2 Editorial |
| Wellness, food, craft, sustainability | §5 Organic/Hand-crafted |
| Creative agency, portfolio, cultural | §2 Editorial OR §4 Brutalist |
| Analytics, monitoring, data tool | §8 Data/Dashboard |
| Game, entertainment, community | §7 Playful/Expressive |
| Fashion, luxury goods, premium brand | §3 Luxury/Restrained |
| Retro/niche/experimental | §9 Retro/Nostalgic |
| Design system, product OS | §10 Material/Tactile |

You MUST quote this in your first response:
```
Archetype selected: §6 Technical/Monochrome
Reason: The brief describes a developer CLI tool — monochrome palette, dense typography, and
code-adjacent aesthetics are the closest match to real products in this space (Vercel, Linear).
```

#### Step 2 — Run the uniqueness audit before delivery

After code is written but BEFORE final gate:

```bash
python3 scripts/audit_style_uniqueness.py --path ./src
```

- **Score 0–40** → OK — continue to `check.py --final`
- **Score 41–65** → WARNING — fix flagged signals, then re-run
- **Score 66–100** → BLOCKED — design is a clone of the Generic AI Template. Do not deliver.

#### Forbidden style combinations (auto-signals of Generic AI Template)

| Signal | Code | Why blocked |
|---|---|---|
| Blue→purple gradient on `.hero` | T1 | Most recognizable AI template signature — detected in millions of outputs |
| Inter + Poppins both present | T2 | Default AI font combination — signals template thinking |
| `.testimonial-card` + `.trusted-by` | T3 | Fabricated social proof — blocks if not in brief |
| `backdrop-filter: blur()` on 3+ elements | T4 | Glassmorphism spam — over-used since 2022 |
| All 4 generic sections present | T5 | Hero+Features+Testimonials+CTA without brief justification |
| `@keyframes float` or `pulse` unsolicited | T9 | Decorative animations not in brief |
| `color: #3B82F6` hardcoded | T12 | Tailwind blue-500 as default AI primary |

#### Differentiation checklist (at least 2 must be true)

- [ ] Primary color is NOT blue, purple, or their direct derivatives
- [ ] At least ONE unusual structural element (split layout, sidebar-first, diagonal section, full-bleed type)
- [ ] Font pairing is NOT Inter+Poppins or Inter+Roboto
- [ ] Hero section does NOT have a gradient background
- [ ] Number of sections ≤ brief specification (no added sections)

---

## Phase 1 — Design Contract (the "Brain")

The final `DESIGN.md` must be complete before any code. Minimum requirements:

- **§2 Palette**: 4–8 colors with semantic roles (`Primary`, `Background`, `Text`, `Accent`, `Success`, `Danger`) — WCAG AA contrast auto-verified
- **§3 Typography**: max 2 fonts (display + body), Google Fonts only
- **§4 Type hierarchy**: sizes in ranges auto-checked by `validate_design.py` — **H1 28–80px**, H2 22–60px, H3 18–36px, **P 13–18px**, Small 11–14px
- **§5 Spacing**: all multiples of 8px
- **§6 Components**: max 3 variants per type
- **§7 Animations**: ≤ 400ms, mandatory `prefers-reduced-motion` mention
- **§8 Dark Mode**: mandatory if main background is dark — surface, secondary-text, dark-border documented
- **§9 Mobile** *(optional — mandatory if a native app is in scope)*: touch targets ≥ 44pt iOS / 48dp Android, safe areas, native units. For native targets, run `python3 scripts/audit_mobile.py --path ./<app-src>` (Phase 5, separate from `check.py --final`) and clear all M1/M2 blockers — see `references/mobile-beauty.md` for per-platform gestures
- **§10 Three.js** *(optional — mandatory if a WebGL scene is in scope)*: pixel ratio cap, dispose strategy, WebGL fallback — see `references/threejs-best-practices.md`

Validate before continuing:

```bash
python3 scripts/check.py --gate 1
```

**`check.py --gate 1` is the canonical command.** It invokes `validate_design.py` (WCAG AA, §4 ranges, §8/§9/§10) and persists the DESIGN.md SHA-256 hash to `.phase-log.json` — the gate auto-invalidates if DESIGN.md is modified.

**If the command returns an error → fix DESIGN.md. Do not write a single line of code until this gate is green.**

---

### Phase 2 — Structural Implementation (the "Body")

#### Phase 2a — Structural Decision Lock (mandatory, before any code)

> **Why this step exists.** Phase 2 below is token-level (primitives, variables, grid).
> Without an explicit structural lock first, the agent takes the path of least resistance —
> tweaking `--primary`, swapping radii, adjusting padding — and ships a design that looks
> different but is structurally identical to a generic template. The validator catches
> tokens; only the agent itself can lock structure.

Before writing the first line of code, the agent must quote, in its own response, **3 structural decisions** taken from `DESIGN.md`:

- **Mobile native target** (§9 present): quote `Primary screen pattern`, `Navigation pattern → Type`, `Primary CTA → Position`.
- **Web-only target** (§9 absent): quote `Card structure` (§6), the section pattern chosen (Hero/Features/Pricing variant in §1 or §6), and the Primary button shape from §6.

If any quoted decision is still a placeholder (`[A | B | C]` or `[Ex: ...]`), stop — the contract was not committed to. Fix DESIGN.md, rerun `check.py --gate 1`, then resume.

Format example (web-only):

```
Structural lock — decisions from DESIGN.md:
1. Card structure: `surface-card` background, hairline border, 24px padding (§6)
2. Section pattern: split-pane dashboard, left sidebar, dense header (§1)
3. Primary button: filled, 4px radius, no shadow (§6)
```

This block is the entry ticket for Phase 2 — no lock, no code.

#### Phase 2 — Token-level implementation

- **Primitives**: exclusively **shadcn/ui** components (Button, Card, Dialog, Input, Table...). Recreating these blocks from raw `div`s is forbidden.
- **Variables**: configure `globals.css` only via CSS variables defined in DESIGN.md (`--primary`, `--background`, `--radius`...).
- **Grid**: Tailwind classes in multiples of 8 only (`p-2`, `p-4`, `p-8`, `gap-4`, `gap-8`). Arbitrary values (`p-[11px]`, `mt-[13px]`) are strictly forbidden.

---

### Phase 3 — Dynamism with GSAP (the "Soul")

See `references/gsap-best-practices.md`.

- **shadcn/ui + Tailwind** handle native states (hover, focus, disabled).
- **GSAP** only for orchestration: staggered entries, scroll effects (ScrollTrigger).
- All durations respect the timings in DESIGN.md (≤ 400ms).

---

### Phase 4 — Visual Inspection (the "Eyes" via MCP Playwright) — CRITICAL

A task is never done until it has been visually inspected.

```bash
python3 scripts/visual_audit.py --url http://localhost:3000 --output ./audit-results
```

Inspects on **4 breakpoints** (375 / 768 / 1280 / 1920px). Fix immediately if:

- **AI artifacts**: emojis, stickers, decorative icons that weren't requested
- **Invented logos**: graphic placeholders (`logo-placeholder`, `your-logo`, `brandname`)
- **Wonky geometry**: spacings that aren't multiples of 8px

Validation loop: fix → rerun audit → repeat until zero defect.

#### Aesthetic review — the "is it beautiful?" judgment (vision model)

Mechanical audits cannot answer "does this look designed by a human?". After the visual audit is clean, submit the rendered screenshots to a vision model for a scored, structured verdict:

```bash
# 1. The script prints the screenshots + rubric + verdict schema:
python3 scripts/aesthetic_review.py --screenshots ./audit-results --archetype "§3 Luxury"
# 2. YOU (the vision-capable model running this skill) open those screenshots with your
#    own vision, apply the rubric, and write the verdict JSON to verdict.json.
# 3. Score it and get the gate exit code:
python3 scripts/aesthetic_review.py --verdict verdict.json
# Unsupervised pipelines may call an external model instead: --mode api --provider anthropic
```

It scores 7 dimensions an eye judges in the first seconds (first impression, hierarchy, whitespace/balance, typography, colour harmony, finish, **human-vs-AI tell**), returns an `overall_score`, a `reads_as: human|ai` flag, and ranked fixes. **Score < 60 = BLOCKED** (does not yet read as human-designed); ≥ 75 passes.

> **No API key needed by default** — the model executing this skill judges with its own vision (mode `agent`). An external vision model (`--mode api`, `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`) is only for fully-unsupervised pipelines. **`check.py --final` enforces this step as gate 8: it will not authorize delivery unless a fresh `audit_report.json` and a passing aesthetic verdict both exist** — see Phase 5.

---

### Phase 5 — Automated Validation (mandatory before delivery)

Run the final gate — it orchestrates all **8 gates** in sequence (7 static + 1 rendered visual/vision pass):

| Step | Tool | What it checks |
|---|---|---|
| 1 | `detect_ai_slop.py` | G1-G9 + A1-A6 + B4-B8 + C1-C7 + H1 + D1-D3 patterns in HTML/CSS/JS |
| 2 | `audit_spacing.py` | 8px grid violations in CSS |
| 3 | `validate_design.py` | DESIGN.md contract, WCAG AA contrast, §4 type ranges |
| 4 | `diff_design_vs_code.py` | Colors, fonts, animations match between DESIGN.md and code |
| 5 | `audit_accessibility.py` | WCAG 2.1 AA — img alt, button type, input labels, div onclick, html lang, viewport meta |
| 6 | `audit_style_uniqueness.py` | Generic AI template detection — score must be ≤ 65 |
| 7 | `audit_beauty.py` | Positive craft floor — Beauty Score must be ≥ 50 (blocks clean-but-soulless designs) |
| 8 | `visual_audit.py` + `aesthetic_review.py` | **Rendered pass (mandatory):** requires a fresh `audit_report.json` with a clean rendered DOM **and** a passing aesthetic verdict (`reads_as: human`, score ≥ pass). Blocks delivery if missing, stale, or below floor. |

```bash
python3 scripts/check.py --final --code ./src --url http://localhost:3000
python3 scripts/check.py --final --code ./src --url http://localhost:3000 --verbose   # shows fix_instructions on failure
```

> **The rendered visual + vision pass is gate 8 of `check.py --final` and cannot be bypassed.** `visual_audit.py` still runs separately (it needs a live server) to PRODUCE the evidence; `check.py --final` then REQUIRES it:
> ```bash
> # 1. render the evidence (live server, Playwright)
> python3 scripts/visual_audit.py --url http://localhost:3000 --output ./audit-results
> # 2. open the screenshots with your own vision, write the verdict to ./audit-results/aesthetic-verdict.json
> python3 scripts/aesthetic_review.py --screenshots ./audit-results --archetype "§6 Technical"
> # 3. the final gate now blocks unless both artifacts exist, are fresh, and pass:
> python3 scripts/check.py --final --code ./src --url http://localhost:3000
> ```
> Gate 8 fails (no DELIVERY AUTHORIZED) if `audit_report.json` is missing, the rendered DOM still contains slop, the report is **stale** (any source file changed after the last render), or the aesthetic verdict is missing / below floor. Default verdict path: `<audit-output>/aesthetic-verdict.json` (override with `--verdict`).

If the gate fails → **do not patch files manually**. Go to Phase 5b below.

---

### Phase 5b — Self-Correction Loop (triggered if Phase 5 fails)

When `check.py --final` reports violations, run the detector in JSON mode to get machine-readable fix instructions:

```bash
python3 scripts/detect_ai_slop.py --design DESIGN.md --code . --json
```

The output is a JSON object with a `violations` array. Each entry contains:

| Field | Content |
|---|---|
| `file` | The exact file to open |
| `type` | Violation category |
| `message` | What was detected |
| `fix_instruction` | The **exact action to perform** — no interpretation needed |

**Correction protocol — follow in order:**

1. Read the full JSON output
2. For each violation: open `file`, locate the element described in `message`, apply `fix_instruction` **precisely** — no improvisation, no scope creep beyond the instruction
3. Re-run: `python3 scripts/detect_ai_slop.py --design DESIGN.md --code . --json`
4. Repeat until `"passed": true` — **maximum 3 iterations**
5. Once `"passed": true` → re-run `python3 scripts/check.py --final --code .`

**Hard stop:** if violations persist after 3 iterations, stop. Report the unresolved violations with their `fix_instruction`. Do not deliver.

> **Why this protocol exists.** A regex-based auto-fixer would patch HTML but leave orphaned CSS rules, miss JS references, or corrupt adjacent structure. The model executing this skill has full context — it applies fixes semantically, not mechanically. The JSON output is the interface between the detector (mechanical) and the fixer (the model itself).

---

## Visual Hygiene Rules (non-negotiable)

- **Less but better**: any visual element without a clear function (border, shadow, gradient) is removed.
- **Strict 8px grid**: `p-2` `p-4` `p-6` `p-8` `gap-4` `gap-8`. Never `p-[11px]`.
- **Text logo**: if no logo asset is provided → styled text only (`font-bold tracking-tight uppercase`). Never an improvised graphic placeholder.
- **WCAG AA contrast**: text/background minimum **4.5:1**. UI elements minimum **3.0:1**.

---

## Resources

| File | Role |
|---|---|
| `templates/design-md-template.md` | DESIGN.md skeleton to fill |
| `templates/design-system.css` | Ready-to-customize CSS variables |
| `references/design-md-spec-v2.md` | Full DESIGN.md format spec |
| `references/antipatterns-guide.md` | Concrete ❌ vs ✅ examples |
| `references/beauty-gestures.md` | Per-archetype signature gestures + validated font pairings, mapped to Beauty Score dimensions (the positive recipe for gate 7) |
| `references/gsap-best-practices.md` | GSAP guide |
| `references/threejs-best-practices.md` | Three.js guide — critical WebGL antipatterns (§10) |
| `references/mobile-references.md` | Mobile UX references — open CSV index + walled sources (Mobbin / Page Flows / Screenlane) |
| `references/mobile-beauty.md` | Native signature gestures + hard rules (touch targets, safe areas, nav) per platform, mapped to mobile-audit dimensions |
| `scripts/audit_mobile.py` | Native craft + mobile gates for SwiftUI / Compose / Flutter / React Native — scores M1-M5, hard-blocks sub-min touch targets and missing safe areas |
| `data/apple-hig-patterns.csv` | 77 Apple HIG component anatomies (iOS / iPadOS / macOS / watchOS / tvOS / visionOS / CarPlay) — queryable via `--domain apple-hig` |
| `data/material-design-3-patterns.csv` | 155 Material Design 3 component anatomies, screen patterns, layout/motion/branding tokens (Android / cross-platform) — queryable via `--domain material-design-3` |
| `data/pttrns-patterns.csv` | 50 Pttrns mobile UX pattern categories with anatomy — queryable via `--domain pttrns` |
| `data/page-flows-patterns.csv` | 97 Page Flows end-to-end mobile user flows (onboarding, login, checkout, booking, cancellation, verification…) — queryable via `--domain page-flows` |
| `scripts/validate_design.py` | DESIGN.md validation + WCAG AA + §4 ranges + §10 Three.js |
| `scripts/detect_ai_slop.py` | G1-G9 + A1-A6 + B4-B5 + C1-C7 + D1-D3 antipattern detection in HTML/CSS/JS |
| `scripts/audit_spacing.py` | 8px grid audit on CSS files |
| `scripts/audit_accessibility.py` | WCAG 2.1 AA — img alt, button type, input labels, div onclick, html lang, title, empty links |
| `scripts/visual_audit.py` | Playwright visual audit — 4 breakpoints, real DOM, rendered slop detection |
| `scripts/aesthetic_review.py` | Aesthetic judgment of rendered screenshots — the agent judges with its OWN vision by default (no key); external model optional via --mode api |
| `scripts/diff_design_vs_code.py` | Diff DESIGN.md ↔ code (colors, fonts, animations) |
| `scripts/audit_beauty.py` | Beauty Score (0-100) — rewards type-scale contrast, hierarchy, signature colour, spacing rhythm, finition. Blocks below 50 |
| `.slop-ignore` | Whitelist against false positives for detect_ai_slop.py |
