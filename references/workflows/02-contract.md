# Workflow 02 — Contract (Phase 0–1)

## Hard stop
Do not invent DESIGN.md from priors. Archetype ≠ substitute for pillars.  
**Reusing an old `getdesign-*.md` or inventing Sources §0 without tool runs will fail gate 0.**

## Skill scripts path

```text
SKILL = path to web-design-enhancer-pro install
        e.g. ~/.claude/skills/web-design-enhancer-pro
```

Always: `python3 $SKILL/scripts/search.py` and `python3 $SKILL/scripts/check.py`.

## Steps (order is mandatory — show outputs)

1. **Pillar 2 — UI/UX Pro Max (must RUN now)**  
   ```bash
   python3 $SKILL/scripts/search.py "<product description>" --design-system -p "<Project>" --save
   ```  
   → produces **fresh** `design-system-output*.md` in the **project cwd**  
   → paste key palette/type/antipatterns into DESIGN.md (you may reject crypto-blue defaults, but you must **run** then **document why**)

2. **Pillar 1 — getdesign (must RUN now)**  
   ```bash
   npx getdesign@latest add <brand>
   ```  
   → produces **fresh** `getdesign-*.md` / `brand-*.md`  
   → Prefer ≥1 non-SaaS when possible (`$SKILL/data/getdesign-references.csv`)  
   → **Delete or overwrite** any stale getdesign file from another project/date

3. **Merge → DESIGN.md** (`templates/design-md-template.md`)  
   - Conflict: Pro Max wins structure; getdesign refines texture  
   - `## 0. Sources Phase 0` must list **real** commands + artifact filenames  
   - No placeholders

4. **Gate 0** (freshness enforced)  
   ```bash
   python3 $SKILL/scripts/check.py --gate 0
   ```  
   Fails if pillars missing, **older than CREATIVE-BRIEF.md**, or **>72h old**.

5. Complete §2–§12; signature §11 + tensions §12  

6. **Gate 1**  
   ```bash
   python3 $SKILL/scripts/check.py --gate 1
   ```

## What “bypass” looks like (blocked)

| Bypass | Gate reaction |
|--------|----------------|
| Invent DESIGN.md without search/getdesign | gate 0 missing artifacts |
| Copy June `getdesign-bugatti.md` into July project | gate 0 stale / older than brief |
| Write “Command executed: npx …” without running | gate 0 if file still old |
| Skip Pro Max because “archetype is enough” | gate 0 missing design-system-output |

## Pass
Gate 0 + gate 1 green. No application code yet (unless redesign: then lock must match UI).
