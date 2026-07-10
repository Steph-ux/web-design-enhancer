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

```bash
python -m wde.cli.main init --root <project>
python -m wde.cli.main status --json --root <project>
python -m wde.cli.main next --root <project>
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
python -m wde.cli.main validate intent|experience|design|lock --root <project>
python -m wde.cli.main run static --root <project>
python -m wde.cli.main deliver-check --root <project>
python -m wde.cli.main review --emit-package --url <url> --root <project>
# independent judge → aesthetic-verdict.json (never self for delivery)
python -m wde.cli.main review --url <url> --root <project>
python -m wde.cli.main report --root <project>
```

## Forbidden

- Hand-edit `.wde/state.json` / write `.wde/evidence/` as the model
- Claim READY without independent review evidence
- Invent metrics, testimonials, trusted-by
- Skip pillars (use fresh `search.py --persist` + `npx getdesign`)

## Benchmark / migrate

```bash
python -m wde.cli.main benchmark --corpus
python -m wde.cli.main migrate-v2 --root <project>
```

V2 scripts remain under `scripts/` — invoked only through trusted `wde-core` checks.
