#!/usr/bin/env python3
"""
audit_brief.py - Creative-Brief quality scorer (Phase -1 quality layer)

check.py's gate-0 brief check validates PRESENCE and STRUCTURE only - it states
plainly that "a gate cannot tell an inspired brief from filler". That is the
hole this script fills. It scores the *quality* of the point of view, because a
blank-or-bland brief is the single biggest cause of "competent-but-forgettable"
output (the skill predicts this failure itself).

It scores six dimensions of a sharp brief (0-100) and can block below a floor:

  B1 Emotional Intent concreteness  (20) - sensory/place/simile, not buzzwords
  B2 The One Unexpected Thing       (18) - a real bet, not a named existing site
  B3 The Broken Rule: what + why    (14) - both the rule AND the 'because'
  B4 The Cross-Domain Steal         (22) - a genuinely NON-software discipline
  B5 Design Dials reasoned          (14) - three values, at least one pushed far
  B6 Hero Dimension: exactly one    (12) - excess in ONE direction

Usage:
  python3 scripts/audit_brief.py                       # reads ./CREATIVE-BRIEF.md
  python3 scripts/audit_brief.py --brief path/to.md
  python3 scripts/audit_brief.py --json
  python3 scripts/audit_brief.py --threshold 50 75     # FLOOR PASS

Exit codes:
  0 = score >= floor (PASS / NEEDS-SHARPENING)
  1 = score <  floor (BLOCKED - the brief is filler, sharpen it before Phase 0)
  2 = CREATIVE-BRIEF.md not found
"""

import re
import sys
import json
import argparse
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VAGUE_TERMS = [
    "professional", "modern", "clean", "sleek", "elegant", "premium",
    "minimalist", "beautiful", "nice", "simple", "user-friendly", "intuitive",
    "innovative", "cutting-edge", "stunning", "engaging", "seamless",
    # French equivalents (gendered forms spelled out — \b won't bridge a trailing 'e')
    "professionnel", "professionnelle", "moderne", "épuré", "épurée",
    "élégant", "élégante", "minimaliste", "soigné", "soignée", "raffiné",
    "raffinée", "haut de gamme", "convivial", "conviviale", "intuitif",
    "intuitive", "innovant", "innovante", "fluide", "impactant", "immersif",
    "immersive", "épurés", "élégants",
]

# Concreteness lexicon - sensory, material, place, atmosphere words.
CONCRETE_LEX = [
    "ink", "paper", "concrete", "brass", "copper", "linen", "marble", "neon",
    "dust", "fog", "smoke", "warehouse", "cafe", "café", "studio", "smell",
    "hum", "grain", "matte", "glossy", "weight", "heavy", "cold", "warm",
    "dim", "shadow", "light", "fluorescent", "wood", "steel", "glass", "stone",
    "leather", "wool", "rust", "patina", "chalk", "graphite", "velvet", "amber",
    "morning", "midnight", "rain", "sun", "salt", "sweat", "engine", "vinyl",
    # French sensory/material/place words (substring match — short/ambiguous ones omitted)
    "encre", "papier", "béton", "laiton", "cuivre", "marbre", "néon",
    "poussière", "brouillard", "fumée", "entrepôt", "atelier", "odeur",
    "lourd", "froid", "chaud", "ombre", "lumière", "acier", "verre", "cuir",
    "laine", "rouille", "velours", "minuit", "pluie", "soleil", "sueur",
    "moteur", "vinyle", "ampoule", "sillon", "graphite", "ardoise", "pierre",
]

# Disciplines that are genuinely OUTSIDE software (the golden-rule whitelist).
NONSOFTWARE = [
    "print", "editorial", "newspaper", "broadsheet", "magazine", "book",
    "typograph", "architecture", "cinema", "film", "movie", "signage",
    "wayfinding", "packaging", "fashion", "textile", "industrial design",
    "product design", "exhibition", "museum", "gallery", "photography",
    "music", "album", "vinyl record", "theatre", "theater", "ceramic",
    "poster", "sculpture", "painting", "menu", "couture", "automotive",
    "cartography", "map-making", "botanic", "interior design", "stage",
    # French disciplines (substring match — avoid "mode" which collides with "modern")
    "signalétique", "typographie", "sérigraphie", "affiche", "pressage",
    "vinyle", "céramique", "cinéma", "peinture", "mobilier", "cartographie",
    "photographie", "édition", "presse écrite", "joaillerie", "parfum",
    "gastronomie", "scénographie", "reliure", "enseigne", "estampe",
    "ébénisterie", "architecture d", "haute couture", "broderie",
    # Rare craft / artisanal disciplines (FR) — reduce the "unknown lexical field"
    # miss on B4. Each checked substring-safe (no collision with VAGUE/SOFTWARE).
    "lutherie", "ferronnerie", "verrerie", "soufflage", "forge",
    "tannerie", "maroquinerie", "horlogerie", "orfèvrerie", "tapisserie",
    "vitrail", "mosaïque", "fresque", "calligraphie", "enluminure",
    "gravure", "lithographie", "fonderie", "tissage", "teinture",
    "marqueterie", "vannerie", "poterie", "émaillage", "dorure",
    "chaudronnerie", "menuiserie", "charpenterie", "tonnellerie", "coutellerie",
    # rare craft disciplines (EN) — keep symmetry with the FR additions
    "lutherie", "luthier", "blacksmith", "glassblow", "bookbind",
    "watchmaking", "goldsmith", "tapestry", "stained glass", "mosaic",
    "fresco", "calligraphy", "illumination", "engraving", "lithography",
    "weaving", "marquetry", "basketry", "pottery", "enamel", "gilding",
]

# Software / tech references the steal must NOT lean on (the failure mode).
SOFTWARE = [
    "website", "web site", "webapp", "web app", "saas", "dashboard",
    "landing page", "dev tool", "developer tool", "framework", "ui kit",
    "design system", "mobile app", "software", "tech company", "another site",
    "another app", "linear.app", "stripe", "vercel", "notion", "figma",
    "airbnb", "spotify app",
    # French software references (the failure mode the steal must NOT lean on)
    "site web", "site internet", "page d'atterrissage", "tableau de bord",
    "application mobile", "appli", "logiciel", "système de design",
    "autre site", "autre appli", "outil de dev", "page d'accueil saas",
]

# Well-known sites/apps - naming one in "the unexpected thing" means it is not
# unexpected (the template says: if you can name a site that does it, start over).
KNOWN_SITES = [
    "stripe", "vercel", "linear", "notion", "figma", "airbnb", "spotify",
    "apple", "nike", "tesla", "github", "framer", "webflow", "dribbble",
]


def section_body(content: str, header: str) -> str:
    out, capturing = [], False
    for ln in content.splitlines():
        s = ln.strip()
        if s.lower() == f"## {header}".lower():
            capturing = True
            continue
        if capturing and s.startswith("## "):
            break
        if capturing:
            out.append(ln)
    body = "\n".join(out)
    body = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)   # strip guidance comments
    return body.strip()


def filled(body: str) -> bool:
    t = body.replace("___", "").strip()
    t = re.sub(r"^[-*]\s*\[\s*\].*$", "", t, flags=re.MULTILINE).strip()
    return len(t) >= 8


def words(s: str) -> int:
    return len([w for w in re.findall(r"[a-zA-Z\u00c0-\u017f']+", s)])


def has_proper_noun(s: str) -> bool:
    # A capitalised word that is not the first token of a line (a likely name/place).
    for line in s.splitlines():
        toks = line.strip().split()
        for i, tok in enumerate(toks):
            if i == 0:
                continue
            if re.match(r"^[A-Z][a-z]{2,}", tok):
                return True
    return False


def score_brief(content: str):
    dims = []  # (id, label, points, max, note)

    # B1 - Emotional Intent concreteness ------------------------------------
    emo = section_body(content, "Emotional Intent")
    pts, note = 0, ""
    if not filled(emo):
        note = "empty/unfilled."
    else:
        low = emo.lower()
        vague = [w for w in VAGUE_TERMS if re.search(rf"\b{re.escape(w)}\b", low)]
        concrete = [w for w in CONCRETE_LEX if w in low]
        simile = bool(re.search(r"\b(like|as if|comme|tel(?:le)?s?\s+que|à la manière)\b", low))
        pn = has_proper_noun(emo)
        pts = 6  # filled
        if concrete: pts += 5
        if simile: pts += 4
        if pn: pts += 5
        if vague and not concrete and not simile and not pn:
            pts = min(pts, 6)
            note = f"buzzword-only ({', '.join(vague)}); name a concrete scene instead."
        else:
            bits = []
            if simile: bits.append("simile")
            if pn: bits.append("proper noun")
            if concrete: bits.append("sensory words")
            note = "concrete: " + ", ".join(bits) if bits else "filled but generic."
        pts = min(pts, 20)
    dims.append(("B1", "Emotional Intent concreteness", pts, 20, note))

    # B2 - The One Unexpected Thing -----------------------------------------
    unx = section_body(content, "The One Unexpected Thing")
    pts, note = 0, ""
    if not filled(unx):
        note = "empty/unfilled."
    else:
        low = unx.lower()
        named = [s for s in KNOWN_SITES if re.search(rf"\b{re.escape(s)}\b", low)]
        pts = 8
        if words(unx) >= 14: pts += 6
        if has_proper_noun(unx) or re.search(r"\bno\b|\bnever\b|\binstead\b|\bonly\b", low):
            pts += 4  # a stated bet ("no image", "only X")
        if named:
            pts = min(pts, 8)
            note = f"names an existing site ({', '.join(named)}) - if it exists, it is not unexpected."
        else:
            note = "a specific, owned bet." if pts >= 14 else "filled; push it further / be more specific."
        pts = min(pts, 18)
    dims.append(("B2", "The One Unexpected Thing", pts, 18, note))

    # B3 - The Broken Rule: what + why --------------------------------------
    brk = section_body(content, "The Broken Rule")
    pts, note = 0, ""
    if not filled(brk):
        note = "empty/unfilled."
    else:
        low = brk.lower()
        has_why = bool(re.search(r"\bbecause\b|\bso that\b|\bparce que\b|\bwhy\b", low))
        pts = 7
        if has_why and words(brk) >= 12:
            pts += 7
            note = "states the rule AND the 'because'."
        elif has_why:
            pts += 4
            note = "has a 'because' but is thin - explain why breaking it IS the design."
        else:
            note = "no 'because' - a broken rule without a reason is just a mistake."
        pts = min(pts, 14)
    dims.append(("B3", "The Broken Rule: what + why", pts, 14, note))

    # B4 - The Cross-Domain Steal (the golden rule) -------------------------
    steal = section_body(content, "The Cross-Domain Steal")
    pts, note = 0, ""
    if not filled(steal):
        note = "missing - steal ONE move from a non-software discipline."
    else:
        low = steal.lower()
        non = [d for d in NONSOFTWARE if d in low]
        soft = [d for d in SOFTWARE if re.search(rf"(?<!non-)\b{re.escape(d)}\b", low)]
        # "specific move": a second substantive line / a 'move' description
        lines = [l for l in steal.splitlines() if filled(l)]
        specific = len(lines) >= 2 or words(steal) >= 18
        if non and not soft:
            pts = 14
            if specific: pts += 8
            note = f"non-software steal ({non[0]})" + ("; specific move named." if specific else "; name the SPECIFIC move.")
        elif non and soft:
            pts = 10
            note = f"mixes a non-software steal with a software reference ({soft[0]}) - drop the software one."
        elif soft:
            pts = 0
            note = f"the steal IS software ({soft[0]}) - this is how AI pages all look the same. Start over."
        else:
            pts = 6
            note = "discipline unclear - state a concrete non-software field (print, architecture, cinema...)."
        pts = min(pts, 22)
    dims.append(("B4", "The Cross-Domain Steal (non-software)", pts, 22, note))

    # B5 - Design Dials reasoned --------------------------------------------
    dials = section_body(content, "Design Dials")
    pts, note = 0, ""
    nums = [int(n) for n in re.findall(r"(?:VARIANCE|MOTION|DENSITY)\s*[:=]\s*\**\s*(\d{1,2})", dials, re.I)]
    if len(nums) < 3:
        note = f"only {len(nums)}/3 dials set - reason all three (VARIANCE / MOTION / DENSITY)."
        pts = 4 * len(nums)
    else:
        pts = 7
        pushed = [n for n in nums if n <= 2 or n >= 9]
        if pushed:
            pts += 7
            note = f"three dials set; at least one pushed to an extreme ({pushed[0]}) - good, waouh comes from one extreme."
        else:
            note = "three dials set but all mid-range - push ONE to an extreme (<=2 or >=9)."
    pts = min(pts, 14)
    dims.append(("B5", "Design Dials reasoned", pts, 14, note))

    # B6 - Hero Dimension: exactly one --------------------------------------
    hero = section_body(content, "Hero Dimension")
    ticked = len(re.findall(r"[-*]\s*\[[xX]\]", hero))
    if ticked == 1:
        pts, note = 12, "exactly one dimension of excess - correct."
    elif ticked == 0:
        pts, note = 0, "no Hero Dimension ticked - pick exactly ONE."
    else:
        pts, note = 3, f"{ticked} ticked - excess means ONE direction, not several."
    dims.append(("B6", "Hero Dimension: exactly one", pts, 12, note))

    total = sum(d[2] for d in dims)
    return total, dims


def main():
    ap = argparse.ArgumentParser(prog="audit_brief", description="Creative-Brief quality scorer")
    ap.add_argument("--brief", default="CREATIVE-BRIEF.md")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--threshold", nargs=2, type=int, metavar=("FLOOR", "PASS"), default=[50, 75],
                    help="FLOOR (block below) and PASS (strong above). Default 50 75.")
    args = ap.parse_args()

    bp = Path(args.brief)
    if not bp.exists():
        if args.json:
            print(json.dumps({"status": "missing", "brief": str(bp)}))
        else:
            print(f"\n  [ERROR] {bp} not found - Phase -1 must precede Phase 0.\n")
        sys.exit(2)

    floor, passmark = args.threshold
    content = bp.read_text(encoding="utf-8")
    total, dims = score_brief(content)

    if args.json:
        print(json.dumps({
            "status": "blocked" if total < floor else ("strong" if total >= passmark else "needs-sharpening"),
            "score": total, "floor": floor, "pass": passmark,
            "dimensions": [{"id": i, "label": l, "points": p, "max": m, "note": n}
                           for i, l, p, m, n in dims],
        }, indent=2))
        sys.exit(1 if total < floor else 0)

    verdict = "❌ BLOCKED (filler)" if total < floor else ("✅ SHARP" if total >= passmark else "⚠️ NEEDS SHARPENING")
    bar_w = 24
    filled_w = round(bar_w * total / 100)
    print("\n" + "=" * 60)
    print("  CREATIVE-BRIEF QUALITY (Phase -1)")
    print("=" * 60 + "\n")
    print(f"  Brief Score: {total}/100   {verdict}")
    print("  [" + "#" * filled_w + "-" * (bar_w - filled_w) + "]\n")
    print("  Dimension breakdown:")
    for i, l, p, m, n in dims:
        flag = "[OK]" if p >= 0.7 * m else ("[WARN]" if p > 0 else "[--]")
        print(f"  {flag} {i} {l:<38} {p:>2}/{m}")
        print(f"       {n}")
    print("\n" + "=" * 60)
    if total < floor:
        print(f"  [BLOCKED] {total}/100 below floor {floor}. The brief is filler, not a point of view.")
        print("       Sharpen the flagged dimensions before Phase 0 - everything downstream inherits this.")
    elif total >= passmark:
        print(f"  [OK] SHARP - {total}/100. The point of view can carry a 'waouh' result.")
    else:
        print(f"  [WARN] {total}/100 - usable but soft. Sharpen the low dimensions to aim for waouh.")
    print("=" * 60 + "\n")
    sys.exit(1 if total < floor else 0)


if __name__ == "__main__":
    main()
