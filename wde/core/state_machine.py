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


# Public CLI commands that next_action may emit — kept in sync with argparse.
PUBLIC_NEXT_COMMANDS = frozenset(
    {
        "wde init",
        "wde status",
        "wde next",
        "wde doctor",
        "wde validate intent",
        "wde validate research",
        "wde validate experience",
        "wde validate design",
        "wde validate lock",
        "wde run static",
        "wde run mechanical",
        "wde run browser",
        "wde run visual",
        "wde run wow",
        "wde run deliver",
        "wde run full",
        "wde deliver-check",
        "wde review",
        "wde report",
        "wde migrate-v2",
        "wde benchmark",
    }
)


def next_action_for(phase: str) -> NextAction:
    """Every `.command` must be a real public CLI entry (see PUBLIC_NEXT_COMMANDS)."""
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
            "wde validate intent",
            "agent",
        ),
        "INTENT_VALIDATED": NextAction(
            "research",
            "Run design research pillars then validate research",
            "wde validate research",
            "agent",
        ),
        "RESEARCH_REQUIRED": NextAction(
            "research_run",
            "Prove pillars (search.py --persist + getdesign) then validate research",
            "wde validate research",
            "agent",
        ),
        "RESEARCH_VALIDATED": NextAction(
            "architecture",
            "Write EXPERIENCE-CONTRACT then validate experience",
            "wde validate experience",
            "agent",
        ),
        "ARCHITECTURE_REQUIRED": NextAction(
            "architecture_write",
            "Complete experience contract and validate experience",
            "wde validate experience",
            "agent",
        ),
        "ARCHITECTURE_VALIDATED": NextAction(
            "design_contract",
            "Write DESIGN.md then validate design",
            "wde validate design",
            "agent",
        ),
        "CONTRACT_REQUIRED": NextAction(
            "contracts",
            "Validate DESIGN.md and structural lock (design then lock)",
            "wde validate design",
            "agent",
        ),
        "CONTRACT_VALIDATED": NextAction(
            "implement",
            "Implementation allowed — implement UI then deliver-check",
            "wde deliver-check",
            "agent",
        ),
        "IMPLEMENTATION_ALLOWED": NextAction(
            "code",
            "Implement UI then run deliver-check",
            "wde deliver-check",
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
            "Run mechanical checks (or deliver-check)",
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
            "Emit review package + process independent aesthetic verdict",
            "wde review",
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
    """Internal helper for wde-core only — not a public CLI target.

    Prefer domain events (`validate *`, `run *`, `review`, `deliver-check`) which
    verify preconditions before calling this.
    """
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


def assert_next_command_is_public(command: str) -> None:
    """Raise if next_action.command is not a known public CLI entry."""
    base = (command or "").strip().split(" --")[0].strip()
    # allow optional trailing args already stripped by split on --
    # also accept exact matches from table
    if base in PUBLIC_NEXT_COMMANDS:
        return
    # profile variants like "wde run mechanical" already in set
    raise ValueError(f"next_action.command is not a public CLI command: {command!r}")


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
