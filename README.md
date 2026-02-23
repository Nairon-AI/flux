<div align="center">

# N-bench

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Plugin-blueviolet)](https://claude.ai/code)

**Your AI workflow has gaps. N-bench finds them.**

</div>

---

## The Problem

You're using Claude Code, but something's off:

- There's no structure to your development process
- You keep re-explaining the same context
- The agent tries the same broken approach 5 times
- You discover a tool that would've saved hours—after the fact
- Requirements drift mid-session - you don't notice

These aren't model failures. They're **process failures**.

Not to mention best practices and new tools are released weekly on X, and you can't keep up.

All you want is to be as productive as possible without going homeless and finally get a good night's rest.

<p align="center">
  <img src="https://media1.tenor.com/m/KBShDXgDMsUAAAAC/green-mile-im-tired-boss.gif" alt="I'm tired, boss" width="400">
</p>

**This is where N-bench comes in.**

---

## What N-bench Does

N-bench gives you a **structured workflow** based on how software is actually built—so you stop pulling your hair out.

### The Workflow

Instead of jumping straight into code and watching the agent go off the rails:

1. **Quick Interview** — Get just enough to start (~5 min). What's the MVP? What's the riskiest unknown? You'll learn more as you build. Use `--deep` only for high-risk features.

2. **Plan** — Break down into small, atomic tasks. N-bench creates tasks in `.flux/` with clear scope. Each task should be 30-90 min of work.

3. **Build → Feel → Adapt** — Execute one task, then:
   - **Feel check**: Does it work? Does it feel right?
   - **Adapt**: Update the plan based on what you learned
   - Repeat

4. **Review** — Built-in review after each task catches issues before they compound.

### Drift Protection

Documentation drift is your worst enemy on large projects with AI agents. Code changes but specs don't. Future tasks reference outdated assumptions.

N-bench runs drift checks after every task completion—verifying specs match implementation and updating future tasks if needed. Another pass runs at epic completion to catch anything that slipped through.

You should not be manually updating Documentation. Delegate to Agents. Always.

### Tool Discovery

N-bench also analyzes your **actual coding sessions** to find friction—then recommends specific tools that would help:

- MCPs, CLI tools, skills, workflow patterns
- Matched to your project type and detected pain points
- Only recommends when there's actual friction (not tool spam)

```
/nbench:improve
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
/nbench:improve
```

In one run you'll see:
- what N-bench detected in your environment
- what friction showed up in recent sessions
- exactly which fixes/tools map to those issues

If you want live community discoveries too:

```bash
/nbench:improve --discover
```

If you want full matching rationale (signals + gaps):

```bash
/nbench:improve --explain
```

---

## Install

### Claude Code

```bash
# From marketplace
/plugin marketplace add Nairon-AI/n-bench
/plugin install flux@nairon-flux

# Or manual
git clone https://github.com/Nairon-AI/n-bench.git ~/.claude/plugins/flux
```

If marketplace isn't available in your CLI version, use the manual install path.

### OpenCode

```bash
/plugin marketplace add Nairon-AI/n-bench
/plugin install flux@nairon-flux
```

### First-Time Setup

After installing, initialize N-bench in your project:

```bash
/nbench:setup
```

This creates `.flux/` in your project, sets up task tracking, and bootstraps `claudeception` into `~/.claude/skills/claudeception` if missing. Run once per project.

Then run:

```bash
/nbench:improve
```

Note: first run may take a few seconds while N-bench clones the recommendations database into `~/.flux/recommendations`.

### Support

- macOS: supported
- Linux: supported
- Windows: use WSL (best-effort)

N-bench is local-first. It also provides optional discovery mode (`--discover`) for live external search.

### Dependency Setup

N-bench checks for required tools during execution and tells you what to install when something is missing.
You can start with `/nbench:setup` and `/nbench:improve` directly.

---

## Quick Start

Here's how to use N-bench from install to daily usage:

### 1. Install & Setup (once)

```bash
/plugin install flux@nairon-flux   # Install plugin
/nbench:setup                         # Initialize in your project
```

### 2. Start a Feature

```bash
/nbench:interview Add user notifications   # Optional: flesh out requirements
/nbench:plan Add user notifications         # Break into tasks
```

### 3. Build It

```bash
/nbench:work fn-1.1                         # Execute first task
/nbench:work fn-1.2                         # Next task (auto-reloads context)
# ... continue until done
```

### 4. Find Better Tools (anytime)

```bash
/nbench:improve                             # Analyze sessions, get recommendations
```

---

## Commands

| Command | What it does |
|---------|--------------|
| `/nbench:setup` | Optional local install of `fluxctl` and project docs |
| `/nbench:improve` | Analyze sessions, detect friction, and recommend improvements |
| `/nbench:profile` | Export/share/import SDLC profile snapshots |
| `/nbench:plan <idea|epic>` | Build structured execution plan |
| `/nbench:work <task|epic>` | Execute tasks with context reload + checks |
| `/nbench:interview <id|file>` | Quick (default) or deep (`--deep`) requirements interview |
| `/nbench:prime` | Agent readiness assessment + guided fixes |
| `/nbench:sync <id>` | Sync downstream task specs after drift |
| `/nbench:plan-review <epic>` | Carmack-level plan quality review |
| `/nbench:impl-review` | Carmack-level implementation review |
| `/nbench:epic-review <epic>` | Verify epic completion against spec |
| `/nbench:ralph-init` | Scaffold Ralph autonomous harness |
| `/nbench:uninstall` | Remove N-bench files from project |

For full options and examples, see `docs/commands-reference.md`.

---

## How It Works

### Task Tracking

N-bench maintains tasks in `.flux/`:
- Epics: `.flux/epics/fn-N-slug.json`
- Tasks: `.flux/tasks/fn-N-slug.M.json`
- Specs: `.flux/specs/fn-N-slug.md`

Each task has clear scope, dependencies, and acceptance criteria. `/nbench:work` reloads this context before each task—nothing drifts.

### Tool Discovery

1. **Extracts** your session history (OpenCode SQLite or Claude Code JSONL)
2. **Detects friction** — 70+ patterns: user frustration, tool errors, agent confusion
3. **Scans your setup** — OS, CLI tools, MCPs, apps, repo configs
4. **Matches gaps** to 30+ curated recommendations with pricing
5. **Asks** which improvements to apply
6. **Implements** — installs tools, adds AGENTS.md rules, configures hooks

Preferences saved to `.flux/preferences.json`.

Profile curation state saved to `~/.flux/profile-state.json`.

---

## FAQ

### Privacy & Data

**What data does N-bench read?**

- Your repo structure (package.json, config files, directories)
- Installed MCPs from `~/.mcp.json`
- Optionally: Claude Code session files from `~/.claude/projects/`

**Is any data sent externally?**

By default, analysis runs locally. Network access is used to fetch the recommendations repo.

If you run `/nbench:improve --discover`, N-bench also sends search queries to Exa/Twitter APIs (using your keys) to find optional community discoveries.

If you run `/nbench:profile`, N-bench can publish a public-anonymous immutable profile snapshot link. Secrets are auto-redacted before publish.

**How does session analysis work?**

N-bench reads your Claude Code JSONL session files and looks for friction patterns:
- Tool errors and failures
- Repeated attempts at the same thing
- Knowledge gaps ("I don't know how to...")
- TypeScript/Python errors in tool outputs
- Agent confusion (apologies, retries)

You're asked for consent before any session files are read.

---

### Recommendations

**How are recommendations chosen?**

N-bench only recommends tools when it detects **actual friction**. No friction = no recommendations.

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

Run `/nbench:improve --detect` to see what N-bench found.

**Can I see why a specific tool was recommended?**

Yes — each recommendation shows the friction signal that triggered it. Example:
```
context7 (MCP)
→ You had 5 api_hallucination errors - context7 provides current docs
```

**Where do recommendations come from?**

A curated database at [Nairon-AI/n-bench-recommendations](https://github.com/Nairon-AI/n-bench-recommendations). Currently 30+ tools across MCPs, CLI tools, apps, and workflow patterns.

**How do I suggest a tool?**

Open an issue on the [recommendations repo](https://github.com/Nairon-AI/n-bench-recommendations/issues).

---

### Profiles

**What is `/nbench:profile` for?**

It exports your SDLC setup (MCPs, CLI tools, skills, apps, patterns, model prefs) into an immutable share link teammates can import.

**How are skills handled?**

Each export asks for scope: global, project, or both. When using both, skills are de-duped by `name + content hash`.

**How are applications handled over time?**

N-bench remembers saved apps. Future exports primarily surface newly detected apps, with an option to re-include previously saved-but-missing apps.

**How does import safety work?**

- Per-item confirmation before install
- Already installed items skipped by default
- Cross-OS incompatible items filtered into an unsupported list
- Manual-only items kept as instructions (not blindly auto-installed)

**Can immutable links be removed?**

They can be tombstoned by owner action, which preserves the link but hides profile contents.

---

## Vision: Engineering Observability

Today, N-bench helps individual engineers work more effectively. Tomorrow, it becomes observability for your entire engineering organization.

**What's coming:**

- **Team Dashboard** — See where every engineer is in the SDLC at any moment. Interview, planning, implementing, reviewing—all visible.
- **Cycle Time Analytics** — Track how long features take from idea to shipped. Identify bottlenecks before they become problems.
- **Token Usage Monitoring** — Understand AI costs across your engineering department.
- **Org-Wide Recommendations** — When one engineer discovers a tool that works, roll it out to everyone. No more knowledge silos.
- **Shared SDLC Evolution** — As the community discovers better workflows, everyone evolves together.

The goal: **every engineer as effective as your best engineer**. No bottlenecks. No one left behind.

N-bench will grow with the industry. The SDLC framework evolves as we collectively learn better ways to build software with AI.

*Interested in early access for your team? [Get in touch](https://github.com/Nairon-AI/n-bench/issues).*

---

## Docs

- `docs/commands-reference.md` - full command reference
- `docs/architecture.md` - command -> skill -> script architecture
- `docs/recommendation-format.md` - recommendation YAML format guide
- `docs/troubleshooting.md` - common issues and fixes

---

## Community

Join the most AI-native developer community. No hype. No AI slop. Just practical discussions on becoming the strongest developers alive.

AI-slop pull requests are automatically triaged and closed.

[discord.gg/CEQMd6fmXk](https://discord.gg/CEQMd6fmXk)

---

## License

MIT
