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

Generate the appropriate commands and print them for the user to run manually. Destructive commands like `rm -rf` should have human hands on the keyboard.

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
rm -rf .claude/skills/
```

### Clean up docs

For CLAUDE.md and AGENTS.md: if file exists, remove everything between `<!-- BEGIN FLUX -->` and `<!-- END FLUX -->` (inclusive). Use the Edit tool for this — it does not require Bash and is safe for the AI to execute directly.

### Report (project uninstall)

```
Flux removed from this project.

Cleaned up:
- Flux sections from docs (if existed)

Run these commands manually to complete removal:
<commands from above>

Note: The global Flux plugin is still installed. Other projects
using Flux are unaffected. To remove Flux from your entire machine,
run /flux uninstall again and choose "Everything on this machine".

Why manual? Destructive commands like rm -rf should have human hands on the keyboard.
If you use DCG (Destructive Command Guard), it will block these commands from AI agents — this is intentional protection.
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

**Step 1 — Project cleanup** (same commands as project uninstall above, printed for user to run manually)

**Step 2 — Global cleanup:**
```bash
# Remove plugin cache
rm -rf ~/.claude/plugins/cache/nairon-flux
```

### Report (full machine uninstall)

```
Flux fully uninstalled from this machine.

Cleaned up:
- Flux sections from docs (if existed)

Run these commands manually to complete removal:
<all commands from above, including global cleanup>

Manual steps remaining:
- <list any commands that were blocked — print the exact commands>
- Run in your agent UI: /plugin uninstall flux@nairon-flux
- Restart with --resume
```

If all cleanup commands succeeded, the "Manual steps remaining" section only contains the `/plugin uninstall` and restart steps.
