"""Bridge: audit_gestures.py"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from wde.checks.base import Check, CheckResult, Finding
from wde.runners.subprocess_runner import run_python_script


class GesturesStaticCheck(Check):
    id = "gestures.archetype"
    version = "1.0.0"
    category = "brand_contract"
    default_severity = "blocking"

    def run(self, context: dict[str, Any]) -> CheckResult:
        root = Path(context["root"])
        code = (context.get("source_paths") or ["."])[0]
        args = ["--code", code]
        if (root / "DESIGN.md").is_file():
            args += ["--design", "DESIGN.md"]
        res = run_python_script("audit_gestures.py", args, cwd=root, timeout=90)
        if res.returncode == 127:
            return CheckResult(
                self.id, "skipped", "blocking", self.category, "audit_gestures.py missing"
            )
        findings = []
        if res.returncode != 0:
            findings.append(
                Finding(
                    "GESTURE",
                    code,
                    (res.stdout or res.stderr)[:400],
                    "Archetype signature gestures missing in code",
                    "Implement gestures from beauty-gestures.md",
                )
            )
        return CheckResult(
            self.id,
            "passed" if res.returncode == 0 else "failed",
            self.default_severity,
            self.category,
            "Signature gestures present" if res.returncode == 0 else "Gestures missing",
            findings,
            {"returncode": res.returncode},
        )
