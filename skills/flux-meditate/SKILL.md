---
name: flux-meditate
description: >-
  Audit and evolve the brain vault — prune outdated content, discover cross-cutting principles,
  review skills for structural encoding opportunities. Triggers: /flux:meditate, "meditate", "audit the brain".
user-invocable: false
---

# Meditate

**Quality bar:** A note earns its place by being **high-signal** (Claude would reliably get this wrong without it), **high-frequency** (comes up in most sessions or most tasks of a type), or **high-impact** (getting it wrong causes significant damage or wasted work). Everything else is noise. A lean, precise brain outperforms a comprehensive but bloated one.

Adapted from [brainmaxxing](https://github.com/poteto/brainmaxxing) by [@poteto](https://github.com/poteto).

## Session Phase Tracking

On entry, set the session phase:
```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
[ ! -d "$PLUGIN_ROOT/scripts" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
$FLUXCTL session-phase set meditate
```
On completion, reset:
```bash
$FLUXCTL session-phase set idle
```

## Process

### 1. Build snapshots

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
[ ! -d "$PLUGIN_ROOT/scripts" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
sh "$PLUGIN_ROOT/skills/flux-meditate/scripts/snapshot.sh" .flux/brain/ /tmp/brain-snapshot.md
sh "$PLUGIN_ROOT/skills/flux-meditate/scripts/snapshot.sh" skills/ /tmp/skills-snapshot.md
```

Files are delimited with `=== path/to/file.md ===` headers. Also locate the auto-memory directory (`~/.claude/projects/<project>/memory/`).

### 2. Auditor (blocking — its report feeds step 3)

Spawn `general` subagent. See `references/agents.md` for the full prompt spec. Inputs: brain snapshot, auto-memory path, CLAUDE.md path.

Audits brain notes, CLAUDE.md, and auto-memory for staleness, redundancy, low-value content, verbosity, and orphans. Returns a categorized report.

**Early-exit gate:** If the auditor finds fewer than 3 actionable items, skip step 3 and go directly to step 4.

### 3. Reviewer (after auditor completes)

Spawn one `general` subagent. See `references/agents.md` for the full prompt spec. Inputs: brain snapshot, skills snapshot, auditor report, `.flux/brain/principles.md`.

Combines three concerns in a single pass:
- **Synthesis**: Proposes missing wikilinks, flags principle tensions, suggests clarifications.
- **Distillation**: Identifies recurring patterns that reveal unstated principles. New principles must be (1) independent, (2) evidenced by 2+ notes, (3) actionable.
- **Skill review**: Cross-references skills against brain principles. Finds contradictions, missed structural enforcement, redundant instructions.

### 4. Review reports

Present the user with a consolidated summary. See `references/agents.md` for the report format.

### 5. Route skill-specific learnings

Check all reports for findings that belong in skill files, not `.flux/brain/`. Update the skill's SKILL.md or references/ directly. Read the skill first to avoid duplication.

### 6. Apply changes

Apply all changes directly. The user reviews the diff.

- **Outdated notes**: Update or delete
- **Redundant notes**: Merge into the stronger note, delete the weaker
- **Low-value notes**: Delete
- **Verbose notes**: Condense in place
- **New connections**: Add `[[wikilinks]]`
- **Tensions**: Reword to clarify boundaries
- **New principles**: Only from the distillation section, only if genuinely independent. Write brain files and update `.flux/brain/principles.md`
- **Merge principles**: Look for principles that are subsets or specific applications of each other — merge the narrower into the broader
- **CLAUDE.md issues**: Rewrite or delete
- **Stale memories**: Delete or rewrite

### 6b. Business context audit

If `.flux/brain/business/` exists, audit it alongside the brain vault:

```bash
ls .flux/brain/business/*.md 2>/dev/null
```

If business context files exist:
- **Stale facts**: Check if any business context describes things that no longer exist in the codebase (e.g., "credits system" after credits were removed). Verify by searching the codebase for key terms. Delete or update stale entries.
- **Glossary drift**: Check if any glossary terms are no longer used in the codebase. Remove obsolete terms.
- **Area files**: Check if area-specific files (e.g., `billing.md`) reference systems or decisions that are outdated. Update or prune.
- **Context.md**: Check if product stage or team structure has changed based on recent proposals or brain notes.

Present business context findings alongside the brain audit report. Apply changes with user approval.

### 7. Housekeep

Update `.flux/brain/index.md` for any files added or removed. Also update `.flux/brain/business/index.md` if business context files were added, removed, or renamed.

Update meditate timestamp so the session health check knows when this last ran:
```bash
mkdir -p "$HOME/.flux"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$HOME/.flux/last_meditate"
```

## Summary

```
## Meditate Summary
- Pruned: [N notes deleted, M condensed, K merged]
- Extracted: [N new principles, with one-line + evidence count each]
- Skill review: [N findings, M applied]
- Housekeep: [state files cleaned]
```

## Gotchas

- Meditate is a reduction pass, not a brainstorming session. Prefer deleting, merging, or tightening existing content before adding anything new.
- Structural fixes beat prose. If a repeated issue can become a script, lint rule, or guardrail, route it there instead of bloating the brain.
- Do not preserve low-signal notes just because they are technically accurate. Signal density matters more than completeness.
