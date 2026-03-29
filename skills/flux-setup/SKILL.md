---
name: flux-setup
description: Optional local install of fluxctl CLI and AGENTS.md/legacy CLAUDE.md instructions. Use when user runs /flux:setup. Triggers on literal `/flux:setup`.
user-invocable: false
---

# Flux Setup (Optional)

Install fluxctl locally and add instructions to project docs. **Fully optional** - Flux works without this local setup, but this is the preferred path for Codex-first repos.

## Session Phase Tracking

On entry, set the session phase:
```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
[ ! -d "$PLUGIN_ROOT/scripts" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
$FLUXCTL session-phase set setup
```

On completion, reset:
```bash
$FLUXCTL session-phase set idle
```

## Benefits

- `fluxctl` accessible from command line (add `.flux/bin` to PATH)
- Codex reads `AGENTS.md`, and Flux can keep a legacy `CLAUDE.md` mirror when needed
- Works without any Claude-specific install path
- **Optional** recommended MCP servers (user chooses which to install, all free):
  - **Context7** — no more hallucinated APIs, up-to-date library docs in every prompt
  - **Exa** — fastest AI web search, real-time research without leaving your session
  - **GitHub** — PRs, issues, actions directly from the agent, no context switching
- **Optional** additional MCP:
  - **Firecrawl** — scrape websites and parse PDFs into LLM-ready markdown
- **Optional** recommended CLI tools:
  - **jq** — JSON parsing for scripts and API output
  - **fzf** — fuzzy finder for terminal workflows
  - **Lefthook** — fast pre-commit hooks
  - **Agent Browser** — checklist-driven browser QA with snapshots and screenshots
  - **Expect** — diff-driven browser QA, AI generates test plans from git changes
  - **React Doctor** — React code health scan with an opt-in pre-commit gate for changed files
  - **CLI Continues** — resume/switch session context across agent CLIs
- **Optional** recommended desktop apps (OS-aware prompts in setup):
  - **Superset** — primary orchestrator for parallel Codex sessions and cross-lab review worktrees
  - **CodexBar** — menu bar visibility into Codex and Claude Code subscription usage/reset windows
  - **Raycast** — launcher/snippets/clipboard productivity layer
  - **Wispr Flow** — voice-to-text acceleration (macOS)
  - **Granola** — AI meeting notes companion (macOS/Windows)
- **Optional** additional agent skill:
  - **UI Skills** — accessibility/motion/metadata/design polish for frontend output
  - **Dejank** — React visual-jank detection and diagnosis (18 anti-patterns + runtime workflows)
  - **Taste Skill** — anti-generic design taste layer for better UI generation
  - **Semver Changelog** — automated semantic changelog/release-note hygiene
  - **Diffity Tour** — interactive browser-based walkthroughs for understanding unfamiliar codepaths and features, with optional `diffity` CLI install during setup so tours work immediately
  - **Find Skills (Vercel)** — bootstrap for Vercel's skill catalog in repo-local skill folders
  - **X Research Skill** — structured X/Twitter research and summarization
- **Optional** task tracker integration:
  - **Linear** — installs the [Linear CLI skill](https://github.com/schpet/linear-cli) into repo-local skill folders so the agent can manage issues and projects directly. Team gets visibility without touching the CLI.
- **Optional** auto-fix (cloud PR babysitting):
  - **Claude Auto-Fix** — after Flux submits a PR, Claude can watch it remotely in the cloud, automatically fixing CI failures and addressing review comments. This remains an optional secondary workflow and requires the [Claude GitHub App](https://github.com/apps/claude).
- **Smart conflict detection** — detects existing similar tools and asks how to handle (keep, switch, both)

## Workflow

**CRITICAL: Read the ENTIRE [workflow.md](workflow.md) before starting execution.** The workflow is ~2000 lines across 10+ steps. The most common failure is reading the first few steps, starting execution, and never reaching the configuration questions (Step 6), business context (Step 5b), or docs block update.

A step completion checklist and verification gate at the end of workflow.md will catch skipped steps — but prevention is better than detection. Read it all first.

## Notes

- **Fully optional** - standard plugin usage works without local setup
- Copies scripts (not symlinks) for portability across environments
- Safe to re-run - will detect existing setup and offer to update
- All MCPs and project state install project-local (`.mcp.json`, `.flux/`, `.flux/brain/`). Supported skill installs go into repo-local `.codex/skills/` / `.claude/skills/`
- React-only tools and skills should only be offered when the repo actually uses React or a React-based framework
- After setup + restart, run `/flux:prime` first before feature work
- After implementation/review, run `/flux:reflect` at session end

## Gotchas

- Setup is project-local by design. Never "helpfully" spill config into global agent settings to make one repo work.
- Re-runs should refresh or reconcile existing tools, not duplicate them or clobber user choices without confirmation.
- Installing optional MCPs, skills, or desktop tools can require restart boundaries. Tell the user when a restart is actually needed.

---

## Update Check (End of Command)

**ALWAYS run at the very end of /flux:setup execution:**

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
[ ! -d "$PLUGIN_ROOT/scripts" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
UPDATE_JSON=$("$PLUGIN_ROOT/scripts/version-check.sh" 2>/dev/null || echo '{"update_available":false}')
UPDATE_AVAILABLE=$(echo "$UPDATE_JSON" | jq -r '.update_available')
LOCAL_VER=$(echo "$UPDATE_JSON" | jq -r '.local_version')
REMOTE_VER=$(echo "$UPDATE_JSON" | jq -r '.remote_version')
UPDATE_CMD=$(echo "$UPDATE_JSON" | jq -r '.update_command // "Update Flux from the same source you installed it from, then restart your agent session."')
```

**If update available**, append to output:

```
---
Flux update available: v${LOCAL_VER} → v${REMOTE_VER}
${UPDATE_CMD}
---
```
