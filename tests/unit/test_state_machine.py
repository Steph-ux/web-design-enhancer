"""V3 state machine — models cannot force READY_TO_DELIVER."""

from wde.core.state_machine import (
    apply_transition,
    can_transition,
    initial_state,
    next_action_for,
)


def test_initial_state_is_intent_required():
    s = initial_state()
    assert s["phase"] == "INTENT_REQUIRED"
    assert s["schema_version"] == "3.0"
    assert s["next_action"]["id"] == "discover_or_brief"
    assert s["next_action"]["command"] == "wde discover"


def test_illegal_transition_raises():
    s = initial_state()
    try:
        apply_transition(s, "READY_TO_DELIVER")
        assert False, "should raise"
    except ValueError as e:
        assert "Illegal transition" in str(e)


def test_cannot_skip_to_ready():
    assert not can_transition("INTENT_REQUIRED", "READY_TO_DELIVER")
    assert can_transition("INDEPENDENT_REVIEW_REQUIRED", "READY_TO_DELIVER")


def test_happy_path_prefix():
    s = initial_state()
    s = apply_transition(s, "INTENT_VALIDATED")
    assert s["phase"] == "INTENT_VALIDATED"
    s = apply_transition(s, "RESEARCH_REQUIRED")
    assert s["history"][-1]["via"] == "research.start"


def test_source_change_dirties_ready():
    s = initial_state()
    # jump via legal chain abbreviated for test using successive legal edges
    for phase in [
        "INTENT_VALIDATED",
        "RESEARCH_REQUIRED",
        "RESEARCH_VALIDATED",
        "ARCHITECTURE_REQUIRED",
        "ARCHITECTURE_VALIDATED",
        "CONTRACT_REQUIRED",
        "CONTRACT_VALIDATED",
        "IMPLEMENTATION_ALLOWED",
        "MECHANICAL_REVIEW_REQUIRED",
        "VISUAL_REVIEW_REQUIRED",
        "INDEPENDENT_REVIEW_REQUIRED",
        "READY_TO_DELIVER",
    ]:
        s = apply_transition(s, phase)
    assert s["phase"] == "READY_TO_DELIVER"
    s = apply_transition(s, "IMPLEMENTATION_DIRTY")
    assert s["phase"] == "IMPLEMENTATION_DIRTY"
    assert next_action_for(s["phase"]).id == "mechanical"
