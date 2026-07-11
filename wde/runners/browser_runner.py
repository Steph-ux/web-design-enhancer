"""Browser-side helpers: URL probe + V2 visual_audit invocation."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from wde.runners.subprocess_runner import run_python_script


@dataclass
class UrlProbe:
    ok: bool
    status: int | None
    error: str = ""


def probe_url(url: str, timeout: float = 5.0) -> UrlProbe:
    try:
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "wde-v3"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return UrlProbe(ok=200 <= resp.status < 400, status=resp.status)
    except urllib.error.HTTPError as e:
        return UrlProbe(ok=False, status=e.code, error=str(e))
    except Exception as e:  # noqa: BLE001 — surface any network failure
        return UrlProbe(ok=False, status=None, error=str(e))


def run_visual_audit(
    *,
    root: Path,
    url: str,
    output: Path,
) -> dict[str, Any]:
    """Run scripts/visual_audit.py; return structured summary."""
    output.mkdir(parents=True, exist_ok=True)
    res = run_python_script(
        "visual_audit.py",
        ["--url", url, "--output", str(output)],
        cwd=root,
        timeout=300,
    )
    report_path = output / "audit_report.json"
    report: dict[str, Any] = {}
    if report_path.is_file():
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            report = {}
    return {
        "returncode": res.returncode,
        "stdout": res.stdout[-2000:] if res.stdout else "",
        "stderr": res.stderr[-1000:] if res.stderr else "",
        "report_path": str(report_path) if report_path.is_file() else "",
        "report": report,
        "ok": res.returncode == 0 and report_path.is_file(),
    }


def run_discovery_render_probe(
    *,
    root: Path,
    target: str,
    signature_id: str = "",
    out_dir: Path | None = None,
) -> dict[str, Any]:
    """Playwright probe for discovery.render_trace.

    Checks:
      - signature marker exists and is visible at desktop
      - optional interaction (click / hover) does not throw
      - signature still visible at mobile width
      - screenshots written under .wde/discovery/render/

    ``target`` may be a URL (http…) or a filesystem path to an HTML file.
    Returns structured result; never raises to callers.
    """
    out = out_dir or (root / ".wde" / "discovery" / "render")
    out.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {
        "ok": False,
        "playwright": False,
        "signature_visible_desktop": False,
        "signature_visible_mobile": False,
        "interaction_ok": False,
        "captures": [],
        "error": "",
        "target": target,
    }

    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError:
        result["error"] = "playwright not installed"
        return result

    # Resolve file:// for local HTML
    nav = target
    if not target.startswith("http://") and not target.startswith("https://"):
        p = Path(target)
        if not p.is_absolute():
            p = (root / target).resolve()
        if not p.is_file():
            result["error"] = f"HTML not found: {p}"
            return result
        nav = p.as_uri()

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 800})
                page.goto(nav, wait_until="domcontentloaded", timeout=15000)
                result["playwright"] = True

                # Prefer exact machine contract selector — avoid loose [class*="signature"]
                selectors = []
                if signature_id:
                    selectors.extend(
                        [
                            f"[data-wde-signature='{signature_id}']",
                            f"[data-wde-signature=\"{signature_id}\"]",
                            f"#{signature_id}",
                            f".{signature_id}",
                        ]
                    )
                # No broad signature substring fallbacks

                loc = None
                used_sel = ""
                for sel in selectors:
                    try:
                        candidate = page.locator(sel).first
                        if candidate.count() > 0:
                            loc = candidate
                            used_sel = sel
                            break
                    except Exception:  # noqa: BLE001
                        continue

                before_box = None
                before_text = ""
                if loc is not None:
                    try:
                        result["signature_visible_desktop"] = bool(loc.is_visible())
                        before_box = loc.bounding_box()
                        before_text = (loc.inner_text(timeout=1000) or "")[:200]
                        result["selector_used"] = used_sel
                        if before_box:
                            area = float(before_box.get("width", 0)) * float(
                                before_box.get("height", 0)
                            )
                            result["visible_area_desktop"] = area
                            if area < 400:
                                result["signature_visible_desktop"] = False
                                result["error"] = f"visible area too small: {area}"
                    except Exception as e:  # noqa: BLE001
                        result["signature_visible_desktop"] = False
                        result["error"] = f"visibility: {e}"[:200]

                    # Interaction: require measurable change when possible
                    try:
                        loc.hover(timeout=2000)
                        loc.click(timeout=2000, force=True)
                        page.wait_for_timeout(150)
                        after_box = loc.bounding_box()
                        after_text = (loc.inner_text(timeout=1000) or "")[:200]
                        changed = False
                        if before_text != after_text:
                            changed = True
                        if before_box and after_box:
                            if abs(before_box.get("y", 0) - after_box.get("y", 0)) > 1:
                                changed = True
                            if abs(before_box.get("width", 0) - after_box.get("width", 0)) > 1:
                                changed = True
                        # Accept interaction if no error even when static (button click)
                        result["interaction_ok"] = True
                        result["interaction_changed"] = changed
                    except Exception as e:  # noqa: BLE001
                        result["interaction_ok"] = False
                        result["error"] = f"interaction: {e}"[:200]
                else:
                    result["error"] = (
                        "signature selector not found "
                        f"(expected data-wde-signature='{signature_id}')"
                    )

                desk = out / "desktop-1280.png"
                page.screenshot(path=str(desk), full_page=True)
                result["captures"].append(str(desk.relative_to(root)).replace("\\", "/"))

                # Mobile survival
                page.set_viewport_size({"width": 375, "height": 812})
                page.wait_for_timeout(200)
                if loc is not None:
                    try:
                        result["signature_visible_mobile"] = bool(loc.is_visible())
                    except Exception:  # noqa: BLE001
                        result["signature_visible_mobile"] = False

                mob = out / "mobile-375.png"
                page.screenshot(path=str(mob), full_page=True)
                result["captures"].append(str(mob.relative_to(root)).replace("\\", "/"))

                result["ok"] = (
                    result["signature_visible_desktop"]
                    and result["signature_visible_mobile"]
                    and len(result["captures"]) >= 2
                )
            finally:
                browser.close()
    except Exception as e:  # noqa: BLE001
        result["error"] = str(e)[:400]
        result["ok"] = False

    # Persist machine-readable probe
    probe_path = out / "probe.json"
    probe_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    result["probe_path"] = str(probe_path.relative_to(root)).replace("\\", "/")
    return result
