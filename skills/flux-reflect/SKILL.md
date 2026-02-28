---
name: flux-reflect
description: >-
  Reflect on the conversation and update the brain vault. Use when wrapping up, after mistakes
  or corrections, or when significant codebase knowledge was gained. Triggers: /flux:reflect,
  "reflect", "remember this".
user-invocable: false
---

# Reflect

Review the conversation and persist learnings — to `brain/`, to skill files, or as structural enforcement.

Adapted from [brainmaxxing](https://github.com/poteto/brainmaxxing) by [@poteto](https://github.com/poteto).

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
3. **Skip** anything trivial or already captured in existing brain files
4. **Route each learning** to the right destination (see Routing below)
5. **Update `brain/index.md`** if any brain files were added or removed

## Routing

Not everything belongs in the brain. Route each learning to where it will have the most impact.

### Structural enforcement check

Before routing a learning to `brain/`, ask: can this be a lint rule, script, metadata flag, or runtime check? If yes, encode it structurally and skip the brain note. See `brain/principles/encode-lessons-in-structure.md`.

### Brain files (`brain/`)

Codebase knowledge, principles, gotchas — anything that informs future sessions. This is the default destination. Use the `flux-brain` skill for writing conventions.

- One topic per file. File name = topic slug.
- Group in directories with index files using `[[wikilinks]]`.
- No inlined content in index files.

### Skill improvements (`skills/<skill>/`)

If a learning is about how a specific skill works — its process, prompts, or edge cases — update the skill directly.

### Backlog items

Follow-up work that can't be done during reflection — bugs, non-trivial rewrites, tooling gaps. File as a task via `fluxctl`.

## Summary

```
## Reflect Summary
- Brain: [files created/updated, one-line each]
- Skills: [skill files modified, one-line each]
- Structural: [rules/scripts/checks added]
- Todos: [follow-up items filed]
```
