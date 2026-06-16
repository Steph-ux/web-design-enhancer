# DESIGN.md — Project Design Contract

This document defines the strict design rules for the project. Every implementation must respect these specifications to avoid "AI slop" and guarantee professional quality.

---

## 0. Sources Phase 0

> **Mandatory block — proof that Phase 0 was executed.** `scripts/check.py --gate 0` reads this section and blocks until it is filled.
> All placeholders `[Ex: ...]`, `<brand>`, `<description>`, `<Project>` must be replaced with real values before moving to Phase 1.

### 0a. Visual reference — getdesign.md
- **Brand used**: [Ex: stripe]
- **Command executed**: `npx getdesign@latest add <brand>`
- **Tokens extracted from the reference DESIGN.md**: [Ex: gray palette + accent #635BFF, radius 8px, soft shadows]

### 0b. Design intelligence — UI/UX Pro Max
- **Product description**: [Ex: "fintech analytics dashboard"]
- **Query executed**: `python3 scripts/search.py "<description>" --design-system -p "<Project>"`
- **Style chosen**: [Ex: Clean Tech]
- **Recommended page pattern**: [Ex: split-pane dashboard, left sidebar, dense header]
- **Sector antipatterns to avoid**: [Ex: decorative glassmorphism, neon glow]

### 0c. Rationale
- **Rationale for the chosen theme**: [Ex: Stripe palette + Clean Tech density for demanding B2B SaaS]

---

## 1. Theme & Visual Concept
*Describe the visual mood in technical terms (e.g. "Soft neumorphism", "Brutalist minimalism", "High-fidelity dark mode"). Avoid buzzwords like "modern" or "premium". Reference UI/UX Pro Max styles for inspiration.*

- **Concept**: [Ex: High-Precision Tech Minimalism, Industrial Aesthetic]
- **Keywords**: [Ex: Geometric, Contrasted, Functional, Brutalist, Clean]
- **UI/UX Pro Max inspiration**: [Ex: "Neo-Brutalism", "Clean Tech", "Glassmorphism" style]

## 2. Color Palette
*Use semantic roles. Maximum 8 main colors. Reference UI/UX Pro Max color palettes or `getdesign.md` examples for proven combinations.*

| Role | Hex | Usage |
| :--- | :--- | :--- |
| Primary | # | [Ex: Action buttons, key elements] |
| Secondary | # | [Ex: Secondary elements, accents] |
| Background | # | [Ex: Main background] |
| Text | # | [Ex: Main text] |
| Accent | # | [Ex: Interactive elements, highlights] |
| Success | # | [Ex: Success messages] |
| Warning | # | [Ex: Alerts, warnings] |
| Danger | # | [Ex: Destructive actions] |

## 3. Typography
*Maximum 2 fonts (one for display/titles, one for body text). Reference UI/UX Pro Max font pairs or `getdesign.md` examples.*

- **Display (Titles)**: [Font name] (Source: Google Fonts, Adobe Fonts, etc.)
- **Body (Body text)**: [Font name] (Source: Google Fonts, Adobe Fonts, etc.)
- **Monospace (Code/Data)**: [Font name] (Optional, if needed)

## 4. Typography Hierarchy
*All sizes must follow a harmonic scale. Define size, weight and line-height for each level. Auto-validated ranges: H1 28–80px, H2 22–60px, H3 18–36px, P 13–18px, Small 11–14px.*

- **H1**: [Size] / [Weight] / [Line-height]
- **H2**: [Size] / [Weight] / [Line-height]
- **H3**: [Size] / [Weight] / [Line-height]
- **P (Paragraph)**: [Size] / [Weight] / [Line-height]
- **Small (Secondary text)**: [Size] / [Weight] / [Line-height]

## 5. Spacing & Grid
*Base: 8px. All multiples allowed (8, 16, 24, 32, 48, 64, etc.). Reference `getdesign.md` spacing systems.*

- **Grid base**: 8px
- **Gutter (columns)**: [Ex: 24px, 32px]
- **Section vertical padding**: [Ex: 64px, 96px]
- **Section horizontal padding**: [Ex: 32px, 48px]
- **Radius**: [Ex: 0px, 4px, 8px, 12px] (multiples of 4px accepted)

## 6. Components & States
*Define interactions and variants for key components. Use `shadcn/ui` as a base and customize per these specs. Reference UI/UX Pro Max UX guidelines.*

### Buttons
- **Primary (Normal)**: [Visual description: background color, text, border]
- **Primary (Hover)**: [Visual description: color change, shadow]
- **Secondary (Normal)**: [Visual description]
- **Secondary (Hover)**: [Visual description]
- **Ghost/Link (Normal)**: [Visual description]

### Cards
- **Structure**: [Ex: `surface-card` background, `hairline` border]
- **Inner padding**: [Ex: 24px]
- **Shadow**: [Ex: `0px 4px 12px rgba(0,0,0,0.1)`]

## 7. Motion & Animations
*Strict timings (≤ 400ms). Reference GSAP best practices and UI/UX Pro Max guidelines for smooth, intentional animations.*

- **General transitions**: [Ex: 200ms ease-out]
- **Element entries (Stagger)**: [Ex: Stagger 50ms, Duration 300ms]
- **Interactions (Hover/Click)**: [Ex: 150ms ease-in-out]
- **Accessibility**: `prefers-reduced-motion` mandatory.

---

## 8. Dark Mode

> **Mandatory.** Without an explicit dark mode contract, the implementation will be improvised.
> `validate_design.py` blocks if this section is absent or insufficient (< 3 colors). Unfilled brackets (`[Ex: ...]`) block too — replace examples with real hex values.

| Role | Hex | Light equivalent |
| :--- | :--- | :--- |
| Background | [Ex: #0F1117] | [Ex: #FFFFFF] |
| Surface | [Ex: #1C1E26] | [Ex: #F8FAFC] |
| Text | [Ex: #E8EAF0] | [Ex: #1E3A8A] |
| Secondary text | [Ex: #94A3B8] | [Ex: #64748B] |
| Border | [Ex: #2D3142] | [Ex: #E2E8F0] |
| Primary (unchanged) | [Ex: #533afd] | [Ex: #533afd] |
| Dark accent | [Ex: #7C6FFF] | [Ex: #D97706] |

**Dark mode rules:**
- Background must be < `#333` (relative luminance < 9%)
- Text on dark background must pass WCAG AA (≥ 4.5:1)
- Semantic colors (Success, Danger, Warning) remain readable on dark
- Use `prefers-color-scheme: dark` in CSS — no unsolicited JS toggle

---

## 9. Mobile

> **Optional for web-only projects. Mandatory as soon as a native or hybrid app is in scope.**
> `validate_design.py` validates this section if present — touch targets, safe areas, native units, **component anatomy**, accessibility. Unfilled brackets (`[A | B | C]`, `[Ex: ...]`) block validation: narrow each choice to one committed value.

### Target platform(s)

- **Stack:** [SwiftUI | Flutter | React Native | Jetpack Compose | Expo]
- **Platforms:** [iOS | Android | Both]
- **Minimum version:** [Ex: iOS 16+, Android 8+ (API 26)]

### Mobile units & grid

> Never use hard-coded `px` in native code — use the platform's units.

| Platform | Unit | Base grid | Example |
| :--- | :--- | :--- | :--- |
| iOS / SwiftUI | pt (points) | 4pt | `padding(16)` = 16pt |
| Android / Compose | dp | 4dp | `Modifier.padding(16.dp)` |
| Flutter | logical pixels | 4 | `SizedBox(height: 16)` |
| React Native | dp (auto) | 4 | `padding: 16` |

- **Base grid:** [4pt / 4dp — multiples of 4 only on mobile]
- **Horizontal padding:** [Ex: 16pt / 16dp]
- **Section vertical padding:** [Ex: 24pt / 24dp]
- **Element spacing:** [Ex: 8pt, 12pt, 16pt, 24pt]

### Touch targets

> iOS HIG minimum: **44×44pt**. Material Design minimum: **48×48dp**.

- **Primary buttons:** [Ex: 44pt min height, full-width or ≥ 120pt wide]
- **Interactive icons:** [Ex: 44×44pt tap area even if the icon is smaller]
- **List rows:** [Ex: row height ≥ 44pt]
- **Form fields:** [Ex: 44pt min height]

```swift
// SwiftUI — explicit tap area
Button(action: {}) {
    Image(systemName: "heart")
        .frame(width: 44, height: 44) // iOS HIG touch target
}
```

```kotlin
// Compose — Material touch area
IconButton(
    modifier = Modifier.size(48.dp), // Material touch target
    onClick = {}
) { Icon(Icons.Default.Favorite, contentDescription = "Favorites") }
```

### Safe areas

> Never hard-code status bar, notch, or home-indicator heights.

- **iOS strategy:** `.safeAreaInset()` or `.ignoresSafeArea()` only for backgrounds
- **Android strategy:** `WindowInsets` via `Modifier.windowInsetsPadding()`
- **RN strategy:** `useSafeAreaInsets()` from `react-native-safe-area-context`
- **Flutter strategy:** `MediaQuery.of(context).padding` or `SafeArea` widget

### Mobile component anatomy

> These sections override §6 when the target is mobile native.
> Web-only projects use §6 instead. Fill every bracket — placeholders block `validate_design.py`.

#### Screen patterns
- **Screen types in scope:** [List | Detail | Form | Onboarding | Empty full-screen | Settings]
- **Primary screen pattern:** [Ex: List → Detail with bottom tab bar]

#### Navigation pattern
- **Type:** [Tab Bar 5 items | Bottom Sheet | Drawer | Pure Stack]
- **Position:** [Bottom (iOS) | Bottom (Android) | Top (web-first PWA)]
- **Active state:** [color + filled icon + visible label | color only | icon swap only]
- **Transitions:** [Ex: native push/pop, modal sheet, fullscreen cover]

#### Card anatomy
- **Structure:** [Image top | Left thumbnail | No image]
- **Inner padding:** [16pt / 16dp]
- **Content:** [Title + Subtitle + Action | Title + Meta + Badge]
- **Interaction:** [Tap → detail | Swipe → actions | Long-press → menu]

#### List item
- **Leading:** [Avatar 40pt | Icon 24pt | None]
- **Content:** [Title + subtitle | Title only | Title + right-detail]
- **Trailing:** [Chevron | Toggle | Action icon | None]
- **Separator:** [Full-bleed | inset-leading | None]

#### Primary CTA
- **Position:** [Fixed bottom, margin 16pt | In scroll flow | Sticky header]
- **Height:** [52pt minimum]
- **Scroll behavior:** [Hides on scroll-down | Stays fixed | Shrinks]

#### States
- **Empty state:** [Illustration + title + CTA | Icon + title + CTA | Text only]
- **Loading:** [Skeleton screen | Centered spinner | Card shimmer]
- **Error:** [Inline under field | Bottom toast | Full-screen]

### Mobile animations

> On mobile, system animations (spring) are preferred over fixed durations.

- **Navigation transitions:** native system animation (no custom duration)
- **Micro-interactions:** [Ex: spring() for bounces, 200ms for fades]
- **Haptic feedback:** [Ex: UIImpactFeedbackGenerator / HapticFeedback.lightImpact()]
- **prefers-reduced-motion:** iOS `isReduceMotionEnabled`, Android `isReducedMotionEnabled`

### Mobile dark mode

> Native dark mode is automatic on iOS/Android when semantic colors are used.

- **iOS:** Use `Color(.systemBackground)`, `Color(.label)`, `Color(.secondaryLabel)`
- **Android:** Use `MaterialTheme.colorScheme.background`, `.onBackground`, `.surface`
- **Flutter:** `Theme.of(context).colorScheme` with `ThemeData.dark()`
- **React Native:** `useColorScheme()` + `StyleSheet.create` with conditional variables

### Mobile accessibility

- **VoiceOver (iOS):** `.accessibilityLabel()` on every `Image` and interactive element
- **TalkBack (Android):** `contentDescription` on every `Image` (null if decorative)
- **Focus order:** `.accessibilitySortPriority()` (iOS) / `Modifier.semantics` (Compose)
- **Dynamic text size:** Support Dynamic Type (iOS) / Text Scaling (Android)

---

## 10. Three.js

> **Optional. Mandatory as soon as a WebGL/Three.js scene is in scope.**
> `validate_design.py` validates this section if present. `detect_ai_slop.py` scans `.js`/`.ts`/`.jsx`/`.tsx` code for critical Three.js antipatterns.

### Scene type

- **Type:** [Hero background | Interactive viewer | Scroll-driven storytelling | Particle system | Product showcase]
- **Visual role:** [Ex: static animated background, interactive 3D model, scroll-driven camera]
- **Stack:** Three.js r128 via pinned CDN (never `@latest`)

### Renderer

- **Instance:** A single `WebGLRenderer` per page — lifetime = entire page
- **Pixel ratio:** `renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))` — cap mandatory
- **Alpha:** `alpha: true` on the renderer + background via CSS (not `setClearColor`)
- **Antialias:** `antialias: true` on desktop, `false` on mobile if perf is insufficient

### Geometry budget

| Role | Recommended segments |
| :--- | :--- |
| Hero mesh (foreground) | 32–64 |
| Background meshes | 8–16 |
| Particles stand-in | 6–8 |
| Ground plane | 1 (PlaneGeometry) |

**Absolute rule:** Never `new THREE.XxxGeometry()` inside `animate()` — build before the loop.

### Lighting

- **Minimum:** `AmbientLight` (fill, intensity 0.4) + `DirectionalLight` (key, intensity 1.0)
- **Shadows:** Enabled only on the primary `DirectionalLight` and the hero mesh
- **`MeshBasicMaterial`:** No lights needed — use for flat decorative elements

### Dispose strategy

Always call before `scene.remove()`:
```js
mesh.geometry.dispose()
mesh.material.dispose()
mesh.material.map?.dispose()       // textures
mesh.material.normalMap?.dispose() // normal maps
```

### WebGL fallback

- **Detection:** `WebGL2RenderingContext` or `WebGLRenderingContext` in `window`
- **Fallback:** [Static PNG image | Simplified 2D canvas | Discreet message]

### Three.js animations

> Note: the ≤ 400ms rule from §7 applies to UI transitions, **not** Three.js animations.
> 60fps loops, scroll scrub, and continuous rotations are exempt.

- **UI transitions** (fade, reveal): ≤ 400ms via GSAP
- **Three.js loops:** clock.getDelta(), requestAnimationFrame — no fixed duration
- **Scroll scrub:** GSAP ScrollTrigger + `scrub: 1` — scroll-relative, not ms
- **prefers-reduced-motion:** Freeze the scene (`renderer` still active but `delta = 0`) or slow rotation (max 0.001 rad/frame)

### WebGL accessibility

- **`<canvas>`:** Descriptive `aria-label` attribute + `role="img"`
- **3D interactivity:** `pointer` cursor on hover (raycasting), haptic feedback on mobile
- **Screen readers:** Alternative content visible in `<noscript>` or `aria-describedby`

---

## 11. Signature Gesture

> **One thing. Extremely specific. An implementation, not a category.** The creative budget must concentrate in a single owned move, not diffuse across 50 forgettable micro-details. Concentrate, don't spread.

- **Description**: [Ex: project cards get a 2px vertical accent line on the left edge that grows from 0 to 100% height in 200ms on hover. Nowhere else. No gradient, no shadow — just this.]
- **DESIGN.md token**: [Ex: §2 accent #E84C3D]
- **Implementation**: [Ex: `border-left` + CSS transition — not GSAP]
- **Grep signature**: [Ex: `border-left.*transition`]
  *(A short regex `check.py --final` can grep for in the code. If you provide it and a code path, the gate verifies the gesture is actually implemented — a declared-but-absent signature is flagged.)*

---

## 12. Intentional Tensions

> **"Waouh" comes from deliberate contrast, not harmony.** Name at least **2** tension pairs. If every tension is "moderate", there is no tension — that is the warning. A design where everything is balanced is a design nobody remembers.

(minimum 2 pairs — format: `T<n> <axis>: <pole A> / <pole B> — <ratio or note>`)

- **T1 Typography**: [Ex: H1 80px / Body 15px — ratio 5.3:1 (not a clean 2:1)]
- **T2 Density**: [Ex: hero 160px padding / feature section 24px padding]
- **T3 Colour**: [Ex: 97% monochrome / 3% accent — one single splash of colour in the whole page]

---

## Anti-Slop Validation Checklist

Before delivery, verify:

- [ ] **DESIGN.md**: Complete and respects every defined section.
- [ ] **Fonts**: Maximum 2 main fonts, from intentional pairings.
- [ ] **Spacing**: Every padding/margin/gap is a multiple of 8px.
- [ ] **Radii**: Every border-radius is a multiple of 4px.
- [ ] **Icons**: Custom SVG or a consistent pack (no generic, unjustified Lucide icons).
- [ ] **Gradients**: Justified by a clear semantic role, max 2–3 distinct gradients.
- [ ] **Visual artifacts**: No emojis, stickers, or unsolicited decorative elements.
- [ ] **Logos/Names**: No generic placeholders ("your-logo", "brandname"). Use styled text if no logo is provided.
- [ ] **Structure**: Unique, intentional layout — not a generic template (Hero, Features, Testimonials, CTA, Pricing, FAQ, Footer).
- [ ] **Copy**: Precise descriptions, no vague buzzwords ("premium", "modern", "amazing").
- [ ] **Buttons**: Clear hierarchy (Primary, Secondary, Ghost, Destructive) with distinct styles.
- [ ] **Colors**: 4–8 colors with clear semantic roles, defined in DESIGN.md.
- [ ] **Animations**: Every animation ≤ 400ms and respects `prefers-reduced-motion`.
- [ ] **shadcn/ui**: Components customized, not left at default.
- [ ] **Dark mode**: §8 Dark Mode present, ≥ 3 colors, background < #333, WCAG AA validated.
- [ ] **Mobile** (if applicable): §9 Mobile present, touch targets ≥ 44pt/48dp, safe areas documented, native units (no px).

**Run the automated audit:**
```bash
python3 scripts/detect_ai_slop.py --design DESIGN.md --code ./client/src
python3 scripts/visual_audit.py --url http://localhost:3000 --output ./audit-results
```

Expected quality score ≥ 80/100 for delivery.
