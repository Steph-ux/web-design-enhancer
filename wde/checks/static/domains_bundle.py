"""Domain bundle check — forms, states, i18n, performance, maintainability."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from wde.checks.base import Check, CheckResult, Finding
from wde.domains.forms import audit_forms
from wde.domains.i18n import audit_i18n
from wde.domains.maintainability import audit_maintainability
from wde.domains.performance import audit_performance
from wde.domains.states import audit_interaction_states


class DomainsBundleCheck(Check):
    id = "domains.bundle"
    version = "1.0.0"
    category = "functional_quality"
    default_severity = "major"

    def run(self, context: dict[str, Any]) -> CheckResult:
        root = Path(context["root"])
        forms = audit_forms(root)
        i18n = audit_i18n(root)
        states = audit_interaction_states(root)
        perf = audit_performance(root)
        maint = audit_maintainability(root)
        findings: list[Finding] = []
        if forms.get("inputs", 0) and not forms.get("labels_ok"):
            findings.append(
                Finding(
                    "FORMS-LABEL",
                    "forms",
                    str(forms.get("issues", [])[:3]),
                    "Inputs without labels",
                    "Add label/for or aria-label",
                    severity="blocking",
                )
            )
        if not i18n.get("lang_ok"):
            findings.append(
                Finding(
                    "I18N-LANG",
                    "html",
                    "missing lang",
                    "html lang attribute missing",
                    "Add lang on <html>",
                    severity="major",
                )
            )
        if not perf.get("within_simple_budget"):
            findings.append(
                Finding(
                    "PERF-BUDGET",
                    "assets",
                    str(perf.get("large_images_over_500kb")),
                    "Lab asset budget warning",
                    "Compress images / reduce tracked bytes",
                    severity="major",
                )
            )
        if maint.get("large_files_over_800_lines"):
            findings.append(
                Finding(
                    "MAINT-SIZE",
                    "source",
                    str(maint.get("large_files_over_800_lines")[:2]),
                    "Very large source files",
                    "Split modules for maintainability",
                    severity="advice",
                )
            )
        blocking = [f for f in findings if f.severity == "blocking"]
        status = "failed" if blocking else ("warned" if findings else "passed")
        return CheckResult(
            self.id,
            status,
            "blocking" if blocking else "major",
            self.category,
            "Domain bundle OK" if status == "passed" else f"Domain findings: {len(findings)}",
            findings,
            {
                "forms": forms,
                "i18n": i18n,
                "states": states,
                "performance": perf,
                "maintainability": maint,
            },
        )
