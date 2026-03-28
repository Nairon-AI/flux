---
name: flux-improve-claude-md
description: >-
  Restructure CLAUDE.md for better agent adherence by adding <important if> conditional blocks.
  Separates foundational content (always relevant) from task-specific instructions (wrapped in
  conditional tags). Preserves <!-- BEGIN FLUX --> markers. Triggers: /flux:improve-claude-md.
user-invocable: true
---

# Improve CLAUDE.md

Restructure a CLAUDE.md file so Claude actually follows the instructions. Applies the `<important if="condition">` pattern to task-specific sections while keeping foundational content unwrapped.

**Why**: Legacy Claude environments wrap `CLAUDE.md` in a `<system_reminder>` that says contents "may or may not be relevant." Long flat files cause the model to treat individual sections as optional. Conditional blocks give a clearer signal about when to apply specific instructions.

## Input

Full request: $ARGUMENTS

Accepts:
- No arguments (restructures CLAUDE.md in current directory)
- Path to a specific CLAUDE.md file

## Session Phase Tracking

On entry, set the session phase:
```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
[ ! -d "$PLUGIN_ROOT/scripts" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
$FLUXCTL session-phase set improve-claude-md
```

On completion, reset to idle:
```bash
$FLUXCTL session-phase set idle
```

## Workflow

### Step 1: Read and analyze

1. Find CLAUDE.md (check `CLAUDE.md`, then `.claude/CLAUDE.md`)
2. If not found, tell the user and exit
3. Read the file and count lines
4. If under 50 lines, tell the user it's already concise enough and conditional blocks aren't needed. Exit.

### Step 2: Classify sections

Scan the file and classify each section into one of two buckets:

**Foundational (never wrap):**
- Project identity, description, purpose
- Tech stack and directory structure
- Package manager rules ("use pnpm")
- Core constraints that apply to every task ("never import from legacy/")
- Build, test, and dev commands
- `<!-- BEGIN FLUX -->` ... `<!-- END FLUX -->` block (preserve as-is — this is already managed by flux-setup)

**Task-specific (candidates for wrapping):**
- Testing setup, test helpers, fixtures → `<important if="you are writing or modifying tests">`
- API patterns, endpoint conventions, auth validation → `<important if="you are writing API routes, endpoints, or server actions">`
- Database/migration rules, ORM conventions → `<important if="you are modifying database schemas, queries, or migrations">`
- Deployment procedures, CI/CD config → `<important if="you are deploying, configuring CI/CD, or managing infrastructure">`
- Security rules, auth patterns, secrets handling → `<important if="you are handling authentication, authorization, or secrets">`
- Styling conventions, CSS patterns, design system → `<important if="you are writing CSS, styling components, or working on UI">`
- Performance rules, caching strategies → `<important if="you are optimizing performance or configuring caching">`
- Documentation rules, comment conventions → `<important if="you are writing or updating documentation">`

### Step 3: Generate rewrite

Produce a rewritten version that:

1. Keeps foundational content at the top, unwrapped
2. Groups task-specific rules under `<important if="condition">` blocks
3. Uses specific, narrow conditions (not "you are writing code")
4. Preserves `<!-- BEGIN FLUX -->` / `<!-- END FLUX -->` markers exactly
5. Does NOT wrap content inside the FLUX markers (that's managed by flux-setup separately)
6. Preserves all existing content — just restructures it
7. Merges related rules into the same conditional block rather than creating one block per rule
8. Aims for 3-8 conditional blocks (fewer if the file is shorter)

### Step 4: Preview and confirm

Show the user a diff-style preview of the changes:
- What stays unwrapped (foundational)
- What gets wrapped and under which condition
- Any sections that were merged

Use `AskUserQuestion` to confirm:

```json
{
  "questions": [{
    "question": "Here's the restructured CLAUDE.md. The task-specific sections are now wrapped in <important if> blocks so Claude applies them more reliably. Apply these changes?",
    "header": "Apply",
    "multiSelect": false,
    "options": [
      {
        "label": "Yes — apply the restructured version",
        "description": "Replaces CLAUDE.md with the version using conditional blocks. All content is preserved, just restructured."
      },
      {
        "label": "No — keep the current version",
        "description": "No changes made."
      }
    ]
  }]
}
```

### Step 5: Apply

If approved:
1. Write the restructured CLAUDE.md
2. Show a summary: N foundational sections, M conditional blocks created
3. List the conditions used

If declined:
1. Exit without changes

## Rules

- Never delete content — only restructure
- Never wrap the `<!-- BEGIN FLUX -->` block contents (managed by flux-setup)
- Never wrap foundational content that applies to every task
- Keep conditions specific and narrow
- Merge related rules into one block (don't create `<important if="tests">` and `<important if="test fixtures">` separately)
- If existing `<important if>` blocks are already present, preserve and potentially expand them
- Linter rules, style guide references, and other things that belong in a linter config should be flagged but not removed (the user decides)

## Examples

### Before

```markdown
# MyProject

Use pnpm. Node 20+.

## Testing
- Use `createTestApp()` for integration tests
- Mock database with `dbMock` from `packages/db/test`
- Test fixtures live in `__fixtures__/` directories

## API Conventions
- All endpoints return `{ data, error }` shape
- Validate auth tokens in middleware
- Use zod for request validation

## Deployment
- Run `pnpm build` before deploying
- Set DATABASE_URL in production
- Never deploy on Fridays
```

### After

```markdown
# MyProject

Use pnpm. Node 20+.

<important if="you are writing or modifying tests">
## Testing
- Use `createTestApp()` for integration tests
- Mock database with `dbMock` from `packages/db/test`
- Test fixtures live in `__fixtures__/` directories
</important>

<important if="you are writing API routes or server actions">
## API Conventions
- All endpoints return `{ data, error }` shape
- Validate auth tokens in middleware
- Use zod for request validation
</important>

<important if="you are deploying or configuring CI/CD">
## Deployment
- Run `pnpm build` before deploying
- Set DATABASE_URL in production
- Never deploy on Fridays
</important>
```
