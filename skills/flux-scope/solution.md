# Phase 2: Solution Space

Steps 7-12 — research, planning, and task creation after the problem space converges.

---

## Step 6.5: Epic Structure Interview

Before creating any epics or tasks, interview the user about how they want to organize the work. Use `AskUserQuestion` for each question.

### Step 6.5.1: Single vs Multiple Epics

Based on the problem space findings, assess whether the work could logically be split into multiple independent epics (e.g., backend API + frontend UI + migration are three separate workstreams).

If the work has clearly separable workstreams, ask:

```json
{
  "questions": [{
    "question": "This work has separable workstreams. Do you want a single epic or multiple epics?",
    "header": "Epic Split",
    "multiSelect": false,
    "options": [
      {
        "label": "Single epic — keep everything together",
        "description": "All tasks in one epic. Simpler to track, but larger."
      },
      {
        "label": "Multiple epics — split by workstream",
        "description": "E.g., 'Backend: [feature]' + 'Frontend: [feature]' + 'Migration: [feature]'. Each can be worked and reviewed independently."
      }
    ]
  }]
}
```

If the user chooses **multiple epics**, ask them to confirm the proposed split (list the epics you'd create with rough task counts). Adjust based on their feedback.

If the work is clearly a single epic (small scope, tightly coupled tasks), skip this question.

### Step 6.5.2: Linear Project Selection (if Linear connected)

If Linear MCP is available and connected (checked in Step 0.1), ask which project to add the epic(s) to:

```bash
# Fetch all projects from the user's Linear teams
# Call: mcp_linear_list_projects for each team
```

Use `AskUserQuestion`:

```json
{
  "questions": [{
    "question": "Which Linear project should this epic go into?",
    "header": "Project",
    "multiSelect": false,
    "options": [
      {
        "label": "[Project Name 1]",
        "description": "[N] existing issues, [status], [priority]"
      },
      {
        "label": "[Project Name 2]",
        "description": "[N] existing issues, [status], [priority]"
      },
      {
        "label": "Create a new project",
        "description": "I'll create a new Linear project for this work"
      }
    ]
  }]
}
```

If **"Create a new project"** is selected, the epic title will become the Linear project name.

Store the selection for use in Step 13 (Linear task creation).

If Linear is NOT connected, skip this question — tasks are created locally in `.flux/` only.

### Step 6.5.3: Assignee Selection (if Linear connected)

If Linear is connected, fetch the team members and ask who to assign the work to:

```bash
# Fetch team members
# Call: mcp_linear_list_teams(limit: 50) — use the selected team from Step 6.5.2
# Team members are included in the team response
```

Use `AskUserQuestion`:

```json
{
  "questions": [{
    "question": "Who should be assigned to this work?",
    "header": "Assignee",
    "multiSelect": false,
    "options": [
      {
        "label": "[Member Name 1]",
        "description": "[role/title if available]"
      },
      {
        "label": "[Member Name 2]",
        "description": "[role/title if available]"
      },
      {
        "label": "Unassigned",
        "description": "Don't assign to anyone yet — assign later in Linear"
      }
    ]
  }]
}
```

Store the selected assignee ID. When creating Linear issues in Step 13, pass `assignee: SELECTED_USER_ID` for both the epic and all sub-tasks.

If the user selects **"Unassigned"**, omit the assignee field when creating issues.

---

## Step 7: Create Epic

Create the epic with the problem statement:

```bash
$FLUXCTL epic create --title "<Short title from problem statement>" --json
```

Write the problem space findings to the epic spec. **The epic spec is the high-level business context** — an agent or human reading this should understand *why* this work exists, *who* it impacts, and *what success looks like*. Implementation details belong in task specs, not here.

```bash
$FLUXCTL epic set-plan <epic-id> --file - --json <<'EOF'
# <Epic Title>

## Problem Statement
<Final problem statement from Step 6 — one clear sentence>

## Why This Matters
<Business impact in plain language. Who is affected and how.
Explain the reasoning from first principles — not just "the user asked for it"
but why it matters for the product, users, or business.
E.g., "Users are abandoning onboarding at the OAuth step because we only
support email/password. Adding Google OAuth removes the highest-friction
step in signup — our analytics show 40% drop-off at registration.">

## Context
- **Core Desire**: <from Step 1 — what the user/stakeholder actually wants>
- **Key Assumptions**: <from Step 2 — what we're betting on being true>
- **User Impact**: <from Step 3 — who this affects and how>
- **Blind Spots**: <from Step 4 — what we identified as potentially missing>
- **Risks**: <from Step 5 — what could go wrong and mitigation strategies>
- **Decision Authority**: <who approved this, who to escalate to if scope changes>

## Stress-Tested Assumptions
<from Step 6.1 — include decisions, rationale, reversal signals>

### Assumptions Deferred to Implementation
<assumptions that couldn't be resolved during scoping — validate during these tasks>

## Scope
<To be filled after research>

## Acceptance
<To be filled after research>
EOF
```

## Step 7.5: Stakeholder Check

Before research, identify who's affected:
- **End users** — What changes for them? New UI, changed behavior?
- **Developers** — New APIs, changed interfaces, migration needed?
- **Operations** — New config, monitoring, deployment changes?

This shapes what the research and plan need to cover.

## Step 8: Research (Diverge)

**Check configuration:**
```bash
$FLUXCTL config get scouts.github --json
```

**Set epic branch:**
```bash
$FLUXCTL epic set-branch <epic-id> --branch "<epic-id>" --json
```

**Read brain vault** (before scouts, fast local read):

```bash
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Read engineering principles to ground scoping decisions
if [ -f "$REPO_ROOT/.flux/brain/principles.md" ]; then
  cat "$REPO_ROOT/.flux/brain/principles.md"
fi

# Read known pitfalls — organized by area (.flux/brain/pitfalls/<area>/<pattern>.md)
if [ -d "$REPO_ROOT/.flux/brain/pitfalls" ]; then
  ls "$REPO_ROOT/.flux/brain/pitfalls"
  # Read pitfalls from areas relevant to the problem domain
  for f in "$REPO_ROOT/.flux/brain/pitfalls/<relevant-area>"/*.md 2>/dev/null; do
    cat "$f"
  done
fi
```

Use brain principles to guide research direction and plan structure. Read relevant individual principle files in full if the problem domain maps to specific principles (e.g., `experience-first.md` for UX work, `boundary-discipline.md` for API design).

**Run scouts in parallel** (same as flux-plan):

| Scout | Purpose | Required |
|-------|---------|----------|
| `flux:repo-scout` | Grep/Glob/Read patterns | YES |
| `flux:practice-scout` | Best practices + pitfalls | YES |
| `flux:docs-scout` | External documentation | YES |
| `flux:github-scout` | Cross-repo patterns | IF scouts.github |
| `flux:epic-scout` | Dependencies on open epics | YES |
| `flux:docs-gap-scout` | Docs needing updates | YES |

**Alternative: If RepoPrompt available**, use `flux:context-scout` instead of `flux:repo-scout` for deeper AI-powered file discovery.

**CRITICAL**: Run ALL scouts in parallel. Each provides unique signal.

Must capture:
- File paths + line refs
- Existing code to reuse
- Similar patterns / prior work
- External docs links
- Project conventions

## Step 9: Gap Analysis (Diverge)

Run the gap analyst:
- Task flux:flow-gap-analyst(<problem statement>, research_findings)

Fold gaps + questions into the plan.

## Step 9.5: Epic Dependencies

If epic-scout found dependencies on other epics, set them:

```bash
# For each dependency found:
$FLUXCTL epic add-dep <this-epic-id> <dependency-epic-id> --json
```

Report at end of planning:
```
Epic dependencies set:
- fn-N-slug → fn-2-auth (Auth): Uses authService from fn-2.1
```

## Step 10: Task Creation (Converge)

**Task sizing rule** (from flux-plan):

| Size | Files | Acceptance Criteria | Action |
|------|-------|---------------------|--------|
| **S** | 1-2 | 1-3 | Combine with related work |
| **M** | 3-5 | 3-5 | Target size |
| **L** | 5+ | 5+ | Split into M tasks |

### Dependency Ordering

**Tasks MUST be created in dependency order.** The first task created has no deps. Subsequent tasks reference earlier tasks by ID. This is critical — `fluxctl ready` uses this graph to determine which tasks can run next (only tasks whose deps are all `done`).

Think about it like a build system:
1. What can be built with zero dependencies? (foundation tasks — schema, config, types)
2. What depends on #1? (implementation tasks that use the foundation)
3. What depends on #2? (integration, wiring, API endpoints)
4. What depends on everything? (tests, QA, docs — always last)

Tasks at the same dependency level CAN run in parallel. Call this out explicitly in the completion summary (e.g., "Tasks 3/4/5 can run in parallel after task 2").

```bash
# Create tasks in dependency order — first task has no deps
$FLUXCTL task create --epic <epic-id> --title "<Foundation task>" --json
# → returns fn-1-slug.1

$FLUXCTL task create --epic <epic-id> --title "<Task that needs foundation>" --deps fn-1-slug.1 --json
# → returns fn-1-slug.2

# Multiple deps for tasks that need several predecessors
$FLUXCTL task create --epic <epic-id> --title "<Integration task>" --deps fn-1-slug.2,fn-1-slug.3 --json
```

### Task Spec Content

Each task spec must contain **everything an agent needs to implement it without asking questions**. The agent implementing this task will NOT have access to the scoping conversation — only the task spec and the epic spec. Write accordingly.

```bash
$FLUXCTL task set-spec <task-id> --description /tmp/desc.md --acceptance /tmp/acc.md --json
```

**Task spec template** (NO implementation code, but comprehensive context):
```markdown
## Description
[What to build — specific enough that an agent can start immediately]

**Size:** S/M
**Estimated files:** [list the files that will be created or modified]

## Context
[Why this task exists. What problem it solves. How it fits into the epic.
Reference the epic problem statement if needed. An agent reading this
should understand the motivation, not just the mechanics.]

## Current State
[What exists today that this task builds on or changes.
Include specific file paths, function names, line numbers from research.
E.g., "Authentication currently uses `src/auth/session.ts` with cookie-based
sessions. This task adds OAuth2 support alongside the existing flow."]

## Approach
[Concrete guidance — not pseudocode, but clear direction:]
- Follow the pattern at `src/example.ts:42-65`
- Reuse `helper()` from `lib/utils.ts`
- The new endpoint should follow the same middleware chain as `src/routes/api/users.ts`
- Use the existing `DatabaseClient` from `src/db/client.ts` — do NOT create a new connection

## Constraints
[Hard rules the agent must follow:]
- Do NOT modify `src/legacy/auth.ts` — it's deprecated but still used by mobile clients
- All new API endpoints must use the `withAuth` middleware
- Database migrations must be backwards-compatible (no column drops)

## Dependencies
[What must be done before this task, and what this task produces for later tasks:]
- **Depends on:** fn-1-slug.1 (schema must exist before this task can create queries)
- **Produces:** the `UserService` class that fn-1-slug.3 will import

## Acceptance
- [ ] [Specific, testable criterion — not vague]
- [ ] [Include the expected behavior, not just "it works"]
- [ ] [E.g., "POST /api/auth/google returns 200 with { token, user } on valid OAuth code"]
- [ ] [E.g., "Invalid OAuth code returns 401 with { error: 'invalid_grant' }"]
- [ ] [E.g., "Existing cookie-based auth still works (regression test)"]
```

**Rules for writing task specs:**
1. **Self-contained** — the agent should never need to read the scoping conversation
2. **File paths are mandatory** — every task must reference concrete files from the research phase
3. **Constraints prevent regressions** — explicitly state what NOT to touch
4. **Acceptance criteria are testable** — "it works" is not a criterion. Specify inputs, outputs, and edge cases
5. **Dependencies are explicit** — state what this task consumes and produces

## Step 10.5: Browser QA Checklist (if frontend/web)

**Auto-create a Browser QA Checklist task when the epic involves frontend/web changes.**

Detect if the epic touches frontend/web UI by checking:
- Do any tasks reference UI components, pages, routes, views, forms, modals, dashboards?
- Do file paths include patterns like `src/components/`, `pages/`, `app/`, `views/`, `*.tsx`, `*.vue`, `*.svelte`?
- Does the problem statement or scope mention user-facing UI?

**If YES** — create a Browser QA Checklist task:

```bash
$FLUXCTL task create --epic <epic-id> --title "Browser QA Checklist" --json
```

Set its spec with testable acceptance criteria derived from the epic's acceptance criteria and task specs. Each criterion must be concrete and browser-testable:

```bash
cat > /tmp/qa-desc.md << 'EOF'
## Description
Browser QA checklist for epic review. Each criterion is tested automatically by
agent-browser during `/flux:epic-review`. Not an implementation task — this is
a test checklist.

**Size:** S
EOF

cat > /tmp/qa-acc.md << 'EOF'
- [ ] Navigate to <URL> — verify <expected element/text> renders
- [ ] Click "<button/link>" — verify <expected result>
- [ ] Submit <form> with valid data — verify <success state>
- [ ] Navigate to <URL> — verify <visual state> after changes
- [ ] Check responsive layout at mobile width (375px)
EOF

$FLUXCTL task set-spec <qa-task-id> --description /tmp/qa-desc.md --acceptance /tmp/qa-acc.md --json
```

**Criteria guidelines:**
- Each criterion = one URL + one action + one expected result
- Use actual URLs/paths from the epic scope
- Include at least one responsive/mobile check if applicable
- Keep criteria to 5-10 items max — focused on acceptance-critical flows

**If NO** (pure backend, CLI, library, or infrastructure epic) — skip this step.

## Step 11: Update Epic Spec

Update the epic spec with the full picture. The epic spec is the **high-level business context** — why this work exists, who it impacts, and what success looks like. Individual task specs handle the technical details. An agent reading the epic should understand the *motivation and impact*, not the implementation.

```bash
$FLUXCTL epic set-plan <epic-id> --file - --json <<'EOF'
# <Epic Title>

## Problem Statement
<Final problem statement from Step 6 — one clear sentence>

## Why This Matters
<Business impact in plain language. Who is affected and how.
E.g., "Users are abandoning onboarding at the OAuth step because we only
support email/password. Adding Google OAuth removes the highest-friction
step in signup — our analytics show 40% drop-off at registration.">

## Context
- **Core Desire**: <from Step 1 — what the user/stakeholder actually wants>
- **Key Assumptions**: <from Step 2 — what we're betting on being true>
- **User Impact**: <from Step 3 — who this affects and how>
- **Risks**: <from Step 5 — what could go wrong>
- **Decision Authority**: <who approved this, who to escalate to>

## Stress-Tested Assumptions
<from Step 6.1 — include decisions made, rationale, and reversal signals>

### Assumptions Deferred to Implementation
<assumptions that couldn't be resolved during scoping — validate during these tasks>

## Scope
<List all tasks with their dependencies and sizes. This is the execution plan.>

| # | Task | Size | Depends On | Parallel? |
|---|------|------|------------|-----------|
| 1 | <task title> | M | — | — |
| 2 | <task title> | M | 1 | — |
| 3 | <task title> | S | 1 | Yes (with 2) |
| 4 | <task title> | M | 2, 3 | — |

## Out of Scope
<Explicit exclusions — things the agent should NOT build even if they seem related>

## Quick Commands
```bash
# Smoke test command(s) to verify the epic works end-to-end
```

## Acceptance (Epic-Level)
<High-level acceptance — what does "done" look like for the whole epic?>
- [ ] <User-visible outcome, not implementation detail>
- [ ] <E.g., "Users can sign in with Google OAuth on web and mobile">
- [ ] <E.g., "Existing email/password auth still works (regression)">
- [ ] <E.g., "Auth tokens are validated server-side with <provider>">
EOF
```

## Step 12: Validate

```bash
$FLUXCTL validate --epic <epic-id> --json
```

Fix any errors before completing.
