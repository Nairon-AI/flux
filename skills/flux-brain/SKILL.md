---
name: flux-brain
description: >-
  Read/write brain files in .flux/brain/. Use for any task that persists knowledge —
  reflection, planning, or direct edits. Handles the "Remember" flow: classifies content as
  CLAUDE.md (short rules for every session) or .flux/brain/ (deeper context), asks user to confirm,
  then writes. Triggers: brain/ modifications, "add to brain", "remember X", "don't forget X",
  "keep in mind X", "from now on X", "note that X".
user-invocable: false
---

# Brain

Persistent memory across sessions. Brain files live in `.flux/brain/`.

Adapted from [brainmaxxing](https://github.com/poteto/brainmaxxing) by [@poteto](https://github.com/poteto).

The brain is the foundation of the entire workflow — every agent, skill, and session reads it. Low-quality or speculative content degrades everything downstream. Before adding anything, ask: "Does this genuinely improve how the system operates?" If the answer isn't a clear yes, don't write it.

## "Remember" Flow

When the user says "remember X", "don't forget X", "keep in mind X", or similar — first decide whether it belongs in **CLAUDE.md** or the **brain vault**, then ask the user to confirm.

### Step 0: Check for external memory provider

Before routing, check if an external memory MCP is configured:

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
[ ! -d "$PLUGIN_ROOT/scripts" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
EXTERNAL_MEMORY_PROVIDER=$($FLUXCTL config get externalMemory.provider --json 2>/dev/null | jq -r '.value // empty')
EXTERNAL_MEMORY_TOOL=$($FLUXCTL config get externalMemory.tool --json 2>/dev/null | jq -r '.value // empty')
```

If `EXTERNAL_MEMORY_PROVIDER` is set, a third destination is available (see Step 2 below).

### Step 1: CLAUDE.md vs Brain (vs External Memory)

Use this heuristic to pre-select the right destination:

| Goes in **CLAUDE.md** | Goes in **.flux/brain/** | Goes in **external memory** |
|---|---|---|
| Short, actionable rules the agent needs **every session** | Deeper knowledge, context, or rationale | Personal preferences that span repos |
| Commands and how to run them ("use `pnpm test`", "run `make build`") | Why a decision was made ("we chose Supabase because...") | Cross-project patterns ("I prefer single PRs for refactors") |
| Hard constraints ("never import from `legacy/`", "always use TypeScript") | Business context ("Sarah is the PM", "we have 500 users") | Personal tool preferences ("I use Vim keybindings everywhere") |
| Code style rules ("use camelCase for APIs", "4-space indent") | Pitfalls and lessons learned ("migration script doesn't handle NULLs") | Learning notes not tied to this repo |
| Things that affect every task regardless of domain | Things that are relevant only in certain contexts | Things that are relevant across multiple repos |

**Rule of thumb:** If the agent would need this to avoid a mistake on *any* task in the project, it's CLAUDE.md. If it's context that helps make *better* decisions in specific situations, it's brain. If it's personal knowledge that helps across *all* your projects, it's external memory.

**Note:** The external memory column only applies when `externalMemory.provider` is configured. If not set, route between CLAUDE.md and brain as before.

### Step 2: Ask the user

Use `AskUserQuestion` with the pre-selected option first.

**If `EXTERNAL_MEMORY_PROVIDER` is NOT set** (default — two options):

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

**If `EXTERNAL_MEMORY_PROVIDER` IS set** (three options — add external memory):

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
        "label": "Brain vault — repo-specific context",
        "description": "Decisions, business context, principles, pitfalls for THIS repo. Git-tracked, shared with team."
      },
      {
        "label": "{EXTERNAL_MEMORY_PROVIDER} — cross-project, personal",
        "description": "Personal knowledge that spans repos. Not git-tracked. Use for preferences, patterns, and learnings that apply everywhere."
      }
    ]
  }]
}
```

Replace `{EXTERNAL_MEMORY_PROVIDER}` with the actual provider name (e.g., "Supermemory", "Mem0").

### Step 3a: If CLAUDE.md selected

1. Read the current CLAUDE.md
2. Find the most appropriate section (or create one if needed)
3. Append the rule as a concise bullet point
4. If there's a `<!-- BEGIN FLUX -->` section, add it inside that section under the right heading
5. **Conditional block check**: If the rule is task-specific (only applies when testing, deploying, writing APIs, etc.), check if an appropriate `<important if="...">` block already exists. If so, add the rule inside it. If the CLAUDE.md is long (>50 lines) and no matching block exists, create one. Examples:
   - "always use `createTestApp()` helper" → add inside `<important if="you are writing or modifying tests">`
   - "API routes must validate auth" → add inside `<important if="you are writing API routes or server actions">`
   - "use pnpm, not npm" → add as a regular bullet (applies to every task, don't wrap)

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
        "description": "Project-specific pattern or rule. Stored in .flux/brain/conventions/"
      },
      {
        "label": "Decision",
        "description": "Architectural decision with rationale. Stored in .flux/brain/decisions/"
      },
      {
        "label": "Principle",
        "description": "Engineering principle that applies broadly. Stored in .flux/brain/principles/"
      },
      {
        "label": "Business context",
        "description": "Product, team, or stakeholder context. Stored in .flux/brain/business/"
      },
      {
        "label": "Pitfall",
        "description": "Something that went wrong or could go wrong. Stored in .flux/brain/pitfalls/"
      }
    ]
  }]
}
```

Then:
1. Create the file in the selected directory with a descriptive slug (e.g., `.flux/brain/conventions/always-use-pnpm.md`)
2. Write a concise note — bullets over prose, one topic per file, under ~50 lines
3. For pitfalls, also ask which area it belongs to (e.g., `.flux/brain/pitfalls/frontend/`, `.flux/brain/pitfalls/api/`)
4. Update `.flux/brain/index.md` to include a link to the new file

Notes are prunable — `/flux:meditate` audits and removes stale ones. Store freely.

### Step 3c: If external memory selected

When the user chooses the external memory option, use the provider's MCP tool to store the knowledge. Do NOT write to `.flux/brain/` or CLAUDE.md.

1. Format the learning as a concise note (same style as brain vault — bullets over prose)
2. Call the external memory MCP tool to store it. The tool name is in `EXTERNAL_MEMORY_TOOL`. Example for Supermemory:
   - Use the MCP tool `search_supermemory_memory_api_for` to first check if a similar memory already exists
   - If it exists, inform the user: "This is already stored in {EXTERNAL_MEMORY_PROVIDER} — skipping."
   - If it does not exist, use the appropriate MCP write/add tool to store the new memory
3. Confirm to the user: "Stored in {EXTERNAL_MEMORY_PROVIDER} (not git-tracked)."

**Important:** Never silently write to external memory. The user explicitly chose this destination in Step 2. If the MCP tool call fails (provider down, auth expired), fall back to brain vault and tell the user why.

## Before Writing

Read `.flux/brain/index.md` first. Then read the relevant entrypoint for your topic:

- `.flux/brain/principles.md` for principle updates

For directories without a dedicated index file yet, scan nearby files directly and edit an existing note when possible.

## Structure

```
.flux/brain/
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

- One topic per file. `.flux/brain/codebase/deploy-gotchas.md`, not a mega-file.
- Maintain existing index entrypoints: `.flux/brain/index.md`, `.flux/brain/principles.md`.
- If you introduce a new top-level category, add an index-style entrypoint for it (links only, no inlined content).
- `.flux/brain/index.md` is the root. Every brain file must be reachable from it.
- File names: lowercase, hyphenated. `worktree-gotchas.md`.

## Wikilinks

Format: `[[section/file-name]]`. Resolution order: same directory, then relative path, then vault root. Heading anchors (`[[file#heading]]`) are stripped during resolution.

## Writing Style

- Bullets over prose. No preamble.
- Plain markdown with `# Title`. No Obsidian frontmatter.
- Keep notes under ~50 lines. Split if longer.

## After Writing

Update `.flux/brain/index.md` for any files you added or removed. Also update the relevant entrypoint when applicable. Keep indexes link-only and scannable.

Note: The auto-index hook will also update `.flux/brain/index.md` automatically when brain files change.

## Durability Test

Ask: "Would I include this in a prompt for a *different* task?"

- **Yes** -> write to `.flux/brain/`. It's durable knowledge.
- **No, it's plan-specific** -> update the plan's docs instead.
- **No, it's a skill issue** -> update the skill file directly.
- **No, it needs follow-up work** -> file a task via fluxctl.

## Maintenance

- Delete outdated or subsumed notes.
- Merge overlapping notes before adding new ones.

## Gotchas

- Do not store ephemeral task state, scratch notes, or one-off debugging output in `.flux/brain/`. Brain files must survive reuse across future sessions.
- Keep one topic per file and update the relevant indexes. A correct note that is not reachable from `.flux/brain/index.md` is effectively lost.
- If the learning is really about a skill failing, update the skill instead of creating a brain note that papers over the process bug.
