"""Bridge: scripts/diff_design_vs_code.py"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from wde.checks.base import Check, CheckResult, Finding
from wde.runners.subprocess_runner import run_python_script


class DesignDiffStaticCheck(Check):
    id = "design.diff"
    version = "1.0.0"
    category = "brand_contract"
    default_severity = "blocking"

    def run(self, context: dict[str, Any]) -> CheckResult:
        root = Path(context["root"])
        code = (context.get("source_paths") or ["."])[0]
        if not (root / "DESIGN.md").is_file():
            return CheckResult(
                self.id,
                "skipped",
                "major",
                self.category,
                "DESIGN.md missing — design.diff not applicable",
            )
        res = run_python_script(
            "diff_design_vs_code.py",
            ["DESIGN.md", "--code", code],
            cwd=root,
            timeout=120,
        )
        if res.returncode == 127:
            return CheckResult(
                self.id, "skipped", "blocking", self.category, "diff_design_vs_code.py missing"
            )
        findings: list[Finding] = []
        if res.returncode != 0:
            findings.append(
                Finding(
                    "DIFF",
                    code,
                    (res.stdout or res.stderr)[:500],
                    "Code diverges from DESIGN.md tokens",
                    "Align colors/fonts/motion with DESIGN.md or update contract",
                )
            )
        return CheckResult(
            self.id,
            "passed" if res.returncode == 0 else "failed",
            self.default_severity,
            self.category,
            "DESIGN.md ↔ code aligned" if res.returncode == 0 else "DESIGN.md ↔ code mismatch",
            findings,
            {"returncode": res.returncode},
        )
