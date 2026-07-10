"""Execute registered checks and record evidence envelopes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from wde.checks.base import Check, CheckResult
from wde.checks.registry import get_registry
from wde.core.evidence import Evidence, write_evidence
from wde.core.project_context import ProjectContext
from wde.core.state_machine import apply_transition


def build_context(ctx: ProjectContext, *, url: str | None = None) -> dict[str, Any]:
    project = ctx.load_project()
    state = ctx.load_state()
    return {
        "root": ctx.root,
        "project": project,
        "state": state,
        "source_paths": project.get("source_paths") or ["."],
        "local_url": url or project.get("local_url"),
        "url": url or project.get("local_url"),
        "capabilities": state.get("capabilities") or ctx.detect_capabilities(),
        "hashes": state.get("hashes") or {},
    }


def run_checks(
    ctx: ProjectContext,
    checks: list[Check],
    *,
    url: str | None = None,
    record_evidence: bool = True,
) -> list[CheckResult]:
    context = build_context(ctx, url=url)
    state = ctx.refresh_invalidation()
    context["hashes"] = state.get("hashes") or {}
    context["capabilities"] = state.get("capabilities") or ctx.detect_capabilities()

    results: list[CheckResult] = []
    source_hash = (state.get("hashes") or {}).get("SOURCE", "")
    contract_hash = (state.get("hashes") or {}).get("DESIGN", "")

    for check in checks:
        if not check.applicable(context):
            results.append(
                CheckResult(
                    check_id=check.id,
                    status="skipped",
                    severity=check.default_severity,
                    category=check.category,
                    summary=f"Not applicable (missing capabilities: {check.required_capabilities})",
                )
            )
            continue
        result = check.run(context)
        results.append(result)

        if record_evidence and result.status == "passed":
            ev = Evidence(
                check_id=result.check_id,
                status="passed",
                executor="wde-core",
                source_hash=source_hash,
                contract_hash=contract_hash,
                artifacts=list(result.artifacts),
                details=result.to_dict(),
                rule_category=result.category,
            )
            path = write_evidence(ctx.wde / "evidence", ev)
            state.setdefault("valid_checks", {})[result.check_id] = str(
                path.relative_to(ctx.root)
            ).replace("\\", "/")
            # remove from invalidated list if present
            inv = [i for i in (state.get("invalidated_checks") or []) if i != result.check_id]
            state["invalidated_checks"] = inv
        elif record_evidence and result.status == "failed":
            # failed evidence still stored but not valid_checks
            ev = Evidence(
                check_id=result.check_id,
                status="failed",
                executor="wde-core",
                source_hash=source_hash,
                contract_hash=contract_hash,
                details=result.to_dict(),
                rule_category=result.category,
            )
            write_evidence(ctx.wde / "evidence", ev)
            state.setdefault("valid_checks", {}).pop(result.check_id, None)

    ctx.save_state(state)
    return results


def run_profile(
    ctx: ProjectContext,
    profile: str,
    *,
    url: str | None = None,
) -> list[CheckResult]:
    reg = get_registry()
    checks = reg.profile(profile)
    return run_checks(ctx, checks, url=url)


def deliver_check(ctx: ProjectContext, *, url: str | None = None) -> tuple[bool, list[str], list[CheckResult]]:
    """
    Re-hash, re-run mechanical static checks, verify evidence freshness.
    Does NOT mark READY_TO_DELIVER without independent review (future).
    Returns (ok, blockers, results).
    """
    state = ctx.refresh_invalidation()
    results = run_profile(ctx, "deliver", url=url)
    state = ctx.load_state()
    blockers: list[str] = []

    for r in results:
        if r.blocks_delivery:
            blockers.append(f"{r.check_id}: {r.summary}")

    source_hash = (state.get("hashes") or {}).get("SOURCE", "")
    for check_id, rel in list((state.get("valid_checks") or {}).items()):
        path = ctx.root / rel
        if not path.is_file():
            blockers.append(f"{check_id}: evidence file missing ({rel})")
            continue
        try:
            import json

            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            blockers.append(f"{check_id}: evidence unreadable")
            continue
        if data.get("executor") not in {"wde-core", "wde-check", "wde-browser", "wde-v2-bridge"}:
            blockers.append(f"{check_id}: executor not trusted ({data.get('executor')})")
        if source_hash and data.get("source_hash") != source_hash:
            blockers.append(f"{check_id}: stale evidence (source_hash mismatch) — re-run checks")
        if data.get("status") != "passed":
            blockers.append(f"{check_id}: evidence status is {data.get('status')}")

    # Required minimum for any delivery claim
    required = {"slop.static"}
    valid = set((state.get("valid_checks") or {}).keys())
    for r in required:
        if r not in valid:
            # if just ran and passed, valid_checks should have it
            just_passed = any(x.check_id == r and x.status == "passed" for x in results)
            if not just_passed:
                blockers.append(f"missing required fresh check: {r}")

    # Drop any valid_checks whose on-disk evidence no longer matches current SOURCE
    state = ctx.load_state()
    current_src = (state.get("hashes") or {}).get("SOURCE") or ctx.compute_hashes().get("SOURCE", "")
    state["hashes"] = {**(state.get("hashes") or {}), **ctx.compute_hashes()}
    current_src = state["hashes"].get("SOURCE", current_src)
    cleaned: dict[str, str] = {}
    for check_id, rel in list((state.get("valid_checks") or {}).items()):
        path = ctx.root / rel
        if not path.is_file():
            blockers.append(f"{check_id}: evidence file missing after run ({rel})")
            continue
        try:
            import json as _json

            data = _json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            blockers.append(f"{check_id}: evidence unreadable after run")
            continue
        if data.get("status") == "passed" and data.get("source_hash") != current_src:
            blockers.append(f"{check_id}: stale evidence after source change — re-run checks")
            continue
        if data.get("status") == "passed" and data.get("executor") not in {
            "wde-core",
            "wde-check",
            "wde-browser",
            "wde-v2-bridge",
        }:
            blockers.append(f"{check_id}: executor not trusted ({data.get('executor')})")
            continue
        cleaned[check_id] = rel
    state["valid_checks"] = cleaned

    ok = len(blockers) == 0

    # Advance mechanical → visual only — never READY_TO_DELIVER here
    if ok:
        phase = state.get("phase")
        try:
            if phase == "IMPLEMENTATION_ALLOWED":
                state = apply_transition(state, "MECHANICAL_REVIEW_REQUIRED")
                phase = state["phase"]
            if phase == "IMPLEMENTATION_DIRTY":
                state = apply_transition(state, "MECHANICAL_REVIEW_REQUIRED")
                phase = state["phase"]
            if phase == "MECHANICAL_REVIEW_REQUIRED":
                state = apply_transition(state, "VISUAL_REVIEW_REQUIRED")
            state["blockers"] = []
            ctx.save_state(state)
        except ValueError:
            ctx.save_state(state)
    else:
        state["blockers"] = [
            {"code": "deliver", "message": b, "remediation": "wde run static && fix findings"}
            for b in blockers
        ]
        ctx.save_state(state)

    return ok, blockers, results
