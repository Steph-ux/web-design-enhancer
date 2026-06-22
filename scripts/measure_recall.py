#!/usr/bin/env python3
"""
measure_recall.py — Honest recall measurement for detect_ai_slop.py

Two labeled corpora, measured separately:

  ID  (in-distribution)  : slop using the EXACT tokens the detector claims to
                           target. Measures implementation correctness — does the
                           regex actually fire end-to-end through the file-dispatch
                           pipeline? A miss here is a real bug (dead pattern).

  OOD (out-of-distribution): realistic real-world AI slop using variations,
                           synonyms, sentence-case, and patterns an *ideal* slop
                           detector should catch. Measures TRUE recall
                           (generalization / coverage). This is the honest number.

Each sample is written to a temp directory with the correct extension and run
through the FULL detector pipeline (AISloPDetector.run), exactly as in production.
A sample counts as "detected" if at least one issue fired (score dropped).

Run:  python scripts/measure_recall.py
      python scripts/measure_recall.py --verbose   # show per-sample result
"""

import sys
import argparse
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from detect_ai_slop import AISloPDetector  # noqa: E402


# ---------------------------------------------------------------------------
# Corpus. Each entry: (id, group, ext, content, slop_type_human)
#   group: "ID" or "OOD"
#   ext:   file extension that triggers the right scanner (html/css/tsx/js/md)
#   For DESIGN.md-scanned samples use ext "design" (routed to --design).
# All samples are *intended* slop: an ideal detector flags every one.
# ---------------------------------------------------------------------------

CORPUS = [
    # ===================== IN-DISTRIBUTION (ID) ==========================
    ("id-sys-active", "ID", "html",
     "<head><meta name='viewport' content='width=device-width'></head>"
     "<body><span>SYS_ACTIVE</span></body>", "SYS_ACTIVE badge"),
    ("id-pulse-dot", "ID", "html",
     "<head><meta name='viewport' content='x'></head><div class='pulse-dot'></div>",
     "pulse-dot class"),
    ("id-allcaps-cta", "ID", "html",
     "<head><meta name='viewport' content='x'></head><button>GET STARTED NOW</button>",
     "ALL_CAPS CTA"),
    ("id-emdash", "ID", "html",
     "<head><meta name='viewport' content='x'></head><p>Fast, secure — simple.</p>",
     "em-dash in text"),
    ("id-scroll-cue", "ID", "html",
     "<head><meta name='viewport' content='x'></head><div>Scroll to explore</div>",
     "scroll cue"),
    ("id-version-label", "ID", "html",
     "<head><meta name='viewport' content='x'></head><span>v1.4.2</span>",
     "version/build label"),
    ("id-jane-doe", "ID", "html",
     "<head><meta name='viewport' content='x'></head><p>Jane Doe, CEO</p>",
     "Jane Doe placeholder"),
    ("id-lorem", "ID", "html",
     "<head><meta name='viewport' content='x'></head><p>Lorem ipsum dolor sit amet</p>",
     "lorem ipsum"),
    ("id-picsum", "ID", "html",
     "<head><meta name='viewport' content='x'></head><img src='https://picsum.photos/200' alt='x'>",
     "placeholder image service"),
    ("id-testimonial", "ID", "html",
     "<head><meta name='viewport' content='x'></head><div class='testimonial-card'>Great!</div>",
     "testimonial card"),
    ("id-trusted-by", "ID", "html",
     "<head><meta name='viewport' content='x'></head><div class='trusted-by'>logos</div>",
     "trusted-by section"),
    ("id-emoji-heading", "ID", "html",
     "<head><meta name='viewport' content='x'></head><h1>\U0001F680 Welcome</h1>",
     "emoji in heading"),
    ("id-marketing-stat", "ID", "html",
     "<head><meta name='viewport' content='x'></head><span>10,000+ users</span>",
     "invented marketing stat"),
    ("id-status-pill", "ID", "html",
     "<head><meta name='viewport' content='x'></head><span>OPTIMAL</span>",
     "operational status pill"),
    ("id-machine-id", "ID", "html",
     "<head><meta name='viewport' content='x'></head><span>ID: VALVE_01</span>",
     "machine ID in UI"),
    ("id-console-log", "ID", "html",
     "<head><meta name='viewport' content='x'></head><div>[12:34:56] SYSTEM: ok</div>",
     "fake console timestamp"),
    ("id-secnum-eyebrow", "ID", "html",
     "<head><meta name='viewport' content='x'></head><span>00 / INDEX</span>",
     "section-number eyebrow"),
    ("id-status-is-active", "ID", "html",
     "<head><meta name='viewport' content='x'></head><div>Status is active</div>",
     "sentence-case fake status"),
    ("id-css-blue-purple-hero", "ID", "css",
     ".hero { background: linear-gradient(90deg, #3b82f6, #8b5cf6); }",
     "blue->purple hero gradient"),
    ("id-css-pulse-ring", "ID", "css",
     "@keyframes pulse-ring { from {opacity:1} to {opacity:0} }",
     "pulse-ring keyframes"),
    ("id-css-monospace-ui", "ID", "css",
     ".label { font-family: monospace; }", "monospace on UI"),
    ("id-css-important-layout", "ID", "css",
     ".box { margin: 0 !important; }", "!important on layout"),
    ("id-css-zindex", "ID", "css",
     ".modal { z-index: 9999; }", "arbitrary z-index"),
    ("id-css-hardcoded-hex", "ID", "css",
     ".text { color: #4ab3f7; }", "hardcoded hex color"),
    ("id-css-glass-card", "ID", "css",
     ".card { backdrop-filter: blur(10px); }", "glassmorphism on card"),
    ("id-css-typewriter", "ID", "css",
     "@keyframes typing { from {width:0} to {width:100%} }", "typewriter keyframes"),
    ("id-js-console-log", "ID", "js",
     "function f(){ console.log('debug'); }", "console.log in code"),
    ("id-js-todo", "ID", "js",
     "// TODO: fix this later\nconst x = 1;", "unresolved TODO"),
    ("id-js-mock-data", "ID", "js",
     "const mockUsers = [{id:1}];", "mock data variable"),
    ("id-tsx-allcaps-class", "ID", "tsx",
     "export const B = () => <button className='uppercase btn'>go</button>;",
     "uppercase class on CTA"),
    ("id-design-buzzwords", "ID", "design",
     "# Design\nA premium, elegant, modern interface that is incroyable.",
     "vague buzzwords"),
    ("id-design-generic-font", "ID", "design",
     "# Design\nfont-family: helvetica, arial, sans-serif;", "generic font"),
    ("id-design-cliche-gradient", "ID", "design",
     "# Design\nUse a gradient from blue to purple on the hero.",
     "cliche blue->purple gradient"),
    ("id-tsx-threejs-leak", "ID", "tsx",
     "import * as THREE from 'three';\nfunction animate(){ const g = new THREE.BoxGeometry(1,1,1); "
     "requestAnimationFrame(animate); }", "three.js geometry-in-loop leak"),
    ("id-swift-hardcoded-width", "ID", "swift",
     "import SwiftUI\nstruct V: View { var body: some View { Rectangle().frame(width: 375) } }",
     "hardcoded iPhone width"),

    # ===================== OUT-OF-DISTRIBUTION (OOD) =====================
    # Realistic AI slop an ideal detector should catch; tests true coverage.
    ("ood-generic-hero-copy", "OOD", "html",
     "<head><meta name='viewport' content='x'></head>"
     "<h1>Transform Your Workflow</h1><p>Unlock the power of seamless productivity.</p>",
     "generic SaaS hero copy"),
    ("ood-cta-get-started", "OOD", "html",
     "<head><meta name='viewport' content='x'></head>"
     "<button>Get Started</button><button>Learn More</button>",
     "generic sentence-case CTAs"),
    ("ood-inter-font", "OOD", "css",
     "body { font-family: 'Inter', -apple-system, sans-serif; }",
     "Inter — the #1 AI default font"),
    ("ood-gradient-text", "OOD", "css",
     ".title { background: linear-gradient(90deg,#a855f7,#ec4899); "
     "-webkit-background-clip: text; -webkit-text-fill-color: transparent; }",
     "gradient clipped text cliche"),
    ("ood-rounded-shadow-card", "OOD", "css",
     ".card { border-radius: 1rem; box-shadow: 0 20px 25px -5px rgba(0,0,0,.1); padding: 2rem; }",
     "rounded-2xl + shadow-xl card cliche"),
    ("ood-indigo-violet-gradient", "OOD", "css",
     ".banner { background: linear-gradient(to right, #6366f1, #8b5cf6); }",
     "indigo->violet gradient (non-hero, dodges B7)"),
    ("ood-emoji-bullets", "OOD", "html",
     "<head><meta name='viewport' content='x'></head>"
     "<ul><li>✨ Lightning fast</li><li>\U0001F512 Secure by default</li></ul>",
     "emoji as <li> bullets (dodges heading/button rule)"),
    ("ood-powered-by-ai", "OOD", "html",
     "<head><meta name='viewport' content='x'></head><span>Powered by AI</span>",
     "'Powered by AI' sentence-case badge"),
    ("ood-feature-grid-3col", "OOD", "html",
     "<head><meta name='viewport' content='x'></head>"
     "<section class='features'><div class='feature'><h3>Fast</h3><p>Very fast.</p></div>"
     "<div class='feature'><h3>Secure</h3><p>Very secure.</p></div>"
     "<div class='feature'><h3>Simple</h3><p>Very simple.</p></div></section>",
     "identical 3-column feature grid"),
    ("ood-generic-spacing", "OOD", "css",
     ".section { padding: 80px 0; } .container { padding: 80px 0; }",
     "uniform 80px section padding rhythm"),
    ("ood-aurora-blob-bg", "OOD", "css",
     ".bg { background: radial-gradient(circle at 20% 30%, #c084fc, transparent), "
     "radial-gradient(circle at 80% 70%, #60a5fa, transparent); filter: blur(80px); }",
     "aurora/mesh blob background cliche"),
    ("ood-glass-navbar", "OOD", "css",
     ".navbar { backdrop-filter: blur(12px); background: rgba(255,255,255,.7); }",
     "glassmorphism navbar (non-modal)"),
    ("ood-dark-mode-toggle", "OOD", "html",
     "<head><meta name='viewport' content='x'></head>"
     "<button class='theme-toggle' aria-label='Toggle dark mode'>\U0001F319</button>",
     "obligatory dark-mode toggle"),
    ("ood-hero-cta-pair", "OOD", "html",
     "<head><meta name='viewport' content='x'></head>"
     "<div class='hero'><h1>Build faster</h1><a class='btn-primary'>Start free trial</a>"
     "<a class='btn-secondary'>Book a demo</a></div>",
     "primary+secondary hero CTA pair cliche"),
    ("ood-poppins-font", "OOD", "css",
     "h1 { font-family: 'Poppins', sans-serif; }",
     "Poppins — common AI display font"),
    ("ood-generic-tagline", "OOD", "html",
     "<head><meta name='viewport' content='x'></head>"
     "<p>The all-in-one platform for modern teams.</p>",
     "generic 'all-in-one platform' tagline"),
    ("ood-pricing-3tier", "OOD", "html",
     "<head><meta name='viewport' content='x'></head>"
     "<div class='pricing'><div class='tier'>Starter</div><div class='tier popular'>Pro</div>"
     "<div class='tier'>Enterprise</div></div>",
     "Starter/Pro/Enterprise 3-tier pricing cliche"),
    ("ood-gradient-button", "OOD", "css",
     ".btn-primary { background: linear-gradient(135deg, #667eea, #764ba2); color:#fff; "
     "border-radius: 9999px; }",
     "gradient pill button (purple-ish, dodges blue/purple kw)"),
    ("ood-floating-badge", "OOD", "html",
     "<head><meta name='viewport' content='x'></head>"
     "<span class='badge'>New</span>",
     "decorative 'New' floating badge"),
    ("ood-hover-lift-card", "OOD", "css",
     ".card:hover { transform: translateY(-8px); transition: transform .3s; "
     "box-shadow: 0 30px 60px rgba(0,0,0,.15); }",
     "hover-lift card transform cliche"),
]


def detect_one(ext: str, content: str):
    """Run the real detector pipeline on a single sample.

    Returns (detected: bool, fired_types: list[str]). The viewport-meta
    auto-issue is excluded so it can never mask a true miss.
    """
    import io
    import contextlib
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        if ext == "design":
            design = tdp / "DESIGN.md"
            design.write_text(content, encoding="utf-8")
            det = AISloPDetector(design_file=str(design), code_dir=None)
        else:
            fname = {"html": "index.html", "css": "style.css", "js": "app.js",
                     "tsx": "App.tsx", "swift": "View.swift"}[ext]
            (tdp / fname).write_text(content, encoding="utf-8")
            det = AISloPDetector(design_file=None, code_dir=str(tdp))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            det.run(json_mode=False)
        real_issues = [i for i in det.issues
                       if "viewport" not in i.get("message", "").lower()]
        return len(real_issues) > 0, sorted({i["type"] for i in real_issues})


def measure(verbose: bool = False):
    results = []
    for sample_id, group, ext, content, human in CORPUS:
        detected, fired = detect_one(ext, content)
        results.append((sample_id, group, detected, human, fired))
        if verbose:
            mark = "HIT " if detected else "MISS"
            print(f"  [{mark}] {group:3} {sample_id:30} {human}")
            if detected:
                print(f"         fired: {', '.join(fired)}")

    def recall(group):
        g = [r for r in results if r[1] == group]
        hit = sum(1 for r in g if r[2])
        return hit, len(g)

    id_hit, id_n = recall("ID")
    ood_hit, ood_n = recall("OOD")
    tot_hit = id_hit + ood_hit
    tot_n = id_n + ood_n

    print("\n" + "=" * 70)
    print("RECALL MEASUREMENT — detect_ai_slop.py")
    print("=" * 70)
    print(f"\nIN-DISTRIBUTION  (implementation correctness): "
          f"{id_hit}/{id_n} = {100*id_hit/id_n:.0f}%")
    print(f"OUT-OF-DISTRIB.  (true coverage / recall)    : "
          f"{ood_hit}/{ood_n} = {100*ood_hit/ood_n:.0f}%")
    print(f"OVERALL                                       : "
          f"{tot_hit}/{tot_n} = {100*tot_hit/tot_n:.0f}%")

    id_miss = [r for r in results if r[1] == "ID" and not r[2]]
    ood_miss = [r for r in results if r[1] == "OOD" and not r[2]]

    if id_miss:
        print(f"\n[!] ID MISSES (dead/broken patterns — real bugs): {len(id_miss)}")
        for r in id_miss:
            print(f"      - {r[0]}: {r[3]}")
    else:
        print("\n[ok] No ID misses — every claimed pattern fires end-to-end.")

    print(f"\n[i] OOD MISSES (coverage gaps — slop the tool lets through): {len(ood_miss)}")
    for r in ood_miss:
        print(f"      - {r[0]}: {r[3]}")

    print("\n" + "=" * 70)
    return results


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    measure(verbose=args.verbose)
