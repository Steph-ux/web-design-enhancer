#!/usr/bin/env python3
"""wde — Web Design Enhancer V3 CLI (stdlib argparse, no agent-specific code)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from wde import __version__
from wde.core.evidence import Evidence, write_evidence
from wde.core.project_context import ProjectContext, init_project
from wde.core.state_machine import apply_transition, can_transition


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
    """Internal/core transition — records evidence. Not for freehand model use."""
    ctx = ProjectContext(_root(args))
    if not ctx.exists():
        print("ERROR: not a WDE project", file=sys.stderr)
        return 1
    state = ctx.refresh_invalidation()
    to_phase = args.to_phase
    if not can_transition(state["phase"], to_phase) and not args.force:
        print(
            f"ERROR: illegal transition {state['phase']} → {to_phase}",
            file=sys.stderr,
        )
        return 1
    try:
        if args.force and not can_transition(state["phase"], to_phase):
            print("ERROR: --force cannot invent illegal edges", file=sys.stderr)
            return 1
        state = apply_transition(state, to_phase, evidence_id=args.evidence_id or "")
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    # Record a core evidence stub for the transition
    ev = Evidence(
        check_id=f"transition.{to_phase.lower()}",
        status="passed",
        executor="wde-core",
        source_hash=(state.get("hashes") or {}).get("SOURCE", ""),
        contract_hash=(state.get("hashes") or {}).get("DESIGN", ""),
        details={"from": state["history"][-1]["from_phase"], "to": to_phase},
    )
    path = write_evidence(ctx.wde / "evidence", ev)
    state.setdefault("valid_checks", {})[ev.check_id] = str(path.relative_to(ctx.root))
    ctx.save_state(state)
    print(f"transition OK → {to_phase}")
    print(f"evidence: {path}")
    return 0


def cmd_version(_: argparse.Namespace) -> int:
    print(__version__)
    return 0


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

    s = sub.add_parser(
        "transition",
        parents=[common],
        help="Apply a legal state transition (wde-core only; for tools/tests)",
    )
    s.add_argument("to_phase")
    s.add_argument("--evidence-id", default="")
    s.add_argument("--force", action="store_true", help="Unused guard — illegal edges still fail")
    s.set_defaults(func=cmd_transition)

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
