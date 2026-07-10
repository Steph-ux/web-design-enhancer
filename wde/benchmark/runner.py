"""Run a small fixed task corpus; score procedural compliance vs result quality.

Does NOT auto-authorize READY_TO_DELIVER.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from wde.core.project_context import ProjectContext, init_project
from wde.core.runner import deliver_check, run_profile
from wde.domains.contracts import validate_intent
from wde.reporting.consolidate import build_consolidated


@dataclass
class TaskResult:
    task_id: str
    procedural: dict[str, bool] = field(default_factory=dict)
    quality: dict[str, Any] = field(default_factory=dict)
    phase: str = ""
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _fixture_minimal_site(dest: Path) -> None:
    """Write a minimal clean static site used by smoke tasks."""
    src = dest / "src"
    src.mkdir(parents=True, exist_ok=True)
    (src / "index.html").write_text(
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Benchmark Fixture</title>
  <link rel="stylesheet" href="styles.css" />
</head>
<body>
  <header>
    <h1>Clearing Desk</h1>
    <p class="lede">Instrument catalogue — no lifestyle cards.</p>
  </header>
  <main>
    <table class="board-table" role="table">
      <thead><tr><th>CAT</th><th>PRODUCT</th><th>STOCK</th><th>PRICE</th></tr></thead>
      <tbody>
        <tr class="board-row"><td>AI</td><td>Alpha Access</td><td>12</td><td>$9.00</td></tr>
      </tbody>
    </table>
    <button type="button">Order</button>
  </main>
</body>
</html>
""",
        encoding="utf-8",
    )
    (src / "styles.css").write_text(
        """:root { --bg:#0a0a0a; --fg:#fafafa; --accent:#d4a017; }
body { margin:0; font-family: system-ui,sans-serif; background:var(--bg); color:var(--fg); }
h1 { font-size: clamp(2.5rem, 6vw, 4rem); letter-spacing:0.04em; }
.board-table { width:100%; border-collapse: collapse; }
.board-row td { border-top:1px solid #262626; padding:8px; font-variant-numeric: tabular-nums; }
button { min-height:44px; }
""",
        encoding="utf-8",
    )
    (dest / "CREATIVE-BRIEF.md").write_text(
        """# CREATIVE-BRIEF.md

## Emotional Intent
Like a Swiss railway board at dawn — cold precision, no carnival.

## The One Unexpected Thing
Catalogue is a fixed-column invoice board, never product cards.

## Hero Dimension
- [x] Typography
- [ ] Negative space
- [ ] Colour
- [ ] Motion
- [ ] Illustration

## The Broken Rule
We ignore marketplace card grids because digital SKUs are instruments not lifestyle objects.

## Design Read
a benchmark storefront for operators, monochrome invoice language, HTML/CSS only.

## Design Dials
- VARIANCE: 7
- MOTION: 2
- DENSITY: 8

## The Cross-Domain Steal
The non-software discipline: Swiss railway signage
The specific move: fixed columns CAT|PRODUCT|STOCK|PRICE
""",
        encoding="utf-8",
    )


def run_smoke_task_clean_static(work: Path) -> TaskResult:
    """Task: init → validate intent → run static → deliver-check; no ready forge."""
    _fixture_minimal_site(work)
    init_project(work, force=True)
    ctx = ProjectContext(work)
    project = ctx.load_project()
    project["source_paths"] = ["src"]
    ctx.save_project(project)

    procedural: dict[str, bool] = {}
    notes: list[str] = []

    # status after init
    state = ctx.load_state()
    procedural["init_phase_intent"] = state.get("phase") == "INTENT_REQUIRED"
    procedural["no_forged_ready"] = state.get("phase") != "READY_TO_DELIVER"

    intent = validate_intent(work)
    procedural["intent_validate_ran"] = True
    procedural["intent_structurally_ok"] = intent.ok or not any(
        i.code in {"missing_section", "unfilled"} for i in intent.issues
    )

    results = run_profile(ctx, "static")
    procedural["static_ran"] = True
    procedural["evidence_written"] = any(
        (work / ".wde" / "evidence").glob("*.json")
    )
    # All sealed evidence must be wde-core if present
    trusted = True
    for p in (work / ".wde" / "evidence").glob("*.json"):
        data = json.loads(p.read_text(encoding="utf-8"))
        if data.get("status") == "passed" and data.get("executor") not in {
            "wde-core",
            "wde-check",
            "wde-browser",
            "wde-v2-bridge",
        }:
            trusted = False
    procedural["evidence_trusted_executor"] = trusted

    ok, blockers, _ = deliver_check(ctx)
    state2 = ctx.load_state()
    procedural["deliver_check_ran"] = True
    procedural["never_silent_ready"] = state2.get("phase") != "READY_TO_DELIVER" or (
        "review.independent" in (state2.get("valid_checks") or {})
    )
    if state2.get("phase") == "READY_TO_DELIVER" and not (state2.get("valid_checks") or {}):
        procedural["never_silent_ready"] = False

    quality = {
        "static_blocking_failures": sum(1 for r in results if r.blocks_delivery),
        "deliver_ok_mechanical": ok,
        "blocker_count": len(blockers),
        "phase": state2.get("phase"),
    }
    if not procedural["evidence_trusted_executor"]:
        notes.append("untrusted evidence executor detected")
    return TaskResult(
        task_id="smoke.clean_static",
        procedural=procedural,
        quality=quality,
        phase=str(state2.get("phase")),
        notes=notes,
    )


def run_smoke_task_forged_ready(work: Path) -> TaskResult:
    """Task: hand-edit READY without checks → doctor / consolidated integrity fails."""
    _fixture_minimal_site(work)
    init_project(work, force=True)
    ctx = ProjectContext(work)
    state = ctx.load_state()
    state["phase"] = "READY_TO_DELIVER"
    state["valid_checks"] = {}
    ctx.save_state(state)
    issues = ctx.doctor()
    consolidated = build_consolidated(root=work, state=ctx.load_state(), project=ctx.load_project())
    procedural = {
        "forged_ready_detected_by_doctor": any(i["code"] == "forged_delivery" for i in issues),
        "consolidated_flags_forged": consolidated["integrity"]["forged_ready_without_checks"] is True,
        "delivery_not_safe": consolidated["integrity"]["delivery_safe"] is False,
    }
    return TaskResult(
        task_id="smoke.forged_ready",
        procedural=procedural,
        quality={"doctor_issues": len(issues)},
        phase=ctx.load_state().get("phase", ""),
        notes=[],
    )


TASKS = {
    "smoke.clean_static": run_smoke_task_clean_static,
    "smoke.forged_ready": run_smoke_task_forged_ready,
}


def score_procedural(results: list[TaskResult]) -> dict[str, Any]:
    flags: list[bool] = []
    for tr in results:
        flags.extend(bool(v) for v in tr.procedural.values())
    passed = sum(1 for f in flags if f)
    total = len(flags) or 1
    return {
        "passed_flags": passed,
        "total_flags": total,
        "rate": round(passed / total, 4),
    }


def run_benchmark(
    *,
    task_ids: list[str] | None = None,
    keep_dir: Path | None = None,
    corpus: bool = False,
) -> dict[str, Any]:
    """Run smoke tasks by default; corpus=True runs full 12-task catalog."""
    from wde.benchmark.corpus import load_catalog, run_corpus_task

    results: list[TaskResult] = []
    work_root = keep_dir or Path(tempfile.mkdtemp(prefix="wde-bench-"))
    work_root.mkdir(parents=True, exist_ok=True)

    if corpus:
        catalog = load_catalog()
        tasks_meta = catalog.get("tasks") or []
        if task_ids:
            tasks_meta = [t for t in tasks_meta if t.get("id") in task_ids]
        for meta in tasks_meta:
            tid = meta.get("id", "unknown")
            task_dir = work_root / tid.replace(".", "_")
            if task_dir.exists():
                shutil.rmtree(task_dir)
            task_dir.mkdir(parents=True)
            results.append(run_corpus_task(meta, task_dir))
        kind = "benchmark_corpus"
        note = "12-task corpus (lab/static procedural); multi-model medians still external"
    else:
        ids = task_ids or list(TASKS.keys())
        for tid in ids:
            fn = TASKS.get(tid)
            if not fn:
                # allow corpus ids without --corpus for convenience
                from wde.benchmark.corpus import load_catalog, run_corpus_task

                meta = next((t for t in (load_catalog().get("tasks") or []) if t.get("id") == tid), None)
                task_dir = work_root / tid.replace(".", "_")
                if task_dir.exists():
                    shutil.rmtree(task_dir)
                task_dir.mkdir(parents=True)
                if meta:
                    results.append(run_corpus_task(meta, task_dir))
                else:
                    results.append(TaskResult(task_id=tid, notes=[f"unknown task {tid}"]))
                continue
            task_dir = work_root / tid.replace(".", "_")
            if task_dir.exists():
                shutil.rmtree(task_dir)
            task_dir.mkdir(parents=True)
            results.append(fn(task_dir))
        kind = "benchmark_smoke"
        note = "Smoke tasks only; use --corpus for full 12-task catalog"

    report = {
        "schema_version": "3.0",
        "kind": kind,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tasks": [r.to_dict() for r in results],
        "procedural_score": score_procedural(results),
        "quality_summary": {
            "note": note,
            "per_task": {r.task_id: r.quality for r in results},
        },
        "authorizes_delivery": False,
        "work_root": str(work_root).replace("\\", "/"),
    }
    return report
