# Codex / GPT adapter

Extends **generic**.

1. Put in repo instructions: always run `python -m wde.cli.main status --json` before coding.
2. Prefer short JSON CLI outputs (`--json`).
3. Do not depend on Claude skill format — CLI is source of truth.
4. If final-response interception is unavailable, still run `deliver-check` and refuse delivery language when exit code ≠ 0.
