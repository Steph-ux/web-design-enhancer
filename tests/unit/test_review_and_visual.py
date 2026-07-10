"""Visual review package + aesthetic independence anti-bypass."""

from __future__ import annotations

import json
from pathlib import Path

from wde.checks.visual.aesthetic import AestheticVerdictCheck
from wde.core.project_context import ProjectContext, init_project
from wde.core.review import emit_review_package
from wde.core.state_machine import apply_transition
from wde.runners.browser_runner import probe_url


def test_probe_url_localhost_may_fail_without_server():
    r = probe_url("http://127.0.0.1:9/", timeout=0.5)
    assert r.ok is False


def test_emit_review_package_writes_files(tmp_path: Path):
    init_project(tmp_path)
    ctx = ProjectContext(tmp_path)
    out = emit_review_package(ctx, url="http://127.0.0.1:9/", run_audit=False)
    assert Path(out["package_path"]).is_file()
    assert Path(out["prompt_path"]).is_file()
    pkg = json.loads(Path(out["package_path"]).read_text(encoding="utf-8"))
    assert "rubric_dimensions" in pkg
    assert "do_not" in pkg["instructions"]


def test_aesthetic_rejects_self_reviewer(tmp_path: Path):
    init_project(tmp_path)
    audit = tmp_path / "audit-results"
    audit.mkdir()
    (audit / "aesthetic-verdict.json").write_text(
        json.dumps(
            {
                "reviewer": "self",
                "overall_score": 95,
                "reads_as": "human",
                "memorable_idea": "A champagne hairline under the header",
            }
        ),
        encoding="utf-8",
    )
    check = AestheticVerdictCheck()
    result = check.run({"root": tmp_path})
    assert result.status == "failed"
    assert any(f.rule_id == "PROVENANCE" for f in result.findings)


def test_aesthetic_accepts_independent_clone(tmp_path: Path):
    init_project(tmp_path)
    audit = tmp_path / "audit-results"
    audit.mkdir()
    (audit / "aesthetic-verdict.json").write_text(
        json.dumps(
            {
                "reviewer": "independent-clone",
                "overall_score": 78,
                "reads_as": "human",
                "memorable_idea": "Departure-board catalogue columns with gold rule",
                "dimensions": {
                    "composition": {"score": 80, "evidence": "fixed columns visible"},
                },
            }
        ),
        encoding="utf-8",
    )
    result = AestheticVerdictCheck().run({"root": tmp_path})
    assert result.status == "passed"
    assert result.details.get("independence") == "medium"


def test_aesthetic_rejects_reads_as_ai(tmp_path: Path):
    init_project(tmp_path)
    audit = tmp_path / "audit-results"
    audit.mkdir()
    (audit / "aesthetic-verdict.json").write_text(
        json.dumps(
            {
                "reviewer": "human",
                "overall_score": 80,
                "reads_as": "ai",
                "memorable_idea": "Something memorable enough here",
            }
        ),
        encoding="utf-8",
    )
    result = AestheticVerdictCheck().run({"root": tmp_path})
    assert result.status == "failed"
    assert any(f.rule_id == "READS-AI" for f in result.findings)


def test_manual_state_ready_without_checks_flagged_by_doctor(tmp_path: Path):
    init_project(tmp_path)
    ctx = ProjectContext(tmp_path)
    state = ctx.load_state()
    state["phase"] = "READY_TO_DELIVER"
    state["valid_checks"] = {}
    ctx.save_state(state)
    issues = ctx.doctor()
    assert any(i["code"] == "forged_delivery" for i in issues)
