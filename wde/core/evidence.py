"""Evidence envelopes — only wde-core (or registered runners) may create 'passed'."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from wde import __version__
from wde.core.hashing import sha256_text

ALLOWED_EXECUTORS = frozenset({"wde-core", "wde-check", "wde-browser", "wde-v2-bridge"})


@dataclass
class Evidence:
    schema_version: str = "3.0"
    check_id: str = ""
    status: str = "failed"
    executed_at: str = ""
    executor: str = "wde-core"
    tool_version: str = __version__
    source_hash: str = ""
    contract_hash: str = ""
    environment: dict[str, Any] = field(default_factory=dict)
    artifacts: list[str] = field(default_factory=list)
    result_digest: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    rule_category: str = "functional_quality"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def validate_writer(self) -> None:
        if self.status == "passed" and self.executor not in ALLOWED_EXECUTORS:
            raise PermissionError(
                f"executor '{self.executor}' cannot write status=passed "
                f"(allowed: {sorted(ALLOWED_EXECUTORS)})"
            )

    def seal(self) -> "Evidence":
        """Compute result_digest from canonical payload (excluding digest itself)."""
        self.validate_writer()
        if not self.executed_at:
            self.executed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        payload = self.to_dict()
        payload.pop("result_digest", None)
        canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        self.result_digest = sha256_text(canonical)
        return self


def write_evidence(evidence_dir: Path, evidence: Evidence) -> Path:
    evidence.seal()
    evidence_dir.mkdir(parents=True, exist_ok=True)
    safe_id = evidence.check_id.replace("/", "_").replace("\\", "_")
    path = evidence_dir / f"{safe_id}.json"
    path.write_text(
        json.dumps(evidence.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def load_evidence(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def evidence_is_fresh(ev: dict[str, Any], expected_source_hash: str) -> bool:
    if ev.get("status") != "passed":
        return False
    if ev.get("executor") not in ALLOWED_EXECUTORS:
        return False
    if expected_source_hash and ev.get("source_hash") != expected_source_hash:
        return False
    return True
