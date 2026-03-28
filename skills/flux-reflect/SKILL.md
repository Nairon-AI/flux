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
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
[ ! -d "$PLUGIN_ROOT/scripts" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
$FLUXCTL session-phase set reflect
```
On completion, reset:
```bash
$FLUXCTL session-phase set idle
```

## External Memory Awareness

Before processing learnings, check if an external memory provider is configured:

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
[ ! -d "$PLUGIN_ROOT/scripts" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
EXTERNAL_MEMORY_PROVIDER=$($FLUXCTL config get externalMemory.provider --json 2>/dev/null | jq -r '.value // empty')
EXTERNAL_MEMORY_TOOL=$($FLUXCTL config get externalMemory.tool --json 2>/dev/null | jq -r '.value // empty')
```

If `EXTERNAL_MEMORY_PROVIDER` is set, two additional behaviors activate:

1. **Dedup on write** — before writing a learning to `.flux/brain/`, query the external memory MCP to check if it already exists externally. If a close match is found, skip the brain write and log: "Already in {provider} — skipping brain write for: {topic}". This prevents the same insight living in both places.

2. **Personal-scope routing** — when a learning is personal/cross-project (not repo-specific), offer to store it in the external provider instead of brain. Use `AskUserQuestion`:

```json
{
  "questions": [{
    "question": "This learning seems personal/cross-project. Store in {EXTERNAL_MEMORY_PROVIDER} instead of brain vault?",
    "header": "Learning: {one-line summary}",
    "multiSelect": false,
    "options": [
      {"label": "Yes — store in {EXTERNAL_MEMORY_PROVIDER}", "description": "Cross-project, personal, not git-tracked"},
      {"label": "No — store in brain vault", "description": "Repo-specific, git-tracked, shared with team"},
      {"label": "Skip", "description": "Don't store this learning anywhere"}
    ]
  }]
}
```

**Heuristic for personal vs repo-scoped:** A learning is personal if it's about the user's preferences, workflow habits, tool choices, or general engineering patterns that aren't specific to this codebase. A learning is repo-scoped if it references specific files, APIs, architecture, team members, or project decisions.

If `EXTERNAL_MEMORY_PROVIDER` is NOT set, skip both behaviors — reflect works exactly as before.

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

### Skill extraction (`.secureskills/` preferred)

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

Invoke the `flux-skill-builder` skill autonomously. Pass it the learning context — what was discovered, why it's reusable, and the verified solution from this session. The skill builder handles research, drafting, validation (`validate_skills.py`), and installation to project-local `.secureskills/` through PlaTo when available, with loose `.codex/skills/<name>/` mirrors only as fallback.

Do NOT manually create skill files. The skill builder encodes all best practices from `docs/skills-best-practices.md` and produces validated, trigger-optimized skills with proper progressive disclosure.

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
- External memory: [learnings routed to {provider}, one-line each] (only if external memory is configured)
- Dedup skipped: [learnings already in {provider}, one-line each] (only if any were deduped)
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
