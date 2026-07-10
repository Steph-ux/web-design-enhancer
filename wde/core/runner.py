"""Execute registered checks and record evidence envelopes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from wde.checks.base import Check, CheckResult
from wde.checks.registry import get_registry
from wde.core.evidence import (
    ALLOWED_EXECUTORS,
    Evidence,
    rebuild_valid_checks_from_disk,
    verify_evidence_envelope,
    write_evidence,
)
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
    Re-hash, re-run mechanical static checks, verify evidence integrity.
    Rebuilds valid_checks from disk (state.json is not authority).
    Does NOT mark READY_TO_DELIVER (needs independent review event).
    Returns (ok, blockers, results).
    """
    state = ctx.refresh_invalidation()
    results = run_profile(ctx, "deliver", url=url)
    state = ctx.load_state()
    blockers: list[str] = []

    for r in results:
        if r.blocks_delivery:
            blockers.append(f"{r.check_id}: {r.summary}")

    # Authoritative hashes after run
    state["hashes"] = {**(state.get("hashes") or {}), **ctx.compute_hashes()}
    current_src = state["hashes"].get("SOURCE", "")
    current_contract = state["hashes"].get("DESIGN", "")

    # Rebuild valid_checks from verified envelopes only
    rebuilt, rejected = rebuild_valid_checks_from_disk(
        ctx.wde / "evidence",
        root=ctx.root,
        expected_source_hash=current_src,
        expected_contract_hash=current_contract,
    )
    for msg in rejected:
        # Do not block on intentional failed envelopes — only forged/tampered/stale passed ones
        low = msg.lower()
        if "status is 'failed'" in low or 'status is "failed"' in low or "not passed" in low:
            continue
        blockers.append(f"evidence rejected: {msg}")

    # Cross-check any leftover state pointers
    for check_id, rel in list((state.get("valid_checks") or {}).items()):
        if check_id not in rebuilt:
            path = ctx.root / rel
            if path.is_file():
                try:
                    import json as _json

                    data = _json.loads(path.read_text(encoding="utf-8"))
                except Exception:
                    blockers.append(f"{check_id}: evidence unreadable")
                    continue
                ok, reasons = verify_evidence_envelope(
                    data,
                    expected_source_hash=current_src,
                    expected_contract_hash=current_contract,
                    root=ctx.root,
                )
                if not ok:
                    blockers.append(f"{check_id}: {'; '.join(reasons)}")
            else:
                blockers.append(f"{check_id}: evidence file missing ({rel})")

    state["valid_checks"] = rebuilt

    # Required minimum for any delivery claim
    required = {"slop.static"}
    valid = set(rebuilt.keys())
    for r in required:
        if r not in valid:
            just_passed = any(x.check_id == r and x.status == "passed" for x in results)
            if not just_passed:
                blockers.append(f"missing required fresh check: {r}")

    # If READY was hand-set without review.independent verified → demote
    if state.get("phase") == "READY_TO_DELIVER":
        if "review.independent" not in rebuilt:
            blockers.append(
                "READY_TO_DELIVER without verified review.independent evidence — forged or incomplete"
            )
            try:
                state = apply_transition(state, "IMPLEMENTATION_DIRTY")
            except ValueError:
                state["phase"] = "IMPLEMENTATION_DIRTY"

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
