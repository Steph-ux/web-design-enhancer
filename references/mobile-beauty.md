# Mobile Beauty — native craft per platform

> Companion to `audit_mobile.py` and `mobile-references.md`.
> Version 1.0

## Why this document exists

The web archetypes and the Beauty Score judge HTML/CSS. A native screen has a
different bar: it must respect platform ergonomics and feel like it belongs on
the device, not like a website shrunk into a phone. The single biggest tell of
AI-generated mobile work is exactly that, a responsive web layout wearing a
native costume.

`audit_mobile.py` scores five mobile dimensions and hard-blocks accessibility
failures. This file is the positive recipe it leans on: the non-negotiable rules
and the signature gestures that make each platform read as the real thing.

| Dim | What it checks | Hard or soft |
|-----|----------------|--------------|
| **M1** | Touch ergonomics — minimum hit area | **Hard blocker** if sub-min |
| **M2** | Safe-area handling — notch / home indicator | **Hard blocker** if absent |
| **M3** | Native navigation container | Soft (polish) |
| **M4** | Semantic type scale + spacing grid | Soft (polish) |
| **M5** | Native motion + tactile feedback | Soft (polish) |

---

## Non-negotiables (every platform)

1. **Minimum touch target (M1).** iOS: **44×44 pt**. Android: **48×48 dp**. Never
   ship an interactive element with an explicit size below this. A 30pt icon
   button is an accessibility failure, not a style choice — `audit_mobile.py`
   blocks it.
2. **Safe areas (M2).** Respect the notch, status bar, and home indicator. Never
   blanket-ignore the safe area to get edge-to-edge; inset content deliberately.
3. **Native navigation (M3).** Use the platform's own nav (tab bar, navigation
   stack, bottom nav) — not a hamburger menu or a web-style top nav transplanted
   onto mobile.
4. **The device type scale (M4).** Use Dynamic Type / Material type roles / the
   framework's text theme so text respects the user's accessibility settings.
   Hardcoded `fontSize: 14` everywhere is the web-shrink tell.
5. **Motion + feedback (M5).** Native transitions and tactile feedback (haptics on
   iOS, ripple on Android) are what make a tap feel real.

---

## SwiftUI (iOS) — min touch 44pt

**Type:** `.font(.largeTitle / .title / .headline / .body / .caption)` + `.dynamicTypeSize`. Never hardcode point sizes.
- **G1 (M1/M5)** Tappable rows get `.frame(minHeight: 44)` and `.contentShape(Rectangle())`; fire `UIImpactFeedbackGenerator` (or `.sensoryFeedback`) on primary actions.
- **G2 (M2)** Edge-to-edge done right: `.safeAreaInset(edge:)` for bars, never a blanket `.ignoresSafeArea()` over content.
- **G3 (M3/M5)** `NavigationStack` + native `.navigationTransition`; `TabView` with SF Symbols for the root. Use `.matchedGeometryEffect` for hero transitions.

## Jetpack Compose (Android) — min touch 48dp

**Type:** `MaterialTheme.typography.titleLarge / bodyMedium…`. Never raw `sp` literals scattered in code.
- **G1 (M1/M5)** Clickables sized `Modifier.sizeIn(minWidth = 48.dp, minHeight = 48.dp)` with `indication = ripple()`; `LocalHapticFeedback` on long-press.
- **G2 (M2)** `Modifier.systemBarsPadding()` / `WindowInsets` on scaffolds; go edge-to-edge with `enableEdgeToEdge()` and inset deliberately.
- **G3 (M3/M5)** `Scaffold` + `NavigationBar` (M3) or `NavigationRail` on tablets; `AnimatedContent` / `animate*AsState` for state changes.

## Flutter — min touch 48dp

**Type:** `Theme.of(context).textTheme.titleLarge / bodyMedium…`. Never hardcode `TextStyle(fontSize: 14)` repeatedly.
- **G1 (M1/M5)** Wrap taps in `InkWell` (ripple) inside a `Material`; enforce `MaterialTapTargetSize.padded`; `HapticFeedback.lightImpact()` on key actions.
- **G2 (M2)** Wrap screens in `SafeArea`; use `MediaQuery.viewPadding` for custom insets.
- **G3 (M3/M5)** `Scaffold` + `NavigationBar` / `BottomNavigationBar`; `Hero` + `AnimatedContainer` for transitions; respect Material motion durations.

## React Native — min touch 44pt

**Type:** font sizes from a token/theme object or a `variant` prop, not inline magic numbers per component.
- **G1 (M1/M5)** `Pressable` with `hitSlop` and a `style` min height of 44; `expo-haptics` `impactAsync` on primary actions; never rely on hover.
- **G2 (M2)** `SafeAreaView` / `useSafeAreaInsets` from `react-native-safe-area-context` — never hardcode a `paddingTop: 44` for the notch.
- **G3 (M3/M5)** `@react-navigation` native stack + bottom tabs (native feel, not a JS router faking it); `react-native-reanimated` for 60fps transitions, `LayoutAnimation` for list changes.

---

## The web-shrink tells (instant AI-mobile signals)

- `hover` states as the primary affordance (no hover on touch).
- `px`/`rem` units or CSS media queries in a native file.
- A hamburger menu instead of a tab bar.
- One hardcoded font size everywhere; no Dynamic Type / text theme.
- Content jammed against the top edge (no safe-area inset).
- Zero motion — screens snap between states with no transition.
- Buttons smaller than the platform minimum to "fit more in".

> After building, run `python3 scripts/audit_mobile.py --path ./<app-src>`.
> Any hard blocker (M1/M2) must be cleared. Aim for ≥70/100 overall so the
> screen reads as a real native app, not a website in a phone frame.
