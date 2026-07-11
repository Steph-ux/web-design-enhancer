"""Consume research receipts into a structured synthesis for territory generation."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Finding:
    statement: str
    source_path_kind: str = ""
    source_tool: str = ""
    weight: float = 1.0
    receipt_digest: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ResearchSynthesis:
    sector_findings: list[Finding] = field(default_factory=list)
    visual_principles: list[Finding] = field(default_factory=list)
    anti_references: list[Finding] = field(default_factory=list)
    cross_domain_moves: list[Finding] = field(default_factory=list)
    typography_options: list[Finding] = field(default_factory=list)
    interaction_options: list[Finding] = field(default_factory=list)
    source_receipts: list[str] = field(default_factory=list)
    confidence: str = "limited"  # high | medium | limited | none
    coverage: dict[str, bool] = field(default_factory=dict)
    unused_tools: list[str] = field(default_factory=list)
    degraded_mode: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "sector_findings": [f.to_dict() for f in self.sector_findings],
            "visual_principles": [f.to_dict() for f in self.visual_principles],
            "anti_references": [f.to_dict() for f in self.anti_references],
            "cross_domain_moves": [f.to_dict() for f in self.cross_domain_moves],
            "typography_options": [f.to_dict() for f in self.typography_options],
            "interaction_options": [f.to_dict() for f in self.interaction_options],
            "source_receipts": list(self.source_receipts),
            "confidence": self.confidence,
            "coverage": dict(self.coverage),
            "unused_tools": list(self.unused_tools),
            "degraded_mode": self.degraded_mode,
        }

    def coverage_report(self) -> str:
        lines = ["Research coverage"]
        labels = {
            "internal_sector": "Internal sector framing",
            "local_corpus": "Local UI corpus",
            "live_visual": "Live visual references",
            "external_cross_domain": "External cross-domain research",
            "promax": "UI/UX Pro Max search",
            "getdesign": "getdesign brand tokens",
        }
        for key, label in labels.items():
            ok = self.coverage.get(key, False)
            mark = "✓" if ok else "✗"
            suffix = "" if ok else " unavailable"
            lines.append(f"{mark} {label}{suffix if not ok else ''}")
        lines.append("")
        lines.append(f"Confidence: {self.confidence}")
        if self.degraded_mode:
            lines.append("Mode: degraded (no successful external tools)")
        return "\n".join(lines)


def _finding(statement: str, r: dict[str, Any], weight: float = 1.0) -> Finding:
    return Finding(
        statement=statement,
        source_path_kind=str(r.get("path_kind") or ""),
        source_tool=str(r.get("tool") or ""),
        weight=weight,
        receipt_digest=str(r.get("digest") or "")[:24],
    )


def synthesize_research(receipts: list[Any]) -> ResearchSynthesis:
    """Turn raw receipts (dataclass or dict) into design inputs."""
    rows: list[dict[str, Any]] = []
    for r in receipts:
        if hasattr(r, "to_dict"):
            rows.append(r.to_dict())
        elif isinstance(r, dict):
            rows.append(r)

    syn = ResearchSynthesis()
    syn.source_receipts = [
        str(r.get("_path") or r.get("artifact") or r.get("tool") or "")
        for r in rows
        if r.get("tool")
    ]

    success = [r for r in rows if r.get("status") == "success"]
    external_ok = [
        r
        for r in success
        if r.get("source_type") in {"external_cli", "live_web"}
        or r.get("network_used") is True
    ]
    internal_ok = [
        r
        for r in success
        if r.get("source_type") in {"internal_knowledge", "local_corpus", None, ""}
        or r.get("network_used") is False
    ]

    for r in rows:
        kind = r.get("path_kind") or ""
        status = r.get("status")
        details = r.get("details") if isinstance(r.get("details"), dict) else {}
        retained = r.get("retained") or []

        if kind == "sector" and status == "success":
            syn.coverage["internal_sector"] = True
            for c in details.get("content_types") or retained:
                syn.sector_findings.append(_finding(f"Content type: {c}", r))
            if details.get("conversion_path"):
                syn.sector_findings.append(
                    _finding(f"Conversion: {details['conversion_path']}", r, 1.2)
                )
            for code in details.get("typical_codes") or []:
                syn.visual_principles.append(_finding(str(code), r))

        if kind == "anti_reference" and status == "success":
            avoid = details.get("avoid") or retained
            for a in avoid:
                syn.anti_references.append(_finding(str(a), r, 1.1))

        if kind == "cross_domain" and status == "success":
            syn.coverage["external_cross_domain"] = status == "success" and bool(
                r.get("network_used") or r.get("source_type") == "external_cli"
            )
            moves = details.get("moves") or retained or details.get("steal") or []
            if isinstance(moves, str):
                moves = [moves]
            for m in moves:
                syn.cross_domain_moves.append(_finding(str(m), r))
            # Always capture notes as a move if present
            if r.get("notes"):
                syn.cross_domain_moves.append(_finding(str(r["notes"])[:200], r, 0.8))

        if kind == "visual" and status == "success":
            syn.coverage["live_visual"] = bool(
                r.get("network_used") or r.get("source_type") in {"live_web", "external_cli"}
            )
            for k in ("motion", "typography", "layout", "image"):
                if details.get(k):
                    bucket = (
                        syn.typography_options
                        if k == "typography"
                        else syn.visual_principles
                    )
                    bucket.append(_finding(f"{k}: {details[k]}", r))

        if kind == "promax" and status == "success":
            syn.coverage["promax"] = True
            syn.coverage["local_corpus"] = True
            for item in retained[:8]:
                syn.visual_principles.append(_finding(str(item), r))
            if details.get("styles"):
                for s in details["styles"][:5]:
                    syn.visual_principles.append(_finding(f"style: {s}", r))

        if kind == "getdesign" and status == "success":
            syn.coverage["getdesign"] = True
            syn.coverage["live_visual"] = True
            for item in retained[:8]:
                syn.visual_principles.append(_finding(str(item), r))

        # Tools called but not consumed → track
        if status in {"skipped", "failed"}:
            syn.unused_tools.append(f"{r.get('tool')}:{kind}:{status}")

    # Default coverage flags
    for k in (
        "internal_sector",
        "local_corpus",
        "live_visual",
        "external_cross_domain",
        "promax",
        "getdesign",
    ):
        syn.coverage.setdefault(k, False)

    # Confidence
    n_success = len(success)
    n_external = len(external_ok)
    if n_success == 0:
        syn.confidence = "none"
        syn.degraded_mode = True
    elif n_external == 0:
        syn.confidence = "limited"
        syn.degraded_mode = True
    elif n_success >= 4 and n_external >= 1:
        syn.confidence = "high"
        syn.degraded_mode = False
    else:
        syn.confidence = "medium"
        syn.degraded_mode = False

    # If sector internal always succeeded, mark internal
    if any(r.get("path_kind") == "sector" and r.get("status") == "success" for r in rows):
        syn.coverage["internal_sector"] = True

    return syn


def write_synthesis(root: Path, synthesis: ResearchSynthesis) -> Path:
    d = root / ".wde" / "research"
    d.mkdir(parents=True, exist_ok=True)
    path = d / "research-synthesis.json"
    path.write_text(
        json.dumps(synthesis.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    report = d / "research-coverage.txt"
    report.write_text(synthesis.coverage_report() + "\n", encoding="utf-8")
    return path
