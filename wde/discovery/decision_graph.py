"""Decision graph — source → principle → transformation → contract → code → render."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from wde.discovery.critic import SelectionResult
from wde.discovery.interpret import Interpretation
from wde.discovery.synthesis import ResearchSynthesis
from wde.discovery.territories import Territory


@dataclass
class DecisionNode:
    id: str
    kind: str  # source | principle | transformation | contract | code | render
    label: str
    refs: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DecisionEdge:
    source: str
    target: str
    relation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_decision_graph(
    interp: Interpretation,
    synthesis: ResearchSynthesis,
    winner: Territory,
    selection: SelectionResult,
    receipt_paths: list[str],
) -> dict[str, Any]:
    nodes: list[DecisionNode] = []
    edges: list[DecisionEdge] = []

    # Sources
    for i, path in enumerate(receipt_paths[:12]):
        nid = f"src-{i}"
        nodes.append(DecisionNode(id=nid, kind="source", label=path, refs=[path]))
    for i, f in enumerate(synthesis.sector_findings[:4]):
        nid = f"principle-sector-{i}"
        nodes.append(
            DecisionNode(
                id=nid,
                kind="principle",
                label=f.statement,
                refs=[f.source_path_kind, f.receipt_digest],
            )
        )
        if receipt_paths:
            edges.append(DecisionEdge(source="src-0", target=nid, relation="extracts"))
    for i, f in enumerate(synthesis.anti_references[:4]):
        nid = f"principle-anti-{i}"
        nodes.append(
            DecisionNode(
                id=nid,
                kind="principle",
                label=f"Avoid: {f.statement}",
                refs=[f.source_path_kind],
            )
        )

    # Transformation = selected territory
    t_id = f"transform-{winner.id}"
    nodes.append(
        DecisionNode(
            id=t_id,
            kind="transformation",
            label=f"{winner.name}: {winner.metaphor}",
            refs=[winner.palette_role, winner.signature_move],
            meta={
                "tokens_mode": winner.resolved_tokens().mode,
                "background": winner.resolved_tokens().background,
                "motion_level": winner.motion_level,
            },
        )
    )
    edges.append(
        DecisionEdge(
            source="principle-sector-0" if synthesis.sector_findings else "src-0",
            target=t_id,
            relation="selects",
        )
    )

    # Contracts
    for name in (
        "CREATIVE-BRIEF.md",
        "EXPERIENCE-CONTRACT.md",
        "DESIGN.md",
        "STRUCTURAL-LOCK.md",
    ):
        cid = f"contract-{name}"
        nodes.append(
            DecisionNode(
                id=cid,
                kind="contract",
                label=name,
                refs=[winner.signature_move, interp.primary_action],
            )
        )
        edges.append(DecisionEdge(source=t_id, target=cid, relation="compiles_to"))

    # Code / render placeholders (filled by later traces)
    nodes.append(
        DecisionNode(
            id="code-pending",
            kind="code",
            label="implementation (pending implement phase)",
            refs=[f"{winner.id.lower()}-signature"],
        )
    )
    edges.append(DecisionEdge(source="contract-DESIGN.md", target="code-pending", relation="implements"))
    nodes.append(
        DecisionNode(
            id="render-pending",
            kind="render",
            label="browser evidence (pending check phase)",
            refs=[],
        )
    )
    edges.append(DecisionEdge(source="code-pending", target="render-pending", relation="renders_as"))

    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "request": interp.raw_request,
        "winner_id": winner.id,
        "selection_rationale": selection.rationale,
        "confidence": synthesis.confidence,
        "coverage": synthesis.coverage,
        "nodes": [n.to_dict() for n in nodes],
        "edges": [e.to_dict() for e in edges],
    }


def write_decision_graph(root: Path, graph: dict[str, Any]) -> Path:
    d = root / ".wde" / "discovery"
    d.mkdir(parents=True, exist_ok=True)
    path = d / "decision-graph.json"
    path.write_text(json.dumps(graph, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # Also mirror under research for discoverers who only look there
    research = root / ".wde" / "research"
    research.mkdir(parents=True, exist_ok=True)
    (research / "decision-graph.json").write_text(
        json.dumps(graph, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path
