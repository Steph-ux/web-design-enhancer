"""Structural validators for V3 contracts — used by `wde validate *`."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ValidationIssue:
    code: str
    message: str
    severity: str = "blocking"  # blocking | warn
    remediation: str = ""


@dataclass
class ValidationReport:
    target: str
    ok: bool
    issues: list[ValidationIssue] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "target": self.target,
            "ok": self.ok,
            "issues": [
                {
                    "code": i.code,
                    "message": i.message,
                    "severity": i.severity,
                    "remediation": i.remediation,
                }
                for i in self.issues
            ],
        }


def _section(md: str, title: str) -> str:
    pat = re.compile(
        rf"^##\s+{re.escape(title)}\s*$([\s\S]*?)(?=^##\s+|\Z)",
        re.M | re.I,
    )
    m = pat.search(md)
    return (m.group(1) if m else "").strip()


def _filled(text: str) -> bool:
    t = text.strip()
    if not t or t in {"___", "…", "..."}:
        return False
    if re.fullmatch(r"[_….\-\s]+", t):
        return False
    return len(t) >= 3


def validate_intent(root: Path) -> ValidationReport:
    path = root / "CREATIVE-BRIEF.md"
    issues: list[ValidationIssue] = []
    if not path.is_file():
        return ValidationReport(
            "intent",
            False,
            [
                ValidationIssue(
                    "missing_brief",
                    "CREATIVE-BRIEF.md missing",
                    remediation="Copy templates/creative-brief-template.md",
                )
            ],
        )
    md = path.read_text(encoding="utf-8", errors="replace")
    required = [
        "Emotional Intent",
        "The One Unexpected Thing",
        "Hero Dimension",
        "The Broken Rule",
        "Design Read",
        "Design Dials",
        "The Cross-Domain Steal",
    ]
    for title in required:
        body = _section(md, title)
        if not body:
            issues.append(
                ValidationIssue(
                    "missing_section",
                    f"Section missing: {title}",
                    remediation=f"Add ## {title}",
                )
            )
            continue
        if title == "Hero Dimension":
            if not re.search(r"\[[xX]\]", body):
                issues.append(
                    ValidationIssue(
                        "hero_unticked",
                        "Hero Dimension needs exactly one [x] box",
                        remediation="Tick one dimension",
                    )
                )
            elif len(re.findall(r"\[[xX]\]", body)) > 1:
                issues.append(
                    ValidationIssue(
                        "hero_multiple",
                        "Hero Dimension has multiple [x] — pick exactly one",
                    )
                )
        elif title == "The Broken Rule":
            if not _filled(body):
                issues.append(ValidationIssue("unfilled", f"{title} unfilled"))
            elif "because" not in body.lower():
                issues.append(
                    ValidationIssue(
                        "broken_no_because",
                        "Broken Rule must include 'because'",
                    )
                )
        elif title == "Design Dials":
            for dial in ("VARIANCE", "MOTION", "DENSITY"):
                if not re.search(rf"{dial}\s*:\s*\d{{1,2}}", body, re.I):
                    issues.append(
                        ValidationIssue(
                            "dial_missing",
                            f"Design Dials missing {dial}: N (1-10)",
                        )
                    )
        elif not _filled(body):
            issues.append(ValidationIssue("unfilled", f"{title} unfilled or placeholder"))

    # Prefer V2 audit_brief if available
    brief_script = Path(__file__).resolve().parents[2] / "scripts" / "audit_brief.py"
    if brief_script.is_file() and path.is_file():
        from wde.runners.subprocess_runner import run_python_script

        res = run_python_script(
            "audit_brief.py",
            ["--brief", str(path)],
            cwd=root,
            timeout=60,
        )
        if res.returncode == 1:
            issues.append(
                ValidationIssue(
                    "brief_quality",
                    "audit_brief.py blocked (below quality floor)",
                    remediation="Sharpen Emotional Intent / steal / dials — see audit_brief output",
                )
            )

    blocking = [i for i in issues if i.severity == "blocking"]
    return ValidationReport("intent", len(blocking) == 0, issues)


def validate_experience(root: Path) -> ValidationReport:
    path = root / "EXPERIENCE-CONTRACT.md"
    issues: list[ValidationIssue] = []
    if not path.is_file():
        return ValidationReport(
            "experience",
            False,
            [
                ValidationIssue(
                    "missing_experience",
                    "EXPERIENCE-CONTRACT.md missing",
                    remediation="Copy templates/experience-contract-template.md",
                )
            ],
        )
    md = path.read_text(encoding="utf-8", errors="replace")
    for title in (
        "Product goal",
        "Pages & objectives",
        "Critical journeys",
        "Navigation",
        "Interaction states",
        "Responsive behaviour",
        "Accessibility requirements",
        "Content & data policy",
        "Acceptance criteria",
    ):
        body = _section(md, title)
        if not body or not _filled(body.replace("|", " ").replace("-", " ")):
            issues.append(
                ValidationIssue(
                    "experience_section",
                    f"EXPERIENCE-CONTRACT section weak/missing: {title}",
                    remediation=f"Fill ## {title} with concrete UX decisions",
                )
            )
    if re.search(r"\b(lorem ipsum|50,?000 users|99\.9%|fake testimonial)\b", md, re.I):
        issues.append(
            ValidationIssue(
                "truth",
                "Experience contract contains forbidden invented social-proof patterns",
                severity="blocking",
                remediation="Remove invented metrics/testimonials",
            )
        )
    blocking = [i for i in issues if i.severity == "blocking"]
    return ValidationReport("experience", len(blocking) == 0, issues)


def validate_design(root: Path) -> ValidationReport:
    path = root / "DESIGN.md"
    issues: list[ValidationIssue] = []
    if not path.is_file():
        return ValidationReport(
            "design",
            False,
            [
                ValidationIssue(
                    "missing_design",
                    "DESIGN.md missing",
                    remediation="Create from templates/design-md-template.md",
                )
            ],
        )
    md = path.read_text(encoding="utf-8", errors="replace")
    if "## 0. Sources Phase 0" not in md and "Sources Phase 0" not in md:
        issues.append(
            ValidationIssue(
                "no_sources",
                "DESIGN.md missing Phase 0 sources section",
                remediation="Document search.py + getdesign commands and artifacts",
            )
        )
    # Prefer V2 validate_design.py
    from wde.runners.subprocess_runner import run_python_script

    res = run_python_script("validate_design.py", ["DESIGN.md"], cwd=root, timeout=90)
    if res.returncode == 127:
        issues.append(
            ValidationIssue(
                "no_validator",
                "validate_design.py not found — structural section checks only",
                severity="warn",
            )
        )
    elif res.returncode != 0:
        issues.append(
            ValidationIssue(
                "validate_design",
                "validate_design.py failed",
                remediation=(res.stdout or res.stderr)[:500] or "Fix DESIGN.md contract",
            )
        )
    blocking = [i for i in issues if i.severity == "blocking"]
    return ValidationReport("design", len(blocking) == 0, issues)


def validate_lock(root: Path) -> ValidationReport:
    candidates = [root / "STRUCTURAL-LOCK.md", root / "structural-lock.md"]
    path = next((p for p in candidates if p.is_file()), None)
    issues: list[ValidationIssue] = []
    if not path:
        return ValidationReport(
            "lock",
            False,
            [
                ValidationIssue(
                    "missing_lock",
                    "STRUCTURAL-LOCK.md / structural-lock.md missing",
                    remediation="Write ≥3 numbered structural decisions",
                )
            ],
        )
    md = path.read_text(encoding="utf-8", errors="replace")
    numbered = re.findall(r"^\s*\d+\.", md, re.M)
    if len(numbered) < 3:
        issues.append(
            ValidationIssue(
                "lock_count",
                f"Only {len(numbered)} numbered decision(s) — need ≥3",
            )
        )
    if re.search(r"\[(?:Ex:|[A-Z]\s*\|)", md):
        issues.append(ValidationIssue("lock_placeholder", "Lock still has placeholders"))
    blocking = [i for i in issues if i.severity == "blocking"]
    return ValidationReport("lock", len(blocking) == 0, issues)


def apply_validation_transition(ctx, target: str, report: ValidationReport) -> None:
    """Advance state machine when validation passes."""
    from wde.core.evidence import Evidence, write_evidence
    from wde.core.state_machine import apply_transition

    state = ctx.refresh_invalidation()
    if not report.ok:
        state["blockers"] = [
            {"code": i.code, "message": i.message, "remediation": i.remediation}
            for i in report.issues
            if i.severity == "blocking"
        ]
        ctx.save_state(state)
        return

    hashes = state.get("hashes") or {}
    ev = Evidence(
        check_id=f"contract.{target}",
        status="passed",
        executor="wde-core",
        source_hash=hashes.get("SOURCE", ""),
        contract_hash=hashes.get("DESIGN", "") or hashes.get("CREATIVE_BRIEF", ""),
        details=report.to_dict(),
        rule_category="brand_contract" if target in {"design", "lock"} else "user_requirement",
    )
    path = write_evidence(ctx.wde / "evidence", ev)
    state.setdefault("valid_checks", {})[ev.check_id] = str(path.relative_to(ctx.root)).replace(
        "\\", "/"
    )

    phase = state.get("phase")
    try:
        if target == "intent" and phase == "INTENT_REQUIRED":
            state = apply_transition(state, "INTENT_VALIDATED")
            state = apply_transition(state, "RESEARCH_REQUIRED")
        elif target == "experience" and phase in {
            "RESEARCH_VALIDATED",
            "ARCHITECTURE_REQUIRED",
            "INTENT_VALIDATED",
            "RESEARCH_REQUIRED",
        }:
            # Allow experience after research; if still early, jump carefully
            if phase == "RESEARCH_REQUIRED":
                # research not validated — only record evidence
                pass
            elif phase == "RESEARCH_VALIDATED":
                state = apply_transition(state, "ARCHITECTURE_REQUIRED")
                state = apply_transition(state, "ARCHITECTURE_VALIDATED")
            elif phase == "ARCHITECTURE_REQUIRED":
                state = apply_transition(state, "ARCHITECTURE_VALIDATED")
        elif target == "design" and phase in {
            "ARCHITECTURE_VALIDATED",
            "CONTRACT_REQUIRED",
            "CONTRACT_VALIDATED",
        }:
            if phase == "ARCHITECTURE_VALIDATED":
                state = apply_transition(state, "CONTRACT_REQUIRED")
            # stay CONTRACT_REQUIRED until lock also ok — design alone partial
        elif target == "lock" and phase in {"CONTRACT_REQUIRED", "CONTRACT_VALIDATED"}:
            if phase == "CONTRACT_REQUIRED":
                # need design evidence too ideally
                has_design = "contract.design" in (state.get("valid_checks") or {})
                if has_design:
                    state = apply_transition(state, "CONTRACT_VALIDATED")
                    state = apply_transition(state, "IMPLEMENTATION_ALLOWED")
        elif target == "design" and phase == "CONTRACT_REQUIRED":
            has_lock = "contract.lock" in (state.get("valid_checks") or {})
            if has_lock:
                state = apply_transition(state, "CONTRACT_VALIDATED")
                state = apply_transition(state, "IMPLEMENTATION_ALLOWED")
    except ValueError:
        pass

    # lock check id
    if target == "lock":
        state.setdefault("valid_checks", {})["contract.lock"] = state["valid_checks"].get(
            ev.check_id, ""
        )

    state["blockers"] = []
    ctx.save_state(state)
