#!/usr/bin/env python3
"""wde — Web Design Enhancer V3 CLI (stdlib argparse, no agent-specific code)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from wde import __version__
from wde.core.project_context import ProjectContext, init_project


def _root(args: argparse.Namespace) -> Path:
    return Path(args.root).resolve()


def cmd_init(args: argparse.Namespace) -> int:
    root = _root(args)
    try:
        ctx = init_project(root, force=args.force)
    except FileExistsError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print("Use --force to reinitialize (destroys state).", file=sys.stderr)
        return 1
    state = ctx.load_state()
    print(f"WDE V{__version__} initialized in {ctx.wde}")
    print(f"phase: {state['phase']}")
    print(f"next:  {state['next_action']['summary']}")
    print(f"command: {state['next_action'].get('command', '')}")
    if state.get("degraded_mode"):
        print("NOTE: degraded_mode=true (no Playwright detected) — visual proofs limited")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    ctx = ProjectContext(_root(args))
    if not ctx.exists():
        print("ERROR: not a WDE project — run: wde init", file=sys.stderr)
        return 1
    state = ctx.refresh_invalidation()
    ctx.save_state(state)
    if args.json:
        print(json.dumps(state, indent=2, ensure_ascii=False))
    else:
        print(f"phase:     {state['phase']}")
        print(f"updated:   {state['updated_at']}")
        na = state.get("next_action") or {}
        print(f"next:      {na.get('summary')}")
        print(f"command:   {na.get('command')}")
        print(f"valid:     {len(state.get('valid_checks') or {})} checks")
        print(f"invalidated: {len(state.get('invalidated_checks') or [])}")
        if state.get("degraded_mode"):
            print("degraded:  yes")
        for b in state.get("blockers") or []:
            print(f"blocker:   [{b.get('code')}] {b.get('message')}")
    return 0


def cmd_next(args: argparse.Namespace) -> int:
    ctx = ProjectContext(_root(args))
    if not ctx.exists():
        print("ERROR: not a WDE project — run: wde init", file=sys.stderr)
        return 1
    state = ctx.refresh_invalidation()
    ctx.save_state(state)
    na = state.get("next_action") or {}
    if args.json:
        print(json.dumps(na, indent=2, ensure_ascii=False))
    else:
        print(na.get("command") or na.get("summary") or "wde doctor")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    ctx = ProjectContext(_root(args))
    issues = ctx.doctor()
    if ctx.exists():
        state = ctx.refresh_invalidation()
        ctx.save_state(state)
        caps = state.get("capabilities") or ctx.detect_capabilities()
    else:
        caps = ctx.detect_capabilities()
    if args.json:
        print(json.dumps({"issues": issues, "capabilities": caps}, indent=2))
    else:
        print(f"capabilities: {json.dumps(caps)}")
        if not issues:
            print("doctor: OK")
        for i in issues:
            print(f"[{i['code']}] {i['message']}")
            if i.get("remediation"):
                print(f"  → {i['remediation']}")
    return 1 if issues else 0


def cmd_transition(args: argparse.Namespace) -> int:
    """REMOVED from public surface — phase jumps without domain events are forbidden."""
    print(
        "ERROR: `wde transition` was removed from the public CLI.\n"
        "Phases advance only via domain events:\n"
        "  wde validate intent|research|experience|design|lock\n"
        "  wde run static|mechanical|browser|visual|…\n"
        "  wde deliver-check\n"
        "  wde review\n"
        "Internal tests may call wde.core.state_machine.apply_transition in-process.",
        file=sys.stderr,
    )
    return 2


def cmd_version(_: argparse.Namespace) -> int:
    print(__version__)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    """Run a check profile (static / mechanical / browser / deliver)."""
    from wde.core.runner import run_profile
    from wde.reporting.console import print_results
    from wde.reporting.json_report import build_report, write_report

    ctx = ProjectContext(_root(args))
    if not ctx.exists():
        print("ERROR: not a WDE project — run: wde init", file=sys.stderr)
        return 1
    profile = args.profile
    results = run_profile(ctx, profile, url=args.url)
    state = ctx.load_state()
    report = build_report(results=results, phase=state.get("phase", ""), root=str(ctx.root))
    report_path = write_report(ctx.wde / "reports" / f"run-{profile}.json", report)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_results(results)
        print(f"report: {report_path}")

    blocking = any(r.blocks_delivery for r in results)
    return 1 if blocking else 0


def cmd_discover(args: argparse.Namespace) -> int:
    """Creative Discovery: interpret → research receipts → territories → contracts."""
    from wde.discovery.orchestrator import run_discovery

    root = _root(args)
    request = (args.request or "").strip()
    if not request and args.request_file:
        request = Path(args.request_file).read_text(encoding="utf-8", errors="replace").strip()
    if not request:
        print(
            "ERROR: provide --request \"…\" or --request-file path",
            file=sys.stderr,
        )
        return 2

    result = run_discovery(
        root,
        request,
        force_init=bool(args.force_init),
        try_getdesign=not bool(args.skip_getdesign),
    )
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    else:
        status = "OK" if result.ok else "FAIL"
        print(f"discover: {status}")
        print(f"artifacts: {result.artifact_dir}")
        print(f"receipts:  {len(result.receipt_paths)}")
        print(f"territories: {len(result.territories)}")
        if result.selection:
            print(f"winner: {result.selection.get('winner_name')} ({result.selection.get('winner_id')})")
        for name in result.contracts:
            print(f"  wrote {name}")
        for e in result.errors:
            print(f"  error: {e}", file=sys.stderr)
        print("next: wde validate intent  (then wde validate research)")
    return 0 if result.ok else 1


def cmd_validate(args: argparse.Namespace) -> int:
    from wde.domains.contracts import (
        apply_validation_transition,
        validate_design,
        validate_experience,
        validate_intent,
        validate_lock,
        validate_research,
    )

    ctx = ProjectContext(_root(args))
    if not ctx.exists():
        print("ERROR: not a WDE project — run: wde init", file=sys.stderr)
        return 1

    target = args.target
    # architecture is an alias of experience (UX / IA contract)
    validators = {
        "intent": validate_intent,
        "research": validate_research,
        "experience": validate_experience,
        "architecture": validate_experience,
        "design": validate_design,
        "lock": validate_lock,
    }
    if target not in validators:
        print(f"ERROR: unknown target {target}", file=sys.stderr)
        return 2
    # architecture is an alias of experience for the state machine event
    event_target = "experience" if target == "architecture" else target
    report = validators[target](ctx.root)
    apply_validation_transition(ctx, event_target, report)
    state = ctx.load_state()

    payload = {"validation": report.to_dict(), "phase": state.get("phase")}
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        status = "OK" if report.ok else "FAIL"
        print(f"validate {target}: {status}")
        for i in report.issues:
            print(f"  [{i.severity}] {i.code}: {i.message}")
            if i.remediation:
                print(f"    → {i.remediation}")
        print(f"phase: {state.get('phase')}")
        print(f"next:  {(state.get('next_action') or {}).get('command')}")
    return 0 if report.ok else 1


def cmd_report(args: argparse.Namespace) -> int:
    from wde.reporting.consolidate import write_consolidated

    ctx = ProjectContext(_root(args))
    if not ctx.exists():
        print("ERROR: not a WDE project — run: wde init", file=sys.stderr)
        return 1
    state = ctx.refresh_invalidation()
    ctx.save_state(state)
    paths = write_consolidated(ctx.root, state, ctx.load_project())
    report = paths["report"]
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"consolidated: {paths['json']}")
        print(f"human:        {paths['md']}")
        print(f"phase:        {report.get('phase')}")
        print(f"delivery_safe:{report.get('integrity', {}).get('delivery_safe')}")
        if report.get("integrity", {}).get("forged_ready_without_checks"):
            print("WARN: READY_TO_DELIVER without valid_checks")
    return 0


def cmd_benchmark(args: argparse.Namespace) -> int:
    from wde.benchmark.runner import run_benchmark

    tasks = None
    if args.task:
        tasks = [args.task]
    keep = Path(args.keep_dir) if args.keep_dir else None
    report = run_benchmark(task_ids=tasks, keep_dir=keep, corpus=bool(args.corpus))
    # Persist under cwd .wde if present, else scratch-like cwd
    out_root = _root(args)
    out_dir = out_root / ".wde" / "reports"
    if not (out_root / ".wde").is_dir():
        out_dir = out_root / "benchmark-results"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "benchmark-smoke.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        ps = report.get("procedural_score") or {}
        print(f"benchmark smoke: {ps.get('passed_flags')}/{ps.get('total_flags')} procedural flags")
        print(f"rate: {ps.get('rate')}")
        print(f"authorizes_delivery: {report.get('authorizes_delivery')}")
        for t in report.get("tasks") or []:
            print(f"  - {t.get('task_id')}: phase={t.get('phase')}")
        print(f"report: {path}")
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    """Emit independent judge package; optionally process visual + aesthetic evidence."""
    from wde.core.review import emit_review_package, process_review
    from wde.reporting.console import print_results
    from wde.checks.base import CheckResult

    ctx = ProjectContext(_root(args))
    if not ctx.exists():
        print("ERROR: not a WDE project — run: wde init", file=sys.stderr)
        return 1

    if args.emit_package:
        emitted = emit_review_package(ctx, url=args.url, run_audit=not args.skip_audit)
        if args.json:
            print(json.dumps(emitted, indent=2, ensure_ascii=False))
        else:
            print("Review package emitted (judge must write verdict — builder must not self-score).")
            print(f"  package: {emitted.get('package_path')}")
            print(f"  prompt:  {emitted.get('prompt_path')}")
            print(f"  audit:   {emitted.get('audit_dir')}")
            if not emitted.get("probe_ok"):
                print("  WARN: URL not reachable — start dev server before audit")
        return 0 if emitted.get("probe_ok") or args.skip_audit else 1

    out = process_review(ctx, url=args.url, emit_only=False)
    if args.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        print(f"package: {out.get('emitted', {}).get('package_path')}")
        results = [
            CheckResult(
                check_id=r["check_id"],
                status=r["status"],
                severity=r.get("severity", "blocking"),
                category=r.get("category", ""),
                summary=r.get("summary", ""),
                findings=[],
            )
            for r in (out.get("results") or [])
            if isinstance(r, dict)
        ]
        if results:
            print_results(results)
        print(f"independence: {out.get('independence')}")
        print(f"phase: {out.get('phase')}")
        if out.get("independence") in {None, "weak", "unavailable"}:
            print("NOTE: delivery not fully authorized without medium/strong independent review")
    # Exit 0 only if ready or visual path clean
    state = ctx.load_state()
    if state.get("phase") == "READY_TO_DELIVER":
        return 0
    # package emitted is success for workflow even if aesthetic pending
    return 0 if out.get("emitted") else 1


def cmd_migrate_v2(args: argparse.Namespace) -> int:
    from wde.core.migrate_v2 import migrate_v2

    report = migrate_v2(_root(args), force=args.force)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"migrate-v2 → phase={report.get('phase')}")
        for a in report.get("actions") or []:
            print(f"  action: {a}")
        for w in report.get("warnings") or []:
            print(f"  warn: {w}")
        if report.get("suggested_next"):
            print(f"  next: {report['suggested_next']}")
        print("NOTE: never auto-marks READY_TO_DELIVER — re-run all checks")
    return 0


def cmd_deliver_check(args: argparse.Namespace) -> int:
    """Re-hash sources, re-run mechanical checks, reject stale/forged evidence."""
    from wde.core.runner import deliver_check
    from wde.reporting.console import print_results
    from wde.reporting.json_report import build_report, write_report

    ctx = ProjectContext(_root(args))
    if not ctx.exists():
        print("ERROR: not a WDE project — run: wde init", file=sys.stderr)
        return 1

    ok, blockers, results = deliver_check(ctx, url=args.url)
    state = ctx.load_state()
    report = build_report(results=results, phase=state.get("phase", ""), root=str(ctx.root))
    report["deliver_ok"] = ok
    report["blockers"] = blockers
    report_path = write_report(ctx.wde / "reports" / "deliver-check.json", report)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_results(results)
        if ok:
            print("DELIVER-CHECK: mechanical evidence OK (visual/independent still required for READY_TO_DELIVER)")
            print(f"phase: {state.get('phase')}")
        else:
            print("DELIVER-CHECK: BLOCKED")
            for b in blockers:
                print(f"  - {b}")
        print(f"report: {report_path}")

    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="wde",
        description="Web Design Enhancer V3 — evidence-driven quality orchestrator",
    )
    p.add_argument("--version", action="store_true", help="Print version")

    # Shared parent so both `wde --root . status` and `wde status --root .` work
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=".", help="Project root (default: cwd)")

    sub = p.add_subparsers(dest="cmd")

    s = sub.add_parser("init", parents=[common], help="Initialize .wde control plane")
    s.add_argument("--force", action="store_true")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser(
        "discover",
        parents=[common],
        help="Creative Discovery: vague request → research receipts → 3 territories → contracts",
    )
    s.add_argument("--request", default="", help="Vague product/site request text")
    s.add_argument("--request-file", default=None, help="Read request text from file")
    s.add_argument(
        "--force-init",
        action="store_true",
        help="Force re-init .wde if needed",
    )
    s.add_argument(
        "--skip-getdesign",
        action="store_true",
        help="Do not call npx getdesign (offline CI)",
    )
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_discover)

    s = sub.add_parser(
        "status",
        parents=[common],
        help="Show phase + next action (refreshes invalidation)",
    )
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_status)

    s = sub.add_parser("next", parents=[common], help="Print only the next authorized command")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_next)

    s = sub.add_parser("doctor", parents=[common], help="Environment + integrity diagnostics")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_doctor)

    # `transition` intentionally NOT registered — public phase walking is forbidden.
    # Legacy invocations hit unknown-command or we keep a stub that always errors:
    s = sub.add_parser(
        "transition",
        parents=[common],
        help="REMOVED — use validate/run/review domain events (always fails)",
    )
    s.add_argument("to_phase", nargs="?", default="")
    s.add_argument("--evidence-id", default="")
    s.add_argument("--force", action="store_true")
    s.set_defaults(func=cmd_transition)

    s = sub.add_parser(
        "run",
        parents=[common],
        help="Run a check profile: static | mechanical | browser | discovery | deliver | full",
    )
    s.add_argument(
        "profile",
        nargs="?",
        default="static",
        choices=[
            "static",
            "mechanical",
            "browser",
            "visual",
            "wow",
            "discovery",
            "deliver",
            "full",
        ],
    )
    s.add_argument("--url", default=None, help="Override project.local_url (browser checks)")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_run)

    s = sub.add_parser(
        "validate",
        parents=[common],
        help="Validate intent | research | experience | design | lock",
    )
    s.add_argument(
        "target",
        choices=["intent", "research", "experience", "architecture", "design", "lock"],
    )
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_validate)

    s = sub.add_parser(
        "deliver-check",
        parents=[common],
        help="Re-run mechanical checks; block on stale/forged evidence",
    )
    s.add_argument("--url", default=None)
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_deliver_check)

    s = sub.add_parser(
        "migrate-v2",
        parents=[common],
        help="Import V2 artifacts into .wde (never marks ready-to-deliver)",
    )
    s.add_argument("--force", action="store_true")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_migrate_v2)

    s = sub.add_parser(
        "report",
        parents=[common],
        help="Consolidate evidence + reports under .wde/reports/consolidated.*",
    )
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_report)

    s = sub.add_parser(
        "benchmark",
        parents=[common],
        help="Run benchmark (smoke by default; --corpus for 12 tasks; never auto-delivers)",
    )
    s.add_argument("--task", default=None, help="Single task id")
    s.add_argument("--corpus", action="store_true", help="Run full 12-task catalog")
    s.add_argument("--keep-dir", default=None, help="Directory to keep task workspaces")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_benchmark)

    s = sub.add_parser(
        "review",
        parents=[common],
        help="Emit independent visual review package; process verdict if present",
    )
    s.add_argument("--url", default=None)
    s.add_argument(
        "--emit-package",
        action="store_true",
        help="Only emit judge package + optional visual_audit (no state advance)",
    )
    s.add_argument(
        "--skip-audit",
        action="store_true",
        help="With --emit-package, do not run visual_audit.py",
    )
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_review)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "version", False) and not args.cmd:
        return cmd_version(args)
    if not args.cmd:
        parser.print_help()
        return 2
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
