"""End-to-end Creative Discovery orchestration."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from wde.core.project_context import ProjectContext, init_project
from wde.discovery.compile import write_contracts
from wde.discovery.critic import select_territory
from wde.discovery.decision_graph import build_decision_graph, write_decision_graph
from wde.discovery.interpret import interpret_request
from wde.discovery.receipts import partition_receipts, request_hash, research_dir
from wde.discovery.research_runner import run_all_research
from wde.discovery.synthesis import synthesize_research, write_synthesis
from wde.discovery.territories import (
    generate_territories,
    territories_are_structurally_divergent,
)
from wde.discovery.traces import run_all_traces


@dataclass
class DiscoveryResult:
    ok: bool
    interpretation: dict[str, Any] = field(default_factory=dict)
    receipt_paths: list[str] = field(default_factory=list)
    territories: list[dict[str, Any]] = field(default_factory=list)
    selection: dict[str, Any] = field(default_factory=dict)
    contracts: dict[str, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    artifact_dir: str = ""
    synthesis: dict[str, Any] = field(default_factory=dict)
    coverage_report: str = ""
    decision_graph: str = ""
    traces: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_discovery(
    root: Path,
    request: str,
    *,
    force_init: bool = False,
    try_getdesign: bool = True,
) -> DiscoveryResult:
    """
    interpret → research receipts → synthesize → 3 territories → select → compile contracts.
    """
    root = root.resolve()
    errors: list[str] = []

    # Ensure .wde exists
    ctx = ProjectContext(root)
    if not ctx.exists():
        try:
            init_project(root, force=force_init)
        except FileExistsError:
            pass
        except Exception as e:
            errors.append(f"init failed: {e}")
            return DiscoveryResult(ok=False, errors=errors)

    interp = interpret_request(request)
    research_dir(root).mkdir(parents=True, exist_ok=True)

    # Persist interpretation
    interp_path = research_dir(root) / "interpretation.json"
    interp_path.write_text(
        json.dumps(interp.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # ── Research ──────────────────────────────────────────────────────────
    run_all_research(root, interp, try_getdesign=try_getdesign)

    # ── Reload + validate receipts from disk before any consumption ─────
    req_h = request_hash(request)
    parts = partition_receipts(root, expected_request_hash=req_h)
    valid_receipts = parts["valid_receipts"]
    invalid_receipts = parts["invalid_receipts"]
    unavailable = parts["unavailable_tools"]

    # Persist validation partition for audit
    val_path = research_dir(root) / "receipt-validation.json"
    val_path.write_text(
        json.dumps(
            {
                "request_hash": req_h,
                "valid": len(valid_receipts),
                "invalid": len(invalid_receipts),
                "unavailable": len(unavailable),
                "invalid_paths": [r.get("_path") for r in invalid_receipts],
                "unavailable_tools": [
                    f"{r.get('tool')}:{r.get('path_kind')}:{r.get('status')}"
                    for r in unavailable
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    if invalid_receipts:
        errors.append(
            f"{len(invalid_receipts)} invalid receipt(s) rejected before synthesis"
        )

    receipt_paths: list[str] = []
    for r in valid_receipts + unavailable:
        if r.get("_path") and r["_path"] not in receipt_paths:
            receipt_paths.append(r["_path"])
        if r.get("artifact") and r["artifact"] not in receipt_paths:
            receipt_paths.append(r["artifact"])

    # ── Synthesize ONLY valid receipts (never forged / tampered) ────────
    synthesis = synthesize_research(valid_receipts + unavailable)
    # External success only from valid external receipts
    ext_ok = [
        r
        for r in valid_receipts
        if r.get("status") == "success"
        and (
            r.get("source_type") in {"external_cli", "live_web"}
            or r.get("network_used") is True
        )
    ]
    if not ext_ok:
        synthesis.degraded_mode = True
        if synthesis.confidence == "high":
            synthesis.confidence = "limited"
    synth_path = write_synthesis(root, synthesis)
    coverage_report = synthesis.coverage_report()

    # ── Territories (biased by synthesis) ─────────────────────────────────
    territories = generate_territories(interp, synthesis)
    if not territories_are_structurally_divergent(territories):
        errors.append("territories are not structurally divergent")

    selection = select_territory(territories, interp, synthesis)
    winner = next(t for t in territories if t.id == selection.winner_id)

    # Persist territories + selection
    terr_path = research_dir(root) / "territories.json"
    terr_path.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "territories": [t.to_dict() for t in territories],
                "selection": selection.to_dict(),
                "synthesis_confidence": synthesis.confidence,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    # ── Compile contracts from winner tokens ──────────────────────────────
    contracts = write_contracts(root, interp, winner, selection, receipt_paths)

    # Guard: light territory must not compile Dark-first global palette
    design_text = (root / "DESIGN.md").read_text(encoding="utf-8", errors="replace")
    tok = winner.resolved_tokens()
    if tok.mode == "light":
        if "Dark-first project" in design_text and "Light-first project" not in design_text:
            errors.append("light territory compiled Dark-first DESIGN.md (token contradiction)")
        if tok.background not in design_text:
            errors.append(
                f"winner background token {tok.background} missing from DESIGN.md"
            )
    elif tok.mode == "dark":
        if tok.background not in design_text:
            errors.append(f"winner background token {tok.background} missing from DESIGN.md")

    # ── Decision graph ────────────────────────────────────────────────────
    graph = build_decision_graph(interp, synthesis, winner, selection, receipt_paths)
    graph_path = write_decision_graph(root, graph)

    # ── P5 traces (contract always; code/render soft until implement) ─────
    traces_payload = run_all_traces(root, require_browser=False)
    # contract_trace failure is blocking for discovery quality
    ct = (traces_payload.get("traces") or {}).get("contract_trace") or {}
    if traces_payload.get("ok") is False and ct.get("ok") is False:
        errors.append("discovery.contract_trace failed — see .wde/discovery/traces.json")

    # Success receipts required: at least one *valid* success
    success_n = sum(1 for r in valid_receipts if r.get("status") == "success")
    if success_n < 1:
        errors.append("no successful valid research receipts")

    # Minimum shape: 4 contracts
    for name in (
        "CREATIVE-BRIEF.md",
        "EXPERIENCE-CONTRACT.md",
        "DESIGN.md",
        "STRUCTURAL-LOCK.md",
    ):
        if not (root / name).is_file():
            errors.append(f"missing contract {name}")

    # Provenance citation in brief
    brief = (root / "CREATIVE-BRIEF.md").read_text(encoding="utf-8", errors="replace")
    if "provenance" not in brief.lower() and "receipt" not in brief.lower():
        errors.append("CREATIVE-BRIEF missing provenance linkage")

    ok = len(errors) == 0 and territories_are_structurally_divergent(territories)

    # Manifest
    manifest = {
        "ok": ok,
        "request": request,
        "interpretation": str(interp_path.relative_to(root)).replace("\\", "/"),
        "receipts": receipt_paths,
        "synthesis": str(synth_path.relative_to(root)).replace("\\", "/"),
        "coverage_report": coverage_report,
        "decision_graph": str(graph_path.relative_to(root)).replace("\\", "/"),
        "traces": ".wde/discovery/traces.json",
        "territories": str(terr_path.relative_to(root)).replace("\\", "/"),
        "contracts": contracts,
        "winner_tokens": tok.to_dict(),
        "errors": errors,
        "completed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    man_path = research_dir(root) / "discovery-manifest.json"
    man_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return DiscoveryResult(
        ok=ok,
        interpretation=interp.to_dict(),
        receipt_paths=receipt_paths,
        territories=[t.to_dict() for t in territories],
        selection=selection.to_dict(),
        contracts=contracts,
        errors=errors,
        artifact_dir=str(research_dir(root).relative_to(root)).replace("\\", "/"),
        synthesis=synthesis.to_dict(),
        coverage_report=coverage_report,
        decision_graph=str(graph_path.relative_to(root)).replace("\\", "/"),
        traces=traces_payload,
    )
