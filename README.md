<div align="center">

# Flux

[![Discord](https://img.shields.io/badge/Discord-Join-5865F2?logo=discord&logoColor=white)](https://discord.gg/CEQMd6fmXk)
[![Version](https://img.shields.io/badge/version-v1.9.6-green)](https://github.com/Nairon-AI/flux/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Plugin-blueviolet)](https://claude.ai/code)

**A structured harness and deterministic state engine for Claude Code.**<br>
Build software reliably with agents.

</div>

## The Problem

You're using an AI coding agent, but something's off:

- **No structure** → You said "build me a dashboard" and came back to a mess of half-finished components
- **Context amnesia** → You've explained the auth flow three times this week. To the same agent.
- **Groundhog Day** → The agent tried the same broken import path five times in a row and you watched it happen
- **Tool FOMO** → You found out about Context7 after spending two hours debugging stale docs
- **Requirements drift** → You asked for a login page and got a full user management system with email verification
- **Blind acceptance** → You shipped the agent's suggestion without reading it. It's in production now. Good luck.
- **Security roulette** → Someone found the hardcoded API key the agent left in your config. On GitHub. Publicly.
- **Echo chamber** → The agent reviewed its own code, said "looks good", and you believed it
- **Long tasks implode** → 20 minutes into a complex refactor, the agent forgot what it was doing and started over
- **Flying blind** → You have no idea if you're getting better at this or just getting faster at making mistakes

<p align="center">
  <img src="https://media1.tenor.com/m/KBShDXgDMsUAAAAC/green-mile-im-tired-boss.gif" alt="I'm tired, boss" width="400">
</p>

These aren't model failures. They're **process failures**.

**This is where Flux comes in.**

- **Repeatable workflows** — enforces structure across sessions so you and the agent never lose track of what's next
- **Multi-model adversarial reviews** — catches what no single model spots alone
- **Long tasks without drift** — Flux keeps the agent on rails even when context gets deep
- **Session analysis** — detect inefficiencies and get recommended optimisations from an engine that learns your patterns
- **Always up-to-date** — stays current with the latest harness and context engineering best practices so you can stop doom-scrolling

Ship with confidence. Sleep better at night.

---

## Contents

- [Install](#install)
- [Getting Started](#getting-started)
- [Core Workflow](#core-workflow)
- [Features](#features)
- [Commands](#commands)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Roadmap](#roadmap)
- [Community](#community)

---

## Install

| Agent | Status | Install |
|-------|--------|---------|
| [Claude Code](https://claude.ai/code) | ✅ Recommended | `/plugin add https://github.com/Nairon-AI/flux@latest` |
| [OpenCode](https://github.com/anomalyco/opencode) | `[██████████░] 96%` | [flux-opencode](https://github.com/Nairon-AI/flux-opencode) |

**Install** — paste this into your agent:
```
Install Flux. Fetch the README at https://github.com/Nairon-AI/flux for install instructions.
```

**Upgrade** — paste this into your agent:
```
Upgrade Flux. Fetch the README at https://github.com/Nairon-AI/flux for upgrade instructions.
```

**Uninstall** — paste this into your agent:
```
Uninstall Flux. Fetch the README at https://github.com/Nairon-AI/flux for uninstall instructions.
```

After setup, just talk to the agent. Flux parses your message intent and routes to the right workflow — scope, work, review, or reflect — based on session state and what's currently in progress. You and the agent always know what's next.

<details>
<summary><strong>Agent Instructions</strong> — the agent reads this section when it fetches the README</summary>

> **⚠️ Slash commands (`/plugin ...`) must be run by the user in the agent UI, not by you in bash.**

#### Install flow

1. Tell the user to run in their agent UI:
   ```
   /plugin add https://github.com/Nairon-AI/flux@latest
   ```
2. Tell the user to restart their agent/session.
3. After restart, run `/flux:setup` to scaffold `.flux/` and configure preferences.
4. If setup installs new MCP servers, tell the user to restart once more.
5. After restart, run `/flux:prime` if the repo hasn't been primed yet.

For **OpenCode**, use the [flux-opencode](https://github.com/Nairon-AI/flux-opencode) port instead.

#### Upgrade flow

The `/plugin update` command resolves from a stale marketplace cache. **Do not use it.**

1. Tell the user to run in their agent UI:
   ```
   /plugin remove flux@nairon-flux
   /plugin add https://github.com/Nairon-AI/flux@latest
   ```
2. Tell the user to restart their agent/session.
3. Run `/flux:setup` to refresh local scripts if needed.

#### Uninstall flow

1. Read `.flux/meta.json` for the `installed_by_flux` manifest to see what Flux added.
2. Ask the user per-category what to keep vs. remove (MCP servers, skills, desktop apps, CLI tools) — many aren't Flux-specific.
3. Tell the user to run in their agent UI:
   ```
   /plugin remove flux@nairon-flux
   ```
4. Remove project artifacts:
   ```bash
   rm -rf .flux
   ```
5. Remove the `<!-- BEGIN FLUX -->` ... `<!-- END FLUX -->` section from CLAUDE.md and AGENTS.md.
6. Optionally remove user-level data: `rm -rf ~/.flux ~/.claude/plugins/cache/nairon-flux`
7. Tell the user to restart.

</details>

---

## Getting Started

### 1. Setup

`/flux:setup` scaffolds `.flux/` in your project, configures your preferences, and optionally installs productivity tools (MCP servers, CLI tools, desktop apps, agent skills).

### 2. Prime

`/flux:prime` audits your codebase for agent readiness across 8 pillars and 48 criteria. It runs once per repo and Flux detects when it's needed.

### 3. Build

After prime, just tell the agent what you want — *build a feature, fix a bug, refactor something, continue work*. Flux uses repo state plus your message to decide whether to scope, resume, review, or hand off.

> **Why both Claude and Codex?** Flux works best with both a Claude and an OpenAI Codex subscription. During reviews, Flux uses the Codex CLI as an adversarial reviewer — a second model with different training data and biases. Multiple models reaching consensus catches blind spots that no single model finds alone.

---

## Core Workflow

```
Prime → Scope → Work → Review → Improve → Reflect
```

| Step | What happens |
|------|-------------|
| **Scope** | Guided interview: classify the work, surface blind spots, create an epic with sized tasks |
| **Work** | Execute tasks with context reload and state tracking |
| **Review** | Adversarial multi-model review of your implementation |
| **Improve** | Analyze sessions, detect inefficiencies, get tool recommendations |
| **Reflect** | Capture learnings into persistent brain vault |

---

## Features

### Deterministic State Engine

`.flux/` is the canonical workflow memory. `session-state` tells Flux whether to prime, start fresh, resume scoping, resume implementation, or route to review. Startup hooks realign the agent with Flux state before acting on new requests.

### Built-in Agentmap

Flux generates YAML repo maps from git-tracked files for faster agent navigation.

```bash
fluxctl agentmap --write   # Writes .flux/context/agentmap.yaml
```

### Brain Vault

Persistent memory that makes the agent smarter over time. Adapted from [brainmaxxing](https://github.com/poteto/brainmaxxing).

```bash
/flux:reflect    # Capture session learnings
/flux:ruminate   # Mine past conversations for patterns
/flux:meditate   # Prune stale notes, extract principles
```

### Recommendation Engine

`/flux:improve` analyzes your sessions and recommends tools mapped to your specific friction patterns — from MCP servers to CLI tools to workflow changes. Recommendations are community-driven via [flux-recommendations](https://github.com/Nairon-AI/flux-recommendations).

### Desloppify

Systematic code quality improvement powered by [desloppify](https://github.com/peteromallet/desloppify). Combines mechanical detection with LLM-based review. The scoring system resists gaming — you can't suppress warnings, you have to actually fix the code.

```bash
/flux:desloppify scan     # See your score
/flux:desloppify next     # Get next priority fix
```

### Security

STRIDE-based security analysis adapted from [Factory AI security-engineer plugin](https://github.com/Factory-AI/factory-plugins). Findings are validated for exploitability with proof-of-concept generation.

```bash
/flux:threat-model           # Generate threat model
/flux:security-scan PR #123  # Scan changes for vulnerabilities
/flux:security-review        # Full security review
```

### Linear Integration

Connect Flux to [Linear](https://linear.app/docs/mcp) for team workflows — scope Linear projects with the same guided flow and create tasks directly.

```bash
/flux:scope --linear    # Browse teams → projects
/flux:scope LIN-42      # Scope specific issue
```

---

## Commands

| Command | What it does |
|---------|-------------|
| `/flux:setup` | Initialize Flux in your project |
| `/flux:scope <idea>` | Guided scoping workflow (`--deep`, `--explore N`, `--linear`) |
| `/flux:plan <idea>` | Create tasks only (skip interview) |
| `/flux:work <task>` | Execute task with context reload |
| `/flux:sync <epic>` | Sync specs after drift |
| `/flux:impl-review` | Implementation review |
| `/flux:epic-review <epic>` | Verify epic completion |
| `/flux:prime` | Codebase readiness audit (8 pillars, 48 criteria) |
| `/flux:desloppify` | Code quality improvement |
| `/flux:improve` | Analyze sessions, recommend tools |
| `/flux:reflect` | Capture session learnings |
| `/flux:ruminate` | Mine past conversations for patterns |
| `/flux:meditate` | Prune brain vault, extract principles |
| `/flux:threat-model` | STRIDE-based threat model |
| `/flux:security-scan` | Scan for vulnerabilities |
| `/flux:security-review` | Full security review |
| `/flux:vuln-validate` | Validate findings with PoC |
| `/flux:score` | AI-native capability score |
| `/flux:profile` | Export/share SDLC profile |
| `/flux:contribute` | Report bug and auto-create fix PR |

Full reference: `docs/commands-reference.md`

### Prerequisites

Python 3.9+, jq, git. Flux checks for these during execution and tells you what's missing.

---

## Troubleshooting

> **AI Agents**: If you're debugging a Flux installation issue, follow these steps exactly. Do not guess.

<details>
<summary><strong>"Unknown skill: flux:setup"</strong></summary>

The plugin is registered but not enabled. Add to `~/.claude/settings.json`:

```bash
jq '.enabledPlugins["flux@nairon-flux"] = true' ~/.claude/settings.json > tmp.json && mv tmp.json ~/.claude/settings.json
```
Then restart Claude Code.
</details>

<details>
<summary><strong>Agent tried to run /plugin add in bash</strong></summary>

`/plugin` is a Claude Code slash command, not a shell command. Run it directly in the chat input, then restart.
</details>

<details>
<summary><strong>Commands still not working after enabling</strong></summary>

Clear cache and reinstall:
```bash
rm -rf ~/.claude/plugins/cache/nairon-flux ~/.claude/plugins/marketplaces/nairon-flux
```
Restart Claude Code, run `/plugin add https://github.com/Nairon-AI/flux@latest`, restart again.
</details>

<details>
<summary><strong>Old version / missing new commands</strong></summary>

```bash
rm -rf ~/.claude/plugins/cache/nairon-flux
```
Restart, run `/plugin add https://github.com/Nairon-AI/flux@latest`, restart again.
</details>

<details>
<summary><strong>"/plugin add" opens Discover tab instead of installing</strong></summary>

Run `/plugin marketplace add https://github.com/Nairon-AI/flux`, then `/plugin install flux@nairon-flux`, then restart.
</details>

<details>
<summary><strong>Nuclear option: complete reset</strong></summary>

```bash
rm -rf ~/.claude/plugins/cache/nairon-flux ~/.claude/plugins/marketplaces/nairon-flux
# Edit ~/.claude/plugins/installed_plugins.json — remove "nairon-flux" entries
# Edit ~/.claude/settings.json — remove "flux@nairon-flux" from enabledPlugins
```
Restart Claude Code, run `/plugin add https://github.com/Nairon-AI/flux@latest`, restart, run `/flux:setup`.
</details>

**Still stuck?** Join [Discord](https://discord.gg/CEQMd6fmXk) or open a [GitHub issue](https://github.com/Nairon-AI/flux/issues).

---

## FAQ

**What data does Flux read?**
Repo structure, installed MCPs, and optionally Claude Code session files (with consent).

**Is any data sent externally?**
Analysis runs locally. Network only used to fetch the recommendations repo.

**Can I use Flux with Beads?**
Not recommended — both are task tracking systems and will confuse the agent. Pick one.

---

## Roadmap

### v2.0 — Relay

A fully autonomous orchestration layer for Flux. Heavily inspired by [OpenAI Symphony](https://github.com/openai/symphony).

Relay coordinates multiple agents working in parallel across worktrees, manages task dependencies, and handles handoffs — so you can kick off a complex build, go for a walk, and come back to a PR. Human-in-the-loop when you want it, fully autonomous when you don't.

### Feature Roadmap

| Command | Enhancement |
|---------|-------------|
| `/flux:work` | Git worktree support for parallel development |
| `/flux:scope` | Meeting transcript ingestion |

### Universe Integration

Flux will sync to [Nairon Universe](https://nairon.ai/universe) — a public portal for AI-native engineers with profiles, benchmarks, and team dashboards.

*Coming Q2 2026.*

---

## Philosophy

1. **AI amplifies your skill level, it doesn't replace it.**
2. **Disagreement is a feature.** The best AI collaborators push back constantly.
3. **Process beats raw talent.** Structured approach > vibes-based prompting.
4. **What gets measured gets improved.** You can't fix what you can't see.
5. **The agent should do the work.** Analysis, installation — AI handles it. You decide.

---

## Community

No hype. No AI slop. Just practical discussions on becoming the strongest developers alive.

[discord.gg/CEQMd6fmXk](https://discord.gg/CEQMd6fmXk)

---

## Docs

- `docs/commands-reference.md` — Full command reference
- `docs/architecture.md` — How Flux works internally

---

## License

MIT

---

<p align="center">
  <em>Stop hoping AI makes you better. Start measuring it.</em>
</p>
