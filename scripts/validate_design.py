#!/usr/bin/env python3
"""
Design Validation Script for web-design-enhancer

Validates a DESIGN.md file to prevent "AI slop":
- Checks spacings (multiples of 8px)
- Validates typography (max 2 fonts)
- Audits colors (semantic roles)
- Audits animations (<= 400ms) — handles ms AND seconds
- Validates WCAG AA contrast (4.5:1 text, 3.0:1 UI)
- Detects antipatterns (cliche gradients, generic icons)

Usage:
    python3 validate_design.py DESIGN.md
    python3 validate_design.py DESIGN.md --strict
"""

import sys
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


class DesignValidator:
    """DESIGN.md validator."""

    def __init__(self, filepath: str, strict: bool = False, code_path: str = None):
        self.filepath = Path(filepath)
        self.strict = strict
        self.code_path = code_path
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self._has_threejs: bool = False  # Three.js in scope
        self.content = ""
        self.sections = {}

    def run(self) -> bool:
        """Run the full validation. Returns True if OK."""
        if not self.filepath.exists():
            print(f"[ERROR] File {self.filepath} not found")
            return False

        self.content = self.filepath.read_text(encoding="utf-8")
        self._parse_sections()

        # Validations
        self._validate_phase0_evidence()    # Gate 0 — proof Phase 0 was executed
        self._validate_structure()
        self._validate_theme_originality()  # Level 1 — block at DESIGN.md stage
        self._validate_typography()
        self._validate_hierarchy()  # §4 — H1/H2/H3/P/Small ranges (WCAG + readability)
        self._validate_colors()
        self._validate_wcag_contrast()
        self._validate_spacing()
        self._validate_animations()
        self._validate_components()
        self._detect_antipatterns()
        self._validate_dark_mode()  # Dark mode section mandatory
        self._validate_ux_completeness()  # UX rules from real visual audit
        self._validate_mobile()      # Mobile section (optional, validated if present)
        self._validate_dark_mode_required()  # §8 mandatory if dark background
        self._validate_section_density()     # Contact/CTA density + odd N grid
        self._validate_threejs()           # §10 Three.js (optional, validated if present)
        self._validate_signature_gesture()  # §11 — one owned move (WARN), verified in code if --code
        self._validate_tensions()           # §12 — >=2 intentional contrasts (WARN)

        # Deduplicate identical errors
        self.errors   = list(dict.fromkeys(self.errors))
        self.warnings = list(dict.fromkeys(self.warnings))

        # Report
        self._print_report()
        return len(self.errors) == 0

    def _parse_sections(self):
        """Parse main DESIGN.md sections (English headings)."""
        sections = {
            "theme":      r"## 1\. Theme.*?(?=\n## |\Z)",
            "colors":     r"## 2\. Color Palette.*?(?=\n## |\Z)",
            "typography": r"## 3\. Typography\b.*?(?=\n## |\Z)",
            "hierarchy":  r"## 4\. Typography Hierarchy.*?(?=\n## |\Z)",
            "spacing":    r"## 5\. Spacing.*?(?=\n## |\Z)",
            "components": r"## 6\. Components.*?(?=\n## |\Z)",
            "animations": r"## 7\. Motion.*?(?=\n## |\Z)",
            "checklist":  r"## .*?Checklist.*?(?=\n## |\Z)",
            "darkmode":   r"## 8\. Dark Mode.*?(?=\n## |\Z)",
            "mobile":     r"## 9\. Mobile.*?(?=\n## |\Z)",
            "threejs":    r"## 10\. Three\.js.*?(?=\n## |\Z)",
            "signature":  r"## 11\. Signature Gesture.*?(?=\n## |\Z)",
            "tensions":   r"## 12\. Intentional Tensions.*?(?=\n## |\Z)",
        }

        for name, pattern in sections.items():
            match = re.search(pattern, self.content, re.DOTALL | re.IGNORECASE)
            self.sections[name] = match.group(0) if match else ""

    def _validate_phase0_evidence(self):
        """
        Gate 0 — Verify Phase 0 was actually executed.
        Without evidence in DESIGN.md -> block everything else.
        Prevents the AI from skipping Phase 0 and fabricating DESIGN.md from training data.
        """
        missing = []

        # Mandatory section
        if "## 0. Sources Phase 0" not in self.content:
            self.errors.append(
                "[PHASE 0 MISSING] Section '## 0. Sources Phase 0' is absent from DESIGN.md. "
                "Phase 0 (getdesign.md + UI/UX Pro Max) must be executed before any code. "
                "Use templates/design-md-template.md as a base."
            )
            return  # No point continuing — evidence totally absent

        # Verify placeholders have been replaced with real values
        placeholder_patterns = [
            (r"\[Ex:", "Still contains unfilled placeholders '[Ex: ...]'"),
            (r"Brand used\s*:\s*\[", "getdesign.md brand not filled in"),
            (r"Command executed\s*:\s*`npx getdesign@latest add <brand>`",
             "getdesign.md command not run ('<brand>' placeholder not replaced)"),
            (r"Query executed\s*:\s*`python3 scripts/search\.py \"<description>\"",
             "UI/UX Pro Max command not run (placeholder not replaced)"),
            (r"Style chosen\s*:\s*\[",
             "UI/UX Pro Max style not filled in — search.py must be run"),
            (r"Rationale.*?:\s*\[",
             "Theme rationale not filled in"),
        ]

        for pattern, message in placeholder_patterns:
            if re.search(pattern, self.content):
                missing.append(message)

        for msg in missing:
            self.errors.append(f"[PHASE 0 INCOMPLETE] {msg}")

        if missing:
            self.errors.append(
                "-> Execute Phase 0 before continuing: "
                "(1) npx getdesign@latest add <brand>  "
                "(2) python3 scripts/search.py '<description>' --design-system -p '<Project>'  "
                "(3) Fill section '## 0. Sources Phase 0' with real values."
            )

    def _validate_theme_originality(self):
        """
        Level 1 — Detect AI-cliche themes and concepts directly in DESIGN.md.
        Blocks before any code is written.
        """
        FORBIDDEN_THEMES = [
            (r"\bdark\s+cyberpunk\b",
             "'dark cyberpunk' — AI cliche #1 for tech portfolios. Describe the real texture instead."),
            (r"\bcyberneti[cq]",
             "'cybernetic' — generic AI aesthetic. Specify the real visual tokens."),
            (r"\bglow[\s-]cursor\b",
             "Glow cursor — unsolicited effect, strong AI signal. Remove from DESIGN.md."),
            (r"\bgrid[\s-]background\b",
             "Grid background — present in 90% of AI dev portfolios. Use a solid background."),
            (r"\bglassmorphism\b",
             "Glassmorphism — exhausted trend. Allow only for functional modals/dropdowns."),
            (r"\bneon[\s-]glow\b|\bneon[\s-]accent",
             "Neon glow/accents — immediate AI cyberpunk signal."),
            (r"\bparticle(?:s)?[\s-](?:background|effect|js)\b",
             "Particles background — overdone since 2018, strong AI signal."),
            (r"\btyp(?:ewriter|ed)[\s-]effect\b|\btyped\.js\b",
             "Typewriter/typed effect — dev portfolio cliche. Static title only."),
            (r"\bsys[_\s]status\b",
             "SYS_STATUS badge — unsolicited AI injection. Must be justified in the brief."),
            (r"\bhero[\s-]badge\b",
             "Decorative hero badge — the info is already in H1/H2. Remove."),
            (r"\bstyle\s+(?:monitoring|grafana|datadog)\b",
             "Monitoring/Grafana style as a theme — generic AI choice for sysadmin profiles."),
        ]

        found = []
        for pattern, message in FORBIDDEN_THEMES:
            if re.search(pattern, self.content, re.IGNORECASE):
                found.append(message)

        for msg in found:
            self.errors.append(f"[FORBIDDEN THEME] {msg}")

        if found:
            self.errors.append(
                "-> Fix DESIGN.md before any code. "
                "Each forbidden concept must be replaced with a description "
                "specific to the real project, not the sector."
            )

    def _validate_structure(self):
        """Verify all mandatory sections exist."""
        required = ["theme", "colors", "typography", "spacing", "components", "animations"]
        for section in required:
            if not self.sections.get(section):
                self.errors.append(f"[ERROR] Mandatory section missing: {section}")

    def _validate_typography(self):
        """Validate typography (max 2 fonts)."""
        typography_section = self.sections.get("typography", "")

        # Detect mentioned fonts
        font_patterns = [
            r"(?:Font|Typeface):\s*([A-Za-z\s]+?)(?:\n|,|$)",
            r"\*\*([A-Za-z\s]+?)\*\*.*?(?:Display|Body|Monospace)",
        ]

        fonts = set()
        for pattern in font_patterns:
            matches = re.findall(pattern, typography_section, re.IGNORECASE)
            fonts.update(m.strip() for m in matches if m.strip())

        # Exclude non-font keywords
        exclude = {"font", "typeface", "reason", "usage", "weight", "spacing"}
        fonts = {f for f in fonts if f.lower() not in exclude and len(f) > 2}

        # Max 2 families — monospace counts as the 3rd family
        # Rationale: 3 families = AI slop signal (the generator always adds a mono)
        # If a mono is needed, it must replace display or body, not add to them.
        if len(fonts) > 2:
            self.errors.append(
                f"[ERROR] Too many fonts ({len(fonts)}): {', '.join(sorted(fonts))}. "
                f"Max 2 families — monospace counts as the 3rd. "
                f"If JetBrains Mono / Fira Code is needed, replace display or body, do not add."
            )
        elif len(fonts) < 2:
            self.warnings.append(f"[WARN] Insufficient fonts ({len(fonts)}): minimum 2 required")

        # Generic font check (antipattern)
        generic_fonts = {"helvetica", "arial", "times new roman", "georgia", "verdana"}
        for font in fonts:
            if font.lower() in generic_fonts:
                self.errors.append(f"[ERROR] Generic font detected: {font}. Use Google Fonts or custom")

    def _validate_hierarchy(self):
        """§4 — Validate typography size ranges.

        Sources:
        - H1 28–80px  : readable display range (below = no hierarchy, above = AI-slop giant hero)
        - H2 22–60px  : section subtitle range
        - H3 18–36px  : card/sub-section title range
        - P  13–18px  : WCAG body-text readability (below = inaccessible, above = AI signal)
        - Small 11–14px : caption / meta

        §4 must be present. This validation closes the last subjective gap
        in the pipeline ("verifiable > subjective").
        """
        hierarchy_section = self.sections.get("hierarchy", "")
        if not hierarchy_section:
            self.warnings.append(
                "[WARN] Section '## 4. Typography Hierarchy' missing. "
                "Define H1/H2/H3/P/Small with px sizes for automated validation."
            )
            return

        # Recommended ranges in px (min, max)
        RANGES = {
            "h1":    (28, 80),
            "h2":    (22, 60),
            "h3":    (18, 36),
            "p":     (13, 18),
            "small": (11, 14),
        }

        # Matches lines like "- **H1**: 48px / 700 / 1.2"
        # or "- **P (Paragraph)**: 16px ..." — capture the label and the first px value
        # The label can contain a digit (H1, H2, H3) — hence [A-Za-z]\w*
        line_pattern = re.compile(
            r"^\s*-\s*\*\*\s*([A-Za-z]\w*)(?:\s*\([^)]+\))?\s*\*\*\s*:\s*(\d+)\s*px",
            re.MULTILINE
        )

        found_levels = set()
        for match in line_pattern.finditer(hierarchy_section):
            label = match.group(1).lower()
            val = int(match.group(2))
            if label not in RANGES:
                continue
            found_levels.add(label)
            lo, hi = RANGES[label]
            if val < lo:
                self.errors.append(
                    f"[ERROR] §4 Hierarchy: {label.upper()} too small ({val}px). "
                    f"Expected range: {lo}-{hi}px."
                )
            elif val > hi:
                self.errors.append(
                    f"[ERROR] §4 Hierarchy: {label.upper()} too large ({val}px). "
                    f"Expected range: {lo}-{hi}px."
                )

        # At minimum H1 and P must be declared with px values
        if "h1" not in found_levels:
            self.warnings.append(
                "[WARN] §4 Hierarchy: H1 missing or without a px value. "
                "Expected format: '- **H1**: 48px / 700 / 1.2'."
            )
        if "p" not in found_levels:
            self.warnings.append(
                "[WARN] §4 Hierarchy: P (body text) missing or without a px value. "
                "Expected format: '- **P**: 16px / 400 / 1.6'."
            )

    def _validate_colors(self):
        """Validate the color palette."""
        colors_section = self.sections.get("colors", "")

        # Detect hex colors
        hex_pattern = r"#[0-9A-Fa-f]{6}"
        colors = re.findall(hex_pattern, colors_section)

        if len(colors) < 4:
            self.errors.append(f"[ERROR] Too few colors ({len(colors)}). Minimum 4 required")
        elif len(colors) > 8:
            self.errors.append(f"[ERROR] Too many colors ({len(colors)}). Maximum 8 recommended")

        # Check semantic roles
        roles = [
            "primary",
            "secondary",
            "accent",
            "background", "bg",
            "foreground", "text",
            "success",
            "warning",
            "danger", "destructive", "error",
            "muted", "border", "surface",
            "ring", "card",
        ]
        found_roles = sum(1 for role in roles if role.lower() in colors_section.lower())

        if found_roles < 4:
            self.warnings.append(f"[WARN] Insufficient semantic roles ({found_roles}). Minimum 4 recommended")

        # Cliche gradients
        cliche_gradients = [
            (r"blue.*?purple", "blue->purple"),
            (r"pink.*?purple", "pink->purple"),
            (r"pink.*?red", "pink->red"),
            (r"cyan.*?blue", "cyan->blue"),
        ]

        for pattern, name in cliche_gradients:
            if re.search(pattern, colors_section, re.IGNORECASE):
                self.warnings.append(f"[WARN] Cliche gradient detected: {name}. Justify by semantic role")

    def _validate_spacing(self):
        """Validate that all spacings are multiples of 8px."""
        spacing_section = self.sections.get("spacing", "")

        # Detect spacing values
        spacing_pattern = r"(\d+)\s*px"
        spacings = re.findall(spacing_pattern, spacing_section)

        invalid_spacings = []
        for spacing in spacings:
            value = int(spacing)
            if value % 8 != 0 and value != 4:  # 4px acceptable for micro-spacings
                invalid_spacings.append(value)

        if invalid_spacings:
            self.errors.append(
                f"[ERROR] Spacings not multiples of 8px: {invalid_spacings}. "
                f"Use: 4, 8, 16, 24, 32, 48, 64"
            )

        # 8px grid mentioned?
        if "8px" not in spacing_section and "8 px" not in spacing_section:
            self.warnings.append("[WARN] 8px grid not explicitly mentioned")

    def _validate_animations(self):
        """Validate animations (duration <= 400ms) — handles ms and s separately."""
        animations_section = self.sections.get("animations", "")

        # Explicit millisecond durations (e.g. 200ms, 300ms, 50ms)
        ms_raw = re.findall(r"(\d+(?:\.\d+)?)\s*ms\b", animations_section)
        ms_values = [(float(v), f"{v}ms") for v in ms_raw]

        # Durations in seconds (e.g. 0.3s, 1s, 2s) — exclude the word "seconds"
        # The pattern does NOT match "Nms" because after N comes 'm', not 's' directly.
        s_raw = re.findall(r"(\d+(?:\.\d+)?)\s*s(?!econds)\b", animations_section)
        s_values = [(float(v) * 1000, f"{v}s -> {float(v)*1000:.0f}ms") for v in s_raw]

        all_durations = ms_values + s_values
        invalid_durations = [(ms_val, label) for ms_val, label in all_durations if ms_val > 400]

        if invalid_durations:
            # Exception: if Three.js is in scope (§10), long durations are legitimate
            # for scroll scrub, 60fps loops, etc.
            if getattr(self, "_has_threejs", False):
                long_ui = [(ms, l) for ms, l in invalid_durations if ms < 5000]
                if long_ui:
                    labels = [l for _, l in long_ui]
                    self.warnings.append(
                        f"[WARN] Long animations (likely Three.js scroll/loop): {chr(39).join(labels)}. "
                        f"If UI transitions: max 400ms. If Three.js: document in §10."
                    )
            else:
                labels = [label for _, label in invalid_durations]
                self.errors.append(
                    f"[ERROR] Animations too long: {', '.join(labels)}. "
                    f"Maximum 400ms recommended"
                )

        # prefers-reduced-motion?
        if "prefers-reduced-motion" not in animations_section.lower():
            self.warnings.append("[WARN] No mention of prefers-reduced-motion")

    # ------------------------------------------------------------------ #
    # WCAG AA Contrast                                                    #
    # ------------------------------------------------------------------ #

    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert #RRGGBB to (R, G, B) tuple — 0-255."""
        h = hex_color.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    def _relative_luminance(self, rgb: tuple) -> float:
        """WCAG 2.1 relative luminance (https://www.w3.org/TR/WCAG21/#dfn-relative-luminance)."""
        def linearize(c: int) -> float:
            s = c / 255.0
            return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4
        r, g, b = (linearize(c) for c in rgb)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    def _contrast_ratio(self, hex1: str, hex2: str) -> float:
        """WCAG contrast ratio between two hex colors."""
        l1 = self._relative_luminance(self._hex_to_rgb(hex1))
        l2 = self._relative_luminance(self._hex_to_rgb(hex2))
        lighter, darker = max(l1, l2), min(l1, l2)
        return (lighter + 0.05) / (darker + 0.05)

    def _validate_wcag_contrast(self):
        """Validate WCAG AA contrast (text 4.5:1, UI elements 3.0:1)."""
        colors_section = self.sections.get("colors", "")
        hex_pattern = r"#[0-9A-Fa-f]{6}"

        # Extract (semantic role, hex color) pairs from the table
        role_map: Dict[str, str] = {}
        for line in colors_section.splitlines():
            hexes = re.findall(hex_pattern, line)
            if not hexes:
                continue
            # Parse role from column 1 of the markdown table (between first two pipes)
            cells = [c.strip() for c in line.split("|")]
            role_cell = cells[1].lower() if len(cells) > 2 else line.lower()
            if any(k in role_cell for k in ("text", "foreground", "body")):
                role_map.setdefault("text", hexes[0])
            elif any(k in role_cell for k in ("background", "bg", "surface")):
                role_map.setdefault("bg", hexes[0])
            elif "primary" in role_cell:
                role_map.setdefault("primary", hexes[0])

        if "text" not in role_map or "bg" not in role_map:
            self.warnings.append(
                "[WARN] WCAG: cannot identify Text/Background automatically. "
                "Name the roles 'Text' and 'Background' explicitly in the color table."
            )
            return

        # Text / Background contrast — WCAG AA normal text: 4.5:1
        ratio_text = self._contrast_ratio(role_map["text"], role_map["bg"])
        if ratio_text < 4.5:
            self.errors.append(
                f"[ERROR] WCAG AA: insufficient Text/Background contrast {ratio_text:.2f}:1 "
                f"({role_map['text']} on {role_map['bg']}). Minimum: 4.5:1"
            )

        # Primary / Background contrast — WCAG AA UI elements: 3.0:1
        if "primary" in role_map:
            ratio_ui = self._contrast_ratio(role_map["primary"], role_map["bg"])
            if ratio_ui < 3.0:
                self.errors.append(
                    f"[ERROR] WCAG AA: insufficient Primary/Background contrast {ratio_ui:.2f}:1 "
                    f"({role_map['primary']} on {role_map['bg']}). UI minimum: 3.0:1"
                )

    def _validate_components(self):
        """Validate components (max 3 variants)."""
        components_section = self.sections.get("components", "")

        # Detect button variants
        button_pattern = r"### Variants.*?(?=###|$)"
        button_section = re.search(button_pattern, components_section, re.DOTALL)

        if button_section:
            variants = re.findall(r"\d\.\s+\*\*([^*]+)\*\*", button_section.group(0))
            if len(variants) > 3:
                self.errors.append(
                    f"[ERROR] Too many button variants ({len(variants)}). Maximum 3 recommended"
                )

    def _detect_antipatterns(self):
        """Detect antipatterns (AI slop)."""
        content_lower = self.content.lower()

        # Generic Lucide icons
        lucide_icons = ["sparkles", "zap", "cog", "network", "arrow", "check", "star"]
        found_icons = [icon for icon in lucide_icons if re.search(rf"\b{icon}\b", content_lower)]

        if found_icons:
            self.warnings.append(
                f"[WARN] Generic Lucide icons detected: {', '.join(found_icons)}. "
                f"Consider custom SVG or a consistent pack"
            )

        # Vague buzzwords
        buzzwords = ["premium", "modern", "elegant", "amazing", "incredible"]
        found_buzzwords = [bw for bw in buzzwords if re.search(rf"\b{bw}\b", content_lower)]

        if found_buzzwords:
            self.warnings.append(
                f"[WARN] Vague buzzwords: {', '.join(found_buzzwords)}. "
                f"Replace with precise descriptions"
            )

        # Generic template sections
        template_sections = ["hero", "features", "cta", "testimonials", "footer"]
        found_sections = sum(1 for sec in template_sections if sec in content_lower)

        if found_sections >= 4:
            self.warnings.append(
                f"[WARN] Generic template structure detected ({found_sections} sections). "
                f"Consider a more unique approach"
            )

        # Uniform gradients
        if "gradient" in content_lower:
            gradient_count = len(re.findall(r"gradient", content_lower))
            if gradient_count > 3:
                self.warnings.append(
                    f"[WARN] Too many gradients ({gradient_count}). "
                    f"Limit to 2-3 intentional gradients"
                )



    def _validate_ux_completeness(self):
        """Verify UX completeness — rules surfaced by real visual audits.
        Catches frequent gaps not covered by other validators."""
        components_section = self.sections.get("components", "")
        spacing_section    = self.sections.get("spacing", "")
        animations_section = self.sections.get("animations", "")

        # ── Odd N project grid ────────────────────────────────────────────
        # If §6 mentions a card/project grid, verify the odd-count behavior
        # is documented.
        has_grid = any(k in components_section.lower() for k in
                       ["grid", "card", "project"])
        has_odd_rule = any(k in components_section.lower() for k in
                           ["odd", "last-card", "last card", "full-width", "2xn"])
        if has_grid and not has_odd_rule:
            self.warnings.append(
                "[WARN] §6 Components: card grid detected but odd-N behavior undocumented. "
                "Add: last-card behavior on odd counts "
                "(e.g. last-card full-width, or left-align, or 2xN grid)."
            )

        # ── Contact section density ───────────────────────────────────────
        has_contact = any(k in components_section.lower() for k in
                          ["contact", "form", "cta", "email"])
        if not has_contact:
            self.warnings.append(
                "[WARN] §6 Components: Contact/CTA section undocumented. "
                "Define minimum density (max 96px vertical padding, "
                "minimum content: title + subtitle + action)."
            )

        # ── Hero scroll cue ───────────────────────────────────────────────
        has_scroll_cue = any(k in animations_section.lower() for k in
                             ["scroll", "chevron", "indicator", "scroll cue", "next section"])
        has_hero = "hero" in self.content.lower()
        if has_hero and not has_scroll_cue:
            self.warnings.append(
                "[WARN] §7 Motion: hero detected but scroll cue undocumented. "
                "Document the transition signal to the next section "
                "(animated chevron, transition shadow, or subtle parallax)."
            )

    def _validate_dark_mode(self):
        """Verify Dark Mode section is present and properly defined."""
        darkmode_section = self.sections.get("darkmode", "")

        if not darkmode_section:
            # If main background < #333 -> dark-first project -> blocking error
            colors_section = self.sections.get("colors", "")
            bg_hex = None
            for line in colors_section.splitlines():
                if any(k in line.lower() for k in ("background", "bg", "surface")):
                    hexes = re.findall(r"#[0-9A-Fa-f]{6}", line)
                    if hexes:
                        bg_hex = hexes[0]
                        break
            if bg_hex:
                lum = self._relative_luminance(self._hex_to_rgb(bg_hex))
                if lum < 0.09:
                    self.errors.append(
                        f"[ERROR] §8 Dark Mode missing but main background is dark ({bg_hex}, lum={lum:.3f}). "
                        f"Dark-first project: §8 is mandatory. "
                        f"Document surface, secondary-text, dark-border."
                    )
                    return
            # Light background or undetected -> warning only
            self.warnings.append(
                "[WARN] Section '## 8. Dark Mode' missing from DESIGN.md. "
                "Without an explicit dark mode contract, the implementation will be improvised — "
                "slop comes back through the window. "
                "Add a section with the inverted tokens (dark-bg, dark-text, dark-surface)."
            )
            return

        # Verify hex declarations in the dark section
        dark_hexes = re.findall(r"#[0-9A-Fa-f]{6}", darkmode_section)
        if len(dark_hexes) < 3:
            self.warnings.append(
                f"[WARN] Dark Mode section insufficient: {len(dark_hexes)} color(s) declared. "
                f"Minimum 3 required (dark-bg, dark-text, dark-surface)."
            )

        # Verify minimal roles are present
        required_dark_roles = ["background", "text", "surface"]
        missing = [r for r in required_dark_roles if r not in darkmode_section.lower()]
        if missing:
            self.warnings.append(
                f"[WARN] Missing dark mode roles: {', '.join(missing)}. "
                f"Explicitly declare dark-bg, dark-text and dark-surface."
            )

        # Verify dark background is actually dark (luminance < 9%)
        for line in darkmode_section.splitlines():
            if any(k in line.lower() for k in ("background", "bg")):
                hexes = re.findall(r"#[0-9A-Fa-f]{6}", line)
                if hexes:
                    lum = self._relative_luminance(self._hex_to_rgb(hexes[0]))
                    if lum > 0.09:
                        self.warnings.append(
                            f"[WARN] Dark mode background too light ({hexes[0]}, luminance {lum:.2f}). "
                            f"Recommended: < #333 for comfortable dark mode."
                        )
                    break

        # ── Unfilled placeholders ────────────────────────────────────────
        # Same loophole as §9: section present but `[Ex: ...]` left as-is
        # means the agent never committed to actual values.
        self._check_unfilled_placeholders("§8 Dark Mode", darkmode_section)


    def _validate_mobile(self):
        """Validate Mobile section (§9) if present.
        Checks native units (pt/dp/sp), touch targets,
        safe areas, and system animation patterns."""
        mobile_section = self.sections.get("mobile", "")

        if not mobile_section:
            # Not an error — optional section for web-only projects
            return

        # ── Native units ─────────────────────────────────────────────────
        # Detect hardcoded px in native mobile context
        # (iOS = pt, Android = dp, Flutter = logical pixels, RN = dp)
        platform_section = mobile_section.lower()
        is_native = any(k in platform_section for k in [
            "swiftui", "flutter", "jetpack", "compose", "react native", "react-native",
            "ios", "android", "uikit", "swift", "kotlin"
        ])

        if is_native:
            # Look for hardcoded px outside of a CSS context
            px_in_native = re.findall(
                r"(?<!font-size:)(?<!padding:)(?<!margin:)\b(\d+)px\b",
                mobile_section
            )
            if px_in_native:
                self.warnings.append(
                    f"[WARN] px units in native mobile context: {px_in_native[:5]}. "
                    f"Use pt (iOS), dp (Android), or logical pixels (Flutter/RN)."
                )

        # ── Touch targets ─────────────────────────────────────────────────
        # iOS HIG: 44pt min, Android Material: 48dp min
        touch_target_mentioned = any(k in mobile_section.lower() for k in [
            "touch target", "tap target", "44pt", "44dp", "48dp", "48pt",
            "tap size", "tap area", "minimum tap"
        ])
        if not touch_target_mentioned:
            self.warnings.append(
                "[WARN] Minimum touch target size undocumented in §9 Mobile. "
                "iOS HIG: 44pt min, Material Design: 48dp min."
            )

        # ── Safe areas ────────────────────────────────────────────────────
        safe_area_mentioned = any(k in mobile_section.lower() for k in [
            "safe area", "safeareainsets", "edgeinsets", "notch", "dynamic island",
            "home indicator", "status bar", "navigation bar", "insets"
        ])
        if not safe_area_mentioned:
            self.warnings.append(
                "[WARN] Safe Areas handling undocumented in §9 Mobile. "
                "Document how the layout respects notch/Dynamic Island/Home Indicator."
            )

        # ── Mobile animations ────────────────────────────────────────────
        # System animations (spring, easeInOut) are allowed even > 400ms
        # because they respect the platform's native rhythm
        anim_section = mobile_section
        ms_raw = re.findall(r"(\d+(?:\.\d+)?)\s*ms\b", anim_section)
        s_raw  = re.findall(r"(\d+(?:\.\d+)?)\s*s(?!econds)\b", anim_section)
        all_ms = [float(v) for v in ms_raw] + [float(v)*1000 for v in s_raw]

        # Skip if spring/system is mentioned (native animations without fixed duration)
        is_spring = any(k in anim_section.lower() for k in [
            "spring", "uispringtiming", "withspring", "animation.spring",
            "springanimation", "system animation"
        ])
        if not is_spring:
            violations = [v for v in all_ms if v > 500]  # looser threshold on mobile
            if violations:
                self.warnings.append(
                    f"[WARN] Long mobile animations: {violations}ms. "
                    f"On mobile, prefer spring() or <= 400ms for transitions."
                )

        # ── Mobile accessibility ──────────────────────────────────────────
        a11y_mentioned = any(k in mobile_section.lower() for k in [
            "accessibilitylabel", "contentdescription", "talkback", "voiceover",
            "accessibility", "a11y", "semantics"
        ])
        if not a11y_mentioned:
            self.warnings.append(
                "[WARN] Mobile accessibility undocumented in §9. "
                "Mention VoiceOver (iOS) / TalkBack (Android) and accessibility labels."
            )

        # ── Component anatomy ────────────────────────────────────────────
        # Structural contract — without these, the agent only edits tokens.
        # The 6 subsections override §6 for mobile native targets.
        required_subsections = [
            ("Screen patterns",   r"####\s+Screen\s+patterns\b"),
            ("Navigation pattern",r"####\s+Navigation\s+pattern\b"),
            ("Card anatomy",      r"####\s+Card\s+anatomy\b"),
            ("List item",         r"####\s+List\s+item\b"),
            ("Primary CTA",       r"####\s+Primary\s+CTA\b"),
            ("States",            r"####\s+States\b"),
        ]
        missing_anatomy = [
            name for name, pattern in required_subsections
            if not re.search(pattern, mobile_section, re.IGNORECASE)
        ]
        if missing_anatomy:
            self.errors.append(
                f"[ERROR] §9 Mobile component anatomy incomplete — missing subsections: "
                f"{', '.join(missing_anatomy)}. "
                f"Without structural contract the agent only edits tokens. "
                f"Use templates/design-md-template.md §9 as the base."
            )

        # ── Unfilled placeholders ────────────────────────────────────────
        self._check_unfilled_placeholders("§9 Mobile", mobile_section)

        # If the section is well-filled, confirm silently
        if mobile_section and len(mobile_section) > 200:
            pass  # No useless message

    def _check_unfilled_placeholders(self, section_label: str, section_content: str):
        """Reject unfilled bracket placeholders that signal a contract not committed to.

        Two shapes block:
          - `[A | B | C]` — multiple choices that should have been narrowed to one
          - `[Ex: ...]`   — example placeholders left as-is

        Without this check, an agent can ship a DESIGN.md that looks complete
        (sections present) but commits to no structural decision — the exact
        loophole that lets the implementation fall back to token edits only.
        """
        # Choice-style placeholders: [option1 | option2 | option3]
        choice_pattern = re.compile(r"\[[^\]\n]+\|[^\]\n]+\]")
        choices = choice_pattern.findall(section_content)
        # Example-style placeholders: [Ex: ...]
        example_pattern = re.compile(r"\[Ex:[^\]]+\]", re.IGNORECASE)
        examples = example_pattern.findall(section_content)

        if choices:
            sample = choices[:3]
            self.errors.append(
                f"[ERROR] {section_label}: {len(choices)} unfilled choice placeholder(s) "
                f"(e.g. {sample}). Narrow each '[A | B | C]' to a single committed value."
            )
        if examples:
            sample = examples[:3]
            self.errors.append(
                f"[ERROR] {section_label}: {len(examples)} unfilled '[Ex: ...]' placeholder(s) "
                f"(e.g. {sample}). Replace examples with the project's real values."
            )

    def _validate_dark_mode_required(self):
        """§8 is mandatory if the main background is dark (lum < 9%)."""
        darkmode_section = self.sections.get("darkmode", "")
        if darkmode_section:
            return  # Already validated by _validate_dark_mode()

        # Look for background in §2
        colors_section = self.sections.get("colors", "")
        hex_pat = r"#[0-9A-Fa-f]{6}"

        # First line with "Background" or "bg"
        bg_hex = None
        for line in colors_section.splitlines():
            if any(k in line.lower() for k in ("background", "bg")):
                hexes = re.findall(hex_pat, line)
                if hexes:
                    bg_hex = hexes[0]
                    break

        if bg_hex:
            lum = self._relative_luminance(self._hex_to_rgb(bg_hex))
            if lum < 0.09:  # dark background = dark-first project
                self.errors.append(
                    f"[ERROR] §8 Dark Mode missing but main background is dark "
                    f"({bg_hex}, lum={lum:.3f}). "
                    f"Dark-first project: §8 is mandatory. "
                    f"Document surface, secondary-text, dark-border."
                )

    def _validate_section_density(self):
        """Verify key sections have sufficient density."""
        components_section = self.sections.get("components", "")

        # Verify Contact/CTA section is documented in §6
        has_contact = any(k in components_section.lower() for k in [
            "contact", "cta", "footer", "mail", "email"
        ])
        if not has_contact:
            self.warnings.append(
                "[WARN] §6 Components: Contact/CTA section undocumented. "
                "Define minimum density (max 96px vertical padding, "
                "minimum content: title + subtitle + action)."
            )



    def _validate_threejs(self):
        """Validate Three.js section (§10) if present."""
        threejs_section = self.sections.get("threejs", "")

        if not threejs_section:
            all_content = self.content.lower()
            three_mentioned = any(k in all_content for k in [
                "three.js", "threejs", "webgl", "webglrenderer",
                "from 'three'", 'from "three"'
            ])
            if three_mentioned:
                self.warnings.append(
                    "[WARN] Three.js detected in DESIGN.md but §10 missing. "
                    "Add '## 10. Three.js' with: scene type, geometry budget, "
                    "pixel ratio cap, dispose strategy, WebGL fallback."
                )
            return

        sec = threejs_section.lower()
        self._has_threejs = True  # flag to exempt Three.js durations in §7

        # Scene type
        if not any(k in sec for k in ["hero", "background", "viewer", "scroll",
                                       "interactive", "particle", "product", "ambient"]):
            self.warnings.append(
                "[WARN] §10 Three.js: scene type undocumented. "
                "Specify: hero background | interactive viewer | scroll-driven | particles."
            )

        # Pixel ratio cap
        if not any(k in sec for k in ["devicepixelratio", "pixel ratio", "pixelratio",
                                       "dpr", "math.min", "cap"]):
            self.warnings.append(
                "[WARN] §10 Three.js: pixel ratio undocumented. "
                "Add: Math.min(devicePixelRatio, 2) — cap mandatory "
                "(Retina 3x = 9 pixels/CSS px, without cap GPU cost x 2.25)."
            )

        # Dispose strategy
        if not any(k in sec for k in ["dispose", "teardown", "cleanup",
                                       "memory", "vram"]):
            self.warnings.append(
                "[WARN] §10 Three.js: dispose strategy undocumented. "
                "Three.js never frees VRAM automatically — "
                "document geometry.dispose() + material.dispose() + texture.dispose()."
            )

        # WebGL fallback
        if not any(k in sec for k in ["fallback", "webgl", "support",
                                       "no-webgl", "static image"]):
            self.warnings.append(
                "[WARN] §10 Three.js: WebGL fallback undocumented. "
                "~2% of users have no WebGL — define the behavior "
                "(static image, 2D canvas, or error message)."
            )

        # prefers-reduced-motion
        if not any(k in sec for k in ["prefers-reduced-motion", "reduced-motion",
                                       "reducedmotion", "frozen", "static"]):
            self.warnings.append(
                "[WARN] §10 Three.js: prefers-reduced-motion undocumented. "
                "Frozen scene or slow rotation if reduced-motion is enabled."
            )

        # Renderer singleton
        if not any(k in sec for k in ["renderer", "webglrenderer",
                                       "instance", "singleton", "unique"]):
            self.warnings.append(
                "[WARN] §10 Three.js: renderer strategy undocumented. "
                "A single WebGLRenderer per page — browsers limit to 8-16 GPU contexts."
            )

    def _print_report(self):
        """Print the validation report."""
        print("\n" + "=" * 60)
        print("DESIGN VALIDATION REPORT")
        print("=" * 60)

        if self.errors:
            print(f"\nERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  {error}")

        if self.warnings:
            print(f"\nWARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning}")

        if not self.errors and not self.warnings:
            print("\nVALIDATION PASSED - No errors detected!")

        print("\n" + "=" * 60)
        if self.errors:
            print(f"RESULT: FAILED ({len(self.errors)} errors)")
        elif self.warnings:
            print(f"RESULT: PASSED WITH WARNINGS ({len(self.warnings)} warnings)")
        else:
            print("RESULT: PASSED - Ready to code!")
        print("=" * 60 + "\n")

    # ── §11 Signature Gesture ────────────────────────────────────────────────

    def _validate_signature_gesture(self):
        """§11 — the design must concentrate its creative budget in ONE owned move.

        WARN (never block): a missing/unfilled §11 means the budget is likely
        diffused across forgettable micro-details. If a 'Grep signature' regex is
        declared AND a code path is provided, verify the gesture is actually
        implemented — a declared-but-absent signature is the real failure (the
        original 'grep the pattern' idea is a tautology unless checked against
        real code).
        """
        section = self.sections.get("signature", "")
        if not section:
            self.warnings.append(
                "[WARN] Section '## 11. Signature Gesture' missing. Concentrate the "
                "creative budget in ONE specific, owned move (see templates/design-md-template.md "
                "§11) instead of spreading it across forgettable details."
            )
            return

        # Unfilled placeholders?
        if "[Ex:" in section or "___" in section:
            self.warnings.append(
                "[WARN] §11 Signature Gesture has unfilled placeholders. Replace [Ex: ...] "
                "with the one specific gesture this design owns."
            )
            return

        # Extract the declared grep signature, if any.
        m = re.search(r"Grep signature\**\s*:\s*\**\s*`([^`]+)`", section, re.IGNORECASE)
        if not m:
            self.warnings.append(
                "[WARN] §11 declares a gesture but no `Grep signature` regex. Add one so "
                "check.py --final can verify the gesture is actually implemented."
            )
            return

        pattern = m.group(1).strip()
        if not self.code_path:
            # Nothing to verify against — note it and move on.
            self.warnings.append(
                f"[INFO] §11 signature `{pattern}` declared. Run with --code <path> so the "
                "gate can verify it is implemented in the rendered code."
            )
            return

        # Verify the signature appears in the code.
        try:
            compiled = re.compile(pattern, re.IGNORECASE)
        except re.error:
            self.warnings.append(
                f"[WARN] §11 `Grep signature` is not a valid regex: {pattern!r}. "
                "Use a simple pattern like `border-left.*transition`."
            )
            return

        found = self._grep_code(compiled)
        if found:
            # Genuine implemented signature — this is the one thing we reward.
            print(f"[OK] §11 signature gesture implemented: `{pattern}` found in {found}")
        else:
            self.warnings.append(
                f"[WARN] §11 signature `{pattern}` is declared in DESIGN.md but NOT found in "
                f"the code ({self.code_path}). Implement the owned gesture or correct the regex — "
                "a signature that exists only on paper is not a signature."
            )

    def _grep_code(self, compiled) -> str:
        """Return the first code file matching `compiled`, or '' if none."""
        root = Path(self.code_path)
        exts = {".html", ".htm", ".css", ".scss", ".sass", ".less",
                ".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte", ".astro"}
        if root.is_file():
            candidates = [root]
        else:
            candidates = [p for p in root.rglob("*")
                          if p.is_file() and p.suffix.lower() in exts]
        for p in candidates:
            try:
                if compiled.search(p.read_text(encoding="utf-8", errors="ignore")):
                    return str(p)
            except OSError:
                continue
        return ""

    # ── §12 Intentional Tensions ─────────────────────────────────────────────

    def _validate_tensions(self):
        """§12 — 'waouh' comes from deliberate contrast. Require >=2 tension pairs.

        WARN (never block): fewer than 2 declared tensions, or tensions that all
        read as 'moderate' (no real contrast), are flagged. We can count pairs and
        detect uniformity heuristically; we cannot judge whether a tension is
        *good* — that stays a nudge, not a block.
        """
        section = self.sections.get("tensions", "")
        if not section:
            self.warnings.append(
                "[WARN] Section '## 12. Intentional Tensions' missing. Name at least 2 "
                "deliberate contrasts (typography, density, colour...) — harmony alone is "
                "forgettable. See templates/design-md-template.md §12."
            )
            return

        if "[Ex:" in section or "___" in section:
            self.warnings.append(
                "[WARN] §12 Intentional Tensions has unfilled placeholders. Replace [Ex: ...] "
                "with the real contrasts this design commits to."
            )
            return

        # Count tension lines: bullet items starting with a T<n> label.
        pairs = re.findall(r"^\s*[-*]\s*\**\s*T\d+\b", section, re.MULTILINE)
        n = len(pairs)
        if n == 0:
            self.warnings.append(
                "[WARN] §12 present but no tension pairs found. Use the format "
                "'- T1 Typography: <pole A> / <pole B> — <ratio>'. Minimum 2."
            )
            return
        if n < 2:
            self.warnings.append(
                f"[WARN] §12 declares only {n} tension pair. A single contrast is not a system "
                "of tensions — name at least 2 (typography, density, colour, motion...)."
            )
            return

        # Heuristic uniformity check: if 'moderate'/'balanced'/'subtle' dominate
        # and no contrast ratio or '/' pole-split appears, the tensions are likely flat.
        low = section.lower()
        flat_terms = low.count("moderate") + low.count("balanced") + low.count("subtle")
        has_contrast = bool(re.search(r"\d+\s*[:/]\s*\d+", section)) or section.count("/") >= 2
        if flat_terms >= 2 and not has_contrast:
            self.warnings.append(
                "[WARN] §12 tensions read as uniformly 'moderate/balanced' with no sharp "
                "contrast (no ratios, no clear pole splits). If everything is moderate, there "
                "is no tension — push at least one pair to a real extreme."
            )


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 validate_design.py DESIGN.md [--strict] [--code <path>]")
        sys.exit(1)

    filepath = sys.argv[1]
    strict = "--strict" in sys.argv
    code_path = None
    if "--code" in sys.argv:
        i = sys.argv.index("--code")
        if i + 1 < len(sys.argv):
            code_path = sys.argv[i + 1]

    validator = DesignValidator(filepath, strict, code_path)
    success = validator.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
