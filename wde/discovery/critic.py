"""Score territories on the critique grid and select one — no Christmas-tree mashups."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from wde.discovery.interpret import Interpretation
from wde.discovery.territories import CRITIQUE_CRITERIA, Territory


@dataclass
class TerritoryScore:
    territory_id: str
    scores: dict[str, int] = field(default_factory=dict)
    total: int = 0
    notes: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SelectionResult:
    winner_id: str
    winner_name: str
    rationale: str
    scores: list[TerritoryScore]
    rejected_mashup: bool = True  # we never merge all three

    def to_dict(self) -> dict[str, Any]:
        return {
            "winner_id": self.winner_id,
            "winner_name": self.winner_name,
            "rationale": self.rationale,
            "scores": [s.to_dict() for s in self.scores],
            "rejected_mashup": self.rejected_mashup,
            "criteria": list(CRITIQUE_CRITERIA),
        }


def _score_one(t: Territory, interp: Interpretation) -> TerritoryScore:
    """Heuristic critic — deterministic, inspectable."""
    s: dict[str, int] = {}
    notes: dict[str, str] = {}

    # Relevance: metaphor tied to sector keywords
    sector = interp.sector_key
    blob = f"{t.metaphor} {t.structure} {t.name}".lower()
    if sector in {"agency", "hospitality"} and any(
        w in blob for w in ("hotel", "ledger", "voyage", "travel", "guest", "key", "lieu", "film")
    ):
        s["relevance"] = 9
        notes["relevance"] = "Metaphor lands in hospitality/agency craft language"
    elif sector == "saas" and any(w in blob for w in ("instrument", "spec", "runbook", "signal", "ops")):
        s["relevance"] = 9
        notes["relevance"] = "Metaphor matches technical product register"
    else:
        s["relevance"] = 7
        notes["relevance"] = "Generic but coherent with subject hypothesis"

    # Distinction: anti-references named + non-template structure
    if len(t.anti_references) >= 2 and "card" in " ".join(t.anti_references).lower():
        s["distinction"] = 9
        notes["distinction"] = "Explicit anti-template stance"
    else:
        s["distinction"] = 6
        notes["distinction"] = "Needs stronger anti-reference list"

    # Clarity
    if "CTA" in t.signature_move or "Request" in t.signature_move or "contact" in t.structure.lower():
        s["clarity"] = 8
        notes["clarity"] = "Path to action is named in structure/signature"
    else:
        s["clarity"] = 7
        notes["clarity"] = "Action path implied"

    # Feasibility: lower motion easier
    if t.motion_level <= 3:
        s["feasibility"] = 9
        notes["feasibility"] = "Low motion — executable in static CSS/HTML"
    elif t.motion_level <= 6:
        s["feasibility"] = 7
        notes["feasibility"] = "Moderate motion — needs disciplined animation"
    else:
        s["feasibility"] = 5
        notes["feasibility"] = "High motion — risk of incomplete execution"

    # Responsive
    if "horizontal" in t.structure.lower() or t.motion_level >= 7:
        s["responsive"] = 6
        notes["responsive"] = "Horizontal/cinematic ideas need careful mobile redesign"
    else:
        s["responsive"] = 8
        notes["responsive"] = "Vertical/ledger structures collapse cleanly"

    # Conversion
    if interp.primary_action.lower() in t.structure.lower() or "consult" in t.signature_move.lower() or "request" in t.signature_move.lower() or "CTA" in t.signature_move:
        s["conversion"] = 8
        notes["conversion"] = "Signature or structure references conversion"
    else:
        s["conversion"] = 7
        notes["conversion"] = "Conversion must be explicit in compile"

    # Signature
    if t.signature_move and len(t.signature_move) >= 20:
        s["signature"] = 9
        notes["signature"] = "Memorable owned move stated"
    else:
        s["signature"] = 5
        notes["signature"] = "Signature too thin"

    # Sobriety: penalize high motion + decorative image language
    if t.motion_level <= 3 and "no stock" in t.image_treatment.lower() or "minimal" in t.image_treatment.lower() or "mono" in t.typography.lower():
        s["sobriety"] = 9
        notes["sobriety"] = "Restraint in motion/image"
    elif t.motion_level >= 7:
        s["sobriety"] = 5
        notes["sobriety"] = "High motion risks effect accumulation"
    else:
        s["sobriety"] = 7
        notes["sobriety"] = "Balanced"

    # Ensure all criteria present
    for c in CRITIQUE_CRITERIA:
        s.setdefault(c, 6)
        notes.setdefault(c, "")

    total = sum(s.values())
    return TerritoryScore(territory_id=t.id, scores=s, total=total, notes=notes)


def select_territory(
    territories: list[Territory],
    interp: Interpretation,
) -> SelectionResult:
    """Pick a single winner by total score; never merge all three."""
    scored = [_score_one(t, interp) for t in territories]
    scored.sort(key=lambda x: (-x.total, x.territory_id))
    winner_score = scored[0]
    winner = next(t for t in territories if t.id == winner_score.territory_id)
    runner = scored[1] if len(scored) > 1 else None
    rationale = (
        f"Selected « {winner.name} » ({winner.id}) with total {winner_score.total}/80. "
        f"Highest distinction+signature+sobriety under feasibility. "
    )
    if runner:
        rationale += (
            f"Rejected mashup with « {runner.territory_id} » "
            f"(score {runner.total}) — keep one metaphor, not a collage."
        )
    return SelectionResult(
        winner_id=winner.id,
        winner_name=winner.name,
        rationale=rationale,
        scores=scored,
        rejected_mashup=True,
    )
