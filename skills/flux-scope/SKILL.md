---
name: flux-scope
description: Full Product OS-style scoping workflow for features, bugs, and refactors. Guides through Start, Discover, Define, Develop, Deliver, and Handoff. Default is shallow mode (~10 min). Use --deep for the full staged flow (~45 min).
user-invocable: false
---

# Flow scope

Turn a rough idea into a well-defined objective using a Product OS-style workflow adapted for engineering.

**Flux Scope Flow:**
```
START -> DISCOVER -> DEFINE -> DEVELOP -> DELIVER -> HANDOFF
```

**Modes**:
- **Shallow (default)**: ~10 min total. Compressed scoping for smaller or clearer work.
- **Deep (`--deep`)**: ~45 min total. Full staged workflow with stronger gates, more edge cases, and richer handoff.
- **Explore (`--explore [N]`)**: Generate N competing approaches, scaffold each in parallel, compare visually, pick winner.

> "Understand the problem before solving it. Most failed features solve the wrong problem."
> "Write ten specs. Test them all. Throw away nine."

**IMPORTANT**: This plugin uses `.flux/` for ALL task tracking. Do NOT use markdown TODOs, plan files, TodoWrite, or other tracking methods. All task state must be read and written via `fluxctl`.

**CRITICAL: fluxctl is BUNDLED — NOT installed globally.** `which fluxctl` will fail (expected). Always use:
```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}"
[ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
$FLUXCTL <command>
```

**Agent Compatibility**: This skill works across Claude Code, OpenCode, and Codex. See [agent-compat.md](../../docs/agent-compat.md) for tool differences.

**Question Tool**: Use the appropriate tool for your agent:
- Claude Code: `AskUserQuestion`
- OpenCode: `mcp_question`
- Codex: `AskUserTool`
- Other: Output question as text, wait for response

## Pre-check: Local setup version

If `.flux/meta.json` exists and has `setup_version`, compare to plugin version:
```bash
SETUP_VER=$(jq -r '.setup_version // empty' .flux/meta.json 2>/dev/null)
PLUGIN_ROOT="${PLUGIN_ROOT}"
[ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
PLUGIN_JSON="${PLUGIN_ROOT}/.claude-plugin/plugin.json"
PLUGIN_VER=$(jq -r '.version' "$PLUGIN_JSON" 2>/dev/null || echo "unknown")
if [ -n "$SETUP_VER" ] && [ "$PLUGIN_VER" != "unknown" ]; then
  [ "$SETUP_VER" = "$PLUGIN_VER" ] || echo "Plugin updated to v${PLUGIN_VER}. Run /flux:setup to refresh local scripts (current: v${SETUP_VER})."
fi
```
Continue regardless (non-blocking).

**Role**: product-minded technical interviewer and planner
**Goal**: understand the problem deeply, keep the user aligned to the current workflow, then create actionable implementation context

## Input

Full request: $ARGUMENTS

**Options**:
- `--quick` / default shallow mode: compressed Product OS flow, ~10 min total
- `--deep`: Full staged scoping, ~45 min total
- `--explore [N]`: Generate N approaches (default 3), scaffold each in parallel, compare visually
- `--linear`: Connect to Linear MCP, browse teams/projects, select issue to scope
- `LIN-123` (or any `XXX-123` pattern): Directly scope a specific Linear issue

Accepts:
- Feature/bug description in natural language
- File path to spec document
- Linear issue identifier (e.g., `LIN-123`, `PROJ-456`)

Examples:
- `/flux:scope Add OAuth login for users`
- `/flux:scope Add user notifications --deep`
- `/flux:scope docs/feature-spec.md`
- `/flux:scope Add permissions system --explore 4`
- `/flux:scope Add dashboard --explore --deep`
- `/flux:scope --linear` — Browse Linear, select issue to scope
- `/flux:scope LIN-42` — Scope Linear issue LIN-42 directly
- `/flux:scope PROJ-123 --deep` — Deep scope Linear issue PROJ-123

If empty, ask: "What should I scope? Describe the feature or bug in 1-5 sentences."

## Detect Stakeholder vs Engineer

Before detecting mode, check if the user is a non-technical stakeholder rather than an engineer.

**Skip detection entirely if ANY of these are present** (strong engineer signals):
- Mentions specific files, paths, or line numbers
- References APIs, endpoints, databases, schemas, components, services, or architecture
- Uses technical verbs: "refactor", "migrate", "deploy", "integrate", "implement"
- Includes code snippets, error messages, or stack traces

**Detection signals** (check the input text if no engineer signals found):
- Language focuses on **outcomes** not implementation ("I want users to be able to..." vs "Add an API endpoint for...")
- Describes **what** without **how**
- Talks about business goals, customer needs, revenue, or user experience
- Uses non-technical framing: "customers want...", "our team needs...", "it would be great if..."

If 3+ signals are present and zero engineer signals, ask:

> "It sounds like you're describing what you'd like built rather than how to build it. Are you an engineer planning to implement this, or are you proposing a feature for the engineering team?"

- If **stakeholder** → hand off to `flux-propose` skill with their input preserved. Stop here.
- If **engineer** → continue with `/flux:scope` normally.

## Detect Mode

Parse arguments for `--deep` flag. Default is shallow mode.

```
SCOPE_MODE = "--deep" in arguments ? "deep" : "shallow"
```

## Session Realignment

Before asking new scoping questions, check current workflow state:

```bash
$FLUXCTL session-state --json
```

If there is an active scoped objective, resume it instead of silently starting over.
If there is active implementation work, tell the user and only re-enter scope if they clearly want to switch objectives.
Flux should always prefer alignment with `.flux/` state over treating each prompt as stateless.

## Detect Linear Mode

Check for `--linear` flag or Linear issue ID pattern (e.g., `LIN-123`, `PROJ-456`).

```
LINEAR_MODE = "--linear" in arguments
LINEAR_ISSUE_ID = extract pattern matching /[A-Z]+-\d+/ from arguments
```

If `LINEAR_ISSUE_ID` is found, set `LINEAR_MODE = true`.

**If LINEAR_MODE**: Read [linear.md](linear.md) for the full Linear integration flow (Steps 0.1-0.7). After completing, continue to Phase 1 with Linear context pre-loaded.

## Setup

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}"
[ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
$FLUXCTL init --json
```

---

# PHASE 1: PROBLEM SPACE

**Read [questions.md](questions.md) for the full question bank and guidelines.**
**See [phases.md](phases.md) for phase overview and anti-patterns.**

Walk through Steps 1-6 using the question tool. Each step has quick-mode and deep-mode variants.

| Step | Focus | Goal |
|------|-------|------|
| 1. Core Desire | WHY | Understand why this is being requested |
| 2. Reasoning Chain | LOGIC | Validate the logic from problem to solution |
| 3. User Perspective | WHO | Understand how users will experience this |
| 4. Blind Spots | GAPS | Surface what might be missing |
| 5. Risks | DANGER | Identify what could go wrong |
| 6. Problem Statement | CONVERGE | Synthesize into one clear statement |

**Step 6 output** — present synthesis and confirm:
```
Based on our discussion:
- Core need: [summary]
- Key assumptions: [list]
- User impact: [summary]
- Main risk: [summary]

Proposed problem statement:
"[One sentence problem statement]"

Does this capture it? What would you change?
```

---

# EXPLORE MODE (if --explore)

If `--explore` flag is set, diverge on approaches before converging to solution.

**Read [explore.md](explore.md) for architecture overview.**
**Read [approaches.md](approaches.md) for approach pattern reference.**
**Read [explore-steps.md](explore-steps.md) for detailed execution (Steps 6.5-6.11).**

Summary: Generate N fundamentally different approaches (varying on axes like interaction pattern, architecture, or where logic lives), scaffold each in a parallel git worktree, generate visual previews, present comparison matrix, and let the user pick a winner, request a hybrid, or refine.

---

# PHASE 2: SOLUTION SPACE

**Read [solution.md](solution.md) for detailed Steps 7-12.**

| Step | Focus |
|------|-------|
| 7. Create Epic | Persist problem statement as epic |
| 7.5. Stakeholder Check | Identify who's affected |
| 8. Research | Run scouts in parallel (repo, practice, docs, epic, docs-gap) |
| 9. Gap Analysis | Run gap analyst, fold into plan |
| 9.5. Epic Dependencies | Set cross-epic dependencies |
| 10. Task Creation | Size and create tasks (target M, split L) |
| 10.5. Browser QA | Auto-create QA checklist for frontend epics |
| 11. Update Epic Spec | Write full scope + acceptance |
| 12. Validate | Run `$FLUXCTL validate` |

---

# LINEAR TASK CREATION (if Linear mode)

If `LINEAR_MODE` is true, sync tasks back to Linear after local epic/tasks are created.

**Read [linear.md](linear.md) for Steps 13-16** (create issues, set dependencies, store mapping, report sync).

---

# COMPLETION

**Read [completion.md](completion.md) for summary, Ralph mode offer, update check, and philosophy.**

After showing the completion summary:
1. **Ralph mode offer** — always offer to run the epic autonomously overnight
2. **Update check** — check for Flux plugin updates (silent if none)
