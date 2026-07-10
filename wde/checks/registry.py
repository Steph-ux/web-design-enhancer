"""Global check registry."""

from __future__ import annotations

from typing import Iterable

from wde.checks.base import Check


class CheckRegistry:
    def __init__(self) -> None:
        self._checks: dict[str, Check] = {}

    def register(self, check: Check) -> None:
        self._checks[check.id] = check

    def get(self, check_id: str) -> Check | None:
        return self._checks.get(check_id)

    def all(self) -> list[Check]:
        return list(self._checks.values())

    def by_ids(self, ids: Iterable[str]) -> list[Check]:
        out = []
        for i in ids:
            c = self._checks.get(i)
            if c:
                out.append(c)
        return out

    def profile(self, name: str) -> list[Check]:
        """Named profiles select check IDs (expand over time)."""
        profiles: dict[str, list[str]] = {
            "static": [
                "slop.static",
                "a11y.static",
                "spacing.grid",
                "style.uniqueness",
                "beauty.score",
                "gestures.archetype",
                "design.diff",
            ],
            "mechanical": [
                "slop.static",
                "a11y.static",
                "spacing.grid",
                "style.uniqueness",
                "beauty.score",
                "gestures.archetype",
                "design.diff",
            ],
            "browser": ["layout.browser", "visual.audit"],
            "visual": ["visual.audit", "layout.browser", "visual.aesthetic"],
            "wow": ["wow.excess", "gestures.archetype", "beauty.score"],
            "deliver": [
                "slop.static",
                "a11y.static",
                "spacing.grid",
                "style.uniqueness",
                "design.diff",
            ],
            "full": [
                "slop.static",
                "a11y.static",
                "spacing.grid",
                "style.uniqueness",
                "beauty.score",
                "gestures.archetype",
                "design.diff",
                "wow.excess",
                "layout.browser",
                "visual.audit",
                "visual.aesthetic",
            ],
        }
        ids = profiles.get(name, profiles["static"])
        return self.by_ids(ids)


_REGISTRY: CheckRegistry | None = None


def get_registry() -> CheckRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = default_registry()
    return _REGISTRY


def default_registry() -> CheckRegistry:
    from wde.checks.browser.layout import LayoutBrowserCheck
    from wde.checks.browser.visual_audit import VisualAuditBrowserCheck
    from wde.checks.static.accessibility import AccessibilityStaticCheck
    from wde.checks.static.beauty import BeautyStaticCheck
    from wde.checks.static.design_diff import DesignDiffStaticCheck
    from wde.checks.static.gestures import GesturesStaticCheck
    from wde.checks.static.slop import SlopStaticCheck
    from wde.checks.static.spacing import SpacingStaticCheck
    from wde.checks.static.uniqueness import UniquenessStaticCheck
    from wde.checks.static.wow import WowStaticCheck
    from wde.checks.visual.aesthetic import AestheticVerdictCheck

    reg = CheckRegistry()
    for c in (
        SlopStaticCheck(),
        AccessibilityStaticCheck(),
        SpacingStaticCheck(),
        UniquenessStaticCheck(),
        BeautyStaticCheck(),
        GesturesStaticCheck(),
        DesignDiffStaticCheck(),
        WowStaticCheck(),
        LayoutBrowserCheck(),
        VisualAuditBrowserCheck(),
        AestheticVerdictCheck(),
    ):
        reg.register(c)
    return reg
