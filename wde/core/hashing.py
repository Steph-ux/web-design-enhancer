"""Deterministic content hashing for contracts and source trees."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable

SKIP_DIR_NAMES = {
    ".git",
    ".wde",
    "node_modules",
    "dist",
    "build",
    ".next",
    "__pycache__",
    "audit-results",
    ".pytest_cache",
    "coverage",
    "venv",
    ".venv",
}

SOURCE_SUFFIXES = {
    ".html",
    ".htm",
    ".css",
    ".scss",
    ".sass",
    ".less",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".vue",
    ".svelte",
    ".astro",
    ".json",
    ".md",
}


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def sha256_paths(paths: Iterable[Path], root: Path | None = None) -> str:
    """Hash a sorted list of files (path relative + content)."""
    root = root or Path(".")
    h = hashlib.sha256()
    files: list[Path] = []
    for p in paths:
        p = Path(p)
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            for child in sorted(p.rglob("*")):
                if not child.is_file():
                    continue
                if any(part in SKIP_DIR_NAMES for part in child.parts):
                    continue
                if child.suffix.lower() not in SOURCE_SUFFIXES and child.suffix:
                    # still include unknown text-like? stick to suffixes
                    if child.suffix.lower() not in SOURCE_SUFFIXES:
                        continue
                files.append(child)
    for f in sorted(set(files), key=lambda x: str(x).replace("\\", "/")):
        try:
            rel = f.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            rel = f.as_posix().replace("\\", "/")
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        try:
            h.update(f.read_bytes())
        except OSError:
            h.update(b"<unreadable>")
        h.update(b"\0")
    return "sha256:" + h.hexdigest()


def hash_source_tree(source_paths: list[str], root: Path) -> str:
    return sha256_paths([root / p for p in source_paths], root=root)


def hash_contract_files(root: Path) -> dict[str, str]:
    """Hash known contract documents if present."""
    names = [
        "CREATIVE-BRIEF.md",
        "EXPERIENCE-CONTRACT.md",
        "DESIGN.md",
        "STRUCTURAL-LOCK.md",
        "structural-lock.md",
    ]
    out: dict[str, str] = {}
    for name in names:
        p = root / name
        if p.is_file():
            key = name.upper().replace(".MD", "")
            if key == "STRUCTURAL-LOCK":
                key = "STRUCTURAL_LOCK"
            out[key] = sha256_file(p)
    return out
