"""Validate aesthetic-verdict.json independence + floor (does not invent beauty)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from wde.checks.base import Check, CheckResult, Finding

# Plan §8.4 independence modes
INDEPENDENCE = {
    "human": "strong",
    "independent": "strong",
    "independent-clone": "medium",
    "clone": "medium",
    "self": "weak",
    "agent": "weak",
    "": "unavailable",
}

# Self cannot authorize delivery (matches V2 check.py policy)
BLOCKING_REVIEWERS = {"", "self", "agent", "unknown"}


class AestheticVerdictCheck(Check):
    id = "visual.aesthetic"
    version = "1.0.0"
    category = "taste_preference"
    default_severity = "blocking"
    required_capabilities: list[str] = []

    def run(self, context: dict[str, Any]) -> CheckResult:
        root = Path(context["root"])
        candidates = [
            root / "audit-results" / "aesthetic-verdict.json",
            root / ".wde" / "reports" / "aesthetic-verdict.json",
        ]
        path = next((p for p in candidates if p.is_file()), None)
        if not path:
            return CheckResult(
                self.id,
                "failed",
                "blocking",
                self.category,
                "No aesthetic-verdict.json — run visual review (or mark unverified)",
                [
                    Finding(
                        "NO-VERDICT",
                        "audit-results/aesthetic-verdict.json",
                        "missing",
                        "Independent visual judgment not recorded",
                        "wde review --emit-package then write verdict with non-self reviewer",
                    )
                ],
            )

        try:
            verdict = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            return CheckResult(
                self.id,
                "failed",
                "blocking",
                self.category,
                f"Unreadable verdict: {e}",
            )

        findings: list[Finding] = []
        reviewer = str(verdict.get("reviewer", "")).strip().lower()
        level = INDEPENDENCE.get(reviewer, "unavailable")
        if reviewer in BLOCKING_REVIEWERS:
            findings.append(
                Finding(
                    "PROVENANCE",
                    str(path),
                    f"reviewer={reviewer or 'unset'}",
                    "Self/unknown review cannot authorize delivery",
                    "Use independent-clone, independent, or human reviewer",
                )
            )

        idea = verdict.get("memorable_idea")
        if not (isinstance(idea, str) and len(idea.strip()) >= 8):
            findings.append(
                Finding(
                    "NO-SIGNATURE",
                    str(path),
                    str(idea),
                    "memorable_idea missing or too short",
                    "Name one owned, visible design move",
                )
            )

        if str(verdict.get("reads_as", "")).strip().lower() == "ai":
            findings.append(
                Finding(
                    "READS-AI",
                    str(path),
                    "reads_as=ai",
                    "Verdict says page still reads as AI",
                    "Raise craft until reads_as=human",
                )
            )

        score = verdict.get("overall_score")
        try:
            score_n = float(score)
        except (TypeError, ValueError):
            score_n = -1
        # Floor aligns with V2 aesthetic floor (~62); pass bar not enforced here alone
        if score_n >= 0 and score_n < 62:
            findings.append(
                Finding(
                    "SCORE-FLOOR",
                    str(path),
                    f"overall_score={score_n}",
                    "Below human-craft floor (62)",
                    "Improve craft and re-judge",
                )
            )

        # Dimension evidence required by plan §8.3 when dimensions present
        dims = verdict.get("dimensions") or verdict.get("scores")
        if isinstance(dims, dict) and dims and not any(
            isinstance(v, dict) and v.get("evidence") for v in dims.values()
        ):
            # soft: only warn if scores are bare numbers without evidence
            if all(not isinstance(v, dict) for v in dims.values()):
                findings.append(
                    Finding(
                        "NO-DIM-EVIDENCE",
                        str(path),
                        "dimensions lack per-axis evidence",
                        "Plan requires localized proof per dimension",
                        "Add evidence strings per scored dimension",
                        severity="major",
                    )
                )

        passed = not any(f.severity == "blocking" for f in findings)
        # Treat major-only as warned not failed for delivery of aesthetic? Plan: signature blocking
        blocking = [f for f in findings if f.severity == "blocking"]
        status = "passed" if not blocking else "failed"

        return CheckResult(
            self.id,
            status,
            "blocking" if blocking else "major",
            self.category,
            (
                f"Aesthetic verdict OK (independence={level}, reviewer={reviewer or 'unset'})"
                if status == "passed"
                else f"Aesthetic verdict blocked ({len(blocking)} issue(s), independence={level})"
            ),
            findings,
            {
                "reviewer": reviewer,
                "independence": level,
                "overall_score": score_n,
                "path": str(path),
            },
            artifacts=[str(path)],
        )
