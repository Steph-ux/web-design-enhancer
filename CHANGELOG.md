# Changelog

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
