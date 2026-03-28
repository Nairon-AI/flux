---
name: flux:uninstall
description: Remove flux files from project (scoped or full machine)
---

# Flux Uninstall

Use `AskUserQuestion` to confirm:

**Question 1:** "Remove flux from this project?"
- "Yes, uninstall"
- "Cancel"

If cancel → stop.

**Question 2:** "How much do you want to remove?"
- "This project only" → **project uninstall** (default, safe)
- "This project + keep tasks" → **partial project uninstall**
- "Everything on this machine" → **full machine uninstall**

## Project Uninstall (default)

Only removes Flux artifacts from the current repo. Does NOT touch global state — other projects using Flux are unaffected.

Try to execute each cleanup step directly. If any command is denied or blocked (e.g., by permission settings or a destructive command guard), collect it into a "manual steps" list instead.

### Remove project artifacts

**If removing everything:**
```bash
rm -rf .flux
```

**If keeping tasks (partial):**
```bash
rm -rf .flux/bin .flux/usage.md .flux/version
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
rm -rf .secureskills/
rm -rf .codex/skills/
rm -rf .claude/skills/
```

### Clean up docs

For CLAUDE.md and AGENTS.md: if file exists, remove everything between `<!-- BEGIN FLUX -->` and `<!-- END FLUX -->` (inclusive). Use the Edit tool for this — it does not require Bash.

### Report (project uninstall)

```
Flux removed from this project.

Cleaned up:
- <list items the agent successfully executed>

Note: The global Flux plugin is still installed. Other projects
using Flux are unaffected. To remove Flux from your entire machine,
run /flux uninstall again and choose "Everything on this machine".
```

---

## Full Machine Uninstall

Removes Flux from the current project AND all global state. This will affect every project on the machine that uses Flux.

Before proceeding, scan for other projects that may be using Flux:

```bash
# Check common project locations for .flux/ directories
find ~/Developer ~/Projects ~/Code ~/repos ~/src ~/work ~ -maxdepth 3 -name ".flux" -type d 2>/dev/null | head -20
```

If other projects are found, warn the user:

> Found Flux installed in these other projects:
> - /path/to/project-a
> - /path/to/project-b
>
> Removing the global plugin will break Flux in all of them.
> Continue?

Use `AskUserQuestion`:
- "Yes, remove everything"
- "No, just this project" → fall back to project uninstall

### Execute full cleanup

**Step 1 — Project cleanup** (same as project uninstall above)

**Step 2 — Global cleanup:**
```bash
# Remove legacy plugin cache
rm -rf ~/.claude/plugins/cache/nairon-flux
```

### Report (full machine uninstall)

```
Flux fully uninstalled from this machine.

Cleaned up:
- <list items the agent successfully executed>

Manual steps remaining:
- <list any commands that were blocked — print the exact commands>
- If you installed Flux into any legacy agent/plugin UI, remove that install there too
- Restart your agent session
```

If all cleanup commands succeeded, the "Manual steps remaining" section only contains any legacy plugin cleanup and restart steps.
