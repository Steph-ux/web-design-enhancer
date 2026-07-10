# Claude Code adapter

Extends **generic** (`adapters/generic/ADAPTER.md`).

1. Prefer loading `skill/SKILL.md` as the skill entry (thin).
2. After file edits, re-run `python -m wde.cli.main status --json`.
3. If hooks are available: `post-write` → status; `pre-stop` → `deliver-check`.
4. Visual independence: spawn a **fresh-context** subagent with screenshots only when MCP Playwright is available; tag reviewer honestly (`independent-clone` vs `self`).
5. Never instruct the judge to “confirm success”.
