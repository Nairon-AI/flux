---
name: flux:export-context
description: Export RepoPrompt review context for use with external LLMs.
argument-hint: "<plan <epic-id>|impl> [focus areas]"
---

# IMPORTANT: This command MUST invoke the skill `flux-export-context`

The ONLY purpose of this command is to call the `flux-export-context` skill. You MUST use that skill now.

**User request:** $ARGUMENTS

Pass the user request to the skill. The skill handles review-pack export for external models.
