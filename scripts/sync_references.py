#!/usr/bin/env python3
"""
sync_references.py — keep data/getdesign-references.csv aligned with getdesign.

The anti-monoculture check (gate 0, recommendation #2) classifies Phase 0
references as saas / non-saas via data/getdesign-references.csv. That CSV is a
hand-curated snapshot of getdesign's catalogue. getdesign adds and removes
brands over time, so the snapshot drifts:

  - DEAD brands   — in the CSV but no longer in getdesign → `add <brand>` fails.
  - NEW brands    — in getdesign but missing from the CSV → diversity check
                    classifies them 'unknown' (no nudge value).

This script detects drift in BOTH directions and (optionally) appends new
brands for human review. It NEVER auto-deletes and NEVER overwrites the curated
'segment' column — saas/non-saas is a judgement call, not a keyword match.

Usage:
    python3 scripts/sync_references.py --check     # read-only, exits 1 on drift (CI)
    python3 scripts/sync_references.py --update    # append new brands as segment=unknown
    python3 scripts/sync_references.py --check --list-cmd "npx -y getdesign@latest list"

Exit codes:
  0 — CSV in sync (or --update completed)
  1 — drift detected (--check) / error
"""

import argparse
import csv
import re
import subprocess
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
REFERENCES_CSV = DATA_DIR / "getdesign-references.csv"
DEFAULT_LIST_CMD = "npx -y getdesign@latest list"

# Description keywords that *suggest* a non-saas segment for a NEW brand. Only a
# hint surfaced for human review — never written as a final classification.
_NON_SAAS_HINTS = [
    "automotive", "retail", "editorial", "magazine", "media", "consumer",
    "athletic", "coffee", "electronics", "hardware", "aerospace", "space",
    "gaming", "console", "catalog", "luxury", "supercar", "hypercar",
    "telecom", "payments network", "photography",
]
_SAAS_HINTS = [
    "saas", "api", "database", "dashboard", "developer", "dev tool", "devtool",
    "documentation", "docs", "platform", "infrastructure", "infra", "analytics",
    "crypto", "exchange", "fintech", "banking", "ai ", "llm", "automation",
    "cms", "scheduling", "monitoring", "collaboration", "workspace",
]


def normalize_brand(name: str) -> str:
    """Mirror check.py: lowercase, drop file prefixes/suffixes and TLD tails."""
    n = name.strip().lower()
    n = re.sub(r"\.md$", "", n)
    n = re.sub(r"^(getdesign|brand)-", "", n)
    n = re.sub(r"\.(app|ai|com|io|dev)$", "", n)
    return n


def parse_list_output(text: str) -> dict:
    """Parse getdesign list output into {brand_id: description}.

    Lines look like:  'stripe - Payment infrastructure. Signature purple ...'
    The brand id is kept verbatim (e.g. 'linear.app', 'nintendo-2001'); the
    normalized key is computed separately for matching.
    """
    brands = {}
    for raw in text.splitlines():
        line = raw.strip()
        # Strip ANSI escape codes that getdesign emits.
        line = re.sub(r"\033\[[0-9;]*m", "", line)
        m = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)\s+-\s+(.*)$", line)
        if not m:
            continue
        brand_id, desc = m.group(1).strip(), m.group(2).strip()
        brands[brand_id] = desc
    return brands


def load_csv(path: Path) -> list:
    """Return list of row dicts (preserves order)."""
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def suggest_segment(description: str) -> str:
    """Heuristic hint for a NEW brand's segment — for review, not authority."""
    d = description.lower()
    non_saas = any(h in d for h in _NON_SAAS_HINTS)
    saas = any(h in d for h in _SAAS_HINTS)
    if non_saas and not saas:
        return "non-saas"
    if saas and not non_saas:
        return "saas"
    return "unknown"


def suggest_category(description: str) -> str:
    """First non-saas/saas hint that matched, else 'review'."""
    d = description.lower()
    for h in _NON_SAAS_HINTS + _SAAS_HINTS:
        if h in d:
            return h.strip().replace(" ", "-")
    return "review"


def compute_drift(catalogue: dict, rows: list):
    """Return (dead, new) — CSV brands absent from getdesign, and vice versa."""
    cat_keys = {normalize_brand(b) for b in catalogue}
    csv_keys = {normalize_brand(r.get("brand", "")) for r in rows}
    dead = sorted(csv_keys - cat_keys)
    new = sorted(b for b in catalogue if normalize_brand(b) not in csv_keys)
    return dead, new


def run_list(list_cmd: str) -> str:
    """Run the getdesign list command and return stdout."""
    parts = list_cmd.split()
    r = subprocess.run(parts, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=180)
    if r.returncode != 0:
        raise RuntimeError(f"`{list_cmd}` failed (exit {r.returncode}): {r.stderr[:300]}")
    return r.stdout


def append_new_brands(path: Path, catalogue: dict, new_keys: list) -> int:
    """Append new brands as segment=unknown for human review. Returns count."""
    by_norm = {normalize_brand(b): b for b in catalogue}
    added = 0
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for nk in new_keys:
            brand_id = by_norm.get(nk, nk)
            desc = catalogue.get(brand_id, "")
            seg = suggest_segment(desc)
            note = f"AUTO-ADDED, review segment (hint: {seg}) — {desc[:80]}"
            w.writerow([brand_id, suggest_category(desc), "unknown", note])
            added += 1
    return added


def main() -> int:
    p = argparse.ArgumentParser(
        prog="sync_references",
        description="Detect and repair drift between data/getdesign-references.csv and getdesign's live catalogue.",
    )
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true",
                      help="Read-only: report drift, exit 1 if any (CI-friendly). Default.")
    mode.add_argument("--update", action="store_true",
                      help="Append NEW brands as segment=unknown for review. Never deletes.")
    p.add_argument("--list-cmd", default=DEFAULT_LIST_CMD,
                   help=f"Command that prints the getdesign catalogue (default: '{DEFAULT_LIST_CMD}')")
    p.add_argument("--list-file", type=Path, default=None,
                   help="Read the catalogue from a file instead of running --list-cmd (offline/testing).")
    args = p.parse_args()

    rows = load_csv(REFERENCES_CSV)
    if not rows:
        print(f"[ERROR] {REFERENCES_CSV} missing or empty.", file=sys.stderr)
        return 1

    try:
        if args.list_file:
            text = args.list_file.read_text(encoding="utf-8")
        else:
            text = run_list(args.list_cmd)
    except Exception as e:  # noqa: BLE001
        print(f"[ERROR] could not obtain catalogue: {e}", file=sys.stderr)
        return 1

    catalogue = parse_list_output(text)
    if not catalogue:
        print("[ERROR] catalogue parsed empty — check the list command output.", file=sys.stderr)
        return 1

    dead, new = compute_drift(catalogue, rows)

    print(f"getdesign catalogue: {len(catalogue)} brands | CSV: {len(rows)} rows")
    if dead:
        print(f"\n  DEAD ({len(dead)}) — in CSV but gone from getdesign (`add` will fail):")
        for b in dead:
            print(f"    - {b}")
        print("    -> remove these rows manually (deletion is never automatic).")
    if new:
        print(f"\n  NEW ({len(new)}) — in getdesign but missing from CSV:")
        for b in new:
            hint = suggest_segment(catalogue.get(b, ""))
            print(f"    + {b}  (segment hint: {hint})")

    if not dead and not new:
        print("\n[OK] CSV is in sync with the getdesign catalogue.")
        return 0

    if args.update:
        if new:
            added = append_new_brands(REFERENCES_CSV, catalogue, new)
            print(f"\n[UPDATED] appended {added} new brand(s) as segment=unknown — "
                  "review and set saas/non-saas by hand.")
        if dead:
            print("[NOTE] dead brands were NOT removed (manual review required).")
        return 0

    # --check (default): drift is a non-zero exit so CI can catch it.
    print("\n[DRIFT] CSV out of sync. Run with --update to append new brands, "
          "and remove dead rows by hand.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
