# Documentation — Web Design Enhancer Pro

Technical reference for the skill. The [README](../README.md) covers the quick pitch and install.

---

## Quick start

```bash
# 1. Anchor on real references (mandatory)
npx getdesign@latest add stripe
python3 scripts/search.py "saas analytics dashboard" --design-system -p "MyProject"

# 2. Fill DESIGN.md from the template
cp templates/design-md-template.md DESIGN.md

# 3. Validate the contract
python3 scripts/check.py --gate 1

# 4. After implementation, run the final gate
python3 scripts/check.py --final --code ./src
```

---

## Philosophy: Anti-"AI Slop"

This skill transforms any AI-generated interface into a professional-quality result. It enforces a mechanical rigor that makes producing "AI slop" patterns impossible — even with an unsupervised agent.

**3 core principles:**
- **Contract before code** — DESIGN.md is mechanically validated before a single line of code is written
- **Verifiable > subjective** — every design rule is testable by a Python script
- **Real references > training data** — Phase 0 forces anchoring on existing designs (Stripe, Linear, Vercel...)

---

## Architecture: 3 Pillars

```
Pillar 1 — getdesign.md           Pillar 2 — UI/UX Pro Max
(real visual references)          (sectoral intelligence, 161 rules, 67 styles)
           |                                    |
           +-----------------+------------------+
                             |
                          DESIGN.md
                       (design contract)
                             |
               Pillar 3 — web-design-enhancer-pro
               (validation + implementation + audit)
```

---

## 5-Phase Workflow

### Phase 0 — Anchoring (mandatory, blocking)
```bash
# 1. Get real visual references
npx getdesign@latest add stripe

# 2. Query the UI/UX Pro Max database
python3 scripts/search.py "saas analytics dashboard" --design-system -p "MyProject"

# 3. Verify Phase 0 was executed
python3 scripts/check.py --gate 0
```

### Phase 1 — DESIGN.md contract
Fill `DESIGN.md` with sections 0 through 10 (template: `templates/design-md-template.md`).
Validated sections: 0 (Phase 0 sources), 1-7 (core), **4 (H1/P size ranges)** auto-checked, 8 (Dark Mode, mandatory if dark background), 9 (Mobile, if native app), **10 (Three.js, if WebGL scene — see `references/threejs-best-practices.md`)**.
```bash
python3 scripts/check.py --gate 1   # Canonical entry point, invokes validate_design.py
```

### Phase 2 — CSS/HTML implementation
Map DESIGN.md tokens to `globals.css` or CSS variables.

### Phase 3 — GSAP animations
Orchestrate entries and scroll effects following `references/gsap-best-practices.md`.

### Phase 4 — Playwright visual audit
```bash
python3 scripts/visual_audit.py --url http://localhost:3000 --output ./audit-results
```

### Phase 5 — Final validation (blocking gate)
```bash
python3 scripts/check.py --final --code ./src
# Sequence (7 gates): detect_ai_slop -> audit_spacing -> validate_design ->
#   diff_design_vs_code -> audit_accessibility -> audit_style_uniqueness -> audit_beauty
# Separate (need a running server / screenshots / native source):
#   visual_audit.py, aesthetic_review.py (vision), audit_mobile.py
```

---

## Available scripts

| Script | Usage | Role |
| :--- | :--- | :--- |
| `validate_design.py` | `DESIGN.md` | Validates sections 0-8, WCAG AA, dark mode |
| `detect_ai_slop.py` | `--design` + `--code` | Score AI antipatterns (0-100, threshold 80) |
| `diff_design_vs_code.py` | `DESIGN.md --code ./src` | Divergences between contract and implementation |
| `audit_spacing.py` | `--path ./src` | 8px grid on real CSS/JSX |
| `visual_audit.py` | `--url localhost:3000` | Screenshots + Playwright audit on 4 breakpoints |
| `check.py` | `--gate 0/1/final` | Sequential gate orchestrator |
| `search.py` | `"query" --domain` | BM25 search across UI/UX Pro Max CSVs |
| `audit_accessibility.py` | `--path ./src` | WCAG 2.1 AA — alt, button type, labels, lang, viewport |
| `audit_style_uniqueness.py` | `--path ./src` | Generic AI Template detector — score > 65 blocks |
| `audit_beauty.py` | `--path ./src` | Beauty Score (positive craft) — score < 50 blocks |
| `audit_mobile.py` | `--path ./src` | Native craft + mobile gates (SwiftUI/Compose/Flutter/RN) |
| `aesthetic_review.py` | `--screenshots ./audit-results` | Aesthetic judgment of screenshots — agent's own vision by default (no key); --mode api optional |

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

---

## CI/CD integration

- **`.husky/pre-commit`** — runs `check.py --gate 0` then `--gate 1` before every commit.
  Install with `npx husky install`, then `chmod +x .husky/pre-commit`.

The pre-commit hook no-ops gracefully when no `DESIGN.md` is present at the repo root.

---

## Delivery checklist

- [ ] `DESIGN.md` sections 0-8 complete, `check.py --gate 0` passes
- [ ] `validate_design.py`: 0 errors
- [ ] `detect_ai_slop.py`: score >= 80/100
- [ ] `diff_design_vs_code.py`: 0 divergences
- [ ] `audit_spacing.py`: 0 grid violations
- [ ] `audit_style_uniqueness.py`: template score <= 65
- [ ] `audit_beauty.py`: beauty score >= 50 (>= 70 ideal)
- [ ] `audit_accessibility.py`: 0 WCAG 2.1 AA violations
- [ ] `visual_audit.py`: screenshots validated on 4 breakpoints
- [ ] `aesthetic_review.py`: vision score >= 75, reads_as "human"
- [ ] `audit_mobile.py` (native targets only): no M1/M2 blockers, score >= 70
- [ ] Section 8 (Dark Mode) present with background < #333 and WCAG AA
- [ ] `prefers-reduced-motion` in CSS/JS code
- [ ] Zero decorative emoji, zero cliche gradient, zero unjustified generic icon
