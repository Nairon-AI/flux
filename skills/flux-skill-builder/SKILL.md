---
name: flux-skill-builder
description: >
  Autonomously create production-grade agent skills from a brief description.
  Use when user says "build a skill", "create a skill for X", "I need a skill that does Y",
  or wants to turn a repeated workflow into a reusable skill. Handles research, drafting,
  validation, and installation without interactive gates. Do NOT use for editing existing
  skills (use direct file editing) or for Flux plugin development (use flux-contribute).
user-invocable: true
---

# Flux Skill Builder

Autonomously create production-grade agent skills from a short description. No interview loops — the agent researches, infers, drafts, validates, and installs in one pass.

**Why this exists**: The default LLM behavior when asked to "make a skill" produces vague descriptions that never trigger, monolithic SKILL.md files with no progressive disclosure, empty gotchas sections, and instructions that state the obvious. This skill encodes the hard-won patterns that make skills actually work.

## Session Phase Tracking

On entry, save the current phase and set the new one:
```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
[ ! -d "$PLUGIN_ROOT/scripts" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
PREV_PHASE=$($FLUXCTL session-phase get 2>/dev/null || echo "idle")
$FLUXCTL session-phase set skill_build
```
On completion, restore the previous phase (not blindly reset to idle — this skill may be invoked from reflect or improve):
```bash
$FLUXCTL session-phase set "$PREV_PHASE"
```

## Input

Full request: $ARGUMENTS

Accepts:
- Natural language description: `"build a skill for database migrations"`
- Path to existing workflow: `"turn scripts/deploy.sh into a skill"`
- Reference to repeated behavior: `"I keep doing X manually, make it a skill"`

If empty, ask: "What repeated workflow or capability should this skill encode? Describe it in 1-3 sentences."

## Workflow

Execute these 4 phases sequentially. No human gates between phases — run to completion, present the finished skill.

Read [pipeline.md](pipeline.md) for the detailed autonomous execution pipeline.

**Phase overview:**

| Phase | What happens | Output |
|-------|-------------|--------|
| 1. Research | Analyze intent, scan codebase, study existing skills | Inferred spec (category, triggers, capabilities, failure modes) |
| 2. Draft | Write SKILL.md + supporting files using progressive disclosure | Complete skill folder |
| 3. Validate | Run `validate_skills.py`, self-review against checklists | Pass/fail with auto-fixes |
| 4. Deliver | Install to project-local `.secureskills/` through PlaTo when available, with loose skill mirrors only as fallback, then generate trigger test report | Installed and ready |

## Key Principles

1. **Infer, don't interview** — Research the codebase, existing skills, and brain vault to answer the questions the interactive version would ask. Only ask the user if genuinely ambiguous (2+ equally valid interpretations).
2. **Description is king** — The frontmatter description determines whether the skill ever fires. Spend disproportionate effort here. It must include WHAT, WHEN (with specific trigger phrases), and negative triggers.
3. **Gotchas are the highest-signal section** — Analyze how Claude fails at this task today. Every known failure mode becomes a gotcha. An empty gotchas section means you didn't research hard enough.
4. **Progressive disclosure** — SKILL.md stays under 350 lines. Heavy content goes to `workflow.md`, `references/`, `examples.md`, or `steps.md`.
5. **Scripts for deterministic work** — If the skill involves a checkable operation, write a script. Code is deterministic. Prose instructions are not.
6. **One job per skill** — If the skill straddles two categories, split it or narrow the scope.

## Gotchas

- **Undertriggering is the #1 failure mode.** Skills that never fire are worthless. The description must be "slightly pushy" — include adjacent phrases the user might say, not just the exact command name.
- **Do not state the obvious.** Claude already knows how to code. The skill should contain information Claude does NOT have — repo-specific constraints, non-obvious failure modes, decision rules that override defaults.
- **Do not over-railroad.** Only use rigid step sequences when deviating genuinely breaks things. For judgment-heavy tasks, give principles and examples, not exact scripts.
- **Validate before delivering.** Always run `python3 scripts/validate_skills.py skills/<name>/` before presenting the skill. Fix errors automatically. Present warnings to the user.
- **Check for existing skills first.** Before creating a new skill, scan `.secureskills/store/`, `~/.codex/skills/`, `~/.claude/skills/`, `.codex/skills/`, and `.claude/skills/` for overlap. Extend rather than duplicate.
- **Validate the install path, not the repo path.** Run `validate_skills.py` against the installed skill directory. Prefer PlaTo's materialized project path when available; otherwise validate the loose fallback install path, not `skills/<name>/` inside the Flux repo.
- **Restore session phase on completion.** This skill may be invoked from reflect or improve. Save the previous phase on entry and restore it on exit — do not blindly reset to `idle`.

---

## Update Check (End of Command)

**ALWAYS run at the very end of execution:**

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
