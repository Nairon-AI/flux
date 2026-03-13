---
name: flux:uninstall
description: Remove flux files from project
---

# Flux Uninstall

Use `AskUserQuestion` to confirm:

**Question 1:** "Remove flux from this project?"
- "Yes, uninstall"
- "Cancel"

If cancel → stop.

**Question 2:** "Keep your .flux/ tasks and epics?"
- "Yes, keep tasks" → partial uninstall
- "No, remove everything" → full uninstall

## Execute cleanup

The agent executes all cleanup directly — do not ask the user to run commands manually.

### Remove project artifacts

**If keeping tasks:**
```bash
rm -rf .flux/bin .flux/usage.md
```

**If removing everything:**
```bash
rm -rf .flux
```

**Always check for and remove Ralph if it exists:**
```bash
if [[ -d scripts/ralph ]]; then
  rm -rf scripts/ralph
fi
```

**Remove project-local MCP config and skills:**
```bash
rm -f .mcp.json
rm -rf .claude/skills/
```

### Clean up docs

For CLAUDE.md and AGENTS.md: if file exists, remove everything between `<!-- BEGIN FLUX -->` and `<!-- END FLUX -->` (inclusive).

### Remove plugin cache
```bash
rm -rf ~/.claude/plugins/cache/nairon-flux
```

## Report

```
Flux uninstalled.

Cleaned up:
- Flux project artifacts
- Project-local MCP config (.mcp.json)
- Project-local skills (.claude/skills/)
- Flux sections from docs (if existed)
- Plugin cache

To finish, run in your agent UI:
  /plugin uninstall flux@nairon-flux

Then restart with --resume.
```
