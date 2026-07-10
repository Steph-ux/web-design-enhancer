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

Prefer short CLI (`wde` after `pip install -e .`, else `python -m wde`):

```bash
wde init --root <project>
wde status --json --root <project>
wde next --root <project>
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
wde run static --root <project>
wde deliver-check --root <project>
wde review --emit-package --url <url> --root <project>
# Independent judge writes audit-results/aesthetic-verdict.json
# (reviewer: independent-clone|independent|human — never self for delivery)
wde review --url <url> --root <project>
wde report --root <project>
wde benchmark --root <project>
```

## Migrating V2 projects

```bash
wde migrate-v2 --root <project>
```

Never auto-authorizes delivery.
