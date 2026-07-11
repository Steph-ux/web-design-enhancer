"""Discovery closed-loop traces: contract → code → render.

P5 — prove decisions survive from territory selection into contracts, source, and (optionally) browser evidence.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CONTRACT_FILES = (
    "CREATIVE-BRIEF.md",
    "EXPERIENCE-CONTRACT.md",
    "DESIGN.md",
    "STRUCTURAL-LOCK.md",
)


@dataclass
class TraceFinding:
    check: str
    ok: bool
    detail: str
    severity: str = "blocking"  # blocking | major | minor | advice

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TraceReport:
    kind: str  # contract | code | render
    ok: bool
    findings: list[TraceFinding] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "ok": self.ok,
            "findings": [f.to_dict() for f in self.findings],
            "details": self.details,
        }


def _load_winner(root: Path) -> dict[str, Any] | None:
    terr = root / ".wde" / "research" / "territories.json"
    if not terr.is_file():
        return None
    try:
        data = json.loads(terr.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    sel = data.get("selection") or {}
    wid = sel.get("winner_id")
    for t in data.get("territories") or []:
        if t.get("id") == wid:
            return t
    return None


def _load_interp_action(root: Path) -> str:
    p = root / ".wde" / "research" / "interpretation.json"
    if not p.is_file():
        return ""
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return str(data.get("primary_action") or "")
    except (OSError, json.JSONDecodeError):
        return ""


def run_contract_trace(root: Path) -> TraceReport:
    """Verify discovery decisions appear across the four contracts."""
    findings: list[TraceFinding] = []
    winner = _load_winner(root)
    if not winner:
        return TraceReport(
            kind="contract",
            ok=False,
            findings=[
                TraceFinding(
                    "contract.winner",
                    False,
                    "No winner in .wde/research/territories.json — run wde discover first",
                )
            ],
        )

    signature = str(winner.get("signature_move") or "")
    metaphor = str(winner.get("metaphor") or "")
    anti = [str(a) for a in (winner.get("anti_references") or [])][:5]
    sig_id = f"{str(winner.get('id') or 'a').lower()}-signature"
    primary_action = _load_interp_action(root)
    tokens = winner.get("tokens") or {}
    bg = str(tokens.get("background") or "")

    texts: dict[str, str] = {}
    for name in CONTRACT_FILES:
        path = root / name
        if not path.is_file():
            findings.append(
                TraceFinding("contract.missing", False, f"Missing {name}", "blocking")
            )
            texts[name] = ""
        else:
            texts[name] = path.read_text(encoding="utf-8", errors="replace")

    # Signature in all four
    if signature:
        present = [n for n, t in texts.items() if signature[:40] in t or signature in t]
        missing = [n for n in CONTRACT_FILES if n not in present and texts.get(n) is not None]
        # Allow partial match if very long signature
        ok_sig = len(present) >= 3
        findings.append(
            TraceFinding(
                "contract.signature",
                ok_sig,
                f"Signature in {len(present)}/4 contracts: {present}"
                + (f"; missing {missing}" if missing else ""),
                "blocking" if not ok_sig else "advice",
            )
        )

    # Metaphor in brief + design + lock
    if metaphor:
        need = ["CREATIVE-BRIEF.md", "DESIGN.md", "STRUCTURAL-LOCK.md"]
        hit = [n for n in need if metaphor[:30] in texts.get(n, "")]
        findings.append(
            TraceFinding(
                "contract.metaphor",
                len(hit) >= 2,
                f"Metaphor present in {hit}",
                "major" if len(hit) < 2 else "advice",
            )
        )

    # Grep signature id in DESIGN
    design = texts.get("DESIGN.md", "")
    findings.append(
        TraceFinding(
            "contract.grep_signature",
            sig_id in design.lower() or "signature" in design.lower(),
            f"Expected grep marker `{sig_id}` or Signature section in DESIGN.md",
            "major",
        )
    )

    # CTA consistency
    if primary_action:
        cta_hits = [n for n, t in texts.items() if primary_action.lower()[:24] in t.lower()]
        findings.append(
            TraceFinding(
                "contract.cta",
                len(cta_hits) >= 2,
                f"Primary action « {primary_action[:60]} » in {cta_hits}",
                "major" if len(cta_hits) < 2 else "advice",
            )
        )

    # Winner background token in DESIGN when available
    if bg and design:
        findings.append(
            TraceFinding(
                "contract.tokens",
                bg.upper() in design.upper() or bg in design,
                f"Winner background token {bg} in DESIGN.md",
                "blocking",
            )
        )

    # Anti-references should appear as bans (at least one)
    if anti and design:
        ban_hits = sum(1 for a in anti if a[:20].lower() in design.lower())
        findings.append(
            TraceFinding(
                "contract.anti_refs",
                ban_hits >= 1,
                f"{ban_hits}/{len(anti)} anti-references cited in DESIGN.md",
                "minor",
            )
        )

    blocking_fail = [f for f in findings if not f.ok and f.severity == "blocking"]
    return TraceReport(
        kind="contract",
        ok=len(blocking_fail) == 0,
        findings=findings,
        details={"winner_id": winner.get("id"), "signature": signature[:80]},
    )


def _iter_code_files(root: Path) -> list[Path]:
    exts = {".html", ".css", ".scss", ".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte"}
    skip = {".wde", "node_modules", ".git", "tests", "wde", "scripts", "references", "data"}
    out: list[Path] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in skip for part in p.parts):
            continue
        if p.suffix.lower() in exts:
            out.append(p)
    # Prefer src/ and root html/css
    out.sort(key=lambda x: (0 if "src" in x.parts else 1, str(x)))
    return out[:80]


def run_code_trace(root: Path) -> TraceReport:
    """Verify signature markers / tokens / anti-pattern absence in implementation files."""
    findings: list[TraceFinding] = []
    winner = _load_winner(root)
    if not winner:
        return TraceReport(
            kind="code",
            ok=False,
            findings=[
                TraceFinding("code.winner", False, "No discovery winner — skip or run discover")
            ],
        )

    files = _iter_code_files(root)
    if not files:
        return TraceReport(
            kind="code",
            ok=True,  # no code yet — not a failure at discovery time
            findings=[
                TraceFinding(
                    "code.absent",
                    True,
                    "No implementation files yet — code_trace deferred until implement",
                    "advice",
                )
            ],
            details={"files": 0},
        )

    blob = ""
    for p in files:
        try:
            blob += "\n" + p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
    blob_l = blob.lower()

    sig_id = f"{str(winner.get('id') or 'a').lower()}-signature"
    signature = str(winner.get("signature_move") or "")
    tokens = winner.get("tokens") or {}
    bg = str(tokens.get("background") or "")
    accent = str(tokens.get("accent") or "")
    anti = [str(a).lower() for a in (winner.get("anti_references") or [])]

    # Signature marker
    has_marker = sig_id in blob_l or "data-signature" in blob_l or "wde-signature" in blob_l
    if signature and len(signature) > 12:
        has_marker = has_marker or signature[:24].lower() in blob_l
    findings.append(
        TraceFinding(
            "code.signature_marker",
            has_marker,
            f"Signature marker `{sig_id}` or equivalent in code" if has_marker else f"Missing `{sig_id}` / data-signature in code",
            "major",
        )
    )

    # Tokens
    if bg:
        findings.append(
            TraceFinding(
                "code.token_bg",
                bg.lower() in blob_l,
                f"Background token {bg} in styles/markup",
                "major",
            )
        )
    if accent:
        findings.append(
            TraceFinding(
                "code.token_accent",
                accent.lower() in blob_l,
                f"Accent token {accent} in styles/markup",
                "minor",
            )
        )

    # Forbidden tropes that must not reappear if banned
    banned_patterns = [
        (r"linear-gradient\s*\([^)]*#(?:667eea|764ba2|a78bfa)", "blue-purple gradient"),
        (r"backdrop-filter\s*:\s*blur\s*\(\s*[1-9]\d*px", "heavy glassmorphism blur"),
        (r"trusted[- ]?by", "trusted-by logo wall"),
    ]
    for pat, label in banned_patterns:
        if re.search(pat, blob, re.I):
            # only fail if related anti-ref mentioned
            if any(label.split()[0] in a or "gradient" in a or "glass" in a for a in anti):
                findings.append(
                    TraceFinding(
                        "code.anti_present",
                        False,
                        f"Banned pattern present in code: {label}",
                        "blocking",
                    )
                )

    # CTA present
    action = _load_interp_action(root)
    if action:
        # loose: first word of action
        key = action.split()[0].lower() if action.split() else ""
        findings.append(
            TraceFinding(
                "code.cta",
                key in blob_l if key else True,
                f"Primary action cue « {key} » in markup" if key else "no action",
                "minor",
            )
        )

    blocking_fail = [f for f in findings if not f.ok and f.severity in {"blocking", "major"}]
    # major failures make ok=False for code when code exists
    return TraceReport(
        kind="code",
        ok=len([f for f in findings if not f.ok and f.severity == "blocking"]) == 0
        and len([f for f in findings if not f.ok and f.severity == "major"]) == 0,
        findings=findings,
        details={"files_scanned": len(files)},
    )


def run_render_trace(
    root: Path,
    *,
    require_browser: bool = False,
    url: str | None = None,
) -> TraceReport:
    """Verify browser/capture evidence of signature when available.

    Prefer Playwright when installed + HTML/URL available:
      - signature visible desktop + mobile
      - interaction (hover/click) ok
      - screenshots under .wde/discovery/render/

    Without Playwright, falls back to static HTML / existing captures.
    ``require_browser=True`` makes missing Playwright / failed probe blocking.
    """
    findings: list[TraceFinding] = []
    details: dict[str, Any] = {}
    winner = _load_winner(root)
    sig_id = ""
    if winner:
        sig_id = f"{str(winner.get('id') or 'a').lower()}-signature"

    # Look for evidence artifacts from visual checks
    evidence_dirs = [
        root / ".wde" / "evidence",
        root / ".wde" / "visual",
        root / ".wde" / "discovery" / "render",
        root / "audit-results",
    ]
    captures: list[Path] = []
    for d in evidence_dirs:
        if d.is_dir():
            captures.extend(d.rglob("*.png"))
            captures.extend(d.rglob("*.webp"))
            captures.extend(d.rglob("*report*.json"))

    html_files = list(root.glob("**/*.html"))
    html_files = [p for p in html_files if ".wde" not in p.parts and "node_modules" not in p.parts]

    # ── Playwright probe (preferred) ──────────────────────────────────────
    target: str | None = url
    if not target and html_files:
        # Prefer src/index.html then first html
        preferred = [p for p in html_files if "src" in p.parts and p.name == "index.html"]
        target = str((preferred[0] if preferred else html_files[0]).resolve())

    if target:
        try:
            from wde.runners.browser_runner import run_discovery_render_probe

            probe = run_discovery_render_probe(
                root=root,
                target=target,
                signature_id=sig_id,
            )
            details["playwright_probe"] = probe
            if probe.get("playwright"):
                findings.append(
                    TraceFinding(
                        "render.signature_desktop",
                        bool(probe.get("signature_visible_desktop")),
                        "Signature visible at 1280px"
                        if probe.get("signature_visible_desktop")
                        else "Signature not visible at desktop",
                        "blocking" if require_browser else "major",
                    )
                )
                findings.append(
                    TraceFinding(
                        "render.signature_mobile",
                        bool(probe.get("signature_visible_mobile")),
                        "Signature survives 375px viewport"
                        if probe.get("signature_visible_mobile")
                        else "Signature lost on mobile",
                        "blocking" if require_browser else "major",
                    )
                )
                findings.append(
                    TraceFinding(
                        "render.interaction",
                        bool(probe.get("interaction_ok")),
                        "Signature hover/click interaction ok"
                        if probe.get("interaction_ok")
                        else f"Interaction failed: {probe.get('error') or 'unknown'}",
                        "major",
                    )
                )
                caps = probe.get("captures") or []
                findings.append(
                    TraceFinding(
                        "render.captures",
                        len(caps) >= 2,
                        f"{len(caps)} Playwright capture(s): {caps}",
                        "major" if require_browser else "advice",
                    )
                )
                captures.extend(root / c for c in caps if (root / c).is_file())
            else:
                # Playwright missing or failed to launch
                sev = "blocking" if require_browser else "advice"
                findings.append(
                    TraceFinding(
                        "render.playwright_unavailable",
                        not require_browser,
                        probe.get("error") or "Playwright probe unavailable",
                        sev,
                    )
                )
        except Exception as e:  # noqa: BLE001
            findings.append(
                TraceFinding(
                    "render.playwright_error",
                    not require_browser,
                    str(e)[:200],
                    "blocking" if require_browser else "advice",
                )
            )

    if not captures and not html_files and not target:
        sev = "blocking" if require_browser else "advice"
        findings.append(
            TraceFinding(
                "render.no_evidence",
                not require_browser,
                "No captures or HTML for render_trace"
                + (" — required" if require_browser else " — deferred"),
                sev,
            )
        )
        return TraceReport(
            kind="render",
            ok=not require_browser,
            findings=findings,
            details=details,
        )

    # Static HTML checks when present (always as supplement)
    if html_files:
        blob = ""
        for p in html_files[:20]:
            try:
                blob += p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
        blob_l = blob.lower()
        if sig_id:
            findings.append(
                TraceFinding(
                    "render.signature_dom",
                    sig_id in blob_l or "data-signature" in blob_l or "signature" in blob_l,
                    f"Signature cue in HTML ({sig_id})",
                    "major",
                )
            )
        # Responsive hints
        has_viewport = "viewport" in blob_l
        has_media = "@media" in blob_l or "max-width" in blob_l
        # media may be in linked CSS only
        css_blob = ""
        for p in root.rglob("*.css"):
            if ".wde" in p.parts or "node_modules" in p.parts:
                continue
            try:
                css_blob += p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if len(css_blob) > 200_000:
                break
        has_media = has_media or "@media" in css_blob
        findings.append(
            TraceFinding(
                "render.viewport",
                has_viewport,
                "viewport meta present" if has_viewport else "missing viewport meta",
                "major",
            )
        )
        findings.append(
            TraceFinding(
                "render.responsive",
                has_media,
                "responsive @media rules found" if has_media else "no @media — may fail responsive survival",
                "minor",
            )
        )

    if captures and not any(f.check == "render.captures" for f in findings):
        findings.append(
            TraceFinding(
                "render.captures",
                True,
                f"{len(captures)} capture/report artifact(s) under evidence dirs",
                "advice",
            )
        )

    blocking_fail = [f for f in findings if not f.ok and f.severity in {"blocking", "major"}]
    details.update(
        {
            "captures": len(captures),
            "html_files": len(html_files),
            "target": target,
        }
    )
    return TraceReport(
        kind="render",
        ok=len(blocking_fail) == 0,
        findings=findings,
        details=details,
    )


def run_all_traces(
    root: Path,
    *,
    require_browser: bool = False,
    url: str | None = None,
) -> dict[str, Any]:
    """Run contract + code + render traces; write report under .wde/discovery/."""
    root = root.resolve()
    reports = {
        "contract_trace": run_contract_trace(root),
        "code_trace": run_code_trace(root),
        "render_trace": run_render_trace(
            root, require_browser=require_browser, url=url
        ),
    }
    ok = all(r.ok for r in reports.values())
    payload = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ok": ok,
        "traces": {k: v.to_dict() for k, v in reports.items()},
    }
    out_dir = root / ".wde" / "discovery"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "traces.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # human summary
    lines = ["Discovery traces", f"Overall: {'PASS' if ok else 'FAIL'}", ""]
    for name, rep in reports.items():
        lines.append(f"## {name}: {'ok' if rep.ok else 'FAIL'}")
        for f in rep.findings:
            mark = "✓" if f.ok else "✗"
            lines.append(f"  {mark} [{f.severity}] {f.check}: {f.detail}")
        lines.append("")
    (out_dir / "traces-report.txt").write_text("\n".join(lines), encoding="utf-8")
    return payload
