#!/usr/bin/env python3
"""
Flux Score Calculator

Computes AI-native capability score from Claude Code session data.
Reference: https://github.com/douglance/ccql

Data sources:
- ~/.claude/history.jsonl - User prompts
- ~/.claude/transcripts/*.jsonl - Conversation logs
- ~/.claude/todos/*.json - Task items

Usage:
    python3 flux-score.py                    # Score from default data dir
    python3 flux-score.py --data-dir ~/.claude
    python3 flux-score.py --since 2026-02-01 --until 2026-02-23
    python3 flux-score.py --format json
    python3 flux-score.py --export evidence.yaml
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# =============================================================================
# DATA MODELS
# =============================================================================


@dataclass
class HistoryEntry:
    display: str
    timestamp: int  # Unix ms
    project: Optional[str] = None
    session_id: Optional[str] = None

    @property
    def is_user_prompt(self) -> bool:
        return bool(self.display) and not self.display.startswith("/")

    @property
    def is_command(self) -> bool:
        return self.display.startswith("/")

    @property
    def datetime(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp / 1000)


@dataclass
class TranscriptEntry:
    type: str  # 'user', 'assistant', 'tool_use', 'tool_result'
    session_id: str
    source_file: str
    timestamp: Optional[str] = None
    content: Optional[str] = None
    tool_name: Optional[str] = None
    tool_input: Optional[dict] = None
    tool_output: Optional[dict] = None


@dataclass
class TodoEntry:
    content: str
    status: str  # 'pending', 'in_progress', 'completed'
    workspace_id: str
    agent_id: str


@dataclass
class SessionMetrics:
    session_id: str
    user_messages: int = 0
    tool_calls: int = 0
    tools_used: set = field(default_factory=set)
    pushback_count: int = 0
    exploration_signals: int = 0
    planning_signals: int = 0
    file_references: int = 0
    requirement_signals: int = 0
    errors: int = 0
    todos_completed: int = 0
    prompt_lengths: list = field(default_factory=list)


@dataclass
class NbenchScore:
    period_start: str
    period_end: str
    sessions_analyzed: int

    # Dimension scores (0-100)
    interview_depth: int
    pushback_ratio: int
    prompt_quality: int
    iteration_efficiency: int
    tool_breadth: int

    # Composite
    score: int
    grade: str

    # Strengths and growth areas
    strengths: list = field(default_factory=list)
    growth_areas: list = field(default_factory=list)

    # Raw metrics for evidence
    raw_metrics: dict = field(default_factory=dict)


# =============================================================================
# DATA LOADING
# =============================================================================


def get_default_data_dir() -> Path:
    """Get default Claude data directory."""
    return Path.home() / ".claude"


def load_history(
    data_dir: Path, since: Optional[datetime] = None, until: Optional[datetime] = None
) -> list[HistoryEntry]:
    """Load history.jsonl entries."""
    history_file = data_dir / "history.jsonl"
    if not history_file.exists():
        return []

    entries = []
    with open(history_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                entry = HistoryEntry(
                    display=data.get("display", ""),
                    timestamp=data.get("timestamp", 0),
                    project=data.get("project"),
                    session_id=data.get("sessionId"),
                )

                # Filter by date range
                if since and entry.datetime < since:
                    continue
                if until and entry.datetime > until:
                    continue

                entries.append(entry)
            except json.JSONDecodeError:
                continue

    return entries


def load_transcripts(
    data_dir: Path, since: Optional[datetime] = None, until: Optional[datetime] = None
) -> list[TranscriptEntry]:
    """Load transcript entries from Claude Code session files.

    Claude Code stores sessions in:
    - ~/.claude/projects/{project-path}/*.jsonl (per-project sessions)
    - ~/.claude/transcripts/*.jsonl (legacy location)
    """
    entries = []

    # Collect all session files from both locations
    session_files = []

    # Primary location: projects directory
    projects_dir = data_dir / "projects"
    if projects_dir.exists():
        for project_dir in projects_dir.iterdir():
            if project_dir.is_dir():
                session_files.extend(project_dir.glob("*.jsonl"))

    # Legacy location: transcripts directory
    transcripts_dir = data_dir / "transcripts"
    if transcripts_dir.exists():
        session_files.extend(transcripts_dir.glob("*.jsonl"))

    for jsonl_file in session_files:
        # Extract session ID from filename (UUID.jsonl)
        session_id = jsonl_file.stem

        with open(jsonl_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    msg_type = data.get("type", "")

                    # Skip non-message types (progress, file-history-snapshot, etc.)
                    if msg_type not in ("user", "assistant", "tool_use", "tool_result"):
                        continue

                    # Extract content based on message type
                    content = None
                    tool_name = None
                    tool_input = None
                    tool_output = None

                    if msg_type == "user":
                        # Skip meta messages (command injections, caveats)
                        if data.get("isMeta"):
                            continue

                        message = data.get("message", {})
                        content_data = message.get("content", "")
                        if isinstance(content_data, str):
                            content = content_data
                        elif isinstance(content_data, list):
                            # Extract text from content blocks
                            texts = []
                            for block in content_data:
                                if (
                                    isinstance(block, dict)
                                    and block.get("type") == "text"
                                ):
                                    texts.append(block.get("text", ""))
                            content = " ".join(texts)

                    elif msg_type == "assistant":
                        # Extract tool_use from assistant messages
                        # Parse timestamp for filtering
                        ts_str = data.get("timestamp")
                        entry_dt = None
                        if ts_str:
                            try:
                                entry_dt = datetime.fromisoformat(
                                    ts_str.replace("Z", "+00:00")
                                )
                                entry_dt = entry_dt.replace(tzinfo=None)
                            except (ValueError, AttributeError):
                                pass

                        # Apply date filters
                        if since and entry_dt and entry_dt < since:
                            continue
                        if until and entry_dt and entry_dt > until:
                            continue

                        message = data.get("message", {})
                        content_blocks = message.get("content", [])
                        if isinstance(content_blocks, list):
                            for block in content_blocks:
                                if (
                                    isinstance(block, dict)
                                    and block.get("type") == "tool_use"
                                ):
                                    # Create a tool_use entry
                                    tool_entry = TranscriptEntry(
                                        type="tool_use",
                                        session_id=session_id,
                                        source_file=jsonl_file.name,
                                        timestamp=ts_str,
                                        tool_name=block.get("name"),
                                        tool_input=block.get("input"),
                                    )
                                    entries.append(tool_entry)
                        continue  # Don't add assistant message itself, we extracted tools

                    elif msg_type == "tool_use":
                        tool_name = data.get("tool_name") or data.get("name")
                        tool_input = data.get("tool_input") or data.get("input")

                    elif msg_type == "tool_result":
                        tool_name = data.get("tool_name") or data.get("name")
                        tool_output = data.get("result") or data.get("output")

                    # Parse timestamp for filtering
                    ts_str = data.get("timestamp")
                    entry_dt = None
                    if ts_str:
                        try:
                            # Handle ISO format: 2026-02-22T19:14:19.831Z
                            entry_dt = datetime.fromisoformat(
                                ts_str.replace("Z", "+00:00")
                            )
                            entry_dt = entry_dt.replace(
                                tzinfo=None
                            )  # Make naive for comparison
                        except (ValueError, AttributeError):
                            pass

                    # Apply date filters
                    if since and entry_dt and entry_dt < since:
                        continue
                    if until and entry_dt and entry_dt > until:
                        continue

                    entry = TranscriptEntry(
                        type=msg_type,
                        session_id=session_id,
                        source_file=jsonl_file.name,
                        timestamp=ts_str,
                        content=content,
                        tool_name=tool_name,
                        tool_input=tool_input,
                        tool_output=tool_output,
                    )
                    entries.append(entry)
                except json.JSONDecodeError:
                    continue

    return entries


def load_todos(data_dir: Path) -> list[TodoEntry]:
    """Load todo entries from todos/*.json."""
    todos_dir = data_dir / "todos"
    if not todos_dir.exists():
        return []

    entries = []
    for json_file in todos_dir.glob("*.json"):
        # Parse filename: workspace_id-agent-agent_id.json
        filename = json_file.stem
        parts = filename.split("-agent-")
        if len(parts) != 2:
            continue
        workspace_id, agent_id = parts

        try:
            with open(json_file, "r") as f:
                data = json.load(f)
                todos = data if isinstance(data, list) else data.get("todos", [])
                for todo in todos:
                    entry = TodoEntry(
                        content=todo.get("content", ""),
                        status=todo.get("status", "pending"),
                        workspace_id=workspace_id,
                        agent_id=agent_id,
                    )
                    entries.append(entry)
        except (json.JSONDecodeError, KeyError):
            continue

    return entries


# =============================================================================
# METRICS COMPUTATION
# =============================================================================

# Patterns for detecting quality signals
PUSHBACK_PATTERNS = [
    r"\bno[,.]",
    r"\binstead\b",
    r"\bactually\b",
    r"\bwrong\b",
    r"\bdifferent approach\b",
    r"\bthat\'s not\b",
    r"\bdon\'t\b.*\bthat\b",
    r"\brather\b",
    r"\bwait\b",
]

EXPLORATION_PATTERNS = [
    r"\bedge case\b",
    r"\bwhat if\b",
    r"\bconsider\b",
    r"\bwhat about\b",
    r"\bhow would\b",
    r"\bwhat happens\b",
    r"\bworst case\b",
    r"\bboundary\b",
]

PLANNING_PATTERNS = [
    r"\bplan\b",
    r"\bstep\b",
    r"\bfirst\b.*\bthen\b",
    r"\bbreak.*down\b",
    r"\brequirement\b",
    r"\bacceptance\b",
    r"\bcriteria\b",
]

REQUIREMENT_PATTERNS = [
    r"\bshould\b",
    r"\bmust\b",
    r"\brequire\b",
    r"\bneed to\b",
    r"\bexpect\b",
]

FILE_PATTERNS = [
    r"\.\w{2,4}\b",  # File extensions
    r"line \d+",
    r":\d+",  # file:line
]


def count_pattern_matches(text: str, patterns: list[str]) -> int:
    """Count how many patterns match in the text."""
    if not text:
        return 0
    text_lower = text.lower()
    count = 0
    for pattern in patterns:
        if re.search(pattern, text_lower):
            count += 1
    return count


def compute_session_metrics(
    transcripts: list[TranscriptEntry],
) -> dict[str, SessionMetrics]:
    """Compute metrics per session from transcripts."""
    sessions: dict[str, SessionMetrics] = {}

    for entry in transcripts:
        sid = entry.session_id
        if sid not in sessions:
            sessions[sid] = SessionMetrics(session_id=sid)

        metrics = sessions[sid]

        if entry.type == "user" and entry.content:
            metrics.user_messages += 1
            metrics.prompt_lengths.append(len(entry.content))

            # Quality signals
            metrics.pushback_count += count_pattern_matches(
                entry.content, PUSHBACK_PATTERNS
            )
            metrics.exploration_signals += count_pattern_matches(
                entry.content, EXPLORATION_PATTERNS
            )
            metrics.file_references += count_pattern_matches(
                entry.content, FILE_PATTERNS
            )
            metrics.requirement_signals += count_pattern_matches(
                entry.content, REQUIREMENT_PATTERNS
            )

        elif entry.type == "tool_use" and entry.tool_name:
            metrics.tool_calls += 1
            metrics.tools_used.add(entry.tool_name)

            if entry.tool_name == "TodoWrite":
                metrics.planning_signals += 1

        elif entry.type == "tool_result":
            if entry.tool_output:
                output_str = (
                    json.dumps(entry.tool_output)
                    if isinstance(entry.tool_output, dict)
                    else str(entry.tool_output)
                )
                if "error" in output_str.lower() or "failed" in output_str.lower():
                    metrics.errors += 1

    return sessions


def compute_dimension_scores(
    session_metrics: dict[str, SessionMetrics], todos: list[TodoEntry]
) -> dict:
    """Compute the 5 Flux dimension scores."""
    if not session_metrics:
        return {
            "interview_depth": 0,
            "pushback_ratio": 0,
            "prompt_quality": 0,
            "iteration_efficiency": 0,
            "tool_breadth": 0,
        }

    # Aggregate across sessions
    total_user_messages = sum(m.user_messages for m in session_metrics.values())
    total_pushback = sum(m.pushback_count for m in session_metrics.values())
    total_exploration = sum(m.exploration_signals for m in session_metrics.values())
    total_planning = sum(m.planning_signals for m in session_metrics.values())
    total_file_refs = sum(m.file_references for m in session_metrics.values())
    total_requirement = sum(m.requirement_signals for m in session_metrics.values())
    total_tool_calls = sum(m.tool_calls for m in session_metrics.values())
    total_errors = sum(m.errors for m in session_metrics.values())

    all_prompt_lengths = []
    for m in session_metrics.values():
        all_prompt_lengths.extend(m.prompt_lengths)
    avg_prompt_length = (
        sum(all_prompt_lengths) / len(all_prompt_lengths) if all_prompt_lengths else 0
    )

    all_tools = set()
    for m in session_metrics.values():
        all_tools.update(m.tools_used)

    todos_completed = sum(1 for t in todos if t.status == "completed")
    todos_total = len(todos)

    # =========================================================================
    # 1. INTERVIEW DEPTH (0-100)
    # Measures exploration before implementation
    # =========================================================================
    exploration_per_msg = (
        total_exploration / total_user_messages if total_user_messages else 0
    )
    planning_per_msg = (
        total_planning / total_user_messages if total_user_messages else 0
    )

    # Score based on exploration + planning signals
    interview_raw = (exploration_per_msg * 50) + (planning_per_msg * 50)
    interview_depth = min(100, int(interview_raw * 100))

    # =========================================================================
    # 2. PUSHBACK RATIO (0-100)
    # Measures critical evaluation of AI suggestions
    # =========================================================================
    pushback_per_msg = (
        total_pushback / total_user_messages if total_user_messages else 0
    )

    # Ideal pushback rate is ~20-40% of messages
    # Too low = rubber-stamping, too high = adversarial
    if pushback_per_msg < 0.05:
        pushback_ratio = int(pushback_per_msg * 400)  # 0-20 range
    elif pushback_per_msg < 0.40:
        pushback_ratio = int(20 + (pushback_per_msg - 0.05) * 200)  # 20-90 range
    else:
        pushback_ratio = max(
            60, int(90 - (pushback_per_msg - 0.40) * 100)
        )  # Diminishing
    pushback_ratio = min(100, max(0, pushback_ratio))

    # =========================================================================
    # 3. PROMPT QUALITY (0-100)
    # Measures specificity and context in prompts
    # =========================================================================
    file_ref_per_msg = (
        total_file_refs / total_user_messages if total_user_messages else 0
    )
    req_per_msg = total_requirement / total_user_messages if total_user_messages else 0

    # Score based on length + references + requirements
    length_score = min(40, avg_prompt_length / 10)  # Up to 40 points for length
    ref_score = min(30, file_ref_per_msg * 60)  # Up to 30 points for file refs
    req_score = min(30, req_per_msg * 60)  # Up to 30 points for requirements

    prompt_quality = int(length_score + ref_score + req_score)

    # =========================================================================
    # 4. ITERATION EFFICIENCY (0-100)
    # Measures prompts-to-completion ratio and error rate
    # =========================================================================
    msgs_per_session = (
        total_user_messages / len(session_metrics) if session_metrics else 0
    )
    error_rate = total_errors / total_tool_calls if total_tool_calls else 0
    completion_rate = (
        todos_completed / todos_total if todos_total else 0.5
    )  # Default 50% if no todos

    # Lower messages per session is better (efficient), low error rate is better
    efficiency_raw = (
        max(0, 50 - msgs_per_session * 2)  # Penalize high message count
        + max(0, 30 - error_rate * 100)  # Penalize errors
        + completion_rate * 20  # Reward completions
    )
    iteration_efficiency = min(100, max(0, int(efficiency_raw)))

    # =========================================================================
    # 5. TOOL BREADTH (0-100)
    # Measures appropriate tool usage
    # =========================================================================
    # Categorize tools
    research_tools = {"Read", "Grep", "Glob", "WebFetch", "Task"}
    impl_tools = {"Edit", "Write", "MultiEdit"}
    exec_tools = {"Bash"}
    planning_tools = {"TodoWrite", "AskFollowupQuestion"}

    has_research = bool(all_tools & research_tools)
    has_impl = bool(all_tools & impl_tools)
    has_exec = bool(all_tools & exec_tools)
    has_planning = bool(all_tools & planning_tools)

    breadth_score = (
        (25 if has_research else 0)
        + (25 if has_impl else 0)
        + (25 if has_exec else 0)
        + (25 if has_planning else 0)
    )

    # Bonus for tool diversity
    diversity_bonus = min(20, len(all_tools) * 2)
    tool_breadth = min(100, breadth_score + diversity_bonus)

    return {
        "interview_depth": interview_depth,
        "pushback_ratio": pushback_ratio,
        "prompt_quality": prompt_quality,
        "iteration_efficiency": iteration_efficiency,
        "tool_breadth": tool_breadth,
    }


def compute_composite_score(dimensions: dict) -> tuple[int, str]:
    """Compute weighted composite score and letter grade."""
    # Weights emphasize thinking quality over raw productivity
    weights = {
        "interview_depth": 0.25,
        "pushback_ratio": 0.20,
        "prompt_quality": 0.25,
        "iteration_efficiency": 0.15,
        "tool_breadth": 0.15,
    }

    score = sum(dimensions[k] * weights[k] for k in weights)
    score = int(score)

    # Letter grade
    if score >= 90:
        grade = "S"
    elif score >= 80:
        grade = "A"
    elif score >= 70:
        grade = "B"
    elif score >= 60:
        grade = "C"
    elif score >= 50:
        grade = "D"
    else:
        grade = "F"

    # Add +/- modifiers
    remainder = score % 10
    if grade not in ("S", "F"):
        if remainder >= 7:
            grade += "+"
        elif remainder <= 3:
            grade += "-"

    return score, grade


def identify_strengths_and_growth(dimensions: dict) -> tuple[list[str], list[str]]:
    """Identify top strengths and growth areas."""
    strengths = []
    growth_areas = []

    labels = {
        "interview_depth": (
            "Strong problem exploration before implementation",
            "Could explore edge cases more before coding",
        ),
        "pushback_ratio": (
            "Good critical evaluation of AI suggestions",
            "Consider pushing back more on AI suggestions",
        ),
        "prompt_quality": (
            "High-quality, specific prompts with context",
            "Prompts could include more context and specifics",
        ),
        "iteration_efficiency": (
            "Efficient prompt-to-completion ratio",
            "High rework cycles - consider planning more upfront",
        ),
        "tool_breadth": (
            "Good tool diversity across SDLC phases",
            "Could use more varied tools for different tasks",
        ),
    }

    sorted_dims = sorted(dimensions.items(), key=lambda x: x[1], reverse=True)

    for dim, score in sorted_dims[:2]:
        if score >= 60:
            strengths.append(labels[dim][0])

    for dim, score in sorted_dims[-2:]:
        if score < 70:
            growth_areas.append(labels[dim][1])

    return strengths, growth_areas


def compute_flux_score(
    data_dir: Path, since: Optional[datetime] = None, until: Optional[datetime] = None
) -> NbenchScore:
    """Compute full Flux score from Claude Code data."""

    # Load data
    history = load_history(data_dir, since, until)
    transcripts = load_transcripts(data_dir, since, until)
    todos = load_todos(data_dir)

    # Compute session metrics
    session_metrics = compute_session_metrics(transcripts)

    # Compute dimensions
    dimensions = compute_dimension_scores(session_metrics, todos)

    # Compute composite
    score, grade = compute_composite_score(dimensions)

    # Identify strengths and growth areas
    strengths, growth_areas = identify_strengths_and_growth(dimensions)

    # Raw metrics for evidence
    raw_metrics = {
        "total_sessions": len(session_metrics),
        "total_prompts": len(history),
        "total_transcripts": len(transcripts),
        "total_todos": len(todos),
        "avg_prompts_per_session": len(history) / len(session_metrics)
        if session_metrics
        else 0,
        "tools_used": list(
            set().union(*(m.tools_used for m in session_metrics.values()))
        ),
    }

    # Period
    period_start = since.strftime("%Y-%m-%d") if since else "all-time"
    period_end = until.strftime("%Y-%m-%d") if until else "now"

    return NbenchScore(
        period_start=period_start,
        period_end=period_end,
        sessions_analyzed=len(session_metrics),
        interview_depth=dimensions["interview_depth"],
        pushback_ratio=dimensions["pushback_ratio"],
        prompt_quality=dimensions["prompt_quality"],
        iteration_efficiency=dimensions["iteration_efficiency"],
        tool_breadth=dimensions["tool_breadth"],
        score=score,
        grade=grade,
        strengths=strengths,
        growth_areas=growth_areas,
        raw_metrics=raw_metrics,
    )


# =============================================================================
# OUTPUT FORMATTING
# =============================================================================


def format_table(score: NbenchScore) -> str:
    """Format score as ASCII table."""
    lines = [
        "",
        "═══════════════════════════════════════════════════════════════",
        f"  N-BENCH SCORE: {score.score}  ({score.grade})",
        "═══════════════════════════════════════════════════════════════",
        "",
        f"  Period: {score.period_start} to {score.period_end}",
        f"  Sessions analyzed: {score.sessions_analyzed}",
        "",
        "  DIMENSIONS",
        "  ───────────────────────────────────────────────────────────────",
        f"  Interview Depth:      {score.interview_depth:3d}/100  {'█' * (score.interview_depth // 5)}",
        f"  Pushback Ratio:       {score.pushback_ratio:3d}/100  {'█' * (score.pushback_ratio // 5)}",
        f"  Prompt Quality:       {score.prompt_quality:3d}/100  {'█' * (score.prompt_quality // 5)}",
        f"  Iteration Efficiency: {score.iteration_efficiency:3d}/100  {'█' * (score.iteration_efficiency // 5)}",
        f"  Tool Breadth:         {score.tool_breadth:3d}/100  {'█' * (score.tool_breadth // 5)}",
        "",
    ]

    if score.strengths:
        lines.append("  STRENGTHS")
        lines.append(
            "  ───────────────────────────────────────────────────────────────"
        )
        for s in score.strengths:
            lines.append(f"  ✓ {s}")
        lines.append("")

    if score.growth_areas:
        lines.append("  GROWTH AREAS")
        lines.append(
            "  ───────────────────────────────────────────────────────────────"
        )
        for g in score.growth_areas:
            lines.append(f"  → {g}")
        lines.append("")

    lines.append("═══════════════════════════════════════════════════════════════")
    lines.append("")

    return "\n".join(lines)


def format_json(score: NbenchScore) -> str:
    """Format score as JSON."""
    return json.dumps(asdict(score), indent=2)


def format_yaml(score: NbenchScore) -> str:
    """Format score as YAML (for evidence export)."""
    data = asdict(score)
    lines = []

    def yaml_value(v, indent=0):
        prefix = "  " * indent
        if isinstance(v, list):
            if not v:
                return "[]"
            return "\n" + "\n".join(f"{prefix}- {item}" for item in v)
        elif isinstance(v, dict):
            if not v:
                return "{}"
            return "\n" + "\n".join(
                f"{prefix}{k}: {yaml_value(val, indent + 1)}" for k, val in v.items()
            )
        elif isinstance(v, str):
            return f'"{v}"' if " " in v or ":" in v else v
        else:
            return str(v)

    for key, value in data.items():
        lines.append(f"{key}: {yaml_value(value, 1)}")

    return "\n".join(lines)


# =============================================================================
# CLI
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Compute Flux AI-native capability score from Claude Code data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  flux-score.py                              # Score from default data dir
  flux-score.py --since 2026-02-01           # Score from specific date
  flux-score.py --format json                # JSON output
  flux-score.py --export evidence.yaml       # Export for recruiting
        """,
    )

    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Path to Claude data directory (default: ~/.claude)",
    )
    parser.add_argument("--since", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--until", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument(
        "--format",
        "-f",
        choices=["table", "json", "yaml"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument("--export", type=Path, help="Export score to file")

    args = parser.parse_args()

    # Data directory
    data_dir = args.data_dir or get_default_data_dir()
    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}", file=sys.stderr)
        print(
            "Hint: Set --data-dir or CLAUDE_DATA_DIR environment variable",
            file=sys.stderr,
        )
        sys.exit(1)

    # Parse dates
    since = datetime.strptime(args.since, "%Y-%m-%d") if args.since else None
    until = datetime.strptime(args.until, "%Y-%m-%d") if args.until else None

    # Compute score
    score = compute_flux_score(data_dir, since, until)

    # Format output
    if args.format == "json":
        output = format_json(score)
    elif args.format == "yaml":
        output = format_yaml(score)
    else:
        output = format_table(score)

    # Export or print
    if args.export:
        with open(args.export, "w") as f:
            f.write(format_yaml(score))
        print(f"Score exported to {args.export}")
    else:
        print(output)


if __name__ == "__main__":
    main()
