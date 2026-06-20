#!/usr/bin/env python3
"""
audit_layout.py — Layout-integrity gate (responsiveness, measured not eyeballed).

The existing visual_audit.py renders 4 breakpoints and re-runs the SAME slop/8px
checks at each size, then leaves "does the layout actually hold?" to the vision
pass (which is self-judged and therefore weak). This gate closes that hole by
MEASURING layout integrity on the real rendered DOM, at every breakpoint:

  ERROR (blocks delivery):
    L1  Page horizontal overflow  — documentElement.scrollWidth > clientWidth
    L2  Element overflows viewport — an element's box extends past the right edge
    L3  Child overflows its parent — content spills horizontally out of its container

  WARN (reported, blocks only with --strict):
    L4  Ragged grid baseline       — cards in the same grid row whose bottom-most
                                      element (e.g. the author/date meta) sits at
                                      different Y positions because the card is not
                                      flex-col + h-full + mt-auto. This is the
                                      "cadre cassé" defect: divider rules run full
                                      height while content floats unaligned.
    L5  Uneven card heights         — sibling cards in a divided row whose heights
                                      differ beyond tolerance.

Breakpoints: 375 / 768 / 1280 / 1920 px (same as visual_audit.py).

Usage:
    python3 scripts/audit_layout.py --url http://localhost:3000
    python3 scripts/audit_layout.py --url http://localhost:3000 --json
    python3 scripts/audit_layout.py --url http://localhost:3000 --strict   # WARN also blocks
    python3 scripts/audit_layout.py --url http://localhost:3000 --output ./audit-results

Exit code: 0 = clean (or warn-only without --strict), 1 = blocking violation.
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERROR: playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(2)

BREAKPOINTS = [
    ("mobile", 375, 667),
    ("tablet", 768, 1024),
    ("desktop", 1280, 800),
    ("wide", 1920, 1080),
]

# Sub-pixel tolerance — browsers report fractional px; don't flag rounding noise.
OVERFLOW_TOL = 2      # px past an edge before it counts as overflow
BASELINE_TOL = 16     # px spread of meta baselines within a row before "ragged"
HEIGHT_TOL = 24       # px spread of card heights within a divided row before "uneven"
ROW_BUCKET = 12       # px tolerance for grouping cards into the same visual row

# JS runs inside the page. Raw string so \b \d \s are passed to the JS engine intact.
_JS_LAYOUT = r"""
(cfg) => {
    const TOL = cfg.overflowTol, BTOL = cfg.baselineTol, HTOL = cfg.heightTol, RB = cfg.rowBucket;
    const vw = window.innerWidth;
    const out = { errors: [], warnings: [] };

    const label = (el) => {
        const cls = (el.className && typeof el.className === 'string')
            ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.')
            : '';
        return el.tagName.toLowerCase() + cls;
    };

    // ── L1: page-level horizontal overflow ────────────────────────────────
    const de = document.documentElement;
    if (de.scrollWidth - de.clientWidth > TOL) {
        out.errors.push({
            code: 'L1',
            message: 'Page overflows horizontally: scrollWidth ' + de.scrollWidth +
                     'px > viewport ' + de.clientWidth + 'px (+' +
                     (de.scrollWidth - de.clientWidth) + 'px). The page can be scrolled sideways.',
            fix: 'Find the offending element (see L2). Common causes: a fixed width > viewport, ' +
                 'an unwrapped wide table/image, negative margins, or 100vw + padding. ' +
                 'Use max-width:100%, overflow-x guards on the wrapper, or w-full instead of fixed px.'
        });
    }

    // ── L2: element extends past the viewport's right edge ────────────────
    const seenL2 = new Set();
    document.querySelectorAll('body *').forEach(el => {
        const cs = getComputedStyle(el);
        if (cs.position === 'fixed' || cs.display === 'none' || cs.visibility === 'hidden') return;
        const r = el.getBoundingClientRect();
        if (r.width === 0 || r.height === 0) return;
        if (r.right > vw + TOL) {
            const key = label(el) + '|' + Math.round(r.right);
            if (seenL2.has(key)) return;
            seenL2.add(key);
            out.errors.push({
                code: 'L2',
                element: label(el),
                message: 'Element "' + label(el) + '" extends ' + Math.round(r.right - vw) +
                         'px past the right edge of the ' + vw + 'px viewport.',
                fix: 'Constrain this element: max-width:100%, box-sizing:border-box, wrap long ' +
                     'content, or replace a fixed px width with a fluid one.'
            });
        }
    });

    // ── L3: child overflows its parent's content box horizontally ─────────
    const seenL3 = new Set();
    document.querySelectorAll('body *').forEach(el => {
        const cs = getComputedStyle(el);
        if (cs.display === 'none' || cs.visibility === 'hidden') return;
        const ox = cs.overflowX;
        if (ox === 'auto' || ox === 'scroll' || ox === 'hidden') return; // intentional scroll/clip
        const pr = el.getBoundingClientRect();
        if (pr.width === 0) return;
        for (const child of el.children) {
            const ccs = getComputedStyle(child);
            if (ccs.position === 'absolute' || ccs.position === 'fixed') continue;
            const cr = child.getBoundingClientRect();
            if (cr.width === 0 || cr.height === 0) continue;
            const spill = Math.max(cr.right - pr.right, pr.left - cr.left);
            if (spill > TOL + 1) {
                const key = label(el) + '>' + label(child) + '|' + Math.round(spill);
                if (seenL3.has(key)) continue;
                seenL3.add(key);
                out.errors.push({
                    code: 'L3',
                    element: label(el) + ' > ' + label(child),
                    message: 'Child "' + label(child) + '" overflows parent "' + label(el) +
                             '" by ' + Math.round(spill) + 'px horizontally.',
                    fix: 'Add min-width:0 / flex-shrink to the child, wrap its text, or set ' +
                         'max-width:100% on it. Flex/grid children need min-width:0 to shrink.'
                });
            }
        }
    });

    // ── L4 / L5: grid-row baseline & height alignment ─────────────────────
    const grids = document.querySelectorAll('[class*=grid],[class*=Grid]');
    grids.forEach(grid => {
        const cs = getComputedStyle(grid);
        if (cs.display !== 'grid' && cs.display !== 'flex') return;
        const dividedX = cs.columnGap !== '0px' || /divide-x/.test(grid.className) ||
                         Array.from(grid.children).some(c => {
                             const b = getComputedStyle(c);
                             return parseFloat(b.borderLeftWidth) > 0 || parseFloat(b.borderRightWidth) > 0;
                         });
        const cards = Array.from(grid.children).filter(c => {
            const r = c.getBoundingClientRect();
            return r.width > 0 && r.height > 0;
        });
        if (cards.length < 2) return;

        // group cards into rows by their top Y
        const rows = [];
        cards.forEach(c => {
            const top = c.getBoundingClientRect().top;
            let row = rows.find(rw => Math.abs(rw.top - top) <= RB);
            if (!row) { row = { top, cards: [] }; rows.push(row); }
            row.cards.push(c);
        });

        rows.forEach(row => {
            if (row.cards.length < 2) return;

            // L5: card height spread
            const heights = row.cards.map(c => c.getBoundingClientRect().height);
            const hSpread = Math.max(...heights) - Math.min(...heights);

            // L4: bottom-most element baseline spread (the "meta" line)
            const lastBottoms = row.cards.map(c => {
                const kids = Array.from(c.querySelectorAll('*')).filter(k => {
                    const r = k.getBoundingClientRect();
                    return r.height > 0 && r.width > 0 && (k.innerText || '').trim().length > 0;
                });
                if (!kids.length) return c.getBoundingClientRect().bottom;
                return Math.max(...kids.map(k => k.getBoundingClientRect().bottom));
            });
            const bSpread = Math.max(...lastBottoms) - Math.min(...lastBottoms);

            if (bSpread > BTOL) {
                out.warnings.push({
                    code: 'L4',
                    element: label(grid),
                    message: 'Ragged grid row in "' + label(grid) + '": the bottom-most content ' +
                             '(e.g. the meta/author line) of ' + row.cards.length +
                             ' sibling cards spans ' + Math.round(bSpread) + 'px of vertical drift' +
                             (dividedX ? ' while the column rules run full height' : '') +
                             ' — the cards do not share a baseline.',
                    fix: 'Make each card flex flex-col h-full and push the meta line to the bottom ' +
                         'with mt-auto. Then every card fills the row height and all meta lines align ' +
                         'on one baseline (real broadsheet behaviour).'
                });
            } else if (hSpread > HTOL && dividedX) {
                out.warnings.push({
                    code: 'L5',
                    element: label(grid),
                    message: 'Uneven card heights in divided row of "' + label(grid) + '": ' +
                             Math.round(hSpread) + 'px height spread between siblings sharing column rules.',
                    fix: 'Use h-full / items-stretch so cards in a row match height; otherwise the ' +
                         'full-height divider rules expose the imbalance.'
                });
            }
        });
    });

    return out;
}
"""


def run_audit(url, output_dir=None):
    cfg = {
        "overflowTol": OVERFLOW_TOL,
        "baselineTol": BASELINE_TOL,
        "heightTol": HEIGHT_TOL,
        "rowBucket": ROW_BUCKET,
    }
    results = {"url": url, "breakpoints": {}}
    launch_kwargs = {}
    # Prefer playwright's own chromium; fall back to system chromium if present.
    for cand in ("/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome"):
        if os.path.exists(cand):
            launch_kwargs["executable_path"] = cand
            break

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(**launch_kwargs)
        except Exception:
            browser = p.chromium.launch()  # let playwright resolve its bundled binary
        for name, w, h in BREAKPOINTS:
            page = browser.new_page(viewport={"width": w, "height": h})
            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
            except Exception:
                page.goto(url, wait_until="load", timeout=30000)
            page.wait_for_timeout(400)
            data = page.evaluate(_JS_LAYOUT, cfg)
            results["breakpoints"][name] = {"viewport": [w, h], **data}
            if output_dir:
                Path(output_dir).mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(Path(output_dir) / f"layout-{name}.png"), full_page=True)
            page.close()
        browser.close()
    return results


def main():
    ap = argparse.ArgumentParser(description="Layout-integrity gate (overflow + grid alignment).")
    ap.add_argument("--url", required=True, help="URL of the running site (e.g. http://localhost:3000)")
    ap.add_argument("--output", help="Directory to save per-breakpoint screenshots")
    ap.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    ap.add_argument("--strict", action="store_true", help="Treat WARN (L4/L5) as blocking too")
    args = ap.parse_args()

    results = run_audit(args.url, args.output)

    total_err = sum(len(b["errors"]) for b in results["breakpoints"].values())
    total_warn = sum(len(b["warnings"]) for b in results["breakpoints"].values())
    blocking = total_err + (total_warn if args.strict else 0)
    results["summary"] = {"errors": total_err, "warnings": total_warn, "passed": blocking == 0}

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print("=" * 64)
        print(f"LAYOUT AUDIT — {args.url}")
        print("=" * 64)
        for name, b in results["breakpoints"].items():
            vw = b["viewport"][0]
            if not b["errors"] and not b["warnings"]:
                print(f"  [{name:7} {vw:>4}px]  ✓ clean")
                continue
            print(f"  [{name:7} {vw:>4}px]  {len(b['errors'])} error(s), {len(b['warnings'])} warning(s)")
            for v in b["errors"]:
                print(f"      ✗ {v['code']}  {v['message']}")
                print(f"           ↳ fix: {v['fix']}")
            for v in b["warnings"]:
                print(f"      ⚠ {v['code']}  {v['message']}")
                print(f"           ↳ fix: {v['fix']}")
        print("-" * 64)
        verdict = "PASS" if results["summary"]["passed"] else "BLOCKED"
        print(f"  {verdict}  —  {total_err} error(s), {total_warn} warning(s)"
              f"{'  (strict: warnings block)' if args.strict else ''}")
        print("=" * 64)

    sys.exit(0 if blocking == 0 else 1)


if __name__ == "__main__":
    main()
