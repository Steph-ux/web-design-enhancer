# Changelog

## V2.2 — orchestrator packaging + mandatory Eyes (Playwright MCP)

### Changed
- `SKILL.md` rewritten as thin mode-based orchestrator (progressive disclosure).
- Workflows: `references/workflows/01-intent.md` … `04-gates.md`.
- Eyes protocol: `references/vision-playwright.md` (MCP + mechanical AND).
- Skip resistance: `references/rationalizations.md`.
- `scripts/eyes_checklist.py` verifies Eyes artifacts.

### Docs
- README / docs gate map aligned (no more 7-gate drift).

## V2.1 — open-design craft integration (brand-agnostic only)

Vendors the **brand-agnostic craft layer** of [`nexu-io/open-design`](https://github.com/nexu-io/open-design)
(Apache-2.0, pinned `009ff65`) without touching getdesign's territory. Their
per-brand `design-systems/` are deliberately **excluded** — brand references are
sourced live via `getdesign` (Pillar 1), and snapshotting them would duplicate
that and go stale.

### Added — vendored craft references
- `references/craft/*.md` — typography, color, motion discipline, Laws of UX,
  state coverage, form validation, accessibility baseline, RTL/bidi. Enriches
  the agent's reference set (Pillar 2). Vendored verbatim (byte-exact, UTF-8).
- `references/craft/anti-ai-slop.md` — the human-maintained **source of truth**
  for the default-AI indigo palette.
- Attribution: root `NOTICE`, `LICENSES/open-design-APACHE-2.0.txt`,
  `references/craft/ATTRIBUTION.md`, and a `_manifest.txt` for reproducible re-sync.

### Changed — `detect_ai_slop.py` linked to the canon + hardened
- New `CANON_DEFAULT_INDIGO` constant mirrors open-design's `AI_DEFAULT_INDIGO`,
  documenting *why* those hexes are slop (already enforced by rules B6 + B12).
- **Bug fix:** forces UTF-8 stdout at the CLI entry so a non-ASCII finding (the
  indigo→violet gradient message) can no longer crash a real run on a Windows
  cp1252 console.

### Tests
- +4 tests (`test_anti_slop_canon_sync.py`) — fail loudly if the canon and the
  detector constant drift apart. Full suite: **434 passed, 1 skipped**.

### Docs
- README (new "Craft references" section, file tree, 434 count), SKILL.md
  (Resources rows for `references/craft/` + canon link).


## Taste bridge — generative "waouh" lever + mechanized AI-tells

Gates reject ugliness; they do not create beauty. This wave adds the upstream,
generative half (ported from the ideas in taste-skill) and turns its
self-checked pre-flight items into REAL detectors.

### Added — Creative Brief (Phase -1) now drives the design
- `Design Read` one-liner, three `Design Dials` (VARIANCE / MOTION / DENSITY,
  1-10, reasoned from the brief — "waouh" comes from pushing ONE dial far), and
  a `The Cross-Domain Steal` field (a NON-software reference to steal one move
  from). `check.py` blocks on missing dials / unfilled steal, warns when the
  dials are too balanced or the steal is still a tech reference.
- 4 brief tests.

### Changed — `detect_ai_slop.py` mechanizes taste-skill's AI Tells
Self-checked there → enforced here: em-dash in visible text (their #1 tell),
scroll cues, version/build/INVITE-ONLY labels, section-numbering eyebrows
('00 / INDEX'), and placeholder identities (Jane Doe / Acme / "Quietly in use at").

## Gate hardening — closing the self-validation loophole

A real delivery (a "systems engineer" portfolio) passed every gate, self-scored
94/100, and printed DELIVERY AUTHORIZED — while shipping a "Status is active"
badge, "System terminal connection: closed" footer, "Transmit payload" form
labels (terminal cosplay), and a hardcoded AWS access key. Root cause: the
slop detector matched a fixed token list (dodged by sentence-case phrasing) and
the aesthetic gate let the GENERATING model grade its own work.

### Added
- `scripts/audit_declared_antipatterns.py` — new gate [1b] that reads each
  project's OWN "Avoid" list (DESIGN.md antipatterns + design-system-output)
  and blocks if a self-declared antipattern token appears in the delivery.
- 5 tests in `test_check_visual_gate.py` covering provenance + signature rules.

### Changed
- `detect_ai_slop.py` — new patterns for sentence-case fake-terminal chrome
  ("Status is active", "System terminal connection", "Transmit payload",
  "Session payload", "System Initialization"), `status-indicator/-dot/-text`
  classes, and hardcoded credentials (AWS `AKIA…` keys, `api_key/secret = "…"`).
- `check.py` visual gate — a verdict whose `reviewer` is `self`/`agent`/unset can
  **no longer authorize delivery** (independent or human sign-off required); a
  verdict with no named `memorable_idea` is blocked ("clean" is the floor, not a
  pass); `reads_as: ai` is blocked. Delivery pass mark raised 75 → **80**.

## Beauty system — from "not generic" to "magnificent"

The suite was already strong at *prohibiting* AI slop (6 gates, slop detector,
uniqueness score). These changes add the missing half: *enforcing* beauty, so
output reads as the work of a human designer rather than merely "not generic".
Web **and** native mobile.

### Added — Beauty Score gate (gate 7)
- `scripts/audit_beauty.py` — the positive mirror of `audit_style_uniqueness.py`.
  Rewards craft markers and **blocks clean-but-soulless** designs.
  Five dimensions (0-100): type-scale contrast (D1), hierarchy richness (D2),
  colour intentionality (D3), spacing rhythm (D4), finition/interaction depth (D5).
  Exit 2 below floor (50), pass at ≥70. Wired as step 7/7 in `check.py --final`.

### Added — Beauty gestures reference
- `references/beauty-gestures.md` — the positive recipe per archetype:
  2-3 signature gestures + a validated font pairing (escaping Inter / Inter+Poppins),
  each mapped to a Beauty Score dimension, plus a universal craft floor.

### Added — Vision aesthetic review (Phase 4)
- `scripts/aesthetic_review.py` — submits the rendered screenshots to a vision
  model and returns a scored verdict across 7 dimensions incl. a human-vs-AI tell.
  OpenAI-compatible or Anthropic; `--dry-run` assembles the request offline.
  Blocks below 60, passes at ≥75.

### Added — Mobile / native gates (Phase 5, native targets)
- `scripts/audit_mobile.py` — detects SwiftUI / Jetpack Compose / Flutter /
  React Native, scores five mobile dimensions and **hard-blocks** sub-minimum
  touch targets and missing safe-area handling.
- `references/mobile-beauty.md` — native signature gestures + non-negotiables
  per platform, and the "web-shrink tells" that betray AI-generated mobile.

### Tests
- +63 tests (beauty 24, aesthetic 21, mobile 18). Full suite: **188 passed**.

### Docs
- README (7-gate table, structure, test count), SKILL.md (Phase 4/5 + Resources),
  and docs/README (scripts table, Phase 5 sequence, delivery checklist) brought
  in line with the full pipeline.