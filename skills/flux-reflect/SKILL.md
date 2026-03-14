---
name: flux-reflect
description: >-
  Reflect on the conversation and persist learnings — brain vault notes, skill extraction,
  or structural enforcement. Use when wrapping up, after mistakes or corrections, after
  non-obvious debugging, or when significant codebase knowledge was gained.
  Triggers: /flux:reflect, "reflect", "remember this", "save this as a skill".
user-invocable: false
---

# Reflect

Review the conversation and persist learnings — to `brain/`, as new skills, to existing skill files, or as structural enforcement.

Adapted from [brainmaxxing](https://github.com/poteto/brainmaxxing) by [@poteto](https://github.com/poteto), with skill extraction adapted from [Claudeception](https://github.com/blader/Claudeception).

## Process

1. **Read `brain/index.md`** to understand what notes already exist
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
5. **Update `brain/index.md`** if any brain files were added or removed

## Routing

Not everything belongs in the brain. Route each learning to where it will have the most impact.

### Decision flow

For each learning, ask in order:

1. **Can this be a lint rule, script, metadata flag, or runtime check?** → Encode it structurally. See `brain/principles/encode-lessons-in-structure.md`.
2. **Is this a reusable, non-obvious solution with clear trigger conditions?** → Extract as a new skill (see Skill Extraction below).
3. **Is this about how an existing skill works?** → Update that skill directly.
4. **Is this codebase knowledge, a principle, or a gotcha?** → Write to `brain/`.
5. **Is this follow-up work?** → File as a backlog item via `fluxctl`.

### Brain files (`brain/`)

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

2. **Create the skill file** at `.claude/skills/[skill-name]/SKILL.md`:

```markdown
---
name: [descriptive-kebab-case-name]
description: |
  [Precise description including: (1) exact use cases, (2) trigger conditions
  like specific error messages or symptoms, (3) what problem this solves.
  Be specific enough that semantic matching surfaces this skill when relevant.]
version: 1.0.0
date: [YYYY-MM-DD]
---

# [Skill Name]

## Problem
[What this skill addresses]

## Trigger Conditions
[When to use — exact error messages, symptoms, scenarios]

## Solution
[Step-by-step solution]

## Verification
[How to confirm it worked]

## Notes
[Caveats, edge cases, related considerations]
```

3. **Description quality matters** — the description field drives Claude's semantic matching. Include specific error messages, framework names, and action phrases ("Use when...", "Fixes...").

**Don't extract when:**
- The solution is a standard documentation lookup
- It's project-specific knowledge (use brain vault instead)
- It duplicates existing documentation
- The solution hasn't been verified

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
