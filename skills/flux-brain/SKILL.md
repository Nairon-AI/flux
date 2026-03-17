---
name: flux-brain
description: >-
  Read/write brain files (Obsidian vault at brain/). Use for any task that persists knowledge —
  reflection, planning, or direct edits. Triggers: brain/ modifications, "add to brain",
  "remember this", "remember that", "don't forget", "keep in mind".
user-invocable: false
---

# Brain

Persistent memory across sessions. Obsidian vault at `brain/`.

Adapted from [brainmaxxing](https://github.com/poteto/brainmaxxing) by [@poteto](https://github.com/poteto).

The brain is the foundation of the entire workflow — every agent, skill, and session reads it. Low-quality or speculative content degrades everything downstream. Before adding anything, ask: "Does this genuinely improve how the system operates?" If the answer isn't a clear yes, don't write it.

## "Remember" Flow

When the user says "remember X", "don't forget X", "keep in mind X", or similar — first decide whether it belongs in **CLAUDE.md** or the **brain vault**, then ask the user to confirm.

### Step 1: CLAUDE.md vs Brain

Use this heuristic to pre-select the right destination:

| Goes in **CLAUDE.md** | Goes in **brain/** |
|---|---|
| Short, actionable rules the agent needs **every session** | Deeper knowledge, context, or rationale |
| Commands and how to run them ("use `pnpm test`", "run `make build`") | Why a decision was made ("we chose Supabase because...") |
| Hard constraints ("never import from `legacy/`", "always use TypeScript") | Business context ("Sarah is the PM", "we have 500 users") |
| Code style rules ("use camelCase for APIs", "4-space indent") | Pitfalls and lessons learned ("migration script doesn't handle NULLs") |
| Things that affect every task regardless of domain | Things that are relevant only in certain contexts |

**Rule of thumb:** If the agent would need this to avoid a mistake on *any* task in the project, it's CLAUDE.md. If it's context that helps make *better* decisions in specific situations, it's brain.

### Step 2: Ask the user

Use `AskUserQuestion` with the pre-selected option first:

```json
{
  "questions": [{
    "question": "Where should I store this?",
    "header": "Remember",
    "multiSelect": false,
    "options": [
      {
        "label": "CLAUDE.md — agent reads every session",
        "description": "Short, actionable rules and constraints (e.g., 'always use pnpm', 'never import from legacy/'). The agent sees this at the start of every conversation."
      },
      {
        "label": "Brain vault — deeper context",
        "description": "Decisions, business context, principles, pitfalls. Read by specific skills when relevant, not loaded every session."
      }
    ]
  }]
}
```

### Step 3a: If CLAUDE.md selected

1. Read the current CLAUDE.md
2. Find the most appropriate section (or create one if needed)
3. Append the rule as a concise bullet point
4. If there's a `<!-- BEGIN FLUX -->` section, add it inside that section under the right heading

### Step 3b: If brain vault selected

Ask which category:

```json
{
  "questions": [{
    "question": "Which brain category?",
    "header": "Category",
    "multiSelect": false,
    "options": [
      {
        "label": "Convention",
        "description": "Project-specific pattern or rule. Stored in brain/conventions/"
      },
      {
        "label": "Decision",
        "description": "Architectural decision with rationale. Stored in brain/decisions/"
      },
      {
        "label": "Principle",
        "description": "Engineering principle that applies broadly. Stored in brain/principles/"
      },
      {
        "label": "Business context",
        "description": "Product, team, or stakeholder context. Stored in brain/business/"
      },
      {
        "label": "Pitfall",
        "description": "Something that went wrong or could go wrong. Stored in brain/pitfalls/"
      }
    ]
  }]
}
```

Then:
1. Create the file in the selected directory with a descriptive slug (e.g., `brain/conventions/always-use-pnpm.md`)
2. Write a concise note — bullets over prose, one topic per file, under ~50 lines
3. For pitfalls, also ask which area it belongs to (e.g., `brain/pitfalls/frontend/`, `brain/pitfalls/api/`)
4. Update `brain/index.md` to include a link to the new file

Notes are prunable — `/flux:meditate` audits and removes stale ones. Store freely.

## Before Writing

Read `brain/index.md` first. Then read the relevant entrypoint for your topic:

- `brain/principles.md` for principle updates

For directories without a dedicated index file yet, scan nearby files directly and edit an existing note when possible.

## Structure

```
brain/
├── index.md              <- root entry point, links to everything
├── principles.md         <- index for principles/
├── principles/           <- engineering and design principles
├── pitfalls/             <- auto-captured from review iterations, organized by area
│   ├── frontend/         <-   e.g., missing-error-states.md
│   ├── security/         <-   e.g., greptile-auth-gap.md
│   └── async/            <-   e.g., consensus-race-condition.md
├── conventions/          <- project-specific patterns and rules
├── decisions/            <- architectural decisions with rationale
├── business/             <- product stage, team, stakeholders, glossary
│   ├── context.md        <-   product stage, team structure, key context
│   ├── glossary.md       <-   ubiquitous language — domain-specific terms
│   └── team.md           <-   names, roles, responsibilities
├── codebase/             <- project-specific knowledge and gotchas
└── plans/                <- feature plans (linked from .flux/ epics)
```

**Rules:**

- One topic per file. `brain/codebase/deploy-gotchas.md`, not a mega-file.
- Maintain existing index entrypoints: `brain/index.md`, `brain/principles.md`.
- If you introduce a new top-level category, add an index-style entrypoint for it (links only, no inlined content).
- `brain/index.md` is the root. Every brain file must be reachable from it.
- File names: lowercase, hyphenated. `worktree-gotchas.md`.

## Wikilinks

Format: `[[section/file-name]]`. Resolution order: same directory, then relative path, then vault root. Heading anchors (`[[file#heading]]`) are stripped during resolution.

## Writing Style

- Bullets over prose. No preamble.
- Plain markdown with `# Title`. No Obsidian frontmatter.
- Keep notes under ~50 lines. Split if longer.

## After Writing

Update `brain/index.md` for any files you added or removed. Also update the relevant entrypoint when applicable. Keep indexes link-only and scannable.

Note: The auto-index hook will also update `brain/index.md` automatically when brain files change.

## Durability Test

Ask: "Would I include this in a prompt for a *different* task?"

- **Yes** -> write to `brain/`. It's durable knowledge.
- **No, it's plan-specific** -> update the plan's docs instead.
- **No, it's a skill issue** -> update the skill file directly.
- **No, it needs follow-up work** -> file a task via fluxctl.

## Maintenance

- Delete outdated or subsumed notes.
- Merge overlapping notes before adding new ones.
