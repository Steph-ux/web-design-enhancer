# Rationalizations — skip resistance

Load this file when tempted to skip a phase, gate, Eyes, or provenance rule under time pressure, user urgency, or “it looks fine.”

**Rule:** an excuse is not a waiver. Either complete the required step or **say incomplete openly**. The skill never authorizes a silent skip.

---

## 1. Excuse table

| Excuse | Reality |
|--------|---------|
| “Gates at the end is enough” | Gate 0/1/2 prevent improvisation; code before green gates is invalid |
| “Playwright / MCP is optional” | Eyes is definition of done for UI modes |
| “Looks fine in the HTML/JSX” | Render + resize required; HTML ≠ pixels |
| “Self aesthetic score is fine” | `reviewer: self` cannot authorize |
| “Archetype replaces getdesign” | False — pillars are mandatory for gate 0 |
| “User said ship fast” | Deliver incomplete openly, or finish Eyes; skill does not authorize silent skip |
| “I’ll write the brief later” | No Phase 0 without brief quality floor |
| “getdesign file already exists” | Must re-run if older than brief or >72h — presence ≠ Phase 0 |
| “I’ll invent Sources §0 from memory” | gate 0 requires real fresh artifacts + documented commands |
| “Pro Max suggested blue crypto fonts — skip the tool” | Run the tool first; reject defaults in writing after |
| “Lock says board, cards ship faster” | final/gate2 lock-vs-code blocks board-promised / cards-delivered |

### How to answer each (agent behavior)

| Excuse | Correct response |
|--------|------------------|
| Gates at the end | Run `check.py --gate 0` then `1` then `2` before structural build; final is not a substitute for early locks |
| Playwright optional | Load `references/vision-playwright.md`; complete MCP (or documented degraded) + mechanical artifacts |
| Looks fine in source | Navigate live URL, resize 375/768/1280, open real PNGs, then judge |
| Self score fine | Use independent-clone / independent / human / panel; rewrite verdict with honest `reviewer` |
| Archetype = getdesign | Keep getdesign anchors + Cross-Domain Steal; archetype is not a pillar replacement |
| Ship fast | State what is missing (e.g. “UI ready; Eyes not run”) or finish Eyes — no fake green |
| Brief later | Stop code; complete creative brief quality floor first |
| getdesign already exists | Delete/overwrite via fresh `npx getdesign@latest add <brand>`; re-run gate 0 |
| Invent Sources | Run pillars; only then fill §0 with real paths |
| Skip Pro Max tool | Run `search.py --design-system --save`; document overrides |
| Lock vs cards | Implement board rows/table or rewrite lock honestly |

---

## 2. Red flags (STOP)

If any of these appear, **STOP**. Do not continue toward a delivery claim until fixed.

- Code written before `check.py --gate 2` green  
- Claim “done” without `./audit-results` fresh artifacts  
- Verdict without real screenshot paths  
- No mobile (375) capture  
- Invented getdesign file / empty design-system-output  
- **Stale** getdesign or design-system-output (older than brief or months old)  
- Structural lock that does not match actual layout (board promised → cards shipped)  
- Claiming pillar runs without tool stdout in the session  

### Additional hard-stop companions (same spirit)

- `reviewer: self` / `agent` / unset used to greenlight `--final`  
- Invented screenshots or empty `mcp/` with no degraded-mode honesty  
- Re-using stale audit while sources changed  
- “Done” after fix loop without re-Eyes  
- Silent skip of Eyes because MCP was missing (must degrade-document or stop)

---

## 3. Soft vs hard compliance

| Soft (chat discipline) | Hard (machine) |
|------------------------|----------------|
| Quote archetype in first code turn | Gate 0/1/2, `--final`, Eyes artifacts |
| Scope list | `detect_ai_slop`, layout L1–L3 |
| Intent narrative | `audit_brief` floor |
| Promise to “check later” | Exit codes + artifact freshness in `check.py` |

v1 does not add cryptographic phase-log. **Exit codes + fresh artifacts** are the enforcement surface. Chat promises do not override red scripts.

---

## 4. Pressure patterns → STOP script

When the user (or internal urgency) pushes:

1. Name the missing hard step in one line.  
2. Offer: **(A)** finish the step now, or **(B)** deliver labeled incomplete.  
3. Never invent green gates, fake Eyes, or self-authorize aesthetics.

Example:

> Incomplete: code is in place but Eyes (Playwright MCP + `visual_audit` / layout / non-self verdict) has not passed. I can run Eyes now, or hand off with that gap explicit.

---

## 5. Related refs

| Need | File |
|------|------|
| Eyes MCP sequence + rubric | `references/vision-playwright.md` |
| Gate map F1–F10 + Eyes | `references/workflows/04-gates.md` |
| Implement recipe before Eyes | `references/workflows/03-implement.md` |
| Orchestrator entry | `SKILL.md` |
