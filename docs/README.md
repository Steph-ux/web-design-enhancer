# Documentation — Web Design Enhancer Pro

Technical reference for the skill. The [README](../README.md) covers the quick pitch and examples (NOIRÉ, CryptoVerse).

**Source of truth for agents:**
- Thin orchestrator: [`SKILL.md`](../SKILL.md) — modes + checklist + red flags
- Progressive workflows: [`references/workflows/`](../references/workflows/) (`01-intent` … `04-gates`)
- **Unified gate map:** [`references/workflows/04-gates.md`](../references/workflows/04-gates.md) (G0–G2 + F1–F10 + Eyes + WOW)
- **Eyes (Playwright MCP) protocol:** [`references/vision-playwright.md`](../references/vision-playwright.md) — mandatory before any UI delivery claim
- Skip resistance: [`references/rationalizations.md`](../references/rationalizations.md)

This page is a short operator cheat-sheet. Prefer SKILL + workflows when the map conflicts with older notes.

---

## Quick start

```bash
# 1. Intent + anchors (mandatory)
# Fill CREATIVE-BRIEF.md from templates/creative-brief-template.md
npx getdesign@latest add stripe
python3 scripts/search.py "saas analytics dashboard" --design-system -p "MyProject" --persist

# 2. Contract
cp templates/design-md-template.md DESIGN.md
# fill DESIGN.md, then:
python3 scripts/check.py --gate 0
python3 scripts/check.py --gate 1
python3 scripts/check.py --gate 2   # structural-lock

# 3. Implement from DESIGN.md + gestures only (see references/workflows/03-implement.md)

# 4. Eyes (mandatory) — live URL + Playwright MCP, then mechanical capture
# Load references/vision-playwright.md
python3 scripts/visual_audit.py --url http://localhost:3000 --output ./audit-results
python3 scripts/audit_layout.py --url http://localhost:3000 --json
python3 scripts/eyes_checklist.py --audit-output ./audit-results

# 5. Final gates
python3 scripts/check.py --final --code ./src --url http://localhost:3000
# brand / marketing landings:
python3 scripts/check.py --final --code ./src --url http://localhost:3000 --wow
```

---

## Philosophy: Anti-"AI Slop"

This skill transforms any AI-generated interface into a professional-quality result. It enforces a mechanical rigor that makes producing "AI slop" patterns impossible — even with an unsupervised agent.

**Core principles:**
- **Contract before code** — DESIGN.md is mechanically validated before a single line of code is written
- **Verifiable > subjective** — every design rule is testable by a Python script
- **Real references > training data** — Phase 0 forces anchoring on existing designs (Stripe, Linear, Vercel…)
- **Eyes before delivery** — Playwright MCP + mechanical scripts (AND, not OR); no silent ship without fresh `./audit-results/`

---

## Architecture: 3 Pillars

```
Pillar 1 — getdesign.md           Pillar 2 — UI/UX Pro Max
(real visual references)          (sectoral intelligence, craft refs)
           |                                    |
           +-----------------+------------------+
                             |
                          DESIGN.md
                       (design contract)
                             |
               Pillar 3 — web-design-enhancer-pro
               (validation + implementation + Eyes + audit)
```

---

## Workflow (modes + progressive load)

`SKILL.md` is the **orchestrator**. Pick a mode, then load only the workflow you need:

| Mode | Load first | Done when |
|------|------------|-----------|
| `greenfield` | `references/workflows/01-intent.md` | Eyes + `check.py --final --code … --url …` green |
| `contract` | `01-intent` then `02-contract.md` | `--gate 0` and `--gate 1` green |
| `implement` | `03-implement.md` | Eyes + `--final --url` green |
| `audit-fix` | `04-gates.md` | Fix loop ≤3 + re-Eyes + `--final` green |
| `vision-only` | `vision-playwright.md` | Eyes rubric + artifacts under `./audit-results/` |

Greenfield path (default): **intent → craft aim → contract (G0/G1) → structural lock (G2) → build → Eyes → final (F1–F10) → fix ≤3**.

---

## Gate map (canonical)

Full detail: [`references/workflows/04-gates.md`](../references/workflows/04-gates.md).

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
| F9 | visual report + aesthetic verdict | floor 62 / pass 80; self cannot authorize |
| F10 | audit_layout | L1–L3 block when `--url` |
| Eyes | Playwright MCP rubric | skill-level mandatory |
| WOW | audit_wow | when `--wow` |

```bash
python3 scripts/check.py --final --code <path> --url <url>
# After any UI change: re-Eyes (MCP + visual_audit + layout) before re-running --final.
```

---

## Available scripts

| Script | Usage | Role |
| :--- | :--- | :--- |
| `validate_design.py` | `DESIGN.md` | Validates sections 0–8+, WCAG AA, dark mode |
| `detect_ai_slop.py` | `--design` + `--code` | Score AI antipatterns (0–100, threshold 80) |
| `diff_design_vs_code.py` | `DESIGN.md --code ./src` | Divergences between contract and implementation |
| `audit_spacing.py` | `--path ./src` | 8px grid on real CSS/JSX |
| `visual_audit.py` | `--url localhost:3000` | Screenshots + Playwright audit on breakpoints |
| `audit_layout.py` | `--url localhost:3000 --json` | Measured layout integrity (F10) |
| `eyes_checklist.py` | `--audit-output ./audit-results` | Verifies Eyes artifacts before delivery language |
| `check.py` | `--gate 0/1/2` or `--final` | Sequential gate orchestrator |
| `search.py` | `"query" --domain` | BM25 search across UI/UX Pro Max CSVs |
| `audit_accessibility.py` | `--path ./src` | WCAG 2.1 AA — alt, button type, labels, lang, viewport |
| `audit_style_uniqueness.py` | `--path ./src` | Generic AI Template detector — score > 65 blocks |
| `audit_beauty.py` | `--path ./src` | Beauty Score (positive craft) — score < 50 blocks |
| `audit_mobile.py` | `--path ./src` | Native craft + mobile gates (SwiftUI/Compose/Flutter/RN) |
| `aesthetic_review.py` | `--screenshots ./audit-results` | Aesthetic judgment — agent vision by default; `--mode api` optional |
| `refine_loop.py` | `--code` + `--design` + `--brief` | Iterative enhancement (measure → prioritise → converge) |

---

## Automatically detected antipatterns

| Antipattern | AI signal | Remedy |
| :--- | :--- | :--- |
| Decorative emojis | inline emoji in code | Radical removal |
| Generic Lucide icons | sparkles, zap, star, bot, magic | Consistent pack or custom SVG |
| Cliche gradients | blue-to-purple, pink-to-purple | Solid semantic colors |
| Unrequested status badges | LIVE NOW, SYS_STATUS: ONLINE | Remove or justify in section 1 |
| Vague buzzwords | premium, modern, elegant | Precise, measurable descriptions |
| Uniform typography | font-size: 16px everywhere | Respect section 4 hierarchy |
| Excessive hover | translateY(-8px), 32px shadow | <= -4px, discreet shadow |
| Improvised dark mode | colors invented at generation time | Mandatory section 8 |
| Forbidden themes | glassmorphism, typewriter effect | Detected and blocked by validate_design |
| Three.js antipatterns | geometry in animate(), renderer in useEffect, uncapped pixel ratio | Blocked by detect_ai_slop on .js/.ts/.jsx/.tsx |

Run the detector for the live list — do not re-memorize pattern codes:

```bash
python3 scripts/detect_ai_slop.py --design DESIGN.md --code . --json
```

---

## CI/CD integration

- **`.husky/pre-commit`** — runs `check.py --gate 0` then `--gate 1` before every commit.
  Install with `npx husky install`, then `chmod +x .husky/pre-commit`.

The pre-commit hook no-ops gracefully when no `DESIGN.md` is present at the repo root.

---

## Delivery checklist

- [ ] `CREATIVE-BRIEF.md` complete (intent + dials + cross-domain steal)
- [ ] Phase 0 anchors + design-system-output; `check.py --gate 0` passes
- [ ] `DESIGN.md` complete; `check.py --gate 1` passes
- [ ] `structural-lock.md` (≥3 decisions); `check.py --gate 2` passes
- [ ] Eyes: Playwright MCP screenshots (incl. **375px**) + `visual_audit.py` + layout
- [ ] Fresh `./audit-results/` (`audit_report.json` + non-self `aesthetic-verdict.json`)
- [ ] `eyes_checklist.py --audit-output ./audit-results` exit 0
- [ ] `detect_ai_slop.py`: score >= 80/100
- [ ] `audit_declared_antipatterns` clean (F1b)
- [ ] `diff_design_vs_code.py`: 0 divergences
- [ ] `audit_spacing.py`: 0 grid violations
- [ ] `audit_style_uniqueness.py`: template score <= 65
- [ ] `audit_beauty.py`: beauty score >= 50 (>= 70 ideal)
- [ ] `audit_gestures`: ≥ 2/3 declared gestures present
- [ ] `audit_accessibility.py`: 0 WCAG 2.1 AA violations
- [ ] Aesthetic verdict: score pass, `reads_as` ≠ ai, named `memorable_idea`, reviewer ≠ self
- [ ] `audit_mobile.py` (native targets only): no M1/M2 blockers, score >= 70
- [ ] `check.py --final --code … --url …` exit 0 (`--wow` for brand landings)
- [ ] Section 8 (Dark Mode) present when dark background; WCAG AA
- [ ] `prefers-reduced-motion` in CSS/JS code
- [ ] Zero decorative emoji, zero cliche gradient, zero unjustified generic icon
