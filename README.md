# Flux

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Plugin-blueviolet)](https://claude.ai/code)

> The AI workflow optimizer that knows what you're missing.

> [!TIP]
> **🤖 Works on [Factory Droid](https://factory.ai) too!** Claude Code plugins are fully compatible:
> ```bash
> droid plugin marketplace add https://github.com/Nairon-AI/flux
> ```
> Then `/plugins` → Marketplace → install flux. Commands don't autocomplete yet but work when typed (e.g. `/flux:improve`). Skills load automatically.

> [!TIP]
> **🖥️ [OpenAI Codex](https://openai.com/index/introducing-codex/) user?** Full multi-agent support:
> ```bash
> git clone https://github.com/Nairon-AI/flux.git
> cd flux && ./scripts/install-codex.sh flux
> ```
> Requires Codex 0.102.0+. Commands use `/prompts:` prefix (e.g. `/prompts:improve`). See [Codex install guide](#openai-codex-experimental).

> [!TIP]
> **🧪 OpenCode user?** Native support built-in. Just install and run `/flux:improve`.

## Compatibility

| Agent | Status | Session Analysis |
|-------|--------|------------------|
| **Claude Code** | Full support | ✅ JSONL files |
| **OpenCode** | Full support | ✅ SQLite database |
| **Factory Droid** | Full support | — |
| **OpenAI Codex** | Full support | — |

Works with both global (`~/.config/`) and local (`.opencode/`, `.claude/`) configurations.

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
6. **Remembers** your preferences in `.flux/preferences.json`

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        /flux:improve                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SESSION EXTRACTION                           │
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │ OpenCode         │    │ Claude Code      │                  │
│  │ ~/.local/share/  │    │ ~/.claude/       │                  │
│  │ opencode.db      │    │ projects/*/      │                  │
│  │ (SQLite)         │    │ *.jsonl          │                  │
│  └────────┬─────────┘    └────────┬─────────┘                  │
│           └──────────┬───────────┘                             │
│                      ▼                                          │
│           ${PLUGIN_ROOT}/scripts/parse-sessions.py              │
│           (extracts user messages)                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FRICTION DETECTION                            │
│                                                                 │
│  Keywords: "bruh", "again", "still", "why", "fail", "error"    │
│  Patterns: repeated attempts, confusion, rework                 │
│                      │                                          │
│                      ▼                                          │
│           friction_signals[]                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                RECOMMENDATIONS DATABASE (external)              │
│                ~/.flux/recommendations/ (git clone)             │
│                                                                 │
│  ┌─────────┐ ┌───────────┐ ┌──────────────┐ ┌────────────────┐ │
│  │  MCPs   │ │ CLI Tools │ │ Applications │ │ Skills/Patterns│ │
│  │ (7)     │ │ (6)       │ │ (4)          │ │ (10)           │ │
│  └─────────┘ └───────────┘ └──────────────┘ └────────────────┘ │
│                                                                 │
│  Each .yaml includes:                                           │
│  - sdlc_phase (requirements/planning/impl/review/test/docs)    │
│  - problem_solved                                               │
│  - pricing (free/freemium/paid/open-source)                    │
│  - install commands                                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MATCHING ENGINE                            │
│                                                                 │
│  friction_signals[] ──┬──▶ Match by keywords/patterns          │
│  detected_tools[]  ───┤                                        │
│  sdlc_gaps[]       ───┘   ▼                                    │
│                      recommendations[]                          │
│                      (filtered, ranked)                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   INTERACTIVE FLOW                              │
│                                                                 │
│  mcp_question() ──▶ "Which improvements to apply?"             │
│                                                                 │
│  User selects ──▶ Auto-implement:                              │
│                   • AGENTS.md rules                             │
│                   • MCP installs                                │
│                   • CLI tool installs                           │
│                   • Git hook setup                              │
└─────────────────────────────────────────────────────────────────┘
```

## Recommendation Database

Recommendations are maintained separately in [Nairon-AI/flux-recommendations](https://github.com/Nairon-AI/flux-recommendations).

**Install recommendations:**
```bash
git clone https://github.com/Nairon-AI/flux-recommendations ~/.flux/recommendations
```

**Update recommendations:**
```bash
cd ~/.flux/recommendations && git pull
```

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

> **Note:** `/flux:improve` works without recommendations installed—it just won't suggest tools. Session analysis and gap detection still run.

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

## OpenAI Codex (Experimental)

Install Flux to OpenAI Codex (requires Codex CLI 0.102.0+):

```bash
# Clone the repo (one-time)
git clone https://github.com/Nairon-AI/flux.git
cd flux

# Install
./scripts/install-codex.sh flux
```

> Codex has no plugin marketplace — clone this repo to install. Everything copies to `~/.codex/`, so the clone can be deleted after (re-clone to update).

**What gets installed:**
- `~/.codex/prompts/` — Command prompts (`/prompts:improve`, `/prompts:plan`, `/prompts:work`)
- `~/.codex/skills/` — Skill definitions (patched for Codex paths)
- `~/.codex/agents/*.toml` — Multi-agent role configs

**Path patching:** All `${CLAUDE_PLUGIN_ROOT}` references are automatically replaced with `~/.codex` paths during install.

**Usage in Codex:**
```bash
# Commands use /prompts: prefix
/prompts:improve    # Analyze workflow gaps
/prompts:plan       # Break feature into tasks
/prompts:work       # Execute a task
```

**Limitations:**
- Hooks not supported
- Session analysis not yet available (Codex session format TBD)

---

## Community

Join the most AI-native developer community on the planet.

[discord.gg/nairon](https://discord.gg/nairon) *(coming soon)*

## License

MIT
