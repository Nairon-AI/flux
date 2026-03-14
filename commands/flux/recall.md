---
name: flux:recall
description: Search prior work by topic across Flux state, git, conversations, and memory. Find and resume where you left off.
argument-hint: "<topic>"
---

# IMPORTANT: This command MUST invoke the skill `flux-recall`

The ONLY purpose of this command is to call the `flux-recall` skill. You MUST use that skill now.

**User input:** $ARGUMENTS

Searches Flux epics, tasks, specs, memory, git history, conversation history, and project memory for the given topic. Shows structured results and suggests the next action.

Examples:
- `/flux:recall auth` — find all prior work related to authentication
- `/flux:recall payments` — recall payment-related epics, tasks, commits
- `/flux:recall migration` — find database migration work across sessions
