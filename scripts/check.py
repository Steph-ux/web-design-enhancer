#!/usr/bin/env python3
"""
check.py — web-design-enhancer validation orchestrator
Turns SKILL.md phases into mechanical gates.
Compatible with any AI model — no platform dependency.

Usage:
  python3 scripts/check.py --gate 0          # Phase 0 executed?
  python3 scripts/check.py --gate 1          # DESIGN.md valid? (blocks before code)
  python3 scripts/check.py --gate 2          # Structural lock committed? (blocks before code)
  python3 scripts/check.py --final           # Full validation before delivery
  python3 scripts/check.py --final --code ./src

Exit codes:
  0 = OK, continue
  1 = BLOCKED, fix before continuing
"""

import sys
import os
import re
import json
import csv
import hashlib
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# --- Terminal colors -------------------------------------------------------
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):   print(f"  {GREEN}[OK] {msg}{RESET}")
def fail(msg): print(f"  {RED}[ERROR] {msg}{RESET}")
def warn(msg): print(f"  {YELLOW}[WARN] {msg}{RESET}")
def info(msg): print(f"  {CYAN}->  {msg}{RESET}")

SCRIPTS_DIR  = Path(__file__).parent
DATA_DIR     = SCRIPTS_DIR.parent / "data"
LOG_FILE     = Path(".phase-log.json")
DESIGN_FILE  = Path("DESIGN.md")
LOCK_FILE    = Path("structural-lock.md")
BRIEF_FILE   = Path("CREATIVE-BRIEF.md")
REFERENCES_CSV = DATA_DIR / "getdesign-references.csv"

# Gates whose validity depends on the content of DESIGN.md
DESIGN_DEPENDENT_GATES = {"gate0", "gate1"}


# --- Phase log -------------------------------------------------------------

def _design_hash():
    if not DESIGN_FILE.exists():
        return None
    return hashlib.sha256(DESIGN_FILE.read_bytes()).hexdigest()

def load_log():
    if LOG_FILE.exists():
        try:
            return json.loads(LOG_FILE.read_text())
        except Exception:
            pass
    return {}

def save_log(log):
    LOG_FILE.write_text(json.dumps(log, indent=2))

def mark_passed(gate):
    log = load_log()
    entry = {"passed": True, "at": datetime.now().isoformat()}
    if gate in DESIGN_DEPENDENT_GATES:
        h = _design_hash()
        if h is not None:
            entry["design_hash"] = h
    log[gate] = entry
    save_log(log)

def gate_passed(gate):
    entry = load_log().get(gate, {})
    if not entry.get("passed", False):
        return False
    if gate in DESIGN_DEPENDENT_GATES:
        stored_hash  = entry.get("design_hash")
        current_hash = _design_hash()
        if stored_hash and current_hash and stored_hash != current_hash:
            warn(f"{gate} invalidated: DESIGN.md was modified since validation.")
            info(f"Re-run: python3 scripts/check.py --gate {gate[-1]}")
            return False
        if stored_hash is None and current_hash is not None:
            warn(f"{gate}: stale log (no hash) — re-run the gate.")
            return False
    return True


# --- Stack detection -------------------------------------------------------

def _detect_project_stack() -> str:
    """
    Auto-detect the project's tech stack.

    Priority:
      1. package.json → Next.js / React
      2. *.tsx / *.jsx files anywhere → React
      3. *.html files present → Vanilla HTML/CSS/JS
      4. Unknown
    """
    if Path("package.json").exists():
        pkg = Path("package.json").read_text(encoding="utf-8", errors="ignore").lower()
        if "\"next\"" in pkg or "next " in pkg:
            return "nextjs"
        if "\"react\"" in pkg or "react-dom" in pkg:
            return "react"

    tsx_files = list(Path(".").rglob("*.tsx")) + list(Path(".").rglob("*.jsx"))
    if tsx_files:
        return "react"

    html_files = list(Path(".").rglob("*.html"))
    if html_files:
        return "vanilla-html"

    return "unknown"


def _validate_stack_consistency(stack: str) -> list:
    """
    Validate that the project implementation matches the detected stack rules.

    React/Next.js → shadcn/ui must be present (package.json or TSX imports)
    Vanilla HTML  → CSS custom properties (--var) must be used in .css files
    """
    errors = []

    if stack in ("react", "nextjs"):
        # shadcn/ui must be present
        has_shadcn = False
        if Path("package.json").exists():
            has_shadcn = "shadcn" in Path("package.json").read_text(encoding="utf-8", errors="ignore").lower()
        if not has_shadcn:
            # Check for @/components/ui imports in TSX
            for f in list(Path(".").rglob("*.tsx"))[:20]:
                try:
                    if "@/components/ui" in f.read_text(encoding="utf-8", errors="ignore"):
                        has_shadcn = True
                        break
                except Exception:
                    pass
        if not has_shadcn:
            warn("React/Next.js project — shadcn/ui not detected.")
            info("Phase 2 requires: import from '@/components/ui' or 'shadcn' in package.json")
            info("If you're using another component library, add a justification in structural-lock.md")
            # Warning only — not a blocking error (another lib may be justified)

    elif stack == "vanilla-html":
        # CSS custom properties must be used
        css_files = list(Path(".").rglob("*.css"))
        has_css_vars = False
        for f in css_files[:10]:
            try:
                if re.search(r"--[a-zA-Z][\w-]+\s*:", f.read_text(encoding="utf-8", errors="ignore")):
                    has_css_vars = True
                    break
            except Exception:
                pass
        if not has_css_vars:
            errors.append(
                "Vanilla HTML project but no CSS custom properties (--var) found in .css files. "
                "Phase 2 requires CSS custom properties from DESIGN.md tokens (--primary, --background, etc.)"
            )
        else:
            ok("CSS custom properties detected in .css files ✓")

        # Semantic HTML check — at least one semantic tag
        html_files = list(Path(".").rglob("*.html"))
        has_semantic = False
        semantic_tags = ["<main", "<nav", "<header", "<footer", "<article", "<section", "<aside"]
        for f in html_files[:5]:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                if any(tag in content for tag in semantic_tags):
                    has_semantic = True
                    break
            except Exception:
                pass
        if html_files and not has_semantic:
            warn("Vanilla HTML project but no semantic HTML5 elements detected (main/nav/header/footer...).")
            info("Phase 2 for vanilla HTML: use semantic elements instead of generic <div>.")

    return errors


# --- Reference diversity (anti-monoculture) --------------------------------

def _normalize_brand(name: str) -> str:
    """Normalize a brand id/filename fragment for matching.

    getdesign uses ids like 'linear.app' / 'mistral.ai', but writes files as
    'getdesign-linear.md'. Lowercase, drop a leading 'getdesign-'/'brand-'
    prefix, strip the '.md' suffix and any TLD-like '.app'/'.ai' tail so both
    sides compare equal.
    """
    n = name.strip().lower()
    n = re.sub(r"\.md$", "", n)
    n = re.sub(r"^(getdesign|brand)-", "", n)
    n = re.sub(r"\.(app|ai|com|io|dev)$", "", n)
    return n


def _load_reference_segments() -> dict:
    """brand -> segment ('saas' | 'non-saas') from the editable CSV.

    Returns an empty dict if the CSV is absent or unreadable — the check then
    degrades to a no-op rather than blocking on infrastructure problems.
    """
    segments = {}
    if not REFERENCES_CSV.exists():
        return segments
    try:
        with open(REFERENCES_CSV, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                brand = _normalize_brand(row.get("brand", ""))
                seg = (row.get("segment", "") or "").strip().lower()
                if brand and seg:
                    segments[brand] = seg
    except Exception:
        pass
    return segments


def _check_reference_diversity(getdesign_files):
    """Anti-monoculture nudge for Phase 0 references.

    Classifies each getdesign reference present at project root as saas /
    non-saas / unknown via data/getdesign-references.csv. Pure-SaaS anchoring
    is the root cause of "every AI site looks like a San-Francisco SaaS", so we
    surface it. This validates *provenance* (where the reference comes from),
    never the quality of the result — the only legitimate use of a gate.

    WARN, not BLOCK: a fintech legitimately anchoring on Stripe alone should
    not be hard-blocked. Returns a list of warning strings (never errors).
    """
    segments = _load_reference_segments()
    if not segments:
        return []

    seen = {}
    for f in getdesign_files:
        brand = _normalize_brand(f.name)
        seen[brand] = segments.get(brand, "unknown")

    if not seen:
        return []

    non_saas = [b for b, s in seen.items() if s == "non-saas"]
    saas     = [b for b, s in seen.items() if s == "saas"]
    unknown  = [b for b, s in seen.items() if s == "unknown"]

    warnings = []
    if non_saas:
        ok(f"Reference diversity: non-SaaS anchor present ({', '.join(sorted(non_saas))})")
    elif saas and not unknown:
        warn("Reference monoculture: every Phase 0 reference is SaaS/tech "
             f"({', '.join(sorted(saas))}).")
        info("Add at least one non-SaaS anchor so the output does not collapse "
             "into the generic San-Francisco SaaS look. Verified non-SaaS brands:")
        info("  editorial: wired, theverge | auto/luxe: ferrari, bmw, tesla")
        info("  retail: apple, nike, starbucks | retro: dell-1996, nintendo-2001, playstation")
        info("  -> npx getdesign@latest add <brand>  (full editable list: data/getdesign-references.csv)")
        warnings.append("reference monoculture — all Phase 0 references are SaaS/tech")
    elif unknown:
        info(f"Reference(s) not in the diversity allow-list: {', '.join(sorted(unknown))}. "
             "If non-SaaS, add a row to data/getdesign-references.csv.")
    return warnings


# --- Phase -1 — Creative Brief (point of view) -----------------------------

_BRIEF_VAGUE_TERMS = [
    "professional", "modern", "clean", "sleek", "elegant", "premium",
    "minimalist", "beautiful", "nice", "simple", "user-friendly", "intuitive",
]


def _section_body(content: str, header: str) -> str:
    """Return the text between '## header' and the next '## ' header (exclusive),
    with HTML comment guidance stripped so it is not mistaken for real content."""
    out, capturing = [], False
    for ln in content.splitlines():
        stripped = ln.strip()
        if stripped.lower() == f"## {header}".lower():
            capturing = True
            continue
        if capturing and stripped.startswith("## "):
            break
        if capturing:
            out.append(ln)
    body = "\n".join(out)
    body = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
    return body.strip()


def _brief_field_filled(body: str) -> bool:
    """Filled if real text remains after removing placeholders and empty checkboxes."""
    t = body.replace("___", "").strip()
    t = re.sub(r"^[-*]\s*\[\s*\].*$", "", t, flags=re.MULTILINE).strip()
    return len(t) >= 8


def check_creative_brief():
    """Phase -1 — the Creative Brief enforces a point of view BEFORE Phase 0.

    A getdesign reference says what a design *looks like*; it never says what it
    must make someone *feel*, or what makes it un-generic. A model cannot invent
    a point of view, so the user must impose one. This gate validates the
    *presence and structure* of that point of view — never its quality (a gate
    cannot tell an inspired brief from filler). It BLOCKS on missing/unfilled
    fields and WARNS on vague-but-present content.

    Returns (errors, warnings).
    """
    errors, warnings = [], []

    if not BRIEF_FILE.exists():
        fail(f"{BRIEF_FILE} missing — Phase -1 (point of view) must precede Phase 0")
        info("Create it from templates/creative-brief-template.md and fill all four fields:")
        info("  Emotional Intent | The One Unexpected Thing | Hero Dimension | The Broken Rule")
        errors.append("CREATIVE-BRIEF.md missing")
        return errors, warnings

    content = BRIEF_FILE.read_text(encoding="utf-8")

    # 1. Emotional Intent — present, filled, not buzzword-only.
    emo = _section_body(content, "Emotional Intent")
    if not _brief_field_filled(emo):
        fail("CREATIVE-BRIEF.md: 'Emotional Intent' is empty or unfilled (___)")
        errors.append("Creative Brief: Emotional Intent unfilled")
    else:
        low = emo.lower()
        hits = [w for w in _BRIEF_VAGUE_TERMS if re.search(rf"\b{w}\b", low)]
        if hits and len(emo.split()) <= 12:
            warn(f"CREATIVE-BRIEF.md: 'Emotional Intent' leans on vague terms ({', '.join(hits)}).")
            info("These are the generic defaults the skill exists to defeat. Make it concrete: "
                 "'like walking into a Zurich architect's studio', not 'professional'.")
            warnings.append("Creative Brief: Emotional Intent is vague")

    # 2. The One Unexpected Thing — present and filled.
    unexpected = _section_body(content, "The One Unexpected Thing")
    if not _brief_field_filled(unexpected):
        fail("CREATIVE-BRIEF.md: 'The One Unexpected Thing' is empty or unfilled")
        errors.append("Creative Brief: The One Unexpected Thing unfilled")

    # 3. Hero Dimension — exactly one box ticked.
    hero = _section_body(content, "Hero Dimension")
    ticked = len(re.findall(r"[-*]\s*\[[xX]\]", hero))
    if ticked == 0:
        fail("CREATIVE-BRIEF.md: 'Hero Dimension' has no box ticked — pick exactly ONE")
        info("Tick one: Typography / Negative space / Colour / Motion / Illustration")
        errors.append("Creative Brief: Hero Dimension not selected")
    elif ticked > 1:
        fail(f"CREATIVE-BRIEF.md: 'Hero Dimension' has {ticked} boxes ticked — pick exactly ONE")
        info("Excess comes from going too far in ONE direction, not balancing several.")
        errors.append("Creative Brief: more than one Hero Dimension selected")

    # 4. The Broken Rule — present, filled, and has a 'because' (rule + rationale).
    broken = _section_body(content, "The Broken Rule")
    if not _brief_field_filled(broken):
        fail("CREATIVE-BRIEF.md: 'The Broken Rule' is empty or unfilled")
        errors.append("Creative Brief: The Broken Rule unfilled")
    elif "because" not in broken.lower():
        fail("CREATIVE-BRIEF.md: 'The Broken Rule' is missing its 'because' — "
             "a broken rule without a reason is just a mistake")
        info("Format: 'We ignore <rule> because <why breaking it IS the design>'.")
        errors.append("Creative Brief: The Broken Rule has no rationale")

    # 5. Design Dials — three numeric dials (taste-skill VARIANCE/MOTION/DENSITY),
    #    reasoned from the brief, not silently left blank. "Waouh" comes from
    #    pushing ONE dial far; a brief with no dials cannot commit to that.
    dials_body = _section_body(content, "Design Dials")
    found_dials = {}
    for dial in ("VARIANCE", "MOTION", "DENSITY"):
        m = re.search(rf"{dial}\s*:\s*(\d{{1,2}})\b", dials_body, re.IGNORECASE)
        if m and 1 <= int(m.group(1)) <= 10:
            found_dials[dial] = int(m.group(1))
    missing_dials = [d for d in ("VARIANCE", "MOTION", "DENSITY") if d not in found_dials]
    if missing_dials:
        fail(f"CREATIVE-BRIEF.md: 'Design Dials' missing valid 1-10 value(s) for: {', '.join(missing_dials)}")
        info("Set all three, reasoned from the Design Read: VARIANCE / MOTION / DENSITY (each 1-10).")
        errors.append("Creative Brief: Design Dials incomplete")
    elif max(found_dials.values()) - min(found_dials.values()) <= 1:
        warn("CREATIVE-BRIEF.md: all three dials are nearly equal — that is the averaged, "
             "templated look. Push ONE dial far so a single dimension can shout.")
        warnings.append("Creative Brief: dials too balanced for a memorable result")

    # 6. The Cross-Domain Steal — a reference from OUTSIDE software. A tech/SaaS
    #    reference here defeats the mechanism (it is how every AI page converges
    #    on the same SF-SaaS look). Structure BLOCKS; a tech reference WARNS.
    steal = _section_body(content, "The Cross-Domain Steal")
    if not _brief_field_filled(steal):
        fail("CREATIVE-BRIEF.md: 'The Cross-Domain Steal' is empty or unfilled")
        info("Name a NON-software reference (print, industrial design, cinema, signage, "
             "architecture, fashion) and the one move you steal from it.")
        errors.append("Creative Brief: The Cross-Domain Steal unfilled")
    else:
        _TECH_REF = [
            "website", "web app", "webapp", "saas", "dashboard", "landing page",
            "app store", "mobile app", "ui kit", "design system", "framer",
            "figma", "dribbble", "behance", "linear", "vercel", "stripe",
            "notion", "github", "tailwind", "shadcn", "bootstrap", "material ui",
        ]
        low = steal.lower()
        tech_hits = [t for t in _TECH_REF if t in low]
        if tech_hits:
            warn(f"CREATIVE-BRIEF.md: 'The Cross-Domain Steal' references software/web ({', '.join(tech_hits)}). "
                 "That defeats the point — steal from OUTSIDE the category (print, industrial design, "
                 "cinema, signage, architecture) or the result converges on the generic SaaS look.")
            warnings.append("Creative Brief: Cross-Domain Steal is still a tech reference")

    if not errors:
        ok("Phase -1 Creative Brief: all six fields present and filled")
    return errors, warnings


# --- Gate 0 — Phase 0 execution proof --------------------------------------

def check_gate0():
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  GATE 0 — Phase 0 executed?{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")

    errors = []

    # Phase -1 — Creative Brief (point of view) must precede Phase 0.
    brief_errors, _brief_warnings = check_creative_brief()
    errors.extend(brief_errors)

    # 1. design-system-output.md
    ds_files = list(Path(".").glob("design-system-output*.md"))
    if ds_files:
        ok(f"design-system-output.md found ({ds_files[0].name})")
    else:
        fail("design-system-output.md missing")
        info("Run: python3 scripts/search.py \"<description>\" --design-system -p \"<Project>\" --save")
        errors.append("search.py not executed")

    # 2. getdesign reference DESIGN.md
    getdesign_files = list(Path(".").glob("getdesign-*.md")) + list(Path(".").glob("brand-*.md"))
    if getdesign_files:
        ok(f"getdesign.md reference found ({getdesign_files[0].name})")
        _check_reference_diversity(getdesign_files)
    else:
        fail("No getdesign.md reference file found")
        info("Run: npx getdesign@latest add <brand>")
        info("Brand examples: vercel / stripe / linear.app (SaaS) — but add at least one")
        info("non-SaaS anchor: wired / ferrari / nike / nintendo-2001 (anti-monoculture)")
        errors.append("getdesign.md not executed")

    # 3. DESIGN.md present
    if DESIGN_FILE.exists():
        ok("DESIGN.md present")
    else:
        fail("DESIGN.md missing — create from templates/design-md-template.md")
        errors.append("DESIGN.md missing")

    # 4. Phase 0 section in DESIGN.md
    if DESIGN_FILE.exists():
        content = DESIGN_FILE.read_text(encoding="utf-8")
        if "## 0. Sources Phase 0" in content:
            ok("Section '## 0. Sources Phase 0' present in DESIGN.md")
            if "[Ex:" in content or "<brand>" in content or "<description>" in content:
                fail("DESIGN.md still contains unfilled placeholders")
                info("Replace all [Ex: ...] and <placeholder> with real values")
                errors.append("Unfilled placeholders in DESIGN.md")
        else:
            fail("Section '## 0. Sources Phase 0' missing from DESIGN.md")
            info("Use templates/design-md-template.md as a base")
            errors.append("Sources section missing from DESIGN.md")

    # 5. Stack auto-detection
    stack = _detect_project_stack()
    if stack != "unknown":
        ok(f"Stack auto-detected: {stack}")
        log = load_log()
        log["detected_stack"] = stack
        save_log(log)
    else:
        warn("Stack not auto-detected.")
        info("Add package.json (React/Next.js) or .html files (Vanilla) so the stack can be identified.")

    _print_result(errors, "GATE 0")
    if not errors:
        mark_passed("gate0")
    return len(errors) == 0


# --- Gate 1 — DESIGN.md validation -----------------------------------------

def check_gate1():
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  GATE 1 — DESIGN.md valid? (before any code){RESET}")
    print(f"{BOLD}{'='*60}{RESET}")

    if not gate_passed("gate0"):
        fail("Gate 0 not validated — run first: python3 scripts/check.py --gate 0")
        _print_result(["Gate 0 not passed"], "GATE 1")
        return False

    if not DESIGN_FILE.exists():
        fail("DESIGN.md missing")
        _print_result(["DESIGN.md missing"], "GATE 1")
        return False

    ok("Gate 0 validated")

    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "validate_design.py"), "DESIGN.md"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    print(result.stdout)
    if result.returncode == 0:
        mark_passed("gate1")
        return True
    return False


# --- Gate 2 — Structural Decision Lock -------------------------------------

def check_gate2():
    """
    Gate 2 — Phase 2a: Structural Decision Lock.

    Validates that the agent committed to 3 explicit structural decisions
    in structural-lock.md BEFORE writing any code.

    structural-lock.md format:
      # Structural Lock
      1. Card structure: surface-card bg, 8px radius, 24px padding (§6)
      2. Layout pattern: split-pane, left sidebar 280px, dense header (§1)
      3. Primary button: filled #22c55e, 4px radius, 44px height (§6)
    """
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  GATE 2 — Structural Decision Lock committed?{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")

    if not gate_passed("gate1"):
        fail("Gate 1 not validated — run first: python3 scripts/check.py --gate 1")
        _print_result(["Gate 1 not passed"], "GATE 2")
        return False

    ok("Gate 1 validated")
    errors = []

    # ── 1. structural-lock.md must exist ────────────────────────────────
    if not LOCK_FILE.exists():
        fail(f"{LOCK_FILE} not found")
        info("Create this file with 3 structural decisions before writing any code.")
        info("")
        info("  Required format:")
        info("  # Structural Lock")
        info("  1. Card structure: [exact description] (§6)")
        info("  2. Layout pattern: [exact description] (§1 or §6)")
        info("  3. Primary button/CTA: [exact description] (§6)")
        info("")
        info("  For vanilla HTML targets: quote Card structure, Section pattern, Button shape.")
        info("  For React/Next.js targets: same — plus confirm shadcn/ui primitive used.")
        errors.append("structural-lock.md missing")
        _print_result(errors, "GATE 2")
        return False

    ok(f"{LOCK_FILE} found")
    lock_content = LOCK_FILE.read_text(encoding="utf-8")

    # ── 2. Minimum 3 numbered decisions ─────────────────────────────────
    numbered = re.findall(r"^\s*\d+\.", lock_content, re.MULTILINE)
    if len(numbered) < 3:
        fail(f"Only {len(numbered)} structural decision(s) — minimum 3 required")
        info("Each decision must start with a number: '1. Card structure: ...'")
        errors.append(f"Insufficient structural decisions ({len(numbered)}/3)")
    else:
        ok(f"{len(numbered)} structural decision(s) committed ✓")

    # ── 3. Each decision must reference a DESIGN.md section ─────────────
    section_refs = re.findall(r"§\d+", lock_content)
    if len(section_refs) < 3:
        warn(
            f"Only {len(section_refs)} DESIGN.md section reference(s) found — "
            f"each decision should cite §N (e.g. §6, §1, §7)"
        )
        # Warning only — intent is clear even without §-refs in every sentence
    else:
        ok(f"{len(section_refs)} DESIGN.md section reference(s) found ✓")

    # ── 4. No unfilled placeholders ──────────────────────────────────────
    placeholders = re.findall(r"\[(?:[A-Z]\s*\||\s*Ex:)", lock_content, re.IGNORECASE)
    if placeholders:
        fail(f"Unfilled placeholder(s) in {LOCK_FILE}: {placeholders[:3]}")
        info("Replace all '[A | B | C]' and '[Ex: ...]' with committed values")
        errors.append("Unfilled placeholders in structural-lock.md")
    else:
        ok("No unfilled placeholders ✓")

    # ── 5. Stack-specific consistency check ──────────────────────────────
    stack = load_log().get("detected_stack", _detect_project_stack())
    if stack != "unknown":
        info(f"Stack in use: {stack}")
        stack_errors = _validate_stack_consistency(stack)
        errors.extend(stack_errors)
    else:
        warn("Stack unknown — run check.py --gate 0 first to enable stack validation")

    _print_result(errors, "GATE 2")
    if not errors:
        mark_passed("gate2")
    return len(errors) == 0


# --- Final Gate — Full validation before delivery --------------------------

def check_final(code_path=None, verbose=False, url=None, audit_output="./audit-results", verdict=None):
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  FINAL GATE — Validation before delivery{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")

    # Gate 1 must have passed
    if not gate_passed("gate1"):
        fail("Gate 1 not validated — run first: python3 scripts/check.py --gate 1")
        _print_result(["Gate 1 not passed"], "FINAL GATE")
        return False
    ok("Gate 1 validated")

    # Gate 2 must have passed
    if not gate_passed("gate2"):
        fail("Gate 2 not validated — run first: python3 scripts/check.py --gate 2")
        info("Gate 2 ensures the structural lock was committed before any code was written.")
        _print_result(["Gate 2 not passed"], "FINAL GATE")
        return False
    ok("Gate 2 validated")

    errors = []

    # 1. detect_ai_slop.py
    print(f"\n{CYAN}[1/8] Detecting AI antipatterns (HTML + CSS + JSX + code quality)...{RESET}")
    slop_args = [sys.executable, str(SCRIPTS_DIR / "detect_ai_slop.py"), "--design", "DESIGN.md"]
    if code_path:
        slop_args += ["--code", code_path]
    r = subprocess.run(slop_args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(r.stdout)
    if r.returncode != 0:
        errors.append("detect_ai_slop.py — antipatterns detected")
        if verbose:
            # Re-run in JSON mode to get machine-readable fix instructions
            print(f"\n{YELLOW}  Fix instructions (JSON mode):{RESET}")
            json_args = slop_args + ["--json"]
            rj = subprocess.run(json_args, capture_output=True, text=True, encoding="utf-8", errors="replace")
            try:
                data = json.loads(rj.stdout)
                for v in data.get("violations", [])[:10]:  # cap at 10
                    print(f"\n  {RED}[{v.get('type','?')}]{RESET} {v.get('message','')}")
                    print(f"  {CYAN}Fix:{RESET} {v.get('fix_instruction','see message')}")
            except Exception:
                print(rj.stdout)

    # 1b. audit_declared_antipatterns.py — enforce the project's OWN "Avoid" list
    print(f"\n{CYAN}[1b/8] Enforcing project-declared antipatterns (DESIGN.md / design-system 'Avoid')...{RESET}")
    decl_args = [sys.executable, str(SCRIPTS_DIR / "audit_declared_antipatterns.py"), "--design", "DESIGN.md"]
    if code_path:
        decl_args += ["--code", code_path]
    rd = subprocess.run(decl_args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(rd.stdout)
    if rd.returncode == 1:
        errors.append("audit_declared_antipatterns.py — the delivery contains an antipattern the project declared it would avoid")

    # 2. audit_spacing.py
    print(f"\n{CYAN}[2/8] 8px grid audit...{RESET}")
    spacing_path = code_path or "."
    r = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "audit_spacing.py"), "--path", spacing_path],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    print(r.stdout)
    if r.returncode != 0:
        errors.append("audit_spacing.py — 8px grid violations")

    # 3. validate_design.py (final pass)
    print(f"\n{CYAN}[3/8] Final DESIGN.md validation...{RESET}")
    vd_args = [sys.executable, str(SCRIPTS_DIR / "validate_design.py"), "DESIGN.md"]
    if code_path:
        vd_args += ["--code", code_path]  # enables §11 signature-gesture verification
    r = subprocess.run(
        vd_args,
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    print(r.stdout)
    if r.returncode != 0:
        errors.append("validate_design.py — DESIGN.md contract not respected")

    # 4. diff_design_vs_code.py
    print(f"\n{CYAN}[4/8] DESIGN.md <-> code diff...{RESET}")
    if code_path:
        r = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "diff_design_vs_code.py"), "DESIGN.md", "--code", code_path],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        print(r.stdout)
        if r.returncode != 0:
            errors.append("diff_design_vs_code.py — code diverges from DESIGN.md")
    else:
        warn("diff_design_vs_code.py skipped (no --code provided)")

    # 5. audit_accessibility.py
    print(f"\n{CYAN}[5/8] WCAG 2.1 AA accessibility audit...{RESET}")
    a11y_script = SCRIPTS_DIR / "audit_accessibility.py"
    if a11y_script.exists():
        a11y_args = [sys.executable, str(a11y_script)]
        if code_path:
            a11y_args += ["--path", code_path]
            if verbose:
                a11y_args += ["--json"]
        else:
            a11y_args += ["--path", "."]
        r = subprocess.run(a11y_args, capture_output=True, text=True, encoding="utf-8", errors="replace")
        print(r.stdout)
        if r.returncode != 0:
            errors.append("audit_accessibility.py — WCAG 2.1 violations found")
    else:
        warn("audit_accessibility.py not found — skipping accessibility check")

    # 6. audit_style_uniqueness.py
    print(f"\n{CYAN}[6/8] Style uniqueness audit (Generic AI Template detector)...{RESET}")
    uniqueness_script = SCRIPTS_DIR / "audit_style_uniqueness.py"
    if uniqueness_script.exists():
        uniq_args = [sys.executable, str(uniqueness_script), "--path", code_path or "."]
        if verbose:
            uniq_args += ["--json"]
        r = subprocess.run(uniq_args, capture_output=True, text=True, encoding="utf-8", errors="replace")
        print(r.stdout)
        if r.returncode == 2:
            errors.append(
                "audit_style_uniqueness.py — BLOCKED: design score > 65/100 (Generic AI Template detected). "
                "Differentiate the design before delivery — see references/design-archetypes.md."
            )
        elif r.returncode == 1:
            warn("audit_style_uniqueness.py — WARNING: template score elevated. Fix flagged signals.")
    else:
        warn("audit_style_uniqueness.py not found — skipping style uniqueness check")

    # 7. audit_beauty.py — positive craft floor (blocks soulless-but-clean designs)
    print(f"\n{CYAN}[7/8] Beauty audit (craft & finish — blocks clean-but-soulless)...{RESET}")
    beauty_script = SCRIPTS_DIR / "audit_beauty.py"
    if beauty_script.exists():
        beauty_args = [sys.executable, str(beauty_script), "--path", code_path or "."]
        if verbose:
            beauty_args += ["--json"]
        r = subprocess.run(beauty_args, capture_output=True, text=True, encoding="utf-8", errors="replace")
        print(r.stdout)
        if r.returncode == 2:
            errors.append(
                "audit_beauty.py — BLOCKED: beauty score below floor (50/100). "
                "Design is technically clean but soulless. Raise the craft before delivery — "
                "see references/beauty-gestures.md for signature gestures per archetype."
            )
        elif r.returncode == 1:
            warn("audit_beauty.py — NEEDS POLISH: beauty score below pass (70/100). Address flagged weaknesses.")
    else:
        warn("audit_beauty.py not found — skipping beauty check")

    # 8. Visual + aesthetic verification (Phase 4) — rendered DOM + vision judgment (mandatory)
    print(f"\n{CYAN}[8/8] Visual + aesthetic verification (rendered DOM + vision)...{RESET}")
    v_errors, v_warnings, v_infos = evaluate_visual_gate(
        audit_output=audit_output, code_path=code_path, verdict=verdict, url=url
    )
    for _m in v_infos:
        print(f"  {_m}")
    for _w in v_warnings:
        warn(_w)
    for _e in v_errors:
        fail(_e)
    errors.extend(v_errors)

    _print_result(errors, "FINAL GATE")
    if not errors:
        mark_passed("final")
        _print_delivery_ok()
    return len(errors) == 0


def _visual_audit_stale(report_file, code_path, audit_dir):
    """Return the path of a source file newer than the visual audit report, or None."""
    try:
        report_mtime = report_file.stat().st_mtime
    except OSError:
        return None
    root = Path(code_path) if code_path else Path(".")
    try:
        audit_dir_resolved = Path(audit_dir).resolve()
    except OSError:
        audit_dir_resolved = None
    exts = {".html", ".htm", ".css", ".scss", ".sass", ".less",
            ".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte", ".astro"}
    newest = None
    newest_file = None
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in exts:
            continue
        try:
            rp = p.resolve()
        except OSError:
            continue
        if audit_dir_resolved is not None and (rp == audit_dir_resolved or audit_dir_resolved in rp.parents):
            continue
        try:
            m = p.stat().st_mtime
        except OSError:
            continue
        if newest is None or m > newest:
            newest = m
            newest_file = p
    if newest is not None and newest > report_mtime + 1:
        return str(newest_file)
    return None


def evaluate_visual_gate(audit_output="./audit-results", code_path=None, verdict=None, url=None):
    """Phase 4 enforcement: require a fresh visual audit report + a passing aesthetic verdict.

    Returns (errors, warnings, infos). Pure except for running aesthetic_review --verdict
    when a verdict file is present. The rendered visual + vision pass is mandatory for
    delivery — it cannot be bypassed by running only the static gates.
    """
    errors, warnings, infos = [], [], []
    audit_dir = Path(audit_output)
    report_file = audit_dir / "audit_report.json"
    url_hint = url or "http://localhost:3000"

    if not report_file.exists():
        errors.append(
            "Phase 4 visual audit missing — the rendered pass is mandatory before delivery. "
            f"Render the site on a live server, then run: python3 scripts/visual_audit.py "
            f"--url {url_hint} --output {audit_dir}"
        )
    else:
        report = None
        try:
            report = json.loads(report_file.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append(f"Visual audit report unreadable ({report_file}): {e}")
        if report is not None:
            stale = _visual_audit_stale(report_file, code_path, audit_dir)
            if stale:
                errors.append(
                    f"Visual audit is stale — '{stale}' changed after the last render. "
                    f"Re-render: python3 scripts/visual_audit.py --url {url_hint} --output {audit_dir}"
                )
            rendered_slop = (report.get("ai_slop_detected") or []) + (report.get("a_group_slop") or [])
            if rendered_slop:
                errors.append(
                    f"Visual audit found {len(rendered_slop)} AI-slop element(s) in the RENDERED DOM "
                    "(regex on static files cannot catch these). Fix and re-render."
                )
            n_spacing = len(report.get("spacing_errors") or [])
            if n_spacing:
                warnings.append(
                    f"visual_audit — {n_spacing} rendered spacing value(s) off the 8px grid (review)."
                )
            if not rendered_slop and not stale:
                infos.append(
                    f"Rendered DOM clean ({len(report.get('screenshots') or {})} breakpoints captured)."
                )

    verdict_file = Path(verdict) if verdict else (audit_dir / "aesthetic-verdict.json")
    if not verdict_file.exists():
        errors.append(
            "Aesthetic vision review missing — the rendered pass is mandatory before delivery. Run: "
            f"python3 scripts/aesthetic_review.py --screenshots {audit_dir} --archetype \"<your §archetype>\", "
            "open the screenshots with your own vision, write the verdict JSON it describes to "
            f"'{verdict_file}', then re-run check.py --final."
        )
    else:
        # 'Waouh' bar: delivery requires a genuinely strong design, not merely a
        # non-ugly one. Pass mark raised to 80 (the "strong, clearly human-crafted"
        # calibration anchor) instead of the lenient 75.
        r = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "aesthetic_review.py"),
             "--verdict", str(verdict_file), "--threshold", "62", "80"],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        if r.stdout:
            infos.append(r.stdout.rstrip())
        if r.returncode == 2:
            errors.append(
                "aesthetic_review.py — BLOCKED: rendered design scored below the human-craft floor. "
                "It does not yet read as human-designed. Raise the craft and re-render — "
                "see references/beauty-gestures.md."
            )
        elif r.returncode == 1:
            warnings.append(
                "aesthetic_review.py — NEEDS POLISH: rendered design acceptable but below the pass mark. "
                "Address the top_fixes in the verdict."
            )

        # Provenance + signature enforcement. The validity hole that let a 94/100
        # self-grade ship terminal cosplay: the SAME model produced AND judged the
        # design. A self/unknown-reviewed or idea-less verdict can NEVER authorize
        # delivery — it must be independently or human-judged AND name one owned idea.
        try:
            v = json.loads(verdict_file.read_text(encoding="utf-8"))
        except Exception:
            v = None
        if isinstance(v, dict):
            reviewer = str(v.get("reviewer", "")).strip().lower()
            if reviewer in {"", "self", "agent"}:
                errors.append(
                    f"aesthetic_review.py — PROVENANCE: the design was judged by the same model "
                    f"that produced it (reviewer='{reviewer or 'unset'}'). Self-review is "
                    f"structurally inflated and CANNOT authorize delivery. Get an INDEPENDENT "
                    f"verdict (aesthetic_review.py --screenshots {audit_dir} --mode api --provider "
                    f"<a different model>) or a HUMAN sign-off (--reviewer human)."
                )
            idea = v.get("memorable_idea")
            has_idea = (isinstance(idea, str) and len(idea.strip()) >= 8
                        and idea.strip().lower() not in {"null", "none", "n/a", "-"})
            if not has_idea:
                errors.append(
                    "aesthetic_review.py — NO SIGNATURE: the verdict names no memorable, owned "
                    "design idea (memorable_idea is empty). 'Clean and professional' is the floor, "
                    "not a pass. Commit to one fearless, nameable move — see references/beauty-gestures.md."
                )
            if str(v.get("reads_as", "")).strip().lower() == "ai":
                errors.append(
                    "aesthetic_review.py — READS AS AI: the verdict itself says the page reads as AI "
                    "output. Raise the craft until it reads as deliberate, human design."
                )
    return errors, warnings, infos


# --- Helpers ---------------------------------------------------------------

def _print_result(errors, gate_name):
    print(f"\n{BOLD}{'-'*60}{RESET}")
    if errors:
        print(f"{RED}{BOLD}  [ERROR] {gate_name}: BLOCKED — {len(errors)} issue(s){RESET}")
        for e in errors:
            print(f"     - {e}")
        print(f"\n{YELLOW}  -> Fix the errors and re-run this command.{RESET}")
        print(f"{YELLOW}  -> Do not move to the next step until this gate is green.{RESET}")
    else:
        print(f"{GREEN}{BOLD}  [OK] {gate_name}: VALIDATED — continue{RESET}")
    print(f"{BOLD}{'-'*60}{RESET}\n")

def _print_delivery_ok():
    lines = [
        "[OK]  DELIVERY AUTHORIZED",
        "",
        "All 8 gates green — including the rendered",
        "visual + vision pass.",
        "Zero AI slop. Unique. Reads as human-crafted.",
    ]
    width = max(len(s) for s in lines) + 4
    border = "+" + "-" * width + "+"
    print(f"\n{GREEN}{BOLD}{border}")
    for s in lines:
        print("|  " + s.ljust(width - 2) + "|")
    print(f"{border}{RESET}\n")


# --- Entry point -----------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="web-design-enhancer — validation orchestrator")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--gate", type=int, choices=[0, 1, 2],
                       help="Check a specific gate (0=Phase0, 1=DESIGN.md, 2=StructuralLock)")
    group.add_argument("--final", action="store_true", help="Full validation before delivery")
    parser.add_argument("--code",    type=str, default=None,  help="Source code path (for --final)")
    parser.add_argument("--verbose", action="store_true",
                        help="When --final fails, print fix_instructions from detect_ai_slop --json")
    parser.add_argument("--url", type=str, default=None,
                        help="Live dev-server URL for the Phase 4 visual audit (used in fix hints)")
    parser.add_argument("--audit-output", type=str, default="./audit-results",
                        help="Directory holding visual_audit report + screenshots + aesthetic verdict")
    parser.add_argument("--verdict", type=str, default=None,
                        help="Path to the aesthetic verdict JSON (default: <audit-output>/aesthetic-verdict.json)")
    args = parser.parse_args()

    if args.gate == 0:
        success = check_gate0()
    elif args.gate == 1:
        success = check_gate1()
    elif args.gate == 2:
        success = check_gate2()
    elif args.final:
        success = check_final(args.code, verbose=args.verbose, url=args.url,
                              audit_output=args.audit_output, verdict=args.verdict)

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
