#!/usr/bin/env python3
"""
audit_gestures.py - Gate 9: Signature-Gesture Enforcement

The missing generative gate. The rest of the skill VALIDATES (no slop, WCAG,
8px grid) and SCORES craft (audit_beauty). None of it forces the model to
actually IMPLEMENT the signature gestures that beauty-gestures.md prescribes
for the archetype it committed to.

Failure mode this gate catches ("tokens without gestures"):
the model adopts an archetype's TOKENS (serif fonts, radius 0, paper bg for
"Editorial") but never lays down the GESTURES that make the archetype sing
(masthead, drop cap, 65ch measure, underline-offset hover). Result: a page
that passes every other gate yet reads as a competent template, not a design.

This gate reads the committed archetype (from --archetype, or auto-detected via
the DESIGN.md font pairing) and verifies that >= threshold of its prescribed
signature gestures are present in the code. Works on raw CSS *and* Tailwind/JSX.

Usage:
  python3 scripts/audit_gestures.py --code ./src --archetype "02 Editorial"
  python3 scripts/audit_gestures.py --code ./src --design DESIGN.md   # auto-detect
  python3 scripts/audit_gestures.py --code ./src --archetype 4 --json
  python3 scripts/audit_gestures.py --code ./src --archetype editorial --threshold 3

Exit codes:
  0 = PASS (archetype unknown -> non-blocking WARN, or enough gestures present)
  1 = BLOCKED (archetype committed but signature gestures missing)
"""

import sys
import re
import json
import argparse
import math
from pathlib import Path

# --- ASCII tags (cp1252-safe, matches the rest of the skill) ---------------
def tag_ok(m):   return f"  [OK] {m}"
def tag_no(m):   return f"  [--] {m}"
def tag_warn(m): return f"  [WARN] {m}"

CODE_EXTS = {".css", ".scss", ".sass", ".less", ".tsx", ".jsx",
             ".ts", ".js", ".html", ".htm", ".vue", ".astro", ".svelte"}

# ---------------------------------------------------------------------------
# Signature-gesture catalog, derived 1:1 from references/beauty-gestures.md.
# Each archetype carries:
#   - name, aliases (for --archetype matching)
#   - fonts: lowercase substrings used to AUTO-DETECT the archetype from the
#            DESIGN.md / CSS font pairing (beauty-gestures.md ties one pairing
#            to each archetype)
#   - gestures: 3 signature moves. Each has any-of `patterns` (regex, matched
#            against lowercased code) so it fires on raw CSS OR Tailwind/JSX.
# ---------------------------------------------------------------------------
ARCHETYPES = {
    "01": {
        "name": "Swiss / Typographic",
        "aliases": ["swiss", "typographic", "grotesk", "1"],
        "fonts": ["archivo", "neue haas", "inter tight"],
        "gestures": [
            {"id": "G1", "dim": "D1", "label": "Oversized weight contrast (H1 900 vs body 400)",
             "patterns": [r"font-weight:\s*900", r"font-weight:\s*800", r"font-black\b", r"font-extrabold\b"],
             "fix": "Set the H1 to font-weight:900 at the display step, body at 400. The weight contrast IS the design."},
            {"id": "G2", "dim": "D4", "label": "Exposed grid: hairline 1px rules / 12-col",
             "patterns": [r"border(-top|-bottom|-left|-right|-[xy])?:\s*1px\s+solid", r"repeat\(\s*12", r"grid-cols-12", r"\bdivide-[xy]\b", r"\bborder-t\b"],
             "fix": "Separate major sections with a visible 1px hairline rule (no shadow); expose a 12-col grid."},
            {"id": "G3", "dim": "D3", "label": "One pure accent on links/primary only",
             "patterns": [r"#ff0000\b", r"#f00\b", r"#ffdd00\b", r"#0033cc\b", r"#ff3333\b", r"#c{2,3}\b", r"#cc0000\b"],
             "fix": "Use ONE pure accent (#FF0000 / #FFDD00 / #0033CC) on links and the single primary action. Never tint it."},
        ],
    },
    "02": {
        "name": "Editorial / Magazine",
        "aliases": ["editorial", "magazine", "news", "journal", "2"],
        "fonts": ["playfair", "fraunces", "source serif", "sohne", "soehne", "freight"],
        "gestures": [
            {"id": "G1", "dim": "D1", "label": "True masthead: display at clamp display step, line-height ~0.95",
             "patterns": [r"line-height:\s*0?\.9\d?", r"masthead", r"leading-\[0?\.9"],
             "fix": "Build a real masthead: display headline at the largest step with line-height:0.95 and optical margin."},
            {"id": "G2", "dim": "D4", "label": "Drop cap on lead + measure capped at ~65ch",
             "patterns": [r"::?first-letter", r"first-letter:", r"max-width:\s*\d{2}ch", r"max-w-\[\d\dch\]", r"max-w-prose"],
             "fix": "Add a drop cap (::first-letter{float:left;font-size:3.2em}) and cap body measure at 65ch."},
            {"id": "G3", "dim": "D5", "label": "Links: underline-offset + colour shift on hover",
             "patterns": [r"text-underline-offset", r"underline-offset-\[", r"text-decoration-thickness"],
             "fix": "Style links with text-underline-offset:0.18em and a hover colour shift, never the default underline."},
        ],
    },
    "03": {
        "name": "Luxury / Restrained",
        "aliases": ["luxury", "restrained", "premium", "fashion", "3"],
        "fonts": ["cormorant", "jost", "ogg", "canela"],
        "gestures": [
            {"id": "G1", "dim": "D4", "label": "Whitespace as material (margins 15vw, gaps >=120px)",
             "patterns": [r"clamp\([^)]*\b(1[2-9]\d|2\d\d)px", r"(margin|padding|gap):[^;]*\b(1[5-9]\d|2\d\d)px", r"\b1[5-9]vw\b", r"\b18vw\b", r"clamp\([^)]*15vw"],
             "fix": "Side margins clamp(60px,15vw,200px); section gaps clamp(120px,18vw,240px). The emptiness IS the luxury."},
            {"id": "G2", "dim": "D3", "label": "Tracked small-caps labels (letter-spacing >=0.15em)",
             "patterns": [r"letter-spacing:\s*0?\.1[5-9]em", r"letter-spacing:\s*0?\.2\d?em", r"tracking-\[0?\.1[5-9]em\]", r"tracking-widest"],
             "fix": "Section labels in uppercase tracked small-caps (letter-spacing:0.18em); a single warm accent on hairlines only."},
            {"id": "G3", "dim": "D5", "label": "Near-imperceptible slow fades (>=0.8s, no transform)",
             "patterns": [r"transition:[^;{]*\b(0?\.[89]|1(\.\d)?)s", r"opacity\s+1(\.\d)?s", r"duration-\[?(8|9|1[0-9])00"],
             "fix": "Reveals via opacity transition 1.2s ease, no transform, no bounce. Restraint in motion = restraint everywhere."},
        ],
    },
    "04": {
        "name": "Brutalist / Raw",
        "aliases": ["brutalist", "brutalism", "raw", "neubrutalism", "neo-brutalism", "4"],
        "fonts": ["space mono", "space grotesk"],
        "gestures": [
            {"id": "G1", "dim": "D3", "label": "Hard offset shadow (no blur): box-shadow Npx Npx 0",
             "patterns": [r"box-shadow:\s*-?\d+px\s+-?\d+px\s+0(px)?[\s;)#]", r"shadow-\[\d+px_\d+px_0"],
             "fix": "Replace blurred shadows with a hard offset: box-shadow:8px 8px 0 #000. The bluntness is the point."},
            {"id": "G2", "dim": "D1", "label": "Heavy raw borders (>=2px solid)",
             "patterns": [r"border(-\w+)?:\s*[2-9]px\s+solid", r"\bborder-[2-8]\b"],
             "fix": "Visible 2px+ solid black borders, zero radius. Structure is exposed, not softened."},
            {"id": "G3", "dim": "D5", "label": "Inverting hover (bg<->fg flip)",
             "patterns": [r":hover[^}]*\{[^}]*background[^}]*#?(000|000000)", r"hover:bg-black", r":hover[^}]*background:\s*var\(--color-ink"],
             "fix": "On hover, invert: background:#000;color:var(--bg). Instant, no transition."},
        ],
    },
    "05": {
        "name": "Organic / Hand-crafted",
        "aliases": ["organic", "biophilic", "handcrafted", "hand-crafted", "natural", "5"],
        "fonts": ["fraunces", "cabinet grotesk", "dm sans"],
        "gestures": [
            {"id": "G1", "dim": "D3", "label": "Earthy owned palette (clay / sage / cream)",
             "patterns": [r"#c1440e", r"#6b8f71", r"#faf7f0", r"#b8945f", r"#(d2691e|cd853f|deb887|bc8f8f|8fbc8f)"],
             "fix": "Use a warm earthy palette (clay #C1440E, sage #6B8F71, cream #FAF7F0), never saturated primaries."},
            {"id": "G2", "dim": "D4", "label": "Asymmetric off-grid placement / bleed",
             "patterns": [r"(margin|inset)(-left|-right)?:\s*-\d", r"\b100vw\b", r"translatex\(-?\d", r"-m[lrxt]-\d", r"justify-self-(start|end)"],
             "fix": "Let images bleed and captions hang in the margin. Organic != centered grid."},
            {"id": "G3", "dim": "D5", "label": "Soft slow ease on reveals (cubic-bezier .22,1)",
             "patterns": [r"cubic-bezier\(\s*0?\.22\s*,\s*1", r"cubic-bezier\([^)]*\)[^;]*(3\d\d|400)ms", r"ease[^;]*(3\d\d|400)ms"],
             "fix": "Reveals on cubic-bezier(.22,1,.36,1) over 300-400ms. Motion that feels grown, not snapped."},
        ],
    },
    "06": {
        "name": "Technical / Monochrome",
        "aliases": ["technical", "monochrome", "devtool", "dev-tool", "infra", "6"],
        "fonts": ["geist", "ibm plex", "jetbrains"],
        "gestures": [
            {"id": "G1", "dim": "D3", "label": "Single semantic accent (meaning, not decoration)",
             "patterns": [r"#22c55e", r"--(success|ok|warn|warning|danger|error|info)\b", r"var\(--(success|danger|warn"],
             "fix": "One semantic accent (e.g. #22C55E for ok) used only where it carries meaning."},
            {"id": "G2", "dim": "D4", "label": "Tabular numerics + rhythmic density",
             "patterns": [r"tabular-nums", r"font-variant-numeric", r"tabular"],
             "fix": "font-variant-numeric:tabular-nums; tight 4/8px micro-spacing in rows, 64px+ between regions."},
            {"id": "G3", "dim": "D5", "label": "Crisp focus rings + fast 0.12s transitions",
             "patterns": [r":focus-visible", r"transition:[^;{]*0?\.1\d?s", r"focus-visible:"],
             "fix": "Crisp :focus-visible rings and 0.12s transitions. Keyboard-first polish is non-negotiable here."},
        ],
    },
    "07": {
        "name": "Playful / Expressive",
        "aliases": ["playful", "expressive", "fun", "vibrant", "7"],
        "fonts": ["syne", "clash display", "dm sans"],
        "gestures": [
            {"id": "G1", "dim": "D1", "label": "Huge confident display, tight LH, optional tilt",
             "patterns": [r"rotate\(-?\d+deg\)", r"line-height:\s*0?\.9", r"-rotate-\d", r"leading-none"],
             "fix": "Huge display (step-5+), line-height:0.9, optionally a -2deg tilt on one word for character."},
            {"id": "G2", "dim": "D3", "label": "Bold 2-3 colour palette with one unexpected pairing",
             "patterns": [r"--accent-[23]", r"#(f43f5e|fb7185|84cc16|a3e635|f59e0b|fb923c)", r"coral"],
             "fix": "A bold 2-3 colour owned palette (e.g. coral + ink + lime). Here chroma is the voice."},
            {"id": "G3", "dim": "D5", "label": "Springy brief micro-interactions",
             "patterns": [r"cubic-bezier\([^)]*1\.5", r"cubic-bezier\(\s*0?\.34\s*,\s*1\.56", r"scale\(1\.0?[3-9]\)", r"hover:scale-1"],
             "fix": "Spring micro-interactions: scale(1.04) on hover, cubic-bezier(.34,1.56,.64,1). Behind reduced-motion guard."},
        ],
    },
    "08": {
        "name": "Data / Dashboard",
        "aliases": ["data", "dashboard", "analytics", "8"],
        "fonts": ["geist", "ibm plex"],
        "gestures": [
            {"id": "G1", "dim": "D3", "label": "Restrained semantic palette (status, not branding)",
             "patterns": [r"--(success|warn|warning|danger|error)\b", r"var\(--(success|danger|warn"],
             "fix": "One neutral base + success/warn/danger. Colour means status, never branding. No gradient chart fills."},
            {"id": "G2", "dim": "D2", "label": "Clear KPI hierarchy + generous card gutters",
             "patterns": [r"gap:\s*(24|28|32)px", r"tabular-nums", r"--step-[3-5]", r"gap-[678]\b"],
             "fix": "Big KPI numbers at step-3+, labels at step--1 with tracking, 24-32px gutters between cards."},
            {"id": "G3", "dim": "D5", "label": "Hover-reveal detail (tooltip / row highlight, 0.1s)",
             "patterns": [r":hover[^}]*background", r"tooltip", r"transition:[^;{]*0?\.1\d?s", r"hover:bg-"],
             "fix": "Hover-reveal tooltips / row highlight with a 0.1s transition. Responsive, not flashy."},
        ],
    },
    "09": {
        "name": "Retro / Nostalgic",
        "aliases": ["retro", "nostalgic", "vintage", "y2k", "vaporwave", "pixel", "9"],
        "fonts": ["vt323", "bebas neue", "monument extended", "press start"],
        "gestures": [
            {"id": "G1", "dim": "D3", "label": "Period-accurate owned palette (CRT amber / 70s)",
             "patterns": [r"#ffb000", r"#(ff8c00|cc5500|d2691e|808000)", r"amber", r"mustard"],
             "fix": "A period-accurate palette (CRT amber #FFB000, or 70s mustard/rust/avocado). The palette IS the nostalgia."},
            {"id": "G2", "dim": "D4", "label": "Era texture used structurally (scanline / chunky)",
             "patterns": [r"repeating-linear-gradient", r"scanline", r"image-rendering:\s*pixelated", r"border(-\w+)?:\s*4px"],
             "fix": "Era texture as structure: scanline divider, chunky 4px borders, deliberate grid - not wallpaper."},
            {"id": "G3", "dim": "D5", "label": "Exactly one in-character motion",
             "patterns": [r"@keyframes\s+(flicker|crt|typewriter|blink|glitch)", r"steps\(\d"],
             "fix": "ONE in-character motion (CRT flicker on load, or typewriter on one heading). Behind reduced-motion guard."},
        ],
    },
    "10": {
        "name": "Material / Tactile",
        "aliases": ["material", "tactile", "md3", "material-you", "10"],
        "fonts": ["roboto flex", "roboto", "geist"],
        "gestures": [
            {"id": "G1", "dim": "D5", "label": "Real elevation system that lifts on interaction",
             "patterns": [r"--elevation", r"--shadow-[123]", r":hover[^}]*box-shadow", r"hover:shadow-"],
             "fix": "Documented shadow tiers (--elevation-1..3) that lift one tier on :hover over 0.2s. Depth that responds."},
            {"id": "G2", "dim": "D3", "label": "One tonal accent driving the surface system",
             "patterns": [r"--surface", r"--primary[^:]*:", r"surface-tint", r"--md-sys"],
             "fix": "One tonal 'primary' accent driving surface tints, not a colour sprinkled on buttons."},
            {"id": "G3", "dim": "D4", "label": "8dp rhythm + real 44px+ touch targets",
             "patterns": [r"(min-height|height):\s*(44|48|56)px", r"\b8dp\b", r"(min-h|h)-(11|12|14)\b"],
             "fix": "Consistent 8dp rhythm, density tiers, a real FAB/primary action with 44px+ touch height."},
        ],
    },
}


def resolve_archetype(arg: str | None, design_text: str, code_text: str):
    """Return (key, source) for the committed archetype, or (None, reason)."""
    # 1. Explicit --archetype: match by leading number, key, name, or alias.
    if arg:
        a = arg.strip().lower()
        num = re.match(r"\s*0?(\d{1,2})", a)
        if num:
            key = num.group(1).zfill(2)
            if key in ARCHETYPES:
                return key, "explicit (--archetype)"
        for key, spec in ARCHETYPES.items():
            if a == spec["name"].lower() or a in spec["aliases"] or a in spec["name"].lower():
                return key, "explicit (--archetype)"
        # fall through to auto-detect if the arg was unrecognised

    # 2. Auto-detect from the declared font pairing (DESIGN.md preferred, else code).
    for source_name, text in (("DESIGN.md font pairing", design_text), ("code font pairing", code_text)):
        if not text:
            continue
        low = text.lower()
        # score each archetype by how many of its signature fonts appear
        scored = []
        for key, spec in ARCHETYPES.items():
            hits = sum(1 for f in spec["fonts"] if f in low)
            if hits:
                scored.append((hits, key))
        if scored:
            scored.sort(reverse=True)
            top = [k for h, k in scored if h == scored[0][0]]
            if len(top) == 1:
                return top[0], f"auto-detected ({source_name})"
            # ambiguous (e.g. Fraunces -> Editorial or Organic): cannot decide
            return None, ("ambiguous font pairing matches multiple archetypes "
                          f"({', '.join(ARCHETYPES[k]['name'] for k in top)}) - pass --archetype")
    return None, "no archetype declared and none detectable from fonts"


def collect_code(code_path: Path):
    files, text = [], []
    if code_path.is_file():
        candidates = [code_path]
    else:
        candidates = [p for p in code_path.rglob("*") if p.suffix.lower() in CODE_EXTS
                      and "node_modules" not in p.parts and ".next" not in p.parts]
    for p in candidates:
        try:
            text.append(p.read_text(encoding="utf-8", errors="ignore"))
            files.append(p)
        except Exception:
            pass
    return "\n".join(text).lower(), files


def audit(code_text, key):
    spec = ARCHETYPES[key]
    results = []
    for g in spec["gestures"]:
        present = any(re.search(p, code_text) for p in g["patterns"])
        results.append({"id": g["id"], "dim": g["dim"], "label": g["label"],
                        "present": present, "fix": g["fix"]})
    return spec, results


def main():
    ap = argparse.ArgumentParser(prog="audit_gestures",
                                 description="Gate 9 - signature-gesture enforcement per archetype")
    ap.add_argument("--code", default=".", help="Source code path (file or dir)")
    ap.add_argument("--archetype", default=None,
                    help="Committed archetype: number (1-10), key ('02'), name or alias ('editorial')")
    ap.add_argument("--design", default="DESIGN.md",
                    help="DESIGN.md path, used to auto-detect the archetype from its font pairing")
    ap.add_argument("--threshold", type=int, default=2,
                    help="Minimum gestures (of 3) that must be present to PASS (default 2)")
    ap.add_argument("--strict", action="store_true",
                    help="Block (exit 1) when the archetype cannot be determined, instead of warning")
    ap.add_argument("--json", action="store_true", help="Machine-readable output")
    args = ap.parse_args()

    code_path = Path(args.code)
    code_text, files = collect_code(code_path)
    design_text = ""
    dp = Path(args.design)
    if dp.exists():
        design_text = dp.read_text(encoding="utf-8", errors="ignore")

    key, source = resolve_archetype(args.archetype, design_text, code_text)

    if key is None:
        payload = {"status": "unknown", "reason": source, "blocked": bool(args.strict)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print("\n" + "=" * 60)
            print("  SIGNATURE-GESTURE AUDIT (Gate 9)")
            print("=" * 60 + "\n")
            print(tag_warn(f"Archetype not determined: {source}."))
            print("       Pass --archetype \"02 Editorial\" (or 1-10) so the gate can enforce its gestures.")
            print("=" * 60 + "\n")
        sys.exit(1 if args.strict else 0)

    spec, results = audit(code_text, key)
    present = [r for r in results if r["present"]]
    n_present, n_total = len(present), len(results)
    passed = n_present >= args.threshold

    if args.json:
        print(json.dumps({
            "status": "pass" if passed else "blocked",
            "archetype": f"{key} {spec['name']}",
            "source": source,
            "present": n_present, "total": n_total, "threshold": args.threshold,
            "blocked": not passed,
            "gestures": results,
            "files_scanned": len(files),
        }, indent=2))
        sys.exit(0 if passed else 1)

    bar_w = 24
    filled = round(bar_w * n_present / n_total) if n_total else 0
    print("\n" + "=" * 60)
    print("  SIGNATURE-GESTURE AUDIT (Gate 9)")
    print("=" * 60 + "\n")
    print(f"  Archetype: {key} {spec['name']}  [{source}]")
    print(f"  Gestures present: {n_present}/{n_total}  (need >= {args.threshold})")
    print("  [" + "#" * filled + "-" * (bar_w - filled) + "]\n")
    print("  Signature gestures for this archetype:")
    for r in results:
        mark = tag_ok if r["present"] else tag_no
        print(mark(f"{r['id']} ({r['dim']}) {r['label']}"))
    missing = [r for r in results if not r["present"]]
    if missing:
        print("\n  How to earn the missing gestures:\n")
        for r in missing:
            print(f"  [{r['id']}] {r['fix']}")
    print("\n" + "=" * 60)
    if passed:
        print(f"  [OK] PASSED - {n_present}/{n_total} signature gestures present.")
        print(f"       This reads as a committed {spec['name']} design, not just its tokens.")
    else:
        print(f"  [BLOCKED] Only {n_present}/{n_total} gestures present (need >= {args.threshold}).")
        print("       TOKENS WITHOUT GESTURES: the archetype's look is adopted but not its craft.")
        print("       Implement the missing gestures above, then re-run.")
    print("=" * 60 + "\n")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
