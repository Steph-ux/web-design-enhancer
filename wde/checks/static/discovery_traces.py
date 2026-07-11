"""Mechanical check: discovery contract/code/render traces."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from wde.checks.base import Check, CheckResult, Finding
from wde.discovery.traces import run_all_traces


class DiscoveryTracesCheck(Check):
    id = "discovery.traces"
    version = "1.0.0"
    category = "discovery"
    default_severity = "major"

    def applicable(self, context: dict[str, Any]) -> bool:
        root = Path(context.get("root") or ".")
        return (root / ".wde" / "research" / "territories.json").is_file()

    def run(self, context: dict[str, Any]) -> CheckResult:
        root = Path(context.get("root") or ".")
        require_browser = bool(context.get("require_browser"))
        url = context.get("local_url") or context.get("url")
        payload = run_all_traces(
            root, require_browser=require_browser, url=str(url) if url else None
        )
        findings: list[Finding] = []
        for tname, trep in (payload.get("traces") or {}).items():
            for f in trep.get("findings") or []:
                if f.get("ok"):
                    continue
                findings.append(
                    Finding(
                        rule_id=f.get("check") or tname,
                        location=f".wde/discovery/traces.json#{tname}",
                        evidence=f.get("detail") or "",
                        reason=f"Discovery {tname} failed",
                        fix="Align contracts/code with winner territory or re-run wde discover",
                        severity=f.get("severity") or "major",
                    )
                )
        status = "passed" if payload.get("ok") else "failed"
        # code/render deferred without files should not fail overall if contract ok
        ct = (payload.get("traces") or {}).get("contract_trace") or {}
        if ct.get("ok") and not payload.get("ok"):
            # only soft failures
            status = "warned"
        return CheckResult(
            check_id=self.id,
            status=status,
            severity=self.default_severity,
            category=self.category,
            summary=(
                "Discovery traces pass"
                if status == "passed"
                else f"Discovery traces: {len(findings)} issue(s)"
            ),
            findings=findings,
            details=payload,
            artifacts=[".wde/discovery/traces.json", ".wde/discovery/traces-report.txt"],
        )
