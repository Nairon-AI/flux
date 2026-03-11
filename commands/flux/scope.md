---
name: flux:scope
description: Full Product OS-style scoping workflow for features, bugs, and refactors. Default is shallow mode; use --deep for the full staged experience. Use --linear or LIN-123 to pull context from Linear.
argument-hint: "<feature|bug|refactor description or spec file> [--deep] [--linear | LIN-123]"
---

# IMPORTANT: This command MUST invoke the skill `flux-scope`

The ONLY purpose of this command is to call the `flux-scope` skill. You MUST use that skill now.

**User input:** $ARGUMENTS

**Modes:**
- Default: Shallow mode (~10 min, compressed scoping + fast implementation package)
- `--deep`: Deep mode (~45 min, full Start -> Discover -> Define -> Develop -> Deliver -> Handoff flow)
- `--linear`: Connect to Linear MCP, browse teams/projects, select issue to scope
- `LIN-123`: Directly scope a specific Linear issue (shorthand for --linear)

**Process:**
1. Start: classify feature/bug/refactor, depth, technical level, implementation target
2. Problem Space: Discover why -> Define problem statement
3. Solution Space: Develop approach -> Deliver implementation package -> Handoff to `/flux:work` or engineer summary

Pass the user input to the skill. The skill handles the full Double Diamond workflow.
