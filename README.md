<div align="center">

# Flux

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Plugin-blueviolet)](https://claude.ai/code)

**Your AI workflow has gaps. Flux finds them.**

</div>

---

## The Problem

You're using AI agents, but something's off:

- You keep re-explaining the same context
- The agent tries the same broken approach 5 times
- You discover a tool that would've saved hours—after the fact
- Requirements drift mid-session and nobody notices

These aren't model failures. They're **process failures**.

---

## What Flux Does

Flux analyzes your **actual coding sessions** to find friction—then recommends specific tools that would have helped.

```
/flux:improve
```

That's it. Flux reads your session history, detects patterns of frustration, checks what you already have installed, and shows you exactly what's missing.

---

## Example Output

```
Step 1/4: Environment Detection

  Repo: my-app (javascript, next, typescript)
  MCPs: 2 installed (playwright, github)
  CLI: jq, fzf, eslint
  Hooks: none    Linter: yes

Step 2/4: Session Analysis (12 sessions, 847 messages)

  Friction detected:
    api_hallucination: 5 (model used APIs that don't exist)
    lint_errors: 3 (caught in CI, not locally)
    context_forgotten: 4 (re-explained same thing)

Step 3/4: Recommendations

  Based on your friction:

  1. [MCP] context7 (free)
     Up-to-date library docs directly from source
     → Addresses: api_hallucination (5 errors)

  2. [CLI] lefthook (free)
     Git hooks manager - catch errors before CI
     → Addresses: lint_errors (3 CI failures)

  3. [MCP] supermemory (free)
     Persistent memory across sessions
     → Addresses: context_forgotten (4 re-explanations)

Step 4/4: Install

  Select: [1,2,3] or 'all' or 'skip'
```

---

## Install

### Claude Code (Marketplace)

```bash
/plugin marketplace add Nairon-AI/flux
/plugin install flux@nairon-flux
```

### Claude Code (Manual)

```bash
# Clone to plugins directory
git clone https://github.com/Nairon-AI/flux.git ~/.claude/plugins/flux

# Restart Claude Code, then verify
/flux:improve --detect
```

### OpenCode

```bash
/plugin marketplace add Nairon-AI/flux
/plugin install flux@nairon-flux
```

### Manual (Any Platform)

```bash
git clone https://github.com/Nairon-AI/flux.git ~/.flux/plugin
# Add to your AI tool's plugin path
```

---

## Commands

| Command | Description |
|---------|-------------|
| `/flux:improve` | Analyze sessions, find gaps, get recommendations |
| `/flux:improve --detect` | Just show what's installed (no recommendations) |
| `/flux:improve --dismiss X` | Never recommend X again |
| `/flux:plan` | Break a feature into dependency-aware tasks |
| `/flux:work` | Execute a task with automatic context reload |

---

## How It Works

1. **Extracts** your session history (OpenCode SQLite or Claude Code JSONL)
2. **Detects friction** — 70+ patterns: user frustration, tool errors, agent confusion
3. **Scans your setup** — OS, CLI tools, MCPs, apps, repo configs
4. **Matches gaps** to 30+ curated recommendations with pricing
5. **Asks** which improvements to apply
6. **Implements** — installs tools, adds AGENTS.md rules, configures hooks

Preferences saved to `.flux/preferences.json` so dismissed items stay dismissed.

---

## Daily Usage

**Weekly check-in** — Run after a few coding sessions:
```
/flux:improve
```
Review what friction patterns emerged. Apply fixes that make sense.

**Before starting a feature** — Plan first:
```
/flux:plan Add dark mode toggle to settings
```
Creates tasks in `.flux/` with dependencies mapped out.

**Execute tasks** — One at a time with context reload:
```
/flux:work fx-1.1
```
Re-anchors to the plan before each task. Nothing drifts.

**Dismiss noise** — Tool not relevant to you?
```
/flux:improve --dismiss figma
```
Won't suggest it again.

---

## All Commands

| Command | Description |
|---------|-------------|
| **Core** | |
| `/flux:improve` | Analyze sessions and get recommendations |
| `/flux:plan <idea>` | Break a feature into tasks |
| `/flux:work <task-id>` | Execute a task with context reload |
| **Options** | |
| `/flux:improve --detect` | Show installed tools only |
| `/flux:improve --skip-sessions` | Skip session analysis |
| `/flux:improve --dismiss <name>` | Never recommend this tool |
| `/flux:improve --category <cat>` | Filter by: mcp, cli, plugin, skill, pattern |
| **Advanced** | |
| `/flux:setup` | Install fluxctl CLI locally |
| `/flux:prime` | Re-anchor to project context |
| `/flux:sync` | Sync tasks with git |

---

## FAQ

### Privacy & Data

**What data does Flux read?**

- Your repo structure (package.json, config files, directories)
- Installed MCPs from `~/.mcp.json`
- Optionally: Claude Code session files from `~/.claude/projects/`

**Is any data sent externally?**

No. Everything runs locally. The only network request is `git clone` to fetch the recommendations database on first run.

**How does session analysis work?**

Flux reads your Claude Code JSONL session files and looks for friction patterns:
- Tool errors and failures
- Repeated attempts at the same thing
- Knowledge gaps ("I don't know how to...")
- TypeScript/Python errors in tool outputs
- Agent confusion (apologies, retries)

You're asked for consent before any session files are read.

---

### Recommendations

**How are recommendations chosen?**

Flux only recommends tools when it detects **actual friction**. No friction = no recommendations.

Matching logic:
- `api_hallucination` errors → context7 (current docs)
- `css_issues` detected → frontend-optimized models
- `lint_errors` in output → oxlint, biome
- `ci_failures` → lefthook (pre-commit hooks)
- Context forgotten → supermemory

**Why am I getting no recommendations?**

Either you have no friction (great!) or:
- Session analysis was skipped
- You've dismissed all relevant tools
- Your setup already covers the gaps

Run `/flux:improve --detect` to see what Flux found.

**Can I see why a specific tool was recommended?**

Yes — each recommendation shows the friction signal that triggered it. Example:
```
context7 (MCP)
→ You had 5 api_hallucination errors - context7 provides current docs
```

**Where do recommendations come from?**

A curated database at [Nairon-AI/flux-recommendations](https://github.com/Nairon-AI/flux-recommendations). Currently 30+ tools across MCPs, CLI tools, apps, and workflow patterns.

**How do I suggest a tool?**

Open an issue on the [recommendations repo](https://github.com/Nairon-AI/flux-recommendations/issues).

---

### Troubleshooting

**"jq not found" error**

Install jq:
```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt install jq

# Fedora
sudo dnf install jq
```

**First run is slow**

On first run, Flux clones the recommendations database to `~/.flux/recommendations`. This takes a few seconds.

**No sessions found**

If you just installed Claude Code, you won't have session history yet. Run `/flux:improve --skip-sessions` to analyze just your repo structure, or wait until you've had a few coding sessions.

**Recommendation install failed**

Flux creates a snapshot before any changes. To rollback:
```bash
ls ~/.flux/snapshots/           # Find the snapshot
# Then restore manually or run:
/flux:improve --rollback <id>
```

**Windows support?**

Flux works best on macOS and Linux. Windows support via WSL is untested but should work.

---

### How It Detects Friction

Flux looks for 70+ patterns across three categories:

**User Frustration** (what you say)
- "still not working", "why is this", "again"
- "I already told you", "as I said before"
- "think harder", "you missed"

**Tool Output Errors** (compiler/runtime)
- TypeScript: `Property 'x' does not exist`
- Python: `AttributeError`, `ModuleNotFoundError`
- Build: `npm ERR!`, `exit code 1`

**Agent Confusion** (model struggling)
- "I apologize", "my mistake"
- "let me try a different approach"
- "I'm not sure how"

Each pattern maps to specific tool recommendations.

---

## License

MIT
