---
name: flux-tdd
description: >-
  Test-driven development with red-green-refactor vertical slices. Use when implementing
  features or fixes TDD-style, when user says "TDD", "test first", "red green refactor",
  or wants to build a feature one test at a time. Works standalone or inside /flux:work.
user-invocable: false
---

# TDD — Test-Driven Development

Build features and fix bugs one vertical slice at a time: write ONE test (RED), write minimal code to pass (GREEN), repeat. Refactor only after all tests pass.

> "Tests should verify behavior through public interfaces, not implementation details. Code can change entirely; tests shouldn't."

**IMPORTANT**: This plugin uses `.flux/` for ALL task tracking. Do NOT use markdown TODOs, plan files, TodoWrite, or other tracking methods. All task state must be read and written via `fluxctl`.

**CRITICAL: fluxctl is BUNDLED — NOT installed globally.** `which fluxctl` will fail (expected). Always use:
```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}"
[ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
$FLUXCTL <command>
```

## Session Phase Tracking

On entry, set the session phase:
```bash
$FLUXCTL session-phase set tdd
```
On completion, reset:
```bash
$FLUXCTL session-phase set idle
```

**Agent Compatibility**: This skill works across Claude Code, OpenCode, and Codex. See [agent-compat.md](../../docs/agent-compat.md) for tool differences.

**Question Tool**: Use the appropriate tool for your agent:
- Claude Code: `AskUserQuestion`
- OpenCode: `mcp_question`
- Codex: `AskUserTool`
- Other: Output question as text, wait for response

## Input

Full request: $ARGUMENTS

## Anti-Pattern: Horizontal Slices

**DO NOT write all tests first, then all implementation.** This produces bad tests:

- Tests written in bulk test *imagined* behavior, not *actual* behavior
- You test the *shape* of things (data structures, function signatures) rather than user-facing behavior
- Tests become insensitive to real changes — they pass when behavior breaks, fail when behavior is fine

```
WRONG (horizontal):
  RED:   test1, test2, test3, test4, test5
  GREEN: impl1, impl2, impl3, impl4, impl5

RIGHT (vertical):
  RED→GREEN: test1→impl1
  RED→GREEN: test2→impl2
  RED→GREEN: test3→impl3
```

## Workflow

### 1. Planning

Before writing any code:

- Confirm with user what interface changes are needed
- Confirm which behaviors to test (prioritize — you can't test everything)
- Look for opportunities to build [deep modules](references/deep-modules.md) (small interface, deep implementation)
- Design interfaces for [testability](references/interface-design.md)
- List the behaviors to test (not implementation steps)
- Get user approval on the plan

Ask: "What should the public interface look like? Which behaviors are most important to test?"

### 2. Tracer Bullet

Write ONE test that confirms ONE thing about the system:

```
RED:   Write test for first behavior → test fails
GREEN: Write minimal code to pass → test passes
```

This proves the path works end-to-end.

### 3. Incremental Loop

For each remaining behavior:

```
RED:   Write next test → fails
GREEN: Minimal code to pass → passes
```

Rules:
- One test at a time
- Only enough code to pass current test
- Don't anticipate future tests
- Keep tests focused on observable behavior

### 4. Refactor

After all tests pass, look for refactor candidates:

- Extract duplication
- Deepen modules (move complexity behind simple interfaces)
- Apply SOLID principles where natural
- Consider what new code reveals about existing code

**Never refactor while RED.** Get to GREEN first.

## Per-Cycle Checklist

```
[ ] Test describes behavior, not implementation
[ ] Test uses public interface only
[ ] Test would survive internal refactor
[ ] Code is minimal for this test
[ ] No speculative features added
```

## When to Mock

Mock at **system boundaries** only:
- External APIs (payment, email, etc.)
- Databases (prefer test DB when possible)
- Time/randomness
- File system (sometimes)

Don't mock:
- Your own classes/modules
- Internal collaborators
- Anything you control

See [references/mocking.md](references/mocking.md) for patterns.

## Update Check (End of Command)

**ALWAYS run at the very end of /flux:tdd execution:**

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}"
[ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
UPDATE_JSON=$("$PLUGIN_ROOT/scripts/version-check.sh" 2>/dev/null || echo '{"update_available":false}')
UPDATE_AVAILABLE=$(echo "$UPDATE_JSON" | jq -r '.update_available')
LOCAL_VER=$(echo "$UPDATE_JSON" | jq -r '.local_version')
REMOTE_VER=$(echo "$UPDATE_JSON" | jq -r '.remote_version')
```

**If update available**, append to output:

```
---
Flux update available: v${LOCAL_VER} → v${REMOTE_VER}
Run: /plugin uninstall flux@nairon-flux && /plugin add https://github.com/Nairon-AI/flux@latest
Then restart Claude Code for changes to take effect.
---
```

**If no update**: Show nothing (silent).

## Gotchas

- If the project has no test runner configured, detect and set up vitest/jest/pytest before starting.
- Vertical slicing feels slow at first — that's the point. Each test responds to what you learned from the previous cycle.
- "Write minimal code" means minimal. Don't add error handling, validation, or edge cases until a test demands them.
- If a test is hard to write, the interface is probably wrong. Redesign the interface, don't force the test.
