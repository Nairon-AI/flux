---
name: flux-reflect
description: >-
  Reflect on the conversation and persist learnings — brain vault notes, skill extraction,
  or structural enforcement. Use when wrapping up, after mistakes or corrections, after
  non-obvious debugging, or when significant codebase knowledge was gained.
  Triggers: /flux:reflect, "reflect", "save this as a skill".
  Note: "remember X" routes to flux-brain, not here. This skill is for session-wide reflection.
user-invocable: false
---

# Reflect

Review the conversation and persist learnings — to `.flux/brain/`, as new skills, to existing skill files, or as structural enforcement.

Adapted from [brainmaxxing](https://github.com/poteto/brainmaxxing) by [@poteto](https://github.com/poteto), with skill extraction adapted from [Claudeception](https://github.com/blader/Claudeception).

## Session Phase Tracking

On entry, set the session phase:
```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}"
[ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
$FLUXCTL session-phase set reflect
```
On completion, reset:
```bash
$FLUXCTL session-phase set idle
```

## Process

1. **Read `.flux/brain/index.md`** to understand what notes already exist
2. **Scan the conversation** for:
   - Mistakes made and corrections received
   - User preferences and workflow patterns
   - Codebase knowledge gained (architecture, gotchas, patterns)
   - Tool/library quirks discovered
   - Decisions made and their rationale
   - Friction in skill execution, orchestration, or delegation
   - Repeated manual steps that could be automated or encoded
   - Non-obvious debugging solutions (>10 min investigation, not in docs)
   - Error resolutions where the error message was misleading
   - Workarounds discovered through trial-and-error
3. **Skip** anything trivial or already captured in existing brain files or skills
4. **Route each learning** to the right destination (see Routing below)
5. **Update `.flux/brain/index.md`** if any brain files were added or removed

## Routing

Not everything belongs in the brain. Route each learning to where it will have the most impact.

### Decision flow

For each learning, ask in order:

1. **Can this be a lint rule, script, metadata flag, or runtime check?** → Encode it structurally. See `.flux/brain/principles/encode-lessons-in-structure.md`.
2. **Is this a reusable, non-obvious solution with clear trigger conditions?** → Extract as a new skill (see Skill Extraction below).
3. **Is this about how an existing skill works?** → Update that skill directly.
4. **Is this codebase knowledge, a principle, or a gotcha?** → Write to `.flux/brain/`.
5. **Is this follow-up work?** → File as a backlog item via `fluxctl`.

### Brain files (`.flux/brain/`)

Codebase knowledge, principles, gotchas — anything that informs future sessions. This is the default destination. Use the `flux-brain` skill for writing conventions.

- One topic per file. File name = topic slug.
- Group in directories with index files using `[[wikilinks]]`.
- No inlined content in index files.

### Skill extraction (`.claude/skills/`)

When a learning meets ALL of these criteria, extract it as a standalone skill:

**Criteria:**
- **Reusable** — will help with future tasks, not just this instance
- **Non-trivial** — requires discovery, not just documentation lookup
- **Specific** — has clear trigger conditions (error messages, symptoms, scenarios)
- **Verified** — the solution actually worked in this session

**When to extract:**
- Non-obvious debugging that took significant investigation
- Error resolution where the root cause wasn't what the error message suggested
- Workaround for a tool/framework limitation found through experimentation
- Tool integration knowledge that documentation doesn't cover well

**Process:**

1. **Check for existing skills** — search `.claude/skills/` and `~/.claude/skills/` for related skills before creating a new one. Update existing skills if the trigger overlaps.

2. **Read [docs/skills-best-practices.md](../../docs/skills-best-practices.md)** before writing or revising a skill. Follow it when deciding what belongs in `SKILL.md` versus supporting files.

3. **Create the skill folder** at `.claude/skills/[skill-name]/`. Start with `SKILL.md`, then add `references/`, `scripts/`, or `assets/` only when they reduce repetition or keep the main file lean.

4. **Create the skill file** at `.claude/skills/[skill-name]/SKILL.md` with this minimum structure:

```markdown
---
name: [descriptive-kebab-case-name]
description: Use when [specific trigger, symptom, command, or scenario]. Handles [distinctive problem].
---

# [Skill Name]

## When To Use
[Exact symptoms, errors, or requests that should trigger this skill]

## Workflow
[Only the non-obvious steps, decision rules, and repo-specific constraints]

## Gotchas
[Repeated failure modes, misleading errors, ordering constraints, footguns]

## Verification
[How to confirm it worked]
```

5. **Keep `SKILL.md` lean** — do not inline long API docs, giant example sets, or boilerplate the model can infer. Move them to sibling files and link them directly from `SKILL.md`.

6. **Prefer scripts for deterministic work** — if the skill keeps rebuilding the same shell, JSON shaping, or parsing logic, store that under `scripts/` instead of describing it repeatedly in prose.

7. **Description quality matters** — the description field drives skill matching. Include the trigger, not a human-oriented summary. Specific error messages, commands, and scenario phrases are high-signal.

**Don't extract when:**
- The solution is a standard documentation lookup
- It's project-specific knowledge (use brain vault instead)
- It duplicates existing documentation
- The solution hasn't been verified

## Gotchas

- Do not create a new skill when updating an existing one would cover the same trigger.
- Do not dump project-specific knowledge into a reusable skill. Route that to `.flux/brain/`.
- Do not restate generic engineering advice the model already knows. Capture non-obvious triggers, constraints, and failure modes.
- If the lesson can become a script, lint rule, config flag, or runtime guard, prefer that over more prose.

### Skill improvements (`skills/<skill>/`)

If a learning is about how a specific Flux skill works — its process, prompts, or edge cases — update the skill directly.

### Backlog items

Follow-up work that can't be done during reflection — bugs, non-trivial rewrites, tooling gaps. File as a task via `fluxctl`.

## Summary

```
## Reflect Summary
- Brain: [files created/updated, one-line each]
- Skills extracted: [new skill files created, one-line each]
- Skills updated: [existing skill files modified, one-line each]
- Structural: [rules/scripts/checks added]
- Todos: [follow-up items filed]
```

## Auto-Meditate (conditional)

After reflection is complete, check if the brain vault needs maintenance:

```bash
PITFALL_COUNT=$(find .flux/brain/pitfalls -name "*.md" 2>/dev/null | wc -l | xargs)
```

If `PITFALL_COUNT >= 20`, automatically run `/flux:meditate` to prune stale content and promote recurring patterns to principles. Do not ask — just run it. If meditate fails, report the error but do not fail the overall reflect. Tell the user:

```
Brain vault has {PITFALL_COUNT} pitfalls — running meditate to prune and promote...
```
