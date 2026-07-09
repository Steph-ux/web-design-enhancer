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

```bash
python3 scripts/search.py "<product>" --design-system -p "<Project>" --save
npx getdesign@latest add <brand>
python3 scripts/check.py --gate 0
python3 scripts/check.py --gate 1
python3 scripts/check.py --gate 2
python3 scripts/visual_audit.py --url http://localhost:3000 --output ./audit-results
python3 scripts/audit_layout.py --url http://localhost:3000 --json
python3 scripts/eyes_checklist.py --audit-output ./audit-results
python3 scripts/check.py --final --code ./src --url http://localhost:3000
python3 scripts/check.py --final --code ./src --url http://localhost:3000 --wow
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
