---
name: web-design-enhancer
description: >
  Use when building, redesigning, or validating web/UI against a DESIGN.md
  contract; when landing pages or product UI risk generic AI slop; when a live
  page needs visual QA before delivery. Not for pure backend, pure copywriting,
  or Figma-only work with no implementation.
---

# Web Design Enhancer

Enforces a design contract and blocks generic AI UI. **You do not invent a look from training priors** — you follow intent → anchors → lock → build → **Eyes (Playwright MCP)** → `check.py --final`.

**Core rule:** any mode that creates or changes UI is incomplete until Eyes pass (human / fluid / OK) **and** mechanical gates are green. Scripts are source of truth for bans — run them; do not re-memorize pattern codes.

## Non-bypassable pillars (read this)

Agents **cannot invent** Phase 0. `check.py --gate 0` **blocks** if:

1. You did **not** run Pillar 2: `search.py … --design-system … --save` → fresh `design-system-output*.md`
2. You did **not** run Pillar 1: `npx getdesign@latest add <brand>` → fresh `getdesign-*.md` / `brand-*.md`
3. Artifacts are **older than the brief** or **>72h old** (stale reuse = fail)
4. `DESIGN.md` §0 does not document the **real** commands

**Forbidden:** copying an old `getdesign-*.md` from another project; writing DESIGN.md from memory; claiming “Bugatti” without a fresh run.

**Script root:** resolve the skill install path once, then always call scripts from there:

```text
SKILL = ~/.claude/skills/web-design-enhancer-pro   # or this repo
python3 $SKILL/scripts/search.py "…" --design-system -p "…" --save
npx getdesign@latest add <brand>
python3 $SKILL/scripts/check.py --gate 0
```

Show command output in the session. Presence of a file without a run = bypass = blocked.

## Modes

| Mode | Load first | Done when |
|------|------------|-----------|
| `greenfield` | `references/workflows/01-intent.md` | Eyes + `check.py --final --code … --url …` green |
| `contract` | `references/workflows/01-intent.md` then `02-contract.md` | `check.py --gate 0` and `--gate 1` green (no code) |
| `implement` | `references/workflows/03-implement.md` | Eyes + `--final --url` green |
| `audit-fix` | `references/workflows/04-gates.md` | Fix loop ≤3 + re-Eyes + `--final` green |
| `vision-only` | `references/vision-playwright.md` | Eyes rubric + artifacts under `./audit-results/` |

Pick one mode from the user request. If unclear, use `greenfield`.

## Greenfield checklist (default)

1. **Intent** — fill `CREATIVE-BRIEF.md` from `templates/creative-brief-template.md` (all fields: Emotional Intent, Unexpected Thing, Hero Dimension, Broken Rule + because, Design Read, Design Dials, Cross-Domain Steal). Load: `references/workflows/01-intent.md`.
2. **Craft aim** — name archetype + 2–3 gestures from `references/beauty-gestures.md` before any code.
3. **Contract** — pillars + DESIGN.md. Load: `references/workflows/02-contract.md`. Run `python3 scripts/check.py --gate 0` then `--gate 1`.
4. **Lock** — `structural-lock.md` (≥3 decisions). Run `--gate 2`. Declare stack + scope + breakpoints.
5. **Build** — Load: `references/workflows/03-implement.md`. Implement only from DESIGN.md + gestures.
6. **Eyes (mandatory)** — Load: `references/vision-playwright.md`. Playwright MCP navigate/resize/screenshot/snapshot/console; then `visual_audit.py` + `audit_layout.py`; write non-self `aesthetic-verdict.json`.
7. **Final** — `python3 scripts/check.py --final --code <path> --url <url>` (add `--wow` for brand/marketing landings). Load: `references/workflows/04-gates.md` if red.
8. **Fix** — max 3 iterations; re-Eyes after any UI change. Then stop and report if still red.

## Red flags — STOP

- Code before gate 2 green
- “Done” without fresh `./audit-results/` (MCP screenshots + `audit_report.json` + `aesthetic-verdict.json`)
- No 375px capture
- `reviewer: self` / empty `memorable_idea`
- Skipping getdesign or design-system-output
- Tempted to skip → read `references/rationalizations.md`

## Stack branch (before code)

- **Vanilla HTML/CSS/JS** → CSS custom properties from DESIGN.md only
- **React / Next.js** → shadcn/ui preferred for primitives, or justified design-system components; Tailwind spacing multiples of 8

## Commands (canonical)

Use **`$SKILL/scripts/…`** (skill install), not a random copy of the project.

```bash
# Phase 0 — BOTH pillars (must run; must be fresh)
python3 $SKILL/scripts/search.py "<product>" --design-system -p "<Project>" --save
npx getdesign@latest add <brand>          # re-run even if an old getdesign-*.md exists

python3 $SKILL/scripts/check.py --gate 0  # fails if pillars stale vs CREATIVE-BRIEF
python3 $SKILL/scripts/check.py --gate 1
python3 $SKILL/scripts/check.py --gate 2  # lock must match code if code exists
python3 $SKILL/scripts/visual_audit.py --url http://localhost:3000 --output ./audit-results
python3 $SKILL/scripts/audit_layout.py --url http://localhost:3000 --json
python3 $SKILL/scripts/eyes_checklist.py --audit-output ./audit-results
python3 $SKILL/scripts/check.py --final --code ./src --url http://localhost:3000
python3 $SKILL/scripts/check.py --final --code ./src --url http://localhost:3000 --wow
```

## Open when

| Need | File |
|------|------|
| Brief fields | `templates/creative-brief-template.md` |
| DESIGN.md skeleton | `templates/design-md-template.md` |
| Gestures / fonts | `references/beauty-gestures.md` |
| Archetypes | `references/design-archetypes.md` |
| Eyes MCP protocol | `references/vision-playwright.md` |
| Gate map / fix loop | `references/workflows/04-gates.md` |
| Skip excuses | `references/rationalizations.md` |
| Craft canon (indigo) | `references/craft/anti-ai-slop.md` |
| Run bans | `python3 scripts/detect_ai_slop.py --design DESIGN.md --code . --json` |
