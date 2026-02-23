---
name: nbench:interview
description: Quick interview (default) or deep requirements gathering. Use --deep for thorough 40+ question interview.
argument-hint: "[epic ID, task ID, or file path] [--deep]"
---

# IMPORTANT: This command MUST invoke the skill `nbench-interview`

The ONLY purpose of this command is to call the `nbench-interview` skill. You MUST use that skill now.

**User input:** $ARGUMENTS

**Modes:**
- Default: Quick mode (~5 min, MVP-focused, 5-10 questions)
- `--deep`: Thorough mode (~20-30 min, 40+ questions)

Pass the user input to the skill. The skill handles the interview logic.
