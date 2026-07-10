"""End-to-end Creative Discovery orchestration."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from wde.discovery.compile import write_contracts
from wde.discovery.critic import select_territory
from wde.discovery.interpret import Interpretation, interpret_request
from wde.discovery.receipts import research_dir
from wde.discovery.research_runner import run_all_research
from wde.discovery.territories import (
    generate_territories,
    territories_are_structurally_divergent,
)
from wde.core.project_context import ProjectContext, init_project


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
    interpret → research receipts → 3 territories → select → compile contracts.
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

    receipts = run_all_research(root, interp, try_getdesign=try_getdesign)
    receipt_paths: list[str] = []
    for r in receipts:
        # find file on disk by path_kind
        for p in research_dir(root).glob(f"{r.path_kind}-*.json"):
            rel = str(p.relative_to(root)).replace("\\", "/")
            if rel not in receipt_paths:
                receipt_paths.append(rel)
        if r.artifact and r.artifact not in receipt_paths:
            receipt_paths.append(r.artifact)

    # Also list all receipt jsons
    for p in sorted(research_dir(root).glob("*.json")):
        rel = str(p.relative_to(root)).replace("\\", "/")
        if rel not in receipt_paths and p.name != "interpretation.json":
            if "receipt" in p.name or any(
                k in p.name
                for k in (
                    "sector",
                    "visual",
                    "anti",
                    "cross",
                    "promax",
                    "getdesign",
                )
            ):
                receipt_paths.append(rel)

    territories = generate_territories(interp)
    if not territories_are_structurally_divergent(territories):
        errors.append("territories are not structurally divergent")

    selection = select_territory(territories, interp)
    winner = next(t for t in territories if t.id == selection.winner_id)

    # Persist territories + selection
    terr_path = research_dir(root) / "territories.json"
    terr_path.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "territories": [t.to_dict() for t in territories],
                "selection": selection.to_dict(),
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    contracts = write_contracts(root, interp, winner, selection, receipt_paths)

    # Success receipts required: at least one success among research
    success_n = sum(1 for r in receipts if r.status == "success")
    if success_n < 1:
        errors.append("no successful research receipts")

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
        "territories": str(terr_path.relative_to(root)).replace("\\", "/"),
        "contracts": contracts,
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
    )
