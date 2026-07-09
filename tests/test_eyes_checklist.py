"""eyes_checklist.py — verify Eyes artifacts before delivery claims."""
from pathlib import Path
import json
import sys

import pytest

# Allow importing scripts/
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from eyes_checklist import check_eyes_artifacts  # noqa: E402


def test_missing_dir_returns_error(tmp_path: Path):
    errs = check_eyes_artifacts(tmp_path / "nope")
    assert any("missing" in e.lower() or "not found" in e.lower() for e in errs)


def test_pass_when_minimum_artifacts_present(tmp_path: Path):
    audit = tmp_path / "audit-results"
    mcp = audit / "mcp"
    mcp.mkdir(parents=True)
    (mcp / "mobile.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (mcp / "desktop.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (audit / "audit_report.json").write_text(
        json.dumps({"screenshots": {"mobile": "x", "desktop": "y"}, "ai_slop_detected": []}),
        encoding="utf-8",
    )
    (audit / "aesthetic-verdict.json").write_text(
        json.dumps({
            "overall_score": 82,
            "reads_as": "human",
            "reviewer": "independent-clone",
            "memorable_idea": "Champagne hairline as sole accent",
        }),
        encoding="utf-8",
    )
    assert check_eyes_artifacts(audit) == []


def test_fail_when_no_mcp_screenshots(tmp_path: Path):
    audit = tmp_path / "audit-results"
    audit.mkdir()
    (audit / "audit_report.json").write_text("{}", encoding="utf-8")
    (audit / "aesthetic-verdict.json").write_text(
        json.dumps({
            "overall_score": 82,
            "reads_as": "human",
            "reviewer": "independent-clone",
            "memorable_idea": "Something memorable here",
        }),
        encoding="utf-8",
    )
    errs = check_eyes_artifacts(audit)
    assert any("mcp" in e.lower() or "screenshot" in e.lower() for e in errs)


def test_fail_when_self_reviewer(tmp_path: Path):
    audit = tmp_path / "audit-results"
    mcp = audit / "mcp"
    mcp.mkdir(parents=True)
    (mcp / "mobile.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (audit / "audit_report.json").write_text("{}", encoding="utf-8")
    (audit / "aesthetic-verdict.json").write_text(
        json.dumps({
            "overall_score": 90,
            "reads_as": "human",
            "reviewer": "self",
            "memorable_idea": "Something memorable here",
        }),
        encoding="utf-8",
    )
    errs = check_eyes_artifacts(audit)
    assert any("provenance" in e.lower() or "self" in e.lower() for e in errs)
