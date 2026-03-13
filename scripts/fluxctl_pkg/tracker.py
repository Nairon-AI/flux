"""
Tracker integration hooks.

When a tracker provider is configured (e.g. Linear), these hooks sync
Flux state changes to the external tracker. If no tracker is configured,
all hooks are no-ops.

Uses Linear's GraphQL API directly via urllib (no external dependencies).
Reads LINEAR_API_KEY from environment. If missing, hooks silently skip.
"""

import json
import os
import sys
import urllib.request
import urllib.error
from typing import Optional

from .config import get_config


# --- Linear GraphQL helpers ---

LINEAR_API_URL = "https://api.linear.app/graphql"


def _get_api_key() -> Optional[str]:
    """Get Linear API key from env var."""
    return os.environ.get("LINEAR_API_KEY")


def _get_team_id() -> Optional[str]:
    """Get Linear team ID. Resolves team key (e.g. 'ENG') to UUID on first use."""
    return get_config("tracker.teamId")


def _is_enabled() -> bool:
    """Check if a tracker provider is configured and not 'none'."""
    provider = get_config("tracker.provider")
    return provider is not None and provider != "none"


def _get_provider() -> Optional[str]:
    """Get configured tracker provider name."""
    if not _is_enabled():
        return None
    return get_config("tracker.provider")


def _linear_request(query: str, variables: dict) -> Optional[dict]:
    """Make a GraphQL request to Linear. Returns response data or None on failure."""
    api_key = _get_api_key()
    if not api_key:
        return None

    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(
        LINEAR_API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": api_key,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if "errors" in data:
                print(f"[tracker] Linear API error: {data['errors']}", file=sys.stderr)
                return None
            return data.get("data")
    except (urllib.error.URLError, urllib.error.HTTPError, Exception) as e:
        print(f"[tracker] Linear API request failed: {e}", file=sys.stderr)
        return None


def _resolve_team_id(team_key: str) -> Optional[str]:
    """Resolve a team key (e.g. 'ENG') to a Linear team UUID."""
    data = _linear_request(
        "query Teams { teams { nodes { id key name } } }",
        {},
    )
    if not data:
        return None
    for team in data.get("teams", {}).get("nodes", []):
        if team.get("key", "").upper() == team_key.upper():
            return team["id"]
    return None


def _get_resolved_team_id() -> Optional[str]:
    """Get team UUID, resolving from key if needed."""
    team_id = _get_team_id()
    if not team_id:
        return None
    # If it looks like a UUID already, use it directly
    if "-" in team_id and len(team_id) > 10:
        return team_id
    # It's a team key — resolve to UUID
    resolved = _resolve_team_id(team_id)
    return resolved


def _get_workflow_states(team_id: str) -> dict:
    """Get workflow state name→id mapping for a team."""
    data = _linear_request(
        """query WorkflowStates($teamId: String!) {
            workflowStates(filter: { team: { id: { eq: $teamId } } }) {
                nodes { id name type }
            }
        }""",
        {"teamId": team_id},
    )
    if not data:
        return {}
    states = {}
    for node in data.get("workflowStates", {}).get("nodes", []):
        # Map by type for easy lookup: started, completed, cancelled, etc.
        states[node["type"]] = node["id"]
        states[node["name"].lower()] = node["id"]
    return states


# --- Hooks (called by cmd_ functions after local writes) ---


def on_epic_created(epic_data: dict) -> Optional[str]:
    """Create a Linear project for a new epic. Returns project ID or None."""
    if not _is_enabled() or _get_provider() != "linear":
        return None

    team_id = _get_resolved_team_id()
    if not team_id:
        return None

    title = epic_data.get("title", epic_data.get("id", "Untitled"))
    epic_id = epic_data.get("id", "")

    data = _linear_request(
        """mutation CreateProject($input: ProjectCreateInput!) {
            projectCreate(input: $input) {
                success
                project { id name }
            }
        }""",
        {
            "input": {
                "name": f"[{epic_id}] {title}",
                "teamIds": [team_id],
            }
        },
    )
    if data and data.get("projectCreate", {}).get("success"):
        project_id = data["projectCreate"]["project"]["id"]
        print(f"[tracker] Created Linear project: {title} ({project_id})", file=sys.stderr)
        return project_id
    return None


def on_task_created(task_data: dict, project_id: Optional[str] = None) -> Optional[str]:
    """Create a Linear issue for a new task. Returns issue ID or None."""
    if not _is_enabled() or _get_provider() != "linear":
        return None

    team_id = _get_resolved_team_id()
    if not team_id:
        return None

    title = task_data.get("title", task_data.get("id", "Untitled"))
    task_id = task_data.get("id", "")

    input_data = {
        "title": f"[{task_id}] {title}",
        "teamId": team_id,
    }
    if project_id:
        input_data["projectId"] = project_id

    data = _linear_request(
        """mutation CreateIssue($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue { id title identifier }
            }
        }""",
        {"input": input_data},
    )
    if data and data.get("issueCreate", {}).get("success"):
        issue = data["issueCreate"]["issue"]
        issue_id = issue["id"]
        identifier = issue.get("identifier", "")
        print(f"[tracker] Created Linear issue: {identifier} - {title}", file=sys.stderr)
        return issue_id
    return None


def on_status_changed(task_id: str, old_status: str, new_status: str, linear_issue_id: Optional[str] = None) -> None:
    """Update Linear issue status when a task status changes."""
    if not _is_enabled() or _get_provider() != "linear":
        return
    if not linear_issue_id:
        return

    team_id = _get_resolved_team_id()
    if not team_id:
        return

    states = _get_workflow_states(team_id)

    # Map Flux status → Linear workflow state type
    status_map = {
        "in_progress": "started",
        "done": "completed",
        "blocked": "started",  # Linear has no "blocked" — keep as started
        "todo": "unstarted",
    }
    target_type = status_map.get(new_status)
    if not target_type:
        return

    state_id = states.get(target_type)
    if not state_id:
        return

    _linear_request(
        """mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
            issueUpdate(id: $id, input: $input) {
                success
            }
        }""",
        {"id": linear_issue_id, "input": {"stateId": state_id}},
    )
    print(f"[tracker] Updated {task_id} → {new_status} in Linear", file=sys.stderr)


def on_blocked(task_id: str, reason: str, linear_issue_id: Optional[str] = None) -> None:
    """Add a comment to a Linear issue when a task is blocked."""
    if not _is_enabled() or _get_provider() != "linear":
        return
    if not linear_issue_id:
        return

    # Update status
    on_status_changed(task_id, "in_progress", "blocked", linear_issue_id)

    # Add comment with block reason
    _linear_request(
        """mutation CreateComment($input: CommentCreateInput!) {
            commentCreate(input: $input) { success }
        }""",
        {"input": {"issueId": linear_issue_id, "body": f"**Blocked**: {reason}"}},
    )
    print(f"[tracker] Added block comment to {task_id} in Linear", file=sys.stderr)
