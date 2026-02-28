---
name: flux-scope
description: Combined requirements gathering and planning using Double Diamond process. Guides through Problem Space (discover/define) then Solution Space (research/plan). Default is quick mode (~10 min). Use --deep for thorough scoping (~45 min).
user-invocable: false
---

# Flow scope

Turn a rough idea into a well-defined epic with tasks using the Double Diamond process.

**Double Diamond Flow:**
```
PROBLEM SPACE                    SOLUTION SPACE
┌────────────────────┐          ┌────────────────────┐
│ DISCOVER   DEFINE  │          │ RESEARCH   PLAN    │
│ (diverge) (converge)│    →    │ (diverge) (converge)│
│     ◇        ▽     │          │     ◇        ▽     │
└────────────────────┘          └────────────────────┘
     ~5-20 min                       ~5-25 min
```

**Modes**:
- **Quick (default)**: ~10 min total. MVP-focused problem exploration + short plan.
- **Deep (`--deep`)**: ~45 min total. Thorough discovery + standard/deep plan.
- **Explore (`--explore [N]`)**: Generate N competing approaches, scaffold each in parallel, compare visually, pick winner.

> "Understand the problem before solving it. Most failed features solve the wrong problem."
> "Write ten specs. Test them all. Throw away nine."

**IMPORTANT**: This plugin uses `.flux/` for ALL task tracking. Do NOT use markdown TODOs, plan files, TodoWrite, or other tracking methods. All task state must be read and written via `fluxctl`.

**CRITICAL: fluxctl is BUNDLED — NOT installed globally.** `which fluxctl` will fail (expected). Always use:
```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}"
[ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
$FLUXCTL <command>
```

**Agent Compatibility**: This skill works across Claude Code, OpenCode, and Codex. See [agent-compat.md](../../docs/agent-compat.md) for tool differences.

**Question Tool**: Use the appropriate tool for your agent:
- Claude Code: `AskUserQuestion`
- OpenCode: `mcp_question`
- Codex: `AskUserTool`
- Other: Output question as text, wait for response

## Pre-check: Local setup version

If `.flux/meta.json` exists and has `setup_version`, compare to plugin version:
```bash
SETUP_VER=$(jq -r '.setup_version // empty' .flux/meta.json 2>/dev/null)
PLUGIN_ROOT="${PLUGIN_ROOT}"
[ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
PLUGIN_JSON="${PLUGIN_ROOT}/.claude-plugin/plugin.json"
[ -f "$PLUGIN_JSON" ] || PLUGIN_JSON="${PLUGIN_ROOT}/.factory-plugin/plugin.json"
PLUGIN_VER=$(jq -r '.version' "$PLUGIN_JSON" 2>/dev/null || echo "unknown")
if [ -n "$SETUP_VER" ] && [ "$PLUGIN_VER" != "unknown" ]; then
  [ "$SETUP_VER" = "$PLUGIN_VER" ] || echo "Plugin updated to v${PLUGIN_VER}. Run /flux:setup to refresh local scripts (current: v${SETUP_VER})."
fi
```
Continue regardless (non-blocking).

**Role**: product-minded technical interviewer and planner
**Goal**: understand the problem deeply, then create actionable tasks

## Input

Full request: $ARGUMENTS

**Options**:
- `--quick` (default): MVP-focused, ~10 min total
- `--deep`: Thorough scoping, ~45 min total
- `--explore [N]`: Generate N approaches (default 3), scaffold each in parallel, compare visually
- `--linear`: Connect to Linear MCP, browse teams/projects, select issue to scope
- `LIN-123` (or any `XXX-123` pattern): Directly scope a specific Linear issue

Accepts:
- Feature/bug description in natural language
- File path to spec document
- Linear issue identifier (e.g., `LIN-123`, `PROJ-456`)

Examples:
- `/flux:scope Add OAuth login for users`
- `/flux:scope Add user notifications --deep`
- `/flux:scope docs/feature-spec.md`
- `/flux:scope Add permissions system --explore 4`
- `/flux:scope Add dashboard --explore --deep`
- `/flux:scope --linear` — Browse Linear, select issue to scope
- `/flux:scope LIN-42` — Scope Linear issue LIN-42 directly
- `/flux:scope PROJ-123 --deep` — Deep scope Linear issue PROJ-123

If empty, ask: "What should I scope? Describe the feature or bug in 1-5 sentences."

## Detect Mode

Parse arguments for `--deep` flag. Default is quick mode.

```
SCOPE_MODE = "--deep" in arguments ? "deep" : "quick"
```

## Detect Linear Mode

Check for `--linear` flag or Linear issue ID pattern (e.g., `LIN-123`, `PROJ-456`).

```
LINEAR_MODE = "--linear" in arguments
LINEAR_ISSUE_ID = extract pattern matching /[A-Z]+-\d+/ from arguments
```

If `LINEAR_ISSUE_ID` is found, set `LINEAR_MODE = true`.

---

# LINEAR INTEGRATION (if --linear or issue ID detected)

If `LINEAR_MODE` is true, follow this flow before Problem Space interview.

## Step 0.1: Check Linear MCP Availability

Check if Linear MCP tools are available:

```
Try calling: mcp_linear_list_teams (with limit: 1)
```

**If Linear MCP is available**: Continue to Step 0.2
**If Linear MCP is NOT available**: Show installation guidance:

```
Linear MCP is not connected. Setup instructions:

**Claude Code:**
claude mcp add --transport http linear-server https://mcp.linear.app/mcp

Then run /mcp in your session to authenticate with Linear.

**Other clients (Cursor, VS Code, etc.):**
{
  "mcpServers": {
    "linear": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.linear.app/mcp"]
    }
  }
}

Full setup guide: https://linear.app/docs/mcp

Options:
- Continue without Linear (describe feature manually)
- Exit and set up Linear first
```

Use question tool to let user choose.

## Step 0.2: Direct Issue Lookup (if LINEAR_ISSUE_ID provided)

If user provided a specific issue ID (e.g., `LIN-42`):

```
Call: mcp_linear_get_issue(id: LINEAR_ISSUE_ID, includeRelations: true)
```

**If found**: This issue becomes the "project" to scope. Skip to Step 0.5.
**If not found**: Report error, fall back to browse mode (Step 0.3)

## Step 0.3: List Linear Teams

```
Call: mcp_linear_list_teams(limit: 50)
```

Use question tool to present teams:

```
header: "Select Team"
question: "Which Linear team?"
options:
  - label: "Engineering (ENG)"
    description: "45 members"
  - label: "Product (PROD)"
    description: "12 members"
  ...
```

## Step 0.4: List Projects (Linear Project = Flux Epic)

After team selection, list projects:

```
Call: mcp_linear_list_projects(team: selected_team_id, limit: 30, includeArchived: false)
```

**IMPORTANT**: A Linear **Project** maps to a Flux **Epic**. The user selects which project they want to scope and break down into tasks.

Use question tool:

```
header: "Select Project"
question: "Which project do you want to scope? (This will become a Flux epic with tasks)"
options:
  - label: "User Authentication"
    description: "5 issues, 40% complete, High priority"
  - label: "Dashboard Redesign"
    description: "12 issues, 10% complete, Medium priority"
  - label: "API v2 Migration"
    description: "8 issues, 0% complete, Urgent"
  ...
```

## Step 0.5: Pull Project Details

Once project is selected, fetch full details:

```
Call: mcp_linear_get_project(
  query: selected_project_id,
  includeMembers: true,
  includeMilestones: true,
  includeResources: true
)
```

Also fetch existing issues in the project:

```
Call: mcp_linear_list_issues(
  project: selected_project_id,
  limit: 50,
  includeArchived: false
)
```

Extract and structure:
- **Project Name**: Title of the project
- **Description**: Full markdown description
- **State**: planned, started, paused, completed, canceled
- **Priority**: 0-4 (Urgent to Low)
- **Lead**: Project lead
- **Milestones**: Any defined milestones
- **Existing Issues**: Issues already created in this project
- **Target Date**: Deadline if set
- **Progress**: Completion percentage

## Step 0.6: Store Linear Context

Save Linear project ID for later task creation:

```bash
mkdir -p .flux/linear
cat > .flux/linear/pending-scope.json << 'EOF'
{
  "linear_project_id": "PROJECT_UUID",
  "linear_project_slug": "user-authentication",
  "linear_team_id": "TEAM_UUID",
  "linear_team_key": "ENG",
  "existing_issues": ["ENG-142", "ENG-143"],
  "scoped_at": "2026-02-28T12:00:00Z"
}
EOF
```

After epic creation (Step 7), move to epic directory:

```bash
mv .flux/linear/pending-scope.json ".flux/epics/${EPIC_ID}/linear.json"
```

## Step 0.7: Pre-populate Problem Space

Use Linear project data to pre-fill interview context:

```
Based on Linear project "User Authentication":

Description: Implement OAuth2 login with Google and GitHub providers...
Priority: High
Lead: @john
Milestones: MVP (Mar 15), Full Release (Apr 1)
Existing issues: 5 (ENG-140 through ENG-144)

I'll use this as the starting point for scoping. The Double Diamond interview
will validate, expand, and potentially restructure the project breakdown.

The goal is to:
1. Understand the problem deeply (Problem Space)
2. Create well-structured tasks with dependencies
3. Push those tasks back to Linear when done

Proceed with scoping?
```

**Then continue to Phase 1: Problem Space** with Linear context pre-loaded.

The interview questions should reference the Linear project:
- "The project description mentions [X]. Is that the core need, or is there something deeper?"
- "Who requested this project? What's the business driver?"
- "Are the existing 5 issues the right breakdown, or do we need to restructure?"

---
SCOPE_MODE = "--deep" in arguments ? "deep" : "quick"
```

## Setup

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}"
[ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
$FLUXCTL init --json
```

---

# PHASE 1: PROBLEM SPACE

## Step 1: Core Desire (Diverge)

**Goal**: Understand WHY this is being requested.

**CRITICAL**: Use the question tool for your agent (see header). Do NOT output questions as text.

### Quick Mode Questions (pick 2-3):
- "Why do we need this? What's the business driver?"
- "What happens if we don't build this?"
- "Who asked for this and what triggered it?"

### Deep Mode Questions (ask all):
- "Why does the stakeholder want this?"
- "What's the underlying business need?"
- "What happens if we don't build this?"
- "Is this solving a symptom or root cause?"
- "What's the opportunity cost of building this?"

**Output**: Capture core desire in working memory.

## Step 2: Reasoning Chain (Diverge)

**Goal**: Validate the logic from problem to proposed solution.

### Quick Mode (1-2 questions):
- "The ask is X. Is X actually the right solution to the underlying problem?"

### Deep Mode (3-4 questions):
- "What assumptions are we making?"
- "Does the reasoning hold? Walk me through the logic."
- "What would have to be true for this to be the right approach?"
- "Are there simpler alternatives we haven't considered?"

**Output**: Capture assumptions and reasoning validation.

## Step 3: User Perspective (Diverge)

**Goal**: Understand how users will experience this.

### Quick Mode (1-2 questions):
- "How would users react to this? What's their current workaround?"

### Deep Mode (3-4 questions):
- "Who are the users affected by this?"
- "What's their current workaround?"
- "What would delight them vs. just satisfy them?"
- "How will they discover and learn this feature?"

**Output**: Capture user perspective.

## Step 4: Blind Spots (Diverge)

**Goal**: Surface what might be missing.

### Quick Mode (1 question):
- "What are we not thinking about? Who else is affected?"

### Deep Mode (2-3 questions):
- "What are we not thinking about?"
- "Who else is affected by this change?"
- "What related problems exist that we might be ignoring?"

**Output**: Capture blind spots.

## Step 5: Risks (Diverge)

**Goal**: Identify what could go wrong.

### Quick Mode (1 question):
- "What's the biggest risk or what could go wrong?"

### Deep Mode (3-4 questions):
- "What could go wrong with this direction?"
- "What are the risks of building this?"
- "What are the risks of NOT building this?"
- "What's the rollback plan if this fails?"

**Output**: Capture risks.

## Step 6: Problem Statement (Converge)

**Goal**: Synthesize into one clear problem statement.

Present synthesis:
```
Based on our discussion:
- Core need: [summary]
- Key assumptions: [list]
- User impact: [summary]
- Main risk: [summary]

Proposed problem statement:
"[One sentence problem statement]"

Does this capture it? What would you change?
```

Use the question tool to confirm or refine.

**Output**: Final problem statement.

---

# EXPLORE MODE (if --explore)

If `--explore` flag is set, diverge on approaches before converging to solution.

**Read [explore.md](explore.md) for full architecture.**
**See [approaches.md](approaches.md) for approach pattern reference.**

## Step 6.5: Generate Approaches

Generate N fundamentally different approaches to solve the problem. The goal is to find approaches that vary on fundamental axes, not superficial differences.

### 6.5.1: Detect Project Type

Analyze the problem statement to determine the primary domain:

| Signal | Project Type |
|--------|--------------|
| UI, component, layout, form, modal, page, dashboard | **frontend** |
| API, service, database, auth, permissions, queue, cache | **backend** |
| Both UI and data/service concerns | **fullstack** |
| CLI, script, automation, tooling | **tooling** |

### 6.5.2: Generate Approaches by Type

Generate N approaches (default 3, max 5) that vary on **fundamental axes**:

**Frontend Approaches** — vary on interaction pattern:
| Approach | Pattern | Tradeoffs |
|----------|---------|-----------|
| Modal wizard | Step-by-step overlay | + Familiar, clear progress | - Interrupts context |
| Inline expansion | Expand in-place | + Contextual | - Limited space |
| Side panel | Persistent slide-out | + More space, visible | - Takes real estate |
| Full page | Dedicated route | + Maximum space | - Navigation required |
| Command palette | Keyboard-driven | + Fast, power users | - Discovery problem |
| Progressive disclosure | Start minimal, reveal | + Clean initial view | - Hidden complexity |

**Backend Approaches** — vary on architecture pattern:
| Approach | Pattern | Tradeoffs |
|----------|---------|-----------|
| Extend existing | Add to current system | + Low risk, incremental | - May not scale |
| New service | Separate bounded context | + Clean separation | - Operational overhead |
| Event-driven | Async pub/sub | + Decoupled, scalable | - Eventual consistency |
| External provider | Third-party service | + Fast to ship | - Vendor dependency |
| Hybrid/gateway | Facade over multiple | + Flexibility | - Added complexity |
| CQRS | Separate read/write | + Performance | - Complexity |

**Fullstack Approaches** — vary on where logic lives:
| Approach | Pattern | Tradeoffs |
|----------|---------|-----------|
| Server-rendered | Traditional SSR | + Simple mental model | - Page reloads |
| Client-heavy | SPA with API | + Rich interactions | - Initial load |
| Islands | Hybrid partial hydration | + Best of both | - Build complexity |
| Edge-first | Logic at CDN edge | + Low latency | - Limited runtime |

**Tooling Approaches** — vary on interface:
| Approach | Pattern | Tradeoffs |
|----------|---------|-----------|
| CLI flags | Traditional args | + Unix composable | - Learning curve |
| Interactive | Prompts/wizard | + Discoverable | - Not scriptable |
| Config file | Declarative YAML/JSON | + Reproducible | - Verbose |
| GUI wrapper | Desktop/web UI | + Visual | - Extra dep |

### 6.5.3: Format Each Approach

For each approach, provide:

```
[LETTER]) "[Name]" — [Key differentiator in one sentence]
   + [Pro 1]
   + [Pro 2]
   - [Con 1]
   - [Con 2]
   Scope: S/M/L
   Risk: Low/Med/High
   Similar to: [Reference if exists in codebase]
```

### 6.5.4: Present to User

```
Based on the problem statement, I identified this as a [frontend/backend/fullstack/tooling] problem.

Here are [N] fundamentally different approaches:

A) "[Name]" — [differentiator]
   + [pros]
   - [cons]
   Scope: M | Risk: Low

B) "[Name]" — [differentiator]
   + [pros]
   - [cons]
   Scope: S | Risk: Med

C) "[Name]" — [differentiator]
   + [pros]
   - [cons]
   Scope: L | Risk: Low

---

Options:
- Pick approaches to explore: "a,b" or "all"
- Suggest alternatives: "What about X approach?"
- Modify an approach: "For A, what if we also..."
- Change scope: "Generate backend-focused approaches instead"
```

Use the question tool with options:
- `a`, `b`, `c`, etc. — Select specific approaches
- `all` — Explore all generated approaches
- `suggest` — User provides their own approach ideas
- `modify` — User refines a generated approach
- `regen` — Generate different approaches (different axis)

### 6.5.5: Handle User Response

**If user selects approaches**: Continue to Step 6.6 with selected list
**If user suggests alternative**: Add to list, re-present for confirmation
**If user modifies approach**: Update approach definition, re-present
**If user asks to regenerate**: Ask what axis to vary on, generate new set

### 6.5.6: Record Approach Decisions

Store approach metadata for later reference:

```bash
$FLUXCTL explore init --epic <epic-id> --approaches "a:Modal wizard,b:Side panel" --json
```

This captures:
- Which approaches were considered
- Which were selected for exploration
- User's rationale (if provided)

## Step 6.6: Create Exploration Worktrees

For each selected approach, create an isolated git worktree.

### 6.6.1: Pre-flight Checks

```bash
# Verify git repo exists
git rev-parse --show-toplevel || {
  echo "Not a git repo. Explore mode requires git for worktree isolation."
  echo "Falling back to single-approach mode (no parallel exploration)."
  # Continue with v1 flow (single approach)
}

# Check for uncommitted changes
git diff --quiet && git diff --cached --quiet || {
  echo "Uncommitted changes detected. Commit or stash before exploring."
  # Use question tool to ask: "Stash changes and continue?" or "Abort"
}
```

### 6.6.2: Create Directory Structure

```bash
mkdir -p .flux/explore/previews

# Add to .gitignore if not present
grep -q "^.flux/explore/" .gitignore 2>/dev/null || echo ".flux/explore/" >> .gitignore
```

### 6.6.3: Create Worktrees

For each selected approach (a, b, c, etc.):

```bash
EPIC_ID="<epic-id>"  # e.g., fn-5-user-dashboard
APPROACH="a"         # or b, c, etc.
BRANCH="explore/${EPIC_ID}/approach-${APPROACH}"
WORKTREE=".flux/explore/approach-${APPROACH}"

# Get current branch as base
BASE_BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null || git rev-parse HEAD)

# Create worktree with new branch
git worktree add -b "$BRANCH" "$WORKTREE" "$BASE_BRANCH"

# Copy .env files (don't overwrite)
for f in .env*; do
  [[ -f "$f" ]] && cp -n "$f" "$WORKTREE/" 2>/dev/null || true
done

echo "Created worktree: $WORKTREE (branch: $BRANCH)"
```

### 6.6.4: Handle Errors

| Error | Action |
|-------|--------|
| Not a git repo | Fall back to v1 (single approach) |
| Worktree already exists | Ask user: reuse, remove & recreate, or abort |
| Branch already exists | Use existing branch, or create with suffix |
| Uncommitted changes | Ask to stash or abort |

### 6.6.5: Record Worktree State

```bash
$FLUXCTL explore set-worktrees --epic <epic-id> \
  --worktree "a:.flux/explore/approach-a" \
  --worktree "b:.flux/explore/approach-b" \
  --json
```

## Step 6.7: Parallel Scaffolding

Spawn parallel agents to scaffold each approach. Each agent works in complete isolation.

### 6.7.1: Agent Prompt Template

For each approach, spawn a Task with this prompt:

```
You are scaffolding Approach [LETTER]: "[NAME]"

## Problem Statement
[PROBLEM_STATEMENT from Step 6]

## Approach Description
[APPROACH_DESCRIPTION from Step 6.5]
Key differentiator: [DIFFERENTIATOR]
Tradeoffs: [PROS/CONS]

## Your Workspace
Working directory: [WORKTREE_PATH]
This is an isolated git worktree. Changes here don't affect the main branch.

## Your Task
1. **Research** (2 min max)
   - Scan existing codebase for relevant patterns
   - Identify files to modify or create
   - Note any dependencies needed

2. **Scaffold** (5 min max)
   - Create minimal implementation that demonstrates this approach
   - Focus on the KEY DIFFERENTIATOR — show what makes this approach unique
   - This is a prototype, not production code

3. **Document**
   - Create APPROACH.md in the worktree root with:
     - What you built
     - Key files created/modified
     - What's working vs stubbed
     - Estimated effort for full implementation

4. **Preview** (if frontend)
   - If this creates UI, ensure it can render (even with mock data)
   - Note any setup needed to see the preview

## Constraints
- **Time limit**: 8 minutes total
- **Scope**: Minimal viable prototype — enough to evaluate, not to ship
- **No deps**: Don't install new packages unless absolutely required
- **Stay isolated**: Only modify files in your worktree

## Output
Return a JSON summary:
{
  "approach": "[LETTER]",
  "name": "[NAME]",
  "status": "success" | "partial" | "failed",
  "files_created": ["path1", "path2"],
  "files_modified": ["path3"],
  "preview_url": "http://localhost:3001" | null,
  "preview_type": "live" | "static_html" | "ascii" | null,
  "effort_estimate": "S" | "M" | "L",
  "notes": "Any issues or observations"
}
```

### 6.7.2: Spawn Parallel Agents

Use the Task tool to spawn N agents simultaneously:

```
For approaches [a, b, c]:
  Task(
    subagent_type: "general",
    description: "Scaffold approach [LETTER]",
    prompt: [AGENT_PROMPT from 6.7.1],
    timeout: 600000  # 10 minutes
  )
```

**CRITICAL**: Launch ALL agents in a single message with multiple Task calls. This enables true parallel execution.

### 6.7.3: Handle Results

Collect results from all agents:

| Status | Action |
|--------|--------|
| `success` | Continue to preview generation |
| `partial` | Note limitations, still usable for comparison |
| `failed` | Log error, skip this approach in comparison |

If all approaches fail:
- Report errors to user
- Ask if they want to retry, modify approaches, or abort

### 6.7.4: Save Scaffold Results

```bash
$FLUXCTL explore set-results --epic <epic-id> \
  --result 'a:{"status":"success","effort":"M"}' \
  --result 'b:{"status":"partial","effort":"S"}' \
  --json
```

### 6.7.5: Timeout Handling

If an agent times out (10 min):
1. Mark approach as `timeout` status
2. Check if any files were created in worktree
3. If partial progress, still include in comparison with note
4. If no progress, exclude from comparison

**Timeout**: 10 minutes per approach. This is for evaluation, not production.

## Step 6.8: Generate Previews

For frontend variations, capture visual previews so users can SEE the differences.

### 6.8.1: Detect Preview Type Needed

Check scaffold results from Step 6.7:

```
For each approach:
  If result.preview_type == "live":     → Try live screenshot
  If result.preview_type == "static_html": → Generate static preview
  If result.preview_type == "ascii":    → Generate ASCII wireframe
  If result.preview_type == null:       → Backend-only, skip preview
```

### 6.8.2: Live Screenshot (Preferred)

Use `agent-browser` to capture running UI:

```bash
APPROACH="a"
WORKTREE=".flux/explore/approach-${APPROACH}"
PORT=$((3000 + APPROACH_INDEX))  # 3001, 3002, 3003...

# Start dev server in worktree (background)
cd "$WORKTREE" && npm run dev -- --port $PORT &
DEV_PID=$!

# Wait for server to be ready (max 30s)
for i in {1..30}; do
  curl -s "http://localhost:$PORT" > /dev/null && break
  sleep 1
done

# Capture screenshot
agent-browser open "http://localhost:$PORT"
agent-browser wait --load networkidle
agent-browser screenshot ".flux/explore/previews/approach-${APPROACH}.png" --full
agent-browser close

# Cleanup
kill $DEV_PID 2>/dev/null || true
```

**agent-browser commands used:**
- `open <url>` — Navigate to page
- `wait --load networkidle` — Wait for page to fully load
- `screenshot <path> --full` — Capture full page
- `close` — Close browser

### 6.8.3: Static HTML Preview (Fallback 1)

If dev server can't run, generate standalone HTML:

```html
<!-- .flux/explore/approach-a/preview.html -->
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Approach A: Modal Wizard</title>
  <style>
    /* Extract relevant styles from scaffold */
    /* Or use inline Tailwind CDN */
  </style>
</head>
<body>
  <!-- Render the component markup statically -->
  <!-- Use placeholder data for dynamic content -->
</body>
</html>
```

Then screenshot the HTML file:

```bash
agent-browser open "file://${PWD}/.flux/explore/approach-a/preview.html"
agent-browser screenshot ".flux/explore/previews/approach-a.png"
agent-browser close
```

### 6.8.4: ASCII Wireframe (Fallback 2)

If browser automation unavailable, generate text-based wireframe:

```
Approach A: Modal Wizard
========================

┌─────────────────────────────────────────┐
│ ╔═══════════════════════════════════╗   │
│ ║        Create New Item            ║   │
│ ╠═══════════════════════════════════╣   │
│ ║  Step 1 of 3: Basic Info          ║   │
│ ║                                   ║   │
│ ║  Name:  [____________________]    ║   │
│ ║  Type:  [▼ Select type      ]    ║   │
│ ║                                   ║   │
│ ║  ┌─────────┐  ┌─────────────────┐ ║   │
│ ║  │ Cancel  │  │ Next →          │ ║   │
│ ║  └─────────┘  └─────────────────┘ ║   │
│ ╚═══════════════════════════════════╝   │
│                                         │
│  (Background content dimmed)            │
└─────────────────────────────────────────┘

Key: Modal overlays content, step indicator shows progress
```

Save as `.flux/explore/previews/approach-a.txt`

### 6.8.5: Preview Strategy Selection

Choose strategy based on environment:

| Condition | Strategy |
|-----------|----------|
| Dev server runs + agent-browser available | Live screenshot |
| No dev server but agent-browser available | Static HTML screenshot |
| No agent-browser but terminal | ASCII wireframe |
| Backend-only approach | Skip preview (use text description) |

### 6.8.6: Record Previews

```bash
$FLUXCTL explore set-previews --epic <epic-id> \
  --preview "a:.flux/explore/previews/approach-a.png:screenshot" \
  --preview "b:.flux/explore/previews/approach-b.png:screenshot" \
  --preview "c:.flux/explore/previews/approach-c.txt:ascii" \
  --json
```

### 6.8.7: Handle Failures

| Failure | Action |
|---------|--------|
| Dev server won't start | Fall back to static HTML |
| agent-browser not available | Fall back to ASCII |
| Component won't render | Use ASCII with error note |
| Timeout (2 min) | Skip preview, note in comparison |

Always continue to comparison even if some previews fail — partial information is better than blocking.

## Step 6.9: Present Comparison

Present all approaches side-by-side with their previews.

### 6.9.1: Gather Comparison Data

```bash
$FLUXCTL explore compare <epic-id> --json
```

Returns:
```json
{
  "approaches": [
    {
      "id": "a",
      "name": "Modal wizard",
      "status": "success",
      "preview": ".flux/explore/previews/approach-a.png",
      "preview_type": "screenshot",
      "pros": ["Familiar pattern", "Clear progress"],
      "cons": ["Interrupts context"],
      "effort": "M",
      "files_created": 3,
      "files_modified": 1
    }
  ]
}
```

### 6.9.2: Display Previews

**For screenshot previews**: Display the image inline if the agent supports it, or reference the file path.

**For ASCII previews**: Display the text directly in the comparison.

**For missing previews**: Show placeholder with explanation.

### 6.9.3: Comparison Format

```
═══════════════════════════════════════════════════════════════════════════════
                            APPROACH COMPARISON
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────┬─────────────────────────┬─────────────────────────┐
│      APPROACH A         │      APPROACH B         │      APPROACH C         │
│    "Modal Wizard"       │  "Inline Expansion"     │    "Side Panel"         │
├─────────────────────────┼─────────────────────────┼─────────────────────────┤
│                         │                         │                         │
│  [Screenshot preview]   │  [Screenshot preview]   │  [ASCII wireframe]      │
│  See: previews/a.png    │  See: previews/b.png    │  (displayed below)      │
│                         │                         │                         │
├─────────────────────────┼─────────────────────────┼─────────────────────────┤
│ PROS                    │ PROS                    │ PROS                    │
│ + Familiar UX pattern   │ + Stays in context      │ + Persistent view       │
│ + Clear step progress   │ + Minimal UI footprint  │ + More screen space     │
│                         │                         │                         │
│ CONS                    │ CONS                    │ CONS                    │
│ - Interrupts workflow   │ - Limited space         │ - Takes screen estate   │
│ - Mobile unfriendly     │ - Complex forms hard    │ - May feel cramped      │
├─────────────────────────┼─────────────────────────┼─────────────────────────┤
│ Effort: M (3 files)     │ Effort: S (2 files)     │ Effort: M (4 files)     │
│ Status: ✓ Success       │ Status: ⚠ Partial       │ Status: ✓ Success       │
└─────────────────────────┴─────────────────────────┴─────────────────────────┘

───────────────────────────────────────────────────────────────────────────────
SELECTION OPTIONS:
  a, b, c     → Pick this approach as the winner
  hybrid a+c  → Combine elements from multiple approaches
  refine b    → Modify an approach and regenerate
  discard     → Throw away all, generate new approaches
───────────────────────────────────────────────────────────────────────────────
```

### 6.9.4: Show ASCII Wireframes Inline

If any approach has ASCII preview, display it after the table:

```
───────────────────────────────────────────────────────────────────────────────
APPROACH C WIREFRAME:
───────────────────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────┐
│ Main Content                              │ ┌─────────────────┐ │
│                                           │ │  Side Panel     │ │
│ [existing page content]                   │ │  ─────────────  │ │
│                                           │ │  Name: [____]   │ │
│                                           │ │  Type: [▼___]   │ │
│                                           │ │                 │ │
│                                           │ │  [Save] [Close] │ │
│                                           │ └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘

───────────────────────────────────────────────────────────────────────────────
```

### 6.9.5: Ask for Selection

Use the question tool to get user's choice:

```
Question: "Which approach should we proceed with?"
Options:
  - "a" — Modal Wizard (M effort, familiar pattern)
  - "b" — Inline Expansion (S effort, contextual)  
  - "c" — Side Panel (M effort, persistent)
  - "hybrid" — Combine elements from multiple
  - "refine" — Modify an approach
  - "discard" — Start over with different approaches
```

## Step 6.10: Handle Selection

Based on user's choice, execute the appropriate workflow.

### 6.10.1: Pick Winner (e.g., "a")

The user selected a single approach as the winner.

```bash
# 1. Record the selection
$FLUXCTL explore pick <epic-id> --approach a --json

# 2. Get winning worktree path
WINNER_WORKTREE=".flux/explore/approach-a"
WINNER_BRANCH="explore/<epic-id>/approach-a"

# 3. Merge winning branch to main (or create PR)
git checkout main
git merge "$WINNER_BRANCH" --no-ff -m "feat: implement <epic-title> using approach A (Modal Wizard)"

# Alternative: Create PR instead of direct merge
# git push -u origin "$WINNER_BRANCH"
# gh pr create --title "feat: <epic-title>" --body "Approach: Modal Wizard\n\n..."
```

**After merge:**
- Continue to Step 7 (Create Epic) with the winning approach context
- The scaffold files are now in main branch
- Epic spec will include "Selected Approach: A (Modal Wizard)" with rationale

### 6.10.2: Request Hybrid (e.g., "hybrid a+c")

User wants to combine elements from multiple approaches.

```
Question: "Describe the hybrid you want:"
Example: "Modal flow from A for initial setup, side panel from C for editing"
```

**Workflow:**
```bash
# 1. Create new worktree for hybrid
git worktree add .flux/explore/approach-hybrid -b explore/<epic-id>/approach-hybrid

# 2. Spawn agent to create hybrid
Task(
  subagent_type: "general",
  description: "Create hybrid approach",
  prompt: """
  Create a hybrid of approaches A and C.
  
  User specification: "Modal flow from A for initial setup, side panel from C for editing"
  
  Approach A worktree: .flux/explore/approach-a
  Approach C worktree: .flux/explore/approach-c
  Your worktree: .flux/explore/approach-hybrid
  
  1. Copy relevant files from both approaches
  2. Merge the implementations as specified
  3. Resolve any conflicts
  4. Create preview
  
  Return JSON summary when complete.
  """
)

# 3. Generate preview for hybrid
# (Same as Step 6.8)

# 4. Present updated comparison (including hybrid)
# Return to Step 6.9 with hybrid added
```

### 6.10.3: Refine Approach (e.g., "refine b")

User wants to modify an approach before deciding.

```
Question: "What changes should I make to approach B?"
Example: "Make the inline expansion taller, add tabs for different sections"
```

**Workflow:**
```bash
# 1. Spawn agent to refine
Task(
  subagent_type: "general",
  description: "Refine approach B",
  prompt: """
  Refine approach B based on user feedback.
  
  User feedback: "Make the inline expansion taller, add tabs for different sections"
  
  Your worktree: .flux/explore/approach-b
  
  1. Read existing implementation
  2. Apply the requested changes
  3. Update APPROACH.md with changes made
  4. Regenerate preview
  
  Return JSON summary when complete.
  """
)

# 2. Regenerate preview
# (Same as Step 6.8)

# 3. Present updated comparison
# Return to Step 6.9 with updated B
```

### 6.10.4: Discard All (e.g., "discard")

User wants to start over with different approaches.

```
Question: "What different directions should I explore?"
Options:
  - "Generate completely different patterns"
  - "Focus on [user specifies axis]"
  - "I'll describe what I want"
```

**Workflow:**
```bash
# 1. Record discard decision
$FLUXCTL explore discard <epic-id> --reason "User requested different directions" --json

# 2. Cleanup all worktrees
git worktree remove .flux/explore/approach-a --force
git worktree remove .flux/explore/approach-b --force
git worktree remove .flux/explore/approach-c --force

# 3. Delete exploration branches
git branch -D explore/<epic-id>/approach-a
git branch -D explore/<epic-id>/approach-b
git branch -D explore/<epic-id>/approach-c

# 4. Return to Step 6.5 with new direction
# Re-generate approaches based on user feedback
```

### 6.10.5: Record Decision Rationale

After any selection, capture why:

```bash
$FLUXCTL explore set-decision <epic-id> \
  --selected "a" \
  --rationale "Modal wizard chosen for familiar UX pattern. Team prefers proven patterns for first iteration." \
  --rejected "b:too limited for complex forms,c:screen space concerns on small monitors" \
  --json
```

This goes into the epic spec for future reference.

## Step 6.11: Cleanup

After successful selection and merge, cleanup exploration artifacts.

### 6.11.1: Remove Non-Selected Worktrees

```bash
SELECTED="a"
EPIC_ID="<epic-id>"

# List all exploration worktrees
for dir in .flux/explore/approach-*; do
  approach=$(basename "$dir" | sed 's/approach-//')
  
  if [[ "$approach" != "$SELECTED" && "$approach" != "hybrid" ]]; then
    echo "Removing worktree: $dir"
    git worktree remove "$dir" --force
    
    # Optionally delete branch
    # git branch -D "explore/${EPIC_ID}/approach-${approach}"
  fi
done
```

### 6.11.2: Handle Winning Worktree

Options for the winning approach:

**Option A: Already merged (recommended)**
```bash
# Worktree contents are in main branch, remove worktree
git worktree remove ".flux/explore/approach-${SELECTED}" --force
```

**Option B: Keep for reference**
```bash
# Move to .flux/archive/ for later reference
mv ".flux/explore/approach-${SELECTED}" ".flux/archive/${EPIC_ID}/"
```

### 6.11.3: Preserve Previews

Move previews to epic documentation:

```bash
# Copy winning preview to epic assets
mkdir -p ".flux/epics/${EPIC_ID}/assets"
cp ".flux/explore/previews/approach-${SELECTED}.png" ".flux/epics/${EPIC_ID}/assets/selected-approach.png"

# Keep comparison for decision record
cp ".flux/explore/previews/"* ".flux/epics/${EPIC_ID}/assets/comparison/"
```

### 6.11.4: Final Cleanup

```bash
# Remove empty explore directory
rm -rf .flux/explore/previews
rmdir .flux/explore 2>/dev/null || true

# Record cleanup completion
$FLUXCTL explore cleanup <epic-id> --json
```

### 6.11.5: Verify Clean State

```bash
# Check no orphaned worktrees
git worktree list | grep "explore/${EPIC_ID}" && echo "WARNING: Orphaned worktrees found"

# Check no uncommitted changes
git status --short
```

---

# PHASE 2: SOLUTION SPACE

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
$FLUXCTL config get memory.enabled --json
$FLUXCTL config get scouts.github --json
```

**Set epic branch:**
```bash
$FLUXCTL epic set-branch <epic-id> --branch "<epic-id>" --json
```

**Run scouts in parallel** (same as flux-plan):

| Scout | Purpose | Required |
|-------|---------|----------|
| `flux:repo-scout` | Grep/Glob/Read patterns | YES |
| `flux:practice-scout` | Best practices + pitfalls | YES |
| `flux:docs-scout` | External documentation | YES |
| `flux:github-scout` | Cross-repo patterns | IF scouts.github |
| `flux:memory-scout` | Project memory | IF memory.enabled |
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

---

# LINEAR TASK CREATION (if Linear mode)

If `LINEAR_MODE` is true, create tasks in Linear after local epic/tasks are created.

## Step 13: Create Linear Issues

For each task created in `.flux/`, create a corresponding Linear issue:

```
For each task in $FLUXCTL tasks --epic <epic-id> --json:
  Call: mcp_linear_save_issue(
    title: task.title,
    description: task.description + "\n\n---\nFlux Task: " + task.id,
    team: LINEAR_TEAM_ID (from Step 0.6),
    project: LINEAR_PROJECT_ID (from Step 0.6),
    priority: map_priority(task.priority),  # 0=None, 1=Urgent, 2=High, 3=Normal, 4=Low
    labels: ["flux-managed"],
    state: "backlog"
  )
  
  Store mapping: task.id → linear_issue_id
```

**Priority mapping:**
- Flux P0 → Linear 1 (Urgent)
- Flux P1 → Linear 2 (High)
- Flux P2 → Linear 3 (Normal)
- Flux P3 → Linear 4 (Low)
- Flux P4 → Linear 4 (Low)

## Step 14: Create Linear Dependencies

After all issues are created, set up blocking relationships:

```
For each dependency in $FLUXCTL deps --epic <epic-id> --json:
  blocked_issue = linear_issue_map[dependency.blocked_by]
  blocking_issue = linear_issue_map[dependency.task_id]
  
  Call: mcp_linear_save_issue(
    id: blocking_issue,
    blockedBy: [blocked_issue]
  )
```

## Step 15: Update Linear Mapping

Store the full mapping for future sync:

```bash
cat > ".flux/epics/${EPIC_ID}/linear.json" << 'EOF'
{
  "linear_project_id": "PROJECT_UUID",
  "linear_team_id": "TEAM_UUID",
  "linear_team_key": "ENG",
  "task_mapping": {
    "fn-1.1": "ENG-150",
    "fn-1.2": "ENG-151",
    "fn-1.3": "ENG-152"
  },
  "synced_at": "2026-02-28T14:30:00Z",
  "sync_direction": "flux_to_linear"
}
EOF
```

## Step 16: Report Linear Sync

```
Linear sync complete:

Project: User Authentication
Created issues:
  - ENG-150: Set up OAuth2 provider config (blocked by: none)
  - ENG-151: Implement Google OAuth flow (blocked by: ENG-150)
  - ENG-152: Implement GitHub OAuth flow (blocked by: ENG-150)
  - ENG-153: Add auth token refresh logic (blocked by: ENG-151, ENG-152)
  - ENG-154: Write integration tests (blocked by: ENG-153)

View in Linear: https://linear.app/team/ENG/project/user-authentication
```

---

## Completion

Show summary:

```
Epic <epic-id> created: "<title>"

Problem Statement:
"<one sentence>"

Tasks: N total | Sizes: Xs S, Ym M

Next steps:
1) Start work: /flux:work <epic-id>
2) Review the plan: /flux:plan-review <epic-id>
3) Deep dive on specific tasks: /flux:scope <task-id> --deep
```

**If Linear mode was used**, also show:
```
Linear: Synced to project "User Authentication"
Issues created: ENG-150 through ENG-154
View: https://linear.app/team/ENG/project/user-authentication
```

---

## Update Check (End of Command)

**ALWAYS run at the very end of /flux:scope execution:**

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}"
[ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
UPDATE_JSON=$("$PLUGIN_ROOT/scripts/version-check.sh" 2>/dev/null || echo '{"update_available":false}')
UPDATE_AVAILABLE=$(echo "$UPDATE_JSON" | jq -r '.update_available')
LOCAL_VER=$(echo "$UPDATE_JSON" | jq -r '.local_version')
REMOTE_VER=$(echo "$UPDATE_JSON" | jq -r '.remote_version')
```

**If update available**, append to output:

```
---
Flux update available: v${LOCAL_VER} → v${REMOTE_VER}
Run: /plugin marketplace update nairon-flux
Then restart Claude Code for changes to take effect.
---
```

**If no update**: Show nothing (silent).

## Philosophy

> "The constraint used to be 'can we build it.' Now it's 'do we know what we're building.'"

**The bottleneck has flipped.** Agents can prototype faster than any team ever could. Execution is cheap. Clarity is the constraint.

**Specs are hypotheses, not canonical truths.** They're testable, run in parallel, and thrown away. This is the first time software engineers have been able to work this way at scale.

**Teams used to skip the first diamond.** Writing one implementation takes weeks, so you can't afford to build three approaches and compare them. You pick something plausible and commit before you can evaluate alternatives. This is why so many architecture decisions feel arbitrary in retrospect.

**Agents change the cost structure.** Working code in hours rather than weeks, against your actual codebase. When exploration is cheap, you stop guessing and start testing.

The Double Diamond forces you to:
1. **Diverge** on the problem — explore broadly (what teams couldn't afford before)
2. **Converge** on the problem — commit to one clear statement
3. **Diverge** on solutions — research options, consider alternatives
4. **Converge** on solution — create actionable tasks

**The skill that matters now:** Knowing what to build, defining boundaries, making implicit knowledge explicit, recognizing failure modes before they become production incidents.

Quick mode gets you enough to start. Deep mode is for high-stakes or ambiguous features. Both give you clarity before execution.
