"""Human-readable check report."""

from __future__ import annotations

from wde.checks.base import CheckResult


def print_results(results: list[CheckResult]) -> None:
    for r in results:
        icon = {
            "passed": "OK",
            "failed": "FAIL",
            "warned": "WARN",
            "skipped": "SKIP",
            "degraded": "DEGRADED",
        }.get(r.status, r.status.upper())
        print(f"[{icon}] {r.check_id} — {r.summary}")
        for f in r.findings[:8]:
            print(f"    - [{f.rule_id}] {f.location}: {f.reason}")
            if f.fix:
                print(f"      fix: {f.fix[:160]}")
        if len(r.findings) > 8:
            print(f"    … +{len(r.findings) - 8} more")
