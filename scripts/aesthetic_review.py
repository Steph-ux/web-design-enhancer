#!/usr/bin/env python3
"""
aesthetic_review.py — aesthetic judgment of rendered screenshots.

The Beauty Score (audit_beauty.py) measures craft markers from source code.
But "is this magnificent at a glance?" is a question only an eye can answer.
This script turns the rendered screenshots (from visual_audit.py) into a
scored, structured verdict — the closest thing to a human designer looking
at the page.

It is the Phase 4 counterpart to visual_audit.py: that one catches mechanical
slop in the DOM; this one judges whether the result actually looks designed
by a human.

Two modes:
  agent (DEFAULT) — the model executing this skill IS vision-capable, so it
      judges with its OWN vision. No API key. The script emits the screenshots
      + rubric + verdict schema; the agent looks, writes a verdict JSON, then
      re-runs with --verdict to score it and get the gate exit code.
  api — call an external vision model (OpenAI-compatible or Anthropic) for
      fully-unsupervised pipelines. Reads OPENAI_API_KEY / ANTHROPIC_API_KEY
      from the environment on the machine running the skill.

Usage:
    # after visual_audit.py has produced ./audit-results/*.png
    python3 scripts/aesthetic_review.py --screenshots ./audit-results --archetype "§3 Luxury"
    #   -> prints screenshots + rubric; the agent looks, writes verdict.json, then:
    python3 scripts/aesthetic_review.py --verdict verdict.json
    # unsupervised, external model:
    python3 scripts/aesthetic_review.py --screenshots ./audit-results --mode api --provider anthropic

Exit codes:
  0 — overall_score ≥ pass threshold (looks designed) / agent manifest emitted
  1 — floor ≤ score < pass (acceptable, polish)
  2 — score < floor (BLOCKED — does not look human-designed)
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ── ANSI helpers ─────────────────────────────────────────────────────────────

def _ansi(code: str) -> str:
    return f"\033[{code}m" if sys.stdout.isatty() else ""

RESET, BOLD = _ansi("0"), _ansi("1")
RED, YELLOW, GREEN, CYAN, DIM = _ansi("31"), _ansi("33"), _ansi("32"), _ansi("36"), _ansi("2")


# ── The rubric ───────────────────────────────────────────────────────────────
# Seven dimensions a human designer judges in the first seconds. Each maps loosely
# to the code-level Beauty Score (D1-D5) but adds what only the eye catches.

RUBRIC_DIMENSIONS = [
    ("first_impression", "Magnificence at a glance — does it look professionally designed?"),
    ("visual_hierarchy", "Does the eye land where it should? Clear focal point and flow."),
    ("whitespace_balance", "Composition, breathing room, optical alignment, balance."),
    ("typography_craft", "Scale contrast, pairing, rhythm — as rendered."),
    ("colour_harmony", "Palette cohesion and one intentional, owned accent."),
    ("finish_consistency", "Alignment, spacing regularity, no wonky geometry or orphans."),
    ("human_vs_ai", "Does it read as hand-designed, or as generic AI template output?"),
]

_RUBRIC_TEXT = "\n".join(f"  - {k}: {desc}" for k, desc in RUBRIC_DIMENSIONS)


def build_prompt(archetype: str | None, breakpoints: list[str]) -> str:
    """Assemble the instruction sent alongside the screenshots."""
    arch = (
        f"The design committed to archetype: {archetype}. Judge it against that intent "
        f"(e.g. a Luxury archetype SHOULD be restrained — do not penalise it for being quiet).\n"
        if archetype else
        "No archetype was declared. Judge it as a general professional web design.\n"
    )
    bp = ", ".join(breakpoints)
    return (
        "You are a senior product designer doing a brutally honest design review.\n"
        "You are shown the SAME page rendered at these breakpoints: " + bp + ".\n\n"
        + arch +
        "\nGoal of the project: the page must look magnificent and indistinguishable from "
        "the work of a skilled human designer — not generic AI output.\n\n"
        "Score each dimension 0-100 (0 = amateur/AI-slop, 100 = award-worthy):\n"
        + _RUBRIC_TEXT +
        "\n\nCalibration anchors — score like a skeptical senior reviewer, not a cheerleader:\n"
        "  90-100  award-worthy, would headline a design gallery — RARE.\n"
        "  80-89   strong, polished, clearly human-crafted, only minor nits.\n"
        "  70-79   good and shippable, but with visible weaknesses.\n"
        "  60-69   acceptable but generic in places; needs real work.\n"
        "  below 60  reads as AI-slop or amateur.\n"
        "Most competent first attempts land 72-85. Reserve 90+ for genuinely exceptional work and justify why.\n"
        "Uniform near-perfect scores (everything > 95) are treated as un-calibrated and automatically penalised.\n\n"
        "Then give an overall_score (0-100) as your honest holistic judgment (NOT a mean), "
        "a one-line verdict, whether it reads_as \"human\" or \"ai\", and the concrete, high-leverage "
        "fixes ranked by impact. You MUST list AT LEAST 2 specific fixes — even excellent designs have them; "
        "reference exactly what you see.\n\n"
        "Respond with ONLY a JSON object, no prose, in exactly this shape:\n"
        "{\n"
        '  "overall_score": <int>,\n'
        '  "verdict": "<one line>",\n'
        '  "reads_as": "human" | "ai",\n'
        '  "dimensions": { "first_impression": {"score": <int>, "note": "<str>"}, ... all 7 ... },\n'
        '  "top_fixes": ["<fix>", ...]\n'
        "}"
    )


# ── Image handling ───────────────────────────────────────────────────────────

def collect_screenshots(screenshots_dir: Path) -> list[tuple[str, Path]]:
    """Return [(breakpoint_name, path)] for PNGs in the directory, stable order."""
    if not screenshots_dir.is_dir():
        raise FileNotFoundError(f"screenshots dir not found: {screenshots_dir}")
    pngs = sorted(screenshots_dir.glob("*.png"))
    if not pngs:
        raise FileNotFoundError(f"no .png screenshots in {screenshots_dir}")
    return [(p.stem, p) for p in pngs]


def encode_image(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


# ── Request assembly (provider-specific, no network here — testable) ──────────

def build_openai_payload(model: str, prompt: str, shots: list[tuple[str, Path]]) -> dict[str, Any]:
    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    for name, path in shots:
        content.append({"type": "text", "text": f"[breakpoint: {name}]"})
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{encode_image(path)}"},
        })
    return {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": 1500,
        "temperature": 0.2,
    }


def build_anthropic_payload(model: str, prompt: str, shots: list[tuple[str, Path]]) -> dict[str, Any]:
    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    for name, path in shots:
        content.append({"type": "text", "text": f"[breakpoint: {name}]"})
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": encode_image(path)},
        })
    return {
        "model": model,
        "max_tokens": 1500,
        "temperature": 0.2,
        "messages": [{"role": "user", "content": content}],
    }


# ── Response parsing ─────────────────────────────────────────────────────────

def extract_text_openai(resp: dict[str, Any]) -> str:
    return resp["choices"][0]["message"]["content"]


def extract_text_anthropic(resp: dict[str, Any]) -> str:
    parts = resp.get("content", [])
    return "".join(p.get("text", "") for p in parts if p.get("type") == "text")


def parse_verdict(text: str) -> dict[str, Any]:
    """Pull the JSON object out of a model reply, tolerating code fences / prose."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1]
        if t.lstrip().lower().startswith("json"):
            t = t.lstrip()[4:]
    start, end = t.find("{"), t.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no JSON object found in model response")
    data = json.loads(t[start:end + 1])
    if "overall_score" not in data:
        raise ValueError("model response missing 'overall_score'")
    data["overall_score"] = int(data["overall_score"])
    return data


# ── Network call (only place that touches the API) ────────────────────────────

def call_model(provider: str, base_url: str, model: str, payload: dict[str, Any]) -> dict[str, Any]:
    import urllib.request
    import urllib.error

    if provider == "anthropic":
        url = base_url.rstrip("/") + "/v1/messages"
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY not set in environment")
        headers = {
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
    else:  # openai-compatible
        url = base_url.rstrip("/") + "/v1/chat/completions"
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY not set in environment")
        headers = {"Authorization": f"Bearer {key}", "content-type": "application/json"}

    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"API error {e.code}: {e.read().decode('utf-8', 'replace')[:500]}")


# ── Reporting ────────────────────────────────────────────────────────────────

def score_colour(score: int, floor: int, passing: int) -> str:
    if score >= passing:
        return GREEN
    if score >= floor:
        return YELLOW
    return RED


def print_report(verdict: dict[str, Any], floor: int, passing: int, effective: int | None = None, flags: list | None = None) -> None:
    raw = verdict["overall_score"]
    s = effective if effective is not None else raw
    colour = score_colour(s, floor, passing)
    reads = verdict.get("reads_as", "?")
    sep = "=" * 52
    print(f"\n{BOLD}{sep}{RESET}")
    print("  AESTHETIC REVIEW — vision judgment")
    print(f"{BOLD}{sep}{RESET}\n")
    print(f"  Overall: {colour}{BOLD}{s}/100{RESET}   reads as: "
          f"{(GREEN if reads=='human' else RED)}{reads.upper()}{RESET}")
    print(f"  {DIM}{verdict.get('verdict','')}{RESET}\n")
    if effective is not None and effective != raw:
        print(f"  {DIM}(raw self-score {raw} -> calibrated {s}){RESET}")
    for _fl in (flags or []):
        print(f"  {YELLOW}⚠ {_fl}{RESET}")
    if flags:
        print()

    dims = verdict.get("dimensions", {})
    for key, desc in RUBRIC_DIMENSIONS:
        d = dims.get(key, {})
        sc = d.get("score", "?")
        mark = score_colour(sc, floor, passing) if isinstance(sc, int) else DIM
        print(f"  {BOLD}{key:<20}{RESET} {mark}{str(sc):>3}{RESET}  {DIM}{d.get('note','')[:70]}{RESET}")
    print()

    fixes = verdict.get("top_fixes", [])
    if fixes:
        print(f"  {YELLOW}Top fixes (ranked by impact):{RESET}")
        for i, f in enumerate(fixes, 1):
            print(f"   {i}. {f}")
        print()

    print(f"{BOLD}{sep}{RESET}")
    if s < floor:
        print(f"  {RED}{BOLD}❌ BLOCKED{RESET} — {s}/100 below floor {floor}. "
              f"Does not yet read as human-designed.")
    elif s < passing:
        print(f"  {YELLOW}{BOLD}⚠️  POLISH{RESET} — {s}/100 below pass {passing}. "
              f"Apply the fixes above.")
    else:
        print(f"  {GREEN}{BOLD}✅ PASSED{RESET} — {s}/100. Reads as deliberate, human design.")
    print(f"{BOLD}{sep}{RESET}\n")


def exit_code_for(score: int, floor: int, passing: int) -> int:
    if score < floor:
        return 2
    if score < passing:
        return 1
    return 0


def calibrate_verdict(verdict: dict[str, Any], floor: int, passing: int) -> tuple[int, list]:
    """Anti-inflation calibration for a vision verdict.

    The agent frequently grades its OWN work, so a self-flattered near-perfect
    verdict is discounted and a verdict without concrete critiques is treated as
    un-calibrated. Returns (effective_score, flags).
    """
    raw = int(verdict.get("overall_score", 0))
    dims = verdict.get("dimensions", {}) or {}
    dim_scores = [d.get("score") for d in dims.values()
                  if isinstance(d, dict) and isinstance(d.get("score"), int)]
    fixes = [f for f in (verdict.get("top_fixes") or [])
             if isinstance(f, str) and len(f.strip()) >= 8]
    flags: list = []
    effective = raw

    uniform_perfect = raw >= 95 or (len(dim_scores) >= 5 and min(dim_scores) >= 95)
    if uniform_perfect:
        penalty = 18 if len(fixes) < 3 else 10
        effective = max(0, raw - penalty)
        flags.append(
            f"INFLATION GUARD - near-perfect scores (overall {raw}, {len(fixes)} concrete "
            f"fix(es)) match the self-flattery pattern. Applied -{penalty} calibration "
            f"penalty -> effective {effective}/100."
        )

    if len(fixes) < 2:
        flags.append(
            "UNCALIBRATED - fewer than 2 concrete critiques. No shippable design is flawless: "
            "re-review honestly and list at least 2 specific, high-leverage fixes."
        )

    return effective, flags


# ── CLI ──────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="aesthetic_review",
        description="Aesthetic judgment of rendered screenshots — by the agent's own vision (default) or an external vision API.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--screenshots", type=Path, default=Path("./audit-results"),
                   help="Directory of PNG screenshots (from visual_audit.py)")
    p.add_argument("--archetype", type=str, default=None,
                   help="Declared archetype, so the review judges against intent")
    p.add_argument("--mode", choices=["agent", "api"], default="agent",
                   help="agent (default): the model executing the skill judges with its own vision, no API key. "
                        "api: call an external vision model.")
    p.add_argument("--verdict", type=Path, default=None,
                   help="Path to a verdict JSON the agent produced; scores it and returns the gate exit code.")
    p.add_argument("--threshold", nargs=2, type=int, metavar=("FLOOR", "PASS"), default=[60, 75])
    p.add_argument("--json", action="store_true", dest="json_output")
    # --- api mode only ---
    p.add_argument("--provider", choices=["openai", "anthropic"], default="openai",
                   help="(api mode) vision provider")
    p.add_argument("--model", type=str, default=None,
                   help="(api mode) vision model (default: gpt-4o / claude-3-5-sonnet-latest)")
    p.add_argument("--base-url", type=str, default="https://api.openai.com",
                   help="(api mode) API base URL (any OpenAI-compatible endpoint)")
    p.add_argument("--dry-run", action="store_true",
                   help="(api mode) assemble the request and print a summary; do NOT call the API")
    return p


def default_model(provider: str) -> str:
    return "claude-3-5-sonnet-latest" if provider == "anthropic" else "gpt-4o"


def main() -> int:
    args = build_parser().parse_args()
    floor, passing = args.threshold
    if not (0 <= floor < passing <= 100):
        print("Error: thresholds must satisfy 0 ≤ FLOOR < PASS ≤ 100.", file=sys.stderr)
        return 2

    # Loop-closer: score a verdict the agent already produced with its own vision.
    if args.verdict is not None:
        try:
            verdict = parse_verdict(args.verdict.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            print(f"Error reading verdict: {e}", file=sys.stderr)
            return 2
        effective, flags = calibrate_verdict(verdict, floor, passing)
        uncalibrated = any(f.startswith("UNCALIBRATED") for f in flags)
        code = 2 if uncalibrated else exit_code_for(effective, floor, passing)
        if args.json_output:
            verdict["raw_score"] = verdict["overall_score"]
            verdict["effective_score"] = effective
            verdict["calibration_flags"] = flags
            verdict["exit_code"] = code
            print(json.dumps(verdict, indent=2, ensure_ascii=False))
        else:
            print_report(verdict, floor, passing, effective=effective, flags=flags)
        return code

    try:
        shots = collect_screenshots(args.screenshots)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    breakpoints = [name for name, _ in shots]
    prompt = build_prompt(args.archetype, breakpoints)

    # Default: the model executing the skill judges with its OWN native vision — no API key.
    if args.mode == "agent":
        manifest = {
            "status": "awaiting_agent_vision",
            "instructions": (
                "You (the model executing this skill) are vision-capable. Open each screenshot "
                "listed below with your own vision, apply the rubric, and write the verdict JSON "
                "to a file. Then run: python3 scripts/aesthetic_review.py --verdict <file.json> "
                f"--threshold {floor} {passing}  to score it and get the gate exit code."
            ),
            "screenshots": [str(p.resolve()) for _, p in shots],
            "rubric": prompt,
            "verdict_schema": {
                "overall_score": "int 0-100",
                "verdict": "one line",
                "reads_as": "human | ai",
                "dimensions": {k: {"score": "int", "note": "str"} for k, _ in RUBRIC_DIMENSIONS},
                "top_fixes": ["str", "..."],
            },
            "thresholds": {"floor": floor, "pass": passing},
        }
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
        return 0

    # api mode: call an external vision model (for unsupervised pipelines).
    model = args.model or default_model(args.provider)
    payload = (build_anthropic_payload if args.provider == "anthropic" else build_openai_payload)(model, prompt, shots)
    if args.dry_run:
        print(json.dumps({
            "provider": args.provider, "model": model, "base_url": args.base_url,
            "breakpoints": breakpoints, "n_images": len(shots),
            "prompt_chars": len(prompt), "thresholds": {"floor": floor, "pass": passing},
        }, indent=2))
        return 0
    try:
        raw = call_model(args.provider, args.base_url, model, payload)
        text = extract_text_anthropic(raw) if args.provider == "anthropic" else extract_text_openai(raw)
        verdict = parse_verdict(text)
    except Exception as e:  # noqa: BLE001
        print(f"Error: {e}", file=sys.stderr)
        return 2
    effective, flags = calibrate_verdict(verdict, floor, passing)
    uncalibrated = any(f.startswith("UNCALIBRATED") for f in flags)
    code = 2 if uncalibrated else exit_code_for(effective, floor, passing)
    if args.json_output:
        verdict["raw_score"] = verdict["overall_score"]
        verdict["effective_score"] = effective
        verdict["calibration_flags"] = flags
        verdict["exit_code"] = code
        print(json.dumps(verdict, indent=2, ensure_ascii=False))
    else:
        print_report(verdict, floor, passing, effective=effective, flags=flags)
    return code


if __name__ == "__main__":
    sys.exit(main())
