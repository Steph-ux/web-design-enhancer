# Web Design Enhancer Pro

**Eliminate AI visual improvisation — deliver clean, precise, professional interfaces.**

A tool-agnostic skill that enforces a machine-verifiable `DESIGN.md` contract. Runs in any AI coding agent (Claude Code, Codex, OpenCode, Antigravity, or a plain terminal). Every rule is validated by a deterministic Python script before code is generated, so the agent cannot produce "AI slop" patterns — decorative emojis, cliche gradients, glassmorphism, improvised dark modes, broken 8px grids, WCAG violations, Three.js antipatterns, etc.

See [`docs/README.md`](./docs/README.md) for the full technical reference (philosophy, 5-phase workflow, scripts, antipatterns, CI/CD, delivery checklist).

---

## Install

Clone the repo, install Python dependencies:

```bash
git clone https://github.com/Steph-ux/web-design-enhancer.git
cd web-design-enhancer
pip install -r requirements.txt
```

**Prerequisites**: Python 3.10+. No LLM API key required — scripts are deterministic.

### Per AI tool

| Tool | Install location | How to invoke |
| :--- | :--- | :--- |
| **Claude Code** | `~/.claude/skills/web-design-enhancer-pro/` | Auto-discovered. Use `/web-design-enhancer` or let Claude detect it |
| **Codex** (OpenAI CLI) | Clone anywhere | `codex --context ./web-design-enhancer-pro "validate my DESIGN.md"` |
| **OpenCode** | Clone or add as submodule in the project | `/add SKILL.md` then run `python3 scripts/...` |
| **Antigravity** (Google) | Clone into the workspace | Load `SKILL.md` as agent context; run scripts in the built-in terminal |
| **Any other agent / plain shell** | Clone anywhere | Run the scripts directly with `python3 scripts/...` |

---

*Built to turn AI-generated code into exceptional design.*
