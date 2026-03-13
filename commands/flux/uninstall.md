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

Try to execute each cleanup step directly. If any command is denied or blocked (e.g., by permission settings or a destructive command guard), collect it into a "manual steps" list instead.

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

For CLAUDE.md and AGENTS.md: if file exists, remove everything between `<!-- BEGIN FLUX -->` and `<!-- END FLUX -->` (inclusive). Use the Edit tool for this — it does not require Bash.

### Remove plugin cache
```bash
rm -rf ~/.claude/plugins/cache/nairon-flux
```

## Report

Print what was cleaned up and what still needs manual action:

```
Flux uninstalled.

Cleaned up:
- <list items the agent successfully executed>

Manual steps remaining:
- <list any commands that were blocked — print the exact commands>
- Run in your agent UI: /plugin uninstall flux@nairon-flux
- Restart with --resume
```

If all cleanup commands succeeded, the "Manual steps remaining" section only contains the `/plugin uninstall` and restart steps.
