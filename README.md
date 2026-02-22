# Flux

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Plugin-blueviolet)](https://claude.ai/code)

> The AI workflow optimizer that knows what you're missing.

## Compatibility

| Agent | Status | Session Analysis |
|-------|--------|------------------|
| **OpenCode** | Full support | SQLite database |
| **Claude Code** | Full support | JSONL files |
| **Cursor** | Planned | — |
| **Codex** | Planned | — |

Works with both global (`~/.config/opencode/`) and local (`.opencode/`, `.claude/`) configurations.

## The Problem

Process failures, not model failures:

- **Repeating the same debugging cycle** — trying the same broken approach 5 times before pivoting
- **Losing context mid-session** — agent forgets what was decided, you re-explain
- **Drip-feeding requirements** — "also add X" after implementation, causing rework
- **Missing obvious tools** — not using MCPs/skills that would save hours

Flux analyzes your **actual sessions**, finds these patterns, and recommends specific fixes.

## Why Flux?

**Not spray-and-pray recommendations.** Flux detects:
- What you already have installed (MCPs, CLI tools, apps)
- Gaps in your workflow (no tests? no git hooks? no design tools?)
- The SDLC phase each gap affects (requirements → planning → implementation → review → testing → documentation)

Then recommends **only what fills actual gaps**, with pricing upfront.

## Quick Start

```bash
# Install the plugin
/plugin marketplace add Nairon-AI/flux
/plugin install flux@nairon-flux

# See what you're missing
/flux:improve
```

## What `/flux:improve` Shows You

```
Detected:
  OS: macos
  CLI: jq, fzf, eslint, beads
  Apps: granola, wispr-flow
  MCPs: playwriter

Gaps by SDLC Phase:

Requirements
  - No design tools → Pencil (free) or Figma ($15/mo)
  - No web search → Exa (free tier: 1000/mo)

Planning  
  - No diagramming → Excalidraw (free, open-source)
  - No issue tracking → Linear ($8/user) or Beads (free)

Review
  - No git hooks → Lefthook (free) catches errors in 5s not 5min
  
Testing
  - No tests → Stagehand E2E (self-healing tests)

Documentation
  - No AGENTS.md → AI guesses wrong about your project
```

## Commands

| Command | What it does |
|---------|--------------|
| `/flux:improve` | Analyze workflow gaps, get smart recommendations |
| `/flux:improve --detect` | Just show what's installed |
| `/flux:improve --dismiss X` | Never recommend X again |
| `/flux:improve --alternative X Y` | "I use Y instead of X" |
| `/flux:plan` | Break a feature into dependency-aware tasks |
| `/flux:work` | Execute a task with automatic context reload |

## How It Works

1. **Detects** your OS, installed CLI tools, apps, MCPs, and plugins
2. **Analyzes** your repo (package.json, configs, test setup, CI, hooks)
3. **Identifies gaps** across 6 SDLC phases
4. **Matches** from 26+ curated recommendations with pricing
5. **Skips** tools you already have or dismissed
6. **Remembers** your preferences in `~/.flux/preferences.json`

## Recommendation Database

Recommendations live in [Nairon-AI/flux-recommendations](https://github.com/Nairon-AI/flux-recommendations):

| Category | Examples |
|----------|----------|
| **MCPs** | Context7, Exa, Linear, GitHub, Figma, Pencil, Excalidraw, Supermemory |
| **CLI Tools** | Lefthook, OxLint, Biome, Beads, jq, fzf |
| **Applications** | Granola, Wispr Flow, Raycast, Dia |
| **Skills** | Stagehand E2E, Remotion, RepoPrompt |
| **Patterns** | AGENTS.md structure, pre-commit hooks, atomic commits |

Each recommendation includes:
- **SDLC phase** it addresses
- **What problem it solves**
- **Pricing** (free, freemium, paid, open-source)

## Workflow Engine

Flux also enforces **plan before you code**:

```bash
/flux:plan Add user authentication with OAuth
/flux:work fx-1
```

Every feature gets broken into trackable tasks stored in `.flux/`. Every task re-anchors to the plan before execution. Nothing slips through the cracks.

## Installation

```bash
/plugin marketplace add Nairon-AI/flux
/plugin install flux@nairon-flux
```

**Auto-update (recommended):**
```
/plugin → Marketplaces tab → nairon-flux → Enable auto-update
```

## Community

Join the most AI-native developer community on the planet.

[discord.gg/nairon](https://discord.gg/nairon) *(coming soon)*

## License

MIT
