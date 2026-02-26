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

## Generate removal instructions

Based on answers, generate the appropriate commands and print them for the user to run manually.

**If keeping tasks:**
```
To complete uninstall, run these commands manually:

rm -rf .flux/bin .flux/usage.md
```

**If removing everything:**
```
To complete uninstall, run these commands manually:

rm -rf .flow
```

**Always check for Ralph and add if exists:**
```bash
# Check if Ralph is installed
if [[ -d scripts/ralph ]]; then
  echo "rm -rf scripts/ralph"
fi
```

## Clean up docs (AI can do this)

For CLAUDE.md and AGENTS.md: if file exists, remove everything between `<!-- BEGIN NBENCH -->` and `<!-- END NBENCH -->` (inclusive). This is safe for the AI to execute.

## Report

```
Flux uninstall prepared.

Cleaned up:
- Flux sections from docs (if existed)

Run these commands manually to complete removal:
<commands from above>

Why manual? Destructive commands like rm -rf should have human hands on the keyboard.
If you use DCG (Destructive Command Guard), it will block these commands from AI agents - this is intentional protection.
```
