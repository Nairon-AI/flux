---
name: flux-desloppify
description: Systematic codebase quality improvement. Scans for dead code, duplication, complexity, naming issues, and architectural problems. Scoring resists gaming - only real improvements raise the score.
user-invocable: false
---

# Flux Desloppify

Codebase quality scanner and fix orchestrator powered by [desloppify](https://github.com/peteromallet/desloppify).

**Role**: quality assessor, iterative fixer
**Goal**: raise strict score to target (default 95) through systematic improvements

## What It Does

Combines mechanical detection (dead code, duplication, complexity) with subjective LLM review (naming, abstractions, module boundaries). Works through prioritized fix loop until target score reached.

| Tier | Fix Type | Examples |
|------|----------|----------|
| T1 | Auto-fixable | Unused imports, debug logs |
| T2 | Quick manual | Unused vars, dead exports |
| T3 | Needs judgment | Near-dupes, single_use abstractions |
| T4 | Major refactor | God components, mixed concerns |

Score is weighted (T4 = 4× T1). Strict score penalizes both open and wontfix.

## Input

Full request: $ARGUMENTS

Accepts:
- No arguments → full workflow (scan → fix loop)
- `scan` → scan only, show score
- `status` → current score and progress
- `next` → next priority fix
- `plan` → prioritized markdown plan
- `--path <dir>` → scan specific directory (default: `.`)
- `--target <N>` → target strict score (default: 95)

Examples:
- `/flux:desloppify` — full improvement workflow
- `/flux:desloppify scan --path src/` — scan src only
- `/flux:desloppify status` — check current score
- `/flux:desloppify next --tier 2` — next T2 fix

## Workflow

### Phase 1: Setup

1. Check if desloppify is installed:
   ```bash
   which desloppify || pip install --upgrade "desloppify[full]"
   ```

2. Install the Claude skill (provides workflow guidance):
   ```bash
   desloppify update-skill claude
   ```

### Phase 2: Initial Scan

Run full scan on target path:
```bash
desloppify scan --path .
```

Parse output for:
- Current strict score
- Issue counts by tier
- Top priority findings

### Phase 3: Fix Loop

Repeat until target score reached or no more fixable issues:

1. **Get next issue**:
   ```bash
   desloppify next
   ```

2. **Understand the issue**: Read the file, understand context

3. **Fix it properly**: Make the code genuinely better
   - Don't game the score
   - Large refactors are fine if needed
   - Small fixes are also valuable

4. **Resolve**:
   ```bash
   desloppify resolve fixed <pattern>
   ```

5. **Re-scan periodically** to refresh findings:
   ```bash
   desloppify scan --path .
   ```

### Phase 4: Report

When target reached or session ending:
- Show final score
- Summary of fixes applied
- Remaining issues by tier

## Commands Reference

| Command | Description |
|---------|-------------|
| `scan [--path <dir>]` | Run all detectors, update state |
| `status` | Score + per-tier progress |
| `next [--tier N]` | Highest-priority open finding |
| `resolve <status> <pattern>` | Mark: fixed, wontfix, false_positive |
| `fix <fixer> [--dry-run]` | Auto-fix mechanical issues |
| `plan` | Prioritized markdown plan |
| `tree` | Annotated codebase tree |
| `show <pattern>` | Findings by file/detector/ID |

## Guardrails

### Quality Over Speed
- Fix things properly, not superficially
- Large refactors are fine if that's what it takes
- Don't suppress warnings to game the score

### Transparency
- Show the user what's being fixed and why
- Explain trade-offs for judgment calls (T3/T4)
- Don't auto-resolve without user consent for T3+

### Scope
- Stay focused on the scan path
- Don't modify files outside the scanned directory
- Respect existing code style and conventions

## Target Score Guide

| Score | Quality Level |
|-------|---------------|
| <70 | Needs significant work |
| 70-84 | Functional but rough |
| 85-94 | Good, minor issues |
| 95-97 | Clean, well-maintained |
| 98+ | Beautiful, engineer-approved |

**Default target: 95** — achievable for most codebases with focused effort.

## State

Desloppify maintains state in `.desloppify/`:
- `state.json` — findings, resolutions, scores
- `config.json` — project settings
- `scorecard.png` — badge for README

State persists across sessions, so improvements accumulate.


---

## Update Check (End of Command)

**ALWAYS run at the very end of command execution:**

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}"
[ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
UPDATE_JSON=$("$PLUGIN_ROOT/scripts/version-check.sh" 2>/dev/null || echo '{"update_available":false}')
UPDATE_AVAILABLE=$(echo "$UPDATE_JSON" | jq -r '.update_available')
LOCAL_VER=$(echo "$UPDATE_JSON" | jq -r '.local_version')
REMOTE_VER=$(echo "$UPDATE_JSON" | jq -r '.remote_version')
```

**If update available**, append to output:

```
---
Flux update available: v${LOCAL_VER} → v${REMOTE_VER}
Run: /plugin marketplace update nairon-flux
Then restart Claude Code for changes to take effect.
---
```
