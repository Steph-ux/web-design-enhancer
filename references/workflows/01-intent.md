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
