"""Bridge: visual_audit.py (rendered DOM + screenshots)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from wde.checks.base import Check, CheckResult, Finding
from wde.runners.browser_runner import probe_url, run_visual_audit


class VisualAuditBrowserCheck(Check):
    id = "visual.audit"
    version = "1.0.0"
    category = "functional_quality"
    default_severity = "blocking"
    required_capabilities = ["browser"]

    def run(self, context: dict[str, Any]) -> CheckResult:
        url = context.get("local_url") or context.get("url")
        root = Path(context["root"])
        if not url:
            return CheckResult(
                self.id,
                "skipped",
                "blocking",
                self.category,
                "No URL — set project.local_url or --url",
            )

        probe = probe_url(str(url))
        if not probe.ok:
            return CheckResult(
                self.id,
                "failed",
                "blocking",
                self.category,
                f"URL not reachable: {url}",
                [
                    Finding(
                        "URL-DOWN",
                        str(url),
                        probe.error or f"status={probe.status}",
                        "Dev server not responding",
                        "Start the app (npm run dev) then re-run wde run browser",
                    )
                ],
                {"probe": {"status": probe.status, "error": probe.error}},
            )

        out = root / "audit-results"
        result = run_visual_audit(root=root, url=str(url), output=out)
        findings: list[Finding] = []
        report = result.get("report") or {}
        slop = (report.get("ai_slop_detected") or []) + (report.get("a_group_slop") or [])
        for item in slop[:20]:
            findings.append(
                Finding(
                    "RENDER-SLOP",
                    str(url),
                    str(item)[:300],
                    "AI slop in rendered DOM",
                    "Fix rendered markup then re-run visual audit",
                )
            )
        if not result.get("ok") and not findings:
            findings.append(
                Finding(
                    "VISUAL-EXIT",
                    str(url),
                    (result.get("stderr") or result.get("stdout") or "")[:400],
                    "visual_audit.py failed",
                    "Install Playwright; ensure URL loads; re-run",
                )
            )

        artifacts = []
        if result.get("report_path"):
            artifacts.append(result["report_path"])
        shots = report.get("screenshots") or {}
        if isinstance(shots, dict):
            artifacts.extend(str(v) for v in shots.values() if v)

        passed = bool(result.get("ok")) and not findings
        return CheckResult(
            self.id,
            "passed" if passed else "failed",
            self.default_severity,
            self.category,
            "Rendered audit clean" if passed else f"Visual audit issues ({len(findings)})",
            findings,
            {"returncode": result.get("returncode"), "url": url},
            artifacts=artifacts,
        )
