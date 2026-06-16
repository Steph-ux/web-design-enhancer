#!/usr/bin/env python3
"""
visual_audit.py — Playwright visual audit for AI-generated web pages.

Checks on the REAL rendered DOM (what regex cannot catch in static files):
  G-group: status badges, ALL_CAPS labels, too many fonts, asymmetric grids
  A-group: emojis in headings/buttons (A1), hardcoded fake stats (A2),
           trusted-by sections (A3), testimonial blockquotes (A4),
           Lorem ipsum (A5), placeholder image URLs (A6)
  Spacing: margins/paddings that violate the 8px grid

Screenshots captured on 4 breakpoints: 375 / 768 / 1280 / 1920 px.

Usage:
    python3 scripts/visual_audit.py --url http://localhost:3000 --output ./audit-results
"""

import asyncio
import argparse
import json
from pathlib import Path

# ── Breakpoints ──────────────────────────────────────────────────────────────

BREAKPOINTS = [
    ("mobile",  375,  667),
    ("tablet",  768,  1024),
    ("desktop", 1280, 800),
    ("wide",    1920, 1080),
]

# ── JS audit code — raw string avoids Python misinterpreting \b \d \s etc. ──
# This is evaluated inside the Playwright page context.

_JS_AUDIT = r"""
() => {
    const elements = document.querySelectorAll('h1, h2, h3, p, button, section, div, span, article');
    const fonts = new Set();
    const spacingErrors = [];
    const slopElements = [];

    const isMultipleOf8 = (val) => {
        const num = parseInt(val);
        return isNaN(num) || num === 0 || num % 8 === 0 || num === 4;
    };

    elements.forEach(el => {
        const cs = window.getComputedStyle(el);
        const text = (el.innerText || "").trim();
        const tag = el.tagName.toLowerCase();

        // 1. Loaded fonts
        fonts.add(cs.fontFamily.split(",")[0].trim().replace(/['"]/g, ""));

        // 2. Spacing audit — 8px grid
        ["paddingTop", "paddingBottom", "paddingLeft", "paddingRight", "marginTop", "marginBottom"].forEach(prop => {
            if (!isMultipleOf8(cs[prop])) {
                spacingErrors.push(tag + "." + el.className.split(" ")[0] + ": " + prop + "=" + cs[prop]);
            }
        });

        // 3. G1/G2: System status badge (SYS_STATUS: ONLINE, OPTIMAL, STABLE…)
        if (/[A-Z][A-Z_]{3,}:\s*[A-Z][A-Z_]+/.test(text) && text.length < 50) {
            slopElements.push('Status badge: "' + text + '" — AI slop');
        }

        // 4. G5: ALL_CAPS button text
        if ((tag === "button" || el.closest("button")) && text.length > 3) {
            const isUpper = cs.textTransform === "uppercase" ||
                            (text === text.toUpperCase() && /[A-Z]{3}/.test(text));
            if (isUpper) slopElements.push('ALL_CAPS button: "' + text.substring(0, 40) + '"');
        }

        // 5. G5: ALL_CAPS labels inside cards
        if (/^[A-Z][A-Z'\s]{6,}\s*:/.test(text) && text.length < 60) {
            if (el.closest("[class*=card],[class*=Card],article")) {
                slopElements.push('ALL_CAPS label: "' + text.substring(0, 50) + '"');
            }
        }

        // 6. Asymmetric grid (orphan card columns)
        if (el.matches("[class*=grid],[class*=Grid]")) {
            const cards = el.querySelectorAll("[class*=card],[class*=Card],article");
            if (cards.length > 0) {
                const cols = cs.gridTemplateColumns === "none" ? 1 : cs.gridTemplateColumns.split(" ").length;
                if (cols >= 3 && cards.length % cols !== 0) {
                    slopElements.push("Asymmetric grid: " + cards.length + " cards / " + cols + " col");
                }
            }
        }

        // 7. Over-empty section (padding > 192px with ≤ 2 children)
        if (tag === "section") {
            const pTop = parseInt(cs.paddingTop) || 0;
            const pBot = parseInt(cs.paddingBottom) || 0;
            if ((pTop + pBot) > 192 && el.children.length <= 2) {
                slopElements.push("Over-empty section: padding " + (pTop + pBot) + "px, " + el.children.length + " children");
            }
        }
    });

    // 8. Too many font families
    const fontList = Array.from(fonts).filter(f => f && f.length > 1);
    if (fontList.length > 3) {
        slopElements.push("Too many fonts: " + fontList.length + " families (" + fontList.slice(0, 4).join(", ") + ")");
    }

    // ── A-group: content authenticity (render-level) ─────────────────────────
    const aGroupSlop = [];

    // A1: Emojis in headings and buttons
    // Uses codePointAt — no \u{} escape sequences needed in the regex engine
    const hasEmoji = (str) => {
        for (const cp of str) {
            const c = cp.codePointAt(0);
            if ((c >= 0x1F300 && c <= 0x1FAFF) ||
                (c >= 0x2600  && c <= 0x27BF)  ||
                (c >= 0xFE00  && c <= 0xFEFF)) return true;
        }
        return false;
    };
    document.querySelectorAll('h1,h2,h3,h4,button,a.btn,[class*="nav"] li').forEach(el => {
        const t = (el.firstChild && el.firstChild.nodeType === 3
            ? el.firstChild.textContent
            : el.innerText || '').trim();
        if (hasEmoji(t)) {
            aGroupSlop.push('A1 Emoji in <' + el.tagName.toLowerCase() + '>: "' + t.substring(0, 60) + '"');
        }
    });

    // A2: Hardcoded fake stats (N,NNN+ users / 99.9% / 500ms response)
    const statRx = /\b(\d[\d,]+[+k]+\s*(users?|utilisateurs?|clients?)|\d{2,3}[.,]\d%|\d+\s*ms\s*(response|latency|latence))/i;
    document.querySelectorAll('[class*="stat"],[class*="metric"],[class*="count"],[class*="kpi"],strong,b').forEach(el => {
        const t = (el.innerText || '').trim();
        if (statRx.test(t) && el.closest('script') === null) {
            aGroupSlop.push('A2 Hardcoded stat (verify from real data): "' + t.substring(0, 80) + '"');
        }
    });

    // A3: Invented trusted-by / logo-wall sections
    document.querySelectorAll('[class*="trusted"],[class*="partner"],[class*="logo-wall"],[class*="logowall"],[class*="clients"]').forEach(el => {
        if (el.querySelectorAll('img,svg').length >= 2) {
            aGroupSlop.push('A3 Trusted-by/logo-wall section: <' + el.tagName.toLowerCase() + ' class="' + el.className.substring(0, 50) + '">');
        }
    });

    // A4: Hardcoded testimonial blockquotes with <cite>
    document.querySelectorAll('blockquote').forEach(el => {
        const t = (el.innerText || '').trim();
        const hasCite = el.querySelector('cite') !== null;
        if (hasCite && t.length > 20) {
            aGroupSlop.push('A4 Testimonial blockquote — verify data comes from CMS/API: "' + t.substring(0, 80) + '"');
        }
    });

    // A5: Lorem ipsum placeholder text
    const allText = document.body.innerText || '';
    if (/lorem ipsum/i.test(allText)) {
        aGroupSlop.push('A5 Lorem ipsum placeholder text visible in rendered page');
    }

    // A6: Placeholder image URLs
    document.querySelectorAll('img').forEach(el => {
        const src = el.src || '';
        if (/picsum\.photos|via\.placeholder|dummyimage\.com|placehold\.co/.test(src)) {
            aGroupSlop.push('A6 Placeholder image URL: ' + src.substring(0, 100));
        }
    });

    return {
        fonts:         fontList,
        spacingErrors: spacingErrors.slice(0, 20),
        slopElements:  slopElements,
        aGroupSlop:    aGroupSlop
    };
}
"""


# ── Main audit coroutine ─────────────────────────────────────────────────────

async def run_audit(url: str, output_dir: str):
    from playwright.async_api import async_playwright

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    results = {
        "url":             url,
        "fonts":           [],
        "spacing_errors":  [],
        "ai_slop_detected": [],
        "a_group_slop":    [],
        "screenshots":     {}
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page    = await context.new_page()

        print(f"[INFO] Navigating to {url}...")
        try:
            await page.goto(url, wait_until="networkidle")
        except Exception as e:
            print(f"[ERROR] Navigation error: {e}")
            await browser.close()
            return

        # 1. Screenshots — 4 breakpoints
        print("[INFO] Capturing screenshots (4 breakpoints)...")
        for name, width, height in BREAKPOINTS:
            await page.set_viewport_size({"width": width, "height": height})
            shot = str(output_path / f"{name}.png")
            await page.screenshot(path=shot, full_page=True)
            results["screenshots"][name] = shot
            print(f"   - {name} ({width}x{height}px)")

        # Back to desktop reference viewport
        await page.set_viewport_size({"width": 1280, "height": 800})

        # 2. DOM audit via JS
        print("[INFO] Analyzing DOM and computed styles...")
        data = await page.evaluate(_JS_AUDIT)

        results["fonts"]            = data["fonts"]
        results["spacing_errors"]   = data["spacingErrors"]
        results["ai_slop_detected"] = data["slopElements"]
        results["a_group_slop"]     = data["aGroupSlop"]

        await browser.close()

    # Save JSON report
    with open(output_path / "audit_report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Print summary
    n_g = len(results["ai_slop_detected"])
    n_a = len(results["a_group_slop"])
    n_s = len(results["spacing_errors"])
    total_slop = n_g + n_a

    print(f"\n{'='*60}")
    print(f"  VISUAL AUDIT REPORT")
    print(f"{'='*60}")
    print(f"  Screenshots : {len(results['screenshots'])} breakpoints ({', '.join(results['screenshots'].keys())})")
    print(f"  Fonts       : {len(results['fonts'])} famil(y/ies) detected")
    print(f"  Spacing     : {n_s} 8px grid violation(s)")
    print(f"  Slop G-group: {n_g} violation(s)")
    print(f"  Slop A-group: {n_a} violation(s)")

    if total_slop > 0:
        print(f"\n  [ERROR] {total_slop} AI slop element(s) in rendered DOM:")
        for item in results["ai_slop_detected"] + results["a_group_slop"]:
            print(f"    - {item}")
    else:
        print("\n  [OK] No AI slop detected in the rendered DOM.")

    print(f"\n  Full report: {output_dir}/audit_report.json")
    print(f"{'='*60}\n")


# ── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Playwright visual audit — detects AI slop in the rendered DOM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python3 scripts/visual_audit.py --url http://localhost:3000 --output ./audit-results
"""
    )
    parser.add_argument("--url",    default="http://localhost:3000", help="URL of the running dev server")
    parser.add_argument("--output", default="./audit-results",       help="Directory to write screenshots + report")
    args = parser.parse_args()

    asyncio.run(run_audit(args.url, args.output))
