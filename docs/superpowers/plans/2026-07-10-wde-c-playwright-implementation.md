# web-design-enhancer-pro Option C + Eyes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform skill packaging into a thin orchestrator with progressive workflows, recipe-first anti-slop guidance, and mandatory Playwright MCP Eyes (human / fluid / OK) before any delivery claim — without rewriting the core detection engine.

**Architecture:** Hybrid conductor (`SKILL.md` ~150–220 lines) + specialist refs under `references/workflows/` and `references/vision-playwright.md`. Scripts remain source of truth for bans and gates. New thin `eyes_checklist.py` verifies Eyes artifacts exist. Targeted `validate_design.py` exemption for deliberate oversized display type when the brief commits to Typography hero.

**Tech Stack:** Markdown skill packaging; Python 3 scripts/tests (pytest); Playwright MCP (agent runtime); existing `check.py` / `visual_audit.py` / `aesthetic_review.py` pipeline.

**Spec:** `docs/superpowers/specs/2026-07-10-wde-c-playwright-design.md`  
**Baseline tests:** `452 passed` (keep green after any script change)

## Global Constraints

- Preserve detector semantics and aesthetic floors unless a task explicitly changes them with tests: beauty floor 50 / pass 70; uniqueness block >65; aesthetic floor 62 / pass 80; self-review cannot authorize.
- Description field = triggers only (no workflow dump / SDO anti-pattern).
- Ban catalogs (G1–G9, T1–T12, etc.) must not reappear as full tables in `SKILL.md`; scripts are SoT.
- Eyes = Playwright MCP **AND** `visual_audit.py` + layout + verdict — not OR.
- Any UI-producing mode ends with Eyes; no “quick ship” exception.
- Exact numbers for aesthetic thresholds when documenting: floor **62**, pass **80** (as wired in `check.py` → `aesthetic_review.py --threshold 62 80`).
- Commits: small, frequent, conventional messages.
- Do not push to remote unless user asks.
- Do not invent getdesign brands; link existing CSV / templates.

---

## File map

| Path | Action | Responsibility |
|------|--------|----------------|
| `SKILL.md` | **Replace** body | Orchestrator: modes, checklist, red flags, open-when index |
| `references/workflows/01-intent.md` | Create | Phase −1 brief recipe |
| `references/workflows/02-contract.md` | Create | Pillars + DESIGN.md + gates 0/1 |
| `references/workflows/03-implement.md` | Create | Stack branch, lock, gestures, build |
| `references/workflows/04-gates.md` | Create | Unified F1–F10 map + fix loop |
| `references/vision-playwright.md` | Create | MCP Eyes protocol + rubric |
| `references/rationalizations.md` | Create | Skip excuses → STOP |
| `scripts/eyes_checklist.py` | Create | Verify MCP shots + report + verdict present |
| `tests/test_eyes_checklist.py` | Create | Unit tests for eyes checklist |
| `scripts/check.py` | Modify | Step labels F1–F10; optional call out eyes_checklist in final hints |
| `scripts/validate_design.py` | Modify | H1 upper bound exemption for Typography hero |
| `tests/test_signature_and_tensions.py` or new `tests/test_hierarchy_excess.py` | Create/Modify | H1 exemption tests |
| `README.md` | Modify | Gate map + Eyes mandatory; lead non-SaaS example |
| `docs/README.md` | Modify | Align phases/gates with SKILL (remove stale 7-gate story) |
| `CHANGELOG.md` | Modify | Note packaging redesign V2.2 |

---

### Task 1: Orchestrator `SKILL.md` rewrite

**Files:**
- Modify: `SKILL.md` (full body replace; keep skill directory identity)
- Spec reference: `docs/superpowers/specs/2026-07-10-wde-c-playwright-design.md` §4–§5

**Interfaces:**
- Consumes: none (first packaging task)
- Produces: agent entrypoint that points to workflows 01–04, vision-playwright, rationalizations (files may be stubs until Tasks 2–4; create stub files in this task if missing so links resolve)

- [ ] **Step 1: Create stub workflow files if missing** so SKILL links do not 404 during partial work

```bash
# From repo root (PowerShell)
New-Item -ItemType Directory -Force -Path references\workflows | Out-Null
@("01-intent.md","02-contract.md","03-implement.md","04-gates.md") | ForEach-Object {
  if (-not (Test-Path "references\workflows\$_")) {
    Set-Content "references\workflows\$_" "# Stub — filled in later tasks`n"
  }
}
if (-not (Test-Path "references\vision-playwright.md")) {
  Set-Content "references\vision-playwright.md" "# Stub — filled in Task 4`n"
}
if (-not (Test-Path "references\rationalizations.md")) {
  Set-Content "references\rationalizations.md" "# Stub — filled in Task 4`n"
}
```

- [ ] **Step 2: Replace `SKILL.md` with orchestrator content**

Write the complete file (YAML + body). Target ≤220 lines. Required structure:

```markdown
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
```

Adjust wording slightly for line budget; do **not** re-add ban tables or pillar ASCII art essays.

- [ ] **Step 3: Word/line check**

```powershell
(Get-Content SKILL.md | Measure-Object -Line -Word)
```

Expected: lines ≤ ~220, words ≪ previous ~6300 (target roughly under 2000 words).

- [ ] **Step 4: Commit**

```bash
git add SKILL.md references/workflows references/vision-playwright.md references/rationalizations.md
git commit -m "refactor(skill): thin orchestrator SKILL with mode checklist"
```

---

### Task 2: Workflows — intent + contract

**Files:**
- Create/Replace: `references/workflows/01-intent.md`
- Create/Replace: `references/workflows/02-contract.md`

**Interfaces:**
- Consumes: orchestrator links from Task 1
- Produces: complete Phase −1 and Phase 0–1 instructions agents load on demand

- [ ] **Step 1: Write `01-intent.md`** with at least:

```markdown
# Workflow 01 — Intent (Phase −1)

## Purpose
A model cannot invent point of view. Fill `CREATIVE-BRIEF.md` **before** getdesign or DESIGN.md.

## Steps
1. Copy `templates/creative-brief-template.md` → project root `CREATIVE-BRIEF.md`.
2. Fill **all** sections (not only four):
   - Emotional Intent (concrete feeling, not "professional")
   - The One Unexpected Thing
   - Hero Dimension (exactly one checkbox)
   - The Broken Rule (must include "because")
   - Design Read
   - Design Dials (VARIANCE / MOTION / DENSITY 1–10; push ONE dial)
   - Cross-Domain Steal (non-software discipline + specific move)
3. Quality is machine-checked: `check.py --gate 0` runs `audit_brief.py` (floor 50/100). Filler fails.

## Pass
Brief present, specific, one hero dimension, broken rule with because, dials set, non-software steal.
```

- [ ] **Step 2: Write `02-contract.md`** with at least:

```markdown
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
```

- [ ] **Step 3: Commit**

```bash
git add references/workflows/01-intent.md references/workflows/02-contract.md
git commit -m "docs(workflows): add intent and contract progressive refs"
```

---

### Task 3: Workflows — implement + gates map

**Files:**
- Create/Replace: `references/workflows/03-implement.md`
- Create/Replace: `references/workflows/04-gates.md`

**Interfaces:**
- Consumes: gate behavior from `scripts/check.py` (F1–F10 order as implemented)
- Produces: implement recipe + single gate map for README/SKILL alignment

- [ ] **Step 1: Write `03-implement.md`**

Must include recipe-first order:
1. Quote archetype + gestures from `beauty-gestures.md`
2. Create `structural-lock.md` with ≥3 numbered decisions from DESIGN.md
3. `python3 scripts/check.py --gate 2`
4. Stack branch (vanilla CSS vars vs React/shadcn preferred)
5. Implement tokens + gestures (not tokens alone)
6. GSAP only if brief/DESIGN.md requires orchestration (`references/gsap-best-practices.md`)
7. Stop before delivery claims → go Eyes (`vision-playwright.md`) then `04-gates.md`

Include structural lock example (web):

```text
Structural lock — decisions from DESIGN.md:
1. Card structure: …
2. Section pattern: …
3. Primary button: …
```

- [ ] **Step 2: Write `04-gates.md`** with the **unified map** (copy numbers exactly):

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

Fix loop:

```bash
python3 scripts/detect_ai_slop.py --design DESIGN.md --code . --json
# apply fix_instruction precisely; max 3 iterations
python3 scripts/refine_loop.py --code . --design DESIGN.md --brief CREATIVE-BRIEF.md --json
python3 scripts/check.py --final --code . --url http://localhost:3000
```

- [ ] **Step 3: Commit**

```bash
git add references/workflows/03-implement.md references/workflows/04-gates.md
git commit -m "docs(workflows): implement recipe and unified gate map"
```

---

### Task 4: Eyes protocol + rationalizations

**Files:**
- Create/Replace: `references/vision-playwright.md`
- Create/Replace: `references/rationalizations.md`

**Interfaces:**
- Consumes: Playwright MCP tool names (`browser_navigate`, `browser_resize`, `browser_take_screenshot`, `browser_snapshot`, `browser_hover`, `browser_console_messages`)
- Produces: mandatory Eyes procedure agents must follow; skip-resistance table

- [ ] **Step 1: Write full `vision-playwright.md`**

Required sections:
1. **Definition of done** — Humain / Fluide / OK all pass
2. **MCP sequence** (exact tool names):

```text
1. Confirm live URL
2. browser_navigate { url }
3. For each viewport (375x667, 768x1024, 1280x800) [1920 optional]:
   - browser_resize
   - browser_take_screenshot → audit-results/mcp/{bp}.png
4. browser_snapshot at mobile + desktop
5. Scroll + browser_hover primary CTA
6. browser_console_messages level=error → must be clean
7. Optional: click/fill primary flow once
8. Write aesthetic-verdict.json (prefer independent-clone: screenshots+rubric only)
9. python3 scripts/visual_audit.py --url … --output ./audit-results
10. python3 scripts/audit_layout.py --url … --json
11. python3 scripts/eyes_checklist.py --audit-output ./audit-results
12. python3 scripts/check.py --final --code … --url …
```

3. **Rubric table** Humain / Fluide / OK (from spec §7.3)
4. **Provenance** — self/agent/unset blocked; independent-clone default; panel for critical
5. **Artifacts list** under `./audit-results/`
6. **Degraded mode** — if MCP unavailable: use visual_audit PNGs + read images with vision; document in verdict; never invent screenshots
7. **Loop** — fail any axis → fix → re-Eyes ≤3 → hard stop

- [ ] **Step 2: Write `rationalizations.md`** with the full excuse table from spec §9.1 plus red flags from §9.2

- [ ] **Step 3: Commit**

```bash
git add references/vision-playwright.md references/rationalizations.md
git commit -m "docs: Playwright MCP Eyes protocol and skip rationalizations"
```

---

### Task 5: `eyes_checklist.py` + tests (TDD)

**Files:**
- Create: `scripts/eyes_checklist.py`
- Create: `tests/test_eyes_checklist.py`

**Interfaces:**
- Consumes: directory tree under `--audit-output` (default `./audit-results`)
- Produces: exit 0 if minimum Eyes artifacts present; exit 1 + messages otherwise
- Function: `check_eyes_artifacts(audit_dir: Path) -> list[str]` returns error strings (empty = pass)

- [ ] **Step 1: Write failing tests** in `tests/test_eyes_checklist.py`

```python
"""eyes_checklist.py — verify Eyes artifacts before delivery claims."""
from pathlib import Path
import json
import sys

import pytest

# Allow importing scripts/
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from eyes_checklist import check_eyes_artifacts  # noqa: E402


def test_missing_dir_returns_error(tmp_path: Path):
    errs = check_eyes_artifacts(tmp_path / "nope")
    assert any("missing" in e.lower() or "not found" in e.lower() for e in errs)


def test_pass_when_minimum_artifacts_present(tmp_path: Path):
    audit = tmp_path / "audit-results"
    mcp = audit / "mcp"
    mcp.mkdir(parents=True)
    (mcp / "mobile.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (mcp / "desktop.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (audit / "audit_report.json").write_text(
        json.dumps({"screenshots": {"mobile": "x", "desktop": "y"}, "ai_slop_detected": []}),
        encoding="utf-8",
    )
    (audit / "aesthetic-verdict.json").write_text(
        json.dumps({
            "overall_score": 82,
            "reads_as": "human",
            "reviewer": "independent-clone",
            "memorable_idea": "Champagne hairline as sole accent",
        }),
        encoding="utf-8",
    )
    assert check_eyes_artifacts(audit) == []


def test_fail_when_no_mcp_screenshots(tmp_path: Path):
    audit = tmp_path / "audit-results"
    audit.mkdir()
    (audit / "audit_report.json").write_text("{}", encoding="utf-8")
    (audit / "aesthetic-verdict.json").write_text(
        json.dumps({
            "overall_score": 82,
            "reads_as": "human",
            "reviewer": "independent-clone",
            "memorable_idea": "Something memorable here",
        }),
        encoding="utf-8",
    )
    errs = check_eyes_artifacts(audit)
    assert any("mcp" in e.lower() or "screenshot" in e.lower() for e in errs)


def test_fail_when_self_reviewer(tmp_path: Path):
    audit = tmp_path / "audit-results"
    mcp = audit / "mcp"
    mcp.mkdir(parents=True)
    (mcp / "mobile.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (audit / "audit_report.json").write_text("{}", encoding="utf-8")
    (audit / "aesthetic-verdict.json").write_text(
        json.dumps({
            "overall_score": 90,
            "reads_as": "human",
            "reviewer": "self",
            "memorable_idea": "Something memorable here",
        }),
        encoding="utf-8",
    )
    errs = check_eyes_artifacts(audit)
    assert any("provenance" in e.lower() or "self" in e.lower() for e in errs)
```

- [ ] **Step 2: Run tests — expect FAIL** (module missing)

```bash
python -m pytest tests/test_eyes_checklist.py -v
```

Expected: import error or collection error for `eyes_checklist`.

- [ ] **Step 3: Implement `scripts/eyes_checklist.py`**

```python
#!/usr/bin/env python3
"""eyes_checklist.py — verify Playwright Eyes artifacts before delivery claims.

Does NOT replace visual_audit / aesthetic_review scoring. It only checks that
the agent produced the minimum evidence tree required by vision-playwright.md:
  - audit-results/mcp/*.png (or .jpg) — MCP screenshots
  - audit-results/audit_report.json — mechanical visual audit
  - audit-results/aesthetic-verdict.json — non-self verdict with memorable_idea

Usage:
  python3 scripts/eyes_checklist.py --audit-output ./audit-results
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def check_eyes_artifacts(audit_dir: Path) -> list[str]:
    errors: list[str] = []
    if not audit_dir.exists() or not audit_dir.is_dir():
        return [f"Eyes audit directory missing or not a directory: {audit_dir}"]

    mcp = audit_dir / "mcp"
    shots = []
    if mcp.is_dir():
        shots = [p for p in mcp.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}]
    # Degraded mode: accept top-level visual_audit screenshots if mcp/ empty but
    # at least 2 images exist under audit_dir (agent must still set degraded flag in verdict).
    if len(shots) < 1:
        loose = [
            p for p in audit_dir.rglob("*")
            if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
            and "mcp" not in p.parts  # counted separately
        ]
        if len(loose) < 2:
            errors.append(
                "Eyes screenshots missing — need audit-results/mcp/*.png from Playwright MCP "
                "(or ≥2 rendered PNGs from visual_audit in degraded mode). "
                "See references/vision-playwright.md."
            )

    report = audit_dir / "audit_report.json"
    if not report.is_file():
        errors.append(
            "audit_report.json missing — run: python3 scripts/visual_audit.py --url <URL> "
            f"--output {audit_dir}"
        )

    verdict_path = audit_dir / "aesthetic-verdict.json"
    if not verdict_path.is_file():
        errors.append(
            "aesthetic-verdict.json missing — complete vision judgment per "
            "references/vision-playwright.md"
        )
    else:
        try:
            v = json.loads(verdict_path.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append(f"aesthetic-verdict.json unreadable: {e}")
            v = None
        if isinstance(v, dict):
            reviewer = str(v.get("reviewer", "")).strip().lower()
            if reviewer in {"", "self", "agent"}:
                errors.append(
                    f"PROVENANCE: reviewer='{reviewer or 'unset'}' cannot authorize delivery "
                    "(use independent-clone, independent, or human)."
                )
            idea = v.get("memorable_idea")
            if not (isinstance(idea, str) and len(idea.strip()) >= 8):
                errors.append(
                    "memorable_idea missing or too short — name one owned, visible design move."
                )
            if str(v.get("reads_as", "")).strip().lower() == "ai":
                errors.append("reads_as: ai — page still reads as AI; fix craft before delivery.")

    return errors


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Verify Eyes artifacts for web-design-enhancer")
    p.add_argument("--audit-output", default="./audit-results", help="Audit directory")
    args = p.parse_args(argv)
    errs = check_eyes_artifacts(Path(args.audit_output))
    if errs:
        print("EYES CHECKLIST — FAILED")
        for e in errs:
            print(f"  - {e}")
        return 1
    print("EYES CHECKLIST — PASSED")
    print(f"  artifacts OK under {args.audit_output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
python -m pytest tests/test_eyes_checklist.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Wire optional hint into `check.py` visual errors** (light touch)

In `evaluate_visual_gate`, when report or verdict missing, append to the error string:

```text
Also run: python3 scripts/eyes_checklist.py --audit-output <dir>
```

Do not make `eyes_checklist` a hard subprocess of `--final` in v1 if it would break existing tests that only provide report+verdict without `mcp/` — **unless** you also update those tests to create `mcp/` or use the degraded ≥2 PNG path.

**Safer v1 choice:** keep `eyes_checklist` agent-invoked only (documented in SKILL + vision-playwright). Skip hard wire into `--final` to avoid false fails on existing fixtures. Document this decision in the commit message.

- [ ] **Step 6: Commit**

```bash
git add scripts/eyes_checklist.py tests/test_eyes_checklist.py
git commit -m "feat(eyes): add eyes_checklist artifact verifier with tests"
```

---

### Task 6: Align docs (README + docs/README + CHANGELOG)

**Files:**
- Modify: `README.md`
- Modify: `docs/README.md`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: unified map from `04-gates.md`
- Produces: zero conflicting gate counts

- [ ] **Step 1: Update `README.md` sections**

Changes required:
1. State **Eyes (Playwright MCP) is mandatory** before delivery.
2. Replace any “7 gates” language with unified G0–G2 + F1–F10 + Eyes map (short table or link to `references/workflows/04-gates.md`).
3. Mention orchestrator skill + progressive workflows.
4. Keep NOIRÉ / CryptoVerse examples; ensure luxury non-SaaS example remains prominent near the top of examples.

- [ ] **Step 2: Rewrite stale `docs/README.md` gate sequence** to match `04-gates.md` (or replace body with pointer to SKILL + 04-gates if full rewrite is huge).

- [ ] **Step 3: Prepend CHANGELOG entry**

```markdown
## V2.2 — orchestrator packaging + mandatory Eyes (Playwright MCP)

### Changed
- `SKILL.md` rewritten as thin mode-based orchestrator (progressive disclosure).
- Workflows: `references/workflows/01-intent.md` … `04-gates.md`.
- Eyes protocol: `references/vision-playwright.md` (MCP + mechanical AND).
- Skip resistance: `references/rationalizations.md`.
- `scripts/eyes_checklist.py` verifies Eyes artifacts.

### Docs
- README / docs gate map aligned (no more 7-gate drift).
```

- [ ] **Step 4: Grep for stale counts**

```bash
# Prefer rg if available; else Select-String
rg -n "7 gates|five phase|5-phase|1/9" README.md docs/README.md SKILL.md references/workflows || true
```

Expected: no stale “7 gates” left in those files (historical CHANGELOG mentions OK).

- [ ] **Step 5: Commit**

```bash
git add README.md docs/README.md CHANGELOG.md
git commit -m "docs: align gate map and mandate Playwright MCP Eyes"
```

---

### Task 7: Display type excess exemption (quality half)

**Files:**
- Modify: `scripts/validate_design.py` (hierarchy validation ~lines 245–310)
- Create: `tests/test_hierarchy_excess.py`

**Interfaces:**
- Consumes: DESIGN.md text + optional `CREATIVE-BRIEF.md` in CWD or path
- Produces: H1 may exceed 80px only when Typography hero is committed and Broken Rule / §11 documents because

- [ ] **Step 1: Write failing tests**

```python
# tests/test_hierarchy_excess.py
from pathlib import Path
import sys
import tempfile
import textwrap

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_design import DesignValidator  # adjust import to actual class/API


def _write(dir: Path, name: str, content: str) -> Path:
    p = dir / name
    p.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")
    return p


def test_h1_over_80_blocked_without_typography_hero(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    design = _write(tmp_path, "DESIGN.md", """
    # Design
    ## 4. Type hierarchy
    - **H1**: 120px / 700 / 1.0
    - **P**: 16px / 400 / 1.5
    """)
    # Use the project's real entrypoint: if DesignValidator(path) API differs,
    # call the same function check.py uses.
    v = DesignValidator(str(design))
    ok = v.validate() if hasattr(v, "validate") else v.run()
    # Expect hierarchy ERROR about H1 too large
    errors = getattr(v, "errors", []) or getattr(v, "messages", [])
    text = "\n".join(str(e) for e in errors) if errors else str(ok)
    assert "80" in text or "too large" in text.lower() or ok is False


def test_h1_over_80_allowed_with_typography_hero_and_because(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(tmp_path, "CREATIVE-BRIEF.md", """
    # Brief
    ## Hero Dimension
    - [x] Typography
    ## The Broken Rule
    We ignore the 80px H1 cap because the hero type IS the product identity.
    """)
    design = _write(tmp_path, "DESIGN.md", """
    # Design
    ## 4. Type hierarchy
    - **H1**: 120px / 700 / 1.0
    - **P**: 16px / 400 / 1.5
    ## 11. Signature Gesture
    Full-bleed 120px display name; body 16px for tension.
    """)
    v = DesignValidator(str(design))
    if hasattr(v, "validate"):
        v.validate()
    else:
        v.run()
    errors = [str(e).lower() for e in (getattr(v, "errors", []) or [])]
    assert not any("too large" in e and "h1" in e for e in errors)
```

**Important:** Before coding tests, open `validate_design.py` and match the **real** class name and method (`DesignValidator`, `main`, etc.). Adapt the test to call the public API used by `check.py` — do not invent a private API.

- [ ] **Step 2: Run test — expect FAIL** on second case (currently 120px always errors)

```bash
python -m pytest tests/test_hierarchy_excess.py -v
```

- [ ] **Step 3: Implement exemption in `validate_design.py`**

Logic sketch (place near H1 range check):

```python
def _allows_display_excess(self, design_text: str) -> bool:
    """True when brief commits Typography hero + documents because."""
    brief_path = Path("CREATIVE-BRIEF.md")
    brief = brief_path.read_text(encoding="utf-8") if brief_path.exists() else ""
    hero_typo = bool(re.search(
        r"Hero Dimension[\s\S]{0,400}?\[x\]\s*Typography",
        brief,
        re.I,
    ))
    because = bool(re.search(r"because\s+\S+", brief, re.I)) or bool(
        re.search(r"##\s*11[\s\S]{0,500}because", design_text, re.I)
    )
    return hero_typo and because
```

When validating H1 max:
- if `val > 80` and `_allows_display_excess(...)`: emit **WARN** not ERROR (or skip upper bound)
- else keep ERROR as today
- Cap absolute absurdity: still ERROR if H1 > 200px (safety)

- [ ] **Step 4: Run tests + full suite subset**

```bash
python -m pytest tests/test_hierarchy_excess.py tests/test_signature_and_tensions.py -v
python -m pytest tests/ -q --tb=line
```

Expected: new tests pass; full suite still green (or only intentional new failures fixed).

- [ ] **Step 5: Commit**

```bash
git add scripts/validate_design.py tests/test_hierarchy_excess.py
git commit -m "feat(validate): allow deliberate H1 excess for Typography hero"
```

---

### Task 8: `check.py` label clarity (cosmetic)

**Files:**
- Modify: `scripts/check.py` (`check_final` print labels around F1–F10)
- Modify: any test that snapshots exact `"[1/9]"` strings (grep first)

- [ ] **Step 1: Grep for label snapshots**

```bash
rg -n "1/9|2/9|9/9|1b/9" tests scripts/check.py
```

- [ ] **Step 2: Update print labels** to e.g. `[F1]`, `[F1b]`, `[F2]`…`[F9]`, `[F10]` without changing exit codes or gate logic.

- [ ] **Step 3: Run affected tests**

```bash
python -m pytest tests/test_check_visual_gate.py tests/test_wde_measure.py -q
python -m pytest tests/ -q --tb=line
```

- [ ] **Step 4: Commit**

```bash
git add scripts/check.py tests
git commit -m "chore(check): align final gate labels with F1–F10 map"
```

---

### Task 9: Verification smoke (skill packaging)

**Files:**
- None required (manual/scripted verification)
- Optional: `tests/test_skill_packaging.py` for static checks

- [ ] **Step 1: Static packaging asserts (optional but recommended)**

```python
# tests/test_skill_packaging.py
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def test_skill_description_has_no_gate_inventory():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    # YAML description should not list "10 sequential" style workflow dump
    fm = re.match(r"^---\n(.*?)\n---", text, re.S)
    assert fm, "missing frontmatter"
    desc = fm.group(1)
    assert "10 sequential" not in desc
    assert "Use when" in desc or "use when" in desc.lower()


def test_skill_points_to_vision_playwright():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "vision-playwright.md" in text


def test_workflow_files_exist():
    for name in ("01-intent.md", "02-contract.md", "03-implement.md", "04-gates.md"):
        p = ROOT / "references" / "workflows" / name
        assert p.is_file() and p.stat().st_size > 200, f"{name} missing or stub-sized"


def test_eyes_script_exists():
    assert (ROOT / "scripts" / "eyes_checklist.py").is_file()
```

- [ ] **Step 2: Run packaging tests + full suite**

```bash
python -m pytest tests/test_skill_packaging.py tests/test_eyes_checklist.py -v
python -m pytest tests/ -q --tb=line
```

Expected: all green.

- [ ] **Step 3: Manual checklist (agent self-check)**

- [ ] SKILL loads as orchestrator (no ban encyclopedia)
- [ ] Vision protocol names MCP tools
- [ ] README gate count matches 04-gates
- [ ] `eyes_checklist` help works: `python scripts/eyes_checklist.py --help`

- [ ] **Step 4: Commit**

```bash
git add tests/test_skill_packaging.py
git commit -m "test: packaging guards for orchestrator skill and Eyes refs"
```

---

### Task 10: Final integration commit note

- [ ] **Step 1: Ensure working tree clean and suite green**

```bash
python -m pytest tests/ -q --tb=line
git status
```

Expected: all tests pass; only intentional uncommitted work none.

- [ ] **Step 2: Summarize for user**

Deliver:
- Path to plan + list of commits
- How to use: pick mode → follow checklist → Eyes MCP always
- Note: `--final` still enforces mechanical visual gate; `eyes_checklist` is agent-facing unless later wired

---

## Spec coverage (self-review)

| Spec section | Task(s) |
|--------------|---------|
| §4 Packaging / thin SKILL | Task 1 |
| §4 Description SDO fix | Task 1, 9 |
| §5 Modes | Task 1 |
| §6 Pipeline recipe-first | Tasks 1–3 |
| §7 Eyes MCP + AND scripts | Tasks 4–5 |
| §7.3 Rubric | Task 4 |
| §7.4 Provenance | Tasks 4–5 |
| §8 Quality / WOW default recommend | Tasks 1, 3, 6 (docs); not forced in check.py hard default (spec: recommend, opt-out) |
| §8.3 H1 excess | Task 7 |
| §8.5 Stack branch | Tasks 1, 3 |
| §9 Rationalizations | Task 4 |
| §10 Unified gate map | Tasks 3, 6, 8 |
| §11 Sprint A–D | Tasks 1–9 map to sprints |
| Preserve engine / tests | Global + Tasks 5,7,8,9 |
| eyes_checklist optional hard-wire | Task 5 documents safer v1 (agent-invoked) |

## Placeholder scan

No TBD / “implement later” left in task steps. Import names for `DesignValidator` must be adapted to real API when executing Task 7 (explicit note in Step 1).

## Type consistency

- `check_eyes_artifacts(audit_dir: Path) -> list[str]` used in tests and CLI.
- Aesthetic thresholds documented as 62 / 80 everywhere.
- Artifact paths: `./audit-results/mcp/`, `audit_report.json`, `aesthetic-verdict.json`.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-10-wde-c-playwright-implementation.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — this session, task-by-task with checkpoints  

**Which approach?**
