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
2. **Asks for optional pain point description** (dramatically improves accuracy)
3. Analyzes local environment (repo structure, MCPs, plugins, configs)
4. Optionally analyzes session history for pain points (with consent)
5. Fetches recommendations from `nairon-ai/flux-recommendations`
6. Uses AI to match relevant recommendations to user's context
7. Presents recommendations with impact ranking
8. Handles installation and verification

## User Context (Optional but Powerful)

After consent, ask users to describe frustrations in a few words. Even brief context like "fighting CSS" or "keeps forgetting things" **dramatically improves** recommendation accuracy.

The matching engine maps common phrases to friction signals:
- "CSS battles" → css_issues, ui_issues
- "keeps forgetting" → context_forgotten
- "wrong API docs" → api_hallucination, outdated_docs
- "slow builds" → slow_builds
- "missed edge cases" → shallow_answers

This is optional - automated session analysis works alone, but user context makes it much better.

## Input

Full request: $ARGUMENTS

Options:
- `--skip-sessions` - Skip session history analysis
- `--category=<cat>` - Filter to specific category (mcp, cli, plugin, skill, vscode, pattern)
- `--list` - Just list all available recommendations without analysis
- `--score` - Just show workflow score without recommendations
- `--discover` - Optional live discovery from X/Twitter (Exa-first, BYOK fallback)

## Workflow

Follow [workflow.md](workflow.md) exactly.

## Key Principles

1. **Privacy first** - Local by default. `--discover` is optional and sends search queries to Exa/Twitter APIs.
2. **Consent required** - Use `mcp_question` to get explicit consent before analyzing session history.
3. **Non-blocking** - User can skip any step or recommendation.
4. **Verification** - Every installation is verified before marking complete.
5. **Rollback ready** - Snapshot configs before any changes.

## Session Analysis Consent

Before reading any session files from `~/.claude/projects/`, you MUST:

1. Display the privacy notice (what data is analyzed)
2. Use `mcp_question` tool to ask for consent
3. Only proceed with session analysis if user explicitly consents

If user passes `--skip-sessions`, skip the consent question entirely.

## Recommendations Database

Fetched from: `https://github.com/Nairon-AI/flux-recommendations`

Categories:
- `mcps/` - Model Context Protocol servers
- `plugins/` - Claude Code plugins
- `skills/` - Standalone skills
- `cli-tools/` - Development CLI tools
- `vscode-extensions/` - VS Code extensions
- `workflow-patterns/` - Best practices (not tools)
