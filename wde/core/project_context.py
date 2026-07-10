"""Load/save .wde project control plane."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from wde.core.hashing import hash_contract_files, hash_source_tree
from wde.core.invalidation import apply_invalidation, diff_hashes
from wde.core.state_machine import initial_state, next_action_for

WDE_DIR = ".wde"
STATE_FILE = "state.json"
PROJECT_FILE = "project.json"
CAPABILITIES_FILE = "capabilities.json"


class ProjectContext:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.wde = self.root / WDE_DIR

    @property
    def state_path(self) -> Path:
        return self.wde / STATE_FILE

    @property
    def project_path(self) -> Path:
        return self.wde / PROJECT_FILE

    def exists(self) -> bool:
        return self.project_path.is_file() and self.state_path.is_file()

    def load_project(self) -> dict[str, Any]:
        return json.loads(self.project_path.read_text(encoding="utf-8"))

    def load_state(self) -> dict[str, Any]:
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def save_state(self, state: dict[str, Any]) -> None:
        self.wde.mkdir(parents=True, exist_ok=True)
        # Never trust agent-edited READY_TO_DELIVER without core path — still write what we give it
        self.state_path.write_text(
            json.dumps(state, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def save_project(self, project: dict[str, Any]) -> None:
        self.wde.mkdir(parents=True, exist_ok=True)
        self.project_path.write_text(
            json.dumps(project, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def compute_hashes(self, project: dict[str, Any] | None = None) -> dict[str, str]:
        project = project or self.load_project()
        hashes = hash_contract_files(self.root)
        sources = project.get("source_paths") or ["."]
        hashes["SOURCE"] = hash_source_tree(sources, self.root)
        return hashes

    def refresh_invalidation(self, state: dict[str, Any] | None = None) -> dict[str, Any]:
        """Recompute hashes; drop stale valid_checks; may dirty IMPLEMENTATION_*."""
        state = dict(state or self.load_state())
        project = self.load_project()
        new_hashes = self.compute_hashes(project)
        old_hashes = dict(state.get("hashes") or {})
        changed = diff_hashes(old_hashes, new_hashes)
        valid = dict(state.get("valid_checks") or {})
        if changed:
            valid, invalidated = apply_invalidation(valid, changed)
            prev_inv = list(state.get("invalidated_checks") or [])
            for i in invalidated:
                if i not in prev_inv:
                    prev_inv.append(i)
            state["valid_checks"] = valid
            state["invalidated_checks"] = prev_inv
            state["hashes"] = new_hashes
            # Source change dirties delivery phases
            if "SOURCE" in changed and state.get("phase") in {
                "IMPLEMENTATION_ALLOWED",
                "MECHANICAL_REVIEW_REQUIRED",
                "VISUAL_REVIEW_REQUIRED",
                "INDEPENDENT_REVIEW_REQUIRED",
                "READY_TO_DELIVER",
            }:
                from wde.core.state_machine import apply_transition

                try:
                    state = apply_transition(state, "IMPLEMENTATION_DIRTY")
                except ValueError:
                    state["phase"] = "IMPLEMENTATION_DIRTY"
                    state["next_action"] = next_action_for("IMPLEMENTATION_DIRTY").to_dict()
        else:
            state["hashes"] = new_hashes
        state["next_action"] = next_action_for(state["phase"]).to_dict()
        return state

    def detect_capabilities(self) -> dict[str, bool]:
        caps = {
            "python": True,
            "node": (self.root / "package.json").is_file(),
            "playwright_python": _module_available("playwright"),
            "browser": False,
            "mcp_playwright": False,
        }
        caps["browser"] = caps["playwright_python"]
        return caps

    def doctor(self) -> list[dict[str, str]]:
        issues: list[dict[str, str]] = []
        if not self.exists():
            issues.append(
                {
                    "code": "not_initialized",
                    "message": "No .wde/ project — run: wde init",
                    "remediation": "wde init",
                }
            )
            return issues
        state = self.load_state()
        if state.get("phase") == "READY_TO_DELIVER":
            # Verify no agent forged empty valid_checks
            if not state.get("valid_checks"):
                issues.append(
                    {
                        "code": "forged_delivery",
                        "message": "READY_TO_DELIVER without valid_checks — re-run wde deliver-check",
                        "remediation": "wde run mechanical && wde run visual",
                    }
                )
        # Contract files expected after certain phases
        phase = state.get("phase", "")
        if phase not in {"UNINITIALIZED", "INTENT_REQUIRED"}:
            if not (self.root / "CREATIVE-BRIEF.md").is_file():
                issues.append(
                    {
                        "code": "missing_brief",
                        "message": "CREATIVE-BRIEF.md missing",
                        "remediation": "Create from templates/creative-brief-template.md",
                    }
                )
        return issues


def _module_available(name: str) -> bool:
    try:
        __import__(name)
        return True
    except ImportError:
        return False


def default_project(root: Path, project_id: str | None = None) -> dict[str, Any]:
    name = project_id or re.sub(r"[^a-z0-9-]+", "-", root.name.lower()).strip("-") or "project"
    source_paths = ["src"] if (root / "src").is_dir() else ["."]
    framework = "unknown"
    if (root / "package.json").is_file():
        framework = "node"
        try:
            pkg = json.loads((root / "package.json").read_text(encoding="utf-8"))
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "next" in deps:
                framework = "nextjs"
            elif "react" in deps:
                framework = "react"
            elif "vue" in deps:
                framework = "vue"
        except (OSError, json.JSONDecodeError):
            pass
    return {
        "schema_version": "3.0",
        "project_id": name,
        "product_type": "other",
        "framework": framework,
        "dev_command": "npm run dev" if framework != "unknown" else "",
        "build_command": "npm run build" if framework != "unknown" else "",
        "test_command": "",
        "local_url": "http://localhost:5173",
        "source_paths": source_paths,
        "critical_pages": ["/"],
        "policy_profile": "web",
        "adapter": "generic",
    }


def init_project(root: Path, *, force: bool = False) -> ProjectContext:
    ctx = ProjectContext(root)
    if ctx.exists() and not force:
        raise FileExistsError(f"Already initialized: {ctx.wde}")
    ctx.wde.mkdir(parents=True, exist_ok=True)
    (ctx.wde / "evidence").mkdir(exist_ok=True)
    (ctx.wde / "reports").mkdir(exist_ok=True)
    (ctx.wde / "logs").mkdir(exist_ok=True)
    (ctx.wde / "cache").mkdir(exist_ok=True)
    project = default_project(root)
    state = initial_state()
    state["hashes"] = ctx.compute_hashes(project)
    state["capabilities"] = ctx.detect_capabilities()
    state["degraded_mode"] = not state["capabilities"].get("browser", False)
    ctx.save_project(project)
    ctx.save_state(state)
    caps = state["capabilities"]
    (ctx.wde / CAPABILITIES_FILE).write_text(
        json.dumps(caps, indent=2) + "\n", encoding="utf-8"
    )
    # Touch contract stubs if missing
    brief = root / "CREATIVE-BRIEF.md"
    if not brief.is_file():
        brief.write_text(
            "# CREATIVE-BRIEF.md\n\n"
            "> Fill all fields (see skill templates/creative-brief-template.md).\n\n"
            "## Emotional Intent\n\n___\n\n"
            "## The One Unexpected Thing\n\n___\n\n"
            "## Hero Dimension\n\n"
            "- [ ] Typography\n- [ ] Negative space\n- [ ] Colour\n"
            "- [ ] Motion\n- [ ] Illustration\n\n"
            "## The Broken Rule\n\nWe will deliberately ignore ___ because ___\n\n"
            "## Design Read\n\n___\n\n"
            "## Design Dials\n\n"
            "- VARIANCE: ___\n- MOTION: ___\n- DENSITY: ___\n\n"
            "## The Cross-Domain Steal\n\n"
            "The non-software discipline: ___\nThe specific move: ___\n",
            encoding="utf-8",
        )
    exp = root / "EXPERIENCE-CONTRACT.md"
    if not exp.is_file():
        tmpl = Path(__file__).resolve().parents[2] / "templates" / "experience-contract-template.md"
        if tmpl.is_file():
            exp.write_text(tmpl.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            exp.write_text("# EXPERIENCE-CONTRACT.md\n\n## Product goal\n\n___\n", encoding="utf-8")
    return ctx
