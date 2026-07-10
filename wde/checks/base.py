"""Check interface — every mechanical control implements this contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Finding:
    rule_id: str
    location: str
    evidence: str
    reason: str
    fix: str
    severity: str = "blocking"  # blocking | major | minor | advice

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CheckResult:
    check_id: str
    status: str  # passed | failed | warned | skipped | degraded
    severity: str  # blocking | major | minor | advice
    category: str
    summary: str
    findings: list[Finding] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)
    artifacts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["findings"] = [f.to_dict() if isinstance(f, Finding) else f for f in self.findings]
        return d

    @property
    def blocks_delivery(self) -> bool:
        if self.status in {"failed"} and self.severity in {"blocking", "major"}:
            return True
        return False


class Check(ABC):
    id: str = "check.base"
    version: str = "1.0.0"
    dependencies: list[str] = []
    required_capabilities: list[str] = []
    category: str = "functional_quality"
    default_severity: str = "blocking"

    def applicable(self, context: dict[str, Any]) -> bool:
        caps = context.get("capabilities") or {}
        for c in self.required_capabilities:
            if not caps.get(c, False):
                return False
        return True

    @abstractmethod
    def run(self, context: dict[str, Any]) -> CheckResult:
        ...

    def to_evidence_details(self, result: CheckResult) -> dict[str, Any]:
        return result.to_dict()
