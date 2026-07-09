# Workflow 04 — Gates (final map + fix loop)

## Purpose
Single gate map for README / SKILL alignment. Scripts are source of truth; this file documents order and blocking rules.

## Prerequisites
- G0 / G1 / G2 already green (`check.py --gate 0|1|2`).
- Eyes run first when UI exists: `references/vision-playwright.md` → artifacts under `./audit-results/`.

## Unified map

| ID | Tool | Blocking |
|----|------|----------|
| G0 | Phase 0 + brief + sources | yes |
| G1 | validate_design + hash | yes |
| G2 | structural-lock | yes |
| F1 | detect_ai_slop | yes |
| F1b | audit_declared_antipatterns | yes |
| F2 | audit_spacing | yes |
| F3 | validate_design final | yes |
| F4 | diff_design_vs_code | yes if `--code` |
| F5 | audit_accessibility | yes |
| F6 | audit_style_uniqueness | block if score > 65 |
| F7 | audit_beauty | block if score < 50 |
| F8 | audit_gestures | yes if < 2/3 gestures |
| F9 | visual report + aesthetic verdict | floor 62 / pass 80; self cannot authorize; need memorable_idea; reads_as ≠ ai |
| F10 | audit_layout | L1–L3 block when `--url` |
| Eyes | Playwright MCP rubric | skill-level mandatory |
| WOW | audit_wow | when `--wow` (default recommend for brand landings) |

F1–F10 (+ WOW) run via:

```bash
python3 scripts/check.py --final --code <path> --url <url>
# brand / marketing landings:
python3 scripts/check.py --final --code <path> --url <url> --wow
```

## Fix loop (max 3 iterations)

```bash
python3 scripts/detect_ai_slop.py --design DESIGN.md --code . --json
# apply fix_instruction precisely; max 3 iterations
python3 scripts/refine_loop.py --code . --design DESIGN.md --brief CREATIVE-BRIEF.md --json
python3 scripts/check.py --final --code . --url http://localhost:3000
```

After any UI change: re-Eyes (MCP + `visual_audit.py` + layout) before re-running `--final`. If still red after 3 iterations, stop and report — do not silent-ship.

## Pass
All required rows green; Eyes rubric human / fluid / OK; fresh `./audit-results/` (screenshots + `audit_report.json` + non-self `aesthetic-verdict.json`); `check.py --final` exit 0.
