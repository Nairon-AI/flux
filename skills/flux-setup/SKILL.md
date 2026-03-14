---
name: flux-setup
description: Optional local install of fluxctl CLI and CLAUDE.md/AGENTS.md instructions. Use when user runs /flux:setup.
user-invocable: false
---

# Flux Setup (Optional)

Install fluxctl locally and add instructions to project docs. **Fully optional** - flux works without this via the plugin.

## Benefits

- `fluxctl` accessible from command line (add `.flux/bin` to PATH)
- Other AI agents (Codex, Cursor, etc.) can read instructions from CLAUDE.md/AGENTS.md
- Works without Claude Code plugin installed
- **Optional** recommended MCP servers (user chooses which to install, all free):
  - **Context7** — no more hallucinated APIs, up-to-date library docs in every prompt
  - **Exa** — fastest AI web search, real-time research without leaving your session
  - **GitHub** — PRs, issues, actions directly in Claude, no context switching
- **Optional** additional MCP:
  - **Firecrawl** — scrape websites and parse PDFs into LLM-ready markdown
- **Optional** recommended CLI tools:
  - **jq** — JSON parsing for scripts and API output
  - **fzf** — fuzzy finder for terminal workflows
  - **Lefthook** — fast pre-commit hooks
  - **Agent Browser** — browser automation CLI for agent-driven UI QA
  - **CLI Continues** — resume/switch session context across agent CLIs
- **Optional** recommended desktop apps (OS-aware prompts in setup):
  - **Superset** — primary orchestrator for parallel Claude Code sessions using git worktrees
  - **Raycast** — launcher/snippets/clipboard productivity layer
  - **Wispr Flow** — voice-to-text acceleration (macOS)
  - **Granola** — AI meeting notes companion (macOS/Windows)
- **Optional** additional agent skill:
  - **UI Skills** — accessibility/motion/metadata/design polish for frontend output
  - **Taste Skill** — anti-generic design taste layer for better UI generation
  - **Semver Changelog** — automated semantic changelog/release-note hygiene
  - **Agent Skills (Vercel)** — broad reusable skills catalog
  - **X Research Skill** — structured X/Twitter research and summarization
- **Optional** task tracker integration:
  - **Linear** — installs the [Linear CLI skill](https://skills.sh/schpet/linear-cli/linear-cli) so the agent can manage issues and projects directly. Team gets visibility without touching the CLI.
- **Smart conflict detection** — detects existing similar tools and asks how to handle (keep, switch, both)

## Workflow

Read [workflow.md](workflow.md) and follow each step in order.

## Notes

- **Fully optional** - standard plugin usage works without local setup
- Copies scripts (not symlinks) for portability across environments
- Safe to re-run - will detect existing setup and offer to update
- All MCPs, skills, and config install project-local (`.mcp.json`, `.claude/skills/`, `.flux/`) — never touches global `~/.claude/settings.json`
- After setup + restart, run `/flux:prime` first before feature work
- After implementation/review, run `/flux:reflect` at session end

---

## Update Check (End of Command)

**ALWAYS run at the very end of /flux:setup execution:**

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}"
[ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
UPDATE_JSON=$("$PLUGIN_ROOT/scripts/version-check.sh" 2>/dev/null || echo '{"update_available":false}')
UPDATE_AVAILABLE=$(echo "$UPDATE_JSON" | jq -r '.update_available')
LOCAL_VER=$(echo "$UPDATE_JSON" | jq -r '.local_version')
REMOTE_VER=$(echo "$UPDATE_JSON" | jq -r '.remote_version')
```

**If update available**, append to output:

```
---
Flux update available: v${LOCAL_VER} → v${REMOTE_VER}
Run: /plugin uninstall flux@nairon-flux && /plugin install flux@nairon-flux
Then restart Claude Code for changes to take effect.
---
```
