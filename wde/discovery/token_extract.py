"""Extract concrete palette/type tokens from getdesign / Pro Max artifacts."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from wde.discovery.tokens import DesignTokens

_HEX = re.compile(r"#(?:[0-9A-Fa-f]{6})\b")
_FONT = re.compile(
    r"(?:font-family|Display|Body|Sans|Serif|Mono)[^\n#]{0,40}?([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+){0,2})",
    re.I,
)


def _collect_hexes(text: str) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for m in _HEX.findall(text or ""):
        h = m.upper()
        if h not in seen:
            seen.add(h)
            out.append(m if m.startswith("#") else f"#{m}")
    return out


def _rel_luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return 0.5
    r, g, b = int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255

    def f(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def extract_tokens_from_text(text: str, *, brand: str = "") -> DesignTokens | None:
    """Build DesignTokens from free-form design markdown (getdesign / Pro Max)."""
    hexes = _collect_hexes(text)
    if len(hexes) < 3:
        return None

    # Heuristic role assignment
    sorted_by_lum = sorted(hexes, key=_rel_luminance)
    darkest = sorted_by_lum[0]
    lightest = sorted_by_lum[-1]
    mid = sorted_by_lum[len(sorted_by_lum) // 2]

    # Accent: prefer mid-saturation-looking (not pure gray) — pick middle of list
    accent = hexes[min(2, len(hexes) - 1)]
    for h in hexes:
        # skip near black/white
        lum = _rel_luminance(h)
        if 0.08 < lum < 0.85 and h not in {darkest, lightest}:
            accent = h
            break

    # Mode from average of first bg candidates
    bg_candidate = darkest if _rel_luminance(darkest) < 0.2 else lightest
    mode = "dark" if _rel_luminance(bg_candidate) < 0.25 else "light"

    fonts = _FONT.findall(text)
    display = fonts[0] if fonts else ("IBM Plex Sans" if mode == "dark" else "Fraunces")
    body = fonts[1] if len(fonts) > 1 else "IBM Plex Sans"
    mono = "IBM Plex Mono"

    if mode == "dark":
        return DesignTokens(
            mode="dark",
            background=darkest if _rel_luminance(darkest) < 0.25 else "#0A0A0A",
            surface=mid if _rel_luminance(mid) < 0.4 else "#141414",
            text=lightest if _rel_luminance(lightest) > 0.6 else "#F2F2F2",
            muted="#8A8A8A",
            border="#2A2A2A",
            accent=accent,
            display_font=display.strip()[:40],
            body_font=body.strip()[:40],
            mono_font=mono,
        )
    return DesignTokens(
        mode="light",
        background=lightest if _rel_luminance(lightest) > 0.7 else "#F3EEE4",
        surface=mid if _rel_luminance(mid) > 0.5 else "#EFE8DC",
        text=darkest if _rel_luminance(darkest) < 0.35 else "#1A1A1A",
        muted="#666666",
        border="#D4CBB8",
        accent=accent,
        display_font=display.strip()[:40],
        body_font=body.strip()[:40],
        mono_font=mono,
    )


def find_getdesign_artifacts(root: Path) -> list[tuple[str, Path]]:
    """Return (brand, path) for getdesign DESIGN.md copies."""
    out: list[tuple[str, Path]] = []
    for p in sorted(root.glob("getdesign-*.md")):
        brand = p.stem.replace("getdesign-", "", 1)
        out.append((brand, p))
    for p in sorted(root.glob("*/DESIGN.md")):
        if p.parent.name.startswith(".") or p.parent.name in {
            "templates",
            "references",
            "examples",
            "docs",
            "wde",
        }:
            continue
        out.append((p.parent.name, p))
    # de-dupe by path
    seen: set[str] = set()
    uniq: list[tuple[str, Path]] = []
    for b, p in out:
        key = str(p.resolve())
        if key not in seen:
            seen.add(key)
            uniq.append((b, p))
    return uniq


def blend_tokens(base: DesignTokens, donor: DesignTokens, *, weight: str = "accent") -> DesignTokens:
    """Blend external visual reference into territory base (base structure wins)."""
    if weight == "full":
        return donor
    # Prefer donor accent + optional surface; keep mode/background from territory
    return DesignTokens(
        mode=base.mode,
        background=base.background,
        surface=base.surface,
        text=base.text,
        muted=base.muted,
        border=base.border,
        accent=donor.accent or base.accent,
        success=base.success,
        danger=base.danger,
        alt_background=base.alt_background,
        alt_surface=base.alt_surface,
        alt_text=base.alt_text,
        alt_muted=base.alt_muted,
        alt_border=base.alt_border,
        display_font=donor.display_font or base.display_font,
        body_font=base.body_font,
        mono_font=base.mono_font,
        radius_board=base.radius_board,
        radius_control=base.radius_control,
        grid_base=base.grid_base,
    )


def apply_external_tokens_to_winner(
    root: Path,
    winner: Any,
    *,
    valid_receipts: list[dict[str, Any]] | None = None,
) -> tuple[Any, dict[str, Any]]:
    """Mutate winner.tokens from successful getdesign/promax artifacts. Returns (winner, audit)."""
    audit: dict[str, Any] = {"sources": [], "blended": False}
    base = winner.resolved_tokens()
    donors: list[tuple[str, DesignTokens]] = []

    # Prefer artifacts referenced by valid getdesign success receipts
    paths: list[tuple[str, Path]] = []
    if valid_receipts:
        for r in valid_receipts:
            if r.get("status") != "success":
                continue
            if r.get("path_kind") not in {"getdesign", "promax"}:
                continue
            art = r.get("artifact") or ""
            if art:
                p = root / art
                if p.is_file():
                    brand = (r.get("details") or {}).get("brand") or p.stem
                    paths.append((str(brand), p))
    if not paths:
        paths = find_getdesign_artifacts(root)
        # also promax output
        pmax = root / "design-system-output.md"
        if pmax.is_file():
            paths.append(("promax", pmax))

    for brand, path in paths[:3]:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        tok = extract_tokens_from_text(text, brand=brand)
        if tok:
            donors.append((brand, tok))
            try:
                rel = str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
            except ValueError:
                rel = str(path)
            audit["sources"].append(
                {
                    "brand": brand,
                    "path": rel,
                    "mode": tok.mode,
                    "accent": tok.accent,
                    "background": tok.background,
                }
            )

    if not donors:
        audit["reason"] = "no external token sources"
        return winner, audit

    # First donor = structure/material accent blend; keep territory mode
    blended = base
    for brand, donor in donors:
        blended = blend_tokens(blended, donor, weight="accent")
    winner.tokens = blended
    audit["blended"] = True
    audit["result_accent"] = blended.accent
    audit["result_display_font"] = blended.display_font
    # provenance on territory
    for brand, _ in donors:
        dig = f"getdesign:{brand}"
        if dig not in (winner.source_findings or []):
            winner.source_findings = list(winner.source_findings or []) + [dig]
        winner.applied_transformations = list(winner.applied_transformations or []) + [
            {
                "finding": f"external visual reference {brand}",
                "transformation": "accent + display font blended into territory tokens",
                "affected_axes": ["tokens", "typography"],
            }
        ]
    return winner, audit
