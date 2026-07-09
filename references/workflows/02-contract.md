# Workflow 02 — Contract (Phase 0–1)

## Hard stop
Do not invent DESIGN.md from priors. Archetype ≠ substitute for pillars.

## Steps
1. Pillar 2: `python3 scripts/search.py "<product>" --design-system -p "<Project>" --save`
   → `design-system-output*.md`
2. Pillar 1: `npx getdesign@latest add <brand>` → `getdesign-*.md` / `brand-*.md`
   Prefer ≥1 non-SaaS anchor when possible (`data/getdesign-references.csv`).
3. Merge into project `DESIGN.md` using `templates/design-md-template.md`.
   Conflict: Pro Max wins structure; getdesign refines texture.
   Include `## 0. Sources Phase 0` with real paths (no placeholders).
4. `python3 scripts/check.py --gate 0`
5. Complete §2–§12 as required; signature gesture §11 + tensions §12.
6. `python3 scripts/check.py --gate 1` (hashes DESIGN.md into `.phase-log.json`)

## Forbidden themes
Do not freestyle bans from memory — if unsure, run gate 1 / validate_design. Known AI clichés (cyberpunk glow, grid backgrounds, glassmorphism spam, fake terminal, etc.) are blocked by validators.

## Pass
Gate 0 + gate 1 green. No code yet.
