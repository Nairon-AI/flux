---
name: flux-grill
description: >-
  Relentless behavioral review after epic completion. Walks every branch of the
  design tree, verifying implemented behavior matches intent. Use when user says
  "grill me", "stress test the behavior", wants to verify an epic's behavioral
  coverage before shipping, or after /flux:epic-review to stress-test what was built.
user-invocable: false
---

# Grill — Behavioral Stress Test

Relentlessly interrogate the behavior of implemented changes until every branch of the decision tree is verified. This is NOT a code review — it's a behavior review. Code can be perfect and still do the wrong thing.

> "The most dangerous bugs are the ones where the code works exactly as written — it just does the wrong thing."

**IMPORTANT**: This plugin uses `.flux/` for ALL task tracking. Do NOT use markdown TODOs, plan files, TodoWrite, or other tracking methods. All task state must be read and written via `fluxctl`.

**CRITICAL: fluxctl is BUNDLED — NOT installed globally.** `which fluxctl` will fail (expected). Always use:
```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
[ ! -d "$PLUGIN_ROOT/scripts" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
$FLUXCTL <command>
```

## Session Phase Tracking

On entry, set the session phase:
```bash
$FLUXCTL session-phase set grill
```
On completion, reset:
```bash
$FLUXCTL session-phase set idle
```

**Agent Compatibility**: This skill works across Codex, OpenCode, and legacy Claude environments. See [agent-compat.md](../../docs/agent-compat.md) for tool differences.

**Question Tool**: Use the appropriate tool for your agent:
- Claude: `AskUserQuestion`
- OpenCode: `mcp_question`
- Codex: `AskUserTool`
- Other: Output question as text, wait for response

## Input

Full request: $ARGUMENTS

## When to Use

- After `/flux:epic-review` completes — epic-review checks code quality, grill checks behavioral correctness
- Before shipping a completed epic to production
- When the user wants to stress-test decisions and edge cases
- When a stakeholder asks "does it actually do what we said it would?"

## How It Differs From Other Reviews

| Skill | Focus |
|-------|-------|
| `/flux:impl-review` | Code quality per task |
| `/flux:epic-review` | Code quality + security + browser QA at epic level |
| `/flux:grill` | **Behavioral correctness** — does the implementation match intent? |

## Process

### 1. Load Context

Silently gather the epic's intent and what was built:

```bash
$FLUXCTL epic list
$FLUXCTL epic show <epic-id>
```

Also read:
- The epic spec (`.flux/epics/<id>/spec.md` or linked PRD)
- All completed task specs
- The git diff between the epic branch and main
- Any brain vault context (`.flux/brain/business/`, `.flux/brain/decisions/`)

**Goal**: Build a mental model of what was *supposed* to happen vs what *actually* happened.

### 2. Build the Decision Tree

From the epic spec and task specs, map out every behavioral branch:

- Every user action and its expected outcome
- Every edge case mentioned in the spec
- Every "what if" scenario (empty states, error states, concurrent users, invalid input)
- Every integration point (API contracts, database writes, external service calls)
- Every permission/auth boundary
- Every state transition

### 3. Walk Each Branch

For each branch of the decision tree, one at a time:

1. **State the expected behavior** — what should happen according to the spec
2. **Explore the codebase** to verify the behavior is actually implemented
3. **If answerable from code**: verify silently, move on
4. **If ambiguous or missing**: ask the user a pointed question with your recommended answer

**Question format**:
```
Branch: [what scenario we're examining]
Expected: [what should happen based on the spec]
Finding: [what I found in the code — or what's unclear]
Recommendation: [your suggested answer]

Does this match your intent?
```

**Rules**:
- Resolve dependencies between decisions before moving to dependent branches
- Don't ask about things you can verify by reading code — explore first
- When you find a gap, don't just flag it — propose what the behavior *should* be
- Be relentless — don't accept "that's fine" without verifying edge cases
- Group related questions to avoid question fatigue, but don't skip any branch

### 4. Edge Case Gauntlet

After walking the main branches, systematically probe edge cases:

- **Empty states**: What happens with no data? First-time user?
- **Boundary values**: Max lengths, zero values, negative numbers
- **Concurrency**: Two users doing the same thing simultaneously
- **Permissions**: What if the user doesn't have access?
- **Failure modes**: External service down, database timeout, network error
- **Rollback**: If step 3 of 5 fails, what state is the user left in?
- **Migration**: What happens to existing data/users?

### 5. Behavioral Summary

After all branches are resolved, present a summary:

```
## Behavioral Verification Summary

### Verified Behaviors
- [List of behaviors confirmed correct]

### Gaps Found
- [List of behaviors that are missing or incorrect, with recommendations]

### Decisions Made During Grill
- [List of ambiguities resolved during this session]

### Risk Areas
- [Behaviors that work but feel fragile or underspecified]
```

### 6. Capture Learnings

If any gaps or surprising findings emerged:

1. Update the epic spec with resolved ambiguities
2. If new tasks are needed, create them:
   ```bash
   $FLUXCTL task add --epic <epic-id> --title "Fix: [gap description]" --status pending
   ```
3. Write behavioral decisions to brain vault if they establish precedent:
   ```bash
   cat >> .flux/brain/decisions/[area].md << 'EOF'
   ## [Decision Title] — [Date]
   [What was decided and why]
   EOF
   ```

## Anti-Patterns

- **Don't review code** — that's `/flux:impl-review` and `/flux:epic-review`
- **Don't accept vague answers** — "yeah that should work" is not verification
- **Don't skip edge cases** because the happy path works
- **Don't batch all questions at once** — walk the tree branch by branch so each answer can inform the next question
- **Don't stop at the spec** — probe for behaviors the spec didn't mention but users will encounter

## Update Check (End of Command)

**ALWAYS run at the very end of /flux:grill execution:**

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
[ ! -d "$PLUGIN_ROOT/scripts" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
UPDATE_JSON=$("$PLUGIN_ROOT/scripts/version-check.sh" 2>/dev/null || echo '{"update_available":false}')
UPDATE_AVAILABLE=$(echo "$UPDATE_JSON" | jq -r '.update_available')
LOCAL_VER=$(echo "$UPDATE_JSON" | jq -r '.local_version')
REMOTE_VER=$(echo "$UPDATE_JSON" | jq -r '.remote_version')
```

**If update available**, append to output:

```
---
Flux update available: v${LOCAL_VER} → v${REMOTE_VER}
Update Flux from the same source you installed it from, then restart your agent session.
---
```

**If no update**: Show nothing (silent).

## Gotchas

- This skill explores the codebase heavily. If the epic touched many files, the first pass may take a while.
- Grill works best when the epic spec is detailed. If the spec is vague, grill will surface that — which is valuable but may feel like "too many questions."
- Some behavioral questions can only be answered by running the app. If browser verification is needed, suggest `/flux:browser` or manual testing for specific scenarios.
- Don't confuse "the code does X" with "X is the right behavior." The code is not the spec.
