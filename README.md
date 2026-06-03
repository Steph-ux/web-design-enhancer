# Web Design Enhancer

**Eradicate AI visual improvisation and deliver premium, clean, and professional interfaces.**

## Philosophy: Anti-"AI Slop"

This skill transforms any generic website into a high-end visual experience. It enforces absolute rigor to prevent common AI design tells (unnecessary emojis, random spacing, generic components).

### Strict Visual Hygiene Principles
- **Less is more**: Elimination of any cosmetic element without a clear function.
- **Strict 8px grid**: Multiples of 8 for all spacing (Tailwind: `p-2`, `m-8`, etc.).
- **Textual logos**: Use premium stylized typography if no logo asset is provided.
- **WCAG AA Contrast**: Enforced color contrast ratio (minimum 4.5:1 for text, 3.0:1 for UI elements).
- **Visual self-correction**: Mandatory use of Playwright to eliminate "AI slop".

## Improvement Workflow

### 1. Audit & Definition (The "Brain")
Define the design system in a `DESIGN.md` file.
- Map semantic variables to **shadcn/ui**.
- Justify every technical layout decision.
- Validate the design schema and contrast compliance: `python3 scripts/validate_design.py DESIGN.md`

### 2. Structural Implementation (The "Body")
- Exclusively use **shadcn/ui** primitives.
- Configure `globals.css` using the variables defined in `DESIGN.md`.

### 3. Dynamism with GSAP (The "Soul")
- Orchestrate entrance animations and scroll effects.
- Adhere strictly to the timings in `gsap-best-practices.md`.

### 4. Visual Inspection (The "Eyes" via Playwright)
- Mandatory rendering audit of the actual interface.
- Automatic capture and inspection on **4 responsive breakpoints** (Mobile, Tablet, Desktop, Wide).
- Instant correction of geometry errors or AI artifacts.

## Hunting AI Slop (Antipatterns)

| Antipattern | "AI Slop" Tell | Professional Remedy |
|------------|-----------|-----------|
| **Artifacts** | Emojis, stickers, sparkles | Radical suppression |
| **Invented Logos** | Strange graphic placeholders | Stylized typography logos |
| **Wobbly Geometry** | Asymmetrical spacing | Strict 8px grid |
| **Generic shadcn/ui** | "Out of the box" default look | Customization via CSS variables |
| **Generic Icons** | Random Lucide icons without context | Cohesive pack or custom SVG |
| **Cliché Gradients** | Purposeless blue/purple gradients | Solid semantic colors |
| **Low Contrast** | Text or buttons hard to read | WCAG AA compliant colors |
| **Status Badges** | Unrequested uppercase status labels or pulsing dots (e.g. ● LIVE NOW, ATMOSPHÈRE EXCELLENTE) | Radical suppression or explicit justification in DESIGN.md |

## Skill Structure

```
web-design-enhancer/
├── SKILL.md                          # Main documentation
├── README.md                         # This file
├── references/
│   ├── design-md-spec-v2.md        # DESIGN.md specification (shadcn/ui format)
│   ├── gsap-best-practices.md      # GSAP best practices guide
│   └── api_reference.md            # Technical API reference
├── scripts/
│   ├── detect_ai_slop.py           # AI slop and antipattern detector
│   ├── audit_spacing.py            # CSS/TSX spacing grid auditor
│   ├── validate_design.py          # DESIGN.md contract & WCAG contrast validator
│   ├── search.py                   # Semantic BM25 style guide search engine
│   └── visual_audit.py             # Visual layout audit script (Playwright, 4 breakpoints)
└── templates/
    ├── design-system.css           # CSS variables template
    └── design-md-template.md       # DESIGN.md template
```

## Checklist Before Delivery

- [ ] `DESIGN.md` created and mapped onto shadcn/ui.
- [ ] Contrast ratio meets WCAG AA standards (4.5:1 text, 3.0:1 UI).
- [ ] Strict 8px grid respected across the entire website.
- [ ] Zero "decorative" emojis or stickers.
- [ ] Playwright visual audit completed successfully on 4 breakpoints.
- [ ] Fluid and intentional GSAP animations.

---
**Created to transform AI code into exceptional design.**
