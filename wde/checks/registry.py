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
            "static": ["slop.static", "a11y.static"],
            "mechanical": ["slop.static", "a11y.static"],
            "browser": ["layout.browser"],
            "deliver": ["slop.static", "a11y.static"],
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
    from wde.checks.static.accessibility import AccessibilityStaticCheck
    from wde.checks.static.slop import SlopStaticCheck

    reg = CheckRegistry()
    for c in (SlopStaticCheck(), AccessibilityStaticCheck(), LayoutBrowserCheck()):
        reg.register(c)
    return reg
