---
name: flux-improve
description: Analyze environment and recommend workflow optimizations (MCPs, plugins, skills, CLI tools, patterns). Use when user wants to discover and install development workflow improvements.
user-invocable: false
---

# Flux Improve

Analyze user's environment and recommend workflow optimizations from a curated database.

## Overview

This skill:
1. Shows privacy notice and gets consent
2. Analyzes local environment (repo structure, MCPs, plugins, configs)
3. Optionally analyzes session history for pain points (with consent)
4. Fetches recommendations from `nairon-ai/flux-recommendations`
5. Uses AI to match relevant recommendations to user's context
6. Presents recommendations with impact ranking
7. Handles installation and verification

## Input

Full request: $ARGUMENTS

Options:
- `--skip-sessions` - Skip session history analysis
- `--category=<cat>` - Filter to specific category (mcp, cli, plugin, skill, vscode, pattern)
- `--list` - Just list all available recommendations without analysis
- `--score` - Just show workflow score without recommendations

## Workflow

Follow [workflow.md](workflow.md) exactly.

## Key Principles

1. **Privacy first** - Everything happens locally. Nothing sent externally.
2. **Consent required** - Always ask before analyzing session history.
3. **Non-blocking** - User can skip any step or recommendation.
4. **Verification** - Every installation is verified before marking complete.
5. **Rollback ready** - Snapshot configs before any changes.

## Recommendations Database

Fetched from: `https://github.com/Nairon-AI/flux-recommendations`

Categories:
- `mcps/` - Model Context Protocol servers
- `plugins/` - Claude Code plugins
- `skills/` - Standalone skills
- `cli-tools/` - Development CLI tools
- `vscode-extensions/` - VS Code extensions
- `workflow-patterns/` - Best practices (not tools)
