# Workflow 03 — Implement (Phase 2)

## Purpose
Build only from a locked contract + named craft. Tokens without gestures fail later gates.

## Hard stop
No code until gate 2 is green. Do not claim delivery here — that is Eyes + `04-gates.md`.

## Recipe (order is mandatory)

1. **Quote craft before code** — open `references/beauty-gestures.md`. Name the archetype and 2–3 signature gestures you will implement (write them in the session / lock notes). Archetype alone is not a gesture.

2. **Structural lock** — create project-root `structural-lock.md` with **≥3 numbered decisions** pulled from `DESIGN.md` (cite `§N` where possible). No placeholders like `[A | B]`.

```text
Structural lock — decisions from DESIGN.md:
1. Card structure: surface-card bg, 8px radius, 24px padding (§6)
2. Section pattern: full-bleed hero, 120px vertical rhythm, asymmetric media (§1)
3. Primary button: filled brand accent, 4px radius, 44px min height (§6)
```

3. **Validate lock** — `python3 scripts/check.py --gate 2`  
   Must pass before any implementation files.

4. **Stack branch** (declare once, then follow):
   - **Vanilla HTML/CSS/JS** → CSS custom properties from DESIGN.md only; no shadcn mandate.
   - **React / Next.js** → shadcn/ui preferred for primitives, **or** justified design-system components; Tailwind spacing multiples of 8.

5. **Implement tokens + gestures** — colors, type, spacing **and** the quoted gestures (not tokens alone). Layout and components must match the structural lock.

6. **Motion** — GSAP only if the brief / DESIGN.md requires orchestration. Load `references/gsap-best-practices.md`. Prefer CSS for simple transitions.

7. **Stop before “done”** — when UI is ready to review:
   1. Eyes protocol → `references/vision-playwright.md` (Playwright MCP + mechanical artifacts).
   2. Final gates + fix loop → `references/workflows/04-gates.md`.

## Pass
Gate 2 green before code; build matches DESIGN.md + lock + gestures; no delivery claim without Eyes and `--final`.
