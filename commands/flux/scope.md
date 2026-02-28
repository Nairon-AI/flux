---
name: flux:scope
description: Combined requirements gathering and planning. Uses Double Diamond process (Problem Space → Solution Space). Default is quick mode (~10 min). Use --deep for thorough scoping (~45 min).
argument-hint: "<feature description or spec file> [--deep]"
---

# IMPORTANT: This command MUST invoke the skill `flux-scope`

The ONLY purpose of this command is to call the `flux-scope` skill. You MUST use that skill now.

**User input:** $ARGUMENTS

**Modes:**
- Default: Quick mode (~10 min, MVP-focused discovery + short plan)
- `--deep`: Thorough mode (~45 min, full discovery + detailed plan)

**Process:**
1. Problem Space: Discover why → Define problem statement
2. Solution Space: Research codebase → Create epic + tasks

Pass the user input to the skill. The skill handles the full Double Diamond workflow.
