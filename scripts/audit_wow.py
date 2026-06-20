#!/usr/bin/env python3
"""
audit_wow.py - WOW mode: rewards deliberate excess in the ONE hero dimension.

The other gates are floors: they STOP the bad (slop, tepid briefs, tokens
without gestures) and let "clean" through. None of them actively pushes a design
PAST competent into memorable. "Waouh comes from going too far in ONE direction,
not from balancing five" (beauty-gestures.md). This gate measures exactly that.

It is OPT-IN (not part of `check.py --final` unless you pass `--wow`), because a
trust-first / public-sector product legitimately should NOT shout. Use it when
the brief's ambition is a striking, memorable result.

Score 0-100 across four levers, read against the brief's committed Hero Dimension:

  W1 Hero dimension pushed to excess  (40) - the ONE dimension treated with excess
  W2 All 3 signature gestures present (30) - not 2 of 3; the full archetype craft
  W3 A Design Dial pushed to extreme  (15) - <=2 or >=9, not all mid-range
  W4 An owned signature move, in code (15) - DESIGN.md section 11 grep, found in code

Usage:
  python3 scripts/audit_wow.py --code ./src
  python3 scripts/audit_wow.py --code ./src --archetype "02 Editorial" --hero typography
  python3 scripts/audit_wow.py --code ./src --json --threshold 70

Exit codes:
  0 = score >= threshold (the design reaches for waouh)
  1 = score <  threshold (still competent, not memorable - push the hero dimension)
"""

import re
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import audit_gestures as ag   # ARCHETYPES, collect_code, resolve_archetype, audit
import audit_brief as ab      # section_body

HERO_DIMS = ["typography", "negative space", "colour", "color", "motion", "illustration"]

# Per-hero-dimension "deliberate excess" signals in code (raw CSS + Tailwind/JSX).
EXCESS = {
    "typography": {
        "label": "Typography taken to excess (huge display, violent scale jump)",
        "patterns": [
            r"clamp\([^)]*\b([89]\d|1\d\d)px", r"font-size:\s*([89]\d|1\d\d)px",
            r"text-\[\s*([89]\d|1\d\d)px", r"\btext-(7xl|8xl|9xl)\b",
            r"font-size:\s*([5-9](\.\d+)?|1\d)rem", r"clamp\([^)]*[5-9](\.\d+)?rem",
        ],
        "fix": "Push one headline to a genuinely huge display size (>=80px / >=5rem) against tiny body. The jump IS the design.",
    },
    "negative space": {
        "label": "Negative space taken to excess (extreme gaps / margins)",
        "patterns": [
            r"clamp\([^)]*\b(1[2-9]\d|2\d\d)px", r"(margin|padding|gap):[^;]*\b(1[5-9]\d|2\d\d)px",
            r"\b1[5-9]vw\b", r"\b[2-9]\dvh\b", r"\bpy-(32|40|48|56|64)\b", r"\bgap-(20|24|28|32)\b",
        ],
        "fix": "Let one region breathe at clamp(120px,18vw,240px). The emptiness must feel deliberate, almost uncomfortable.",
    },
    "colour": {
        "label": "Colour taken to excess (bold full-bleed owned accent)",
        "patterns": [
            r"(section|header|main|\.hero)[^{]*\{[^}]*background[^}]*var\(--color",
            r"\bbg-\[#[0-9a-f]{3,6}\]", r"background:\s*#[0-9a-f]{3,6}[^;]*;[^}]*min-height:\s*100",
            r"mix-blend", r"\bbg-(accent|primary)\b[^\"']*\bmin-h-screen\b", r"100vh[^}]*background:\s*var\(--color-accent",
        ],
        "fix": "Commit one saturated owned colour to a full-bleed area, not a sprinkle on buttons. Let it dominate one section.",
    },
    "color": None,  # alias, filled below
    "motion": {
        "label": "Motion taken to excess (scroll-driven, beyond a single fade)",
        "patterns": [
            r"scrolltrigger", r"gsap\.timeline", r"\bstagger\b", r"usescroll",
            r"animation-timeline", r"\bscrub\b", r"\bpin:\s*true", r"motionvalue", r"useinview",
        ],
        "fix": "Go past one fade-in: a scroll-driven timeline, a drawn line, pinned section or staggered reveal. ONE, executed perfectly.",
    },
    "illustration": {
        "label": "Illustration / imagery taken to excess (hero canvas, 3D, large SVG art)",
        "patterns": [
            r"<canvas", r"three", r"@react-three", r"webgl", r"lottie",
            r"<svg[^>]*(width|viewbox)[^>]*\b([2-9]\d\d|1\d\d\d)\b", r"background-image:[^;]*\.(svg|webp|avif)",
        ],
        "fix": "Make imagery the event: a hero canvas / 3D object / oversized custom SVG, not a decorative stock thumbnail.",
    },
}
EXCESS["color"] = EXCESS["colour"]


def detect_hero(brief_text: str):
    """Return the ticked Hero Dimension from CREATIVE-BRIEF.md, or None."""
    sec = ab.section_body(brief_text, "Hero Dimension")
    for line in sec.splitlines():
        m = re.match(r"\s*[-*]\s*\[[xX]\]\s*(.+)", line)
        if m:
            label = m.group(1).strip().lower()
            for d in HERO_DIMS:
                if d in label:
                    return d
    return None


def main():
    ap = argparse.ArgumentParser(prog="audit_wow", description="WOW mode - rewards deliberate excess in one hero dimension")
    ap.add_argument("--code", default=".")
    ap.add_argument("--design", default="DESIGN.md")
    ap.add_argument("--brief", default="CREATIVE-BRIEF.md")
    ap.add_argument("--archetype", default=None)
    ap.add_argument("--hero", default=None, help="Override hero dimension (typography/negative space/colour/motion/illustration)")
    ap.add_argument("--threshold", type=int, default=70, help="Minimum WOW score to pass (default 70)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    code_text, files = ag.collect_code(Path(args.code))
    design_text = Path(args.design).read_text(encoding="utf-8", errors="ignore") if Path(args.design).exists() else ""
    brief_text = Path(args.brief).read_text(encoding="utf-8", errors="ignore") if Path(args.brief).exists() else ""

    levers = []

    # W1 - hero dimension pushed to excess ----------------------------------
    hero = (args.hero or "").strip().lower() or detect_hero(brief_text)
    if hero in (None, ""):
        w1, note1 = 0, "no Hero Dimension found (brief not ticked, no --hero) - cannot assess excess."
        hero_label = "unknown"
    else:
        spec = EXCESS.get(hero)
        hero_label = hero
        if spec is None:
            w1, note1 = 0, f"unrecognised hero dimension '{hero}'."
        else:
            hit = any(re.search(p, code_text) for p in spec["patterns"])
            w1 = 40 if hit else 0
            note1 = spec["label"] + (" - present." if hit else f" - ABSENT. {spec['fix']}")
    levers.append(("W1", f"Hero dimension excess ({hero_label})", w1, 40, note1))

    # W2 - all 3 signature gestures -----------------------------------------
    key, src = ag.resolve_archetype(args.archetype, design_text, code_text)
    if key is None:
        w2, note2 = 0, f"archetype unknown ({src}) - pass --archetype so gesture completeness can be scored."
    else:
        _spec, results = ag.audit(code_text, key)
        present = sum(1 for r in results if r["present"])
        w2 = round(30 * present / len(results))
        note2 = f"{ag.ARCHETYPES[key]['name']}: {present}/{len(results)} signature gestures present" + \
                (" - full craft." if present == len(results) else " - implement all three for waouh.")
    levers.append(("W2", "All 3 signature gestures", w2, 30, note2))

    # W3 - a dial pushed to an extreme --------------------------------------
    dials = ab.section_body(brief_text, "Design Dials")
    nums = [int(n) for n in re.findall(r"(?:VARIANCE|MOTION|DENSITY)\s*[:=]\s*\**\s*(\d{1,2})", dials, re.I)]
    pushed = [n for n in nums if n <= 2 or n >= 9]
    if not nums:
        w3, note3 = 0, "no Design Dials set - reason them and push one to an extreme."
    elif pushed:
        w3, note3 = 15, f"a dial is pushed to an extreme ({pushed[0]}) - good."
    else:
        w3, note3 = 5, "dials all mid-range - push ONE to <=2 or >=9. Balance is the enemy of waouh."
    levers.append(("W3", "A Design Dial at an extreme", w3, 15, note3))

    # W4 - an owned signature move, declared AND in code --------------------
    sig_sec = ""
    m = re.search(r"## 11\.?\s*Signature Gesture.*?(?=\n## |\Z)", design_text, re.S | re.I)
    if m:
        sig_sec = m.group(0)
    gm = re.search(r"grep signature[^`]*`([^`]+)`", sig_sec, re.I)
    if not sig_sec:
        w4, note4 = 0, "DESIGN.md section 11 (Signature Gesture) missing - declare the ONE owned move."
    elif not gm:
        w4, note4 = 5, "section 11 present but no `Grep signature` regex - add one so the move can be verified in code."
    else:
        pat = gm.group(1)
        try:
            found = bool(re.search(pat, code_text, re.I))
        except re.error:
            found = False
        w4 = 15 if found else 5
        note4 = f"signature `{pat}` " + ("found in code - owned move is real." if found else "declared but NOT in code - implement it.")
    levers.append(("W4", "An owned signature move (in code)", w4, 15, note4))

    total = sum(l[2] for l in levers)
    passed = total >= args.threshold

    if args.json:
        print(json.dumps({
            "status": "wow" if passed else "competent",
            "score": total, "threshold": args.threshold, "hero": hero_label,
            "levers": [{"id": i, "label": l, "points": p, "max": mx, "note": n} for i, l, p, mx, n in levers],
        }, indent=2))
        sys.exit(0 if passed else 1)

    bar_w = 24
    fw = round(bar_w * total / 100)
    print("\n" + "=" * 60)
    print("  WOW MODE - deliberate excess audit")
    print("=" * 60 + "\n")
    print(f"  WOW Score: {total}/100   {'REACHES FOR WAOUH' if passed else 'STILL COMPETENT'}")
    print("  [" + "#" * fw + "-" * (bar_w - fw) + "]\n")
    for i, l, p, mx, n in levers:
        flag = "[OK]" if p >= 0.7 * mx else ("[WARN]" if p > 0 else "[--]")
        print(f"  {flag} {i} {l:<36} {p:>2}/{mx}")
        print(f"       {n}")
    print("\n" + "=" * 60)
    if passed:
        print(f"  [OK] {total}/100 - the design commits to one dimension hard enough to be memorable.")
    else:
        print(f"  [BELOW WAOUH] {total}/100 (need >= {args.threshold}).")
        print("       It is clean, but it balances instead of committing. Push the hero dimension above.")
    print("=" * 60 + "\n")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
