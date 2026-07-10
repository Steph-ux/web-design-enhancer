"""Bridge: scripts/detect_ai_slop.py → Check."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from wde.checks.base import Check, CheckResult, Finding
from wde.runners.subprocess_runner import run_python_script


class SlopStaticCheck(Check):
    id = "slop.static"
    version = "2.1.0"
    category = "safety_truth"
    default_severity = "blocking"
    required_capabilities: list[str] = []

    def run(self, context: dict[str, Any]) -> CheckResult:
        root = Path(context["root"])
        sources = context.get("source_paths") or ["."]
        code = sources[0]
        design = root / "DESIGN.md"
        args = ["--code", code, "--json"]
        if design.is_file():
            args = ["--design", "DESIGN.md", *args]

        res = run_python_script("detect_ai_slop.py", args, cwd=root, timeout=180)
        findings: list[Finding] = []

        if res.returncode == 127:
            return CheckResult(
                check_id=self.id,
                status="skipped",
                severity="blocking",
                category=self.category,
                summary="detect_ai_slop.py not found in skill scripts/",
                details={"stderr": res.stderr},
            )

        data = res.data if isinstance(res.data, dict) else {}
        violations = data.get("violations") or data.get("findings") or []
        if isinstance(violations, list):
            for v in violations:
                if not isinstance(v, dict):
                    continue
                findings.append(
                    Finding(
                        rule_id=str(v.get("type") or v.get("rule") or "SLOP"),
                        location=str(v.get("file") or v.get("path") or code),
                        evidence=str(v.get("message") or v.get("match") or "")[:300],
                        reason=str(v.get("message") or "AI slop pattern"),
                        fix=str(v.get("fix_instruction") or v.get("fix") or "See detect_ai_slop fix_instruction"),
                        severity="blocking",
                    )
                )

        # Fallback: non-zero exit without parseable JSON
        if res.returncode != 0 and not findings:
            findings.append(
                Finding(
                    rule_id="SLOP-EXIT",
                    location=code,
                    evidence=(res.stdout or res.stderr)[:400],
                    reason="detect_ai_slop exited non-zero",
                    fix="Run: python scripts/detect_ai_slop.py --design DESIGN.md --code <src> --json",
                )
            )

        passed = res.returncode == 0 and not findings
        # Some detectors return 0 with violations in JSON
        if data.get("passed") is False:
            passed = False
        if data.get("passed") is True and not findings:
            passed = True

        return CheckResult(
            check_id=self.id,
            status="passed" if passed else "failed",
            severity=self.default_severity,
            category=self.category,
            summary=(
                "No AI-slop patterns detected"
                if passed
                else f"{len(findings)} AI-slop finding(s)"
            ),
            findings=findings,
            details={
                "returncode": res.returncode,
                "raw_keys": list(data.keys()) if isinstance(data, dict) else [],
            },
        )
