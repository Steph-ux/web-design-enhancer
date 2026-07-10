"""Visual review package emission + independence-aware processing."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from wde.checks.base import CheckResult
from wde.checks.registry import get_registry
from wde.core.evidence import Evidence, write_evidence
from wde.core.project_context import ProjectContext
from wde.core.runner import run_checks
from wde.core.state_machine import apply_transition
from wde.runners.browser_runner import probe_url, run_visual_audit

# Rubric dimensions from plan §8.3
RUBRIC_DIMENSIONS = [
    "intent_fidelity",
    "hierarchy_clarity",
    "visual_coherence",
    "typography_quality",
    "composition",
    "responsive_quality",
    "content_credibility",
    "signature_execution",
    "generic_template_risk",
    "visible_problems",
]


def emit_review_package(
    ctx: ProjectContext,
    *,
    url: str | None = None,
    run_audit: bool = True,
) -> dict[str, Any]:
    """
    Build a judge package (screenshots + contracts summary).
    Does NOT score aesthetics — the judge (agent/human/API) must write the verdict.
    """
    project = ctx.load_project()
    url = url or project.get("local_url") or "http://localhost:5173"
    audit_dir = ctx.root / "audit-results"
    package_dir = ctx.wde / "reports" / "review-package"
    package_dir.mkdir(parents=True, exist_ok=True)

    probe = probe_url(url)
    audit_summary: dict[str, Any] = {"skipped": True}
    if run_audit and probe.ok:
        audit_summary = run_visual_audit(root=ctx.root, url=url, output=audit_dir)
        audit_summary["skipped"] = False
    elif not probe.ok:
        audit_summary = {
            "skipped": False,
            "ok": False,
            "error": f"URL unreachable: {url}",
            "probe": {"status": probe.status, "error": probe.error},
        }

    def _read(name: str, limit: int = 4000) -> str:
        p = ctx.root / name
        if not p.is_file():
            return ""
        text = p.read_text(encoding="utf-8", errors="replace")
        return text[:limit]

    package = {
        "schema_version": "3.0",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "url": url,
        "probe_ok": probe.ok,
        "instructions": {
            "role": "You are an independent design judge. Score skeptically.",
            "do_not": [
                "Read the builder's self-praise or session history",
                "Pre-fill a passing score",
                "Confirm success because the builder asked you to",
            ],
            "must": [
                "Set reviewer to independent-clone | independent | human (never self for delivery)",
                "Provide overall_score 0-100",
                "Provide reads_as: human|ai",
                "Provide memorable_idea (>=8 chars, specific, visible)",
                "Score each dimension with a short evidence string",
            ],
            "output_path": str(audit_dir / "aesthetic-verdict.json"),
        },
        "rubric_dimensions": RUBRIC_DIMENSIONS,
        "contracts": {
            "creative_brief_excerpt": _read("CREATIVE-BRIEF.md", 2500),
            "experience_excerpt": _read("EXPERIENCE-CONTRACT.md", 2500),
            "design_excerpt": _read("DESIGN.md", 3000),
            "structural_lock_excerpt": _read("STRUCTURAL-LOCK.md", 1500)
            or _read("structural-lock.md", 1500),
        },
        "audit": {
            "report_path": audit_summary.get("report_path"),
            "ok": audit_summary.get("ok"),
            "returncode": audit_summary.get("returncode"),
            "error": audit_summary.get("error"),
        },
        "verdict_schema": {
            "reviewer": "independent-clone|independent|human",
            "overall_score": 0,
            "reads_as": "human|ai",
            "memorable_idea": "one owned visible move",
            "dimensions": {
                d: {"score": 0, "evidence": "localized proof"} for d in RUBRIC_DIMENSIONS
            },
            "top_fixes": ["..."],
        },
    }

    path = package_dir / "package.json"
    path.write_text(json.dumps(package, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # Human-readable judge prompt
    prompt_path = package_dir / "JUDGE_PROMPT.md"
    prompt_path.write_text(
        _judge_prompt_md(package),
        encoding="utf-8",
    )
    return {
        "package_path": str(path),
        "prompt_path": str(prompt_path),
        "audit_dir": str(audit_dir),
        "probe_ok": probe.ok,
        "audit_ok": bool(audit_summary.get("ok")),
    }


def _judge_prompt_md(package: dict[str, Any]) -> str:
    return f"""# Independent design review

You are a **context-isolated** judge. You did not build this UI.

## Rules
- Do **not** assume the design is good.
- Score like a skeptical senior reviewer (90+ is rare).
- Every dimension needs **evidence** (what you see).
- Set `reviewer` to `independent-clone` (same model, blank context), `independent` (other model), or `human`.
- **Never** use `reviewer: self` if this verdict will authorize delivery.

## Output
Write JSON to: `{package["instructions"]["output_path"]}`

Required fields: reviewer, overall_score, reads_as, memorable_idea, dimensions (with evidence), top_fixes.

## Rubric dimensions
{chr(10).join(f"- {d}" for d in package["rubric_dimensions"])}

## URL
{package.get("url")}

## Contract excerpts
See package.json `contracts` keys for brief / experience / design / lock excerpts.
"""


def process_review(
    ctx: ProjectContext,
    *,
    url: str | None = None,
    emit_only: bool = False,
) -> dict[str, Any]:
    """Emit package; optionally run visual.audit + visual.aesthetic and advance state."""
    emitted = emit_review_package(ctx, url=url, run_audit=not emit_only)
    out: dict[str, Any] = {"emitted": emitted, "results": []}

    if emit_only:
        return out

    reg = get_registry()
    checks = reg.by_ids(["visual.audit", "layout.browser", "visual.aesthetic"])
    results = run_checks(ctx, checks, url=url)
    out["results"] = [r.to_dict() for r in results]

    state = ctx.load_state()
    visual_ok = all(
        r.status == "passed"
        for r in results
        if r.check_id in {"visual.audit", "layout.browser"}
    )
    aesthetic = next((r for r in results if r.check_id == "visual.aesthetic"), None)
    aesthetic_ok = aesthetic is not None and aesthetic.status == "passed"
    independence = (aesthetic.details or {}).get("independence") if aesthetic else "unavailable"
    independence_class = (
        (aesthetic.details or {}).get("independence_class") if aesthetic else "weak"
    )

    # Advance state carefully — READY only with verified (strong) independence
    # Declared (medium / independent-clone) stays INDEPENDENT_REVIEW_REQUIRED unless
    # WDE_ALLOW_DECLARED_INDEPENDENCE=1 and aesthetic check already passed.
    import os

    allow_declared = os.environ.get("WDE_ALLOW_DECLARED_INDEPENDENCE", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    can_ready = aesthetic_ok and (
        independence == "strong"
        or (independence == "medium" and independence_class == "declared" and allow_declared)
    )

    try:
        if visual_ok and state.get("phase") == "VISUAL_REVIEW_REQUIRED":
            state = apply_transition(state, "INDEPENDENT_REVIEW_REQUIRED")
        if can_ready and state.get("phase") == "INDEPENDENT_REVIEW_REQUIRED":
            state = apply_transition(state, "READY_TO_DELIVER")
            hashes = state.get("hashes") or {}
            ev = Evidence(
                check_id="review.independent",
                status="passed",
                executor="wde-core",
                source_hash=hashes.get("SOURCE", ""),
                contract_hash=hashes.get("DESIGN", ""),
                details={
                    "independence": independence,
                    "independence_class": independence_class,
                    "aesthetic": aesthetic.to_dict() if aesthetic else {},
                },
                rule_category="taste_preference",
            )
            path = write_evidence(ctx.wde / "evidence", ev)
            state.setdefault("valid_checks", {})[ev.check_id] = str(
                path.relative_to(ctx.root)
            ).replace("\\", "/")
        elif aesthetic_ok and independence == "medium" and not allow_declared:
            state["blockers"] = [
                {
                    "code": "declared_independence",
                    "message": "independent-clone is declared-only — not enough for READY under strict mode",
                    "remediation": "Use reviewer independent|human, or set WDE_ALLOW_DECLARED_INDEPENDENCE=1 for local demos",
                }
            ]
        elif aesthetic and independence == "weak":
            state["blockers"] = [
                {
                    "code": "weak_independence",
                    "message": "reviewer is self/agent — delivery stays unverified for independent review",
                    "remediation": "Re-judge with independent / human reviewer",
                }
            ]
        ctx.save_state(state)
    except ValueError:
        ctx.save_state(state)

    out["phase"] = ctx.load_state().get("phase")
    out["independence"] = independence
    return out
