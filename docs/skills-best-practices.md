# Skill Best Practices

Flux skills are prompt programs. Keep them small, sharp, and opinionated only where the workflow is fragile.

This guide distills the current Anthropic guidance on skills into repo rules for `skills/*/`.

## What a good skill does

- Fits one clear job instead of straddling multiple categories.
- Adds information the model would not reliably infer on its own.
- Uses the folder, not just `SKILL.md`: references, scripts, assets, and examples are part of the skill.
- Leaves room for judgment unless the task is brittle enough to require guardrails.

## Description rules

The frontmatter `description` is for the model, not for humans skimming a list.

- Say when the skill should trigger.
- Include distinctive intents, symptoms, or commands.
- Prefer trigger language such as `Use when...`, `Triggers: ...`, `Route here when...`.
- Do not waste description space on generic claims like "helps with development workflow".

Good:

```yaml
description: Investigate failing Flux command flows. Use when setup works inconsistently, a /flux:* command routes incorrectly, or a skill update regresses behavior.
```

Weak:

```yaml
description: A skill for helping with Flux issues.
```

## Body rules

### 1. Do not state the obvious

Assume the agent already knows how to code, read files, run tests, and follow basic engineering hygiene. Spend tokens on repo-specific constraints, failure modes, and decision rules.

### 2. Include a gotchas section

Every mature skill should capture the failure modes the agent repeatedly hits.

Use `## Gotchas` or a comparable section when the skill has meaningful edge cases. Focus on:

- counterintuitive constraints
- common bad assumptions
- order-dependent steps
- misleading errors
- actions that look safe but cause drift

### 3. Use progressive disclosure

Keep `SKILL.md` focused on workflow and routing. Move detail into sibling files when it starts getting bulky.

- Keep `SKILL.md` under roughly 500 lines.
- When a skill exceeds roughly 300 to 350 lines, ask whether detailed examples, question banks, API notes, or command references belong in `references/`, `workflow.md`, `examples.md`, or similar files.
- Link every supporting file directly from `SKILL.md`.

### 4. Match rigidity to fragility

- High freedom: heuristics and principles for context-sensitive work.
- Medium freedom: recommended patterns with scripts or pseudocode.
- Low freedom: exact command sequences when the workflow is easy to corrupt.

Do not railroad the agent into one narrow path unless deviations are genuinely dangerous.

### 5. Prefer scripts for deterministic work

If the skill keeps reconstructing the same shell or Python logic, store it under `scripts/` and invoke it. Use the model for orchestration and judgment, not boilerplate reimplementation.

### 6. Keep data in stable locations

If a skill needs memory, logs, or config:

- store setup values in a config file the agent can read and update
- avoid putting durable runtime data in a location that gets replaced on upgrade
- document what is safe to persist and where

## Review checklist

Before shipping or updating a skill, check:

- Frontmatter has `name` and a trigger-oriented `description`.
- The body adds non-obvious information.
- The workflow points to supporting files instead of inlining everything.
- Gotchas are documented if the skill has repeated failure patterns.
- Deterministic repeated logic is moved into scripts.
- The skill does not duplicate a mechanism that already enforces the rule structurally.

## Repo conventions

- Folder name should match the frontmatter `name` for built-in Flux skills.
- Use kebab-case names.
- Keep references one hop away from `SKILL.md`; avoid deep chains of linked docs.
- If you add a new built-in skill or materially rewrite one, run `python3 scripts/validate_skills.py`.
