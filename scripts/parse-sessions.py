#!/usr/bin/env python3
"""
N-bench Session Parser - Analyzes Claude Code sessions for pain points and patterns.

Extracts:
- API errors and retries
- Tool failures (is_error=true, exit codes, exceptions)
- Knowledge gaps ("I don't know", "can't find", repeated queries)
- Session metrics (duration, message counts)

Output: JSON with aggregated patterns for recommendation matching.
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
import re

# Configuration
SESSIONS_DIR = Path.home() / ".claude" / "projects"
DEFAULT_DAYS_BACK = 7
DEFAULT_MAX_SESSIONS = 50

# Patterns to detect
ERROR_PATTERNS = [
    (r"exit[:\s]+(\d+)", "exit_code"),
    (r"no such file or directory", "file_not_found"),
    (r"command not found", "command_not_found"),
    (r"permission denied", "permission_denied"),
    (r"timeout", "timeout"),
    (r"ENOENT", "file_not_found"),
    (r"EACCES", "permission_denied"),
    (r"ETIMEDOUT", "timeout"),
    (r"Unknown skill:", "unknown_skill"),
    (r"error:", "generic_error"),
]

KNOWLEDGE_GAP_PATTERNS = [
    (r"I don't know how to", "dont_know"),
    (r"I'm not sure how to", "not_sure"),
    (r"I can't find", "cant_find"),
    (r"I couldn't find", "couldnt_find"),
    (r"where is the", "searching"),
    (r"how do I", "how_to"),
]

# Patterns that appear in TOOL OUTPUTS indicating agent made a mistake
# These are errors from compilers, linters, bash, etc.
TOOL_OUTPUT_FRICTION = [
    # TypeScript/JavaScript errors -> api_hallucination (agent used wrong API)
    (r"Property '[\w]+' does not exist on type", "api_hallucination"),
    (r"has no exported member '[\w]+'", "api_hallucination"),
    (r"Cannot find module '[\w/\-@.]+'", "api_hallucination"),
    (r"is not assignable to type", "api_hallucination"),
    (r"'[\w]+' is not a function", "api_hallucination"),
    (r"Cannot read propert(y|ies) of (undefined|null)", "api_hallucination"),
    (r"TypeError:", "api_hallucination"),
    (r"ReferenceError:", "api_hallucination"),
    (r"error TS\d+:", "api_hallucination"),  # TypeScript error codes
    # Python errors
    (r"AttributeError:", "api_hallucination"),
    (r"ImportError:", "api_hallucination"),
    (r"ModuleNotFoundError:", "api_hallucination"),
    (r"NameError:", "api_hallucination"),
    # Lint/format errors in output
    (r"eslint.*error", "lint_errors"),
    (r"prettier.*error", "lint_errors"),
    (r"\d+ error(s)? and \d+ warning", "lint_errors"),
    (r"Parsing error:", "lint_errors"),
    # CSS/styling errors in build output
    (r"(postcss|tailwind|css).*error", "css_issues"),
    (r"Unknown at rule @", "css_issues"),
    (r"Invalid property", "css_issues"),
    # Test failures
    (r"FAIL\s+.*\.test\.", "regressions"),
    (r"AssertionError:", "regressions"),
    (r"Expected .* but (got|received)", "regressions"),
    (r"\d+ (test|spec)s? failed", "regressions"),
    # CI/build failures
    (r"npm ERR!", "ci_failures"),
    (r"Build failed", "ci_failures"),
    (r"exit code 1", "ci_failures"),
    (r"Command failed", "ci_failures"),
]

# Patterns indicating AGENT UNCERTAINTY/CONFUSION
AGENT_CONFUSION_PATTERNS = [
    # Agent admitting mistakes
    (r"I apologize", "shallow_answers"),
    (r"my mistake", "shallow_answers"),
    (r"I was wrong", "shallow_answers"),
    (r"let me (try|correct|fix)", "shallow_answers"),
    (r"that (didn't|did not) work", "shallow_answers"),
    # Agent uncertainty
    (r"I('m| am) not (sure|certain)", "shallow_answers"),
    (r"I don't (know|have|see)", "shallow_answers"),
    (r"I can't (find|determine|figure)", "shallow_answers"),
    # Agent retrying / different approach
    (r"(try|trying) (a |another )?different", "shallow_answers"),
    (r"let me try (again|another|a different)", "shallow_answers"),
    # Agent searching/exploring excessively
    (r"let me (search|look|check|explore)", "search_needed"),
]

# Friction signals from USER messages (frustration, complaints)
# These are the keys expected by the matching engine
FRICTION_PATTERNS = [
    # API/Docs friction -> context7
    (r"method does not exist", "api_hallucination"),
    (r"property .+ does not exist", "api_hallucination"),
    (r"is not a function", "api_hallucination"),
    (r"has no exported member", "api_hallucination"),
    (r"cannot find module", "api_hallucination"),
    (r"that api.+changed", "outdated_docs"),
    (r"deprecated.+use .+ instead", "outdated_docs"),
    (r"docs (are|seem) (outdated|old|wrong)", "outdated_docs"),
    # Search/Research friction -> exa
    (r"is there a (way|tool|library) to", "search_needed"),
    (r"how do (other|people|teams)", "search_needed"),
    (r"what's the best (way|practice|approach)", "search_needed"),
    (r"any (alternatives|options) for", "search_needed"),
    # Memory/Context friction -> supermemory
    (r"I (already|just) told you", "context_forgotten"),
    (r"remember (when|that|earlier)", "context_forgotten"),
    (r"as I (said|mentioned)", "re_explaining"),
    (r"like I said before", "re_explaining"),
    (r"we already discussed", "re_explaining"),
    # UI/Frontend friction -> frontend-models
    (r"(css|style|styling) (isn't|not|doesn't) (work|look)", "css_issues"),
    (r"(ui|layout|design) (looks|is) (wrong|off|broken)", "ui_issues"),
    (r"responsive.+(broken|not working)", "ui_issues"),
    (r"flexbox.+(not|isn't)", "css_issues"),
    (r"grid.+(not|isn't)", "css_issues"),
    (r"tailwind.+(not|isn't|wrong)", "css_issues"),
    # Reasoning friction -> reasoning-models
    (r"think (harder|deeper|more carefully)", "shallow_answers"),
    (r"you missed.+(edge case|scenario)", "edge_case_misses"),
    (r"that's (too simple|shallow|naive)", "shallow_answers"),
    (r"what about (when|if|the case)", "edge_case_misses"),
    (r"you didn't consider", "edge_case_misses"),
    # Lint/Format friction -> oxlint, biome
    (r"lint(ing)? error", "lint_errors"),
    (r"eslint.+error", "lint_errors"),
    (r"prettier.+error", "lint_errors"),
    (r"formatting (error|issue)", "lint_errors"),
    # CI/Hooks friction -> lefthook
    (r"ci (failed|failure|broke)", "ci_failures"),
    (r"pipeline (failed|failure)", "ci_failures"),
    (r"github actions.+fail", "ci_failures"),
    (r"forgot to (lint|format|test)", "forgot_to_lint"),
    (r"should have (run|ran) .+ before", "forgot_to_lint"),
    # Task/Project friction -> linear, beads
    (r"what was I (doing|working on)", "task_tracking_issues"),
    (r"forgot (to|about) .+ (task|issue|ticket)", "task_tracking_issues"),
    (r"we said we('d| would)", "task_tracking_issues"),
    # Testing friction -> stagehand-e2e
    (r"(this|it) (broke|breaks) again", "regressions"),
    (r"regression", "regressions"),
    (r"(test|tests) (are|is|keep) flak", "flaky_tests"),
    (r"intermittent (failure|test)", "flaky_tests"),
    # Git friction
    (r"(hard to|can't) review", "git_history_issues"),
    (r"messy (commit|history)", "git_history_issues"),
    (r"(squash|rebase|amend).+mess", "git_history_issues"),
    # GitHub friction -> github MCP
    (r"create (a |the )?(pr|pull request)", "github_friction"),
    (r"link.+to (issue|ticket)", "github_friction"),
    # Design friction -> figma, pencil
    (r"(design|mockup) doesn't match", "design_friction"),
    (r"what should (it|this) look like", "design_friction"),
    (r"(need|want) a (mockup|design|wireframe)", "design_friction"),
    # Meeting friction -> granola
    (r"in the meeting.+(said|decided|agreed)", "meeting_context_lost"),
    (r"stakeholder (wanted|asked|said)", "meeting_context_lost"),
    # Project conventions -> agents.md
    (r"that's not how we do (it|things)", "project_conventions_unknown"),
    (r"wrong (directory|folder|location)", "project_conventions_unknown"),
    (r"we (use|prefer|have) .+ (here|in this project)", "project_conventions_unknown"),
    # Diagramming friction -> excalidraw
    (r"(draw|create|make) (a |the )?diagram", "needs_diagrams"),
    (r"how does .+ connect to", "needs_diagrams"),
    (r"(visualize|show me) (the )?architecture", "needs_diagrams"),
]


def parse_timestamp(ts_str: str) -> datetime | None:
    """Parse ISO timestamp from session file."""
    if not ts_str:
        return None
    try:
        # Handle various ISO formats
        ts_str = ts_str.replace("Z", "+00:00")
        return datetime.fromisoformat(ts_str)
    except (ValueError, TypeError):
        return None


def extract_text_content(message: dict) -> str:
    """Extract text from message content (handles string and array formats)."""
    content = message.get("content")
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    texts.append(item.get("text", ""))
                elif item.get("type") == "tool_result":
                    result_content = item.get("content", "")
                    if isinstance(result_content, str):
                        texts.append(result_content)
        return "\n".join(texts)
    return ""


def check_patterns(text: str, patterns: list) -> list[tuple[str, str]]:
    """Check text against patterns, return matches with type and context."""
    matches = []
    text_lower = text.lower()
    for pattern, pattern_type in patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            # Get context around match
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                context = text[start:end].strip()
                matches.append((pattern_type, context))
    return matches


def analyze_session(session_path: Path) -> dict:
    """Analyze a single session file."""
    result = {
        "session_id": session_path.stem,
        "project": session_path.parent.name,
        "messages": 0,
        "api_errors": [],
        "tool_errors": [],
        "error_patterns": [],
        "knowledge_gaps": [],
        "friction_signals": defaultdict(int),  # NEW: friction signal counts
        "tools_used": defaultdict(int),
        "start_time": None,
        "end_time": None,
        "duration_ms": 0,
    }

    try:
        with open(session_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                result["messages"] += 1

                # Track timestamps
                ts = parse_timestamp(entry.get("timestamp"))
                if ts:
                    if result["start_time"] is None or ts < result["start_time"]:
                        result["start_time"] = ts
                    if result["end_time"] is None or ts > result["end_time"]:
                        result["end_time"] = ts

                entry_type = entry.get("type")

                # API errors (system messages)
                if entry_type == "system":
                    subtype = entry.get("subtype")
                    if subtype == "api_error":
                        error_info = {
                            "code": entry.get("cause", {}).get("code", "unknown"),
                            "retry_attempt": entry.get("retryAttempt", 0),
                            "max_retries": entry.get("maxRetries", 0),
                        }
                        result["api_errors"].append(error_info)
                    elif subtype == "turn_duration":
                        result["duration_ms"] += entry.get("durationMs", 0)

                # Tool results with errors
                elif entry_type == "user":
                    message = entry.get("message", {})
                    content = message.get("content")

                    if isinstance(content, list):
                        for item in content:
                            if (
                                isinstance(item, dict)
                                and item.get("type") == "tool_result"
                            ):
                                tool_content = str(item.get("content", ""))

                                if item.get("is_error"):
                                    result["tool_errors"].append(
                                        {
                                            "tool_use_id": item.get(
                                                "tool_use_id", "unknown"
                                            ),
                                            "content": tool_content[:200],
                                        }
                                    )

                                # Scan tool output for friction (agent mistakes)
                                for pattern_type, _ in check_patterns(
                                    tool_content, TOOL_OUTPUT_FRICTION
                                ):
                                    result["friction_signals"][pattern_type] += 1

                    # Check for error patterns in content
                    text = extract_text_content(message)
                    for pattern_type, context in check_patterns(text, ERROR_PATTERNS):
                        result["error_patterns"].append(
                            {
                                "type": pattern_type,
                                "context": context[:100],
                            }
                        )

                    # Check for knowledge gaps
                    for pattern_type, context in check_patterns(
                        text, KNOWLEDGE_GAP_PATTERNS
                    ):
                        result["knowledge_gaps"].append(
                            {
                                "type": pattern_type,
                                "context": context[:100],
                            }
                        )

                    # Check for friction signals (user expressing frustration/issues)
                    for pattern_type, _ in check_patterns(text, FRICTION_PATTERNS):
                        result["friction_signals"][pattern_type] += 1

                # Track tool usage from assistant messages
                elif entry_type == "assistant":
                    message = entry.get("message", {})
                    content = message.get("content")
                    if isinstance(content, list):
                        for item in content:
                            if (
                                isinstance(item, dict)
                                and item.get("type") == "tool_use"
                            ):
                                tool_name = item.get("name", "unknown")
                                result["tools_used"][tool_name] += 1
                            # Check text blocks for agent confusion/uncertainty
                            if isinstance(item, dict) and item.get("type") == "text":
                                text = item.get("text", "")
                                # Agent confusion patterns (apologizing, uncertain, etc.)
                                for pattern_type, _ in check_patterns(
                                    text, AGENT_CONFUSION_PATTERNS
                                ):
                                    result["friction_signals"][pattern_type] += 1
                                # Also check for friction patterns agent might mention
                                for pattern_type, _ in check_patterns(
                                    text, FRICTION_PATTERNS
                                ):
                                    result["friction_signals"][pattern_type] += 1

    except (IOError, OSError) as e:
        result["error"] = str(e)

    # Convert defaultdict to regular dict for JSON serialization
    result["tools_used"] = dict(result["tools_used"])
    result["friction_signals"] = dict(result["friction_signals"])

    # Convert datetimes to strings
    if result["start_time"]:
        result["start_time"] = result["start_time"].isoformat()
    if result["end_time"]:
        result["end_time"] = result["end_time"].isoformat()

    return result


def aggregate_results(sessions: list[dict]) -> dict:
    """Aggregate patterns across all sessions."""
    aggregated = {
        "sessions_analyzed": len(sessions),
        "total_messages": 0,
        "total_duration_ms": 0,
        "api_errors": {
            "total": 0,
            "by_code": defaultdict(int),
            "max_retries_seen": 0,
        },
        "tool_errors": {
            "total": 0,
            "samples": [],
        },
        "error_patterns": {
            "by_type": defaultdict(int),
            "samples": [],
        },
        "knowledge_gaps": {
            "by_type": defaultdict(int),
            "samples": [],
        },
        "friction_signals": defaultdict(int),  # NEW: aggregated friction signals
        "tool_usage": defaultdict(int),
        "projects_analyzed": set(),
    }

    for session in sessions:
        aggregated["total_messages"] += session.get("messages", 0)
        aggregated["total_duration_ms"] += session.get("duration_ms", 0)
        aggregated["projects_analyzed"].add(session.get("project", "unknown"))

        # API errors
        for err in session.get("api_errors", []):
            aggregated["api_errors"]["total"] += 1
            aggregated["api_errors"]["by_code"][err.get("code", "unknown")] += 1
            aggregated["api_errors"]["max_retries_seen"] = max(
                aggregated["api_errors"]["max_retries_seen"],
                err.get("retry_attempt", 0),
            )

        # Tool errors
        for err in session.get("tool_errors", []):
            aggregated["tool_errors"]["total"] += 1
            if len(aggregated["tool_errors"]["samples"]) < 5:
                aggregated["tool_errors"]["samples"].append(err)

        # Error patterns
        for pattern in session.get("error_patterns", []):
            pattern_type = pattern.get("type", "unknown")
            aggregated["error_patterns"]["by_type"][pattern_type] += 1
            if len(aggregated["error_patterns"]["samples"]) < 10:
                aggregated["error_patterns"]["samples"].append(pattern)

        # Knowledge gaps
        for gap in session.get("knowledge_gaps", []):
            gap_type = gap.get("type", "unknown")
            aggregated["knowledge_gaps"]["by_type"][gap_type] += 1
            if len(aggregated["knowledge_gaps"]["samples"]) < 10:
                aggregated["knowledge_gaps"]["samples"].append(gap)

        # Tool usage
        for tool, count in session.get("tools_used", {}).items():
            aggregated["tool_usage"][tool] += count

        # Friction signals
        for signal, count in session.get("friction_signals", {}).items():
            aggregated["friction_signals"][signal] += count

    # Convert to JSON-serializable format
    aggregated["api_errors"]["by_code"] = dict(aggregated["api_errors"]["by_code"])
    aggregated["error_patterns"]["by_type"] = dict(
        aggregated["error_patterns"]["by_type"]
    )
    aggregated["knowledge_gaps"]["by_type"] = dict(
        aggregated["knowledge_gaps"]["by_type"]
    )
    aggregated["friction_signals"] = dict(aggregated["friction_signals"])
    aggregated["tool_usage"] = dict(aggregated["tool_usage"])
    aggregated["projects_analyzed"] = list(aggregated["projects_analyzed"])

    return aggregated


def path_to_claude_project_dir(path: Path) -> str:
    """Convert a path to Claude's project directory name format.

    Claude Code stores sessions in directories like:
    ~/.claude/projects/-Users-obaid-Desktop-myproject/

    The path /Users/obaid/Desktop/myproject becomes -Users-obaid-Desktop-myproject
    """
    # Replace / with - and keep leading dash (from the leading /)
    return str(path).replace("/", "-")


def find_session_files(
    days_back: int = DEFAULT_DAYS_BACK,
    max_sessions: int = DEFAULT_MAX_SESSIONS,
    project_path: Path | None = None,
) -> list[Path]:
    """Find recent session files, optionally filtered to a specific project."""
    if not SESSIONS_DIR.exists():
        return []

    cutoff = datetime.now() - timedelta(days=days_back)
    session_files = []

    # If project_path specified, look only in that project's session dir
    if project_path:
        project_dir_name = path_to_claude_project_dir(project_path)
        project_session_dir = SESSIONS_DIR / project_dir_name

        if not project_session_dir.exists():
            return []

        search_dirs = [project_session_dir]
    else:
        search_dirs = [SESSIONS_DIR]

    for search_dir in search_dirs:
        for session_file in search_dir.rglob("*.jsonl"):
            try:
                mtime = datetime.fromtimestamp(session_file.stat().st_mtime)
                if mtime >= cutoff:
                    session_files.append((session_file, mtime))
            except (OSError, IOError):
                continue

    # Sort by modification time, most recent first
    session_files.sort(key=lambda x: x[1], reverse=True)

    return [f for f, _ in session_files[:max_sessions]]


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Parse Claude Code sessions for patterns"
    )
    parser.add_argument(
        "--days", type=int, default=DEFAULT_DAYS_BACK, help="Days of history to analyze"
    )
    parser.add_argument(
        "--max-sessions",
        type=int,
        default=DEFAULT_MAX_SESSIONS,
        help="Max sessions to analyze",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Output raw per-session data instead of aggregated",
    )
    parser.add_argument(
        "--all-projects",
        action="store_true",
        help="Analyze all projects instead of just current directory",
    )
    parser.add_argument(
        "--cwd",
        type=str,
        default=os.getcwd(),
        help="Project directory to analyze (defaults to current working directory)",
    )
    args = parser.parse_args()

    # Default to current project unless --all-projects specified
    project_path = None if args.all_projects else Path(args.cwd)

    session_files = find_session_files(args.days, args.max_sessions, project_path)

    if not session_files:
        print(
            json.dumps(
                {
                    "enabled": False,
                    "reason": "No recent sessions found",
                    "sessions_dir": str(SESSIONS_DIR),
                }
            )
        )
        return

    sessions = []
    for session_file in session_files:
        sessions.append(analyze_session(session_file))

    if args.raw:
        output = {
            "enabled": True,
            "sessions": sessions,
        }
    else:
        output = {
            "enabled": True,
            **aggregate_results(sessions),
        }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
