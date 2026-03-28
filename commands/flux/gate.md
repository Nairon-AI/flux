---
name: flux:gate
description: Validate staging after merge and promote toward production.
argument-hint: "[staging-url|pr-number]"
---

# IMPORTANT: This command MUST invoke the skill `flux-gate`

The ONLY purpose of this command is to call the `flux-gate` skill. You MUST use that skill now.

**User request:** $ARGUMENTS

Pass the user request to the skill. The skill handles staging validation, QA strategy selection, and promotion PR creation.
