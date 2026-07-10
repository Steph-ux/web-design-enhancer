"""Dependency graph: which checks die when which inputs change."""

from __future__ import annotations

from typing import Iterable

# Input keys → check_ids that become invalid when that input's hash changes
DEPENDENCY_GRAPH: dict[str, list[str]] = {
    "CREATIVE_BRIEF": [
        "intent.brief",
        "architecture.ia",
        "contract.design",
        "contract.experience",
        "lock.structural",
        "visual.aesthetic",
        "deliver.final",
    ],
    "EXPERIENCE_CONTRACT": [
        "contract.experience",
        "interaction.states",
        "content.truth",
        "deliver.final",
    ],
    "DESIGN": [
        "contract.design",
        "lock.structural",
        "visual.diff",
        "visual.aesthetic",
        "slop.static",
        "deliver.final",
    ],
    "STRUCTURAL_LOCK": [
        "lock.structural",
        "visual.layout",
        "deliver.final",
    ],
    "SOURCE": [
        "slop.static",
        "a11y.static",
        "layout.measured",
        "spacing.grid",
        "beauty.score",
        "gestures.archetype",
        "visual.audit",
        "visual.aesthetic",
        "responsive.visual",
        "performance.hints",
        "deliver.final",
    ],
}


def checks_invalidated_by(changed_inputs: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for key in changed_inputs:
        for check_id in DEPENDENCY_GRAPH.get(key, []):
            if check_id not in seen:
                seen.add(check_id)
                out.append(check_id)
    return out


def diff_hashes(old: dict[str, str], new: dict[str, str]) -> list[str]:
    """Return keys whose hash value changed or appeared/disappeared."""
    changed: list[str] = []
    keys = set(old) | set(new)
    for k in sorted(keys):
        if old.get(k) != new.get(k):
            changed.append(k)
    return changed


def apply_invalidation(
    valid_checks: dict[str, str],
    changed_inputs: Iterable[str],
) -> tuple[dict[str, str], list[str]]:
    """Remove invalidated check_ids from valid_checks. Returns (new_map, invalidated_ids)."""
    doomed = set(checks_invalidated_by(changed_inputs))
    invalidated = [c for c in valid_checks if c in doomed]
    kept = {k: v for k, v in valid_checks.items() if k not in doomed}
    return kept, invalidated
