#!/usr/bin/env python3
"""eyes_checklist.py — verify Playwright Eyes artifacts before delivery claims.

Does NOT replace visual_audit / aesthetic_review scoring. It only checks that
the agent produced the minimum evidence tree required by vision-playwright.md:
  - audit-results/mcp/*.png (or .jpg) — MCP screenshots
  - audit-results/audit_report.json — mechanical visual audit
  - audit-results/aesthetic-verdict.json — non-self verdict with memorable_idea

Usage:
  python3 scripts/eyes_checklist.py --audit-output ./audit-results
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def check_eyes_artifacts(audit_dir: Path) -> list[str]:
    errors: list[str] = []
    if not audit_dir.exists() or not audit_dir.is_dir():
        return [f"Eyes audit directory missing or not a directory: {audit_dir}"]

    mcp = audit_dir / "mcp"
    shots = []
    if mcp.is_dir():
        shots = [p for p in mcp.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}]
    # Degraded mode: accept top-level visual_audit screenshots if mcp/ empty but
    # at least 2 images exist under audit_dir (agent must still set degraded flag in verdict).
    if len(shots) < 1:
        loose = [
            p for p in audit_dir.rglob("*")
            if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
            and "mcp" not in p.parts  # counted separately
        ]
        if len(loose) < 2:
            errors.append(
                "Eyes screenshots missing — need audit-results/mcp/*.png from Playwright MCP "
                "(or ≥2 rendered PNGs from visual_audit in degraded mode). "
                "See references/vision-playwright.md."
            )

    report = audit_dir / "audit_report.json"
    if not report.is_file():
        errors.append(
            "audit_report.json missing — run: python3 scripts/visual_audit.py --url <URL> "
            f"--output {audit_dir}"
        )

    verdict_path = audit_dir / "aesthetic-verdict.json"
    if not verdict_path.is_file():
        errors.append(
            "aesthetic-verdict.json missing — complete vision judgment per "
            "references/vision-playwright.md"
        )
    else:
        try:
            v = json.loads(verdict_path.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append(f"aesthetic-verdict.json unreadable: {e}")
            v = None
        if isinstance(v, dict):
            reviewer = str(v.get("reviewer", "")).strip().lower()
            if reviewer in {"", "self", "agent"}:
                errors.append(
                    f"PROVENANCE: reviewer='{reviewer or 'unset'}' cannot authorize delivery "
                    "(use independent-clone, independent, or human)."
                )
            idea = v.get("memorable_idea")
            if not (isinstance(idea, str) and len(idea.strip()) >= 8):
                errors.append(
                    "memorable_idea missing or too short — name one owned, visible design move."
                )
            if str(v.get("reads_as", "")).strip().lower() == "ai":
                errors.append("reads_as: ai — page still reads as AI; fix craft before delivery.")

    return errors


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Verify Eyes artifacts for web-design-enhancer")
    p.add_argument("--audit-output", default="./audit-results", help="Audit directory")
    args = p.parse_args(argv)
    errs = check_eyes_artifacts(Path(args.audit_output))
    if errs:
        print("EYES CHECKLIST — FAILED")
        for e in errs:
            print(f"  - {e}")
        return 1
    print("EYES CHECKLIST — PASSED")
    print(f"  artifacts OK under {args.audit_output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
