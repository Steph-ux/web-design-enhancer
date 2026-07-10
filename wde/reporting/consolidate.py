"""Consolidate latest .wde/reports + evidence into a single project report."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def collect_report_files(reports_dir: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not reports_dir.is_dir():
        return out
    for p in sorted(reports_dir.rglob("*.json")):
        if p.name == "consolidated.json":
            continue
        data = _load_json(p)
        if data is None:
            continue
        out.append(
            {
                "path": str(p).replace("\\", "/"),
                "name": p.name,
                "data": data,
            }
        )
    return out


def collect_evidence(evidence_dir: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not evidence_dir.is_dir():
        return out
    for p in sorted(evidence_dir.glob("*.json")):
        data = _load_json(p)
        if not isinstance(data, dict):
            continue
        out.append(
            {
                "path": str(p).replace("\\", "/"),
                "check_id": data.get("check_id"),
                "status": data.get("status"),
                "executor": data.get("executor"),
                "source_hash": data.get("source_hash"),
                "executed_at": data.get("executed_at"),
            }
        )
    return out


def build_consolidated(
    *,
    root: Path,
    state: dict[str, Any],
    project: dict[str, Any] | None = None,
) -> dict[str, Any]:
    wde = root / ".wde"
    reports = collect_report_files(wde / "reports")
    evidence = collect_evidence(wde / "evidence")
    phase = state.get("phase", "UNINITIALIZED")
    blockers = state.get("blockers") or []
    hashes = state.get("hashes") or {}
    # Recompute authority from disk — do not trust state.valid_checks alone
    from wde.core.evidence import rebuild_valid_checks_from_disk, verify_evidence_envelope

    rebuilt, rejected = rebuild_valid_checks_from_disk(
        wde / "evidence",
        root=root,
        expected_source_hash=hashes.get("SOURCE", ""),
        expected_contract_hash=hashes.get("DESIGN", ""),
    )
    valid = rebuilt
    forged_ready = phase == "READY_TO_DELIVER" and (
        not valid or "review.independent" not in valid or "slop.static" not in valid
    )
    untrusted = []
    for e in evidence:
        if e.get("status") != "passed":
            continue
        ok, reasons = verify_evidence_envelope(
            e,
            expected_source_hash=hashes.get("SOURCE", ""),
            expected_contract_hash=hashes.get("DESIGN", ""),
            root=root,
        )
        if not ok:
            untrusted.append({"check_id": e.get("check_id"), "reasons": reasons})
    return {
        "schema_version": "3.0",
        "kind": "consolidated_report",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "root": str(root).replace("\\", "/"),
        "project_id": (project or {}).get("project_id"),
        "phase": phase,
        "next_action": state.get("next_action"),
        "valid_checks": valid,
        "invalidated_checks": state.get("invalidated_checks") or [],
        "blockers": blockers,
        "hashes": hashes,
        "degraded_mode": bool(state.get("degraded_mode")),
        "evidence_index": evidence,
        "report_index": [{"path": r["path"], "name": r["name"]} for r in reports],
        "reports": reports,
        "integrity": {
            "forged_ready_without_checks": forged_ready,
            "untrusted_passed_evidence": untrusted,
            "rejected_envelopes": rejected[:20],
            "delivery_safe": (
                phase != "READY_TO_DELIVER"
                or (
                    bool(valid)
                    and not forged_ready
                    and not untrusted
                    and "review.independent" in valid
                )
            ),
        },
    }


def write_consolidated_human(path: Path, report: dict[str, Any]) -> Path:
    lines = [
        f"# WDE consolidated report",
        f"",
        f"Generated: {report.get('generated_at')}",
        f"Phase: {report.get('phase')}",
        f"Project: {report.get('project_id')}",
        f"",
        f"## Next action",
        f"{(report.get('next_action') or {}).get('summary', 'n/a')}",
        f"Command: `{(report.get('next_action') or {}).get('command', '')}`",
        f"",
        f"## Integrity",
        f"- forged_ready_without_checks: {report.get('integrity', {}).get('forged_ready_without_checks')}",
        f"- delivery_safe: {report.get('integrity', {}).get('delivery_safe')}",
        f"- untrusted_passed_evidence: {len(report.get('integrity', {}).get('untrusted_passed_evidence') or [])}",
        f"",
        f"## Valid checks ({len(report.get('valid_checks') or {})})",
    ]
    for k, v in (report.get("valid_checks") or {}).items():
        lines.append(f"- `{k}` → {v}")
    lines += ["", "## Evidence"]
    for e in report.get("evidence_index") or []:
        lines.append(
            f"- [{e.get('status')}] {e.get('check_id')} executor={e.get('executor')} ({e.get('path')})"
        )
    lines += ["", "## Report files"]
    for r in report.get("report_index") or []:
        lines.append(f"- {r.get('name')}: {r.get('path')}")
    if report.get("blockers"):
        lines += ["", "## Blockers"]
        for b in report["blockers"]:
            if isinstance(b, dict):
                lines.append(f"- [{b.get('code')}] {b.get('message')}")
            else:
                lines.append(f"- {b}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_consolidated(root: Path, state: dict[str, Any], project: dict[str, Any] | None = None) -> dict[str, Path]:
    report = build_consolidated(root=root, state=state, project=project)
    out_dir = root / ".wde" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "consolidated.json"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path = write_consolidated_human(out_dir / "consolidated.md", report)
    return {"json": json_path, "md": md_path, "report": report}  # type: ignore[dict-item]
