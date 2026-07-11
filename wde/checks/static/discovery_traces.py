"""Mechanical check: discovery contract/code/render traces (phase-aware)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from wde.checks.base import Check, CheckResult, Finding
from wde.discovery.traces import run_all_traces


def _has_frontend_files(root: Path) -> bool:
    exts = {".html", ".css", ".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte"}
    skip = {".wde", "node_modules", ".git", "tests", "wde", "scripts", "references", "data"}
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in skip for part in p.parts):
            continue
        if p.suffix.lower() in exts:
            return True
    return False


class DiscoveryTracesCheck(Check):
    id = "discovery.traces"
    version = "1.1.0"
    category = "discovery"
    default_severity = "major"

    def applicable(self, context: dict[str, Any]) -> bool:
        root = Path(context.get("root") or ".")
        return (root / ".wde" / "research" / "territories.json").is_file()

    def run(self, context: dict[str, Any]) -> CheckResult:
        root = Path(context.get("root") or ".")
        profile = str(context.get("profile") or "")
        require_browser = bool(context.get("require_browser")) or profile in {
            "deliver",
            "full",
            "browser",
            "visual",
        }
        # After frontend exists, code failures are blocking
        has_fe = _has_frontend_files(root)
        url = context.get("local_url") or context.get("url")
        payload = run_all_traces(
            root, require_browser=require_browser and bool(url or has_fe), url=str(url) if url else None
        )

        findings: list[Finding] = []
        traces = payload.get("traces") or {}
        ct = traces.get("contract_trace") or {}
        code = traces.get("code_trace") or {}
        rend = traces.get("render_trace") or {}

        def absorb(tname: str, trep: dict[str, Any], *, elevate: bool) -> None:
            for f in trep.get("findings") or []:
                if f.get("ok"):
                    continue
                sev = f.get("severity") or "major"
                # Deferred advice stays advice
                if f.get("check") in {"code.absent", "render.no_evidence", "render.playwright_unavailable"}:
                    if not elevate:
                        sev = "advice"
                    elif require_browser or (tname == "code_trace" and has_fe):
                        sev = "blocking" if tname == "code_trace" and has_fe else sev
                elif elevate and sev == "major":
                    sev = "blocking"
                findings.append(
                    Finding(
                        rule_id=f.get("check") or tname,
                        location=f".wde/discovery/traces.json#{tname}",
                        evidence=f.get("detail") or "",
                        reason=f"Discovery {tname} failed",
                        fix="Align contracts/code with winner territory or re-run wde discover / implement signature contract",
                        severity=sev,
                    )
                )

        absorb("contract_trace", ct, elevate=True)
        absorb("code_trace", code, elevate=has_fe)
        absorb(
            "render_trace",
            rend,
            elevate=require_browser or profile in {"deliver", "full"},
        )

        blocking = [f for f in findings if f.severity == "blocking"]
        majors = [f for f in findings if f.severity == "major"]

        if not ct.get("ok"):
            status = "failed"
        elif has_fe and not code.get("ok"):
            status = "failed"
        elif require_browser and not rend.get("ok"):
            status = "failed"
        elif blocking:
            status = "failed"
        elif majors:
            status = "warned"
        else:
            status = "passed"

        # Explicit: without browser on deliver, do not pretend visual READY
        caps = context.get("capabilities") or {}
        if profile == "deliver" and not caps.get("browser") and not url:
            findings.append(
                Finding(
                    rule_id="render.undeclared",
                    location="deliver-check",
                    evidence="No browser capability / URL — visual delivery unverified",
                    reason="Cannot authorize READY without render verification",
                    fix="Pass --url and ensure Playwright, or mark visual gate open",
                    severity="blocking",
                )
            )
            status = "failed"

        return CheckResult(
            check_id=self.id,
            status=status,
            severity=self.default_severity,
            category=self.category,
            summary=(
                "Discovery traces pass"
                if status == "passed"
                else f"Discovery traces: {status} ({len(findings)} issue(s))"
            ),
            findings=findings,
            details={
                **payload,
                "phase": {
                    "has_frontend": has_fe,
                    "require_browser": require_browser,
                    "profile": profile,
                },
            },
            artifacts=[".wde/discovery/traces.json", ".wde/discovery/traces-report.txt"],
        )
