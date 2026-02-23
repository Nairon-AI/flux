<div align="center">

# N-bench

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Plugin-blueviolet)](https://claude.ai/code)

**Your AI workflow has gaps. N-bench finds them.**

</div>

---

## At a Glance

| | |
|---|---|
| **What** | AI collaboration quality benchmark + workflow optimizer |
| **Who** | Engineers using Claude Code, OpenCode, Cursor, or any AI coding assistant |
| **When** | You're productive with AI but know you could be better |
| **Goal** | Measure how intelligently you collaborate with AI, then fix the gaps |
| **Not** | A linter, a code review tool, or another AI wrapper |

> *"Are you actually good at working with AI, or are you just typing 'implement this' and hoping for the best?"*

---

## The Problem

You're using Claude Code (or Cursor, or Copilot), but something's off:

- **No structure** → You jump straight into code and watch the agent go off the rails
- **Context amnesia** → You keep re-explaining the same thing every session
- **Groundhog Day** → The agent tries the same broken approach 5 times in a row
- **Tool FOMO** → You discover a tool that would've saved hours... after the fact
- **Requirements drift** → Scope creeps mid-session and you don't notice until it's too late
- **Blind acceptance** → You accept suggestions without questioning them (the AI is wrong more than you think)

These aren't model failures. They're **process failures**.

Not to mention: best practices and new tools are released weekly on X, and you can't keep up.

All you want is to be as productive as possible, ship quality code, and finally get a good night's rest.

<p align="center">
  <img src="https://media1.tenor.com/m/KBShDXgDMsUAAAAC/green-mile-im-tired-boss.gif" alt="I'm tired, boss" width="400">
</p>

**This is where N-bench comes in.**

---

## What N-bench Does

N-bench is the accumulation of our learnings working at enterprise and building startups over the last 12 months, watching the SDLC evolve in real-time.

The insight: in the age of agentic development, **you still need a framework**—but it's compressed, morphed, and must prepare for increasingly autonomous building. The right human-in-the-loop checkpoints maintain your understanding of the system as it evolves, whether you're building solo or with a team.

### The Workflow

<!-- TODO: Add video showing full interview → plan → work → review cycle -->
<details>
<summary>Video: The N-bench workflow</summary>
<p><em>Coming soon</em></p>
</details>

Instead of jumping straight into code and watching the agent go off the rails:

1. **Quick Interview** — Get just enough to start (~5 min). What's the MVP? What's the riskiest unknown? You'll learn more as you build. Use `--deep` only for high-risk features.

2. **Plan** — Break down into small, atomic tasks. N-bench creates tasks in `.nbench/` with clear scope. Each task should be 30-90 min of work.

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

<!-- TODO: Add video showing /nbench:improve detecting friction and recommending tools -->
<details>
<summary>Video: Friction detection and recommendations</summary>
<p><em>Coming soon</em></p>
</details>

N-bench also analyzes your **actual coding sessions** to find friction—then recommends specific tools that would help:

- MCPs, CLI tools, skills, workflow patterns
- Matched to your project type and detected pain points
- Only recommends when there's actual friction (not tool spam)

```
/nbench:improve
```

Reads your session history, detects frustration patterns, checks what you already have, shows what's missing.

---

## The Recommendations Database

N-bench doesn't just tell you what's wrong—it tells you exactly how to fix it.

### What's In It?

A curated database of **battle-tested solutions** mapped to specific friction patterns:

| Category | Examples |
|----------|----------|
| **Skills** | Workflow templates, prompt libraries, phase-specific guidance |
| **MCP Servers** | Context7 (live docs), Nia (repo research), Linear (project mgmt), Exa (web search) |
| **Plugins** | AI-specific extensions for VS Code, Cursor, Neovim |
| **Workflows** | Structured approaches like "clarify-first", "test-driven-prompting" |
| **Configurations** | Agent settings, context limits, memory management |

### How Matching Works

```
Your Session                    Recommendations DB
─────────────                   ──────────────────

┌─────────────────┐            ┌─────────────────────────────────┐
│ shallow_prompts │───────────►│ prompt-templates skill          │
│ (3 occurrences) │            │ context-builder workflow        │
└─────────────────┘            └─────────────────────────────────┘

┌─────────────────┐            ┌─────────────────────────────────┐
│ no_docs_lookup  │───────────►│ Context7 MCP (version-aware docs)│
│ (2 occurrences) │            │ Nia MCP (repo indexing)         │
└─────────────────┘            └─────────────────────────────────┘

┌─────────────────┐            ┌─────────────────────────────────┐
│ blind_acceptance│───────────►│ devil-advocate skill            │
│ (5 occurrences) │            │ verification-checkpoint workflow│
└─────────────────┘            └─────────────────────────────────┘
```

### What You Actually See

When your agent analyzes your workflow (via `/nbench:improve`), you get something like:

```
Analyzing 12 sessions from the last 7 days...

Friction Patterns Detected:
━━━━━━━━━━━━━━━━━━━━━━━━━━

  shallow_prompts (8 occurrences)
     Prompts lack sufficient context for quality responses.
     You're making the AI guess instead of telling it what you need.

  no_docs_lookup (5 occurrences)
     Not consulting documentation before or during implementation.
     Relying on potentially outdated training data.

  single_attempt (4 occurrences)
     Accepting first AI response without iteration.
     First drafts are rarely best drafts—even from AI.

Recommended Improvements:
━━━━━━━━━━━━━━━━━━━━━━━━

  1. Context7 MCP Server
     ├─ Fetches live, version-specific documentation
     ├─ Eliminates "AI hallucinated that API" problems
     └─ Addresses: no_docs_lookup, outdated_context

  2. prompt-templates skill
     ├─ Pre-built templates for common tasks
     ├─ Forces context, constraints, and examples
     └─ Addresses: shallow_prompts, missing_context

  3. clarify-first workflow
     ├─ Mandatory clarification phase before implementation
     ├─ Catches requirements gaps early
     └─ Addresses: no_clarification, shallow_prompts

Would you like me to install any of these?
```

The agent handles everything. You just say "yes" and it configures your environment.

### The Database is Community-Driven

We don't invent solutions—we curate what actually works:

- **Sourced from top performers**: What do engineers with high scores actually use?
- **Validated by data**: Recommendations are tracked. If installing X doesn't reduce friction Y, it gets demoted.
- **Always growing**: New MCPs, skills, and workflows added as the ecosystem evolves.

---

## The Vision

### For Individual Engineers

Get better at AI collaboration through data, not vibes.

> "Your sessions are 40% shallower than top performers. They disagree with AI suggestions 3x more often and spend 2x longer in the clarification phase. Here's what to install to close the gap."

### For Teams

Apples-to-apples comparison across engineers:
- Who's actually leveraging AI effectively
- Where the team needs skill development
- Which workflows produce the highest quality output

### For Engineering Leaders

CTO-level observability:
- Team benchmarks and improvement trends
- Quality-of-thinking metrics (not just velocity)
- Recruiting signals: "This candidate demonstrates sophisticated AI collaboration patterns"

---

## Quick Demo

<!-- TODO: Add demo video/GIF showing /nbench:improve in action -->
<p align="center">
  <em>Demo video coming soon</em>
</p>

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

## Prerequisites

| Requirement | Why | Install |
|-------------|-----|---------|
| Python 3.9+ | Session analysis, scoring | `brew install python` / `apt install python3` |
| jq | MCP config management | `brew install jq` / `apt install jq` |
| git | Recommendations sync | Usually pre-installed |

N-bench checks for these during execution and tells you what's missing.

---

## Install

<!-- TODO: Add video showing installation process -->
<details>
<summary>Video: Installing N-bench</summary>
<p><em>Coming soon</em></p>
</details>

### Claude Code (Marketplace)

```bash
/plugin marketplace add Nairon-AI/n-bench
/plugin install n-bench@nairon-n-bench
```

### Claude Code (Manual)

If marketplace isn't available or you prefer manual install:

```bash
# Clone to plugins directory
git clone https://github.com/Nairon-AI/n-bench.git ~/.claude/plugins/n-bench

# Verify installation
ls ~/.claude/plugins/n-bench/commands/nbench/
```

After manual install, restart Claude Code. Commands will be available as `/nbench:*`.

### OpenCode

```bash
/plugin marketplace add Nairon-AI/n-bench
/plugin install n-bench@nairon-n-bench
```

### First-Time Setup

After installing, initialize N-bench in your project:

```bash
/nbench:setup
```

This creates `.nbench/` in your project, sets up task tracking, and bootstraps required skills. Run once per project.

Then run:

```bash
/nbench:improve
```

Note: first run may take a few seconds while N-bench clones the recommendations database into `~/.nbench/recommendations`.

### Support

- macOS: supported
- Linux: supported
- Windows: use WSL (best-effort)

---

## Quick Start

<!-- TODO: Add video showing complete setup to first feature flow -->
<details>
<summary>Video: From zero to first feature</summary>
<p><em>Coming soon</em></p>
</details>

### 1. Install & Setup (once)

```bash
/plugin install n-bench@nairon-n-bench   # Install plugin
/nbench:setup                            # Initialize in your project
```

### 2. Start a Feature

```bash
/nbench:interview Add user notifications   # Optional: flesh out requirements
/nbench:plan Add user notifications        # Break into tasks
```

### 3. Build It

```bash
/nbench:work fn-1.1                        # Execute first task
/nbench:work fn-1.2                        # Next task (auto-reloads context)
# ... continue until done
```

### 4. Find Better Tools (anytime)

```bash
/nbench:improve                            # Analyze sessions, get recommendations
```

---

## Commands

| Command | What it does |
|---------|--------------|
| `/nbench:setup` | Initialize N-bench in your project |
| `/nbench:improve` | Analyze sessions, detect friction, recommend improvements |
| `/nbench:score` | Compute AI-native capability score from session data |
| `/nbench:profile` | Export/share/import SDLC profile snapshots |
| `/nbench:plan <idea>` | Build structured execution plan |
| `/nbench:work <task>` | Execute tasks with context reload + checks |
| `/nbench:interview <id>` | Quick (default) or deep (`--deep`) requirements interview |
| `/nbench:prime` | Agent readiness assessment + guided fixes |
| `/nbench:sync <id>` | Sync downstream task specs after drift |
| `/nbench:plan-review <epic>` | Carmack-level plan quality review |
| `/nbench:impl-review` | Carmack-level implementation review |
| `/nbench:epic-review <epic>` | Verify epic completion against spec |
| `/nbench:uninstall` | Remove N-bench files from project |

For full options and examples, see `docs/commands-reference.md`.

---

## How It Works

### Task Tracking

N-bench maintains tasks in `.nbench/`:
- Epics: `.nbench/epics/fn-N-slug.json`
- Tasks: `.nbench/tasks/fn-N-slug.M.json`
- Specs: `.nbench/specs/fn-N-slug.md`

Each task has clear scope, dependencies, and acceptance criteria. `/nbench:work` reloads this context before each task—nothing drifts.

### Tool Discovery

1. **Extracts** your session history (OpenCode SQLite or Claude Code JSONL)
2. **Detects friction** — 70+ patterns: user frustration, tool errors, agent confusion
3. **Scans your setup** — OS, CLI tools, MCPs, apps, repo configs
4. **Matches gaps** to 30+ curated recommendations with pricing
5. **Asks** which improvements to apply
6. **Implements** — installs tools, adds AGENTS.md rules, configures hooks

Preferences saved to `.nbench/preferences.json`.

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

**How does session analysis work?**

N-bench reads your Claude Code JSONL session files and looks for friction patterns:
- Tool errors and failures
- Repeated attempts at the same thing
- Knowledge gaps ("I don't know how to...")
- TypeScript/Python errors in tool outputs
- Agent confusion (apologies, retries)

You're asked for consent before any session files are read.

### Recommendations

**How are recommendations chosen?**

N-bench only recommends tools when it detects **actual friction**. No friction = no recommendations.

Matching logic:
- `api_hallucination` errors → context7 (current docs)
- `css_issues` detected → frontend-optimized models
- `lint_errors` in output → oxlint, biome
- `ci_failures` → lefthook (pre-commit hooks)
- Context forgotten → supermemory

**Where do recommendations come from?**

A curated database at [Nairon-AI/n-bench-recommendations](https://github.com/Nairon-AI/n-bench-recommendations). Currently 30+ tools across MCPs, CLI tools, skills, and workflow patterns.

---

## Philosophy

We believe:

1. **AI amplifies your skill level, it doesn't replace it.** A mediocre engineer with AI is still mediocre. A great engineer with AI is unstoppable.

2. **Disagreement is a feature, not a bug.** The best AI collaborators push back constantly. They treat AI as a smart-but-fallible colleague, not an oracle.

3. **Process beats raw talent.** A structured approach to AI collaboration will outperform "vibes-based" prompting every time.

4. **What gets measured gets improved.** You can't get better at AI collaboration if you can't see what you're doing wrong.

5. **The agent should do the work.** Analysis, recommendations, installation—your AI handles it. You just make decisions.

---

## Community

Join the most AI-native developer community. No hype. No AI slop. Just practical discussions on becoming the strongest developers alive.

[discord.gg/CEQMd6fmXk](https://discord.gg/CEQMd6fmXk)

---

## Docs

- `docs/commands-reference.md` - full command reference
- `docs/architecture.md` - command → skill → script architecture
- `docs/recommendation-format.md` - recommendation YAML format guide
- `docs/troubleshooting.md` - common issues and fixes

---

## Contributing

Contributions welcome! We're building the standard for AI-native development.

- **Friction patterns**: What bad collaboration habits have you seen?
- **Recommendations**: What tools/skills/MCPs actually improve quality?
- **Integrations**: Help N-bench work with more AI assistants

---

## License

MIT

---

<p align="center">
  <em>Stop hoping AI makes you better. Start measuring it.</em>
</p>
