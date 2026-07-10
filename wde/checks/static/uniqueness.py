"""Bridge: audit_style_uniqueness.py"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from wde.checks.base import Check, CheckResult, Finding
from wde.runners.subprocess_runner import run_python_script


class UniquenessStaticCheck(Check):
    id = "style.uniqueness"
    version = "1.0.0"
    category = "anti_template_heuristic"
    default_severity = "blocking"

    def run(self, context: dict[str, Any]) -> CheckResult:
        root = Path(context["root"])
        path = (context.get("source_paths") or ["."])[0]
        res = run_python_script(
            "audit_style_uniqueness.py",
            ["--path", path],
            cwd=root,
            timeout=90,
        )
        if res.returncode == 127:
            return CheckResult(
                self.id, "skipped", "blocking", self.category, "audit_style_uniqueness.py missing"
            )
        # 2 = blocked template, 1 = warn, 0 = ok
        if res.returncode == 2:
            status, sev = "failed", "blocking"
        elif res.returncode == 1:
            status, sev = "warned", "major"
        else:
            status, sev = "passed", "advice"
        findings = []
        if res.returncode != 0:
            findings.append(
                Finding(
                    "TEMPLATE",
                    path,
                    (res.stdout or "")[:400],
                    "Generic AI template signals elevated",
                    "Differentiate structure/colour/type — see design-archetypes",
                    severity=sev,
                )
            )
        return CheckResult(
            self.id,
            status,
            sev if status != "passed" else "advice",
            self.category,
            "Style uniqueness OK" if status == "passed" else "Template risk",
            findings,
            {"returncode": res.returncode},
        )
