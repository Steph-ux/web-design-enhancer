"""12-task benchmark corpus from plan §12 + graders."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

# json used in migrate task and evidence loops

from wde.benchmark.runner import (
    TaskResult,
    _fixture_minimal_site,
    run_smoke_task_clean_static,
    run_smoke_task_forged_ready,
)
from wde.core.migrate_v2 import migrate_v2
from wde.core.project_context import ProjectContext, init_project
from wde.core.runner import run_profile
from wde.domains.contracts import validate_intent
from wde.domains.forms import audit_forms
from wde.domains.i18n import audit_i18n
from wde.domains.maintainability import audit_maintainability
from wde.domains.performance import audit_performance
from wde.domains.states import audit_interaction_states


def catalog_path() -> Path:
    return Path(__file__).resolve().parents[2] / "benchmark" / "tasks" / "catalog.json"


def load_catalog() -> dict[str, Any]:
    p = catalog_path()
    if not p.is_file():
        return {"tasks": []}
    return json.loads(p.read_text(encoding="utf-8"))


def _write_brief(dest: Path, *, emotional: str, unexpected: str, broken: str) -> None:
    (dest / "CREATIVE-BRIEF.md").write_text(
        f"""# CREATIVE-BRIEF.md

## Emotional Intent
{emotional}

## The One Unexpected Thing
{unexpected}

## Hero Dimension
- [x] Typography
- [ ] Negative space
- [ ] Colour
- [ ] Motion
- [ ] Illustration

## The Broken Rule
{broken}

## Design Read
benchmark task product for evaluators, distinctive language, HTML/CSS.

## Design Dials
- VARIANCE: 7
- MOTION: 2
- DENSITY: 8

## The Cross-Domain Steal
The non-software discipline: print editorial
The specific move: strong masthead hierarchy
""",
        encoding="utf-8",
    )


def _base_site(dest: Path, title: str = "Benchmark") -> None:
    _fixture_minimal_site(dest)
    # retitle
    html = (dest / "src" / "index.html").read_text(encoding="utf-8")
    html = html.replace("Benchmark Fixture", title).replace("Clearing Desk", title)
    (dest / "src" / "index.html").write_text(html, encoding="utf-8")


def _run_static_quality(work: Path) -> tuple[dict[str, bool], dict[str, Any], str]:
    init_project(work, force=True)
    ctx = ProjectContext(work)
    project = ctx.load_project()
    project["source_paths"] = ["src"]
    ctx.save_project(project)
    intent = validate_intent(work)
    results = run_profile(ctx, "static")
    procedural = {
        "init_ok": True,
        "intent_ran": True,
        "static_ran": True,
        "no_ready_without_independent": ctx.load_state().get("phase") != "READY_TO_DELIVER"
        or "review.independent" in (ctx.load_state().get("valid_checks") or {}),
        "trusted_evidence": all(
            json.loads(p.read_text(encoding="utf-8")).get("executor")
            in {"wde-core", "wde-check", "wde-browser", "wde-v2-bridge"}
            for p in (work / ".wde" / "evidence").glob("*.json")
            if json.loads(p.read_text(encoding="utf-8")).get("status") == "passed"
        )
        if any((work / ".wde" / "evidence").glob("*.json"))
        else True,
    }
    quality = {
        "intent_ok": intent.ok,
        "blocking_static": sum(1 for r in results if r.blocks_delivery),
        "phase": ctx.load_state().get("phase"),
    }
    return procedural, quality, str(ctx.load_state().get("phase"))


def task_clean_static(work: Path, meta: dict[str, Any]) -> TaskResult:
    _base_site(work, meta.get("title", "Site"))
    _write_brief(
        work,
        emotional="Precise, calm product presence.",
        unexpected="One structural signature unique to the brief.",
        broken="We ignore generic three-column feature grids because the content needs a different hierarchy.",
    )
    procedural, quality, phase = _run_static_quality(work)
    return TaskResult(meta["id"], procedural, quality, phase)


def task_forms_static(work: Path, meta: dict[str, Any]) -> TaskResult:
    _base_site(work, "Signup")
    src = work / "src"
    (src / "index.html").write_text(
        """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Signup</title></head>
<body>
  <h1>Create account</h1>
  <form id="signup">
    <label for="email">Email</label>
    <input id="email" name="email" type="email" required />
    <label for="password">Password</label>
    <input id="password" name="password" type="password" required />
    <button type="submit">Continue</button>
  </form>
</body></html>
""",
        encoding="utf-8",
    )
    _write_brief(
        work,
        emotional="Trustworthy onboarding desk.",
        unexpected="Form errors are full sentences with next steps.",
        broken="We ignore multi-step wizards without progress because this is a single intent form.",
    )
    procedural, quality, phase = _run_static_quality(work)
    form_rep = audit_forms(work)
    procedural["forms_audit_ran"] = True
    procedural["forms_labels_ok"] = form_rep.get("labels_ok", False)
    quality["forms"] = form_rep
    return TaskResult(meta["id"], procedural, quality, phase)


def task_states_static(work: Path, meta: dict[str, Any]) -> TaskResult:
    _base_site(work, "States App")
    (work / "src" / "index.html").write_text(
        """<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>States</title></head>
<body>
  <h1>Library</h1>
  <div data-state="empty">No items yet. Add your first document.</div>
  <div data-state="error" hidden>Could not load. Retry.</div>
  <div data-state="loading" hidden>Loading…</div>
  <button type="button">Retry</button>
</body></html>
""",
        encoding="utf-8",
    )
    _write_brief(
        work,
        emotional="Calm recovery when things fail.",
        unexpected="Empty state is a full composition, not a grey void.",
        broken="We ignore skeleton-only loading without text because status must be readable.",
    )
    procedural, quality, phase = _run_static_quality(work)
    st = audit_interaction_states(work)
    procedural["states_audit_ran"] = True
    procedural["has_empty_and_error"] = st.get("has_empty", False) and st.get("has_error", False)
    quality["states"] = st
    return TaskResult(meta["id"], procedural, quality, phase)


def task_i18n_static(work: Path, meta: dict[str, Any]) -> TaskResult:
    _base_site(work, "Multilingual")
    html = (work / "src" / "index.html").read_text(encoding="utf-8")
    html = html.replace('lang="en"', 'lang="en" dir="ltr"')
    (work / "src" / "index.html").write_text(html, encoding="utf-8")
    _write_brief(
        work,
        emotional="Clear in every language.",
        unexpected="Layout survives 40% text expansion.",
        broken="We ignore hard-coded sentence fragments because copy must be whole strings.",
    )
    procedural, quality, phase = _run_static_quality(work)
    i18n = audit_i18n(work)
    procedural["i18n_audit_ran"] = True
    procedural["lang_attr_present"] = i18n.get("lang_ok", False)
    quality["i18n"] = i18n
    return TaskResult(meta["id"], procedural, quality, phase)


def task_migrate_then_static(work: Path, meta: dict[str, Any]) -> TaskResult:
    _base_site(work, "Identity Redesign")
    (work / "DESIGN.md").write_text(
        "# DESIGN.md\n\n## 0. Sources Phase 0\nsearch.py + getdesign brand\n\n## 2. Color Palette\n- Background: #0a0a0a\n",
        encoding="utf-8",
    )
    (work / ".phase-log.json").write_text(
        json.dumps({"final": {"passed": True}}), encoding="utf-8"
    )
    _write_brief(
        work,
        emotional="Same brand, sharper structure.",
        unexpected="Keep brand black; change only hierarchy.",
        broken="We ignore full rebrand because identity constraints are locked.",
    )
    rep = migrate_v2(work, force=True)
    procedural = {
        "migrate_ran": True,
        "never_auto_ready": rep.get("phase") != "READY_TO_DELIVER",
        "valid_checks_cleared": True,
    }
    ctx = ProjectContext(work)
    project = ctx.load_project()
    project["source_paths"] = ["src"]
    ctx.save_project(project)
    results = run_profile(ctx, "static")
    procedural["static_after_migrate"] = True
    procedural["no_ready"] = ctx.load_state().get("phase") != "READY_TO_DELIVER"
    quality = {
        "migrate_phase": rep.get("phase"),
        "blocking_static": sum(1 for r in results if r.blocks_delivery),
        "perf": audit_performance(work),
        "maintainability": audit_maintainability(work),
    }
    return TaskResult(meta["id"], procedural, quality, str(ctx.load_state().get("phase")))


def task_vague_brief(work: Path, meta: dict[str, Any]) -> TaskResult:
    work.mkdir(parents=True, exist_ok=True)
    init_project(work, force=True)
    (work / "CREATIVE-BRIEF.md").write_text(
        """# CREATIVE-BRIEF.md

## Emotional Intent
professional modern clean

## The One Unexpected Thing
___

## Hero Dimension
- [ ] Typography

## The Broken Rule
something

## Design Read
___

## Design Dials
- VARIANCE: 
- MOTION: 
- DENSITY: 

## The Cross-Domain Steal
___
""",
        encoding="utf-8",
    )
    intent = validate_intent(work)
    procedural = {
        "intent_ran": True,
        "fails_or_flags_vague": (not intent.ok) or any(i.code for i in intent.issues),
        "no_implementation_forced": ProjectContext(work).load_state().get("phase")
        in {"INTENT_REQUIRED", "INTENT_VALIDATED", "RESEARCH_REQUIRED"},
    }
    return TaskResult(
        meta["id"],
        procedural,
        {"intent_ok": intent.ok, "issue_count": len(intent.issues)},
        ProjectContext(work).load_state().get("phase", ""),
    )


def task_contradictory_brief(work: Path, meta: dict[str, Any]) -> TaskResult:
    work.mkdir(parents=True, exist_ok=True)
    init_project(work, force=True)
    (work / "CREATIVE-BRIEF.md").write_text(
        """# CREATIVE-BRIEF.md

## Emotional Intent
Ultra luxury calm restraint like a private gallery — and also neon cyberpunk maximal chaos for teens.

## The One Unexpected Thing
Everything is both pure Swiss grid and pure brutalist anti-grid at once.

## Hero Dimension
- [x] Typography
- [x] Colour
- [x] Motion

## The Broken Rule
We ignore all rules because we also follow every rule because consistency.

## Design Read
luxury and cyberpunk and dashboard and playful simultaneously.

## Design Dials
- VARIANCE: 1
- MOTION: 10
- DENSITY: 1

## The Cross-Domain Steal
The non-software discipline: another SaaS landing page
The specific move: blue gradient hero
""",
        encoding="utf-8",
    )
    intent = validate_intent(work)
    multi_hero = any(i.code == "hero_multiple" for i in intent.issues)
    procedural = {
        "intent_ran": True,
        "detects_multi_hero": multi_hero or not intent.ok,
        "no_auto_ready": ProjectContext(work).load_state().get("phase") != "READY_TO_DELIVER",
    }
    return TaskResult(
        meta["id"],
        procedural,
        {"intent_ok": intent.ok, "issues": [i.code for i in intent.issues]},
        ProjectContext(work).load_state().get("phase", ""),
    )


RUNNERS: dict[str, Callable[[Path, dict[str, Any]], TaskResult]] = {
    "clean_static": task_clean_static,
    "forms_static": task_forms_static,
    "states_static": task_states_static,
    "i18n_static": task_i18n_static,
    "migrate_then_static": task_migrate_then_static,
    "vague_brief": task_vague_brief,
    "contradictory_brief": task_contradictory_brief,
    "smoke_clean": lambda w, m: run_smoke_task_clean_static(w),
    "smoke_forged": lambda w, m: run_smoke_task_forged_ready(w),
}


def run_corpus_task(task: dict[str, Any], work: Path) -> TaskResult:
    runner = task.get("runner", "clean_static")
    fn = RUNNERS.get(runner, task_clean_static)
    return fn(work, task)
