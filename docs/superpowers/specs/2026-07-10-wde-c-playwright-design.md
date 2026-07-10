# Design: web-design-enhancer-pro — Option C + Eyes (Playwright MCP)

**Date:** 2026-07-10  
**Status:** Draft for user review  
**Goal:** Best skill packaging for **agent compliance + maximum visual quality**, with **mandatory live visual verification** via Playwright MCP (human / fluid / works).  
**Constraint:** Preserve existing scripts, tests (~452), templates, and gate semantics; transform packaging and close skip/gaming holes.

---

## 1. Problem statement

### Explicit goal
Make `web-design-enhancer-pro` the best anti-AI-slop design skill: agents produce **memorable, human-looking UI**, not merely detector-clean pages. Delivery is never claimed without **seeing** the rendered product.

### Implicit constraints
- Scripts and tests are the hard product; do not rewrite the enforcement engine from scratch.
- Skill must load and be followed under context pressure (session token limits).
- User requires **Playwright MCP** always: agent must navigate, screenshot, and judge human / fluid / OK.
- Multi-runtime friendly packaging (Claude / Grok / Codex) where possible.

### Failure mode (what “bad” looks like)
- SKILL.md too long → agent partial-reads → skips Phase −1 / pillars / Eyes.
- Prohibition-first pedagogy → zinc monochrome “valid” clone of Linear (new monoculture).
- Self-graded aesthetic 90 + forged artifacts → “DELIVERY AUTHORIZED” while page is AI slop.
- “Gates at the end” / “Playwright optional” rationalizations under user pressure.
- Docs disagree on gate count (7 vs 10 vs 1/9) → agent picks shortest path.

### Evidence (current state)
| Asset | Finding |
|--------|---------|
| `SKILL.md` | ~430–576 lines / ~6300+ words; SDO description summarizes workflow |
| `scripts/check.py` | Strong orchestrator; labels `1/9` + optional layout; numbering drift vs SKILL |
| Scripts + tests | High quality (452 passed); dual negative/positive gates |
| Phase 4 | Documents MCP Playwright but operational path is mainly `visual_audit.py` + vision on PNGs |
| Packaging | Monolith skill owns intent + design + implement + audit + vision |

---

## 2. Goals and non-goals

### Goals
1. **Compliance:** Agent cannot skip critical phases under pressure (brief → anchors → lock → build → Eyes MCP → final).
2. **Quality:** Output is memorable (POV + signature gesture + deliberate excess), not only “not indigo.”
3. **Eyes always:** Playwright MCP is part of the definition of done for any mode that produces or changes UI.
4. **Progressive disclosure:** Thin orchestrator SKILL; depth in `references/workflows/*` and scripts.
5. **Doc integrity:** One gate map; README / docs / SKILL / check.py labels aligned.
6. **Preserve engine:** Keep detectors, beauty/gestures, provenance discounts, phase-log, refine loop.

### Non-goals (this redesign)
- Replacing getdesign or UI/UX Pro Max with a new design generator.
- Auto-fixing HTML via pure regex (semantic fix stays agent-driven).
- Cryptographic chain-of-custody for every audit artifact (stretch; optional later).
- Splitting into five separately *installed* marketplace skills in v1 (optional phase 2).
- Changing aesthetic pass mark numbers unless a test proves need (keep provenance floors).

---

## 3. Design principles

1. **Recipe first, bans in scripts** — Positive craft (brief, archetype gestures, structural lock) leads; ban catalogs live in `detect_ai_slop.py` / craft canon, not in always-loaded SKILL body.
2. **Orchestrator skill, specialist refs** — One installable skill; progressive load of workflow docs.
3. **Eyes = AND not OR** — Playwright MCP (agent vision + interaction) **and** Python Playwright measurement (`visual_audit.py`, `audit_layout.py`) both required before delivery.
4. **Hard stops = exit codes + artifacts** — Soft “MUST in chat” rituals are secondary; done means files + commands green.
5. **Match form to failure** — Discipline skips → rationalization table; wrong-shaped output → recipes/checklists; detector truth → scripts.
6. **YAGNI on packaging** — Hybrid first; multi-skill install only if hybrid still fails compliance tests.

---

## 4. Target architecture

### 4.1 Package layout

```
web-design-enhancer-pro/
  SKILL.md                          # Orchestrator only (~150–220 lines)
  references/
    workflows/
      01-intent.md                  # Phase −1 Creative Brief
      02-contract.md                # Phase 0–1, gates 0/1, pillars
      03-implement.md               # Stack branch, structural lock, gestures, code
      04-gates.md                   # Unified final gate map + fix loop
    vision-playwright.md            # MCP Eyes protocol (human / fluid / OK)
    rationalizations.md             # Skip excuses → STOP rules
    # existing: beauty-gestures, archetypes, craft/, antipatterns, …
  scripts/                          # Core engine (targeted edits only)
  templates/                        # Unchanged core (brief field count aligned in docs)
  docs/                             # README gate map synced
  tests/                            # Keep + add packaging/smoke where valuable
```

### 4.2 SKILL.md responsibilities (orchestrator)

Must contain only:
- YAML `name` + **trigger-only** `description` (no workflow dump — SDO rule).
- One-line purpose.
- Mode table (greenfield / contract / implement / audit-fix / vision-only).
- Ordered checklist per mode with **one command or one ref load** per step.
- Hard-stop red flags (short list).
- Pointer: load `references/vision-playwright.md` before claiming done.
- Pointer: load `references/rationalizations.md` when tempted to skip.
- Minimal “open when” resource index (≤10 rows).

Must **not** contain:
- Full G/A/B/C ban tables (link: run detector).
- Full aesthetic panel essay (link: vision-playwright + aesthetic_review help).
- Full getdesign brand tables (link: workflow 02 + CSV).
- Giant Resources encyclopedia.

### 4.3 Description field (target)

```yaml
name: web-design-enhancer
description: >
  Use when building, redesigning, or validating web/UI against a DESIGN.md
  contract; when landing pages or product UI risk generic AI slop; when a live
  page needs visual QA before delivery. Not for pure backend, pure copywriting,
  or Figma-only work with no implementation.
```

---

## 5. Modes

| Mode | When | Required end state |
|------|------|--------------------|
| **greenfield** | New site/app UI from brief or user pitch | Brief + DESIGN.md + code + Eyes MCP + `check.py --final --url` green |
| **contract** | Design system / DESIGN.md only | Brief (if missing) + pillars + gate 0/1 green; no code |
| **implement** | DESIGN.md already valid | Structural lock + code + Eyes MCP + `--final --url` green |
| **audit-fix** | Existing code looks generic/broken | Slop/beauty/gesture fix loop (≤3) + Eyes MCP re-run + `--final` |
| **vision-only** | User has URL; wants human/fluid/OK check | Eyes MCP + mechanical visual/layout + verdict artifact; no full redesign |

**Rule:** Any mode that creates or modifies UI **ends with Eyes**. “Quick ship without Eyes” is out of scope for this skill — agent must refuse or reframe as incomplete.

---

## 6. Pipeline (greenfield reference path)

Positive order (recipe-first):

```
1. INTENT     CREATIVE-BRIEF.md (template; all required fields incl. dials + steal)
              → check brief quality (gate 0 includes audit_brief floor)
2. CRAFT AIM  Archetype + 2–3 signature gestures from beauty-gestures.md
              (state explicitly before code)
3. ANCHORS    Pillar 2 search.py --design-system --persist
              Pillar 1 npx getdesign@latest add <brand> (+ non-SaaS preferred)
4. CONTRACT   Merge → DESIGN.md → check.py --gate 0 → --gate 1
5. LOCK       structural-lock.md → check.py --gate 2
              Declare stack + scope + breakpoints
6. BUILD      Implement from contract + gestures (stack-branched)
7. EYES       Playwright MCP protocol (see §7)  ← NON-OPTIONAL
              + visual_audit.py + audit_layout.py artifacts
8. FINAL      check.py --final --code <path> --url <url> [--wow per §8]
9. FIX        If fail: JSON fix loop / refine_loop ≤3; re-Eyes if UI changed
```

Conflict resolution (unchanged): UI/UX Pro Max wins structure; getdesign refines texture.

---

## 7. Phase Eyes — Playwright MCP (mandatory)

### 7.1 Why both MCP and Python scripts

| Path | Role |
|------|------|
| **Playwright MCP** | Agent **sees** and interacts: screenshots in context, scroll, hover, console, basic flows. Answers: human? fluid? works? |
| **visual_audit.py** | Mechanical rendered DOM slop + spacing + multi-BP screenshots → `audit_report.json` |
| **audit_layout.py** | Measured overflow / grid integrity at 4 breakpoints |
| **aesthetic_review.py** | Structured verdict schema + provenance discounts for `--final` |

Delivery requires **all** of: MCP Eyes pass (agent checklist) + fresh mechanical artifacts + non-self aesthetic verdict + `check.py --final` green.

### 7.2 MCP protocol (canonical sequence)

Document fully in `references/vision-playwright.md`. Summary:

1. **Server up** — confirm live URL (default e.g. `http://localhost:3000` or project-specific).
2. **Navigate** — `playwright__browser_navigate` to URL.
3. **Breakpoints** — for each of **375×667, 768×1024, 1280×800** (1920 optional but recommended):
   - `browser_resize`
   - `browser_take_screenshot` (viewport; filename under `./audit-results/mcp/`)
   - optional fullPage hero on desktop
4. **Structure** — `browser_snapshot` (a11y tree) at mobile + desktop; note hierarchy / CTA presence.
5. **Fluidity sample** — scroll page; hover primary CTA (`browser_hover`); note jank, sticky, overflow.
6. **Console** — `browser_console_messages` level `error`; zero unexpected errors for pass.
7. **Smoke interaction** — if form/CTA exists: navigate intent, click or fill once; no crash.
8. **Human judgment** — agent (or independent-clone subagent with screenshots only) answers the Eyes rubric (§7.3) and writes `audit-results/aesthetic-verdict.json` using the existing schema from `aesthetic_review.py`.
9. **Mechanical pass** — run:
   ```bash
   python3 scripts/visual_audit.py --url <URL> --output ./audit-results
   python3 scripts/audit_layout.py --url <URL> --json
   python3 scripts/check.py --final --code <CODE> --url <URL>
   ```
10. **Loop** — any fail → fix → re-Eyes (MCP + mechanical) ≤ **3** iterations → hard stop to human.

If Playwright MCP is unavailable in the runtime: agent must **not** fake Eyes. Options: (a) use Python Playwright scripts + read PNG files with vision tools, and document degraded mode in verdict; (b) stop and report missing MCP. Prefer (a) only if scripts produce screenshots the agent can open; still fill Eyes rubric from real pixels.

### 7.3 Eyes rubric (agent must output explicitly)

| Axis | Pass criteria |
|------|----------------|
| **Humain** | Reads as human-designed; no AI tells (gradient soup, fake social proof, terminal cosplay, generic Inter+blue); **one named memorable idea** visible in the screenshot |
| **Fluide** | Rhythm/spacing intentional; not monotone 3-col card wall; motion restrained if present; no broken sticky/overlap |
| **OK** | No horizontal overflow; primary CTA clear; content not clipped; console errors clean; mobile usable |

All three axes must pass. One fail = no delivery claim.

### 7.4 Provenance (unchanged intent, clearer packaging)

- `reviewer: self` / unset → **cannot** authorize delivery.
- Default free path: **independent-clone** (fresh subagent, screenshots + rubric only, no brief/DESIGN.md).
- Critical launches: panel mode (`aesthetic_review.py --panel`).
- Discount tiers remain: self −8 · independent-clone −3 · independent/human 0.
- Pass mark remains as implemented in `check.py` / aesthetic_review (document actual numbers in 04-gates.md; do not invent new ones without tests).

### 7.5 Artifacts required under `./audit-results/`

| Artifact | Source |
|----------|--------|
| `mcp/*.png` (or equivalent) | Playwright MCP screenshots |
| `audit_report.json` | `visual_audit.py` |
| Breakpoint PNGs from visual_audit | `visual_audit.py` |
| `aesthetic-verdict.json` | Agent / clone / API per schema |
| Layout JSON (optional but preferred when `--url`) | `audit_layout.py --json` |

Staleness: any source newer than audit report → re-run Eyes + mechanical before `--final`.

---

## 8. Quality half (memorable, not just clean)

### 8.1 Positive craft front-door
- After brief: force **archetype + gestures** quote before code (already intended; moves to workflow 03 + orchestrator checklist).
- `beauty-gestures.md` is first hop after brief, not buried after ban lists.

### 8.2 WOW / composition defaults
- **Marketing / landing / brand sites:** `check.py --final --wow` **default recommended** in skill text (orchestrator tells agent to pass `--wow` unless brief is trust-first / public-sector / dense tool UI).
- **Trust-first / public sector / enterprise tool density:** opt-out of WOW; document in brief.
- `audit_composition.py`: recommend after layout JSON available; wire into refine_loop guidance (not necessarily hard-block v1 if false-positive risk high).

### 8.3 Type range vs deliberate excess
- Conflict: `validate_design.py` H1 28–80px vs brief “140px hero”.
- **Decision:** Allow display sizes above range when (a) Hero Dimension is Typography **and** (b) DESIGN.md §11 or Broken Rule documents the excess with “because”. Implementation: targeted `validate_design.py` exemption + tests — not a free-for-all.

### 8.4 Anti-monoculture
- Keep WARN for all-SaaS getdesign anchors in gate 0 for legitimate fintech cases.
- Orchestrator **requires** stating non-SaaS steal (Cross-Domain Steal) and prefers ≥1 non-SaaS getdesign when catalogue allows.
- Lead README/examples with NOIRÉ (non-SaaS luxury) alongside CryptoVerse (technical) so default mental model is not only Linear/Vercel.

### 8.5 Stack branching (fix contradiction)
- **Vanilla:** CSS variables from DESIGN.md; no shadcn mandate.
- **React/Next:** prefer shadcn for primitives; document “or justified design-system components” to avoid second monoculture.
- Orchestrator + workflow 03 state this as a branch, not one absolute.

### 8.6 Gesture gaming (follow-up, not v1 block)
- Longer-term: gestures scored from computed/rendered signals, not only static CSS presence.
- v1: document gaming risk; independent Eyes vision is the main counter to “dead CSS tokens.”

---

## 9. Compliance half (skip resistance)

### 9.1 Rationalization table (must live in skill path)

| Excuse | Reality |
|--------|---------|
| “Gates at the end is enough” | Gate 0/1/2 prevent improvisation; code before green gates is invalid |
| “Playwright / MCP is optional” | Eyes is definition of done for UI modes |
| “Looks fine in the HTML/JSX” | Render + resize required; HTML ≠ pixels |
| “Self aesthetic score is fine” | `reviewer: self` cannot authorize |
| “Archetype replaces getdesign” | False — pillars are mandatory for gate 0 |
| “User said ship fast” | Deliver incomplete openly, or finish Eyes; skill does not authorize silent skip |
| “I’ll write the brief later” | No Phase 0 without brief quality floor |

### 9.2 Red flags (STOP)
- Code written before `check.py --gate 2` green
- Claim “done” without `./audit-results` fresh artifacts
- Verdict without real screenshot paths
- No mobile (375) capture
- Invented getdesign file / empty design-system-output
- Structural lock that does not match actual layout

### 9.3 Soft vs hard
| Soft (chat) | Hard (machine) |
|-------------|----------------|
| Quote archetype in first code turn | Gate 0/1/2, `--final`, Eyes artifacts |
| Scope list | detect_ai_slop, layout L1–L3 |
| Intent narrative | audit_brief floor |

v1 does not add cryptographic phase-log; relies on exit codes + artifact freshness already in check.py.

---

## 10. Unified gate map (single source for docs)

Document in `references/workflows/04-gates.md` and sync README. Align with **implemented** `check.py --final` order:

| ID | Tool | Blocking |
|----|------|----------|
| Pre-0 | Creative brief structure + `audit_brief` | via gate 0 |
| G0 | Phase 0 sources + DESIGN.md sources section | yes |
| G1 | `validate_design.py` + DESIGN.md hash | yes |
| G2 | `structural-lock.md` | yes |
| F1 | `detect_ai_slop.py` | yes |
| F1b | `audit_declared_antipatterns.py` | yes |
| F2 | `audit_spacing.py` | yes |
| F3 | `validate_design.py` (final) | yes |
| F4 | `diff_design_vs_code.py` | yes if `--code` |
| F5 | `audit_accessibility.py` | yes |
| F6 | `audit_style_uniqueness.py` | block score > 65 |
| F7 | `audit_beauty.py` | block score < 50 |
| F8 | `audit_gestures.py` | yes (< 2/3 gestures) |
| F9 | visual report + aesthetic verdict | yes |
| F10 | `audit_layout.py` | yes L1–L3 when `--url` |
| Eyes | Playwright MCP rubric (skill-level) | yes before claim done |
| WOW | `audit_wow.py` | when `--wow` / default per §8.2 |

Update `check.py` print labels from `1/9` to reflect F1–F10 + 1b for operator clarity (cosmetic, tests updated if they snapshot strings).

---

## 11. Implementation plan outline (for writing-plans after approval)

### Sprint A — Packaging (no behavior change to detectors)
1. Rewrite `SKILL.md` orchestrator (description + modes + checklist + red flags).
2. Add `references/workflows/01–04.md`, `vision-playwright.md`, `rationalizations.md`.
3. Move ban encyclopedia out of SKILL (delete duplication; point to scripts).
4. Sync `README.md` + `docs/README.md` gate map and Eyes requirement.
5. Align SKILL brief “four fields” language with template (all required fields listed).

### Sprint B — Eyes enforcement clarity
1. Codify MCP sequence + artifact paths in `vision-playwright.md`.
2. Optionally: `scripts/eyes_checklist.py` that verifies MCP screenshot dir + report + verdict exist (thin wrapper; agent still runs MCP).
3. Document degraded path when MCP missing.

### Sprint C — Quality tightening (tested)
1. H1/display range exemption when Typography hero + documented Broken Rule / §11.
2. Orchestrator defaults for `--wow` by project type.
3. Stack branch wording (vanilla vs React).
4. Optional: composition guidance in refine_loop docs.

### Sprint D — Verification of the skill itself
1. Pressure scenario: “ship landing in one shot” with skill present → must still attempt Eyes / refuse silent skip (writing-skills style).
2. Smoke: fixture page + mock or real Playwright path.
3. Full `pytest` green after any script edits.

---

## 12. Success criteria

| Criterion | Measure |
|-----------|---------|
| SKILL body size | ≤ ~220 lines / substantially under current word count; progressive refs |
| Description | Triggers only; no gate inventory |
| Agent path | Modes load correct workflow refs; greenfield ends with Eyes |
| Eyes | No delivery language without MCP (or documented degraded) + mechanical artifacts |
| Tests | Existing suite remains green; new tests for any script behavior change |
| Docs | Zero conflicting gate counts across README / SKILL / 04-gates |
| Quality | Recipe-first order; WOW guidance for brand landings; non-SaaS example prominence |

---

## 13. Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Agents still skip MCP (soft protocol) | Red flags + rationalizations + optional `eyes_checklist.py` + `--final` still needs artifacts |
| Token cost of screenshots | Cap breakpoints to 3 required; fullPage only hero; independent-clone for judgment |
| False confidence from MCP alone | AND with layout + slop + beauty gates |
| Over-thin SKILL loses force | Hard stops + rationalizations + “load vision-playwright before done” |
| Type exemption abused | Requires hero dimension + explicit because; tested |
| Hybrid not enough | Phase 2: extract installable sub-skills (intent / validate / vision) |

---

## 14. Decisions log

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Packaging | Hybrid conductor + specialist refs | Best C score without multi-install complexity |
| User success criteria | C (compliance + quality) | Explicit |
| Visual verification | Playwright MCP always + scripts | User requirement; AND model |
| Multi-skill install v1 | No | YAGNI; optional later |
| Engine rewrite | No | Preserve 452 tests / scripts |
| WOW | Default recommend for brand landings | Quality half of C |
| Ban lists in SKILL | Remove | Progressive disclosure; scripts are SoT |

---

## 15. Spec self-review

| Check | Result |
|-------|--------|
| Placeholders TBD | None intentional; pass marks “as implemented” deferred to 04-gates for exact numbers |
| Internal consistency | Eyes AND scripts; modes share same hard end; recipe-first matches §3 |
| Scope | Single redesign of packaging + targeted quality/compliance; engine preserved |
| Ambiguity | “MCP unavailable” has degraded path; WOW opt-out criteria named |
| Contradictions | Vanilla vs shadcn resolved via stack branch |

---

## 16. Out of scope follow-ups (backlog)

- Multi-skill marketplace split.
- Cryptographic artifact signing.
- Rendered (computed style) gesture detection.
- Hard-block pure-SaaS anchors for non-fintech categories (needs product policy).
- Auto-start dev server orchestration inside check.py.

---

## 17. Approval gate

**User review required** before implementation plan (`writing-plans`) and code changes.

Approve with:
- “Spec OK” → proceed to implementation plan
- “Change X” → revise this doc first
- “Start packaging only” → Sprint A only
