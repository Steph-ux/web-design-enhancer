---
name: web-design-enhancer
description: >
  Use when building, redesigning, or validating web/UI with WDE V3 evidence
  orchestration; when AI agents must follow authorized next steps and cannot
  forge delivery. Not for pure backend or non-UI work.
---

# Web Design Enhancer (V3 skill adapter)

**The model proposes and implements. The orchestrator authorizes, verifies, and blocks.**

This skill is a **thin adapter**. Do not improvise gates. Always ask the CLI.

## Bootstrap

```bash
# from skill / repo root
python -m wde.cli.main init --root <project>
python -m wde.cli.main status --json --root <project>
python -m wde.cli.main next --root <project>
```

Follow `next_action` only. Load deeper refs only when that action needs them:

| Need | Load |
|------|------|
| Brief | `templates/creative-brief-template.md` |
| UX contract | `templates/experience-contract-template.md` |
| Design contract | `templates/design-md-template.md` |
| Generic agent rules | `adapters/generic/ADAPTER.md` |
| Full plan | `docs/superpowers/specs/2026-07-10-wde-v3-plan.md` |
| V2 craft refs | `references/` (gestures, antipatterns, craft) |

## Forbidden

- Writing `.wde/evidence/*` or faking `READY_TO_DELIVER` in `state.json`
- Code before `validate lock` / implementation-allowed phase
- Claiming visual pass without browser evidence (or admit `degraded_mode`)
- Invented metrics / testimonials / trusted-by

## Delivery

```bash
python -m wde.cli.main run static --root <project>
python -m wde.cli.main deliver-check --root <project>
python -m wde.cli.main review --emit-package --url <url> --root <project>
# Independent judge writes audit-results/aesthetic-verdict.json
# (reviewer: independent-clone|independent|human — never self for delivery)
python -m wde.cli.main review --url <url> --root <project>
python -m wde.cli.main report --root <project>
python -m wde.cli.main benchmark --root <project>
```

## Migrating V2 projects

```bash
python -m wde.cli.main migrate-v2 --root <project>
```

Never auto-authorizes delivery.
