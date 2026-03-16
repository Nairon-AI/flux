# Phase 2: Solution Space

Steps 7-12 — research, planning, and task creation after the problem space converges.

---

## Step 7: Create Epic

Create the epic with the problem statement:

```bash
$FLUXCTL epic create --title "<Short title from problem statement>" --json
```

Write the problem space findings to the epic spec:

```bash
$FLUXCTL epic set-plan <epic-id> --file - --json <<'EOF'
# <Epic Title>

## Problem Statement
<Final problem statement from Step 6>

## Context
- **Core Desire**: <from Step 1>
- **Key Assumptions**: <from Step 2>
- **User Impact**: <from Step 3>
- **Blind Spots**: <from Step 4>
- **Risks**: <from Step 5>

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
if [ -f "$REPO_ROOT/brain/principles.md" ]; then
  cat "$REPO_ROOT/brain/principles.md"
fi

# Read known pitfalls — organized by area (brain/pitfalls/<area>/<pattern>.md)
if [ -d "$REPO_ROOT/brain/pitfalls" ]; then
  ls "$REPO_ROOT/brain/pitfalls"
  # Read pitfalls from areas relevant to the problem domain
  for f in "$REPO_ROOT/brain/pitfalls/<relevant-area>"/*.md 2>/dev/null; do
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

Create tasks under the epic:

```bash
# Create tasks with dependencies
$FLUXCTL task create --epic <epic-id> --title "<Task title>" --json
$FLUXCTL task create --epic <epic-id> --title "<Task title>" --deps <dep1> --json

# Set task specs
$FLUXCTL task set-spec <task-id> --description /tmp/desc.md --acceptance /tmp/acc.md --json
```

**Task spec content** (NO implementation code):
```markdown
## Description
[What to build, not how]

**Size:** S/M
**Files:** expected files

## Approach
- Follow pattern at `src/example.ts:42`
- Reuse `helper()` from `lib/utils.ts`

## Acceptance
- [ ] Criterion 1
- [ ] Criterion 2
```

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

Update epic with full scope and acceptance:

```bash
$FLUXCTL epic set-plan <epic-id> --file - --json <<'EOF'
# <Epic Title>

## Problem Statement
<problem statement>

## Context
<from Problem Space>

## Scope
- Task 1: <description>
- Task 2: <description>
...

## Out of Scope
<explicit exclusions>

## Quick Commands
```bash
# Smoke test command(s)
```

## Acceptance
- [ ] Overall criterion 1
- [ ] Overall criterion 2
EOF
```

## Step 12: Validate

```bash
$FLUXCTL validate --epic <epic-id> --json
```

Fix any errors before completing.
