"""Research receipt schema — proof a tool was called, not merely instructed."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from wde.core.hashing import sha256_text

RECEIPT_SCHEMA_VERSION = "3.1"
RESEARCH_DIR = ".wde/research"
AUTHORIZED_EXECUTORS = frozenset({"wde-core", "wde.discovery", "subprocess", "npx"})

SourceType = Literal[
    "internal_knowledge",
    "local_corpus",
    "external_cli",
    "live_web",
]


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
    # P2 — provenance of execution
    source_type: str = "internal_knowledge"
    network_used: bool = False
    executor: str = "wde-core"
    degraded: bool = False
    # P3 — integrity
    request_hash: str = ""
    command: str = ""
    exit_code: int | None = None
    artifact_sha256: str = ""
    sealed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def seal(self, artifact_text: str = "") -> "ResearchReceipt":
        if not self.executed_at:
            self.executed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if artifact_text:
            self.artifact_sha256 = sha256_text(artifact_text)
        payload = self.to_dict()
        payload.pop("digest", None)
        payload.pop("sealed", None)
        body = artifact_text or json.dumps(payload, sort_keys=True, ensure_ascii=False)
        self.digest = sha256_text(body)
        self.sealed = True
        return self


def research_dir(root: Path) -> Path:
    return root / ".wde" / "research"


def request_hash(request: str) -> str:
    return sha256_text((request or "").strip())


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
        name = p.name
        if name in {
            "interpretation.json",
            "territories.json",
            "discovery-manifest.json",
            "research-synthesis.json",
            "decision-graph.json",
        }:
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("tool"):
                data["_path"] = str(p.relative_to(root)).replace("\\", "/")
                out.append(data)
        except (OSError, json.JSONDecodeError):
            continue
    return out


def receipt_is_valid(
    r: dict[str, Any],
    *,
    root: Path | None = None,
    expected_request_hash: str | None = None,
) -> bool:
    """Validate receipt integrity (P3)."""
    if r.get("status") not in {"success", "failed", "skipped"}:
        return False
    if not r.get("tool") or not r.get("digest"):
        return False
    # Reject hand-edited: must be sealed by wde executor
    executor = str(r.get("executor") or "")
    if executor and executor not in AUTHORIZED_EXECUTORS and not executor.startswith("wde"):
        return False
    if r.get("status") == "success" and not r.get("artifact") and r.get("result_count", 0) < 1:
        if not r.get("notes"):
            return False
    if expected_request_hash and r.get("request_hash"):
        if r["request_hash"] != expected_request_hash:
            return False
    # Recompute artifact hash when file present
    if root and r.get("artifact") and r.get("artifact_sha256"):
        art = root / str(r["artifact"])
        if art.is_file():
            text = art.read_text(encoding="utf-8", errors="replace")
            if sha256_text(text) != r["artifact_sha256"]:
                return False
    return True


def discovery_receipts_satisfy_research(root: Path) -> tuple[bool, list[str]]:
    """True if discovery left enough real receipts (success) to stand in for pillars."""
    receipts = load_receipts(root)
    problems: list[str] = []
    if not receipts:
        return False, ["no receipts under .wde/research/"]
    valid = [r for r in receipts if receipt_is_valid(r, root=root)]
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


def invalidate_receipts_for_request(root: Path, new_request: str) -> int:
    """Mark receipts stale when the discovery request hash changes. Returns count invalidated."""
    h = request_hash(new_request)
    n = 0
    for r in load_receipts(root):
        old = r.get("request_hash") or ""
        if old and old != h:
            path = root / r["_path"]
            if path.is_file():
                r["status"] = "failed"
                r["degraded"] = True
                r["notes"] = (r.get("notes") or "") + " | invalidated: request_hash mismatch"
                path.write_text(
                    json.dumps(r, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
                n += 1
    return n
