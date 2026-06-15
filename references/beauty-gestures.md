# Beauty Gestures — the positive recipe per archetype

> Companion to `design-archetypes.md` and the Beauty Score gate (`scripts/audit_beauty.py`).
> Version 1.0

## Why this document exists

`design-archetypes.md` tells the model **what to avoid** and gives it tokens. It does
not tell it the small, deliberate moves that make a layout read as the work of a
human designer rather than a competent template. "Not generic" is not "beautiful".

This file supplies the **positive recipe**: for each archetype, 2–3 *signature
gestures* — concrete, copy-pasteable details that carry craft — plus one
**validated font pairing** that escapes the AI defaults (Inter-everywhere,
Inter+Poppins, Inter+Roboto).

Each gesture is tagged with the Beauty Score dimension it raises, so the model can
aim its effort where the gate measures it:

| Dim | What it rewards | Gesture lever |
|-----|-----------------|---------------|
| **D1** | Type-scale contrast — the H1 dominates | A genuinely large display size, tight tracking |
| **D2** | Hierarchy richness — ≥5 distinct sizes | A full modular scale, not 2 sizes |
| **D3** | Colour intentionality — a signature accent (not blue) | One deliberate, owned colour |
| **D4** | Spacing rhythm — varied, generous whitespace | A real section gap (≥64px) + varied steps |
| **D5** | Finition — hover, focus-visible, transitions, reduced-motion | State polish on every interactive element |

**Rule:** pick the gestures of the archetype you committed to. Mixing gestures across
archetypes reproduces the averaged look the whole system fights.

---

## Universal craft floor (every archetype)

These four moves alone lift a flat page off the floor of the Beauty Score. Do them
regardless of archetype:

1. **Optical, not just mathematical spacing (D4).** The 8px grid is the minimum, not
   the goal. Let section gaps breathe at `clamp(64px, 8vw, 160px)`; keep intra-card
   gaps tight (8–24px). Uniform padding everywhere reads as a wall.
2. **A real type scale (D1/D2).** Build ≥5 steps on a ratio (1.25 minor-third or 1.333
   perfect-fourth): `--step--1`, `--step-0` (body), `--step-1` … `--step-5` (display).
   The display step should land ≥2.4× the body.
3. **One owned accent (D3).** A single colour that is *not* blue/indigo and *not* a
   neutral, used sparingly. If everything is grey, the page has no voice.
4. **Finish every state (D5).** `:hover`, `:focus-visible`, a ≤200ms `transition`, and a
   `@media (prefers-reduced-motion: reduce)` guard. This is the single cheapest, most
   reliable signal of a human hand.

```css
/* Drop-in modular scale (perfect-fourth, 1.333) — feeds D1 + D2 */
:root {
  --step--1: clamp(0.83rem, 0.8rem + 0.2vw, 0.94rem);
  --step-0:  clamp(1rem,   0.95rem + 0.3vw, 1.13rem);   /* body */
  --step-1:  clamp(1.33rem, 1.2rem + 0.6vw, 1.5rem);
  --step-2:  clamp(1.78rem, 1.5rem + 1.2vw, 2rem);
  --step-3:  clamp(2.37rem, 2rem + 1.9vw, 2.66rem);
  --step-4:  clamp(3.16rem, 2.5rem + 3.3vw, 3.55rem);
  --step-5:  clamp(4.21rem, 3rem + 6vw, 5.6rem);        /* display — ≥2.4× body */
}
:where(a, button, [role="button"]) {
  transition: color .18s ease, background-color .18s ease, transform .18s ease;
}
:where(a, button):focus-visible { outline: 2px solid var(--color-accent); outline-offset: 2px; }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { transition: none !important; animation: none !important; } }
```

---

## Per-archetype gestures

### 01 — Swiss / Typographic
**Font pairing (escape Inter-only):** display **Archivo** (or **Neue Haas Grotesk** if licensed) + body **Inter Tight**. Keep one family if you want true Swiss purity, but vary weight hard (900 vs 400).
- **G1 (D1)** Oversized weight contrast: H1 at `font-weight: 900` and `--step-5`, body at `400`. The contrast *is* the design.
- **G2 (D4)** Expose the grid: a visible 12-col baseline with a hairline `1px` rule (`var(--color-border)`) separating major sections — no shadows.
- **G3 (D3)** One pure accent (`#FF0000`, `#FFDD00`, or `#0033CC`) on links and the single primary action only. Never tint it.

### 02 — Editorial / Magazine
**Font pairing:** display **Playfair Display** (or **Fraunces** for warmth) + body **Source Serif 4**. Avoid pairing the serif with Inter — keep it serif-on-serif or serif + a humanist sans like **Söhne**.
- **G1 (D1)** A true masthead: display at `--step-5`, `line-height: 0.95`, optical margin so the cap-height aligns to the grid, not the line-box.
- **G2 (D4)** Drop cap on the lead paragraph (`::first-letter { float: left; font-size: 3.2em; line-height: .8; }`) and a measure capped at `65ch` for body.
- **G3 (D5)** Underline links with `text-underline-offset: 0.18em` and a colour-shift on hover, never a default browser underline.

### 03 — Luxury / Restrained
**Font pairing:** display **Cormorant Garamond** (weight 300) + body **Jost** (300). Drop the `Inter` fallback in `--font-body`.
- **G1 (D3/D4)** Whitespace as the material: side margins `clamp(60px, 15vw, 200px)`, section gaps `clamp(120px, 18vw, 240px)`. The emptiness is the luxury.
- **G2 (D3)** Tracked small-caps labels: `text-transform: uppercase; letter-spacing: 0.18em; font-size: 0.6875rem;` above each section title. A single warm accent (`#B8945F` gold) on hairline rules only.
- **G3 (D5)** Near-imperceptible fades (`transition: opacity 1.2s ease`), no transform, no bounce. Restraint in motion = restraint in everything.

### 04 — Brutalist / Raw
**Font pairing:** display **Space Mono** + body **Space Grotesk**. Already distinctive — lean in.
- **G1 (D3)** Raw structure: visible `2px solid #000` borders, zero radius, hard offset "shadow" (`box-shadow: 8px 8px 0 #000`) instead of a blur.
- **G2 (D1)** Brutal scale jumps: skip mid steps — body then display, nothing between, for deliberate visual shock.
- **G3 (D5)** Inverting hover: `:hover { background: #000; color: var(--color-bg); }` — instant, no transition, the bluntness is the point (still add the reduced-motion guard for consistency).

### 05 — Organic / Hand-crafted
**Font pairing:** display **Fraunces** (optical, soft) + body **Cabinet Grotesk** (or **DM Sans**). Drop the `Inter` fallback.
- **G1 (D3)** Earthy owned palette (clay `#C1440E`, sage `#6B8F71`, cream `#FAF7F0`) — warm, never saturated primaries.
- **G2 (D4)** Asymmetric, off-grid placement: let images bleed and captions hang in the margin. Organic ≠ centered.
- **G3 (D5)** Soft, slow ease (`cubic-bezier(.22,1,.36,1)`, 300–400ms) on reveals — motion that feels grown, not snapped.

### 06 — Technical / Monochrome
**Font pairing:** display + body **Geist** (or **Geist Mono** for code). Keep one family; the craft is in the spacing, not the typeface.
- **G1 (D3)** Monochrome with a single semantic accent (e.g. `#22C55E` for "ok" states) — used only where it carries meaning, never decoration.
- **G2 (D4)** Dense but rhythmic: tabular numbers (`font-variant-numeric: tabular-nums`), `4px`/`8px` micro-spacing inside rows, generous `64px+` between regions.
- **G3 (D5)** Crisp focus rings and `0.12s` transitions — fast, precise, no easing flourish. Keyboard-first polish (`:focus-visible`) is non-negotiable here.

### 07 — Playful / Expressive
**Font pairing:** display **Syne** (or **Clash Display**) + body **DM Sans**. Avoid Poppins entirely.
- **G1 (D1)** Huge, confident display (`--step-5`+), tight `line-height: 0.9`, optionally a `-2deg` rotation on one word for character.
- **G2 (D3)** A bold 2–3 colour owned palette with one unexpected pairing (e.g. coral + ink + lime). This is the one archetype where chroma is the voice.
- **G3 (D5)** Springy but brief micro-interactions (`transform: scale(1.04)` on hover, `transition: .2s cubic-bezier(.34,1.56,.64,1)`) — always behind the reduced-motion guard.

### 08 — Data / Dashboard
**Font pairing:** display **Geist** + body **IBM Plex Sans** (numbers in **IBM Plex Mono** or tabular Geist). Move off bare Inter for distinctiveness.
- **G1 (D3)** Restrained semantic palette (one neutral base + success/warn/danger) — colour means status, never branding. No gradient fills on charts.
- **G2 (D2/D4)** Clear data hierarchy: big KPI numbers at `--step-3+`, labels at `--step--1` with tracking, generous gutters between cards (`24–32px`), full-bleed section breaks.
- **G3 (D5)** Hover-reveal detail (tooltips, row highlight at `background: var(--color-surface)`) with a `0.1s` transition — responsive, not flashy.

### 09 — Retro / Nostalgic
**Font pairing:** era-dependent — pixel: **VT323**; 70s: **Bebas Neue** + **Work Sans**; 80s: **Monument Extended**. Commit to one era.
- **G1 (D3)** Period-accurate owned palette (CRT amber `#FFB000`, or 70s mustard/rust/avocado) — the palette *is* the nostalgia.
- **G2 (D4)** Era texture used structurally, not as wallpaper: scanline divider, chunky 4px borders, deliberate grid.
- **G3 (D5)** A single in-character motion (a CRT flicker on load, a typewriter on one heading) — exactly one, behind the reduced-motion guard, never everywhere.

### 10 — Material / Tactile
**Font pairing:** display + body **Roboto Flex** (true Material) or **Geist** for a fresher take. Avoid the lazy Inter default.
- **G1 (D5)** Real elevation system: documented shadow tiers (`--elevation-1 … 3`) that change on interaction (`:hover` lifts one tier with a `.2s` transition) — depth that responds.
- **G2 (D3)** One tonal accent driving the whole surface system (Material "primary" → surface tints), not a colour sprinkled on buttons.
- **G3 (D4)** Consistent 8dp rhythm with intentional density tiers (comfortable vs compact), and a real FAB/primary action with `44px+` touch height.

---

## Quick map: gesture → Beauty Score dimension

| Archetype | D1 (scale) | D3 (colour) | D4 (rhythm) | D5 (finish) |
|-----------|-----------|-------------|-------------|-------------|
| 01 Swiss | weight 900 H1 | one pure accent | hairline grid | — |
| 02 Editorial | masthead | — | drop cap + 65ch | underline hover |
| 03 Luxury | — | gold hairlines | extreme whitespace | 1.2s fades |
| 04 Brutalist | brutal jumps | hard offset shadow | — | invert hover |
| 05 Organic | — | earthy palette | off-grid bleed | slow ease |
| 06 Technical | — | one semantic accent | tabular density | crisp focus |
| 07 Playful | huge display | bold 2–3 palette | — | spring micro |
| 08 Data | KPI scale | status colour | card gutters | hover reveal |
| 09 Retro | — | era palette | era texture | one motion |
| 10 Material | — | tonal accent | 8dp density | elevation lift |

> After applying gestures, run `python3 scripts/audit_beauty.py --path ./src`.
> Aim for ≥70/100. A score <50 means the gestures are decorative, not structural —
> revisit D1 (does the H1 truly dominate?) and D4 (does the layout breathe?).
