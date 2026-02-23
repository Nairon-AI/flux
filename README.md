<div align="center">

# N-bench

[![Discord](https://img.shields.io/discord/1234567890?label=discord&color=5865F2)](https://discord.gg/CEQMd6fmXk)
[![Version](https://img.shields.io/badge/version-v1.0.0-green)](https://github.com/Nairon-AI/n-bench/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Plugin-blueviolet)](https://claude.ai/code)

**Your AI workflow has gaps. N-bench finds them.**

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
| [Claude Code](https://claude.ai/code) | ✅ Recommended | `/plugin marketplace add Nairon-AI/n-bench` |
| [Factory Droid](https://factory.ai) | ✅ Supported | `droid plugin marketplace add https://github.com/Nairon-AI/n-bench` |
| [OpenAI Codex](https://openai.com/index/introducing-codex/) | ✅ Supported | `git clone` + `./scripts/install-codex.sh flow-next` |
| [OpenCode](https://github.com/anomalyco/opencode) | 🔜 Coming soon | — |

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

**This is where N-bench comes in.**

---

## What N-bench Does

N-bench is the accumulation of our learnings working at enterprise and building startups over the last 12 months, watching the SDLC evolve in real-time.

The insight: in the age of agentic development, **you still need a framework**—but it's compressed, morphed, and must prepare for increasingly autonomous building. The right human-in-the-loop checkpoints maintain your understanding of the system as it evolves, whether you're building solo or with a team.

**N-bench gives you two things:**

1. **A structured workflow** — Interview → Plan → Build → Review
2. **Continuous improvement** — Analyze your sessions, detect friction, recommend fixes

---

## Quick Start

<!-- TODO: Add video showing complete setup to first feature flow -->
<details>
<summary>Video: From zero to first feature</summary>
<p><em>Coming soon</em></p>
</details>

### Install

```bash
/plugin marketplace add Nairon-AI/n-bench
/plugin install n-bench@nairon-n-bench
```

**Then initialize:**
```bash
/nbench:setup
```

### Build a Feature

```bash
# 1. Interview — Get requirements clear (~5 min)
/nbench:interview Add user notifications

# 2. Plan — Break into atomic tasks (30-90 min each)
/nbench:plan Add user notifications

# 3. Build — Execute tasks one by one
/nbench:work fn-1.1
/nbench:work fn-1.2

# 4. Review — Catch issues before they compound
/nbench:impl-review
/nbench:epic-review fn-1
```

### Find Better Tools

```bash
# Analyze your sessions, get personalized recommendations
/nbench:improve

# Include community discoveries
/nbench:improve --discover
```

That's it. Interview → Plan → Build → Review → Improve. Repeat.

> **You can stop reading here.** Everything below is optional deep-dives.

---

## How `/nbench:improve` Works

N-bench analyzes your **actual coding sessions** to find friction—then recommends specific tools that would help.

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

Browse or contribute: **[n-bench-recommendations](https://github.com/Nairon-AI/n-bench-recommendations)**

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
| `/nbench:setup` | Initialize N-bench in your project |
| `/nbench:interview <idea>` | Requirements interview (use `--deep` for complex features) |
| `/nbench:plan <idea>` | Break into atomic tasks |
| `/nbench:work <task>` | Execute task with context reload |
| `/nbench:sync <epic>` | Sync specs after drift |
| `/nbench:impl-review` | Implementation review |
| `/nbench:epic-review <epic>` | Verify epic completion |
| `/nbench:improve` | Analyze sessions, recommend tools |
| `/nbench:score` | Compute AI-native capability score |
| `/nbench:profile` | Export/share SDLC profile |

Full reference: `docs/commands-reference.md`

---

## Prerequisites

| Requirement | Install |
|-------------|---------|
| Python 3.9+ | `brew install python` / `apt install python3` |
| jq | `brew install jq` / `apt install jq` |
| git | Usually pre-installed |

N-bench checks for these during execution and tells you what's missing.

---

## FAQ

**What data does N-bench read?**
- Repo structure (package.json, configs)
- Installed MCPs from `~/.mcp.json`
- Optionally: Claude Code session files (with consent)

**Is any data sent externally?**
Analysis runs locally. Network only used to fetch recommendations repo.

**Where do recommendations come from?**
[Nairon-AI/n-bench-recommendations](https://github.com/Nairon-AI/n-bench-recommendations) — 30+ curated tools, community-driven.

---

## Philosophy

1. **AI amplifies your skill level, it doesn't replace it.** A mediocre engineer with AI is still mediocre.

2. **Disagreement is a feature.** The best AI collaborators push back constantly.

3. **Process beats raw talent.** Structured approach > vibes-based prompting.

4. **What gets measured gets improved.** You can't fix what you can't see.

5. **The agent should do the work.** Analysis, installation—AI handles it. You decide.

---

## Community

No hype. No AI slop. Just practical discussions on becoming the strongest developers alive.

[discord.gg/CEQMd6fmXk](https://discord.gg/CEQMd6fmXk)

---

## Docs

- `docs/commands-reference.md` — Full command reference
- `docs/architecture.md` — How N-bench works internally
- `docs/troubleshooting.md` — Common issues and fixes

---

## License

MIT

---

<p align="center">
  <em>Stop hoping AI makes you better. Start measuring it.</em>
</p>
