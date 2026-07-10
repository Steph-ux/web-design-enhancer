"""CLI smoke: init / status / next / doctor / illegal transition."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _wde(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "wde", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_init_status_next(tmp_path: Path):
    r = _wde("init", "--root", str(tmp_path), cwd=ROOT)
    assert r.returncode == 0, r.stderr
    assert (tmp_path / ".wde" / "state.json").is_file()
    assert (tmp_path / "CREATIVE-BRIEF.md").is_file()

    r = _wde("status", "--root", str(tmp_path), "--json", cwd=ROOT)
    assert r.returncode == 0, r.stderr
    state = json.loads(r.stdout)
    assert state["phase"] == "INTENT_REQUIRED"

    r = _wde("next", "--root", str(tmp_path), cwd=ROOT)
    assert r.returncode == 0
    assert "intent" in r.stdout.lower() or "brief" in r.stdout.lower() or "wde" in r.stdout.lower()


def test_transition_to_ready_from_intent_fails(tmp_path: Path):
    assert _wde("init", "--root", str(tmp_path), cwd=ROOT).returncode == 0
    r = _wde("transition", "READY_TO_DELIVER", "--root", str(tmp_path), cwd=ROOT)
    # Public transition removed — always hard-fail (no phase walk)
    assert r.returncode == 2
    assert "removed" in r.stderr.lower() or "ERROR" in r.stderr
