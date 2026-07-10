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


def validate_research(root: Path) -> ValidationReport:
    """Prove Phase 0 pillars left real artifacts OR discovery receipts with digests."""
    issues: list[ValidationIssue] = []
    pro_max_hits = [
        root / "design-system-output.md",
        *root.glob("design-system/**/MASTER.md"),
        *root.glob("**/design-system-output.md"),
    ]
    getdesign_hits = [
        *root.glob("getdesign-*.md"),
        *root.glob("**/getdesign-*.md"),
        root / "bugatti" / "DESIGN.md",
    ]
    brand_designs = [
        p
        for p in root.glob("*/DESIGN.md")
        if p.parent.name not in {".wde", "templates", "references", "examples"}
    ]
    design_md = root / "DESIGN.md"
    has_pro = any(p.is_file() for p in pro_max_hits)
    has_gd = any(p.is_file() for p in getdesign_hits) or any(p.is_file() for p in brand_designs)
    phase0_ok = False
    if design_md.is_file():
        text = design_md.read_text(encoding="utf-8", errors="replace")
        phase0_ok = (
            "Sources Phase 0" in text
            or "0a." in text
            or "getdesign" in text.lower()
            or "design-system" in text.lower()
            or "Creative Discovery" in text
            or "wde/research" in text
            or ".wde/research" in text
        )

    # Discovery receipts path (Creative Discovery orchestrator)
    from wde.discovery.receipts import discovery_receipts_satisfy_research

    discovery_ok, discovery_problems = discovery_receipts_satisfy_research(root)

    if discovery_ok:
        # Receipts stand in for classic pillar files when digests + success exist
        blocking = [i for i in issues if i.severity == "blocking"]
        return ValidationReport("research", len(blocking) == 0, issues)

    if not has_pro and not phase0_ok:
        issues.append(
            ValidationIssue(
                "research_promax",
                "Missing Pro Max / design-system artifact (design-system-output.md or design-system/**/MASTER.md)",
                remediation="wde discover --request \"…\"  OR  python scripts/search.py \"…\" --design-system -p <name> --persist",
            )
        )
    if not has_gd and not phase0_ok and not discovery_ok:
        issues.append(
            ValidationIssue(
                "research_getdesign",
                "Missing getdesign visual reference artifact (or discovery receipts)",
                remediation="wde discover --request \"…\"  OR  npx getdesign@latest add <brand>",
            )
        )
    if not has_pro and not has_gd and not phase0_ok and not discovery_ok:
        issues.append(
            ValidationIssue(
                "research_empty",
                "No research pillars or discovery receipts — cannot validate research",
                remediation="wde discover --request \"…\" then re-run validate research",
            )
        )
        if discovery_problems:
            issues.append(
                ValidationIssue(
                    "research_receipts",
                    "Discovery receipts incomplete: " + "; ".join(discovery_problems),
                    remediation="Re-run wde discover so .wde/research/ has ≥2 valid digests",
                )
            )
    if phase0_ok and not has_pro and not has_gd and not discovery_ok:
        issues.append(
            ValidationIssue(
                "research_docs_only",
                "DESIGN.md mentions sources but no on-disk pillar artifacts or receipts found",
                severity="blocking",
                remediation="wde discover or persist design-system-output.md / getdesign",
            )
        )

    blocking = [i for i in issues if i.severity == "blocking"]
    return ValidationReport("research", len(blocking) == 0, issues)


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
        elif target == "research" and phase in {"RESEARCH_REQUIRED", "INTENT_VALIDATED"}:
            if phase == "INTENT_VALIDATED":
                state = apply_transition(state, "RESEARCH_REQUIRED")
            state = apply_transition(state, "RESEARCH_VALIDATED")
            state = apply_transition(state, "ARCHITECTURE_REQUIRED")
        elif target in {"experience", "architecture"} and phase in {
            "RESEARCH_VALIDATED",
            "ARCHITECTURE_REQUIRED",
        }:
            if phase == "RESEARCH_VALIDATED":
                state = apply_transition(state, "ARCHITECTURE_REQUIRED")
            state = apply_transition(state, "ARCHITECTURE_VALIDATED")
            state = apply_transition(state, "CONTRACT_REQUIRED")
        elif target == "design" and phase in {
            "ARCHITECTURE_VALIDATED",
            "CONTRACT_REQUIRED",
            "CONTRACT_VALIDATED",
        }:
            if phase == "ARCHITECTURE_VALIDATED":
                state = apply_transition(state, "CONTRACT_REQUIRED")
            # stay CONTRACT_REQUIRED until lock also ok — design alone partial
            if "contract.lock" in (state.get("valid_checks") or {}):
                state = apply_transition(state, "CONTRACT_VALIDATED")
                state = apply_transition(state, "IMPLEMENTATION_ALLOWED")
            else:
                na = {
                    "id": "lock_next",
                    "summary": "DESIGN.md OK — validate structural lock next",
                    "command": "wde validate lock",
                    "allowed_writer": "agent",
                }
                state["next_action"] = na
        elif target == "lock" and phase in {"CONTRACT_REQUIRED", "CONTRACT_VALIDATED"}:
            if phase == "CONTRACT_REQUIRED":
                has_design = "contract.design" in (state.get("valid_checks") or {})
                if has_design:
                    state = apply_transition(state, "CONTRACT_VALIDATED")
                    state = apply_transition(state, "IMPLEMENTATION_ALLOWED")
                else:
                    state["blockers"] = [
                        {
                            "code": "design_first",
                            "message": "Validate design before lock can unlock implementation",
                            "remediation": "wde validate design",
                        }
                    ]
                    ctx.save_state(state)
                    return
    except ValueError:
        pass

    # Alias check ids for lock
    if target == "lock":
        state.setdefault("valid_checks", {})["contract.lock"] = state["valid_checks"].get(
            ev.check_id, ""
        )
    if target == "research":
        state.setdefault("valid_checks", {})["contract.research"] = state["valid_checks"].get(
            ev.check_id, ""
        )

    if not state.get("blockers"):
        state["blockers"] = []
    ctx.save_state(state)
