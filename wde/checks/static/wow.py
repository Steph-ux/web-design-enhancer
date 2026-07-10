"""Bridge: scripts/audit_wow.py (opt-in deliberate excess)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from wde.checks.base import Check, CheckResult, Finding
from wde.runners.subprocess_runner import run_python_script


class WowStaticCheck(Check):
    id = "wow.excess"
    version = "1.0.0"
    category = "taste_preference"
    default_severity = "major"

    def run(self, context: dict[str, Any]) -> CheckResult:
        root = Path(context["root"])
        code = (context.get("source_paths") or ["."])[0]
        args = ["--code", code]
        if (root / "DESIGN.md").is_file():
            args += ["--design", "DESIGN.md"]
        if (root / "CREATIVE-BRIEF.md").is_file():
            args += ["--brief", "CREATIVE-BRIEF.md"]
        res = run_python_script("audit_wow.py", args, cwd=root, timeout=90)
        if res.returncode == 127:
            return CheckResult(
                self.id, "skipped", "major", self.category, "audit_wow.py missing"
            )
        findings: list[Finding] = []
        # Non-zero = below waouh; not always delivery-blocking (taste)
        if res.returncode != 0:
            findings.append(
                Finding(
                    "WOW",
                    code,
                    (res.stdout or res.stderr)[:400],
                    "Deliberate excess below WOW floor",
                    "Push hero dimension or drop wow profile for restrained products",
                    severity="major",
                )
            )
        status = "passed" if res.returncode == 0 else "warned"
        return CheckResult(
            self.id,
            status,
            "major" if status != "passed" else "advice",
            self.category,
            "WOW excess OK" if status == "passed" else "WOW below target (non-blocking warn)",
            findings,
            {"returncode": res.returncode},
        )
