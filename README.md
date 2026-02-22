<div align="center">

# Flux

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Plugin-blueviolet)](https://claude.ai/code)

**Your AI workflow has gaps. Flux finds them.**

</div>

---

## The Problem

You're using AI agents, but something's off:

- You keep re-explaining the same context
- The agent tries the same broken approach 5 times
- You discover a tool that would've saved hours—after the fact
- Requirements drift mid-session and nobody notices

These aren't model failures. They're **process failures**.

---

## What Flux Does

Flux analyzes your **actual coding sessions** to find friction—then recommends specific tools that would have helped.

```
/flux:improve
```

That's it. Flux reads your session history, detects patterns of frustration, checks what you already have installed, and shows you exactly what's missing.

---

## Example Output

```
Step 1/4 ✓ Extracted 847 messages from 12 sessions

Step 2/4 ✓ Detected friction signals:
  - "still not working" (3 occurrences)
  - "why is this" (2 occurrences)  
  - repeated test failures in same file

Step 3/4 ✓ Analyzed your setup:
  OS: macOS
  CLI: jq, fzf, eslint
  MCPs: playwright
  Missing: git hooks, design tools, issue tracking

Step 4/4 ✓ Matched recommendations:

┌─────────────────────────────────────────────────────────────┐
│ REVIEW                                                      │
├─────────────────────────────────────────────────────────────┤
│ Lefthook (free)                                             │
│ → Pre-commit hooks catch errors in 5 sec, not 5 min         │
│ → You had 3 "lint error" messages that hooks would prevent  │
├─────────────────────────────────────────────────────────────┤
│ PLANNING                                                    │
├─────────────────────────────────────────────────────────────┤
│ Linear ($8/user) or Beads (free)                            │
│ → Issue tracking keeps requirements from drifting           │
│ → You re-explained context 4 times across sessions          │
└─────────────────────────────────────────────────────────────┘

Which improvements would you like to apply?
☐ Lefthook - Add pre-commit hooks
☐ Beads - Install task tracking
☐ AGENTS.md - Create project context file
```

---

## Install

### Claude Code

```bash
/plugin marketplace add Nairon-AI/flux
/plugin install flux@nairon-flux
```

### OpenCode

```bash
/plugin marketplace add Nairon-AI/flux
/plugin install flux@nairon-flux
```

### Factory Droid

```bash
droid plugin marketplace add https://github.com/Nairon-AI/flux
```

Then `/plugins` → Marketplace → install flux.

---

## Commands

| Command | Description |
|---------|-------------|
| `/flux:improve` | Analyze sessions, find gaps, get recommendations |
| `/flux:improve --detect` | Just show what's installed (no recommendations) |
| `/flux:improve --dismiss X` | Never recommend X again |
| `/flux:plan` | Break a feature into dependency-aware tasks |
| `/flux:work` | Execute a task with automatic context reload |

---

## How It Works

1. **Extracts** your session history (OpenCode SQLite or Claude Code JSONL)
2. **Detects friction** — keywords like "again", "still", "why", repeated failures
3. **Scans your setup** — OS, CLI tools, MCPs, apps, repo configs
4. **Matches gaps** to 26+ curated recommendations with pricing
5. **Asks** which improvements to apply
6. **Implements** — installs tools, adds AGENTS.md rules, configures hooks

Preferences saved to `.flux/preferences.json` so dismissed items stay dismissed.

---

## Daily Usage

**Weekly check-in** — Run after a few coding sessions:
```
/flux:improve
```
Review what friction patterns emerged. Apply fixes that make sense.

**Before starting a feature** — Plan first:
```
/flux:plan Add dark mode toggle to settings
```
Creates tasks in `.flux/` with dependencies mapped out.

**Execute tasks** — One at a time with context reload:
```
/flux:work fx-1.1
```
Re-anchors to the plan before each task. Nothing drifts.

**Dismiss noise** — Tool not relevant to you?
```
/flux:improve --dismiss figma
```
Won't suggest it again.

---

## License

MIT
