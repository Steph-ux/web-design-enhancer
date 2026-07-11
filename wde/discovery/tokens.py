"""Structured design tokens attached to creative territories."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


Mode = Literal["light", "dark"]


@dataclass
class DesignTokens:
    """Concrete palette + type tokens a territory commits to.

    The compiler MUST emit these into DESIGN.md — never a global dark default
    that contradicts a light editorial winner.
    """

    mode: Mode  # primary canvas: light-first or dark-first
    background: str
    surface: str
    text: str
    muted: str
    border: str
    accent: str
    success: str = "#5FA657"
    danger: str = "#C44C4C"
    # Alternate scheme for prefers-color-scheme
    alt_background: str = "#0A0A0A"
    alt_surface: str = "#141414"
    alt_text: str = "#F2F2F2"
    alt_muted: str = "#8A8A8A"
    alt_border: str = "#2A2A2A"
    display_font: str = "Fraunces"
    body_font: str = "IBM Plex Sans"
    mono_font: str = "IBM Plex Mono"
    radius_board: str = "0px"
    radius_control: str = "4px"
    grid_base: str = "8px"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def primary_hexes(self) -> list[str]:
        """Up to 8 hex codes for DESIGN.md §2."""
        return [
            self.background,
            self.surface,
            self.text,
            self.muted,
            self.border,
            self.accent,
            self.success,
            self.danger,
        ]

    @staticmethod
    def light_editorial(
        *,
        paper: str = "#F3EEE4",
        ink: str = "#1A1A1A",
        accent: str = "#B8956A",
        display: str = "Fraunces",
    ) -> "DesignTokens":
        return DesignTokens(
            mode="light",
            background=paper,
            surface="#EFE8DC",
            text=ink,
            muted="#666666",
            border="#D4CBB8",
            accent=accent,
            alt_background="#0A0A0A",
            alt_surface="#141414",
            alt_text="#F2F2F2",
            alt_muted="#8A8A8A",
            alt_border="#2A2A2A",
            display_font=display,
            body_font="IBM Plex Sans",
            mono_font="IBM Plex Mono",
        )

    @staticmethod
    def dark_instrument(
        *,
        bg: str = "#0A0A0A",
        accent: str = "#C4A35A",
        display: str = "IBM Plex Sans",
    ) -> "DesignTokens":
        return DesignTokens(
            mode="dark",
            background=bg,
            surface="#141414",
            text="#F2F2F2",
            muted="#8A8A8A",
            border="#2A2A2A",
            accent=accent,
            alt_background="#F6F1E8",
            alt_surface="#EFE8DC",
            alt_text="#1A1A1A",
            alt_muted="#666666",
            alt_border="#D4CBB8",
            display_font=display,
            body_font="IBM Plex Sans",
            mono_font="IBM Plex Mono",
        )

    @staticmethod
    def from_palette_role(palette_role: str, typography: str = "") -> "DesignTokens":
        """Fallback parser when a territory only has free-text palette_role."""
        low = (palette_role or "").lower()
        ty = (typography or "").lower()
        display = "Fraunces" if "serif" in ty else "IBM Plex Sans"
        light_keys = (
            "paper",
            "ivory",
            "off-white",
            "off white",
            "cream",
            "ink and paper",
            "warm grey",
            "parchment",
        )
        if any(k in low for k in light_keys):
            paper = "#F3EEE4" if ("ivory" in low or "paper" in low or "cream" in low) else "#F6F1E8"
            accent = "#B8956A"
            if "ochre" in low or "map" in low:
                accent = "#C4A35A"
            if "red" in low or "warning" in low:
                accent = "#C44C4C"
            if "steel" in low:
                accent = "#6B7280"
            return DesignTokens.light_editorial(paper=paper, accent=accent, display=display)
        accent = "#C4A35A"
        if "cyan" in low:
            accent = "#5B9EA6"
        if "green" in low:
            accent = "#5FA657"
        if "brass" in low:
            accent = "#C4A35A"
        if "silver" in low:
            accent = "#A8B0B8"
        if "follow-spot" in low or "spot" in low:
            accent = "#E8D5A3"
        return DesignTokens.dark_instrument(accent=accent, display=display)
