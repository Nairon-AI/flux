---
name: flux-design-interface
description: >-
  Generate multiple radically different interface designs for a module using parallel
  sub-agents, then compare and synthesize. Based on "Design It Twice" from "A Philosophy
  of Software Design". Use when user wants to design an API, explore interface options,
  compare module shapes, or says "design it twice".
user-invocable: false
---

# Design an Interface

Your first idea is unlikely to be the best. Generate multiple radically different designs using parallel sub-agents, then compare.

> "Design It Twice" — John Ousterhout, "A Philosophy of Software Design"

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
$FLUXCTL session-phase set design_interface
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

## Workflow

### 1. Gather Requirements

Before designing, understand:

- What problem does this module solve?
- Who are the callers? (other modules, external users, tests)
- What are the key operations?
- Any constraints? (performance, compatibility, existing patterns)
- What should be hidden inside vs exposed?

Also explore the codebase to understand existing patterns:
- How are similar modules structured in this project?
- What conventions exist for interfaces?
- Are there dependency injection patterns already in use?

### 2. Generate Designs (Parallel Sub-Agents)

Spawn 3+ sub-agents simultaneously using the Agent tool. Each must produce a **radically different** approach.

Give each agent a different design constraint:
- **Agent 1**: "Minimize method count — aim for 1-3 methods max"
- **Agent 2**: "Maximize flexibility — support many use cases and extension"
- **Agent 3**: "Optimize for the most common case — make the default trivial"
- **Agent 4** (optional): "Take inspiration from [specific paradigm/library relevant to the project]"

Each sub-agent outputs:
1. Interface signature (types, methods, params)
2. Usage example (how callers use it)
3. What this design hides internally
4. Trade-offs of this approach

### 3. Present Designs

Show each design with:
1. **Interface signature** — types, methods, params
2. **Usage examples** — how callers actually use it in practice
3. **What it hides** — complexity kept internal

Present designs sequentially so user can absorb each approach before comparison.

### 4. Compare Designs

After showing all designs, compare them on:

- **Interface simplicity**: fewer methods, simpler params
- **General-purpose vs specialized**: flexibility vs focus
- **Implementation efficiency**: does shape allow efficient internals?
- **Depth**: small interface hiding significant complexity (good) vs large interface with thin implementation (bad)
- **Ease of correct use** vs **ease of misuse**

Discuss trade-offs in prose, not tables. Highlight where designs diverge most.

**Be opinionated** — give your recommendation for which design is strongest and why. If elements from different designs combine well, propose a hybrid.

### 5. Synthesize

Ask:
- "Which design best fits your primary use case?"
- "Any elements from other designs worth incorporating?"

## Evaluation Criteria

From "A Philosophy of Software Design":

- **Interface simplicity**: Fewer methods, simpler params = easier to learn and use correctly.
- **General-purpose**: Can handle future use cases without changes. But beware over-generalization.
- **Implementation efficiency**: Does interface shape allow efficient implementation? Or force awkward internals?
- **Depth**: Small interface hiding significant complexity = deep module (good). Large interface with thin implementation = shallow module (avoid).

## Anti-Patterns

- Don't let sub-agents produce similar designs — enforce radical difference
- Don't skip comparison — the value is in contrast
- Don't implement — this is purely about interface shape
- Don't evaluate based on implementation effort

## Update Check (End of Command)

**ALWAYS run at the very end of /flux:design-interface execution:**

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

- This skill requires the Agent tool for parallel sub-agents. If running in an environment without sub-agent support, generate designs sequentially instead.
- Sub-agents need full context about the module — include file paths, coupling details, and dependency patterns in each sub-agent prompt.
- The value is in the *comparison*, not the designs themselves. Spending extra time on comparison is always worth it.
