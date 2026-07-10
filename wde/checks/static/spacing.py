"""Bridge: audit_spacing.py"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from wde.checks.base import Check, CheckResult, Finding
from wde.runners.subprocess_runner import run_python_script


class SpacingStaticCheck(Check):
    id = "spacing.grid"
    version = "1.0.0"
    category = "functional_quality"
    default_severity = "blocking"

    def run(self, context: dict[str, Any]) -> CheckResult:
        root = Path(context["root"])
        path = (context.get("source_paths") or ["."])[0]
        res = run_python_script(
            "audit_spacing.py",
            ["--path", path],
            cwd=root,
            timeout=90,
        )
        if res.returncode == 127:
            return CheckResult(
                self.id, "skipped", "blocking", self.category, "audit_spacing.py missing"
            )
        findings: list[Finding] = []
        if res.returncode != 0:
            findings.append(
                Finding(
                    "SPACE",
                    path,
                    (res.stdout or res.stderr)[:400],
                    "8px grid / spacing violations",
                    "Align spacing to 8px scale (see audit_spacing output)",
                )
            )
        return CheckResult(
            self.id,
            "passed" if res.returncode == 0 else "failed",
            self.default_severity,
            self.category,
            "Spacing OK" if res.returncode == 0 else "Spacing violations",
            findings,
            {"returncode": res.returncode},
        )
