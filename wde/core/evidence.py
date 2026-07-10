"""Evidence envelopes — only wde-core (or registered runners) may create 'passed'.

Local trust model:
- `result_digest` is always recomputed on verify (detects accidental tampering).
- Optional `WDE_EVIDENCE_SECRET` HMAC makes envelopes hard to forge without the secret.
Without a secret / external signer, a fully privileged agent can still re-seal forged
envelopes — we document that as *local* integrity, not absolute non-forgeability.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from wde import __version__
from wde.core.hashing import sha256_text

ALLOWED_EXECUTORS = frozenset({"wde-core", "wde-check", "wde-browser", "wde-v2-bridge"})


def _canonical_payload(ev: dict[str, Any]) -> str:
    payload = {k: v for k, v in ev.items() if k not in {"result_digest", "signature"}}
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def compute_result_digest(ev: dict[str, Any]) -> str:
    return sha256_text(_canonical_payload(ev))


def compute_signature(ev: dict[str, Any], secret: str) -> str:
    digest = ev.get("result_digest") or compute_result_digest(ev)
    return hmac.new(
        secret.encode("utf-8"),
        digest.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


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
    signature: str = ""
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
        """Compute result_digest (+ optional HMAC signature)."""
        self.validate_writer()
        if not self.executed_at:
            self.executed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        # Clear previous seals before hashing
        self.result_digest = ""
        self.signature = ""
        self.result_digest = compute_result_digest(self.to_dict())
        secret = os.environ.get("WDE_EVIDENCE_SECRET", "").strip()
        if secret:
            self.signature = compute_signature(self.to_dict(), secret)
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
    ok, _ = verify_evidence_envelope(ev, expected_source_hash=expected_source_hash)
    return ok


def verify_evidence_envelope(
    ev: dict[str, Any],
    *,
    expected_source_hash: str = "",
    expected_contract_hash: str = "",
    root: Path | None = None,
    require_signature_if_configured: bool = True,
) -> tuple[bool, list[str]]:
    """Full integrity check — never trust executor string alone."""
    reasons: list[str] = []
    if not isinstance(ev, dict):
        return False, ["evidence not an object"]

    if ev.get("status") != "passed":
        reasons.append(f"status is {ev.get('status')!r}, not passed")

    if ev.get("executor") not in ALLOWED_EXECUTORS:
        reasons.append(f"executor not trusted ({ev.get('executor')!r})")

    claimed_digest = str(ev.get("result_digest") or "")
    recomputed = compute_result_digest(ev)
    if not claimed_digest:
        reasons.append("result_digest missing")
    elif claimed_digest != recomputed:
        reasons.append("result_digest mismatch (tampered or hand-written envelope)")

    secret = os.environ.get("WDE_EVIDENCE_SECRET", "").strip()
    if require_signature_if_configured and secret:
        claimed_sig = str(ev.get("signature") or "")
        expected_sig = compute_signature({**ev, "result_digest": recomputed}, secret)
        if not claimed_sig or not hmac.compare_digest(claimed_sig, expected_sig):
            reasons.append("HMAC signature missing or invalid (WDE_EVIDENCE_SECRET set)")

    if expected_source_hash and ev.get("source_hash") != expected_source_hash:
        reasons.append("source_hash mismatch (stale)")

    if expected_contract_hash:
        ch = ev.get("contract_hash") or ""
        if ch and ch != expected_contract_hash:
            reasons.append("contract_hash mismatch")

    if root is not None:
        for art in ev.get("artifacts") or []:
            if not art:
                continue
            p = Path(str(art))
            if not p.is_file():
                p2 = root / str(art)
                if not p2.is_file():
                    reasons.append(f"missing artifact: {art}")

    return len(reasons) == 0, reasons


def rebuild_valid_checks_from_disk(
    evidence_dir: Path,
    *,
    root: Path,
    expected_source_hash: str = "",
    expected_contract_hash: str = "",
) -> tuple[dict[str, str], list[str]]:
    """Reconstruct valid_checks only from envelopes that fully verify."""
    valid: dict[str, str] = {}
    rejected: list[str] = []
    if not evidence_dir.is_dir():
        return valid, rejected
    for path in sorted(evidence_dir.glob("*.json")):
        try:
            ev = load_evidence(path)
        except (OSError, json.JSONDecodeError) as e:
            rejected.append(f"{path.name}: unreadable ({e})")
            continue
        ok, reasons = verify_evidence_envelope(
            ev,
            expected_source_hash=expected_source_hash,
            expected_contract_hash=expected_contract_hash,
            root=root,
        )
        if ok and ev.get("check_id"):
            try:
                rel = str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
            except ValueError:
                rel = str(path).replace("\\", "/")
            valid[str(ev["check_id"])] = rel
        else:
            cid = ev.get("check_id") or path.name
            rejected.append(f"{cid}: {'; '.join(reasons)}")
    return valid, rejected
