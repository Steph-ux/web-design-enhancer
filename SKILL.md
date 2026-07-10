---
name: web-design-enhancer
description: >
  Use when building, redesigning, or validating web/UI with WDE V3 evidence
  orchestration; when AI agents must follow authorized next steps and cannot
  forge delivery. Not for pure backend or non-UI work.
---

# Web Design Enhancer V3

**The model proposes and implements. The orchestrator authorizes, verifies, and blocks.**

This file is the **thin skill adapter**. Do not invent gates — drive the CLI.

## Bootstrap

Prefer the short CLI (`wde` after `pip install -e .`, else `python -m wde`):

```bash
wde init --root <project>
# Vague request → Creative Discovery (receipts + 3 territories + contracts)
wde discover --root <project> --request "modern premium site for an agency"
wde status --json --root <project>
wde next --root <project>
```

Follow only `next_action`. Deeper refs:

| Need | Path |
|------|------|
| Full adapter rules | `adapters/generic/ADAPTER.md` |
| V3 docs | `docs/V3.md` |
| Plan | `docs/superpowers/specs/2026-07-10-wde-v3-plan.md` |
| Brief / UX / design templates | `templates/` |
| Craft (V2 arsenal) | `references/` |
| Eyes / Playwright protocol | `references/vision-playwright.md` + `wde review` |
| Scripts (V2 checks) | `scripts/` via `wde run` |

## Core loop

```bash
wde validate intent|research|experience|design|lock --root <project>
wde run static --root <project>
wde deliver-check --root <project>
wde review --emit-package --url <url> --root <project>
# judge → aesthetic-verdict.json (reviewer: independent|human — not self;
# independent-clone is declared-only unless WDE_ALLOW_DECLARED_INDEPENDENCE=1)
wde review --url <url> --root <project>
wde report --root <project>
```

## Forbidden

- Hand-edit `.wde/state.json` / write `.wde/evidence/` as the model
- Use `wde transition` (removed — always errors)
- Claim READY without **verified** independent review evidence
- Invent metrics, testimonials, trusted-by
- Skip pillars (use fresh `search.py --persist` + `npx getdesign`, then `wde validate research`)

## Benchmark / migrate

```bash
wde benchmark --corpus
wde migrate-v2 --root <project>
```

V2 scripts remain under `scripts/` — invoked only through trusted `wde-core` checks.
