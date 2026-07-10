"""Bridge: scripts/audit_layout.py → Check (requires live URL + Playwright)."""

from __future__ import annotations

from typing import Any

from wde.checks.base import Check, CheckResult, Finding
from wde.runners.subprocess_runner import run_python_script


class LayoutBrowserCheck(Check):
    id = "layout.browser"
    version = "1.0.0"
    category = "functional_quality"
    default_severity = "blocking"
    required_capabilities = ["browser"]

    def run(self, context: dict[str, Any]) -> CheckResult:
        url = context.get("local_url") or context.get("url")
        if not url:
            return CheckResult(
                check_id=self.id,
                status="skipped",
                severity="blocking",
                category=self.category,
                summary="No local_url configured — set project.local_url or pass --url",
            )

        root = context["root"]
        res = run_python_script(
            "audit_layout.py",
            ["--url", str(url), "--json"],
            cwd=root,
            timeout=180,
        )

        if res.returncode == 127:
            return CheckResult(
                check_id=self.id,
                status="skipped",
                severity="blocking",
                category=self.category,
                summary="audit_layout.py not found",
            )

        findings: list[Finding] = []
        data = res.data if isinstance(res.data, dict) else {}
        breakpoints = data.get("breakpoints") or {}
        for name, bp in breakpoints.items():
            if not isinstance(bp, dict):
                continue
            for e in bp.get("errors") or []:
                if not isinstance(e, dict):
                    continue
                findings.append(
                    Finding(
                        rule_id=str(e.get("code") or "L?"),
                        location=f"{name}:{url}",
                        evidence=str(e.get("message") or e)[:300],
                        reason="Layout integrity error",
                        fix=str(e.get("fix") or "Fix overflow / responsive layout"),
                    )
                )

        if res.returncode != 0 and not findings:
            findings.append(
                Finding(
                    rule_id="LAYOUT-EXIT",
                    location=str(url),
                    evidence=(res.stdout or res.stderr)[:400],
                    reason="audit_layout failed (server down or Playwright missing?)",
                    fix="Start dev server; ensure Playwright is installed; re-run with --url",
                )
            )

        # Missing browser capability → degraded rather than fake pass
        caps = context.get("capabilities") or {}
        if not caps.get("browser") and res.returncode != 0:
            return CheckResult(
                check_id=self.id,
                status="degraded",
                severity="major",
                category=self.category,
                summary="Layout browser check unavailable or failed — not a visual pass",
                findings=findings,
                details={"returncode": res.returncode, "degraded": True},
            )

        passed = res.returncode == 0 and not findings
        return CheckResult(
            check_id=self.id,
            status="passed" if passed else "failed",
            severity=self.default_severity,
            category=self.category,
            summary=(
                "Layout integrity OK on measured breakpoints"
                if passed
                else f"{len(findings)} layout error(s)"
            ),
            findings=findings,
            details={"returncode": res.returncode, "url": url},
        )
