#!/usr/bin/env python3
"""Gate: enforce the project's OWN declared antipatterns.

The skill lets each project declare what it must NOT do, in two places:
  - DESIGN.md            -> "Sector antipatterns to avoid: ..."
  - design-system-output -> a "## Avoid" / "Avoid:" line.

Until now those lists were advisory prose that nothing checked. A real delivery
declared "avoid: fake system console" and then shipped a full terminal cosplay,
passing every gate. This gate closes that hole: it reads the project's declared
antipatterns, turns each into a search phrase, and scans the delivered code/text.
Any hit BLOCKS — the project violated a rule it set for itself.

Usage:
    python3 scripts/audit_declared_antipatterns.py --code ./src \
        [--design DESIGN.md] [--system design-system-output.md] [--json]

Exit codes:
    0 - no declared antipattern found in the code
    1 - at least one declared antipattern appears in the delivered output
    2 - usage / IO error
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Phrases too generic to grep literally — matching them would false-positive on
# ordinary content. We keep multi-word antipatterns and drop bare stopwords.
_STOP = {
    "slop", "spam", "effects", "effect", "fake", "neon", "glow", "glows",
    "cursor", "cursors", "grid", "grids", "background", "backgrounds",
    "blurred", "panels", "panel", "emoji", "badges", "badge", "animations",
    "animation", "and", "or", "the", "a", "an", "with", "of", "to",
}

# Code file types whose visible text/markup we scan.
_EXTS = ("*.html", "*.htm", "*.css", "*.js", "*.jsx", "*.ts", "*.tsx",
         "*.vue", "*.svelte", "*.astro")


def _extract_avoid_phrases(text: str) -> list[str]:
    """Pull declared antipattern phrases out of a spec's markdown."""
    phrases: list[str] = []
    # 1) "Sector antipatterns to avoid: a, b, c" (DESIGN.md, inline)
    for m in re.finditer(
        r"(?:antipatterns?\s+to\s+avoid|antipatterns?|avoid)\s*[:\-]\s*(.+)",
        text, re.IGNORECASE,
    ):
        phrases += re.split(r"[,;.]", m.group(1))
    # 2) "## Avoid" section (design-system-output) — capture following bullet/line block
    for m in re.finditer(r"^#+\s*Avoid\s*$\n(.+?)(?:\n#|\Z)", text,
                         re.IGNORECASE | re.MULTILINE | re.DOTALL):
        block = m.group(1)
        for line in block.splitlines():
            line = line.strip().lstrip("-*0123456789. ").strip()
            phrases += re.split(r"[,;]", line)
    return phrases


def _normalise(phrases: list[str]) -> list[str]:
    """Clean phrases into greppable multi-word antipatterns."""
    out: list[str] = []
    seen: set[str] = set()
    for raw in phrases:
        p = re.sub(r"\([^)]*\)", " ", raw)          # drop parentheticals
        p = re.sub(r"[`'\"*]", " ", p)
        p = re.sub(r"\s+", " ", p).strip().lower()
        if not p:
            continue
        words = [w for w in re.findall(r"[a-zà-ÿ]+", p) if w not in _STOP]
        # Need a meaningful multi-word phrase (avoids matching a single stopword
        # like "console" everywhere). Keep 2+ content words, or one long word.
        if len(words) >= 2:
            phrase = " ".join(words)
        elif len(words) == 1 and len(words[0]) >= 6:
            phrase = words[0]
        else:
            continue
        if phrase not in seen:
            seen.add(phrase)
            out.append(phrase)
    return out


def _scan(code_dir: Path, phrases: list[str]) -> list[dict]:
    hits: list[dict] = []
    files: list[Path] = []
    for ext in _EXTS:
        files += list(code_dir.rglob(ext))
    for fp in files:
        try:
            text = fp.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        # Strip markup/separators so "fake system console" matches
        # "fake-system-console", "fakeSystemConsole", "fake_system console".
        flat = re.sub(r"[^a-zà-ÿ]+", " ", text)
        for phrase in phrases:
            pat = r"\b" + r"\s*".join(re.escape(w) for w in phrase.split()) + r"\b"
            if re.search(pat, flat):
                hits.append({"phrase": phrase, "file": fp.name})
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--code", required=True, help="Source code directory to scan")
    ap.add_argument("--design", default="DESIGN.md", help="Path to DESIGN.md")
    ap.add_argument("--system", default="design-system-output.md",
                    help="Path to design-system-output.md")
    ap.add_argument("--json", action="store_true", help="Machine-readable output")
    args = ap.parse_args()

    code_dir = Path(args.code)
    if not code_dir.is_dir():
        print(f"Error: code dir not found: {code_dir}", file=sys.stderr)
        return 2

    raw_phrases: list[str] = []
    sources_read: list[str] = []
    for spec in (args.design, args.system):
        sp = Path(spec)
        if sp.exists():
            raw_phrases += _extract_avoid_phrases(sp.read_text(encoding="utf-8", errors="ignore"))
            sources_read.append(sp.name)

    phrases = _normalise(raw_phrases)
    if not phrases:
        msg = ("No declared antipatterns found (no DESIGN.md/design-system-output.md "
               "'Avoid' list). Gate skipped.")
        print(json.dumps({"status": "skipped", "reason": msg}) if args.json else f"[INFO] {msg}")
        return 0

    hits = _scan(code_dir, phrases)

    if args.json:
        print(json.dumps({
            "sources": sources_read, "declared_antipatterns": phrases,
            "violations": hits, "passed": not hits,
        }, indent=2, ensure_ascii=False))
    else:
        print("=" * 60)
        print("  DECLARED-ANTIPATTERN GATE")
        print("=" * 60)
        print(f"  Sources: {', '.join(sources_read)}")
        print(f"  Watching {len(phrases)} declared antipattern(s).")
        if hits:
            print(f"\n  [ERROR] {len(hits)} self-declared antipattern(s) appear in the delivery:")
            for h in hits:
                print(f"     - '{h['phrase']}'  ->  {h['file']}")
            print("\n  The project's own DESIGN.md / design-system-output said to AVOID these.")
            print("  Remove them or, if genuinely required, delete them from the Avoid list")
            print("  with a written justification — do not ship a rule you set against yourself.")
        else:
            print("\n  [OK] None of the project's declared antipatterns appear in the code.")
        print("=" * 60)

    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
