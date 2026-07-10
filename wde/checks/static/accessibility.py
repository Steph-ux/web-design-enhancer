"""Bridge: scripts/audit_accessibility.py → Check."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from wde.checks.base import Check, CheckResult, Finding
from wde.runners.subprocess_runner import run_python_script


class AccessibilityStaticCheck(Check):
    id = "a11y.static"
    version = "2.0.0"
    category = "accessibility_critical"
    default_severity = "blocking"
    required_capabilities: list[str] = []

    def run(self, context: dict[str, Any]) -> CheckResult:
        root = Path(context["root"])
        sources = context.get("source_paths") or ["."]
        path = sources[0]
        args = ["--path", path, "--json", "--strict"]

        res = run_python_script("audit_accessibility.py", args, cwd=root, timeout=120)
        findings: list[Finding] = []

        if res.returncode == 127:
            return CheckResult(
                check_id=self.id,
                status="skipped",
                severity="blocking",
                category=self.category,
                summary="audit_accessibility.py not found",
                details={"stderr": res.stderr},
            )

        data = res.data
        # print_json may emit a list or object
        issues: list[Any] = []
        if isinstance(data, dict):
            issues = data.get("violations") or data.get("issues") or data.get("findings") or []
        elif isinstance(data, list):
            issues = data

        for item in issues:
            if not isinstance(item, dict):
                # tuple-like dumps
                findings.append(
                    Finding(
                        rule_id="A11Y",
                        location=path,
                        evidence=str(item)[:300],
                        reason="Accessibility issue",
                        fix="See audit_accessibility report",
                    )
                )
                continue
            findings.append(
                Finding(
                    rule_id=str(item.get("code") or item.get("rule") or item.get("id") or "A11Y"),
                    location=str(item.get("file") or item.get("path") or path),
                    evidence=str(item.get("message") or item.get("text") or item)[:300],
                    reason=str(item.get("message") or "WCAG static finding"),
                    fix=str(item.get("fix") or item.get("fix_instruction") or "Fix a11y violation"),
                    severity="blocking",
                )
            )

        if res.returncode != 0 and not findings:
            findings.append(
                Finding(
                    rule_id="A11Y-EXIT",
                    location=path,
                    evidence=(res.stdout or res.stderr)[:400],
                    reason="audit_accessibility exited non-zero",
                    fix="Run: python scripts/audit_accessibility.py --path <src> --json --strict",
                )
            )

        passed = res.returncode == 0 and not findings
        return CheckResult(
            check_id=self.id,
            status="passed" if passed else "failed",
            severity=self.default_severity,
            category=self.category,
            summary=(
                "Static accessibility checks passed"
                if passed
                else f"{len(findings)} accessibility finding(s)"
            ),
            findings=findings,
            details={"returncode": res.returncode},
        )
