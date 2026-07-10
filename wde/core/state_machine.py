"""Persistent workflow state machine — models cannot force READY_TO_DELIVER."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

# Ordered phases (linear happy path)
PHASES = [
    "UNINITIALIZED",
    "INTENT_REQUIRED",
    "INTENT_VALIDATED",
    "RESEARCH_REQUIRED",
    "RESEARCH_VALIDATED",
    "ARCHITECTURE_REQUIRED",
    "ARCHITECTURE_VALIDATED",
    "CONTRACT_REQUIRED",
    "CONTRACT_VALIDATED",
    "IMPLEMENTATION_ALLOWED",
    "IMPLEMENTATION_DIRTY",
    "MECHANICAL_REVIEW_REQUIRED",
    "VISUAL_REVIEW_REQUIRED",
    "INDEPENDENT_REVIEW_REQUIRED",
    "READY_TO_DELIVER",
]

# Legal transitions: (from, to, via_event)
TRANSITIONS: dict[tuple[str, str], str] = {
    ("UNINITIALIZED", "INTENT_REQUIRED"): "init",
    ("INTENT_REQUIRED", "INTENT_VALIDATED"): "intent.validate",
    ("INTENT_VALIDATED", "RESEARCH_REQUIRED"): "research.start",
    ("RESEARCH_REQUIRED", "RESEARCH_VALIDATED"): "research.validate",
    ("RESEARCH_VALIDATED", "ARCHITECTURE_REQUIRED"): "architecture.start",
    ("ARCHITECTURE_REQUIRED", "ARCHITECTURE_VALIDATED"): "architecture.validate",
    ("ARCHITECTURE_VALIDATED", "CONTRACT_REQUIRED"): "contract.start",
    ("CONTRACT_REQUIRED", "CONTRACT_VALIDATED"): "contract.validate",
    ("CONTRACT_VALIDATED", "IMPLEMENTATION_ALLOWED"): "implementation.allow",
    ("IMPLEMENTATION_ALLOWED", "IMPLEMENTATION_DIRTY"): "source.changed",
    ("IMPLEMENTATION_DIRTY", "MECHANICAL_REVIEW_REQUIRED"): "mechanical.request",
    ("IMPLEMENTATION_ALLOWED", "MECHANICAL_REVIEW_REQUIRED"): "mechanical.request",
    ("MECHANICAL_REVIEW_REQUIRED", "VISUAL_REVIEW_REQUIRED"): "mechanical.passed",
    ("VISUAL_REVIEW_REQUIRED", "INDEPENDENT_REVIEW_REQUIRED"): "visual.passed",
    ("INDEPENDENT_REVIEW_REQUIRED", "READY_TO_DELIVER"): "independent.passed",
    # Dirt after review
    ("MECHANICAL_REVIEW_REQUIRED", "IMPLEMENTATION_DIRTY"): "source.changed",
    ("VISUAL_REVIEW_REQUIRED", "IMPLEMENTATION_DIRTY"): "source.changed",
    ("INDEPENDENT_REVIEW_REQUIRED", "IMPLEMENTATION_DIRTY"): "source.changed",
    ("READY_TO_DELIVER", "IMPLEMENTATION_DIRTY"): "source.changed",
    # Contract edits force rewind
    ("IMPLEMENTATION_ALLOWED", "CONTRACT_REQUIRED"): "contract.invalidated",
    ("IMPLEMENTATION_DIRTY", "CONTRACT_REQUIRED"): "contract.invalidated",
    ("READY_TO_DELIVER", "CONTRACT_REQUIRED"): "contract.invalidated",
}


@dataclass
class NextAction:
    id: str
    summary: str
    command: str = ""
    allowed_writer: str = "agent"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "summary": self.summary,
            "command": self.command,
            "allowed_writer": self.allowed_writer,
        }


def can_transition(from_phase: str, to_phase: str) -> bool:
    return (from_phase, to_phase) in TRANSITIONS


def transition_via(from_phase: str, to_phase: str) -> str | None:
    return TRANSITIONS.get((from_phase, to_phase))


def next_action_for(phase: str) -> NextAction:
    table: dict[str, NextAction] = {
        "UNINITIALIZED": NextAction(
            "init",
            "Initialize WDE project (.wde/ + contracts)",
            "wde init",
            "wde-core",
        ),
        "INTENT_REQUIRED": NextAction(
            "write_brief",
            "Fill CREATIVE-BRIEF.md then validate intent",
            "wde run intent.validate",
            "agent",
        ),
        "INTENT_VALIDATED": NextAction(
            "research",
            "Run design research pillars (search.py + getdesign)",
            "wde run research.validate",
            "agent",
        ),
        "RESEARCH_REQUIRED": NextAction(
            "research_run",
            "Execute fresh pillar tools and record artifacts",
            "wde run research.validate",
            "agent",
        ),
        "RESEARCH_VALIDATED": NextAction(
            "architecture",
            "Write EXPERIENCE-CONTRACT / IA",
            "wde run architecture.validate",
            "agent",
        ),
        "ARCHITECTURE_REQUIRED": NextAction(
            "architecture_write",
            "Complete experience contract and page objectives",
            "wde run architecture.validate",
            "agent",
        ),
        "ARCHITECTURE_VALIDATED": NextAction(
            "design_contract",
            "Write DESIGN.md + STRUCTURAL-LOCK.md",
            "wde run contract.validate",
            "agent",
        ),
        "CONTRACT_REQUIRED": NextAction(
            "contracts",
            "Complete DESIGN.md and structural lock",
            "wde run contract.validate",
            "agent",
        ),
        "CONTRACT_VALIDATED": NextAction(
            "implement",
            "Implementation is allowed under the lock",
            "wde run implementation.allow",
            "wde-core",
        ),
        "IMPLEMENTATION_ALLOWED": NextAction(
            "code",
            "Implement UI (then re-hash / review)",
            "wde status",
            "agent",
        ),
        "IMPLEMENTATION_DIRTY": NextAction(
            "mechanical",
            "Source changed — run mechanical reviews",
            "wde run mechanical",
            "wde-core",
        ),
        "MECHANICAL_REVIEW_REQUIRED": NextAction(
            "mechanical_run",
            "Run static/mechanical checks (slop, a11y, …)",
            "wde run mechanical",
            "wde-core",
        ),
        "VISUAL_REVIEW_REQUIRED": NextAction(
            "visual",
            "Run browser visual / layout audits",
            "wde run visual",
            "wde-core",
        ),
        "INDEPENDENT_REVIEW_REQUIRED": NextAction(
            "independent",
            "Independent aesthetic / human review (non-self)",
            "wde run independent",
            "wde-core",
        ),
        "READY_TO_DELIVER": NextAction(
            "deliver",
            "Delivery authorized — keep proofs fresh",
            "wde deliver-check",
            "wde-core",
        ),
    }
    return table.get(
        phase,
        NextAction("unknown", f"Unknown phase {phase}", "wde doctor", "human"),
    )


def apply_transition(
    state: dict[str, Any],
    to_phase: str,
    *,
    evidence_id: str | None = None,
    force_via: str | None = None,
) -> dict[str, Any]:
    """Return a new state dict after a legal transition. Raises ValueError if illegal."""
    from_phase = state.get("phase", "UNINITIALIZED")
    via = force_via or transition_via(from_phase, to_phase)
    if via is None:
        raise ValueError(
            f"Illegal transition {from_phase} → {to_phase}. "
            "The model cannot force phase changes; use an allowed wde command."
        )
    if to_phase == "READY_TO_DELIVER" and via != "independent.passed":
        raise ValueError("READY_TO_DELIVER requires independent.passed evidence via wde-core")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    history = list(state.get("history") or [])
    history.append(
        {
            "at": now,
            "from_phase": from_phase,
            "to_phase": to_phase,
            "via": via,
            "evidence_id": evidence_id or "",
        }
    )
    new_state = dict(state)
    new_state["phase"] = to_phase
    new_state["updated_at"] = now
    new_state["history"] = history[-50:]
    new_state["next_action"] = next_action_for(to_phase).to_dict()
    new_state["blockers"] = []
    return new_state


def initial_state() -> dict[str, Any]:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    phase = "INTENT_REQUIRED"
    return {
        "schema_version": "3.0",
        "phase": phase,
        "updated_at": now,
        "valid_checks": {},
        "invalidated_checks": [],
        "hashes": {},
        "blockers": [],
        "next_action": next_action_for(phase).to_dict(),
        "history": [
            {
                "at": now,
                "from_phase": "UNINITIALIZED",
                "to_phase": phase,
                "via": "init",
                "evidence_id": "",
            }
        ],
        "degraded_mode": False,
        "capabilities": {},
    }
