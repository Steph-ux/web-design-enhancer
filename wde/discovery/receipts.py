"""Research receipt schema — proof a tool was called, not merely instructed.

Integrity model (P0):
  artifact_sha256 = SHA256(exact artifact file bytes as UTF-8 text)
  digest          = HMAC-SHA256(secret, canonical_metadata_json + artifact_sha256)
                    or SHA256(same) when WDE_EVIDENCE_SECRET is unset

seal() NEVER digests stdout snippets as the artifact. Callers must pass the
exact file content of receipt.artifact (or empty string if no artifact).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from wde.core.hashing import sha256_text

RECEIPT_SCHEMA_VERSION = "3.2"
RESEARCH_DIR = ".wde/research"
# Strict equality only — no "wde*" prefix trust
AUTHORIZED_EXECUTORS = frozenset({"wde-core", "wde.discovery", "subprocess", "npx"})

# Metadata keys included in the receipt digest (order fixed for stability)
_DIGEST_META_KEYS = (
    "schema_version",
    "tool",
    "path_kind",
    "query",
    "executed_at",
    "status",
    "result_count",
    "artifact",
    "notes",
    "retained",
    "details",
    "source_type",
    "network_used",
    "executor",
    "degraded",
    "request_hash",
    "command",
    "exit_code",
    "artifact_sha256",
)

SourceType = Literal[
    "internal_knowledge",
    "local_corpus",
    "external_cli",
    "live_web",
]


def _orchestrator_secret() -> bytes | None:
    """Optional HMAC secret. Prefer WDE_RECEIPT_SECRET, fall back to WDE_EVIDENCE_SECRET."""
    for key in ("WDE_RECEIPT_SECRET", "WDE_EVIDENCE_SECRET"):
        val = (os.environ.get(key) or "").strip()
        if val:
            return val.encode("utf-8")
    return None


def _canonical_meta_payload(data: dict[str, Any]) -> str:
    """Stable JSON of metadata only (no digest / sealed flags)."""
    meta: dict[str, Any] = {}
    for k in _DIGEST_META_KEYS:
        if k in data:
            meta[k] = data[k]
    return json.dumps(meta, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def compute_artifact_sha256(artifact_text: str) -> str:
    return sha256_text(artifact_text if artifact_text is not None else "")


def compute_receipt_digest(
    data: dict[str, Any],
    *,
    secret: bytes | None = None,
) -> str:
    """Digest over canonical metadata (which includes artifact_sha256)."""
    payload = _canonical_meta_payload(data)
    body = payload.encode("utf-8")
    sec = secret if secret is not None else _orchestrator_secret()
    if sec:
        return "hmac-sha256:" + hmac.new(sec, body, hashlib.sha256).hexdigest()
    return "sha256:" + hashlib.sha256(body).hexdigest()


def digests_equal(a: str, b: str) -> bool:
    """Constant-time compare; tolerates missing prefixes for migration."""
    aa = (a or "").strip()
    bb = (b or "").strip()
    if not aa or not bb:
        return False
    # Normalize bare hex vs prefixed
    def bare(x: str) -> str:
        if ":" in x:
            return x.split(":", 1)[1]
        return x

    ba, bb_ = bare(aa), bare(bb)
    if len(ba) != len(bb_):
        return False
    return hmac.compare_digest(ba, bb_)


@dataclass
class ResearchReceipt:
    schema_version: str = RECEIPT_SCHEMA_VERSION
    tool: str = ""
    path_kind: str = ""
    query: str = ""
    executed_at: str = ""
    status: str = "skipped"  # success | failed | skipped
    result_count: int = 0
    artifact: str = ""
    digest: str = ""
    notes: str = ""
    retained: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)
    source_type: str = "internal_knowledge"
    network_used: bool = False
    executor: str = "wde-core"
    degraded: bool = False
    request_hash: str = ""
    command: str = ""
    exit_code: int | None = None
    artifact_sha256: str = ""
    sealed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def seal(self, artifact_text: str = "") -> "ResearchReceipt":
        """Seal with dual digests.

        ``artifact_text`` MUST be the exact content of the file named in
        ``self.artifact`` (or empty if there is no artifact file). Do not pass
        truncated stdout.
        """
        if not self.executed_at:
            self.executed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        # Always set artifact_sha256 from provided text (may be empty for skips)
        self.artifact_sha256 = compute_artifact_sha256(artifact_text or "")
        # Digest over full metadata including artifact_sha256
        payload = self.to_dict()
        payload.pop("digest", None)
        payload.pop("sealed", None)
        self.digest = compute_receipt_digest(payload)
        self.sealed = True
        return self


def research_dir(root: Path) -> Path:
    return root / ".wde" / "research"


def request_hash(request: str) -> str:
    return sha256_text((request or "").strip())


def write_receipt(root: Path, receipt: ResearchReceipt, *, artifact_text: str = "") -> Path:
    """Seal and write. Prefer write_receipt_from_artifact when a file exists."""
    receipt.seal(artifact_text)
    d = research_dir(root)
    d.mkdir(parents=True, exist_ok=True)
    safe = f"{receipt.path_kind or 'misc'}-{receipt.tool or 'tool'}".replace("/", "-")
    path = d / f"{safe}.json"
    if path.is_file():
        path = d / f"{safe}-{receipt.executed_at.replace(':', '')}.json"
    path.write_text(
        json.dumps(receipt.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def write_receipt_from_artifact(
    root: Path,
    receipt: ResearchReceipt,
    *,
    artifact_relpath: str | None = None,
) -> Path:
    """Seal using the exact on-disk content of receipt.artifact (or artifact_relpath)."""
    rel = artifact_relpath or receipt.artifact
    text = ""
    if rel:
        receipt.artifact = rel.replace("\\", "/")
        art = root / receipt.artifact
        if art.is_file():
            text = art.read_text(encoding="utf-8", errors="replace")
        elif receipt.status == "success":
            # Success without file is inconsistent — mark degraded note
            receipt.notes = (receipt.notes or "") + " | seal: artifact file missing"
            receipt.degraded = True
    return write_receipt(root, receipt, artifact_text=text)


def load_receipts(root: Path) -> list[dict[str, Any]]:
    d = research_dir(root)
    if not d.is_dir():
        return []
    out: list[dict[str, Any]] = []
    skip = {
        "interpretation.json",
        "territories.json",
        "discovery-manifest.json",
        "research-synthesis.json",
        "decision-graph.json",
        "receipt-validation.json",
    }
    for p in sorted(d.glob("*.json")):
        if p.name in skip:
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
    secret: bytes | None = None,
) -> bool:
    """Full integrity check — recomputes digests; never trusts claimed sealed alone."""
    if r.get("sealed") is not True:
        return False
    if r.get("status") not in {"success", "failed", "skipped"}:
        return False
    if not r.get("tool") or not r.get("digest"):
        return False

    executor = str(r.get("executor") or "")
    if executor not in AUTHORIZED_EXECUTORS:
        return False

    if expected_request_hash is not None:
        claimed = r.get("request_hash") or ""
        if claimed and not digests_equal(claimed, expected_request_hash):
            # request_hash is plain sha256_text — compare exact
            if claimed != expected_request_hash:
                return False

    # Recompute artifact_sha256 from disk when possible
    artifact_sha = str(r.get("artifact_sha256") or "")
    if root and r.get("artifact"):
        art = root / str(r["artifact"])
        if art.is_file():
            text = art.read_text(encoding="utf-8", errors="replace")
            recomputed_art = compute_artifact_sha256(text)
            if not digests_equal(recomputed_art, artifact_sha):
                return False
        elif r.get("status") == "success" and r.get("result_count", 0) > 0:
            # Success claiming an artifact that does not exist
            if r.get("artifact"):
                return False
    elif r.get("status") == "success" and not r.get("artifact") and r.get("result_count", 0) < 1:
        if not r.get("notes"):
            return False

    # Recompute receipt digest over claimed metadata with artifact_sha as stored
    # (after we verified artifact matches). Use the dict fields as stored but
    # force artifact_sha256 to the recomputed value when we have it.
    meta = {k: r.get(k) for k in _DIGEST_META_KEYS if k in r or k == "artifact_sha256"}
    if root and r.get("artifact"):
        art = root / str(r["artifact"])
        if art.is_file():
            meta["artifact_sha256"] = compute_artifact_sha256(
                art.read_text(encoding="utf-8", errors="replace")
            )
    expected_digest = compute_receipt_digest(meta, secret=secret)
    if not digests_equal(str(r.get("digest") or ""), expected_digest):
        return False

    return True


def partition_receipts(
    root: Path,
    *,
    expected_request_hash: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Split on-disk receipts into valid / invalid / unavailable tool markers."""
    all_r = load_receipts(root)
    valid: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    unavailable: list[dict[str, Any]] = []
    for r in all_r:
        if r.get("status") in {"skipped", "failed"} and r.get("degraded"):
            # still validate integrity of the skip/fail record
            if receipt_is_valid(r, root=root, expected_request_hash=expected_request_hash):
                unavailable.append(r)
            else:
                invalid.append(r)
            continue
        if receipt_is_valid(r, root=root, expected_request_hash=expected_request_hash):
            valid.append(r)
        else:
            invalid.append(r)
    return {
        "valid_receipts": valid,
        "invalid_receipts": invalid,
        "unavailable_tools": unavailable,
    }


def discovery_receipts_satisfy_research(root: Path) -> tuple[bool, list[str]]:
    """True if discovery left enough valid success receipts."""
    problems: list[str] = []
    parts = partition_receipts(root)
    valid = parts["valid_receipts"]
    if not valid and not parts["unavailable_tools"]:
        return False, ["no receipts under .wde/research/"]
    if len(valid) < 2:
        problems.append(f"need ≥2 valid receipts, found {len(valid)}")
    successes = [r for r in valid if r.get("status") == "success"]
    if not successes:
        problems.append("no receipt with status=success")
    kinds = {r.get("path_kind") for r in valid}
    if not ({"sector", "promax", "visual"} & kinds):
        problems.append("missing sector/visual/promax path_kind among receipts")
    if parts["invalid_receipts"]:
        problems.append(
            f"{len(parts['invalid_receipts'])} invalid/forged receipt(s) rejected"
        )
    return len(problems) == 0, problems


def invalidate_receipts_for_request(root: Path, new_request: str) -> int:
    """Mark receipts stale when the discovery request hash changes."""
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
                r["sealed"] = False  # force re-seal if rewritten properly
                # Do not leave a valid digest for a mutated record
                r["digest"] = ""
                path.write_text(
                    json.dumps(r, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
                n += 1
    return n
