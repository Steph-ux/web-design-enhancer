#!/usr/bin/env python3
"""
AI Slop Detector - Detects common antipatterns of AI-generated design

Detects:
- Generic icons (Lucide, FontAwesome)
- Cliche gradients
- Template sections (Hero, Features, CTA)
- Vague buzzwords
- Generic fonts
- Unjustified colors
- Inconsistent spacings
- AI status badges in HTML/CSS/JSX/TSX (SYS_ACTIVE, pulse-dot, etc.)

Usage:
    python3 detect_ai_slop.py --design DESIGN.md --code ./client/src
    python3 detect_ai_slop.py --design DESIGN.md --code .   # also scans .html/.css
"""

import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple
from collections import Counter


class AISloPDetector:
    """AI slop antipattern detector"""

    # Generic icons and "AI smell" artifacts - web and mobile
    GENERIC_ICONS = {
        # Web (Lucide / FontAwesome)
        "sparkles", "zap", "cog", "network", "arrow", "check", "star",
        "heart", "user", "settings", "menu", "search", "bell", "mail",
        "download", "upload", "trash", "edit", "copy", "share", "link",
        "eye", "lock", "unlock", "calendar", "clock", "map", "phone",
        "play", "pause", "volume", "wifi", "battery", "sun", "moon",
        "magic", "stars", "bot", "robot", "ai", "brain",
        # Mobile - generic SF Symbols (iOS)
        "person.fill", "house.fill", "gear", "bell.fill", "magnifyingglass",
        "ellipsis", "xmark", "chevron.right", "arrow.right", "plus.circle",
        # Mobile - generic Material Icons (Android)
        "Icons.Default.Home", "Icons.Default.Person", "Icons.Default.Settings",
        "Icons.Default.Notifications", "Icons.Default.Search", "Icons.Default.Menu",
        "Icons.Default.Add", "Icons.Default.Close", "Icons.Default.ArrowBack",
        # Mobile - generic Expo Icons (React Native)
        "Ionicons.home", "Ionicons.person", "Ionicons.settings",
        "MaterialIcons.home", "MaterialIcons.person",
    }

    # Mobile-specific antipatterns
    MOBILE_SLOP_PATTERNS = [
        (r"width\s*[:=]\s*(?:375|390|393|414|375\.0|390\.0)",
         "Hardcoded iPhone screen width - use .frame(maxWidth: .infinity) or LayoutBuilder"),
        (r"width\s*[:=]\s*(?:360|393|412|411)",
         "Hardcoded Android screen width - use responsive layout"),
        (r"\.frame\s*\(.*?(?:width|height)\s*:\s*([1-3]\d)",
         "Touch target probably too small (< 40pt) - iOS HIG minimum is 44pt"),
        (r"(?:padding|margin).*?(?:top)\s*:\s*(?:44|20|47)",
         "Hardcoded status bar height - use SafeAreaInsets or useSafeAreaInsets()"),
        (r"Color\(red:\s*\d+,\s*green:\s*\d+",
         "Hardcoded SwiftUI RGB color - prefer Color(.systemBackground) or semantic colors"),
        (r"backgroundColor\s*=\s*UIColor\.white",
         "Fixed white backgroundColor - use .systemBackground for automatic dark mode"),
    ]

    # Patterns to detect invented logos or graphic placeholders
    LOGO_PLACEHOLDERS = [
        (r"logo-placeholder", "Generic logo placeholder"),
        (r"your-logo", "Default logo text"),
        (r"brandname", "Generic brand name"),
        (r"company-name", "Generic company name"),
    ]

    # Patterns to detect default shadcn/ui usage (no customization)
    SHADCN_DEFAULT_PATTERNS = [
        (r"<Button\s*[^>]*?variant=\"default\"", "shadcn/ui Button with default variant"),
        (r"<Input(?!\s[^>]*className)[^>]*/?>", "shadcn/ui Input without customization className"),
    ]

    # -----------------------------------------------------------------------
    # AI STATUS BADGES — JSX/TSX patterns
    # -----------------------------------------------------------------------
    STATUS_BADGE_PATTERNS = [
        (r"[●•◉]\s*[A-ZÀ-ÖØ-Þ][A-ZÀ-ÖØ-Þ\s]{4,}",
         "Colored dot + uppercase status text"),
        (r"\b(?:PREMIUM\s+QUALITY|ULTRA\s+FAST|HIGH\s+PERFORMANCE|LIVE\s+NOW|TOP\s+RATED|ATMOSPHÈRE\s+\w+)\b",
         "AI status phrase (never a legitimate data label)"),
        (r"w-2\s+h-2\s+rounded-full\s+bg-(?:green|emerald|lime|teal)-\d{3}",
         "Decorative green dot Tailwind (AI status indicator)"),
        (r"animate-pulse[^\"]*rounded-full|rounded-full[^\"]*animate-pulse",
         "Animated (pulse) decorative dot - frequent AI signal"),
        (r">[\s]*[A-Z][A-Z_]{3,}\s*:\s*[A-Z][A-Z_]+[\s]*<",
         "Invented system status badge e.g. '<span>SYNC_NODE: STABLE</span>' - never real data"),
        (r"\b(?:sync_node|sys_info|sys_status|sync_status)\b",
         "Generic system status indicator - strong AI signal"),
        (r"text-transform\s*:\s*uppercase[^}]{0,200}(?:button|\.btn|\.cta|nav-link|menu-item)",
         "text-transform: uppercase on button/CTA - AI slop pattern"),
        (r"(?:className|class)\s*=\s*\"[^\"]*\b(?:uppercase|tracking-widest)\b[^\"]*\b(?:btn|button|cta|nav-link)\b",
         "Uppercase class on button/CTA - ALL CAPS on CTAs = frequent AI pattern"),
        (r"<(?:Star|StarIcon|StarFilled)\s*/>",
         "JSX star icon with no functional context - decorative GitHub stars badge"),
        (r"(?:starCount|star_count|stargazers_count).*?\d+",
         "Hardcoded GitHub star counter - static data not tied to any API"),
        (r">\s*[A-Z][A-Z ]{6,}\s*:\s*<",
         "ALL_CAPS label inside a card e.g. '>COMMANDE INSTALLATION:<' - not documented in DESIGN.md", 0),
        # SYS_ACTIVE explicitly added — was missing, caused the FloraLink badge to pass
        (r"(?<![.\w/])\b(?:SYS_ACTIVE|SYS_INFO|SYS_STATUS|SYS_NODE|SYS_PING|SYS_ONLINE|SYS_RUNNING|SYS_UP|NODE_STATUS|API_HEALTH|API_LIVE)\b",
         "Injected system status badge — §0d explicitly forbidden (SYS_ACTIVE, SYS_STATUS, etc.)"),
        (r">\s*(?!(?:ID|URL|API|FAQ|CTA|OK|NEW|PRO|VIP|GDPR|RGPD|ALL|TOP|HOT|END|YES|NO|ON|OFF)\s*<)"
         r"[A-Z][A-Z\s]{5,30}<",
         "ALL_CAPS button text in HTML - ALL CAPS on CTAs = AI pattern", 0),
        (r"<(?:Star|StarIcon|StarFilled|FaStar|BsStar)\s*[^>]*/?>",
         "JSX star icon - decorative GitHub stars badge"),
        (r"radial-gradient\s*\([^)]{20,}\)",
         "Radial gradient in CSS - document in §1 if intentional"),
        (r"(?:border|ring)-(?:blue|accent|primary)-\d{3}[^;]*(?:card|Card|projet|project)",
         "Card with colored 'featured' border - variant not documented in §6"),
    ]

    # -----------------------------------------------------------------------
    # HTML-SPECIFIC BADGE PATTERNS
    # Scanned in .html files — different regex context than JSX
    # -----------------------------------------------------------------------
    HTML_BADGE_PATTERNS = [
        # Direct string match (case-insensitive) — catches vanilla HTML text content
        (r"SYS_ACTIVE",
         "SYS_ACTIVE badge text — explicitly forbidden in §0d"),
        (r"SYS_ONLINE|SYS_RUNNING|SYS_UP|SYS_STATUS",
         "SYS_* badge text — forbidden AI injection (§0d)"),
        # HTML class attributes containing badge-related names
        (r'class=["\'][^"\']*\bstatus[-_]badge\b[^"\']*["\']',
         "HTML class 'status-badge' — AI badge component"),
        (r'class=["\'][^"\']*\bpulse[-_]dot\b[^"\']*["\']',
         "HTML class 'pulse-dot' — animated status dot, AI signal"),
        (r'class=["\'][^"\']*\bsys[-_]badge\b[^"\']*["\']',
         "HTML class 'sys-badge' — AI system badge"),
        (r'class=["\'][^"\']*\bsystem[-_]badge\b[^"\']*["\']',
         "HTML class 'system-badge' — AI system badge"),
        # Monitoring-style class names in HTML
        (r'class=["\'][^"\']*(?:monitoring|grafana|datadog)[-_]style[^"\']*["\']',
         "HTML monitoring-style class — generic AI choice for sysadmin themes"),
        # ALL_CAPS isolated text in HTML inline elements (badge-like)
        # Matches: <span>SYS_ACTIVE</span>, <div>NODE_ONLINE</div>, etc.
        (r"<(?:span|div|p|label|small)[^>]*>\s*[A-Z][A-Z_]{3,}\s*</(?:span|div|p|label|small)>",
         "ALL_CAPS text in HTML inline element — potential AI status badge", 0),
        # Typewriter effect in HTML attributes or script blocks
        (r'typed\.js|typewriter[-_]effect|data-typed',
         "Typewriter effect in HTML — dev portfolio cliché, forbidden in §0d"),
        # Particle backgrounds
        (r'particles[-_]js|particlesJS|tsParticles',
         "Particles.js/tsParticles in HTML — forbidden in §0d (overdone since 2018)"),
        # Grid backgrounds
        (r'class=["\'][^"\']*\bgrid[-_]background\b[^"\']*["\']',
         "HTML class 'grid-background' — forbidden in §0d (present in 90% of AI portfolios)"),

        # G2 — Operational status pills (OPTIMAL, STABLE, CHARGE, OFFLINE…)
        (r'>\s*(?:OPTIMAL|STABLE|CHARGE|OFFLINE|CRITICAL|NOMINAL|WARNING|ONLINE|INACTIVE|ACTIF|INACTIF)\s*<',
         "Operational status pill (OPTIMAL/STABLE/CHARGE…) — AI monitoring vocabulary in UI (§0d)"),
        (r'class=["\'][^"\']*(?:status-pill|status-tag|status-chip|badge-status|badge-operational)[^"\']*["\']',
         "HTML class status-pill/badge-operational — AI operational badge component (§0d)"),

        # G3 — Machine / device IDs in UI (ID: VALVE_01, ID: FAN_01…)
        (r'ID\s*:\s*[A-Z][A-Z0-9_]+[0-9]',
         "Machine ID in UI (ID: VALVE_01) — technical ID exposed in interface, AI injection (§0d)"),
        (r'<[^>]*>\s*ID\s*:\s*[A-Z][A-Z_0-9]+\s*</[^>]*>',
         "Machine ID in HTML element — technical label not a UX element (§0d)"),

        # G4 — Fake system console ([HH:MM:SS], SYSTEM:, TELEMETRY:, Console Système…)
        (r'Console\s+Syst.me',
         "Console Système section — fake real-time terminal, never in brief (§0d)"),
        (r'Temps\s+R.el',
         "Temps Réel label on console-style section — AI monitoring injection (§0d)"),
        (r'\[\d{2}:\d{2}:\d{2}\]',
         "Timestamp [HH:MM:SS] in HTML — fake system log terminal pattern (§0d)"),
        (r'(?:SYSTEM|TELEMETRY|AUTO-PILOT|TELEMETRIE)\s*:',
         "SYSTEM:/TELEMETRY:/AUTO-PILOT: keyword — fake system console log (§0d)"),
        (r'class=["\'][^"\']*(?:console-log|system-console|log-terminal|terminal-output)[^"\']*["\']',
         "HTML class console-log/system-console — fake terminal component (§0d)"),

        # G5 — ALL_CAPS operational labels (PILOTE AUTOMATIQUE, AUTOMATIQUE (FERMÉ)…)
        (r'PILOTE\s+AUTOMATIQUE',
         "PILOTE AUTOMATIQUE — industrial ALL_CAPS operational label, AI injection (§0d)"),
        (r'AUTOMATIQUE\s*\(\s*(?:FERME|FERM\u00c9|ACTIF|INACTIF|OUVERT)',
         "AUTOMATIQUE (FERMÉ/ACTIF) — AI operational status label in ALL_CAPS (§0d)"),
        (r'(?:ACTIF|FERM\u00c9|INACTIF)\s*[-\u2013]\s*\d+\s*%',
         "ALL_CAPS status with percentage (ACTIF - 40%) — AI operational pill content (§0d)"),
        # A1 — Decorative emojis in UI headings/buttons/labels (AI cliché — never in brief)
        (r'<(?:h[1-6]|button|label)[^>]*>[^<]*(?:✨|🚀|💡|🎯|⚡|🔥|🌟|💫|🎨|🏆|🎉|🔮|🌈|🦄|🤖|🧠|💎|📊|📈|🌿|🌱|🔑|🛠️|🎪)',
         "Decorative emoji in UI heading/button — AI cliché in chrome elements (§0b)"),

        # A5 — Lorem ipsum / generic placeholder text
        (r'Lorem\s+ipsum\s+dolor',
         "Lorem ipsum placeholder text — unfinished delivery, never acceptable (§0b)"),
        (r'(?:Votre texte ici|Your text here|Description de votre produit|Insert text here|Placeholder text)',
         "Generic placeholder text in HTML — replace with real project content (§0b)"),

        # A6 — External placeholder images (picsum, via.placeholder, placehold.co)
        (r'src=.{0,4}(?:via\.placeholder\.com|picsum\.photos|placehold\.co|dummyimage\.com|lorempixel\.com)',
         "External placeholder image (picsum/via.placeholder.com) — forbidden in delivered code (§0b)"),

        # A2 — Invented marketing statistics hardcoded in HTML
        (r'>\s*\d[\d,]+\+?\s*(?:users|utilisateurs|clients|customers|integrations|membres|abonnés)\s*<',
         "Hardcoded marketing statistic — invented numbers forbidden without real data source (§0b)"),
        (r'>\s*9[89]\.\d%?\s*(?:uptime|disponibilité|availability|satisfaction)\s*<',
         "Hardcoded uptime/satisfaction stat (99.x%) — invented SLA figure, forbidden (§0b)"),

        # A3 — Trusted by / partners section injected without real data
        (r'(?:class|className)=[^>]*(?:trusted[-_]by|partners[-_]section|clients[-_]logos|brands[-_]section)',
         "Trusted-by/partners section class — AI injection, forbidden unless explicitly in brief (§0b)"),
        (r'>(?:\s*Trusted\s+by|\s*As\s+seen\s+on|\s*Ils\s+nous\s+font\s+confiance|\s*Nos\s+partenaires)\s*<',
         "Social proof section header — AI injection, forbidden without real partner data (§0b)"),

        # A4 — Hardcoded testimonial/review cards without real data source
        (r'(?:class|className)=[^>]*(?:testimonial[-_]card|review[-_]card|quote[-_]card|testimonial[-_]item)',
         "Testimonial/review card class — hardcoded testimonials are AI fabrication (§0b)"),

        # (H1 viewport check moved to a dedicated, case-correct check in _detect_html_slop)

        # H2 — CSS hardcoded hex colors bypassing custom properties (B6)
        # Detected separately in CSS patterns, listed here for HTML inline styles
        (r'style=["\'][^"\'>]*(?:color|background)\s*:\s*#[0-9a-fA-F]{3,6}',
         "Inline style with hardcoded hex color — bypass of CSS custom properties. Replace with var(--color-token) from DESIGN.md §2 (§0b B6)"),
    ]

    # -----------------------------------------------------------------------
    # CSS-SPECIFIC SLOP PATTERNS
    # Scanned in .css files
    # -----------------------------------------------------------------------
    CSS_SLOP_PATTERNS = [
        # Badge component classes
        (r"\.status[-_]badge\b",
         "CSS class '.status-badge' — AI badge component (§0d)"),
        (r"\.pulse[-_]dot\b",
         "CSS class '.pulse-dot' — animated AI status indicator (§0d)"),
        (r"\.sys[-_]badge\b|\.system[-_]badge\b",
         "CSS class '.sys-badge' / '.system-badge' — AI system badge"),
        # Animated pulse keyframes for decorative status dots
        (r"@keyframes\s+pulse[-_]ring",
         "@keyframes pulse-ring — animated status dot animation, AI injection signal (§0d)"),
        (r"animation:\s*[^;]*pulse[^;]*rounded|border-radius:\s*50%[^}]*animation:\s*[^;]*pulse",
         "Animated circular element with pulse — decorative status dot pattern"),
        # Neon/glow effects forbidden in §0d
        (r"(?:neon|glow)[-_](?:accent|effect|border|color)\s*:",
         "Neon/glow CSS property — forbidden in §0d"),
        (r"box-shadow\s*:[^;]*(?:#[0-9a-f]{6}|rgba\([^)]+\))[^;]*(?:neon|glow|neon)",
         "box-shadow with neon/glow descriptor — forbidden in §0d"),
        # Grid background patterns (dot-grid, line-grid)
        (r"background(?:-image)?\s*:[^;]*(?:repeating-linear-gradient|repeating-radial-gradient)[^;]*(?:1px|2px)",
         "Repeating gradient background (grid/dot pattern) — forbidden in §0d"),
        # Glassmorphism on non-functional elements
        (r"backdrop-filter\s*:[^;]*blur[^}]{0,200}(?:\.card|\.hero|\.section|\.container)\b",
         "backdrop-filter blur on structural element — glassmorphism outside functional context (§0d)"),
        # Typewriter CSS
        (r"@keyframes\s+typing|@keyframes\s+typewriter|animation:\s*[^;]*typing",
         "@keyframes typing/typewriter — typewriter effect, forbidden in §0d"),

        # G2 CSS — Operational pill shape classes
        (r"\.status[-_]pill\b",
         "CSS class .status-pill — AI operational pill component (§0d)"),
        (r"\.badge[-_]operational\b",
         "CSS class .badge-operational — AI operational badge (§0d)"),

        # G4 CSS — Fake system console styles
        (r"\.console[-_]log\b",
         "CSS class .console-log — fake terminal component style (§0d)"),
        (r"\.log[-_]entry\b",
         "CSS class .log-entry — fake system log line style (§0d)"),
        (r"\.system[-_]console\b",
         "CSS class .system-console — fake monitoring console style (§0d)"),
        (r"\.terminal[-_]output\b",
         "CSS class .terminal-output — fake terminal output style (§0d)"),
        (r"\.(?:log-system|log-telemetry|log-autopilot)\b",
         "CSS class log-system/log-telemetry/log-autopilot — fake console colored keywords (§0d)"),

        # G6 CSS — Monospace on non-code UI elements (systematic AI signature)
        (r"font-family\s*:\s*monospace",
         "font-family: monospace on UI element — systematic AI signature on labels/badges (§0d)"),
        # B4 — !important on layout properties (AI conflict patch signature)
        (r"(?:margin|padding|display|position|float|width|height)\s*:[^;]*!important",
         "!important on layout property — AI conflict patch, indicates structural CSS debt (§0b)"),

        # B5 — Arbitrary z-index values (AI stacking without a documented scale)
        (r"z-index\s*:\s*\d{4,}",
         "z-index 1000+ — undocumented stacking scale, forbidden without §5 z-index table (§0b)"),

        # B6 — Hardcoded hex colors in CSS bypassing DESIGN.md custom properties
        # (Excludes :root definitions, var() uses, and #000/#fff which are standard)
        (r"(?<!var\()(?<!\()(?<!:root)\s*(?:color|background-color|border-color|fill|stroke)\s*:\s*#(?!(?:0{3,6}|f{3,6}|000000|ffffff)\b)[0-9a-fA-F]{4,6}\b",
         "Hardcoded hex color in CSS — bypasses DESIGN.md custom properties. Replace with var(--token) from §2 palette (§0b B6)"),

        # H3 — Fixed px font-size on root/body (WCAG 1.4.4 — breaks browser zoom)
        (r"(?:html|body|:root)\s*\{[^}]*font-size\s*:\s*\d+px",
         "font-size in px on html/body/:root — breaks browser text zoom (WCAG 1.4.4). Use font-size: 100% or font-size: 1rem instead (§0b C7)"),

        # B7 — Style monotony: cliché blue→purple gradient on hero
        (r"\.hero[^{]*\{[^}]*background(?:-image)?\s*:[^;]*linear-gradient[^;]*(?:#3[Bb]82[Ff]6|blue)[^;]*(?:#8[Bb]5[Cc][Ff]6|purple)",
         "Blue→purple gradient on .hero — the most recognized AI template signature. Use project-specific gradient from DESIGN.md §2 (§0d)"),

        # B8 — Glassmorphism spam (backdrop-filter on non-modal elements)
        (r"(?<!modal)(?<!dialog)(?<!dropdown)[^{]*\{[^}]*backdrop-filter\s*:\s*blur\(",
         "backdrop-filter: blur() on non-modal element — glassmorphism overuse is an AI signature. Reserve for modals/dropdowns only (§0d)"),
    ]

    # Cliche gradients
    CLICHE_GRADIENTS = [
        (r"(?:from|to).*?blue.*?(?:from|to).*?purple|purple.*?blue", "blue->purple"),
        (r"(?:from|to).*?pink.*?(?:from|to).*?purple|purple.*?pink", "pink->purple"),
        (r"(?:from|to).*?cyan.*?(?:from|to).*?blue|blue.*?cyan", "cyan->blue"),
        (r"(?:from|to).*?red.*?(?:from|to).*?orange|orange.*?red", "red->orange"),
    ]

    # Three.js antipatterns
    THREEJS_SLOP_PATTERNS = [
        (r"new\s+THREE\.\w+Geometry\s*\([^)]*\)[^}]{0,200}requestAnimationFrame",
         "Geometry created inside animate() - new GPU buffer each frame, VRAM exhausted in seconds"),
        (r"requestAnimationFrame[^}]{0,200}new\s+THREE\.\w+Geometry",
         "Geometry created inside the render loop - critical VRAM leak"),
        (r"function\s+\w+\s*\([^)]*\)[^}]{0,300}new\s+THREE\.WebGLRenderer",
         "WebGLRenderer created inside a repeatedly-called function - GPU context leak"),
        (r"useEffect[^}]{0,400}new\s+THREE\.WebGLRenderer",
         "WebGLRenderer in useEffect without cleanup - recreated on every React render"),
        (r"setPixelRatio\s*\(\s*window\.devicePixelRatio\s*\)",
         "setPixelRatio without cap - Retina 3x = 9 px/CSS px. Use Math.min(devicePixelRatio, 2)"),
        (r"addEventListener.{0,20}(?:mousemove|pointermove).{0,200}new THREE.Raycaster",
         "new THREE.Raycaster() inside mousemove - 200+ allocations/sec. Create once, reuse"),
        (r"for\s*\([^)]+\)[^}]{0,200}new\s+THREE\.Mesh(?:Standard|Phong|Lambert)Material",
         "Material recreated in a loop - share a single instance across identical meshes"),
        (r"new\s+THREE\.CapsuleGeometry",
         "THREE.CapsuleGeometry does not exist in r128 (added in r142)"),
        (r"scene\.remove\s*\([^)]+\)(?![^}]{0,200}\.dispose\s*\(\))",
         "scene.remove() without dispose() - geometry/material/textures stay in VRAM indefinitely"),
        (r"new\s+THREE\.SphereGeometry\s*\([^,]+,\s*(?:128|256|512)\s*,",
         "SphereGeometry with 128+ segments - excessive budget"),
        (r"for\s*\([^)]+\)[^}]{0,200}\.castShadow\s*=\s*true",
         "castShadow enabled in a loop on every object - shadow map pass per mesh, very expensive"),
        (r"unpkg\.com/three@latest|cdnjs\.cloudflare\.com.*three.*latest",
         "Unversioned Three.js CDN - pin to r128"),
        (r"new\s+THREE\.PerspectiveCamera[^}]{0,500}renderer\.render",
         "PerspectiveCamera with no apparent camera.lookAt() - scene may be invisible"),
    ]

    # Vague buzzwords
    BUZZWORDS = {
        "premium": "Replace with a precise description (e.g. 'High contrast, generous spacings')",
        "moderne": "Replace with a precise description (e.g. 'Minimalist', 'Geometric')",
        "elegant": "Replace with a precise description (e.g. 'Generous spacings', 'Hierarchical typography')",
        "magnifique": "Replace with a precise description",
        "incroyable": "Replace with a precise description",
        "unique": "Replace with a precise description",
        "innovant": "Replace with a precise description",
        "futuriste": "Use only if justified by concrete visual choices",
    }

    # Generic template sections
    TEMPLATE_SECTIONS = {
        "hero": "Hero section",
        "features": "Feature grid",
        "testimonials": "Testimonials section",
        "cta": "Call to action",
        "pricing": "Pricing",
        "faq": "FAQ",
        "footer": "Footer",
    }

    # Generic fonts
    GENERIC_FONTS = {
        "helvetica", "arial", "times new roman", "georgia", "verdana",
        "courier", "comic sans", "impact", "trebuchet", "palatino",
    }

    # -----------------------------------------------------------------------
    # ACCESSIBILITY PATTERNS — HTML structural requirements (WCAG 2.1)
    # Scanned in .html files
    # -----------------------------------------------------------------------
    HTML_ACCESSIBILITY_PATTERNS = [
        # C1 — Images without alt attribute (WCAG 2.1 §1.1.1)
        (r'<img(?![^>]*\balt=)[^>]*/?>',
         "img without alt attribute — WCAG 2.1 §1.1.1 violation (§0b)"),
        # C2 — Buttons without explicit type attribute
        (r'<button(?![^>]*\btype=)[^>]*>',
         "button without type attribute — undefined submit/button/reset behavior (§0b)"),
        # C4 — div with onclick handler (missing semantic role)
        (r'<div[^>]*\bonclick=[^>]*>',
         "div with onclick — replace with <button> or add role='button' + tabIndex (§0b)"),
    ]

    # -----------------------------------------------------------------------
    # CODE QUALITY PATTERNS — Scanned in .js/.ts/.jsx/.tsx
    # -----------------------------------------------------------------------
    CODE_QUALITY_PATTERNS = [
        # C5 — console.log left in production code
        (r'\bconsole\.log\s*\(',
         "console.log in delivered code — remove or guard with development-only condition (§0b)"),
        # C6 — Unresolved TODO/FIXME/HACK comments
        (r'//\s*(?:TODO|FIXME|HACK|XXX|TEMP)\b',
         "Unresolved TODO/FIXME/HACK comment in delivered code — resolve before delivery (§0b)"),
        # C7 — Hardcoded API URLs in source code
        (r'(?:API_URL|BASE_URL|apiUrl|baseUrl)\s*=\s*.https?://',
         "Hardcoded API URL in source — move to .env file and use process.env (§0b)"),
        # D3 — Invented mock/fake data variables
        (r'\b(?:mock|sample|demo|fake|dummy)(?:Data|Users|Products|Items|Entries)\b',
         "Mock/fake data variable — invented data forbidden without explicit brief instruction (§0b)"),
        (r'(?:mock|sample|demo|fake)[-_](?:data|users|products|items)\s*[=:]',
         "Mock/fake data assignment — invented data forbidden without explicit brief instruction (§0b)"),
    ]

    def __init__(self, design_file: str = None, code_dir: str = None):
        self.design_file = Path(design_file) if design_file else None
        self.code_dir = Path(code_dir) if code_dir else None
        self.issues: List[Dict] = []
        self.score = 100
        self._whitelist = self._load_slop_ignore()

    # -- .slop-ignore -----------------------------------------------------------

    def _load_slop_ignore(self) -> Dict[str, List[str]]:
        whitelist: Dict[str, List[str]] = {
            "icons": [], "buzzwords": [], "gradients": [], "badges": [], "files": []
        }
        candidates = [
            Path(".slop-ignore"),
            Path("../.slop-ignore"),
            Path(__file__).parent.parent / ".slop-ignore",
        ]
        ignore_path = next((p for p in candidates if p.exists()), None)
        if not ignore_path:
            return whitelist

        current_section = None
        for raw_line in ignore_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            section_match = re.match(r"^\[(\w+)\]$", line)
            if section_match:
                current_section = section_match.group(1).lower()
                continue
            if current_section and current_section in whitelist:
                token = line.split("#")[0].strip()
                justification = line.split("#")[1].strip() if "#" in line else ""
                if token and justification:
                    whitelist[current_section].append(token.lower())

        if any(whitelist.values()):
            loaded = sum(len(v) for v in whitelist.values())
            print(f"  [INFO] .slop-ignore loaded - {loaded} exemption(s)")

        return whitelist

    def _add_issue(self, issue_type: str, message: str, suggestion: str = "", severity: int = 1):
        self.issues.append({
            "type": issue_type.lower(),
            "severity": "warning" if severity == 1 else "error",
            "message": message,
            "suggestion": suggestion,
        })
        self.score -= 5 * severity

    def _is_whitelisted(self, section: str, token: str) -> bool:
        return token.lower() in self._whitelist.get(section, [])

    def _file_is_ignored(self, path) -> bool:
        path_str = str(path).replace("\\", "/")
        for pattern in self._whitelist.get("files", []):
            if pattern.rstrip("/") in path_str:
                return True
        return False

    # -----------------------------------------------------------------------
    # Mobile slop
    # -----------------------------------------------------------------------
    def _detect_mobile_slop(self, content: str, file_path: Path = None):
        ctx = str(file_path.name) if file_path else "code"
        is_swift  = file_path and file_path.suffix in {".swift"}
        is_kotlin = file_path and file_path.suffix in {".kt", ".kts"}
        is_dart   = file_path and file_path.suffix in {".dart"}
        is_rn     = file_path and file_path.suffix in {".tsx", ".jsx"} and (
                      "react-native" in content.lower() or
                      "StyleSheet.create" in content or
                      "from 'react-native'" in content
                    )
        if not (is_swift or is_kotlin or is_dart or is_rn):
            return
        for pattern, description in self.MOBILE_SLOP_PATTERNS:
            if re.search(pattern, content):
                self._add_issue("MOBILE_SLOP", f"{description} [{ctx}]",
                                "Use the platform's native components and APIs", severity=2)
        if is_swift and "Color.white" in content and "colorScheme" not in content:
            self._add_issue("MOBILE_SLOP", f"Fixed white color with no dark mode adaptation [{ctx}]",
                            "Use Color(.systemBackground) or @Environment(.colorScheme)", severity=1)
        if is_kotlin and "Color.White" in content and "isSystemInDarkTheme" not in content:
            self._add_issue("MOBILE_SLOP", f"Fixed Color.White with no adaptive dark mode [{ctx}]",
                            "Use MaterialTheme.colorScheme.background", severity=1)
        if is_swift and "Image(" in content:
            if "accessibilityLabel" not in content and "Label(" not in content:
                self._add_issue("MOBILE_SLOP", f"SwiftUI Image without accessibilityLabel [{ctx}]",
                                "Add .accessibilityLabel(String) to every Image", severity=1)
        if is_kotlin and "Image(" in content and "contentDescription" not in content:
            self._add_issue("MOBILE_SLOP", f"Compose Image without contentDescription [{ctx}]",
                            "Add contentDescription = String or null if decorative", severity=1)

    # -----------------------------------------------------------------------
    # Three.js slop
    # -----------------------------------------------------------------------
    def _detect_threejs_slop(self, content: str, file_path: Path = None):
        ctx = file_path.name if file_path else "code"
        is_three = any(k in content for k in [
            "THREE.", "from 'three'", 'from "three"',
            "WebGLRenderer", "PerspectiveCamera", "BufferGeometry"
        ])
        if not is_three:
            return
        for pattern, description in self.THREEJS_SLOP_PATTERNS:
            if "PerspectiveCamera with no apparent camera.lookAt" in description:
                if "PerspectiveCamera" in content and "lookAt" not in content:
                    self._add_issue("THREEJS_SLOP", f"{description} [{ctx}]",
                                    "Add camera.lookAt(scene.position) before the first render", severity=1)
                continue
            if re.search(pattern, content, re.DOTALL):
                self._add_issue("THREEJS_SLOP", f"{description} [{ctx}]",
                                "See references/threejs-best-practices.md", severity=2)

    # -----------------------------------------------------------------------
    # HTML slop — scans .html files for badge injections and forbidden patterns
    # -----------------------------------------------------------------------
    def _detect_html_slop(self, content: str, file_path: Path = None):
        """
        Detect AI slop patterns specific to HTML files.
        Covers: SYS_ACTIVE badges, class-based badge patterns, typewriter, particles.
        Called for every .html file in the code directory.
        """
        ctx = file_path.name if file_path else "html"
        for entry in self.HTML_BADGE_PATTERNS:
            pattern, message = entry[0], entry[1]
            flags = entry[2] if len(entry) > 2 else re.IGNORECASE
            if re.search(pattern, content, flags):
                self._add_issue(
                    "HTML_BADGE",
                    f"{message} [{ctx}]",
                    (
                        "Remove this element — never requested. "
                        "If functionally required, document it in DESIGN.md §6 with business justification."
                    ),
                    severity=2  # Error-level: direct contract violation
                )

        # H1 — viewport meta: flag ONLY when <head> exists and no viewport meta is present.
        # The previous single-regex approach false-positived even when the meta WAS present
        # (variable-length negative lookahead). This now mirrors audit_accessibility.
        if re.search(r"<head[\s>]", content, re.IGNORECASE) and not re.search(
            r'<meta[^>]+name=["\']viewport["\']', content, re.IGNORECASE
        ):
            self._add_issue(
                "HTML_BADGE",
                f"<head> is missing <meta name='viewport'> — mobile layout will break silently. "
                f"Add: <meta name='viewport' content='width=device-width, initial-scale=1'> [{ctx}]",
                "Add the viewport meta tag inside <head>.",
                severity=2,
            )

    # -----------------------------------------------------------------------
    # CSS slop — scans .css files for forbidden animation/badge CSS rules
    # -----------------------------------------------------------------------
    def _detect_css_slop(self, content: str, file_path: Path = None):
        """
        Detect AI slop patterns in CSS files.
        Covers: badge class names, pulse animations, neon/glow, typewriter keyframes.
        Called for every .css file in the code directory.
        """
        ctx = file_path.name if file_path else "css"
        for pattern, message in self.CSS_SLOP_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                self._add_issue(
                    "CSS_SLOP",
                    f"{message} [{ctx}]",
                    (
                        "Remove or justify this CSS rule. "
                        "It correlates with a forbidden badge/effect pattern (§0d). "
                        "If kept, document it explicitly in DESIGN.md §7 Motion."
                    ),
                    severity=1
                )

    # -----------------------------------------------------------------------
    # Accessibility check — HTML structural requirements
    # -----------------------------------------------------------------------
    def _detect_html_accessibility(self, content: str, file_path: Path = None):
        """
        Detect accessibility violations in HTML files.
        Covers: img without alt, button without type, div with onclick.
        Called for every .html file in the code directory.
        """
        ctx = file_path.name if file_path else "html"
        for pattern, message in self.HTML_ACCESSIBILITY_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                self._add_issue(
                    "HTML_ACCESSIBILITY",
                    f"{message} [{ctx}]",
                    "Fix the accessibility violation before delivery — blocked by §0b.",
                    severity=1
                )

    # -----------------------------------------------------------------------
    # Code quality check — console.log, TODO/FIXME, mock data, hardcoded URLs
    # -----------------------------------------------------------------------
    def _detect_code_quality_issues(self, content: str, file_path: Path = None):
        """
        Detect code quality issues in JS/TS/JSX/TSX files.
        Covers: console.log, unresolved TODO/FIXME, hardcoded API URLs, mock data.
        Called for every JS/TS/JSX/TSX file in the code directory.
        """
        ctx = file_path.name if file_path else "code"
        for pattern, message in self.CODE_QUALITY_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                self._add_issue(
                    "CODE_QUALITY",
                    f"{message} [{ctx}]",
                    "Fix before delivery — see fix_instruction in JSON mode.",
                    severity=1
                )

    # -----------------------------------------------------------------------
    # Entry points
    # -----------------------------------------------------------------------
    def run(self, json_mode: bool = False) -> bool:
        if self.design_file:
            self._check_design_file()
        if self.code_dir:
            self._check_code_directory()
        if json_mode:
            import json as _json
            print(_json.dumps(self._build_json_report(), indent=2, ensure_ascii=False))
        else:
            self._print_report()
        return self.score >= 80

    def _check_design_file(self):
        if not self.design_file.exists():
            print(f"[ERROR] File not found: {self.design_file}")
            return
        content = self.design_file.read_text(encoding="utf-8")
        self._detect_shadcn_defaults(content)
        self._detect_logo_placeholders(content)
        self._detect_buzzwords(content)
        self._detect_generic_icons(content)
        self._detect_cliche_gradients(content)
        self._detect_generic_fonts(content)
        self._detect_status_badges(content)

    def _check_code_directory(self):
        if not self.code_dir.exists():
            print(f"[ERROR] Directory not found: {self.code_dir}")
            return

        # ── JSX / TSX / JS / TS / native mobile ─────────────────────────
        mobile_web_exts = ["*.tsx", "*.jsx", "*.js", "*.ts", "*.swift", "*.kt", "*.kts", "*.dart"]
        for ext in mobile_web_exts:
            for file_path in self.code_dir.rglob(ext):
                if not self._file_is_ignored(file_path):
                    self._check_code_file(file_path)

        # shadcn/ui default usage in TSX/JSX
        for ext in ("*.tsx", "*.jsx"):
            for file_path in self.code_dir.rglob(ext):
                if not self._file_is_ignored(file_path):
                    self._detect_shadcn_defaults(
                        file_path.read_text(encoding="utf-8", errors="ignore"), file_path
                    )

        # Status badges in TSX/JSX
        for ext in ("*.tsx", "*.jsx"):
            for file_path in self.code_dir.rglob(ext):
                if not self._file_is_ignored(file_path):
                    self._detect_status_badges(
                        file_path.read_text(encoding="utf-8", errors="ignore"), file_path
                    )

        # ── HTML files — badge injection + forbidden patterns ────────────
        for file_path in self.code_dir.rglob("*.html"):
            if not self._file_is_ignored(file_path):
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                self._detect_html_slop(content, file_path)
                self._detect_status_badges(content, file_path)
                self._detect_logo_placeholders(content, file_path)
                self._detect_undocumented_gradients(content)

        # ── CSS files — forbidden animation/badge CSS rules ──────────────
        for file_path in self.code_dir.rglob("*.css"):
            if not self._file_is_ignored(file_path):
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                self._detect_css_slop(content, file_path)

        # ── HTML accessibility (img alt, button type, div onclick) ───────
        for file_path in self.code_dir.rglob("*.html"):
            if not self._file_is_ignored(file_path):
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                self._detect_html_accessibility(content, file_path)

        # ── Code quality (console.log, TODO, mock data, hardcoded URLs) ──
        for ext in ("*.js", "*.ts", "*.jsx", "*.tsx"):
            for file_path in self.code_dir.rglob(ext):
                if not self._file_is_ignored(file_path):
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    self._detect_code_quality_issues(content, file_path)

    def _check_code_file(self, file_path: Path):
        content = file_path.read_text(encoding="utf-8", errors="ignore")

        # Lucide imports
        lucide_imports = re.findall(
            r"from\s+['\"]lucide-react['\"].*?import\s+{([^}]+)}", content
        )
        if lucide_imports:
            icons = [i.strip() for i in lucide_imports[0].split(",")]
            generic = [i for i in icons if i.lower() in self.GENERIC_ICONS]
            if generic:
                self.issues.append({
                    "type": "generic_icons",
                    "file": str(file_path),
                    "severity": "warning",
                    "message": f"Generic Lucide icons: {', '.join(generic)}",
                    "suggestion": "Use custom SVG or a coherent icon pack"
                })
                self.score -= 5 * len(generic)

        # Template sections
        template_count = sum(1 for section in self.TEMPLATE_SECTIONS if section in content.lower())
        if template_count >= 4:
            self.issues.append({
                "type": "template_structure",
                "file": str(file_path),
                "severity": "warning",
                "message": f"Generic template structure ({template_count} sections)",
                "suggestion": "Consider a more distinctive approach"
            })
            self.score -= 10

        self._detect_mobile_slop(content, file_path)
        self._detect_threejs_slop(content, file_path)

    # -----------------------------------------------------------------------
    # Pattern detectors (shared across JSX, HTML, DESIGN.md)
    # -----------------------------------------------------------------------
    def _detect_status_badges(self, content: str, file_path: Path = None):
        for entry in self.STATUS_BADGE_PATTERNS:
            pattern, message = entry[0], entry[1]
            flags = entry[2] if len(entry) > 2 else re.IGNORECASE
            if re.search(pattern, content, flags):
                issue = {
                    "type": "status_badge",
                    "severity": "warning",
                    "message": f"AI status badge: {message}",
                    "suggestion": (
                        "Remove this badge - never requested, immediate AI signal. "
                        "If a status is functionally required, justify it in DESIGN.md."
                    )
                }
                if file_path:
                    issue["file"] = str(file_path)
                self.issues.append(issue)
                self.score -= 8

    def _detect_buzzwords(self, content: str):
        for buzzword, suggestion in self.BUZZWORDS.items():
            if self._is_whitelisted("buzzwords", buzzword):
                continue
            if re.search(rf"\b{buzzword}\b", content, re.IGNORECASE):
                self.issues.append({
                    "type": "buzzword",
                    "severity": "warning",
                    "message": f"Vague buzzword: '{buzzword}'",
                    "suggestion": suggestion
                })
                self.score -= 3

    def _detect_generic_icons(self, content: str):
        for icon in self.GENERIC_ICONS:
            if self._is_whitelisted("icons", icon):
                continue
            if re.search(rf"\b{icon}\b", content, re.IGNORECASE):
                self.issues.append({
                    "type": "generic_icon",
                    "severity": "info",
                    "message": f"Generic icon: {icon}",
                    "suggestion": "Consider custom SVG if used in a non-standard way"
                })
                self.score -= 1

    def _detect_undocumented_gradients(self, content: str):
        grad_patterns = [
            r"radial-gradient\s*\(",
            r"linear-gradient\s*\(",
            r"conic-gradient\s*\(",
            r"bg-gradient-",
        ]
        design_mentions = []
        if self.design_file:
            try:
                design_content = self.design_file.read_text(encoding="utf-8", errors="ignore").lower()
                design_mentions = re.findall(r"gradient|dégradé|degrade|mesh|radial", design_content)
            except Exception:
                pass
        for pat in grad_patterns:
            if re.search(pat, content, re.IGNORECASE):
                if not design_mentions:
                    self._add_issue(
                        "UNDOCUMENTED_GRADIENT",
                        "Gradient detected in code but not documented in §1 of DESIGN.md.",
                        "Document the gradient in §1 'Allowed effects' with a visual justification.",
                        severity=1
                    )
                break

    def _detect_cliche_gradients(self, content: str):
        for pattern, name in self.CLICHE_GRADIENTS:
            if re.search(pattern, content, re.IGNORECASE):
                self.issues.append({
                    "type": "cliche_gradient",
                    "severity": "warning",
                    "message": f"Cliche gradient: {name}",
                    "suggestion": "Justify by semantic role or consider an alternative"
                })
                self.score -= 5

    def _detect_generic_fonts(self, content: str):
        for font in self.GENERIC_FONTS:
            if re.search(rf"\b{font}\b", content, re.IGNORECASE):
                self.issues.append({
                    "type": "generic_font",
                    "severity": "error",
                    "message": f"Generic font: {font}",
                    "suggestion": "Use Google Fonts or a custom font"
                })
                self.score -= 10

    def _detect_logo_placeholders(self, content: str, file_path: Path = None):
        for pattern, message in self.LOGO_PLACEHOLDERS:
            if re.search(pattern, content, re.IGNORECASE):
                issue = {
                    "type": "logo_placeholder",
                    "severity": "error",
                    "message": f"Generic logo/name detected: {message}",
                    "suggestion": "Use a stylized text logo (font-bold tracking-tight uppercase) if no logo is provided."
                }
                if file_path:
                    issue["file"] = str(file_path)
                self.issues.append(issue)
                self.score -= 10

    def _detect_shadcn_defaults(self, content: str, file_path: Path = None):
        for pattern, message in self.SHADCN_DEFAULT_PATTERNS:
            if re.search(pattern, content):
                issue = {
                    "type": "shadcn_default",
                    "severity": "warning",
                    "message": f"Default shadcn/ui: {message}",
                    "suggestion": "Customize shadcn/ui components via Tailwind CSS and design tokens."
                }
                if file_path:
                    issue["file"] = str(file_path)
                self.issues.append(issue)
                self.score -= 5

    # -----------------------------------------------------------------------
    # JSON report — machine-readable output for model self-correction
    # -----------------------------------------------------------------------
    def _build_json_report(self) -> dict:
        """
        Build a structured JSON report consumed by the model self-correction loop.
        Each violation carries a precise fix_instruction the model executes directly.
        """
        violations = [
            {
                "file": issue.get("file", str(self.design_file) if self.design_file else "DESIGN.md"),
                "type": issue["type"],
                "severity": issue.get("severity", "warning"),
                "message": issue["message"],
                "fix_instruction": self._get_fix_instruction(issue),
            }
            for issue in self.issues
        ]
        return {
            "score": self.score,
            "passed": self.score >= 80,
            "violation_count": len(violations),
            "violations": violations,
            "self_correction_protocol": (
                "For each violation: open 'file', locate the pattern in 'message', "
                "apply 'fix_instruction' precisely — no improvisation, no scope creep. "
                "After all fixes, re-run: "
                "python3 scripts/detect_ai_slop.py --design DESIGN.md --code . --json"
            ),
        }

    def _get_fix_instruction(self, issue: dict) -> str:
        """Return a precise, model-executable fix instruction per violation type."""
        t = issue["type"].lower()
        msg = issue.get("message", "").lower()
        suggestion = issue.get("suggestion", "")

        if t == "html_badge":
            if "sys_active" in msg or "sys_" in msg or "sys_online" in msg:
                return (
                    "Remove the entire HTML element (div/span/label) that contains this text "
                    "and all its children. Then open every .css file and delete ALL rule blocks "
                    "that reference: .status-badge, .pulse-dot, .pulse-dot::after, "
                    ".status-label, .sys-badge, .system-badge, @keyframes pulse-ring. "
                    "Do not touch any other CSS rule."
                )
            elif "pulse-dot" in msg:
                return (
                    "Remove the HTML element with class 'pulse-dot' and its parent container "
                    "if the container serves no other purpose. "
                    "Remove from CSS: .pulse-dot, .pulse-dot::after, @keyframes pulse-ring."
                )
            elif "typewriter" in msg or "typed" in msg:
                return (
                    "Remove the typed.js / typewriter script tag and its CDN import. "
                    "Remove all data-typed attributes. Replace animated text with a static <span> or <h1>."
                )
            elif "particles" in msg:
                return (
                    "Remove the particles.js / tsParticles script tag and CDN import. "
                    "Remove the canvas element and its initialization <script> block."
                )
            elif "grid-background" in msg:
                return (
                    "Remove the HTML element with class 'grid-background'. "
                    "In CSS, remove any repeating-gradient rule that produces a dot or line grid."
                )
            elif any(k in msg for k in ["operational status pill", "status-pill", "badge-operational",
                                         "optimal", "stable", "charge", "offline", "nominal",
                                         "actif", "inactif"]):
                return (
                    "Remove this operational status pill entirely. "
                    "If a status must be communicated, replace with sentence-case inline text: "
                    "'<span class=\"status-ok\">Optimal</span>' — no pill shape, no ALL_CAPS, no monospace. "
                    "Remove from CSS: .status-pill, .badge-operational, .status-tag, .status-chip rule blocks."
                )
            elif any(k in msg for k in ["machine id", "id: valve", "id: fan", "technical id",
                                         "technical label"]):
                return (
                    "Remove the 'ID: DEVICE_01' label from the HTML entirely. "
                    "Technical device identifiers have no place in a user-facing interface. "
                    "If a device label is required by the brief, use a human-readable name from the data model."
                )
            elif any(k in msg for k in ["console syst", "fake real-time", "hh:mm:ss",
                                         "fake system log", "fake terminal", "console-log",
                                         "system-console", "system:", "telemetry:", "auto-pilot:"]):
                return (
                    "Remove the entire Console Système / fake terminal section: "
                    "the container div, all log-entry children, and any <script> that populates it. "
                    "Remove from CSS: .console-log, .log-entry, .system-console, .terminal-output, "
                    ".log-system, .log-telemetry, .log-autopilot, and any dark monospace terminal block."
                )
            elif any(k in msg for k in ["pilote automatique", "automatique (", "all_caps operational",
                                         "all_caps status", "actif - ", "fermé -", "inactif -"]):
                return (
                    "Convert to sentence case: 'PILOTE AUTOMATIQUE' → 'Pilote automatique', "
                    "'AUTOMATIQUE (FERMÉ)' → 'Automatique — fermé', 'ACTIF - 40%' → 'Actif — 40%'. "
                    "Remove text-transform: uppercase from these elements' CSS rules. "
                    "Status in parentheses → use a semantic color class, not ALL_CAPS text."
                )
            elif "emoji" in msg or "ai cliché in chrome" in msg:
                return (
                    "Remove the emoji character from the HTML element text. "
                    "Emojis in UI chrome (headings, buttons, labels) are an AI cliché — they signal "
                    "generated content. If an icon is semantically required, use an inline SVG "
                    "or an icon from the project's defined icon system."
                )
            elif "lorem ipsum" in msg or "placeholder text" in msg:
                return (
                    "Replace this placeholder text with real project content. "
                    "Never deliver a page with Lorem ipsum or generic filler copy visible to users."
                )
            elif "placeholder image" in msg or "picsum" in msg or "via.placeholder" in msg:
                return (
                    "Replace the placeholder image src with a real asset from the project brief. "
                    "If no image is available, use a CSS background or project-specific SVG illustration — "
                    "never an external placeholder service in delivered code."
                )
            elif "hardcoded marketing statistic" in msg or "uptime" in msg or "satisfaction" in msg:
                return (
                    "Remove the hardcoded number. "
                    "If a real metric exists, load it from an API or CMS. "
                    "If no real data exists, remove the stat block entirely — "
                    "invented numbers erode credibility and are never acceptable."
                )
            elif "trusted-by" in msg or "social proof" in msg or "partners" in msg:
                return (
                    "Remove the entire trusted-by / partners section from HTML and CSS. "
                    "This section is only valid if real partner logos and names are provided in the brief. "
                    "Without real data, this is AI fabrication — remove it."
                )
            elif "testimonial" in msg or "review card" in msg:
                return (
                    "Remove the testimonial/review card(s). "
                    "Hardcoded testimonials with invented names, quotes, and avatars are AI fabrication. "
                    "If testimonials are required, they must come from a real data source "
                    "(API, CMS, or assets explicitly provided in the brief)."
                )
            elif "viewport" in msg or "meta name='viewport'" in msg:
                return (
                    "Add <meta name='viewport' content='width=device-width, initial-scale=1'> "
                    "as the first child of <head>, before any other meta or link tags. "
                    "Without this tag, mobile browsers render the page at desktop width — "
                    "all responsive breakpoints become ineffective."
                )
            elif "inline style" in msg and "hardcoded hex" in msg:
                return (
                    "Remove the style attribute containing the hardcoded hex color. "
                    "Replace with a CSS class that uses a custom property: var(--color-token). "
                    "Never use inline hex colors — they bypass the DESIGN.md §2 token system "
                    "and break theme switching / dark mode."
                )
            else:
                return (
                    "Remove the identified HTML element entirely. "
                    "Search all .css files for selectors matching its class names and remove those rule blocks."
                )

        elif t == "css_slop":
            if "pulse" in msg or "status-badge" in msg or "sys-badge" in msg:
                return (
                    "Delete the entire CSS rule block for this selector, "
                    "including any @keyframes animation it references."
                )
            elif "neon" in msg or "glow" in msg:
                return (
                    "Remove the box-shadow value containing 'neon' or 'glow'. "
                    "If a border is still needed, replace with: border: 1px solid var(--border-color)."
                )
            elif "backdrop-filter" in msg:
                return (
                    "Remove the backdrop-filter property unless this element is a functional modal "
                    "or dropdown explicitly documented in DESIGN.md §6."
                )
            elif "typewriter" in msg or "typing" in msg:
                return "Delete the @keyframes typing / typewriter block and every animation property referencing it."
            elif "gradient" in msg:
                return (
                    "Remove the repeating-gradient background rule. "
                    "Replace with a solid background-color using the DESIGN.md §2 Background token."
                )
            elif any(k in msg for k in ["console-log", "log-entry", "system-console",
                                         "terminal-output", "log-system", "log-telemetry",
                                         "log-autopilot", "fake terminal", "fake console"]):
                return (
                    "Delete this CSS rule block entirely. "
                    "It styles a fake terminal / system console that must also be removed from HTML. "
                    "Remove as a group: .console-log, .log-entry, .system-console, .terminal-output, "
                    ".log-system, .log-telemetry, .log-autopilot."
                )
            elif any(k in msg for k in ["status-pill", "badge-operational", "operational pill",
                                         "operational badge"]):
                return (
                    "Delete this CSS rule block entirely. "
                    "The status pill component must be removed from HTML and CSS simultaneously. "
                    "Also remove: .status-tag, .status-chip, any border-radius+padding combo styled as a pill."
                )
            elif "monospace" in msg and "ui element" in msg:
                return (
                    "Remove font-family: monospace from this CSS rule. "
                    "Monospace is permitted only on <code>, <pre>, <kbd>, and <samp> elements. "
                    "Replace with: font-family: var(--font-sans) or the DESIGN.md §3 body font token."
                )
            elif "!important on layout" in msg:
                return (
                    "Remove '!important' from this CSS rule. "
                    "!important on layout properties (margin, padding, display, position) indicates "
                    "a cascade conflict — fix the cascade specificity instead: "
                    "check selector order, remove conflicting rules, restructure component CSS."
                )
            elif "z-index 1000" in msg or ("z-index" in msg and "undocumented" in msg):
                return (
                    "Replace the arbitrary z-index value with a documented scale value. "
                    "Add a z-index scale to DESIGN.md §5 (example: modal=300, dropdown=200, tooltip=100, sticky=50). "
                    "Then use the appropriate documented value — never 9999 or 99999."
                )
            elif "hardcoded hex color in css" in msg or "b6" in msg:
                return (
                    "Replace the hardcoded hex value with a CSS custom property from DESIGN.md §2. "
                    "Example: color: #3b82f6 → color: var(--color-primary). "
                    "If the token does not exist yet, add it to :root in the base stylesheet first. "
                    "Never hardcode hex colors outside :root definitions."
                )
            elif "font-size" in msg and "px" in msg and ("html" in msg or "body" in msg or ":root" in msg):
                return (
                    "Replace font-size: Npx on html/body/:root with font-size: 100% (or remove it). "
                    "A px value on the root element overrides the user's browser font-size preference, "
                    "breaking WCAG 1.4.4 (Text Resize). All descendant rem values will scale correctly "
                    "when the root uses a percentage or is unset."
                )
            elif "blue" in msg and "purple" in msg and "hero" in msg:
                return (
                    "Remove the blue→purple linear-gradient from .hero. "
                    "Replace with a project-specific gradient documented in DESIGN.md §2, "
                    "or use a solid background-color token. "
                    "Blue→purple on hero is the single most recognisable AI template signature."
                )
            elif "glassmorphism" in msg or ("backdrop-filter" in msg and "non-modal" in msg):
                return (
                    "Remove backdrop-filter: blur() from this element. "
                    "Glassmorphism is reserved for modals, dropdowns, and overlays explicitly "
                    "documented in DESIGN.md §6. "
                    "If this element requires visual depth, use box-shadow with a DESIGN.md §2 shadow token instead."
                )
            else:
                return "Delete the identified CSS rule block entirely."

        elif t == "status_badge":
            return (
                "Remove this JSX/HTML element. If it is a component, delete the component call "
                "and its import statement. Do not add it back unless it is documented in DESIGN.md §6 "
                "with an explicit business justification and a gate 1 re-run."
            )

        elif t == "generic_icons":
            return (
                "Replace each listed generic icon with a custom inline SVG specific to the "
                "project's context, or remove it if purely decorative. "
                "Functional icons (navigation, actions) must remain but use purpose-specific SVG paths."
            )

        elif t == "logo_placeholder":
            return (
                "Replace with a styled text logo: "
                "<span class=\"font-bold tracking-tight uppercase\">ProjectName</span>. "
                "Never use a graphic placeholder or an improvised SVG icon as a logo."
            )

        elif t == "buzzword":
            return (
                "Replace the vague term with a precise visual description drawn from DESIGN.md. "
                "Example: instead of 'elegant' → '32px section padding, 2-font hierarchy, no decorative borders'."
            )

        elif t == "shadcn_default":
            return (
                "Add a className to this shadcn/ui component using Tailwind tokens from DESIGN.md §2/§5. "
                "Example: <Button className=\"bg-primary text-primary-foreground rounded-sm h-11\">."
            )

        elif t == "mobile_slop":
            return (
                "Replace the hardcoded dimension or color with the platform's adaptive equivalent. "
                "iOS: use .frame(maxWidth: .infinity) / Color(.systemBackground). "
                "Android: use LayoutBuilder / MaterialTheme.colorScheme.background."
            )

        elif t == "threejs_slop":
            return "Apply the correct pattern from references/threejs-best-practices.md for this specific antipattern."

        elif t == "undocumented_gradient":
            return (
                "Either remove the gradient and use a solid background-color from DESIGN.md §2, "
                "or add an explicit entry in DESIGN.md §1 'Allowed effects' before keeping it."
            )

        elif t == "cliche_gradient":
            return (
                "Replace this gradient with a solid accent color from DESIGN.md §2, "
                "or justify it with a semantic role in DESIGN.md §1. "
                "Blue→purple, pink→purple, cyan→blue gradients are generic AI signals."
            )

        elif t == "html_accessibility":
            if "img without alt" in msg:
                return (
                    "Add alt attribute to every <img> in this file. "
                    "Informative images: alt='Descriptive text about what the image shows'. "
                    "Decorative images: alt='' (empty string — must be present, not omitted). "
                    "WCAG 2.1 §1.1.1 — failure to provide text alternative for non-text content."
                )
            elif "button without type" in msg:
                return (
                    "Add type attribute to every <button> in this file. "
                    "Use type='button' for standalone actions (most buttons), "
                    "type='submit' for form submission, type='reset' for form reset. "
                    "Missing type defaults to 'submit' which breaks all non-form button clicks."
                )
            elif "div with onclick" in msg:
                return (
                    "Replace <div onclick=...> with <button type='button' onclick=...>. "
                    "If a div is required for layout reasons, add: "
                    "role='button' tabIndex='0' and an onKeyDown handler for Enter and Space keys. "
                    "Divs with onclick are invisible to keyboard users and screen readers."
                )
            else:
                return "Fix the accessibility violation before delivery."

        elif t == "code_quality":
            if "console.log" in msg:
                return (
                    "Remove all console.log() calls from this file. "
                    "If debug output is needed during development only: "
                    "if (process.env.NODE_ENV === 'development') { console.log(...) } "
                    "Never ship console.log() to production."
                )
            elif "todo" in msg or "fixme" in msg or "hack" in msg:
                return (
                    "Resolve this TODO/FIXME/HACK comment before delivery. "
                    "If it cannot be resolved in scope, document the limitation in README.md "
                    "under a 'Known Limitations' section, then remove the inline comment."
                )
            elif "hardcoded api url" in msg:
                return (
                    "Move the URL to an environment variable. "
                    "Create .env.local: NEXT_PUBLIC_API_URL=https://api.example.com "
                    "Access in code: process.env.NEXT_PUBLIC_API_URL "
                    "Add .env*.local to .gitignore. Never hardcode URLs in source."
                )
            elif "mock" in msg or "fake" in msg or "sample" in msg or "demo" in msg:
                return (
                    "Remove the mock/fake data from this file. "
                    "Connect to the real data source (API, CMS, database). "
                    "If mocks are needed for tests only, move them to a /__mocks__ or /tests directory "
                    "with an explicit comment: // Test data only — not shipped to production."
                )
            else:
                return "Fix this code quality issue before delivery."

        return suggestion or "Remove or justify this element against the DESIGN.md contract."

    # -----------------------------------------------------------------------
    # Report
    # -----------------------------------------------------------------------
    def _print_report(self):
        print("\n" + "=" * 70)
        print("AI SLOP DETECTION REPORT")
        print("=" * 70)

        if not self.issues:
            print("\n[OK] NO ANTIPATTERN DETECTED!")
        else:
            print(f"\n[WARN] {len(self.issues)} issues detected:\n")
            by_type = {}
            for issue in self.issues:
                issue_type = issue["type"]
                if issue_type not in by_type:
                    by_type[issue_type] = []
                by_type[issue_type].append(issue)

            for issue_type in sorted(by_type.keys()):
                print(f"\n[{issue_type.upper()}]")
                for issue in by_type[issue_type]:
                    severity = issue.get("severity", "info")
                    tag = {"error": "[ERROR]", "warning": "[WARN]", "info": "[INFO]"}.get(severity, "-")
                    print(f"  {tag} {issue['message']}")
                    if "file" in issue:
                        print(f"     File: {issue['file']}")
                    print(f"     -> {issue['suggestion']}")

        print("\n" + "-" * 70)
        print(f"QUALITY SCORE: {self.score}/100")
        if self.score >= 80:
            print("[OK] RESULT: GOOD - Ready for delivery")
        elif self.score >= 60:
            print("[WARN] RESULT: ACCEPTABLE - Fix the warnings")
        else:
            print("[ERROR] RESULT: POOR - Revisit the design")
        print("=" * 70 + "\n")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="AI slop antipattern detector")
    parser.add_argument("--design", help="DESIGN.md file to check")
    parser.add_argument("--code", help="Code directory to audit")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output violations as structured JSON for model self-correction loop",
    )
    args = parser.parse_args()

    if not args.design and not args.code:
        print("Usage: python3 detect_ai_slop.py --design DESIGN.md --code ./client/src")
        sys.exit(1)

    detector = AISloPDetector(design_file=args.design, code_dir=args.code)
    success = detector.run(json_mode=args.json)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
