"""Research receipt schema — proof a tool was called, not merely instructed."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from wde.core.hashing import sha256_text

RECEIPT_SCHEMA_VERSION = "3.0"
RESEARCH_DIR = ".wde/research"


@dataclass
class ResearchReceipt:
    schema_version: str = RECEIPT_SCHEMA_VERSION
    tool: str = ""
    path_kind: str = ""  # sector | visual | anti_reference | cross_domain | promax | getdesign
    query: str = ""
    executed_at: str = ""
    status: str = "skipped"  # success | failed | skipped
    result_count: int = 0
    artifact: str = ""
    digest: str = ""
    notes: str = ""
    retained: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def seal(self, artifact_text: str = "") -> "ResearchReceipt":
        if not self.executed_at:
            self.executed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        payload = self.to_dict()
        payload.pop("digest", None)
        body = artifact_text or json.dumps(payload, sort_keys=True, ensure_ascii=False)
        self.digest = sha256_text(body)
        return self


def research_dir(root: Path) -> Path:
    return root / ".wde" / "research"


def write_receipt(root: Path, receipt: ResearchReceipt, *, artifact_text: str = "") -> Path:
    receipt.seal(artifact_text)
    d = research_dir(root)
    d.mkdir(parents=True, exist_ok=True)
    safe = f"{receipt.path_kind or 'misc'}-{receipt.tool or 'tool'}".replace("/", "-")
    path = d / f"{safe}.json"
    # avoid collisions
    if path.is_file():
        path = d / f"{safe}-{receipt.executed_at.replace(':', '')}.json"
    path.write_text(
        json.dumps(receipt.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def load_receipts(root: Path) -> list[dict[str, Any]]:
    d = research_dir(root)
    if not d.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for p in sorted(d.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("tool"):
                data["_path"] = str(p.relative_to(root)).replace("\\", "/")
                out.append(data)
        except (OSError, json.JSONDecodeError):
            continue
    return out


def receipt_is_valid(r: dict[str, Any]) -> bool:
    if r.get("status") not in {"success", "failed", "skipped"}:
        return False
    if not r.get("tool") or not r.get("digest"):
        return False
    if r.get("status") == "success" and not r.get("artifact") and r.get("result_count", 0) < 1:
        # success without payload is suspicious unless notes explain
        if not r.get("notes"):
            return False
    return True


def discovery_receipts_satisfy_research(root: Path) -> tuple[bool, list[str]]:
    """True if discovery left enough real receipts (success) to stand in for pillars."""
    receipts = load_receipts(root)
    problems: list[str] = []
    if not receipts:
        return False, ["no receipts under .wde/research/"]
    valid = [r for r in receipts if receipt_is_valid(r)]
    if len(valid) < 2:
        problems.append(f"need ≥2 valid receipts, found {len(valid)}")
    successes = [r for r in valid if r.get("status") == "success"]
    if not successes:
        problems.append("no receipt with status=success")
    kinds = {r.get("path_kind") for r in valid}
    # want at least sector or promax + one more path
    if not ({"sector", "promax", "visual"} & kinds):
        problems.append("missing sector/visual/promax path_kind among receipts")
    digests_ok = all(len(str(r.get("digest", ""))) >= 16 for r in successes)
    if successes and not digests_ok:
        problems.append("success receipts missing digests")
    return len(problems) == 0, problems
