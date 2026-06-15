"""
tests/test_audit_mobile.py
Tests for the native craft + mobile gates auditor (audit_mobile.py):
platform detection, hard blockers (touch targets, safe area), and the
five-dimension mobile score across SwiftUI / Compose / Flutter / React Native.
"""
import tempfile
import textwrap
from pathlib import Path

import pytest
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from audit_mobile import MobileAuditor, detect_platform


def _project(files: dict[str, str]) -> Path:
    tmp = Path(tempfile.mkdtemp())
    for fn, content in files.items():
        fp = tmp / fn
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(textwrap.dedent(content), encoding="utf-8")
    return tmp


def _audit(files: dict[str, str], floor=50, passing=70) -> MobileAuditor:
    a = MobileAuditor(_project(files), floor, passing)
    a.scan()
    return a


def _blocker_dims(a) -> set[str]:
    return {b["dimension"] for b in a.blockers}


# A well-built SwiftUI screen.
GOOD_SWIFT = """
    import SwiftUI
    struct HomeView: View {
        var body: some View {
            NavigationStack {
                VStack(spacing: 16) {
                    Text("Title").font(.largeTitle)
                    Button("Go") { withAnimation { tap() } }
                        .frame(height: 48)
                        .padding(16)
                }
                .safeAreaInset(edge: .bottom) { Spacer() }
            }
        }
        func tap() { let g = UIImpactFeedbackGenerator(style: .medium); g.impactOccurred() }
    }
"""


# ─── Platform detection ──────────────────────────────────────────────────────

class TestDetection:
    def test_swiftui(self):
        a = _audit({"V.swift": GOOD_SWIFT})
        assert a.platform == "swiftui"

    def test_flutter(self):
        a = _audit({"main.dart": "import 'package:flutter/material.dart'; class X extends StatelessWidget {}"})
        assert a.platform == "flutter"

    def test_compose(self):
        a = _audit({"Main.kt": "@Composable fun Screen() { Scaffold {} }"})
        assert a.platform == "compose"

    def test_react_native_needs_import(self):
        a = _audit({"App.tsx": "import { View } from 'react-native';\nexport const A = () => <View/>;"})
        assert a.platform == "react-native"

    def test_plain_web_tsx_not_mobile(self):
        a = _audit({"page.tsx": "export default function P(){ return <div>hi</div> }"})
        assert a.platform is None

    def test_native_beats_rn_when_both(self):
        files = {"V.swift": GOOD_SWIFT, "App.tsx": "import {View} from 'react-native'"}
        assert detect_platform([Path(p) for p in files]) in ("swiftui",)  # path-only; see scan test below


# ─── End-to-end ──────────────────────────────────────────────────────────────

class TestEndToEnd:
    def test_good_swiftui_passes(self):
        a = _audit({"V.swift": GOOD_SWIFT})
        assert not a.blockers
        assert a.score >= a.passing
        assert a._exit_code() == 0

    def test_no_native_source_is_passthrough(self):
        a = _audit({"styles.css": "body{color:#111}"})
        assert a.platform is None
        assert a._exit_code() == 0


# ─── M1: touch targets (hard blocker) ────────────────────────────────────────

class TestTouchTargets:
    def test_sub_min_swiftui_blocks(self):
        src = """
            import SwiftUI
            struct V: View { var body: some View {
                Button("x") {}.frame(height: 30)
            } }
        """
        a = _audit({"V.swift": src})
        assert "M1" in _blocker_dims(a)
        assert a._exit_code() == 2

    def test_sub_min_compose_blocks(self):
        src = "@Composable fun S(){ Button(onClick={}){}.size(36.dp) }\nScaffold{}"
        a = _audit({"S.kt": src})
        assert "M1" in _blocker_dims(a)

    def test_adequate_target_no_block(self):
        src = """
            import SwiftUI
            struct V: View { var body: some View {
                Button("x") {}.frame(height: 48)
            } }
        """
        a = _audit({"V.swift": src})
        assert "M1" not in _blocker_dims(a)


# ─── M2: safe area (hard blocker) ────────────────────────────────────────────

class TestSafeArea:
    def test_missing_safe_area_blocks_flutter(self):
        src = "import 'package:flutter/material.dart'; Widget b()=> Scaffold(body: Text('x'));"
        a = _audit({"main.dart": src})
        assert "M2" in _blocker_dims(a)

    def test_present_safe_area_ok(self):
        src = "import 'package:flutter/material.dart'; Widget b()=> SafeArea(child: Scaffold(body: Text('x')));"
        a = _audit({"main.dart": src})
        assert "M2" not in _blocker_dims(a)


# ─── M3 / M4 / M5 scoring ────────────────────────────────────────────────────

class TestCraftDimensions:
    def test_nav_detected(self):
        a = _audit({"V.swift": GOOD_SWIFT})
        assert a.dimension_scores["M3"] == 15

    def test_type_and_spacing(self):
        a = _audit({"V.swift": GOOD_SWIFT})
        assert a.dimension_scores["M4"] == 20

    def test_motion_and_haptics(self):
        a = _audit({"V.swift": GOOD_SWIFT})
        assert a.dimension_scores["M5"] == 20

    def test_static_screen_low_motion(self):
        src = """
            import SwiftUI
            struct V: View { var body: some View {
                NavigationStack { Text("x").font(.body).padding(16)
                  .safeAreaInset(edge:.top){Spacer()} }
            } }
        """
        a = _audit({"V.swift": src})
        assert a.dimension_scores["M5"] == 0


# ─── JSON contract ───────────────────────────────────────────────────────────

class TestJson:
    def test_to_dict_shape(self):
        d = _audit({"V.swift": GOOD_SWIFT}).to_dict()
        assert set(d) >= {"platform", "mobile_score", "exit_code", "dimensions", "blockers", "weaknesses"}
        assert set(d["dimensions"]) == {"M1", "M2", "M3", "M4", "M5"}


class TestSafeAreaFalsePositive:
    def test_ignores_safe_area_does_not_count(self):
        # .ignoresSafeArea() is the OPPOSITE of handling the safe area
        src = """
            import SwiftUI
            struct V: View { var body: some View {
                VStack { Text("x").font(.body) }.ignoresSafeArea()
            } }
        """
        a = _audit({"V.swift": src})
        assert a.dimension_scores["M2"] == 0
        assert "M2" in {b["dimension"] for b in a.blockers}

    def test_safe_area_inset_counts(self):
        src = """
            import SwiftUI
            struct V: View { var body: some View {
                VStack { Text("x").font(.body) }.safeAreaInset(edge:.top){ Spacer() }
            } }
        """
        a = _audit({"V.swift": src})
        assert a.dimension_scores["M2"] == 20
