"""Bridge: audit_beauty.py"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from wde.checks.base import Check, CheckResult, Finding
from wde.runners.subprocess_runner import run_python_script


class BeautyStaticCheck(Check):
    id = "beauty.score"
    version = "1.0.0"
    category = "anti_template_heuristic"
    default_severity = "major"

    def run(self, context: dict[str, Any]) -> CheckResult:
        root = Path(context["root"])
        path = (context.get("source_paths") or ["."])[0]
        res = run_python_script(
            "audit_beauty.py",
            ["--path", path],
            cwd=root,
            timeout=90,
        )
        if res.returncode == 127:
            return CheckResult(
                self.id, "skipped", "major", self.category, "audit_beauty.py missing"
            )
        # exit 2 = below floor, 1 = needs polish, 0 = pass
        status = "passed"
        severity = "advice"
        if res.returncode == 2:
            status, severity = "failed", "blocking"
        elif res.returncode == 1:
            status, severity = "warned", "major"
        findings = []
        if res.returncode != 0:
            findings.append(
                Finding(
                    "BEAUTY",
                    path,
                    (res.stdout or "")[:400],
                    "Beauty score below threshold",
                    "Raise craft — see beauty-gestures.md and audit_beauty output",
                    severity=severity,
                )
            )
        return CheckResult(
            self.id,
            status,
            severity if status != "passed" else "advice",
            self.category,
            "Beauty score acceptable" if status == "passed" else "Beauty needs work",
            findings,
            {"returncode": res.returncode},
        )
