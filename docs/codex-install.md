# OpenAI Codex Installation

Flux works in OpenAI Codex CLI with near-parity to Claude Code. The install script converts Claude Code's plugin system to Codex's multi-agent roles, prompts, and config.

## Requirements

- Codex CLI 0.102.0+ (for multi-agent role support)

## Install

```bash
# Clone the repo (one-time)
git clone https://github.com/Nairon-AI/flux.git
cd flux

# Run the install script
./scripts/install-codex.sh flux
```

> Codex doesn't have a plugin marketplace yet, so installation requires cloning this repo. The script copies everything to `~/.codex/` — you can delete the clone after install (re-clone to update).

## Command Mapping

Commands use the `/prompts:` prefix in Codex instead of `/flux:`:

| Claude Code | Codex |
|-------------|-------|
| `/flux:plan` | `/prompts:plan` |
| `/flux:work` | `/prompts:work` |
| `/flux:impl-review` | `/prompts:impl-review` |
| `/flux:plan-review` | `/prompts:plan-review` |
| `/flux:epic-review` | `/prompts:epic-review` |
| `/flux:interview` | `/prompts:interview` |

## What Works

- Planning, work execution, interviews, reviews — full workflow
- Multi-agent roles: 20 agents run as parallel Codex threads (up to 12 concurrent)
- Cross-model reviews (Codex as review backend)
- Ralph autonomous mode
- fluxctl CLI

## Model Mapping (3-tier)

| Tier | Codex Model | Agents | Reasoning |
|------|-------------|--------|-----------|
| Intelligent | `gpt-5.3-codex` | quality-auditor, flow-gap-analyst, context-scout | high |
| Smart scouts | `gpt-5.3-codex` | epic-scout, agents-md-scout, docs-gap-scout | high |
| Fast scouts | `gpt-5.3-codex-spark` | build, env, testing, tooling, observability, security, workflow, memory scouts | skipped |
| Inherited | parent model | worker, plan-sync | parent |

Override model defaults:
```bash
CODEX_MODEL_INTELLIGENT=gpt-5.3-codex \
CODEX_MODEL_FAST=gpt-5.3-codex-spark \
CODEX_REASONING_EFFORT=high \
CODEX_MAX_THREADS=12 \
./scripts/install-codex.sh flux
```

## Per-Project Setup

Run in each project:

```bash
# Initialize .flux/ directory
~/.codex/bin/fluxctl init

# Optional: copy fluxctl locally for project portability
mkdir -p .flux/bin
cp ~/.codex/bin/fluxctl .flux/bin/
cp ~/.codex/bin/fluxctl.py .flux/bin/
chmod +x .flux/bin/fluxctl

# Optional: configure review backend
~/.codex/bin/fluxctl config set review.backend codex
```

## Caveats

- `/prompts:setup` not supported — use manual project setup above
- Hooks not supported (ralph-guard won't run in Codex)
- `claude-md-scout` is auto-renamed to `agents-md-scout` (CLAUDE.md → AGENTS.md patching)
