# Linear Integration

Linear integration for `/flux:scope`. Handles both browsing/selecting Linear issues (Steps 0.1-0.7) and syncing tasks back to Linear (Steps 13-16).

A Linear **Project** maps to a Flux **Epic**. The user selects which project to scope and break down into tasks.

---

## Step 0.1: Check Linear MCP Availability

Check if Linear MCP tools are available:

```
Try calling: mcp_linear_list_teams (with limit: 1)
```

**If Linear MCP is available**: Continue to Step 0.2
**If Linear MCP is NOT available**: Show installation guidance:

```
Linear MCP is not connected. Setup instructions:

**Claude:**
- Run /mcp in chat
- Add server URL: https://mcp.linear.app/mcp
- Authenticate in the MCP dialog

If you prefer CLI, run this in an external terminal (not inside an active agent session):
claude mcp add --transport http linear-server https://mcp.linear.app/mcp

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

# LINEAR TASK CREATION (after local epic/tasks created)

If `LINEAR_MODE` is true, create tasks in Linear after local epic/tasks are created.

## Step 13: Create Linear Issues

For each task created in `.flux/`, create a corresponding Linear issue.

### Title Rules (CRITICAL)

The Linear issue title MUST be a **clean, human-readable title only**. Specifically:

- **YES**: `"Set up OAuth2 provider config"`, `"Implement Google OAuth flow"`, `"Add auth token refresh logic"`
- **NO**: `"[fn-1-add-oauth.1] Set up OAuth2 provider config"` — NEVER prefix with Flux task IDs
- **NO**: `"fn-1.1: Set up OAuth2 provider config"` — NEVER prefix with Flux IDs in any format

The Flux task ID is stored as an invisible HTML comment in the description. It must never appear in the title.

### Description Rules

The Linear issue description MUST contain enough context for someone to understand the task **without reading other issues**. Copy the full task spec from `.flux/`:

```
For each task in $FLUXCTL tasks --epic <epic-id> --json:

  # Get the full task spec
  TASK_SPEC=$($FLUXCTL cat <task-id>)

  # Build the Linear description:
  # 1. Full task spec (description, context, approach, constraints, acceptance criteria)
  # 2. Dependencies listed as Linear issue links (not Flux IDs)
  # 3. Invisible Flux sync marker

  DESCRIPTION = TASK_SPEC + "\n\n---\n"
  # Add dependency links if task has deps
  if task.depends_on:
    DESCRIPTION += "**Blocked by:**\n"
    for dep in task.depends_on:
      DESCRIPTION += "- " + linear_issue_map[dep] + "\n"  # e.g., "- ENG-150"
    DESCRIPTION += "\n"
  DESCRIPTION += "<!-- flux:task-id=" + task.id + " -->"

  Call: mcp_linear_save_issue(
    title: task.title,   # CLEAN title only — NO Flux task ID prefix
    description: DESCRIPTION,
    team: LINEAR_TEAM_ID (from Step 0.6),
    project: LINEAR_PROJECT_ID (from Step 6.5.2),
    assignee: SELECTED_USER_ID (from Step 6.5.3, omit if "Unassigned"),
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

## Step 14: Create Linear Dependencies (Blocking Relations)

After ALL issues are created, set up blocking relationships so Linear shows the dependency graph. The Linear MCP does NOT support relations via `save_issue` — you must use `mcp_linear_create_issue_relation`.

**If `mcp_linear_create_issue_relation` is available:**

```
For each task that has depends_on in its Flux spec:
  For each dependency_task_id in task.depends_on:
    blocker_linear_id = linear_issue_map[dependency_task_id]  # the issue that must finish first
    blocked_linear_id = linear_issue_map[task.id]             # the issue that's waiting

    Call: mcp_linear_create_issue_relation(
      issueId: blocked_linear_id,
      relatedIssueId: blocker_linear_id,
      type: "blocks"    # blocker_linear_id blocks blocked_linear_id
    )
```

**If `mcp_linear_create_issue_relation` is NOT available**, use the Linear GraphQL API directly:

```bash
# For each dependency pair, create an "isBlockedBy" relation
# blocker_uuid = the UUID of the issue that must finish first
# blocked_uuid = the UUID of the issue that's waiting

curl -s -X POST https://api.linear.app/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: $LINEAR_API_KEY" \
  -d '{
    "query": "mutation { issueRelationCreate(input: { issueId: \"'$blocked_uuid'\", relatedIssueId: \"'$blocker_uuid'\", type: blocks }) { success issueRelation { id } } }"
  }'
```

**To get issue UUIDs** (Linear MCP returns them, but if you only have issue keys like ENG-511):

```bash
# Get the internal UUID for an issue by its identifier
curl -s -X POST https://api.linear.app/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: $LINEAR_API_KEY" \
  -d '{"query": "{ issueSearch(filter: { number: { eq: 511 }, team: { key: { eq: \"ENG\" } } }) { nodes { id identifier } } }"}'
```

**IMPORTANT**: Always create ALL issues first (Step 13), THEN set up ALL relations (Step 14). Relations require both issues to exist.

**Verify relations were created** by checking one issue:

```bash
# Verify an issue shows its blockers
curl -s -X POST https://api.linear.app/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: $LINEAR_API_KEY" \
  -d '{"query": "{ issue(id: \"'$blocked_uuid'\") { identifier relations { nodes { type relatedIssue { identifier } } } } }"}'
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
Assignee: @john

Issues created with dependencies:
  1. ENG-150: Set up OAuth2 provider config
  2. ENG-151: Implement Google OAuth flow          ← blocked by ENG-150
  3. ENG-152: Implement GitHub OAuth flow           ← blocked by ENG-150
  4. ENG-153: Add auth token refresh logic          ← blocked by ENG-151, ENG-152
  5. ENG-154: Write integration tests               ← blocked by ENG-153

Dependency graph:
  ENG-150 → ENG-151 ─┐
                      ├→ ENG-153 → ENG-154
  ENG-150 → ENG-152 ─┘

Parallel: ENG-151 and ENG-152 can run in parallel after ENG-150.

View in Linear: https://linear.app/team/ENG/project/user-authentication
```
