"""Validate aesthetic-verdict.json — independence class + pass bar 80."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from wde.checks.base import Check, CheckResult, Finding

# Plan §8.4 independence modes → trust class
# declared = free-text claim (independent-clone without external proof)
# verified = human / independent (still honor-system without signatures, but not "clone" label alone)
INDEPENDENCE_CLASS = {
    "human": "verified",
    "independent": "verified",
    "independent-clone": "declared",
    "clone": "declared",
    "self": "weak",
    "agent": "weak",
    "": "weak",
    "unknown": "weak",
}

INDEPENDENCE_LEVEL = {
    "verified": "strong",
    "declared": "medium",
    "weak": "weak",
}

# Self cannot authorize delivery
BLOCKING_REVIEWERS = {"", "self", "agent", "unknown"}

# Align with README: floor 62 diagnostics / pass 80 for delivery-grade
PASS_SCORE = 80
FLOOR_SCORE = 62

REQUIRED_DIMS = [
    "first_impression",
    "hierarchy",
    "spacing_rhythm",
    "colour_restraint",
    "typography",
    "component_polish",
    "mobile",
]


class AestheticVerdictCheck(Check):
    id = "visual.aesthetic"
    version = "2.0.0"
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
            raw = path.read_text(encoding="utf-8-sig")
            verdict = json.loads(raw)
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
        ind_class = INDEPENDENCE_CLASS.get(reviewer, "weak")
        level = INDEPENDENCE_LEVEL[ind_class]

        if reviewer in BLOCKING_REVIEWERS or ind_class == "weak":
            findings.append(
                Finding(
                    "PROVENANCE",
                    str(path),
                    f"reviewer={reviewer or 'unset'} class={ind_class}",
                    "Self/unknown review cannot authorize delivery",
                    "Use reviewer independent|human (verified) or independent-clone with provenance",
                )
            )

        # Provenance block (declared vs verified)
        provenance = verdict.get("provenance") if isinstance(verdict.get("provenance"), dict) else {}
        package_digest = str(
            verdict.get("package_digest") or provenance.get("package_digest") or ""
        ).strip()
        pkg_path = root / ".wde" / "reports" / "review-package" / "package.json"
        if pkg_path.is_file() and package_digest:
            try:
                from wde.core.hashing import sha256_text

                live = sha256_text(pkg_path.read_text(encoding="utf-8"))
                if package_digest != live and not package_digest.startswith("sha256:"):
                    # accept either bare hex or sha256:hex
                    if package_digest.replace("sha256:", "") != live.replace("sha256:", ""):
                        # compare hex portion
                        pd = package_digest.split(":")[-1]
                        if pd != live and f"sha256:{pd}" != live:
                            findings.append(
                                Finding(
                                    "PACKAGE-DIGEST",
                                    str(path),
                                    package_digest[:24],
                                    "package_digest does not match current review package",
                                    "Re-emit package and re-judge against current code",
                                )
                            )
            except OSError:
                pass
        elif ind_class == "declared":
            # Binding package_digest to live review package upgrades local demos when allowed
            allow_declared = os.environ.get("WDE_ALLOW_DECLARED_INDEPENDENCE", "").strip().lower() in {
                "1",
                "true",
                "yes",
            }
            bound = bool(package_digest and pkg_path.is_file())
            if not allow_declared and not bound:
                findings.append(
                    Finding(
                        "DECLARED-ONLY",
                        str(path),
                        "reviewer=independent-clone without package_digest/provenance",
                        "Declared independence is not externally verified",
                        "Set reviewer=independent|human, or add package_digest + "
                        "WDE_ALLOW_DECLARED_INDEPENDENCE=1 for local demos only",
                    )
                )
            elif allow_declared and bound:
                # local demo path: treat as medium accepted later by review.py when env set
                ind_class = "declared"
                level = "medium"

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

        reads = str(verdict.get("reads_as", "")).strip().lower()
        if reads == "ai":
            findings.append(
                Finding(
                    "READS-AI",
                    str(path),
                    "reads_as=ai",
                    "Verdict says page still reads as AI",
                    "Raise craft until reads_as=human",
                )
            )
        elif reads and reads != "human":
            findings.append(
                Finding(
                    "READS-NOT-HUMAN",
                    str(path),
                    f"reads_as={reads}",
                    "Delivery requires reads_as=human",
                    "Re-judge after craft fixes",
                )
            )
        elif not reads:
            findings.append(
                Finding(
                    "READS-MISSING",
                    str(path),
                    "reads_as unset",
                    "reads_as required (human)",
                    "Set reads_as: human",
                )
            )

        score = verdict.get("overall_score")
        try:
            score_n = float(score)
        except (TypeError, ValueError):
            score_n = -1
        if score_n < 0:
            findings.append(
                Finding(
                    "SCORE-MISSING",
                    str(path),
                    str(score),
                    "overall_score missing",
                    "Provide numeric overall_score",
                )
            )
        elif score_n < FLOOR_SCORE:
            findings.append(
                Finding(
                    "SCORE-FLOOR",
                    str(path),
                    f"overall_score={score_n}",
                    f"Below human-craft floor ({FLOOR_SCORE})",
                    "Improve craft and re-judge",
                )
            )
        elif score_n < PASS_SCORE:
            findings.append(
                Finding(
                    "SCORE-PASS",
                    str(path),
                    f"overall_score={score_n}",
                    f"Below delivery pass bar ({PASS_SCORE}) — floor {FLOOR_SCORE} only for diagnostics",
                    "Raise craft to overall_score >= 80",
                )
            )

        dims = verdict.get("dimensions") or verdict.get("scores") or {}
        if not isinstance(dims, dict) or not dims:
            findings.append(
                Finding(
                    "NO-DIMS",
                    str(path),
                    "dimensions missing",
                    "Per-dimension scores required for delivery",
                    f"Provide dimensions for: {', '.join(REQUIRED_DIMS)}",
                )
            )
        else:
            missing = [d for d in REQUIRED_DIMS if d not in dims]
            if missing:
                findings.append(
                    Finding(
                        "DIM-INCOMPLETE",
                        str(path),
                        ",".join(missing),
                        f"Missing required dimensions ({len(missing)})",
                        "Score every required dimension with note/evidence",
                    )
                )
            for d, v in dims.items():
                if isinstance(v, dict):
                    note = str(v.get("note") or v.get("evidence") or "").strip()
                    if not note:
                        findings.append(
                            Finding(
                                "NO-DIM-EVIDENCE",
                                str(path),
                                d,
                                f"Dimension {d} lacks note/evidence",
                                "Add localized proof per dimension",
                            )
                        )
                    sc = v.get("score")
                    try:
                        float(sc)
                    except (TypeError, ValueError):
                        findings.append(
                            Finding(
                                "DIM-SCORE",
                                str(path),
                                d,
                                f"Dimension {d} missing numeric score",
                                "Add score: N",
                            )
                        )
                else:
                    findings.append(
                        Finding(
                            "DIM-SHAPE",
                            str(path),
                            d,
                            f"Dimension {d} must be object with score + note",
                            '{"score": N, "note": "…"}',
                        )
                    )

        blocking = [f for f in findings if f.severity == "blocking"]
        # All findings in this check are blocking by default
        for f in findings:
            if f.severity not in {"blocking", "major", "minor"}:
                f.severity = "blocking"
        blocking = [f for f in findings if f.severity == "blocking"]
        status = "passed" if not blocking else "failed"

        return CheckResult(
            self.id,
            status,
            "blocking" if blocking else "major",
            self.category,
            (
                f"Aesthetic verdict OK (class={ind_class}, independence={level}, reviewer={reviewer or 'unset'})"
                if status == "passed"
                else f"Aesthetic verdict blocked ({len(blocking)} issue(s), class={ind_class})"
            ),
            findings,
            {
                "reviewer": reviewer,
                "independence": level,
                "independence_class": ind_class,
                "overall_score": score_n,
                "path": str(path),
                "pass_score": PASS_SCORE,
            },
            artifacts=[str(path)],
        )
