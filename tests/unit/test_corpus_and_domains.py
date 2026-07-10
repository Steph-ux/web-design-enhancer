"""12-task corpus + domain audits — drive shipped code."""

from __future__ import annotations

import json
from pathlib import Path

from wde.benchmark.corpus import load_catalog, run_corpus_task
from wde.benchmark.runner import run_benchmark
from wde.domains.forms import audit_forms
from wde.domains.i18n import audit_i18n
from wde.domains.performance import audit_performance
from wde.domains.states import audit_interaction_states


def test_catalog_has_12_tasks():
    cat = load_catalog()
    tasks = cat.get("tasks") or []
    assert len(tasks) == 12
    ids = {t["id"] for t in tasks}
    assert "b2b.technical_landing" in ids
    assert "brief.contradictory" in ids


def test_run_vague_and_contradictory_tasks(tmp_path: Path):
    cat = load_catalog()
    by_id = {t["id"]: t for t in cat["tasks"]}
    vague = run_corpus_task(by_id["brief.vague"], tmp_path / "vague")
    assert vague.procedural.get("intent_ran")
    assert vague.procedural.get("fails_or_flags_vague")

    contra = run_corpus_task(by_id["brief.contradictory"], tmp_path / "contra")
    assert contra.procedural.get("detects_multi_hero") or not contra.quality.get("intent_ok")


def test_forms_and_i18n_domains(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "f.html").write_text(
        """<!doctype html><html lang="en"><body>
        <form><label for="e">Email</label><input id="e" name="e" type="email"/></form>
        </body></html>""",
        encoding="utf-8",
    )
    assert audit_forms(tmp_path)["labels_ok"] is True
    assert audit_i18n(tmp_path)["lang_ok"] is True
    assert audit_interaction_states(tmp_path)["has_error"] is False
    assert "lab_only" in audit_performance(tmp_path)


def test_benchmark_corpus_flag_runs_multiple(tmp_path: Path):
    # single corpus task via runner API
    report = run_benchmark(task_ids=["brief.vague"], keep_dir=tmp_path / "b", corpus=True)
    assert report["authorizes_delivery"] is False
    assert report["kind"] == "benchmark_corpus"
    assert report["tasks"][0]["task_id"] == "brief.vague"
