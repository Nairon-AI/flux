#!/usr/bin/env python3
"""
Flux Session Parser - Analyzes Claude Code sessions for pain points and patterns.

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
                                if item.get("is_error"):
                                    result["tool_errors"].append(
                                        {
                                            "tool_use_id": item.get(
                                                "tool_use_id", "unknown"
                                            ),
                                            "content": str(item.get("content", ""))[
                                                :200
                                            ],
                                        }
                                    )

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

    except (IOError, OSError) as e:
        result["error"] = str(e)

    # Convert defaultdict to regular dict for JSON serialization
    result["tools_used"] = dict(result["tools_used"])

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

    # Convert to JSON-serializable format
    aggregated["api_errors"]["by_code"] = dict(aggregated["api_errors"]["by_code"])
    aggregated["error_patterns"]["by_type"] = dict(
        aggregated["error_patterns"]["by_type"]
    )
    aggregated["knowledge_gaps"]["by_type"] = dict(
        aggregated["knowledge_gaps"]["by_type"]
    )
    aggregated["tool_usage"] = dict(aggregated["tool_usage"])
    aggregated["projects_analyzed"] = list(aggregated["projects_analyzed"])

    return aggregated


def find_session_files(
    days_back: int = DEFAULT_DAYS_BACK, max_sessions: int = DEFAULT_MAX_SESSIONS
) -> list[Path]:
    """Find recent session files."""
    if not SESSIONS_DIR.exists():
        return []

    cutoff = datetime.now() - timedelta(days=days_back)
    session_files = []

    for session_file in SESSIONS_DIR.rglob("*.jsonl"):
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
    parser.add_argument("--project", help="Filter to specific project path pattern")
    args = parser.parse_args()

    session_files = find_session_files(args.days, args.max_sessions)

    if args.project:
        session_files = [f for f in session_files if args.project in str(f)]

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
