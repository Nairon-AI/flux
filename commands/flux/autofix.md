---
name: flux:autofix
description: Start Claude cloud auto-fix on a submitted PR.
argument-hint: "[pr-url|pr-number]"
---

# IMPORTANT: This command MUST invoke the skill `flux-autofix`

The ONLY purpose of this command is to call the `flux-autofix` skill. You MUST use that skill now.

**User request:** $ARGUMENTS

Pass the user request to the skill. The skill handles PR resolution and remote auto-fix kickoff.
