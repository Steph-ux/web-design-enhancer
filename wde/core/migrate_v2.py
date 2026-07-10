"""Import a V2-era project into .wde without marking ready-to-deliver."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from wde.core.project_context import ProjectContext, default_project, init_project
from wde.core.state_machine import initial_state


def migrate_v2(root: Path, *, force: bool = False) -> dict[str, Any]:
    root = root.resolve()
    ctx = ProjectContext(root)
    report: dict[str, Any] = {
        "migrated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "root": str(root),
        "found": {},
        "actions": [],
        "warnings": [],
    }

    found = {
        "CREATIVE-BRIEF.md": (root / "CREATIVE-BRIEF.md").is_file(),
        "DESIGN.md": (root / "DESIGN.md").is_file(),
        "structural-lock.md": (root / "structural-lock.md").is_file()
        or (root / "STRUCTURAL-LOCK.md").is_file(),
        "EXPERIENCE-CONTRACT.md": (root / "EXPERIENCE-CONTRACT.md").is_file(),
        ".phase-log.json": (root / ".phase-log.json").is_file(),
        "audit-results": (root / "audit-results").is_dir(),
        "design-system-output": bool(list(root.glob("design-system-output*.md")))
        or bool(list(root.glob("design-system/**/MASTER.md"))),
        "getdesign": bool(list(root.glob("getdesign-*.md")))
        or any((p / "DESIGN.md").is_file() for p in root.iterdir() if p.is_dir()),
    }
    report["found"] = found

    if ctx.exists() and not force:
        report["actions"].append("already_initialized")
        report["warnings"].append("Use --force to re-init state (does not delete contracts)")
        return report

    if not ctx.exists() or force:
        if ctx.exists() and force:
            # keep contracts; reset control plane only
            import shutil

            shutil.rmtree(ctx.wde, ignore_errors=True)
        init_project(root, force=True)
        report["actions"].append("wde_init")

    # Ensure EXPERIENCE stub if missing
    exp = root / "EXPERIENCE-CONTRACT.md"
    if not exp.is_file():
        tmpl = Path(__file__).resolve().parents[2] / "templates" / "experience-contract-template.md"
        if tmpl.is_file():
            exp.write_text(tmpl.read_text(encoding="utf-8"), encoding="utf-8")
            report["actions"].append("wrote_experience_stub")
        else:
            report["warnings"].append("experience template missing")

    # Normalize structural lock name note
    if (root / "structural-lock.md").is_file() and not (root / "STRUCTURAL-LOCK.md").is_file():
        report["warnings"].append(
            "Found structural-lock.md (V2 name). V3 accepts both; optional rename to STRUCTURAL-LOCK.md"
        )

    # Import phase-log as historical ONLY — never trust as ready
    phase_log = root / ".phase-log.json"
    state = ctx.load_state()
    if phase_log.is_file():
        try:
            pl = json.loads(phase_log.read_text(encoding="utf-8"))
            report["actions"].append("read_phase_log")
            report["v2_phase_log_keys"] = list(pl.keys())
            report["warnings"].append(
                "V2 .phase-log.json imported as historical metadata only — "
                "all checks must be re-run; project is NOT ready to deliver"
            )
            state.setdefault("history", []).append(
                {
                    "at": report["migrated_at"],
                    "from_phase": "UNINITIALIZED",
                    "to_phase": state.get("phase", "INTENT_REQUIRED"),
                    "via": "migrate-v2",
                    "evidence_id": "historical-untrusted",
                }
            )
        except json.JSONDecodeError:
            report["warnings"].append("unreadable .phase-log.json")

    # Never set READY_TO_DELIVER
    if state.get("phase") == "READY_TO_DELIVER":
        state = initial_state()
        report["warnings"].append("Reset READY_TO_DELIVER — migrate never authorizes delivery")

    # Heuristic phase based on files (still not delivery)
    if found["CREATIVE-BRIEF.md"] and state["phase"] == "INTENT_REQUIRED":
        report["suggested_next"] = "wde validate intent"
    if found["DESIGN.md"]:
        report["suggested_next"] = "wde validate design && wde validate lock"
    if found["audit-results"]:
        report["warnings"].append(
            "audit-results/ present but treated as stale until re-run under V3 evidence schema"
        )

    state["valid_checks"] = {}  # force re-proof
    state["invalidated_checks"] = ["*migrated*"]
    ctx.save_state(state)
    report["phase"] = state["phase"]
    report["actions"].append("cleared_valid_checks")
    return report
