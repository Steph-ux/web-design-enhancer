#!/usr/bin/env python3
"""
audit_beauty.py
───────────────
The positive mirror of audit_style_uniqueness.py.

Where the uniqueness auditor PENALISES resemblance to the Generic AI Template,
this auditor REWARDS the craft markers that make a design read as the work of a
human designer — and BLOCKS the opposite failure mode: a layout that is
technically clean, passes every prohibition gate, yet is flat, timid and
soulless.

"Not generic" is not the same as "beautiful". A page can have zero blue→purple
gradients, a perfect 8px grid and full WCAG AA contrast, and still be lifeless.
This gate measures the difference.

Five craft dimensions, 100 points total:
  D1  Typographic scale contrast   (25)  — does an H1 actually dominate the body?
  D2  Hierarchy richness           (15)  — enough distinct type sizes in use?
  D3  Colour intentionality        (20)  — a deliberate signature accent + discipline
  D4  Spacing rhythm               (15)  — varied, intentional whitespace (not one flat value)
  D5  Finition / interaction depth (25)  — hover, focus-visible, transitions, reduced-motion

Higher is better (inverse of the uniqueness score).

Exit codes:
  0 — score ≥ threshold_pass   (beautiful enough to ship)
  1 — threshold_floor ≤ score < threshold_pass  (acceptable, needs polish)
  2 — score < threshold_floor  (BLOCKED — technically clean but soulless)
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

# Windows terminals may default to cp1252 — force UTF-8 for emoji output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ──────────────────────────────────────────────────────────────────────────────
# ANSI colour helpers
# ──────────────────────────────────────────────────────────────────────────────

def _ansi(code: str) -> str:
    """Return ANSI escape if stdout is a TTY, else empty string."""
    return f"\033[{code}m" if sys.stdout.isatty() else ""

RESET  = _ansi("0")
BOLD   = _ansi("1")
RED    = _ansi("31")
YELLOW = _ansi("33")
GREEN  = _ansi("32")
CYAN   = _ansi("36")
DIM    = _ansi("2")


# ──────────────────────────────────────────────────────────────────────────────
# Low-level extractors (deterministic, regex-based)
# ──────────────────────────────────────────────────────────────────────────────

# Tailwind's default type scale → px, used when class-based sizing is present.
_TW_TEXT_PX = {
    "text-xs": 12, "text-sm": 14, "text-base": 16, "text-lg": 18,
    "text-xl": 20, "text-2xl": 24, "text-3xl": 30, "text-4xl": 36,
    "text-5xl": 48, "text-6xl": 60, "text-7xl": 72, "text-8xl": 96,
    "text-9xl": 128,
}

_FONT_SIZE_RE = re.compile(
    r"font-size\s*:\s*([0-9.]+)\s*(px|rem|em)", re.IGNORECASE
)
_TW_TEXT_RE = re.compile(r"\btext-(?:xs|sm|base|lg|xl|[2-9]xl)\b")
_HEX_RE = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b")
_SPACE_RE = re.compile(
    r"(?:margin|padding|gap|row-gap|column-gap)[a-z-]*\s*:\s*([^;}{]+)",
    re.IGNORECASE,
)
_SPACE_PX_RE = re.compile(r"([0-9.]+)\s*(px|rem|em)", re.IGNORECASE)


def _to_px(value: float, unit: str) -> float:
    unit = unit.lower()
    if unit in ("rem", "em"):
        return value * 16.0
    return value


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hsl(r: int, g: int, b: int) -> tuple[float, float, float]:
    r_, g_, b_ = r / 255.0, g / 255.0, b / 255.0
    mx, mn = max(r_, g_, b_), min(r_, g_, b_)
    l = (mx + mn) / 2.0
    if mx == mn:
        return 0.0, 0.0, l
    d = mx - mn
    s = d / (2.0 - mx - mn) if l > 0.5 else d / (mx + mn)
    if mx == r_:
        h = (g_ - b_) / d + (6.0 if g_ < b_ else 0.0)
    elif mx == g_:
        h = (b_ - r_) / d + 2.0
    else:
        h = (r_ - g_) / d + 4.0
    return (h / 6.0) * 360.0, s, l


def _is_neutral(hex_color: str) -> bool:
    """True if the colour reads as a neutral (grey/black/white/near-grey)."""
    try:
        r, g, b = _hex_to_rgb(hex_color)
    except ValueError:
        return True
    _, s, _ = _rgb_to_hsl(r, g, b)
    return s < 0.12  # very low saturation → neutral


def _is_default_blue(hex_color: str) -> bool:
    """True for the family of AI-default blues/indigos around #3B82F6."""
    try:
        r, g, b = _hex_to_rgb(hex_color)
    except ValueError:
        return False
    h, s, l = _rgb_to_hsl(r, g, b)
    return 205 <= h <= 255 and s >= 0.45 and 0.35 <= l <= 0.75


# ──────────────────────────────────────────────────────────────────────────────
# Core auditor
# ──────────────────────────────────────────────────────────────────────────────

class BeautyAuditor:
    """
    Scans a directory for positive craft markers and produces a Beauty Score
    (0-100). Higher means more deliberate, more human, more beautiful.
    """

    SCANNABLE_EXTS = {".css", ".scss", ".sass", ".html", ".jsx", ".tsx", ".js", ".ts"}
    SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "__pycache__", "vendor"}

    # Maximum points per dimension.
    DIMENSIONS = [
        ("D1", "Typographic scale contrast", 25),
        ("D2", "Hierarchy richness", 15),
        ("D3", "Colour intentionality", 20),
        ("D4", "Spacing rhythm", 15),
        ("D5", "Finition / interaction depth", 25),
    ]

    def __init__(
        self,
        root_path: Path,
        threshold_floor: int = 50,
        threshold_pass: int = 70,
    ) -> None:
        self.root_path = root_path
        self.threshold_floor = threshold_floor
        self.threshold_pass = threshold_pass

        self.score: int = 0
        self.dimension_scores: dict[str, int] = {}
        self.findings: list[dict[str, Any]] = []   # positive notes
        self.weaknesses: list[dict[str, Any]] = []  # what cost points

        # Raw collected evidence
        self._font_px: list[float] = []
        self._colors: list[str] = []
        self._space_px: list[float] = []
        self._flags: dict[str, bool] = defaultdict(bool)
        self._vars: dict[str, str] = {}

    # ── file collection ────────────────────────────────────────────────────────

    def _collect_files(self) -> list[Path]:
        files: list[Path] = []
        for dirpath, dirnames, filenames in os.walk(self.root_path):
            dirnames[:] = [d for d in dirnames if d not in self.SKIP_DIRS]
            for filename in filenames:
                p = Path(dirpath) / filename
                if p.suffix in self.SCANNABLE_EXTS:
                    files.append(p)
        return files

    # ── scanning ───────────────────────────────────────────────────────────────

    def scan(self) -> None:
        files = self._collect_files()
        texts: list[str] = []
        for fp in files:
            try:
                texts.append(fp.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                continue
        self._vars = self._build_var_map(texts)
        for text in texts:
            self._harvest(self._resolve_vars(text))

        self._score_d1_type_contrast()
        self._score_d2_hierarchy()
        self._score_d3_color()
        self._score_d4_spacing()
        self._score_d5_finition()

        self.score = min(sum(self.dimension_scores.values()), 100)

    def _build_var_map(self, texts: list[str]) -> dict[str, str]:
        raw: dict[str, str] = {}
        for t in texts:
            for name, val in re.findall(r"(--[A-Za-z0-9_-]+)\s*:\s*([^;}{]+)", t):
                raw[name.strip()] = val.strip()
        resolved: dict[str, str] = {}
        for name in raw:
            val = raw[name]
            for _ in range(5):
                m = re.search(r"var\(\s*(--[A-Za-z0-9_-]+)\s*(?:,[^)]*)?\)", val)
                if not m:
                    break
                val = val[: m.start()] + raw.get(m.group(1), "") + val[m.end():]
            resolved[name] = val
        return resolved

    def _resolve_vars(self, text: str) -> str:
        def repl(m):
            return self._vars.get(m.group(1), m.group(0))
        out = text
        for _ in range(5):
            new = re.sub(r"var\(\s*(--[A-Za-z0-9_-]+)\s*(?:,[^)]*)?\)", repl, out)
            if new == out:
                break
            out = new
        return out

    def _harvest(self, text: str) -> None:
        # font sizes (CSS units, incl. clamp(): take the largest rem/px/em present)
        for m in re.finditer(r"font-size\s*:\s*([^;}{]+)", text, re.IGNORECASE):
            pxs = [
                _to_px(float(v), u)
                for v, u in re.findall(r"([0-9.]+)\s*(px|rem|em)\b", m.group(1), re.IGNORECASE)
            ]
            if pxs:
                self._font_px.append(max(pxs))
        # font sizes (Tailwind utility classes)
        for cls in _TW_TEXT_RE.findall(text):
            if cls in _TW_TEXT_PX:
                self._font_px.append(float(_TW_TEXT_PX[cls]))

        # colours
        self._colors.extend(_HEX_RE.findall(text))

        # spacing values
        for chunk in _SPACE_RE.findall(text):
            for val, unit in _SPACE_PX_RE.findall(chunk):
                try:
                    px = _to_px(float(val), unit)
                    if px > 0:
                        self._space_px.append(px)
                except ValueError:
                    pass

        low = text.lower()
        if ":hover" in low or "hover:" in low:
            self._flags["hover"] = True
        if ":focus-visible" in low or "focus-visible:" in low:
            self._flags["focus_visible"] = True
        elif ":focus" in low or "focus:" in low:
            self._flags["focus"] = True
        if "transition" in low:
            self._flags["transition"] = True
        if "prefers-reduced-motion" in low:
            self._flags["reduced_motion"] = True
        if "letter-spacing" in low or "tracking-" in low:
            self._flags["letter_spacing"] = True
        if "line-height" in low or "leading-" in low:
            self._flags["line_height"] = True
        if re.search(r"font-weight\s*:\s*(?:[7-9]00|bold)", low) or "font-bold" in low or "font-black" in low:
            self._flags["bold_weight"] = True

    # ── dimension scorers ───────────────────────────────────────────────────────

    def _add(self, dim_id: str, pts: int) -> None:
        self.dimension_scores[dim_id] = pts

    def _note(self, dim_id: str, msg: str) -> None:
        self.findings.append({"dimension": dim_id, "message": msg})

    def _weak(self, dim_id: str, msg: str, fix: str) -> None:
        self.weaknesses.append({"dimension": dim_id, "message": msg, "fix": fix})

    def _score_d1_type_contrast(self) -> None:
        cap = 25
        if not self._font_px:
            self._add("D1", 0)
            self._weak(
                "D1", "No font sizes detected — cannot establish hierarchy.",
                "Set explicit sizes (DESIGN.md §4): H1 28–80px, body 13–18px.",
            )
            return
        sizes = sorted(set(round(s, 1) for s in self._font_px))
        body_candidates = [s for s in sizes if 13 <= s <= 18] or [min(sizes)]
        body = min(body_candidates)
        biggest = max(sizes)
        ratio = biggest / body if body else 1.0

        if ratio >= 3.0:
            pts = cap
        elif ratio >= 2.4:
            pts = 18
        elif ratio >= 1.8:
            pts = 10
        else:
            pts = 0
        self._add("D1", pts)
        if pts == cap:
            self._note("D1", f"Strong scale contrast — H1/body ratio {ratio:.1f}x.")
        elif pts == 0:
            self._weak(
                "D1", f"Flat type scale — largest/body ratio only {ratio:.1f}x.",
                "Make the H1 dominate: aim for ≥2.4x the body size (e.g. body 16px → H1 ≥ 40px).",
            )
        else:
            self._weak(
                "D1", f"Modest scale contrast — ratio {ratio:.1f}x.",
                "Push the display size higher for a confident hierarchy (target ≥3.0x).",
            )

    def _score_d2_hierarchy(self) -> None:
        cap = 15
        distinct = len(set(round(s, 1) for s in self._font_px))
        if distinct >= 5:
            pts = cap
        elif distinct == 4:
            pts = 12
        elif distinct == 3:
            pts = 8
        elif distinct == 2:
            pts = 3
        else:
            pts = 0
        self._add("D2", pts)
        if pts >= 12:
            self._note("D2", f"{distinct} distinct type sizes — rich hierarchy.")
        else:
            self._weak(
                "D2", f"Only {distinct} distinct type size(s) in use.",
                "Build a real type scale: display, H1, H2, H3, body, small (≥5 steps).",
            )

    def _score_d3_color(self) -> None:
        cap = 20
        colors = {c.lower() for c in self._colors}
        if not colors:
            self._add("D3", 0)
            self._weak(
                "D3", "No colours detected.",
                "Define a semantic palette in DESIGN.md §2 with a signature accent.",
            )
            return
        chromatic = {c for c in colors if not _is_neutral(c)}
        signature = {c for c in chromatic if not _is_default_blue(c)}
        hue_count = len(chromatic)

        pts = 0
        if signature:
            pts += 12
            self._note("D3", f"Signature accent present ({sorted(signature)[0]}), not the default blue.")
        else:
            self._weak(
                "D3", "No signature colour — palette is neutral-only or default-blue.",
                "Introduce one deliberate accent that isn't blue/indigo (#3B82F6 family).",
            )
        if 1 <= hue_count <= 4:
            pts += 8
            self._note("D3", f"Disciplined palette — {hue_count} chromatic hue(s).")
        elif hue_count == 0:
            pass
        elif hue_count <= 6:
            pts += 4
            self._weak(
                "D3", f"Palette getting busy — {hue_count} chromatic hues.",
                "Consolidate to a tight set (1–4 hues) for a coherent identity.",
            )
        else:
            self._weak(
                "D3", f"Palette is noisy — {hue_count} chromatic hues.",
                "Cut to a disciplined 1–4 hue palette; too many colours read as accidental.",
            )
        self._add("D3", min(pts, cap))

    def _score_d4_spacing(self) -> None:
        cap = 15
        if not self._space_px:
            self._add("D4", 0)
            self._weak(
                "D4", "No spacing values detected.",
                "Use an intentional spacing scale (8/16/24/32/64…) with real section breathing room.",
            )
            return
        distinct = sorted(set(round(s) for s in self._space_px))
        variety = len(distinct)
        has_large = any(s >= 64 for s in distinct)  # genuine section rhythm

        pts = 0
        if variety >= 5:
            pts += 10
            self._note("D4", f"{variety} distinct spacing steps — varied rhythm.")
        elif variety >= 3:
            pts += 6
        else:
            self._weak(
                "D4", f"Uniform spacing — only {variety} distinct value(s).",
                "A single repeated gap reads as a wall. Vary spacing to create rhythm.",
            )
        if has_large:
            pts += 5
            self._note("D4", "Generous section spacing present (≥64px).")
        else:
            self._weak(
                "D4", "No large-scale spacing — sections likely cramped.",
                "Add real breathing room between sections (≥64px) to let the layout breathe.",
            )
        self._add("D4", min(pts, cap))

    def _score_d5_finition(self) -> None:
        cap = 25
        pts = 0
        if self._flags["hover"]:
            pts += 6
            self._note("D5", "Hover states defined.")
        else:
            self._weak("D5", "No hover states.", "Add deliberate :hover feedback on interactive elements.")
        if self._flags["focus_visible"]:
            pts += 7
            self._note("D5", "focus-visible handled — keyboard polish.")
        elif self._flags["focus"]:
            pts += 3
            self._weak("D5", "Has :focus but not :focus-visible.", "Prefer :focus-visible to avoid focus rings on mouse clicks.")
        else:
            self._weak("D5", "No focus styling.", "Add :focus-visible styles for keyboard users.")
        if self._flags["transition"]:
            pts += 6
            self._note("D5", "Transitions present — motion is considered.")
        else:
            self._weak("D5", "No transitions.", "Add short transitions (≤400ms) on state changes for finish.")
        if self._flags["reduced_motion"]:
            pts += 6
            self._note("D5", "prefers-reduced-motion respected.")
        else:
            self._weak("D5", "No prefers-reduced-motion guard.", "Wrap animations in a prefers-reduced-motion media query.")
        self._add("D5", min(pts, cap))

    # ── reporting ──────────────────────────────────────────────────────────────

    def _score_label(self) -> tuple[str, str]:
        s = self.score
        if s >= 85:
            return ("✅ BEAUTIFUL", GREEN)
        if s >= self.threshold_pass:
            return ("✅ POLISHED", GREEN)
        if s >= self.threshold_floor:
            return ("⚠️  NEEDS POLISH", YELLOW)
        return ("❌ SOULLESS", RED)

    def _score_bar(self, width: int = 24) -> str:
        filled = round(self.score / 100 * width)
        return f"[{'█' * filled}{'░' * (width - filled)}]"

    def _exit_code(self) -> int:
        if self.score < self.threshold_floor:
            return 2
        if self.score < self.threshold_pass:
            return 1
        return 0

    def print_report(self) -> None:
        label, colour = self._score_label()
        sep = "=" * 52
        print(f"\n{BOLD}{sep}{RESET}")
        print("  BEAUTY AUDIT — craft & finish")
        print(f"{BOLD}{sep}{RESET}\n")
        print(f"  Beauty Score: {colour}{BOLD}{self.score}/100  {label}{RESET}")
        print(f"  {colour}{self._score_bar()} {self.score}%{RESET}\n")

        print("  Dimension breakdown:")
        for dim_id, name, cap in self.DIMENSIONS:
            got = self.dimension_scores.get(dim_id, 0)
            mark = GREEN if got >= cap * 0.8 else (YELLOW if got >= cap * 0.4 else RED)
            print(f"    {BOLD}{dim_id}{RESET} {name:<32} {mark}{got:>2}/{cap}{RESET}")
        print()

        if self.weaknesses:
            print(f"  {YELLOW}What is holding the design back:{RESET}\n")
            for w in self.weaknesses:
                print(f"  {BOLD}{CYAN}[{w['dimension']}]{RESET} {w['message']}")
                print(f"       {YELLOW}Fix:{RESET} {w['fix']}\n")
        else:
            print(f"  {GREEN}No craft weaknesses detected.{RESET}\n")

        print(f"{BOLD}{sep}{RESET}")
        if self._exit_code() == 2:
            print(
                f"  {RED}{BOLD}❌ DELIVERY BLOCKED{RESET} — Score {self.score}/100 below "
                f"floor {self.threshold_floor}.\n"
                f"  Technically clean but soulless. Raise the craft before delivery —\n"
                f"  see references/beauty-gestures.md for the signature gestures per archetype."
            )
        elif self._exit_code() == 1:
            print(
                f"  {YELLOW}{BOLD}⚠️  NEEDS POLISH{RESET} — Score {self.score}/100 below "
                f"pass {self.threshold_pass}.\n"
                f"  Acceptable, but address the weaknesses above to look truly hand-made."
            )
        else:
            print(
                f"  {GREEN}{BOLD}✅ PASSED{RESET} — Score {self.score}/100. "
                f"The design carries deliberate craft."
            )
        print(f"{BOLD}{sep}{RESET}\n")

    def to_dict(self) -> dict[str, Any]:
        label, _ = self._score_label()
        return {
            "beauty_score": self.score,
            "label": label.strip(),
            "threshold_floor": self.threshold_floor,
            "threshold_pass": self.threshold_pass,
            "exit_code": self._exit_code(),
            "dimensions": {
                dim_id: {"name": name, "score": self.dimension_scores.get(dim_id, 0), "max": cap}
                for dim_id, name, cap in self.DIMENSIONS
            },
            "findings": self.findings,
            "weaknesses": self.weaknesses,
        }


# ──────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="audit_beauty",
        description=(
            "Beauty Score (0-100) — the positive mirror of audit_style_uniqueness.\n"
            "Rewards craft markers and blocks designs that are clean but soulless."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--path", type=Path, default=Path("."),
                        help="Root directory to scan (default: current directory)")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="Output machine-readable JSON instead of a terminal report")
    parser.add_argument("--threshold", nargs=2, type=int, metavar=("FLOOR", "PASS"),
                        default=[50, 70],
                        help="Block-floor and pass thresholds (default: 50 70)")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = args.path.resolve()
    if not root.exists():
        print(f"Error: path '{root}' does not exist.", file=sys.stderr)
        return 2
    if not root.is_dir():
        print(f"Error: path '{root}' is not a directory.", file=sys.stderr)
        return 2

    floor, passing = args.threshold
    if floor < 0 or passing < 0 or floor >= passing or passing > 100:
        print("Error: thresholds must satisfy 0 ≤ FLOOR < PASS ≤ 100.", file=sys.stderr)
        return 2

    auditor = BeautyAuditor(root_path=root, threshold_floor=floor, threshold_pass=passing)
    try:
        auditor.scan()
    except Exception as exc:  # noqa: BLE001
        print(f"Error during scan: {exc}", file=sys.stderr)
        return 2

    if args.json_output:
        print(json.dumps(auditor.to_dict(), indent=2, ensure_ascii=False))
    else:
        auditor.print_report()

    return auditor._exit_code()


if __name__ == "__main__":
    sys.exit(main())
