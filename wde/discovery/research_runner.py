"""Execute research tools and always write receipts (success / failed / skipped)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from wde.discovery.interpret import Interpretation
from wde.discovery.receipts import ResearchReceipt, request_hash, research_dir, write_receipt
from wde.runners.subprocess_runner import run_python_script, scripts_dir

# Threaded request hash for receipt invalidation (set by run_all_research)
_ACTIVE_REQUEST_HASH = ""


def _write_text_artifact(root: Path, name: str, text: str) -> Path:
    d = research_dir(root)
    d.mkdir(parents=True, exist_ok=True)
    path = d / name
    path.write_text(text, encoding="utf-8")
    return path


def _stamp(
    receipt: ResearchReceipt,
    *,
    source_type: str,
    network_used: bool = False,
    command: str = "",
    exit_code: int | None = None,
    degraded: bool = False,
) -> ResearchReceipt:
    receipt.source_type = source_type
    receipt.network_used = network_used
    receipt.executor = "wde-core"
    receipt.degraded = degraded
    receipt.request_hash = _ACTIVE_REQUEST_HASH
    receipt.command = command
    receipt.exit_code = exit_code
    return receipt


def _receipt_from_write(
    root: Path,
    receipt: ResearchReceipt,
    artifact_text: str = "",
) -> ResearchReceipt:
    write_receipt(root, receipt, artifact_text=artifact_text)
    return receipt


def run_sector_research(root: Path, interp: Interpretation) -> ResearchReceipt:
    """Local sector notes (no network) — always succeeds with structured notes."""
    query = interp.search_queries.get("sector", interp.subject)
    body = {
        "path_kind": "sector",
        "subject": interp.subject,
        "audience": interp.audience,
        "primary_action": interp.primary_action,
        "typical_codes": [
            "trust through restraint",
            "clear primary CTA",
            "proof without fake metrics",
        ],
        "conversion_path": f"hero → proof → {interp.primary_action}",
        "content_types": ["positioning", "cases", "process", "contact"],
        "query": query,
    }
    text = json.dumps(body, indent=2, ensure_ascii=False)
    art = _write_text_artifact(root, "sector-notes.json", text)
    rel = str(art.relative_to(root)).replace("\\", "/")
    rec = ResearchReceipt(
        tool="wde.discovery.sector",
        path_kind="sector",
        query=query,
        status="success",
        result_count=len(body["content_types"]),
        artifact=rel,
        retained=body["content_types"],
        notes="Sector framing from interpretation hypotheses",
        details=body,
    )
    _stamp(rec, source_type="internal_knowledge", network_used=False, command="sector_notes")
    return _receipt_from_write(root, rec, artifact_text=text)


def run_anti_reference_research(root: Path, interp: Interpretation) -> ResearchReceipt:
    query = interp.search_queries.get("anti_reference", "generic template cliches")
    cliches = [
        "dark hero + blue→purple gradient",
        "3 equal feature cards",
        "fake trusted-by logo wall",
        "soft glassmorphism everywhere",
        "emoji as section markers",
        "generic 'modern premium' with no POV",
    ]
    body = {
        "path_kind": "anti_reference",
        "query": query,
        "sector": interp.sector_key,
        "avoid": cliches,
        "why": "80% of sector templates share these moves — ban them in DESIGN.md",
    }
    text = json.dumps(body, indent=2, ensure_ascii=False)
    art = _write_text_artifact(root, "anti-reference.json", text)
    rel = str(art.relative_to(root)).replace("\\", "/")
    rec = ResearchReceipt(
        tool="wde.discovery.anti_reference",
        path_kind="anti_reference",
        query=query,
        status="success",
        result_count=len(cliches),
        artifact=rel,
        retained=cliches[:3],
        notes="Anti-reference list for distinction scoring",
        details=body,
    )
    _stamp(rec, source_type="internal_knowledge", network_used=False, command="anti_reference")
    return _receipt_from_write(root, rec, artifact_text=text)


def run_cross_domain_research(root: Path, interp: Interpretation) -> ResearchReceipt:
    query = interp.search_queries.get("cross_domain", "non-web inspiration")
    steals = {
        "hospitality": ["luggage tags", "guest ledgers", "topographic maps", "room keys"],
        "agency": ["print portfolios", "atelier stamps", "specimen sheets"],
        "saas": ["lab instruments", "runbooks", "signal diagrams"],
        "portfolio": ["workbenches", "sketchbooks", "specimen posters"],
        "commerce": ["price boards", "invoice columns", "warehouse rails"],
    }
    items = steals.get(interp.sector_key, ["museum labels", "industrial plates", "maps"])
    body = {
        "path_kind": "cross_domain",
        "query": query,
        "steals": items,
        "moves": items,
        "instruction": "Steal ONE move, not the whole aesthetic",
    }
    text = json.dumps(body, indent=2, ensure_ascii=False)
    art = _write_text_artifact(root, "cross-domain.json", text)
    rel = str(art.relative_to(root)).replace("\\", "/")
    rec = ResearchReceipt(
        tool="wde.discovery.cross_domain",
        path_kind="cross_domain",
        query=query,
        status="success",
        result_count=len(items),
        artifact=rel,
        retained=items[:2],
        notes="Cross-domain steal candidates",
        details=body,
    )
    # Local knowledge for now — not live web
    _stamp(
        rec,
        source_type="internal_knowledge",
        network_used=False,
        command="cross_domain_local",
    )
    return _receipt_from_write(root, rec, artifact_text=text)


def run_promax_search(root: Path, interp: Interpretation) -> ResearchReceipt:
    """Invoke real scripts/search.py --persist when available."""
    query = interp.search_queries.get("promax", interp.subject)
    project_name = "wde-discovery"
    script = scripts_dir() / "search.py"
    if not script.is_file():
        rec = ResearchReceipt(
            tool="search.py",
            path_kind="promax",
            query=query,
            status="skipped",
            result_count=0,
            notes=f"search.py not found at {script}",
        )
        _stamp(
            rec,
            source_type="local_corpus",
            network_used=False,
            command="search.py",
            degraded=True,
        )
        return _receipt_from_write(root, rec)

    # Persist into the project root so design-system-output.md lands there
    args = [
        query,
        "--design-system",
        "-p",
        project_name,
        "--persist",
        "--format",
        "markdown",
    ]
    res = run_python_script("search.py", args, cwd=root, timeout=180)
    # Expected artifacts
    out_md = root / "design-system-output.md"
    master = list((root / "design-system").glob("**/MASTER.md")) if (root / "design-system").is_dir() else []
    success = res.returncode == 0 and (out_md.is_file() or master)
    artifact = ""
    result_count = 0
    if out_md.is_file():
        artifact = "design-system-output.md"
        result_count = max(1, out_md.stat().st_size // 200)
    elif master:
        artifact = str(master[0].relative_to(root)).replace("\\", "/")
        result_count = 1

    # Also copy a snippet into research for digest stability
    snippet = (res.stdout or "")[:4000]
    if out_md.is_file():
        try:
            snippet = out_md.read_text(encoding="utf-8", errors="replace")[:8000]
        except OSError:
            pass
    art_path = _write_text_artifact(root, "promax-snippet.md", snippet or res.stderr or "empty")
    if not artifact:
        artifact = str(art_path.relative_to(root)).replace("\\", "/")

    rec = ResearchReceipt(
        tool="search.py",
        path_kind="promax",
        query=query,
        status="success" if success else ("failed" if res.returncode not in (0, 127) else "skipped"),
        result_count=result_count,
        artifact=artifact,
        retained=["design-system-output"] if success else [],
        notes=(res.stderr or "")[:500] or ("Pro Max persist OK" if success else f"rc={res.returncode}"),
        details={"returncode": res.returncode, "stdout_head": (res.stdout or "")[:500]},
    )
    _stamp(
        rec,
        source_type="local_corpus",
        network_used=False,
        command="python scripts/search.py --persist",
        exit_code=res.returncode,
        degraded=not success,
    )
    return _receipt_from_write(root, rec, artifact_text=snippet)


def run_getdesign(root: Path, brand: str = "bugatti") -> ResearchReceipt:
    """Optional npx getdesign — may skip without network/npx."""
    query = f"getdesign add {brand}"
    npx = shutil.which("npx")
    if not npx:
        rec = ResearchReceipt(
            tool="getdesign",
            path_kind="getdesign",
            query=query,
            status="skipped",
            notes="npx not on PATH",
        )
        _stamp(
            rec,
            source_type="external_cli",
            network_used=True,
            command="npx getdesign@latest add",
            degraded=True,
        )
        return _receipt_from_write(root, rec)

    try:
        proc = subprocess.run(
            [npx, "--yes", "getdesign@latest", "add", brand],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )
    except (subprocess.TimeoutExpired, OSError) as e:
        rec = ResearchReceipt(
            tool="getdesign",
            path_kind="getdesign",
            query=query,
            status="failed",
            notes=str(e)[:500],
        )
        _stamp(
            rec,
            source_type="external_cli",
            network_used=True,
            command=f"npx getdesign@latest add {brand}",
            degraded=True,
        )
        return _receipt_from_write(root, rec)

    brand_dir = root / brand / "DESIGN.md"
    gd_copy = root / f"getdesign-{brand}.md"
    success = proc.returncode == 0 and brand_dir.is_file()
    if success:
        try:
            gd_copy.write_text(brand_dir.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
        except OSError:
            pass
    artifact = ""
    if gd_copy.is_file():
        artifact = gd_copy.name
    elif brand_dir.is_file():
        artifact = str(brand_dir.relative_to(root)).replace("\\", "/")

    text = (proc.stdout or "") + "\n" + (proc.stderr or "")
    rec = ResearchReceipt(
        tool="getdesign",
        path_kind="getdesign",
        query=query,
        status="success" if success else "failed",
        result_count=1 if success else 0,
        artifact=artifact,
        retained=[brand] if success else [],
        notes=(proc.stderr or proc.stdout or "")[:400],
        details={"returncode": proc.returncode},
    )
    _stamp(
        rec,
        source_type="external_cli",
        network_used=True,
        command=f"npx getdesign@latest add {brand}",
        exit_code=proc.returncode,
        degraded=not success,
    )
    return _receipt_from_write(root, rec, artifact_text=text)


def run_visual_notes(root: Path, interp: Interpretation) -> ResearchReceipt:
    """Local visual direction notes (pairs with getdesign when available)."""
    query = interp.search_queries.get("visual", "")
    body = {
        "path_kind": "visual",
        "query": query,
        "type_roles": "display + mono captions",
        "composition": "asymmetric hierarchy, hairlines, one accent",
        "typography": "display + mono captions",
        "layout": "asymmetric hierarchy, hairlines, one accent",
        "image": "tactile stills preferred over stock smiles",
        "motion": "restrained unless territory demands otherwise",
    }
    text = json.dumps(body, indent=2, ensure_ascii=False)
    art = _write_text_artifact(root, "visual-notes.json", text)
    rel = str(art.relative_to(root)).replace("\\", "/")
    rec = ResearchReceipt(
        tool="wde.discovery.visual",
        path_kind="visual",
        query=query,
        status="success",
        result_count=3,
        artifact=rel,
        retained=list(body.keys()),
        notes="Visual framing notes",
        details=body,
    )
    _stamp(rec, source_type="internal_knowledge", network_used=False, command="visual_notes")
    return _receipt_from_write(root, rec, artifact_text=text)


def run_all_research(
    root: Path,
    interp: Interpretation,
    *,
    try_getdesign: bool = True,
) -> list[ResearchReceipt]:
    """Run all research paths; always returns receipts."""
    global _ACTIVE_REQUEST_HASH
    _ACTIVE_REQUEST_HASH = request_hash(interp.raw_request)
    receipts: list[ResearchReceipt] = []
    receipts.append(run_sector_research(root, interp))
    receipts.append(run_visual_notes(root, interp))
    receipts.append(run_anti_reference_research(root, interp))
    receipts.append(run_cross_domain_research(root, interp))
    receipts.append(run_promax_search(root, interp))
    if try_getdesign:
        # brand choice: hospitality/agency → bugatti austerity; else linear-ish skip if fails
        brand = "bugatti"
        receipts.append(run_getdesign(root, brand=brand))
    return receipts
