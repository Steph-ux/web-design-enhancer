# Eyes — Playwright MCP protocol (mandatory)

**Load this file before any delivery claim** on UI that was created or changed. Eyes is part of the definition of done for `greenfield`, `implement`, `audit-fix`, and `vision-only`.

**Core rule:** Eyes = Playwright MCP (agent vision + interaction) **AND** Python mechanical scripts — not OR. “Looks fine in the JSX” is not Eyes.

---

## 1. Definition of done

Delivery is allowed only when **all** of the following hold:

1. **Humain** axis — pass  
2. **Fluide** axis — pass  
3. **OK** axis — pass  
4. Fresh mechanical artifacts under `./audit-results/` (`visual_audit.py`, layout when URL, non-self `aesthetic-verdict.json`)  
5. `python3 scripts/eyes_checklist.py --audit-output ./audit-results` exit 0 (when available)  
6. `python3 scripts/check.py --final --code … --url …` exit 0  

One failed Eyes axis = **no delivery claim**. Fix, re-Eyes (≤3), or stop and report incomplete.

---

## 2. Why MCP + scripts (AND, not OR)

| Path | Role |
|------|------|
| **Playwright MCP** | Agent **sees** and interacts: screenshots in context, scroll, hover, console, basic flows. Answers: human? fluid? works? |
| **visual_audit.py** | Mechanical rendered DOM slop + spacing + multi-BP screenshots → `audit_report.json` |
| **audit_layout.py** | Measured overflow / grid integrity at breakpoints |
| **aesthetic_review.py** / agent verdict | Structured `aesthetic-verdict.json` + provenance discounts for `--final` |
| **eyes_checklist.py** | Confirms minimum Eyes artifacts exist before delivery language |

---

## 3. MCP sequence (canonical)

Use the Playwright MCP tools by these **exact names**. Create `./audit-results/mcp/` before screenshots.

```text
1. Confirm live URL
   - Server must respond (default e.g. http://localhost:3000 or project URL).
   - Do not Eyes a dead port.

2. browser_navigate { url }

3. For each viewport:
   required: 375x667, 768x1024, 1280x800
   optional: 1920x1080 (recommended for marketing landings)
   - browser_resize { width, height }
   - browser_take_screenshot → save under audit-results/mcp/
     suggested names: 375.png, 768.png, 1280.png [, 1920.png]
   - optional: fullPage screenshot of hero on desktop only

4. browser_snapshot at mobile (375) and desktop (1280)
   - Note hierarchy, primary CTA presence, landmark structure.

5. Fluidity sample
   - Scroll the page (full scroll once).
   - browser_hover on the primary CTA.
   - Note jank, broken sticky, overlap, dead hover states.

6. browser_console_messages (level=error)
   - Zero unexpected errors for OK pass.
   - Expected dev noise may be noted; product errors fail OK.

7. Optional smoke: click or fill primary flow once
   - No crash, no blank route, no stuck overlay.

8. Write aesthetic-verdict.json
   - Prefer independent-clone: screenshots + rubric only (no brief / DESIGN.md).
   - Schema from aesthetic_review.py (score, reads_as, memorable_idea, reviewer, …).
   - Path: ./audit-results/aesthetic-verdict.json

9.  python3 scripts/visual_audit.py --url <URL> --output ./audit-results

10. python3 scripts/audit_layout.py --url <URL> --json

11. python3 scripts/eyes_checklist.py --audit-output ./audit-results

12. python3 scripts/check.py --final --code <CODE> --url <URL>
    # brand / marketing landings: add --wow unless brief opts out
```

**Order notes:** MCP capture and human rubric (steps 1–8) before or interleaved with mechanical scripts is fine; both must be fresh relative to the current UI. After any UI fix, restart from step 2 (or full re-Eyes).

---

## 4. Rubric (agent must output explicitly)

Judge from **real screenshots** (open the PNG files). Do not invent pixels.

| Axis | Pass criteria |
|------|----------------|
| **Humain** | Reads as human-designed; no AI tells (gradient soup, fake social proof, terminal cosplay, generic Inter+blue); **one named memorable idea** visible in the screenshot |
| **Fluide** | Rhythm/spacing intentional; not monotone 3-col card wall; motion restrained if present; no broken sticky/overlap |
| **OK** | No horizontal overflow; primary CTA clear; content not clipped; console errors clean; mobile usable |

**All three axes must pass.** One fail = no delivery claim.

When writing `aesthetic-verdict.json`, align with engine expectations:

- `reads_as`: `"human"` or `"ai"` — `"ai"` fails F9 / delivery  
- `memorable_idea`: non-null string naming the one owned idea (or fail)  
- `reviewer`: not `self` / `agent` / unset (see provenance)  
- Overall score floors remain those in `check.py` / `04-gates.md` (F9: floor 62 / pass 80 with provenance discounts) — do not invent new pass marks here  

Optional explicit Eyes block in notes or a companion field:

```json
"eyes": {
  "humain": "pass",
  "fluide": "pass",
  "ok": "pass",
  "viewports": ["375x667", "768x1024", "1280x800"],
  "console_errors": 0
}
```

---

## 5. Provenance

| `reviewer` value | Delivery? | Discount (engine) |
|------------------|-----------|-------------------|
| unset / missing | **Blocked** | treated as self |
| `self` / `agent` | **Blocked** | −8 |
| `independent-clone` / `clone` | Allowed | −3 |
| `independent` / other model API | Allowed | 0 |
| `human` | Allowed | 0 |
| Panel (`aesthetic_review.py --panel`) | Allowed for critical launches | per chair aggregation |

**Rules:**

- Default free path: **independent-clone** — fresh subagent, **screenshots + rubric only**, no brief, no DESIGN.md, no generation chat.  
- Critical launches: use **panel** mode.  
- `reviewer: self` / `agent` / unset **cannot authorize** delivery even if the number looks high.  
- Do not lie about provenance (e.g. label `independent-clone` while judging in the same context that wrote the UI).

---

## 6. Artifacts under `./audit-results/`

| Artifact | Source | Required |
|----------|--------|----------|
| `mcp/*.png` (≥3 breakpoints preferred: 375, 768, 1280) | Playwright MCP `browser_take_screenshot` | Yes (or degraded path: ≥2 visual_audit PNGs) |
| Breakpoint / rendered PNGs | `visual_audit.py` | Yes |
| `audit_report.json` | `visual_audit.py` | Yes |
| `aesthetic-verdict.json` | Agent / clone / API / panel | Yes (non-self reviewer) |
| Layout JSON (`audit_layout.py --json` output) | `audit_layout.py` | Preferred when `--url` (F10) |

**Staleness:** if any source file is newer than the audit report / screenshots, re-run Eyes + mechanical before `--final`. Do not ship on stale pixels.

---

## 7. Degraded mode (MCP unavailable)

If Playwright MCP is **not** available in the runtime:

1. **Do not fake Eyes.** Never invent screenshots, console cleanliness, or hover results.  
2. **Preferred fallback:** run Python Playwright scripts, then open real PNGs with vision:

   ```bash
   python3 scripts/visual_audit.py --url <URL> --output ./audit-results
   python3 scripts/audit_layout.py --url <URL> --json
   ```

3. Read the produced PNG files (vision tools / image open). Fill the same Humain / Fluide / OK rubric from **real pixels**.  
4. Document degraded mode in the verdict, e.g.:

   ```json
   "degraded_mode": true,
   "degraded_reason": "Playwright MCP unavailable; judgment from visual_audit PNGs only"
   ```

5. Still require non-self provenance and fresh `audit_report.json`.  
6. `eyes_checklist.py` may accept ≥2 rendered PNGs under the audit dir when `mcp/` is missing — agent must still set the degraded flag honestly.  
7. If scripts cannot produce openable screenshots either: **stop** and report missing Eyes capability. Incomplete delivery only — no silent skip.

---

## 8. Loop (max 3)

```text
Eyes fail (any axis or mechanical/checklist/final red)
  → fix precisely (JSON fix_instruction / refine_loop / targeted CSS-DOM)
  → re-Eyes full sequence (MCP + mechanical)   # count += 1
  → if still red and count < 3: repeat
  → if still red and count == 3: HARD STOP — report remaining failures to human
```

- After **any** UI change, re-Eyes before re-running `--final`.  
- Do not burn iterations on style-only tweaks while overflow or console errors remain.  
- Skill does **not** authorize silent ship after three failed Eyes cycles.

---

## 9. Hard stops (Eyes-specific)

STOP and refuse delivery language when:

- No live URL / no real screenshots  
- Missing mobile **375** capture  
- Verdict without real screenshot paths  
- `reviewer` is self / agent / unset  
- Console product errors ignored  
- Invented or placeholder PNGs  
- Claim “done” without fresh `./audit-results/`  

See also `references/rationalizations.md` when pressure tempts a skip.

---

## 10. Modes that end with Eyes

| Mode | Eyes requirement |
|------|------------------|
| `greenfield` | Full sequence + `--final --url` green |
| `implement` | Full sequence + `--final --url` green |
| `audit-fix` | Re-Eyes after fix loop + `--final` green |
| `vision-only` | MCP (or degraded) + mechanical + rubric/artifacts; no full redesign required |

“Quick ship without Eyes” is **out of scope**. Reframe as incomplete or finish Eyes.
