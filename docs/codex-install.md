# OpenAI Codex Installation

N-bench works in OpenAI Codex CLI with near-parity to Claude Code. The install script converts Claude Code's plugin system to Codex's multi-agent roles, prompts, and config.

## Requirements

- Codex CLI 0.102.0+ (for multi-agent role support)

## Install

```bash
# Clone the repo (one-time)
git clone https://github.com/Nairon-AI/n-bench.git
cd n-bench

# Run the install script
./scripts/install-codex.sh nbench
```

> Codex doesn't have a plugin marketplace yet, so installation requires cloning this repo. The script copies everything to `~/.codex/` — you can delete the clone after install (re-clone to update).

## Command Mapping

Commands use the `/prompts:` prefix in Codex instead of `/nbench:`:

| Claude Code | Codex |
|-------------|-------|
| `/nbench:plan` | `/prompts:plan` |
| `/nbench:work` | `/prompts:work` |
| `/nbench:impl-review` | `/prompts:impl-review` |
| `/nbench:plan-review` | `/prompts:plan-review` |
| `/nbench:epic-review` | `/prompts:epic-review` |
| `/nbench:interview` | `/prompts:interview` |

## What Works

- Planning, work execution, interviews, reviews — full workflow
- Multi-agent roles: 20 agents run as parallel Codex threads (up to 12 concurrent)
- Cross-model reviews (Codex as review backend)
- Ralph autonomous mode
- nbenchctl CLI

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
./scripts/install-codex.sh nbench
```

## Per-Project Setup

Run in each project:

```bash
# Initialize .nbench/ directory
~/.codex/bin/nbenchctl init

# Optional: copy nbenchctl locally for project portability
mkdir -p .nbench/bin
cp ~/.codex/bin/nbenchctl .nbench/bin/
cp ~/.codex/bin/nbenchctl.py .nbench/bin/
chmod +x .nbench/bin/nbenchctl

# Optional: configure review backend
~/.codex/bin/nbenchctl config set review.backend codex
```

## Caveats

- `/prompts:setup` not supported — use manual project setup above
- Hooks not supported (ralph-guard won't run in Codex)
- `claude-md-scout` is auto-renamed to `agents-md-scout` (CLAUDE.md → AGENTS.md patching)
