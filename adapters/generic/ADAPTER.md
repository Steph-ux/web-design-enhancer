# WDE generic adapter (any agent)

Works with any agent that can read files, run shell commands, and edit the project.

## Rules (non-negotiable)

1. Run `wde status --json` (fallback: `python -m wde status --json`) at session start and after every significant change.
2. Perform **only** the action in `next_action.command` / `next_action.summary`.
3. Never hand-edit `.wde/state.json` or write files under `.wde/evidence/`.
4. Never claim “gate passed” without the CLI printing success + an evidence file under `.wde/evidence/`.
5. Before any delivery claim, run `wde deliver-check` and, when available, visual review. If `degraded_mode` is true, say so explicitly — do not invent screenshots.

## Typical loop

```bash
wde init
wde status --json
wde next
# Prefer discovery for vague briefs (writes contracts + research receipts):
wde discover --request "modern premium site for an independent hotel agency"
# or fill CREATIVE-BRIEF.md by hand, then:
wde validate intent
wde validate research   # accepts discovery receipts OR classic pillars
wde validate experience
wde validate design
wde validate lock
# implement UI under STRUCTURAL-LOCK
wde run static
wde deliver-check
wde review --emit-package --url http://localhost:5173
# judge writes audit-results/aesthetic-verdict.json (reviewer: independent|human)
wde review --url http://localhost:5173
wde run browser --url http://localhost:5173
# never: wde transition <phase>
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
