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

Not to mention best practices and new tools are released weekly and you can't keep up.

All you want is to be as productive as possible with your budget, and be able to sleep well at night.

**This is where Flux comes in.**

---

## What Flux Does

Flux gives you a **structured workflow** based on how software is actually built—so you stop pulling your hair out.

### The Workflow

Instead of jumping straight into code and watching the agent go off the rails:

1. **Interview** — Flesh out the feature first. What are the edge cases? What decisions need to be made? Thinking through requirements upfront prevents chaos later.

2. **Plan** — Break down into dependency-aware tasks. Flux creates tasks in `.flux/` with clear scope, so you always know what's next.

3. **Implement** — Execute tasks one at a time with automatic context reload. No forgotten requirements.

4. **Review** — Built-in review step catches issues before they compound.

### Drift Protection

Documentation drift is your worst enemy on large projects with AI agents. Code changes but specs don't. Future tasks reference outdated assumptions.

Flux runs drift checks after every task completion—verifying specs match implementation and updating future tasks if needed. Another pass runs at epic completion to catch anything that slipped through.

Your documentation stays aligned. Always.

### Tool Discovery

Flux also analyzes your **actual coding sessions** to find friction—then recommends specific tools that would help:

- MCPs, CLI tools, skills, workflow patterns
- Matched to your project type and detected pain points
- Only recommends when there's actual friction (not tool spam)

```
/flux:improve
```

Reads your session history, detects frustration patterns, checks what you already have, shows what's missing.

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

## Quick Demo

Try this in any active project:

```bash
/flux:improve
```

In one run you'll see:
- what Flux detected in your environment
- what friction showed up in recent sessions
- exactly which fixes/tools map to those issues

If you want live community discoveries too:

```bash
/flux:improve --discover
```

If you want full matching rationale (signals + gaps):

```bash
/flux:improve --explain
```

---

## Install

### Claude Code

```bash
# From marketplace
/plugin marketplace add Nairon-AI/flux
/plugin install flux@nairon-flux

# Or manual
git clone https://github.com/Nairon-AI/flux.git ~/.claude/plugins/flux
```

If marketplace isn't available in your CLI version, use the manual install path.

### OpenCode

```bash
/plugin marketplace add Nairon-AI/flux
/plugin install flux@nairon-flux
```

### First-Time Setup

After installing, initialize Flux in your project:

```bash
/flux:setup
```

This creates `.flux/` in your project and sets up the task tracking system. Run once per project.

Then run:

```bash
/flux:improve
```

Note: first run may take a few seconds while Flux clones the recommendations database into `~/.flux/recommendations`.

### Support

- macOS: supported
- Linux: supported
- Windows: use WSL (best-effort)

Flux is local-first. It also provides optional discovery mode (`--discover`) for live external search.

### Dependency Setup

Flux checks for required tools during execution and tells you what to install when something is missing.
You can start with `/flux:setup` and `/flux:improve` directly.

---

## Quick Start

Here's how to use Flux from install to daily usage:

### 1. Install & Setup (once)

```bash
/plugin install flux@nairon-flux   # Install plugin
/flux:setup                         # Initialize in your project
```

### 2. Start a Feature

```bash
/flux:interview Add user notifications   # Optional: flesh out requirements
/flux:plan Add user notifications         # Break into tasks
```

### 3. Build It

```bash
/flux:work fn-1.1                         # Execute first task
/flux:work fn-1.2                         # Next task (auto-reloads context)
# ... continue until done
```

### 4. Find Better Tools (anytime)

```bash
/flux:improve                             # Analyze sessions, get recommendations
```

---

## Commands

| Command | What it does |
|---------|--------------|
| `/flux:setup` | Optional local install of `fluxctl` and project docs |
| `/flux:improve` | Analyze sessions, detect friction, and recommend improvements |
| `/flux:plan <idea|epic>` | Build structured execution plan |
| `/flux:work <task|epic>` | Execute tasks with context reload + checks |
| `/flux:interview <id|file>` | Deep requirements interview for epic/task/spec |
| `/flux:prime` | Agent readiness assessment + guided fixes |
| `/flux:sync <id>` | Sync downstream task specs after drift |
| `/flux:plan-review <epic>` | Carmack-level plan quality review |
| `/flux:impl-review` | Carmack-level implementation review |
| `/flux:epic-review <epic>` | Verify epic completion against spec |
| `/flux:ralph-init` | Scaffold Ralph autonomous harness |
| `/flux:uninstall` | Remove Flux files from project |

For full options and examples, see `docs/commands-reference.md`.

---

## How It Works

### Task Tracking

Flux maintains tasks in `.flux/`:
- Epics: `.flux/epics/fn-N-slug.json`
- Tasks: `.flux/tasks/fn-N-slug.M.json`
- Specs: `.flux/specs/fn-N-slug.md`

Each task has clear scope, dependencies, and acceptance criteria. `/flux:work` reloads this context before each task—nothing drifts.

### Tool Discovery

1. **Extracts** your session history (OpenCode SQLite or Claude Code JSONL)
2. **Detects friction** — 70+ patterns: user frustration, tool errors, agent confusion
3. **Scans your setup** — OS, CLI tools, MCPs, apps, repo configs
4. **Matches gaps** to 30+ curated recommendations with pricing
5. **Asks** which improvements to apply
6. **Implements** — installs tools, adds AGENTS.md rules, configures hooks

Preferences saved to `.flux/preferences.json`.

---

## FAQ

### Privacy & Data

**What data does Flux read?**

- Your repo structure (package.json, config files, directories)
- Installed MCPs from `~/.mcp.json`
- Optionally: Claude Code session files from `~/.claude/projects/`

**Is any data sent externally?**

By default, analysis runs locally. Network access is used to fetch the recommendations repo.

If you run `/flux:improve --discover`, Flux also sends search queries to Exa/Twitter APIs (using your keys) to find optional community discoveries.

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

## Vision: Engineering Observability

Today, Flux helps individual engineers work more effectively. Tomorrow, it becomes observability for your entire engineering organization.

**What's coming:**

- **Team Dashboard** — See where every engineer is in the SDLC at any moment. Interview, planning, implementing, reviewing—all visible.
- **Cycle Time Analytics** — Track how long features take from idea to shipped. Identify bottlenecks before they become problems.
- **Token Usage Monitoring** — Understand AI costs across your engineering department.
- **Org-Wide Recommendations** — When one engineer discovers a tool that works, roll it out to everyone. No more knowledge silos.
- **Shared SDLC Evolution** — As the community discovers better workflows, everyone evolves together.

The goal: **every engineer as effective as your best engineer**. No bottlenecks. No one left behind.

Flux will grow with the industry. The SDLC framework evolves as we collectively learn better ways to build software with AI.

*Interested in early access for your team? [Get in touch](https://github.com/Nairon-AI/flux/issues).*

---

## Docs

- `docs/commands-reference.md` - full command reference
- `docs/architecture.md` - command -> skill -> script architecture
- `docs/recommendation-format.md` - recommendation YAML format guide
- `docs/troubleshooting.md` - common issues and fixes

---

## License

MIT
