---
name: nbench-interview
description: Interview user about an epic, task, or spec file. Default is quick mode (5 min, MVP-focused). Use --deep for thorough 40+ question interview. Triggers on /nbench:interview with Flow IDs or file paths.
user-invocable: false
---

# Flow interview

Interview about a task/spec and write refined details back.

**Modes**:
- **Quick (default)**: 5 minutes, MVP-focused, 5-10 questions. Get just enough to start building.
- **Deep (`--deep`)**: Thorough 40+ question interview. Use for high-risk or ambiguous features.

> "You can't know everything upfront. Get enough to start, then iterate."

**IMPORTANT**: This plugin uses `.nbench/` for ALL task tracking. Do NOT use markdown TODOs, plan files, TodoWrite, or other tracking methods. All task state must be read and written via `nbenchctl`.

**CRITICAL: nbenchctl is BUNDLED — NOT installed globally.** `which nbenchctl` will fail (expected). Always use:
```bash
FLOWCTL="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}/scripts/nbenchctl"
$FLOWCTL <command>
```

## Pre-check: Local setup version

If `.nbench/meta.json` exists and has `setup_version`, compare to plugin version:
```bash
SETUP_VER=$(jq -r '.setup_version // empty' .nbench/meta.json 2>/dev/null)
# Portable: Claude Code uses .claude-plugin, Factory Droid uses .factory-plugin
PLUGIN_JSON="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}/.claude-plugin/plugin.json"
[[ -f "$PLUGIN_JSON" ]] || PLUGIN_JSON="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}/.factory-plugin/plugin.json"
PLUGIN_VER=$(jq -r '.version' "$PLUGIN_JSON" 2>/dev/null || echo "unknown")
if [[ -n "$SETUP_VER" && "$PLUGIN_VER" != "unknown" ]]; then
  [[ "$SETUP_VER" = "$PLUGIN_VER" ]] || echo "Plugin updated to v${PLUGIN_VER}. Run /nbench:setup to refresh local scripts (current: v${SETUP_VER})."
fi
```
Continue regardless (non-blocking).

**Role**: technical interviewer, spec refiner
**Goal**: extract enough detail to start building (quick) or complete details (deep)

## Input

Full request: $ARGUMENTS

**Options**:
- `--quick` (default): MVP-focused, 5-10 questions, ~5 minutes
- `--deep`: Thorough interview, 40+ questions, ~20-30 minutes

Accepts:
- **Flow epic ID** `fn-N-slug` (e.g., `fn-1-add-oauth`) or legacy `fn-N`/`fn-N-xxx`: Fetch with `nbenchctl show`, write back with `nbenchctl epic set-plan`
- **Flow task ID** `fn-N-slug.M` (e.g., `fn-1-add-oauth.2`) or legacy `fn-N.M`/`fn-N-xxx.M`: Fetch with `nbenchctl show`, write back with `nbenchctl task set-description/set-acceptance`
- **File path** (e.g., `docs/spec.md`): Read file, interview, rewrite file
- **Empty**: Prompt for target

Examples:
- `/nbench:interview fn-1-add-oauth` (quick mode)
- `/nbench:interview fn-1-add-oauth --deep` (thorough mode)
- `/nbench:interview fn-1-add-oauth.3`
- `/nbench:interview docs/oauth-spec.md`

If empty, ask: "What should I interview you about? Give me a Flow ID (e.g., fn-1-add-oauth) or file path (e.g., docs/spec.md)"

## Detect Mode

Parse arguments for `--deep` flag. Default is quick mode.

```
INTERVIEW_MODE = "--deep" in arguments ? "deep" : "quick"
```

## Setup

```bash
FLOWCTL="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}/scripts/nbenchctl"
```

## Detect Input Type

1. **Flow epic ID pattern**: matches `fn-\d+(-[a-z0-9-]+)?` (e.g., fn-1-add-oauth, fn-12, fn-2-fix-login-bug)
   - Fetch: `$FLOWCTL show <id> --json`
   - Read spec: `$FLOWCTL cat <id>`

2. **Flow task ID pattern**: matches `fn-\d+(-[a-z0-9-]+)?\.\d+` (e.g., fn-1-add-oauth.3, fn-12.5)
   - Fetch: `$FLOWCTL show <id> --json`
   - Read spec: `$FLOWCTL cat <id>`
   - Also get epic context: `$FLOWCTL cat <epic-id>`

3. **File path**: anything else with a path-like structure or .md extension
   - Read file contents
   - If file doesn't exist, ask user to provide valid path

## Interview Process

**CRITICAL REQUIREMENT**: You MUST use the `AskUserQuestion` tool for every question.

- DO NOT output questions as text
- DO NOT list questions in your response
- ONLY ask questions via AskUserQuestion tool calls
- Group 2-4 related questions per tool call

### Quick Mode (default)

**Goal**: Get just enough to start building. You'll learn more as you build.

**Time limit**: ~5 minutes
**Question count**: 5-10 questions max

Focus on:
1. **What's the smallest shippable version?** (MVP scope)
2. **What's the riskiest unknown?** (biggest assumption to validate)
3. **What does "done" look like?** (1-3 acceptance criteria)
4. **Any hard constraints?** (tech, timeline, compatibility)
5. **What can we defer?** (explicitly cut scope)

**Philosophy**: Don't try to answer every question upfront. Get enough to build something, ship it, feel it, then iterate.

### Deep Mode (`--deep`)

**Goal**: Extract complete implementation details for high-risk or ambiguous features.

**Time**: ~20-30 minutes
**Question count**: 40+ questions typical

Read [questions.md](questions.md) for all question categories.

Use deep mode when:
- Feature is high-risk or security-sensitive
- Requirements are genuinely ambiguous
- Failure cost is high (payments, data migration, etc.)
- User explicitly requests thorough planning

**Anti-pattern (WRONG)**:
```
Question 1: What database should we use?
Options: a) PostgreSQL b) SQLite c) MongoDB
```

**Correct pattern**: Call AskUserQuestion tool with question and options.

## NOT in scope (defer to /nbench:plan)

- Research scouts (codebase analysis)
- File/line references
- Task creation (interview refines requirements, plan creates tasks)
- Task sizing (S/M/L)
- Dependency ordering
- Phased implementation details

## Write Refined Spec

After interview complete, write everything back — **scope depends on input type**.

### For NEW IDEA (text input, no Flow ID)

Create epic with interview output. **DO NOT create tasks** — that's `/nbench:plan`'s job.

```bash
$FLOWCTL epic create --title "..." --json
$FLOWCTL epic set-plan <id> --file - --json <<'EOF'
# Epic Title

## Problem
Clear problem statement

## Key Decisions
Decisions made during interview (e.g., "Use OAuth not SAML", "Support mobile + web")

## Edge Cases
- Edge case 1
- Edge case 2

## Open Questions
Unresolved items that need research during planning

## Acceptance
- [ ] Criterion 1
- [ ] Criterion 2
EOF
```

Then suggest: "Run `/nbench:plan fn-N` to research best practices and create tasks."

### For EXISTING EPIC (fn-N that already has tasks)

**First check if tasks exist:**
```bash
$FLOWCTL tasks --epic <id> --json
```

**If tasks exist:** Only update the epic spec (add edge cases, clarify requirements). **Do NOT touch task specs** — plan already created them.

**If no tasks:** Update epic spec, then suggest `/nbench:plan`.

```bash
$FLOWCTL epic set-plan <id> --file - --json <<'EOF'
# Epic Title

## Problem
Clear problem statement

## Key Decisions
Decisions made during interview

## Edge Cases
- Edge case 1
- Edge case 2

## Open Questions
Unresolved items

## Acceptance
- [ ] Criterion 1
- [ ] Criterion 2
EOF
```

### For Flow Task ID (fn-N.M)

**First check if task has existing spec from planning:**
```bash
$FLOWCTL cat <id>
```

**If task has substantial planning content** (description with file refs, sizing, approach):
- **Do NOT overwrite** — planning detail would be lost
- Only ADD new acceptance criteria discovered in interview:
  ```bash
  # Read existing acceptance, append new criteria
  $FLOWCTL task set-acceptance <id> --file /tmp/acc.md --json
  ```
- Or suggest interviewing the epic instead: `/nbench:interview <epic-id>`

**If task is minimal** (just title, empty or stub description):
- Update task with interview findings
- Focus on **requirements**, not implementation details

```bash
$FLOWCTL task set-spec <id> --description /tmp/desc.md --acceptance /tmp/acc.md --json
```

Description should capture:
- What needs to be accomplished (not how)
- Edge cases discovered in interview
- Constraints and requirements

Do NOT add: file/line refs, sizing, implementation approach — that's plan's job.

### For File Path

Rewrite the file with refined spec:
- Preserve any existing structure/format
- Add sections for areas covered in interview
- Include edge cases, acceptance criteria
- Keep it requirements-focused (what, not how)

This is typically a pre-epic doc. After interview, suggest `/nbench:plan <file>` to create epic + tasks.

## Completion

Show summary:
- Mode used (quick/deep)
- Number of questions asked
- Key decisions captured
- What was written (Flow ID updated / file rewritten)

Suggest next step based on input type:
- New idea / epic without tasks → `/nbench:plan fn-N`
- Epic with tasks → `/nbench:work fn-N` (or more interview on specific tasks)
- Task → `/nbench:work fn-N.M`
- File → `/nbench:plan <file>`

### Quick Mode Reminder

After quick interview, remind user:

> "This is enough to start. Build something small, feel it, then we'll refine. Run `/nbench:interview fn-N --deep` later if you need thorough requirements."

## Philosophy

**Don't fall for the trap of waterfall development.**

You can't know everything upfront—neither can agents. The goal is:
1. Get enough context to not be stupid
2. Build something small
3. Feel it (does it work? does it feel right?)
4. Adapt based on what you learned
5. Repeat

Quick mode embodies this. Deep mode is for when you genuinely need thorough upfront planning (high-risk, ambiguous, expensive-to-fix).
