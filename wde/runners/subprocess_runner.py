"""Run V2 scripts (and other tools) as subprocesses with JSON capture."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class SubprocessResult:
    returncode: int
    stdout: str
    stderr: str
    data: Any | None = None


def scripts_dir() -> Path:
    """V2 scripts live next to the wde package (repo root / scripts)."""
    return Path(__file__).resolve().parents[2] / "scripts"


def run_python_script(
    script_name: str,
    args: list[str],
    *,
    cwd: Path,
    timeout: int = 120,
) -> SubprocessResult:
    script = scripts_dir() / script_name
    if not script.is_file():
        return SubprocessResult(
            returncode=127,
            stdout="",
            stderr=f"script not found: {script}",
            data=None,
        )
    cmd = [sys.executable, str(script), *args]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        return SubprocessResult(
            returncode=124,
            stdout=e.stdout or "",
            stderr=f"timeout after {timeout}s",
            data=None,
        )
    data = None
    out = proc.stdout or ""
    # Best-effort JSON parse (last {...} or full stdout)
    stripped = out.strip()
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError:
            # try last JSON object in stream
            for i in range(len(stripped) - 1, -1, -1):
                if stripped[i] == "{":
                    try:
                        data = json.loads(stripped[i:])
                        break
                    except json.JSONDecodeError:
                        continue
    return SubprocessResult(
        returncode=proc.returncode,
        stdout=out,
        stderr=proc.stderr or "",
        data=data,
    )
