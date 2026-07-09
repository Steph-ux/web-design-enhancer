# tests/test_skill_packaging.py
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def test_skill_description_has_no_gate_inventory():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    # YAML description should not list "10 sequential" style workflow dump
    fm = re.match(r"^---\n(.*?)\n---", text, re.S)
    assert fm, "missing frontmatter"
    desc = fm.group(1)
    assert "10 sequential" not in desc
    assert "Use when" in desc or "use when" in desc.lower()


def test_skill_points_to_vision_playwright():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "vision-playwright.md" in text


def test_workflow_files_exist():
    for name in ("01-intent.md", "02-contract.md", "03-implement.md", "04-gates.md"):
        p = ROOT / "references" / "workflows" / name
        assert p.is_file() and p.stat().st_size > 200, f"{name} missing or stub-sized"


def test_eyes_script_exists():
    assert (ROOT / "scripts" / "eyes_checklist.py").is_file()
