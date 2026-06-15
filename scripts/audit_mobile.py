#!/usr/bin/env python3
"""
audit_mobile.py — native craft + mobile gates for SwiftUI / Jetpack Compose /
Flutter / React Native.

The web gates (audit_beauty, audit_style_uniqueness) judge HTML/CSS/JSX. They
say nothing about whether a *native* screen respects platform ergonomics or
reads as a real app rather than a shrunk-down website. This auditor closes that
gap.

It auto-detects the platform from source extensions and imports, then scores
five mobile dimensions (0-100) and collects hard **blockers** — accessibility
non-negotiables (sub-minimum touch targets, no safe-area handling) that block
delivery regardless of the craft score.

Dimensions:
  M1  Touch ergonomics      (25)  — no sub-min targets (44pt iOS / 48dp Android)
  M2  Safe-area handling     (20)  — notch / home-indicator insets respected
  M3  Native navigation      (15)  — a real native nav container, not a div menu
  M4  Type & spacing craft   (20)  — semantic text styles + grid, not magic px
  M5  Motion & finish         (20)  — native animation + tactile feedback

Exit codes:
  0 — score ≥ pass AND no blockers
  1 — floor ≤ score < pass, no blockers
  2 — score < floor, OR any hard blocker (delivery blocked)
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def _ansi(code: str) -> str:
    return f"\033[{code}m" if sys.stdout.isatty() else ""

RESET, BOLD = _ansi("0"), _ansi("1")
RED, YELLOW, GREEN, CYAN, DIM = _ansi("31"), _ansi("33"), _ansi("32"), _ansi("36"), _ansi("2")


# ── Platform detection ───────────────────────────────────────────────────────

PLATFORMS = {
    "swiftui": {"exts": {".swift"}, "min_touch": 44, "unit": "pt"},
    "compose": {"exts": {".kt", ".kts"}, "min_touch": 48, "unit": "dp"},
    "flutter": {"exts": {".dart"}, "min_touch": 48, "unit": "dp"},
    "react-native": {"exts": {".tsx", ".jsx", ".ts", ".js"}, "min_touch": 44, "unit": "pt"},
}
SKIP_DIRS = {"node_modules", ".git", "build", ".dart_tool", "Pods", "DerivedData", "__pycache__"}


def detect_platform(files: list[Path]) -> str | None:
    """Pick the dominant native platform. React Native only if RN imports exist."""
    counts = {p: 0 for p in PLATFORMS}
    rn_signal = False
    for f in files:
        suf = f.suffix
        if suf == ".swift":
            counts["swiftui"] += 1
        elif suf in (".kt", ".kts"):
            counts["compose"] += 1
        elif suf == ".dart":
            counts["flutter"] += 1
        elif suf in (".tsx", ".jsx", ".ts", ".js"):
            try:
                head = f.read_text(encoding="utf-8", errors="replace")[:2000]
            except OSError:
                continue
            if re.search(r"react-native|from ['\"]expo|expo-router|@expo/", head):
                rn_signal = True
                counts["react-native"] += 1
    # Prefer a true-native platform if present; RN needs the import signal.
    native = {k: v for k, v in counts.items() if k != "react-native" and v > 0}
    if native:
        return max(native, key=native.get)
    if rn_signal and counts["react-native"] > 0:
        return "react-native"
    return None


# ── Per-platform pattern sets ────────────────────────────────────────────────
# Each: regexes for safe-area, native nav, animation, tactile, type, spacing,
# plus an interactive-element + explicit-size detector for touch targets.

PATTERNS = {
    "swiftui": {
        "safe_area": r"\.safeAreaInset\b|safeAreaPadding|\.safeAreaInsets\b",
        "nav": r"\b(?:NavigationStack|NavigationSplitView|TabView|NavigationView)\b",
        "anim": r"\bwithAnimation\b|\.animation\(|\bmatchedGeometryEffect\b|\.transition\(",
        "tactile": r"UIImpactFeedbackGenerator|\.sensoryFeedback\(|UISelectionFeedbackGenerator",
        "type_good": r"\.font\(\.(?:largeTitle|title|title2|title3|headline|subheadline|body|callout|caption|footnote)\)|\.dynamicTypeSize",
        "spacing": r"\.padding\(\s*\d+|spacing:\s*\d+",
        "interactive": r"\bButton\b|\.onTapGesture\b",
        # frame height/width with a literal < min
        "fixed_size": r"\.frame\([^)]*(?:height|width)\s*:\s*(\d+)",
    },
    "compose": {
        "safe_area": r"systemBarsPadding|WindowInsets|navigationBarsPadding|statusBarsPadding|safeDrawing",
        "nav": r"\bScaffold\b|\bNavigationBar\b|\bBottomNavigation\b|\bNavHost\b|\bTopAppBar\b",
        "anim": r"animate\w*AsState|AnimatedVisibility|AnimatedContent|updateTransition|rememberInfiniteTransition",
        "tactile": r"LocalHapticFeedback|performHapticFeedback|indication\s*=|rememberRipple",
        "type_good": r"MaterialTheme\.typography|style\s*=\s*MaterialTheme\.typography|Typography\(",
        "spacing": r"\.padding\(\s*\d+\.dp|Arrangement\.spacedBy\(\s*\d+\.dp",
        "interactive": r"\bButton\b|\.clickable\b|IconButton|\bTextButton\b",
        "fixed_size": r"\.size\(\s*(\d+)\.dp|\.height\(\s*(\d+)\.dp",
    },
    "flutter": {
        "safe_area": r"\bSafeArea\b|MediaQuery\.of\([^)]*\)\.padding|viewPadding|SliverSafeArea",
        "nav": r"\bScaffold\b|BottomNavigationBar|\bNavigationBar\b|\bNavigationRail\b|\bAppBar\b",
        "anim": r"AnimatedContainer|AnimationController|\bHero\b|AnimatedBuilder|\bTween\b|\.animate\(",
        "tactile": r"HapticFeedback\.|InkWell|InkResponse|splashColor",
        "type_good": r"Theme\.of\([^)]*\)\.textTheme|TextTheme|\.titleLarge|\.bodyMedium|\.headlineSmall",
        "spacing": r"EdgeInsets\.\w+\(\s*\d+|SizedBox\(\s*(?:height|width):\s*\d+",
        "interactive": r"ElevatedButton|TextButton|IconButton|GestureDetector|InkWell|\bButton\b",
        "fixed_size": r"(?:height|width|minHeight|minWidth)\s*:\s*(\d+)",
    },
    "react-native": {
        "safe_area": r"SafeAreaView|useSafeAreaInsets|SafeAreaProvider|react-native-safe-area",
        "nav": r"@react-navigation|createBottomTabNavigator|createNativeStackNavigator|NavigationContainer",
        "anim": r"Animated\.|useSharedValue|withTiming|withSpring|react-native-reanimated|LayoutAnimation",
        "tactile": r"Haptics\.|HapticFeedback|impactAsync|TouchableOpacity|Pressable",
        "type_good": r"fontSize:\s*(?:typography|theme|tokens)|variant=|textStyle",
        "spacing": r"(?:padding|margin|gap)\w*:\s*\d+",
        "interactive": r"TouchableOpacity|Pressable|TouchableHighlight|<Button\b",
        "fixed_size": r"(?:height|minHeight)\s*:\s*(\d+)",
    },
}


class MobileAuditor:
    DIMENSIONS = [
        ("M1", "Touch ergonomics", 25),
        ("M2", "Safe-area handling", 20),
        ("M3", "Native navigation", 15),
        ("M4", "Type & spacing craft", 20),
        ("M5", "Motion & finish", 20),
    ]

    def __init__(self, root: Path, floor: int = 50, passing: int = 70) -> None:
        self.root = root
        self.floor = floor
        self.passing = passing
        self.platform: str | None = None
        self.score = 0
        self.dimension_scores: dict[str, int] = {}
        self.findings: list[dict[str, Any]] = []
        self.weaknesses: list[dict[str, Any]] = []
        self.blockers: list[dict[str, Any]] = []
        self._texts: list[tuple[Path, str]] = []

    def _collect(self) -> list[Path]:
        out: list[Path] = []
        exts = set().union(*(p["exts"] for p in PLATFORMS.values()))
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in filenames:
                p = Path(dirpath) / fn
                if p.suffix in exts:
                    out.append(p)
        return out

    def scan(self) -> None:
        files = self._collect()
        self.platform = detect_platform(files)
        if not self.platform:
            return
        exts = PLATFORMS[self.platform]["exts"]
        for f in files:
            if f.suffix not in exts:
                continue
            try:
                self._texts.append((f, f.read_text(encoding="utf-8", errors="replace")))
            except OSError:
                continue
        self._score_touch()
        self._score_safe_area()
        self._score_nav()
        self._score_type_spacing()
        self._score_motion()
        self.score = min(sum(self.dimension_scores.values()), 100)

    def _present(self, key: str) -> bool:
        rx = re.compile(PATTERNS[self.platform][key])
        return any(rx.search(t) for _, t in self._texts)

    def _rel(self, p: Path) -> str:
        try:
            return str(p.relative_to(self.root))
        except ValueError:
            return str(p)

    def _score_touch(self) -> None:
        cap = 25
        min_t = PLATFORMS[self.platform]["min_touch"]
        unit = PLATFORMS[self.platform]["unit"]
        inter_rx = re.compile(PATTERNS[self.platform]["interactive"])
        size_rx = re.compile(PATTERNS[self.platform]["fixed_size"])
        sub_min = []
        for p, t in self._texts:
            lines = t.splitlines()
            for i, line in enumerate(lines):
                if not inter_rx.search(line):
                    continue
                # look at this line and the next 2 for an explicit small size
                window = "\n".join(lines[i:i + 3])
                for m in size_rx.finditer(window):
                    val = next((g for g in m.groups() if g), None)
                    if val and 0 < int(val) < min_t:
                        sub_min.append({"file": self._rel(p), "line": i + 1, "value": int(val)})
        if sub_min:
            self.dimension_scores["M1"] = 0
            self.blockers.append({
                "dimension": "M1",
                "message": f"{len(sub_min)} interactive element(s) below the {min_t}{unit} minimum touch target.",
                "fix": f"Give every tappable element a minimum {min_t}{unit} hit area.",
                "hits": sub_min[:5],
            })
            return
        if self._present("interactive"):
            self.dimension_scores["M1"] = cap
            self.findings.append({"dimension": "M1", "message": f"No sub-{min_t}{unit} touch targets detected."})
        else:
            self.dimension_scores["M1"] = 12  # no interactive elements found — neutral
            self.weaknesses.append({
                "dimension": "M1",
                "message": "No interactive elements detected to verify touch ergonomics.",
                "fix": f"Ensure tappable elements exist and meet the {min_t}{unit} minimum.",
            })

    def _score_safe_area(self) -> None:
        cap = 20
        if self._present("safe_area"):
            self.dimension_scores["M2"] = cap
            self.findings.append({"dimension": "M2", "message": "Safe-area / window insets handled."})
        else:
            self.dimension_scores["M2"] = 0
            self.blockers.append({
                "dimension": "M2",
                "message": "No safe-area handling — content will collide with the notch / home indicator / status bar.",
                "fix": {
                    "swiftui": "Use .safeAreaInset / respect the safe area; avoid blanket .ignoresSafeArea().",
                    "compose": "Apply systemBarsPadding() / WindowInsets to root scaffolds.",
                    "flutter": "Wrap screens in SafeArea (or use MediaQuery padding).",
                    "react-native": "Use SafeAreaView / useSafeAreaInsets from react-native-safe-area-context.",
                }[self.platform],
            })

    def _score_nav(self) -> None:
        cap = 15
        if self._present("nav"):
            self.dimension_scores["M3"] = cap
            self.findings.append({"dimension": "M3", "message": "Native navigation container present."})
        else:
            self.dimension_scores["M3"] = 0
            self.weaknesses.append({
                "dimension": "M3",
                "message": "No native navigation container detected — risk of a web-style menu shrunk onto mobile.",
                "fix": "Use the platform's native nav (TabView/NavigationStack, Scaffold/NavigationBar, BottomNavigationBar, or react-navigation).",
            })

    def _score_type_spacing(self) -> None:
        cap = 20
        pts = 0
        if self._present("type_good"):
            pts += 12
            self.findings.append({"dimension": "M4", "message": "Semantic / dynamic text styles used."})
        else:
            self.weaknesses.append({
                "dimension": "M4",
                "message": "No semantic text styles — likely hardcoded font sizes.",
                "fix": "Use the platform type scale (Dynamic Type, MaterialTheme.typography, TextTheme, or design tokens).",
            })
        if self._present("spacing"):
            pts += 8
        else:
            self.weaknesses.append({
                "dimension": "M4",
                "message": "No consistent spacing tokens detected.",
                "fix": "Use a spacing scale (8dp/pt grid) rather than ad-hoc values.",
            })
        self.dimension_scores["M4"] = min(pts, cap)

    def _score_motion(self) -> None:
        cap = 20
        pts = 0
        if self._present("anim"):
            pts += 12
            self.findings.append({"dimension": "M5", "message": "Native animation APIs used."})
        else:
            self.weaknesses.append({
                "dimension": "M5",
                "message": "No native motion — screens will feel static and web-like.",
                "fix": "Add native transitions (withAnimation, animate*AsState, AnimatedContainer, Reanimated).",
            })
        if self._present("tactile"):
            pts += 8
            self.findings.append({"dimension": "M5", "message": "Tactile feedback / ripple present."})
        else:
            self.weaknesses.append({
                "dimension": "M5",
                "message": "No tactile feedback (haptics / ripple).",
                "fix": "Add platform feedback on key actions (haptics on iOS, ripple/InkWell on Android).",
            })
        self.dimension_scores["M5"] = min(pts, cap)

    # ── reporting ────────────────────────────────────────────────────────────

    def _exit_code(self) -> int:
        if self.platform is None:
            return 0
        if self.blockers or self.score < self.floor:
            return 2
        if self.score < self.passing:
            return 1
        return 0

    def _label(self) -> tuple[str, str]:
        if self.blockers:
            return ("❌ BLOCKED (hard mobile failures)", RED)
        s = self.score
        if s >= 85:
            return ("✅ NATIVE-GRADE", GREEN)
        if s >= self.passing:
            return ("✅ SOLID", GREEN)
        if s >= self.floor:
            return ("⚠️  NEEDS POLISH", YELLOW)
        return ("❌ READS AS A SHRUNK WEBSITE", RED)

    def print_report(self) -> None:
        sep = "=" * 52
        print(f"\n{BOLD}{sep}{RESET}")
        print("  MOBILE / NATIVE AUDIT")
        print(f"{BOLD}{sep}{RESET}\n")
        if not self.platform:
            print(f"  {YELLOW}No native source detected (.swift/.kt/.dart/RN).{RESET}")
            print(f"  This auditor is for native apps; web targets use audit_beauty.py.\n")
            print(f"{BOLD}{sep}{RESET}\n")
            return
        label, colour = self._label()
        print(f"  Platform: {BOLD}{self.platform}{RESET}")
        print(f"  Mobile Score: {colour}{BOLD}{self.score}/100  {label}{RESET}\n")
        for did, name, cap in self.DIMENSIONS:
            got = self.dimension_scores.get(did, 0)
            mark = GREEN if got >= cap * 0.8 else (YELLOW if got >= cap * 0.4 else RED)
            print(f"    {BOLD}{did}{RESET} {name:<24} {mark}{got:>2}/{cap}{RESET}")
        print()
        if self.blockers:
            print(f"  {RED}Hard blockers (must fix):{RESET}")
            for b in self.blockers:
                print(f"  {BOLD}{RED}[{b['dimension']}]{RESET} {b['message']}")
                print(f"       {CYAN}Fix:{RESET} {b['fix']}\n")
        if self.weaknesses:
            print(f"  {YELLOW}Polish:{RESET}")
            for w in self.weaknesses:
                print(f"  {BOLD}{CYAN}[{w['dimension']}]{RESET} {w['message']}")
                print(f"       {YELLOW}Fix:{RESET} {w['fix']}\n")
        print(f"{BOLD}{sep}{RESET}")
        ec = self._exit_code()
        if ec == 2 and self.blockers:
            print(f"  {RED}{BOLD}❌ BLOCKED{RESET} — hard mobile failures. Fix the blockers above.")
        elif ec == 2:
            print(f"  {RED}{BOLD}❌ BLOCKED{RESET} — {self.score}/100 below floor {self.floor}. Reads as a shrunk website.")
        elif ec == 1:
            print(f"  {YELLOW}{BOLD}⚠️  NEEDS POLISH{RESET} — {self.score}/100 below pass {self.passing}.")
        else:
            print(f"  {GREEN}{BOLD}✅ PASSED{RESET} — {self.score}/100. Reads as a real native app.")
        print(f"{BOLD}{sep}{RESET}\n")

    def to_dict(self) -> dict[str, Any]:
        label, _ = self._label()
        return {
            "platform": self.platform,
            "mobile_score": self.score,
            "label": label,
            "floor": self.floor,
            "pass": self.passing,
            "exit_code": self._exit_code(),
            "dimensions": {d: {"name": n, "score": self.dimension_scores.get(d, 0), "max": c}
                           for d, n, c in self.DIMENSIONS},
            "blockers": self.blockers,
            "weaknesses": self.weaknesses,
            "findings": self.findings,
        }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="audit_mobile",
        description="Native craft + mobile gates for SwiftUI / Compose / Flutter / React Native.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--path", type=Path, default=Path("."))
    p.add_argument("--json", action="store_true", dest="json_output")
    p.add_argument("--threshold", nargs=2, type=int, metavar=("FLOOR", "PASS"), default=[50, 70])
    return p


def main() -> int:
    args = build_parser().parse_args()
    root = args.path.resolve()
    if not root.is_dir():
        print(f"Error: path '{root}' is not a directory.", file=sys.stderr)
        return 2
    floor, passing = args.threshold
    if not (0 <= floor < passing <= 100):
        print("Error: thresholds must satisfy 0 ≤ FLOOR < PASS ≤ 100.", file=sys.stderr)
        return 2
    a = MobileAuditor(root, floor, passing)
    try:
        a.scan()
    except Exception as exc:  # noqa: BLE001
        print(f"Error during scan: {exc}", file=sys.stderr)
        return 2
    if args.json_output:
        print(json.dumps(a.to_dict(), indent=2, ensure_ascii=False))
    else:
        a.print_report()
    # No native source → nothing to block on; treat as pass-through (0).
    if a.platform is None:
        return 0
    return a._exit_code()


if __name__ == "__main__":
    sys.exit(main())
