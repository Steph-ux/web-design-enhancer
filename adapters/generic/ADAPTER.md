# WDE generic adapter (any agent)

Works with any agent that can read files, run shell commands, and edit the project.

## Rules (non-negotiable)

1. Run `python -m wde.cli.main status --json` (or `wde status --json`) at session start and after every significant change.
2. Perform **only** the action in `next_action.command` / `next_action.summary`.
3. Never hand-edit `.wde/state.json` or write files under `.wde/evidence/`.
4. Never claim “gate passed” without the CLI printing success + an evidence file under `.wde/evidence/`.
5. Before any delivery claim, run `python -m wde.cli.main deliver-check` and, when available, visual review. If `degraded_mode` is true, say so explicitly — do not invent screenshots.

## Typical loop

```bash
python -m wde.cli.main init
python -m wde.cli.main status --json
python -m wde.cli.main next
# agent fills CREATIVE-BRIEF.md
python -m wde.cli.main validate intent
# pillars: search.py --persist + npx getdesign
python -m wde.cli.main validate experience
python -m wde.cli.main validate design
python -m wde.cli.main validate lock
# implement UI under STRUCTURAL-LOCK
python -m wde.cli.main run static
python -m wde.cli.main run browser --url http://localhost:5173
python -m wde.cli.main deliver-check
```

## Capabilities JSON (declare honestly)

```json
{
  "adapter": "generic",
  "capabilities": {
    "shell": true,
    "filesystem": true,
    "browser": false,
    "vision": false,
    "subagents": false,
    "hooks": false,
    "final_response_interception": false
  }
}
```

If browser/vision is false, delivery must be labeled **unverified** for visual independence.
