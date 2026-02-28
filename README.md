<div align="center">

# Flux

[![Discord](https://img.shields.io/badge/Discord-Join-5865F2?logo=discord&logoColor=white)](https://discord.gg/CEQMd6fmXk)
[![Version](https://img.shields.io/badge/version-v1.5.0-green)](https://github.com/Nairon-AI/flux/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Plugin-blueviolet)](https://claude.ai/code)

**Your AI workflow has gaps. Flux finds them.**

</div>

---

## At a Glance

| | |
|---|---|
| **What** | AI collaboration quality benchmark + workflow optimizer |
| **Who** | Engineers using AI coding agents (CTOs soon) |
| **When** | You think you're productive with AI but know you could be better |
| **Goal** | Measure how intelligently you collaborate with AI, then fix the gaps |
| **Not** | A linter, a code review tool, or another AI wrapper |

> *"Are you actually good at working with AI, or are you just typing 'implement X, make no mistakes' and hoping for the best?"*

### Platform Compatibility

| Platform | Status | Install |
|----------|--------|---------|
| [Claude Code](https://claude.ai/code) | ✅ Recommended | `/plugin marketplace add Nairon-AI/flux` |
| [Factory Droid](https://factory.ai) | ✅ Supported | `droid plugin marketplace add https://github.com/Nairon-AI/flux` |
| [OpenAI Codex](https://openai.com/index/introducing-codex/) | ✅ Supported | `git clone` + `./scripts/install-codex.sh flux` |
| [OpenCode](https://github.com/anomalyco/opencode) | `[██████████░] 96%` | [flux-opencode](https://github.com/Nairon-AI/flux-opencode) |

---

## The Problem

You're using Claude Code, but something's off:

- **No structure** → You jump straight into code and watch the agent go off the rails
- **Context amnesia** → You keep re-explaining the same thing every session
- **Groundhog Day** → The agent tries the same broken approach 5 times in a row
- **Tool FOMO** → You discover a tool that would've saved hours... after the fact
- **Requirements drift** → Scope creeps mid-session and you don't notice until it's too late
- **Blind acceptance** → You accept suggestions without questioning them (the AI is wrong more than you think)
- **No observability** → You have no idea how "AI-native" you are compared to others or where your gaps are

<p align="center">
  <img src="https://media1.tenor.com/m/KBShDXgDMsUAAAAC/green-mile-im-tired-boss.gif" alt="I'm tired, boss" width="400">
</p>


These aren't model failures. They're **process failures**.

**This is where Flux comes in.**

---

## What Flux Does

Flux is the accumulation of our learnings working at enterprise and building startups over the last 12 months, watching the SDLC evolve in real-time.

The insight: in the age of agentic development, **you still need a framework**—but it's compressed, morphed, and must prepare for increasingly autonomous building. The right human-in-the-loop checkpoints maintain your understanding of the system as it evolves, whether you're building solo or with a team.

**Flux gives you three things:**

1. **A structured workflow** — Scope → Build → Review (Double Diamond process)
2. **Continuous improvement** — Analyze your sessions, detect friction, recommend fixes
3. **Observability** — Tap into your sessions to see if you're blindly accepting or intelligently pushing back

---

## Quick Start

### Step 1: Install the Plugin

```bash
/plugin marketplace add Nairon-AI/flux
/plugin install flux@nairon-flux
```

### Step 2: Restart Claude Code

**Important:** Plugins are cached at session start. After installing:

1. Exit this session (`/exit` or Ctrl+C)
2. Restart Claude Code (run `claude` again, or use `claude --resume` to continue)
3. The Flux commands will now be available

### Step 3: Initialize (in new session)

```bash
/flux:setup
```

This scaffolds Flux config in your project.

### Updating

```bash
/plugin marketplace update nairon-flux
```

Then **restart Claude Code** for changes to take effect.

> **Note for AI agents:** Do NOT try to run `/flux:setup` or any Flux commands immediately after installation. The plugin won't be available until the user restarts their session. Install the plugin, then tell the user to restart and run `/flux:setup` in the new session.

### Build a Feature

```bash
# 1. Scope — Understand problem + create plan
/flux:scope Add user notifications

# 2. Build — Execute tasks one by one
/flux:work fn-1.1
/flux:work fn-1.2

# 3. Review — Catch issues before they compound
/flux:impl-review
/flux:epic-review fn-1
```

#### `/flux:scope` — The Double Diamond

This is your starting point. It guides you through:

1. **Problem Space** — WHY are we building this?
   - Core desire, reasoning validation, user perspective
   - Surface blind spots and risks
   - Converge to clear problem statement

2. **Solution Space** — HOW should we build it?
   - Research codebase patterns
   - Create epic with sized tasks

**Modes:**
```bash
/flux:scope Add notifications          # Quick (~10 min) - MVP focus
/flux:scope Add notifications --deep   # Deep (~45 min) - thorough scoping
/flux:scope Add notifications --explore 3  # Generate 3 competing approaches
```

`--explore` scaffolds multiple approaches in parallel (git worktrees), generates previews, and lets you compare before committing to one.

### Linear Integration (Optional)

Connect Flux to Linear for team workflows. Select a Linear project, scope it with Double Diamond, and create tasks directly in Linear.

```bash
/flux:scope --linear              # Browse teams → projects, select one to scope
/flux:scope LIN-42                # Scope specific Linear issue
/flux:scope PROJ-123 --deep       # Deep scope with Linear context
```

**What it does:**
1. Checks if Linear MCP is available (guides setup if not)
2. Lists teams → projects (Linear project = Flux epic)
3. Pulls project description, milestones, existing issues
4. Runs Double Diamond scoping with Linear context
5. Creates tasks in Linear with proper dependencies
6. Stores mapping in `.flux/epics/<id>/linear.json`

**Setup:** Requires [Linear MCP](https://linear.app/docs/mcp).

**Claude Code:**
```bash
claude mcp add --transport http linear-server https://mcp.linear.app/mcp
```
Then run `/mcp` in your session to authenticate.

**Other clients (Cursor, VS Code, Windsurf):**
```json
{
  "mcpServers": {
    "linear": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.linear.app/mcp"]
    }
  }
}
```

Full setup guide: https://linear.app/docs/mcp

<details>
<summary>Alternative: Skip interview, plan only</summary>

```bash
# If you already have a clear spec:
/flux:plan fn-1                          # ~5-15 min
```
</details>

### Find Better Tools

```bash
# Analyze your sessions, get personalized recommendations
/flux:improve

# Include community discoveries
/flux:improve --discover
```

### Clean Up Your Codebase

```bash
# Scan and systematically fix code quality issues
/flux:desloppify
```

Powered by [desloppify](https://github.com/peteromallet/desloppify) — a codebase quality scanner that combines mechanical detection (dead code, duplication, complexity) with LLM-based subjective review (naming, abstractions, architecture).

**Why it's different:** The scoring system is designed to resist gaming. You can't just suppress warnings — the only way to raise the score is to actually make the code better.

| Tier | What It Catches |
|------|-----------------|
| T1 | Auto-fixable: unused imports, debug logs |
| T2 | Quick manual: unused vars, dead exports |
| T3 | Judgment calls: near-dupes, single-use abstractions |
| T4 | Major refactors: god components, mixed concerns |

```bash
/flux:desloppify scan          # See your score
/flux:desloppify next          # Get next priority fix
/flux:desloppify status        # Track progress
```

Target: **95+ strict score** = codebase a senior engineer would respect.

That's it. Scope → Build → Review → Improve → Clean. Repeat.

> **You can stop reading here.** Everything below is optional deep-dives.

---

## How `/flux:improve` Works

Flux analyzes your **actual coding sessions** to find friction—then recommends specific tools that would help.

### What It Detects

| Signal | What It Means |
|--------|---------------|
| `shallow_prompts` | "Implement this" without context |
| `blind_acceptance` | Never disagreeing with AI suggestions |
| `no_docs_lookup` | Relying on outdated training data |
| `undo_loops` | AI producing slop, needs better planning |
| `memory_loss` | Context not persisting across sessions |

### What It Recommends

A curated database of **battle-tested solutions** mapped to your specific friction:

| Category | Examples |
|----------|----------|
| **MCP Servers** | Context7 (live docs), Nia (repo research), Supermemory (persistence) |
| **Skills** | Workflow templates, prompt libraries |
| **CLI Tools** | Lefthook (git hooks), Beads (task tracking) |
| **Workflows** | Clarify-first, test-driven-prompting |

Browse or contribute: **[flux-recommendations](https://github.com/Nairon-AI/flux-recommendations)**

### Example Output

```
Friction Patterns Detected:
━━━━━━━━━━━━━━━━━━━━━━━━━━

  shallow_prompts (8 occurrences)
     Prompts lack sufficient context for quality responses.

  no_docs_lookup (5 occurrences)
     Not consulting documentation before implementation.

Recommended Improvements:
━━━━━━━━━━━━━━━━━━━━━━━━

  1. Context7 MCP Server
     ├─ Fetches live, version-specific documentation
     └─ Addresses: no_docs_lookup

  2. prompt-templates skill
     ├─ Pre-built templates for common tasks
     └─ Addresses: shallow_prompts

Would you like me to install any of these?
```

The agent handles installation. You just say "yes."

---

## The Vision

### For Individual Engineers

Get better at AI collaboration through data, not vibes.

> "Your sessions are 40% shallower than top performers. They disagree with AI suggestions 3x more often. Here's what to install to close the gap."

### For Teams

- Who's actually leveraging AI effectively
- Where the team needs skill development
- Which workflows produce the highest quality output
- Share your entire setup with new engineers for instant 10x onboarding

### For Engineering Leaders (Coming Soon)

CTO-level observability:
- Team benchmarks and improvement trends
- Quality-of-thinking metrics (not just velocity)
- Recruiting signals: "This candidate demonstrates sophisticated AI collaboration patterns"

---

## Commands

| Command | What it does |
|---------|--------------|
| `/flux:setup` | Initialize Flux in your project |
| `/flux:scope <idea>` | **Double Diamond scoping** — interview + plan (`--deep`, `--explore N`, `--linear`) |
| `/flux:plan <idea>` | Create tasks only (skip problem space interview) |
| `/flux:work <task>` | Execute task with context reload |
| `/flux:sync <epic>` | Sync specs after drift |
| `/flux:impl-review` | Implementation review |
| `/flux:epic-review <epic>` | Verify epic completion |
| `/flux:prime` | Codebase readiness audit (8 pillars, 48 criteria) |
| `/flux:desloppify` | Systematic code quality improvement (scan → fix loop) |
| `/flux:improve` | Analyze sessions, recommend tools |
| `/flux:score` | Compute AI-native capability score |
| `/flux:profile` | Export/share SDLC profile |
| `/flux:contribute` | Report bug and auto-create PR to fix Flux |

Full reference: `docs/commands-reference.md`

---

## Prerequisites

| Requirement | Install |
|-------------|---------|
| Python 3.9+ | `brew install python` / `apt install python3` |
| jq | `brew install jq` / `apt install jq` |
| git | Usually pre-installed |

Flux checks for these during execution and tells you what's missing.

---

## FAQ

**What data does Flux read?**
- Repo structure (package.json, configs)
- Installed MCPs from `~/.mcp.json`
- Optionally: Claude Code session files (with consent)

**Is any data sent externally?**
Analysis runs locally. Network only used to fetch recommendations repo.

**Where do recommendations come from?**
[Nairon-AI/flux-recommendations](https://github.com/Nairon-AI/flux-recommendations) — 30+ curated tools, community-driven.

**Can I use Flux with Beads?**
Not recommended. Both are task tracking systems — Flux uses `.flux/` + `fluxctl`, Beads uses `.beads/` + `bd`. Having both in your AGENTS.md will confuse the agent about which to use. Pick one:
- **Flux** if you want the full workflow (scope → plan → work → review)
- **Beads** if you just want lightweight issue tracking

If migrating from Beads: remove the beads section from AGENTS.md and run `/flux:setup`.

---

## Philosophy

1. **AI amplifies your skill level, it doesn't replace it.** A mediocre engineer with AI is still mediocre.

2. **Disagreement is a feature.** The best AI collaborators push back constantly.

3. **Process beats raw talent.** Structured approach > vibes-based prompting.

4. **What gets measured gets improved.** You can't fix what you can't see.

5. **The agent should do the work.** Analysis, installation—AI handles it. You decide.

---

## Feature Roadmap

Upcoming enhancements to core commands:

| Command | Enhancement | Description |
|---------|-------------|-------------|
| `/flux:work` | Git worktree support | Isolate task work in separate worktrees for parallel development and clean rollbacks |
| `/flux:scope` | Transcript ingestion | Ingest meeting transcripts, auto-detect affected issues, ask clarifying questions, update task details |

Want to contribute? Check out the [issues](https://github.com/Nairon-AI/flux/issues) or join the [Discord](https://discord.gg/CEQMd6fmXk).

---

## Roadmap: Universe Integration

Flux will sync to [Nairon Universe](https://nairon.ai/universe) — a public portal for AI-native engineers.

**Public Profile (visible to others):**
| Data | Example |
|------|---------|
| Sessions | "350 sessions with Claude Code" |
| Tokens | "15M tokens used this month" |
| Tools | MCP servers, skills, CLI tools you use |
| Activity | Recent projects, contributions |

**Private Dashboard (for you):**
| Data | What It Shows |
|------|---------------|
| AI-Native Score | Your grade across 5 dimensions |
| Radar Chart | Interview depth, pushback ratio, prompt quality, iteration efficiency |
| Trends | How you're improving over time |

**Why this matters:** When you follow an engineer on Universe, you can see exactly what tools they use and how they work with AI. No more guessing — just copy what works.

*Status: Coming Q2 2026. Auth will use Universe accounts.*

---

## Community

No hype. No AI slop. Just practical discussions on becoming the strongest developers alive.

[discord.gg/CEQMd6fmXk](https://discord.gg/CEQMd6fmXk)

---

## Docs

- `docs/commands-reference.md` — Full command reference
- `docs/architecture.md` — How Flux works internally
- `docs/troubleshooting.md` — Common issues and fixes

---

## License

MIT

---

<p align="center">
  <em>Stop hoping AI makes you better. Start measuring it.</em>
</p>
