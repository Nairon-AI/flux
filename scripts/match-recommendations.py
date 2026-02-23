#!/usr/bin/env python3
"""
N-bench Improve - SDLC-Aware Recommendation Engine

Analyzes workflow gaps across the SDLC and recommends tools that solve
specific problems. Not spray-and-pray - only recommends what fills real gaps.

Supports user-provided context to boost friction signal detection.
"""

import json
import sys
import os
import re
import argparse
from pathlib import Path


# =============================================================================
# USER CONTEXT MAPPING
# Maps user-provided pain point descriptions to friction signals
# =============================================================================

USER_CONTEXT_PATTERNS = {
    # CSS/UI issues
    r"\b(css|styling|style|responsive|layout|flexbox|grid|tailwind)\b": [
        "css_issues",
        "ui_issues",
    ],
    r"\b(ui|frontend|visual|looks? wrong|design)\b": ["ui_issues"],
    # Memory/context issues
    r"\b(forget|forgetting|forgets|forgot|remember|repeating|told you|already said)\b": [
        "context_forgotten",
        "re_explaining",
    ],
    r"\b(context|memory|re-?explain|keeps asking)\b": [
        "context_forgotten",
        "re_explaining",
    ],
    # Documentation/API issues
    r"\b(wrong docs?|outdated|doesn'?t exist|hallucin|made up|incorrect api)\b": [
        "api_hallucination",
        "outdated_docs",
    ],
    r"\b(api changed|deprecated|old version|wrong method|wrong api)\b": [
        "api_hallucination",
        "outdated_docs",
    ],
    r"\b(method|function|property).*(not exist|doesn'?t exist|missing)\b": [
        "api_hallucination",
    ],
    # Slow/build issues
    r"\b(slow|waiting|takes? forever|build time|long builds?)\b": ["slow_builds"],
    # Reasoning issues
    r"\b(edge case|missed|shallow|think harder|wrong answer|obvious mistake)\b": [
        "shallow_answers",
        "edge_case_misses",
    ],
    r"\b(complex|reasoning|logic|algorithm)\b": ["shallow_answers"],
    # Lint/format issues
    r"\b(lint|linting|eslint|format|prettier|biome)\b": ["lint_errors"],
    # CI/pipeline issues
    r"\b(ci|pipeline|github actions?|build failed|deploy)\b": ["ci_failures"],
    r"\b(forgot to lint|push failed|pre-?commit)\b": ["ci_failures", "forgot_to_lint"],
    # Testing issues
    r"\b(test|regression|broke again|flaky|keeps? breaking)\b": [
        "regressions",
        "flaky_tests",
    ],
    # Search/navigation issues
    r"\b(can'?t find|where is|searching|lost|navigation)\b": ["search_needed"],
    # Git issues
    r"\b(git|commit|merge|rebase|history)\b": ["git_history_issues"],
    # GitHub/PR issues
    r"\b(pr|pull request|issue|github)\b": ["github_friction"],
    r"\b(ai slop|low quality pr|spam pr|drive-by pr)\b": ["pr_quality_issues"],
    r"\b(parallel|concurrent|multi-agent|worktree|context switch|switching tools|productivity)\b": [
        "parallelization_needed"
    ],
}

FRICTION_LABELS = {
    "api_hallucination": "Model used APIs that do not exist",
    "outdated_docs": "Documentation/version mismatch issues",
    "search_needed": "Research or external lookup needed",
    "context_forgotten": "Model forgot previously stated context",
    "re_explaining": "User had to repeat requirements",
    "css_issues": "Styling/CSS issues",
    "ui_issues": "UI quality/layout issues",
    "lint_errors": "Lint/format errors recurring",
    "ci_failures": "CI/pipeline failures",
    "forgot_to_lint": "Pre-commit checks missed locally",
    "shallow_answers": "Insufficient depth/quality in responses",
    "edge_case_misses": "Edge cases were missed",
    "regressions": "Bugs reappeared",
    "flaky_tests": "Intermittent test failures",
    "pr_quality_issues": "Low-quality PR noise",
    "parallelization_needed": "Parallel execution and handoff friction",
}


def parse_user_context(user_context: str) -> dict[str, int]:
    """Parse user-provided context into friction signals."""
    if not user_context:
        return {}

    signals = {}
    text = user_context.lower()

    for pattern, signal_list in USER_CONTEXT_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            for signal in signal_list:
                # User-provided context gets strong weight (3)
                signals[signal] = signals.get(signal, 0) + 3

    return signals


def simple_yaml_parse(content: str) -> dict:
    """Simple YAML parser for our recommendation format."""
    result = {}
    current_key = None
    current_list = None
    multiline_key = None
    multiline_value = []
    indent_stack = [0]
    nested_key = None
    nested_dict = {}

    lines = content.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip empty lines and comments
        if not stripped or stripped.startswith("#"):
            if multiline_key:
                multiline_value.append("")
            i += 1
            continue

        # Check for multiline string continuation
        if multiline_key:
            indent = len(line) - len(line.lstrip())
            if indent > indent_stack[-1] or stripped == "":
                multiline_value.append(stripped)
                i += 1
                continue
            else:
                result[multiline_key] = "\n".join(multiline_value).strip()
                multiline_key = None
                multiline_value = []

        # Handle nested dict (like pricing:)
        if nested_key:
            indent = len(line) - len(line.lstrip())
            if indent > 0 and ":" in stripped:
                parts = stripped.split(":", 1)
                key = parts[0].strip()
                value = parts[1].strip().strip("\"'") if len(parts) > 1 else ""
                nested_dict[key] = value
                i += 1
                continue
            else:
                result[nested_key] = nested_dict
                nested_key = None
                nested_dict = {}

        # Key-value pair
        if ":" in stripped:
            # Check if it's a list item with key
            if stripped.startswith("- "):
                if current_list is not None:
                    item_content = stripped[2:]
                    if ":" in item_content:
                        pass
                    else:
                        current_list.append(item_content.strip())
                i += 1
                continue

            parts = stripped.split(":", 1)
            key = parts[0].strip()
            value = parts[1].strip() if len(parts) > 1 else ""

            # Check for multiline indicator
            if value == "|":
                multiline_key = key
                multiline_value = []
                indent_stack.append(len(line) - len(line.lstrip()))
                i += 1
                continue

            # Check for list start or nested object
            if value == "":
                current_key = key
                # Look ahead to see if next line is a list or nested dict
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line.startswith("- "):
                        result[key] = []
                        current_list = result[key]
                    else:
                        # Nested dict
                        nested_key = key
                        nested_dict = {}
            elif value.startswith("[") and value.endswith("]"):
                # Inline list
                items = value[1:-1].split(",")
                result[key] = [
                    item.strip().strip("\"'") for item in items if item.strip()
                ]
            elif value.startswith("{"):
                result[key] = {}
            else:
                # Simple value
                result[key] = value.strip("\"'")
                if value.lower() == "true":
                    result[key] = True
                elif value.lower() == "false":
                    result[key] = False
                elif value.isdigit():
                    result[key] = int(value)

        elif stripped.startswith("- "):
            item = stripped[2:].strip().strip("\"'")
            if current_list is not None:
                current_list.append(item)

        i += 1

    # Handle final multiline or nested
    if multiline_key:
        result[multiline_key] = "\n".join(multiline_value).strip()
    if nested_key:
        result[nested_key] = nested_dict

    return result


def load_recommendations(recs_dir: str) -> list:
    """Load all recommendation YAML files."""
    recs = []
    recs_path = Path(recs_dir)

    if not recs_path.exists():
        return recs

    for yaml_file in recs_path.rglob("*.yaml"):
        if yaml_file.name in ("schema.yaml", "accounts.yaml"):
            continue
        if "pending" in str(yaml_file):
            continue

        try:
            with open(yaml_file) as f:
                content = f.read()
                rec = simple_yaml_parse(content)
                if rec and isinstance(rec, dict) and "name" in rec:
                    rec["_file"] = str(yaml_file)
                    rel_path = yaml_file.relative_to(recs_path)
                    parts = rel_path.parts
                    rec["_category_folder"] = parts[0] if parts else ""
                    rec["_subcategory"] = parts[1] if len(parts) > 2 else ""
                    recs.append(rec)
        except Exception as e:
            print(f"Warning: Failed to parse {yaml_file}: {e}", file=sys.stderr)

    return recs


def detect_sdlc_gaps(context: dict, user_context: str = "") -> dict:
    """
    Analyze context to identify gaps - FRICTION-FIRST approach.

    Only recommends tools when there's evidence of actual friction,
    not just because a tool is missing.

    Args:
        context: Environment and session analysis context
        user_context: Optional user-provided pain point description
    """
    repo = context.get("repo", {})
    installed = context.get("installed", {})
    session_insights = context.get("session_insights", {})
    friction = session_insights.get("friction_signals", {})

    # Merge user-provided context signals (these get priority)
    user_signals = parse_user_context(user_context)
    if user_signals:
        # User context boosts existing signals or adds new ones
        for signal, weight in user_signals.items():
            friction[signal] = friction.get(signal, 0) + weight
        # Enable session insights if user provided context
        if not session_insights.get("enabled"):
            session_insights["enabled"] = True
            context["session_insights"] = session_insights

    gaps = {
        "requirements": [],
        "planning": [],
        "implementation": [],
        "review": [],
        "testing": [],
        "documentation": [],
    }

    installed_mcps = [m.lower() for m in installed.get("mcps", []) or []]

    # ==========================================================================
    # FRICTION-DRIVEN GAPS (only trigger when user has actual problems)
    # ==========================================================================

    if session_insights.get("enabled"):
        # --- Research/Search Friction ---
        # "can't find solution", "is there a way to", needs web search
        if friction.get("search_needed", 0) > 0:
            if not any(m in installed_mcps for m in ["exa", "google-search"]):
                gaps["requirements"].append("no_web_search")

        # --- Design/UI Friction ---
        # "design doesn't match", "what should it look like", "mockup"
        if friction.get("design_friction", 0) > 0:
            if not any(m in installed_mcps for m in ["figma", "pencil"]):
                gaps["requirements"].append("no_design_tools")

        # --- Meeting/Stakeholder Friction ---
        # "in the meeting we said", "stakeholder wanted"
        if friction.get("meeting_context_lost", 0) > 0:
            gaps["requirements"].append("no_meeting_capture")

        # --- Task Tracking Friction ---
        # "what was I doing", "forgot to", "we said we'd"
        if friction.get("task_tracking_issues", 0) > 0:
            if not any(m in installed_mcps for m in ["linear", "github"]):
                gaps["planning"].append("no_issue_tracking")

        # --- Architecture/Diagram Friction ---
        # "draw a diagram", "how does X connect to Y"
        if friction.get("needs_diagrams", 0) > 0:
            if "excalidraw" not in installed_mcps:
                gaps["planning"].append("no_diagramming")

        # --- Complex Reasoning Friction ---
        # "think harder", "missed edge case", "shallow answer"
        if (
            friction.get("shallow_answers", 0) > 0
            or friction.get("edge_case_misses", 0) > 0
        ):
            gaps["planning"].append("needs_reasoning_model")

        # --- Documentation/API Friction ---
        # "that method doesn't exist", "API changed", hallucinated APIs
        if (
            friction.get("api_hallucination", 0) > 0
            or friction.get("outdated_docs", 0) > 0
        ):
            if "context7" not in installed_mcps:
                gaps["implementation"].append("no_doc_lookup")

        # --- Frequent Doc Lookups ---
        # "how do I use X" repeatedly
        knowledge_gaps = session_insights.get("knowledge_gaps", {})
        gap_by_type = knowledge_gaps.get("by_type", {})
        if gap_by_type.get("how_to", 0) > 2:
            gaps["implementation"].append("frequent_lookups")
            gaps["documentation"].append("frequent_lookups")

        # --- Linting/Formatting Friction ---
        # "lint error", "formatting issue" showing up repeatedly
        if friction.get("lint_errors", 0) > 2:
            if not repo.get("has_linter"):
                gaps["implementation"].append("no_linter")

        # --- Frontend/UI Model Friction ---
        # "styling is off", "CSS isn't working", "UI looks wrong"
        if friction.get("ui_issues", 0) > 0 or friction.get("css_issues", 0) > 0:
            gaps["implementation"].append("frontend_model_mismatch")

        # --- Search/Navigation Friction ---
        # "can't find the file", "where is"
        if (
            gap_by_type.get("cant_find", 0) > 0
            or gap_by_type.get("couldnt_find", 0) > 0
        ):
            gaps["implementation"].append("search_difficulties")

        # --- Git Hooks Friction ---
        # "CI failed", "forgot to lint", errors caught in CI not locally
        if friction.get("ci_failures", 0) > 2 or friction.get("forgot_to_lint", 0) > 0:
            if not repo.get("has_hooks"):
                gaps["review"].append("no_git_hooks")

        # --- PR/GitHub Friction ---
        # "create a PR", "link this to issue"
        if friction.get("github_friction", 0) > 0:
            if "github" not in installed_mcps:
                gaps["review"].append("no_github_mcp")

        # --- PR Quality Friction ---
        # "AI slop PRs", "spam pull requests"
        if friction.get("pr_quality_issues", 0) > 0:
            gaps["review"].append("needs_pr_gatekeeping")

        # --- Parallelization Friction ---
        # "run in parallel", "worktrees", "switching tools"
        if friction.get("parallelization_needed", 0) > 0:
            gaps["implementation"].append("needs_parallel_workflows")

        # --- Git History Friction ---
        # "hard to review", "can't revert", messy commits
        if friction.get("git_history_issues", 0) > 0:
            gaps["review"].append("no_ci")

        # --- Testing Friction ---
        # "this broke again", "regression", flaky tests
        if friction.get("regressions", 0) > 0 or friction.get("flaky_tests", 0) > 0:
            if not repo.get("has_tests"):
                gaps["testing"].append("no_tests")

        # --- Repeated Tool Errors ---
        tool_errors = session_insights.get("tool_errors", {})
        if tool_errors.get("total", 0) > 3:
            gaps["testing"].append("recurring_tool_errors")

        # --- Memory/Context Friction ---
        # "I already told you", "remember when", re-explaining
        if (
            friction.get("context_forgotten", 0) > 0
            or friction.get("re_explaining", 0) > 0
        ):
            if "supermemory" not in installed_mcps:
                gaps["documentation"].append("no_memory")

        # --- AGENTS.md Friction ---
        # "that's not how we do it", "wrong directory", model doesn't know project
        if friction.get("project_conventions_unknown", 0) > 0:
            if not repo.get("has_agent_docs"):
                gaps["documentation"].append("no_agents_md")

    # ==========================================================================
    # CRITICAL GAPS (always check - these are foundational)
    # Only flag if there's ANY session friction detected at all
    # ==========================================================================

    total_friction = sum(friction.get(k, 0) for k in friction.keys()) if friction else 0

    if total_friction > 0:
        # If user has friction but no AGENTS.md, that's likely contributing
        if not repo.get("has_agent_docs"):
            if "no_agents_md" not in gaps["documentation"]:
                gaps["documentation"].append("no_agents_md")

    return gaps


def is_installed_or_dismissed(rec: dict, context: dict) -> tuple[bool, str]:
    """Check if recommendation is installed, dismissed, or has alternative.
    Returns (skip, reason)."""
    name = rec.get("name", "").lower()
    category = rec.get("category", "")

    installed = context.get("installed", {})
    preferences = context.get("preferences", {})

    # Check dismissed list
    dismissed = [d.lower() for d in preferences.get("dismissed", [])]
    if name in dismissed:
        alt = preferences.get("alternatives", {}).get(name)
        if alt:
            return True, f"Using alternative: {alt}"
        return True, "Dismissed by user"

    # Check installed MCPs
    installed_mcps = [m.lower() for m in installed.get("mcps", [])]
    if category == "mcp" and name in installed_mcps:
        return True, "Already installed"

    # Check installed plugins
    installed_plugins = [p.lower() for p in installed.get("plugins", [])]
    if category == "plugin" and name in installed_plugins:
        return True, "Already installed"

    # Check installed CLI tools
    installed_cli = [c.lower() for c in installed.get("cli_tools", [])]
    if category == "cli-tool" and name in installed_cli:
        return True, "Already installed"

    # Check installed applications
    installed_apps = [a.lower() for a in installed.get("applications", [])]
    if category == "application" and name in installed_apps:
        return True, "Already installed"

    # Check for equivalent tools (e.g., has otter = skip granola)
    equivalents = {
        "granola": ["otter", "fireflies", "fathom"],
        "wispr-flow": ["superwhisper", "mac-dictation"],
        "raycast": ["alfred"],
        "oxlint": ["eslint", "biome"],
        "biome": ["eslint", "prettier"],
    }

    for equiv in equivalents.get(name, []):
        if equiv in installed_apps or equiv in installed_cli:
            return True, f"Has equivalent: {equiv}"

    return False, ""


def recommendation_fills_gap(rec: dict, gaps: dict) -> tuple[bool, str, str]:
    """Check if recommendation fills an identified gap. Returns (fills_gap, phase, reason)."""
    name = rec.get("name", "").lower()
    phase = rec.get("sdlc_phase", "")
    solves = rec.get("solves", "")
    tags = rec.get("tags", []) if isinstance(rec.get("tags"), list) else []

    phase_gaps = gaps.get(phase, [])

    # Map recommendations to gaps they fill
    # Map tools to gaps they fill. Tools can fill multiple gaps.
    # Format: tool_name -> [(phase, gap_type, reason), ...]
    gap_mappings = {
        # Requirements
        "exa": [("requirements", "no_web_search", "Research and fact-checking")],
        "figma": [("requirements", "no_design_tools", "Design-to-code workflow")],
        "pencil": [("requirements", "no_design_tools", "Design-to-code workflow")],
        "granola": [
            ("requirements", "no_meeting_capture", "Capture stakeholder context")
        ],
        # Planning
        "linear": [("planning", "no_issue_tracking", "Track work in Claude")],
        "excalidraw": [("planning", "no_diagramming", "Visualize architecture")],
        "beads": [("planning", "no_issue_tracking", "AI-native task tracking")],
        # Implementation
        "context7": [
            ("implementation", "no_doc_lookup", "Current library docs"),
            ("implementation", "frequent_lookups", "Stop searching docs repeatedly"),
        ],
        "oxlint": [("implementation", "no_linter", "Fast linting")],
        "biome": [("implementation", "no_linter", "Linting + formatting")],
        "jq": [("implementation", "knowledge_gaps", "JSON processing")],
        "fzf": [
            ("implementation", "knowledge_gaps", "Fast navigation"),
            ("implementation", "search_difficulties", "Fuzzy file search"),
        ],
        "raycast": [("implementation", "knowledge_gaps", "Quick access")],
        "remotion": [("implementation", "knowledge_gaps", "Video generation")],
        "nia": [
            ("implementation", "search_difficulties", "Index and search external repos")
        ],
        "worktree-isolation": [
            (
                "implementation",
                "needs_parallel_workflows",
                "Parallel task isolation with git worktrees",
            )
        ],
        "cli-continues": [
            (
                "implementation",
                "needs_parallel_workflows",
                "Cross-agent context handoff between tools",
            )
        ],
        "nightshift": [
            (
                "implementation",
                "needs_parallel_workflows",
                "Parallel background execution for maintenance",
            )
        ],
        "sandbox-agent": [
            (
                "implementation",
                "needs_parallel_workflows",
                "Sandboxed parallel coding agent runtime",
            )
        ],
        # Review
        "lefthook": [("review", "no_git_hooks", "Catch errors before CI")],
        "gh": [("review", "no_github_mcp", "Terminal GitHub workflows")],
        "github": [("review", "no_github_mcp", "PR/issue management")],
        "repoprompt": [("review", "no_github_mcp", "Code context for reviews")],
        "pre-commit-hooks": [("review", "no_git_hooks", "Catch errors locally")],
        "atomic-commits": [("review", "no_ci", "Better git history")],
        "anti-slop": [
            (
                "review",
                "needs_pr_gatekeeping",
                "Auto-close low-quality AI-generated pull requests",
            )
        ],
        # Testing
        "stagehand-e2e": [
            ("testing", "no_tests", "Self-healing E2E tests"),
            ("testing", "recurring_tool_errors", "Catch UI errors before they repeat"),
        ],
        "agent-browser": [("testing", "no_tests", "Browser automation test coverage")],
        "playwriter": [
            ("testing", "recurring_tool_errors", "Stateful browser debugging")
        ],
        "test-first-debugging": [("testing", "no_tests", "Regression protection")],
        # Documentation
        "agents-md-structure": [
            ("documentation", "no_agents_md", "AI knows your project")
        ],
        "claudeception": [
            ("documentation", "no_memory", "Extract and retain session learnings")
        ],
        # Model recommendations
        "frontend-models": [
            (
                "implementation",
                "frontend_model_mismatch",
                "Use opus-4.5/4.6 or gemini-3.1-pro for UI work",
            ),
        ],
        "reasoning-models": [
            (
                "planning",
                "needs_reasoning_model",
                "Use extended thinking for complex problems",
            ),
        ],
        "supermemory": [
            ("documentation", "no_memory", "Persistent memory"),
            ("documentation", "frequent_lookups", "Remember what you learned"),
        ],
        "context-management": [("documentation", "no_memory", "Session continuity")],
    }

    if name in gap_mappings:
        for mapped_phase, gap_type, reason in gap_mappings[name]:
            if gap_type in gaps.get(mapped_phase, []):
                return True, mapped_phase, reason

    return False, phase, ""


def calculate_relevance(rec: dict, context: dict, gaps: dict) -> dict | None:
    """Calculate relevance based on SDLC gaps, not arbitrary boosts."""
    name = rec.get("name", "").lower()
    category = rec.get("category", "")
    phase = rec.get("sdlc_phase", "")
    solves = rec.get("solves", "")
    pricing = rec.get("pricing", {})

    fills_gap, gap_phase, gap_reason = recommendation_fills_gap(rec, gaps)

    if not fills_gap:
        # Skip recommendations that don't fill any gap
        return None

    # Get pricing info
    pricing_model = ""
    pricing_details = ""
    if isinstance(pricing, dict):
        pricing_model = pricing.get("model", "")
        pricing_details = pricing.get("details", "")

    return {
        "name": name,
        "category": category,
        "tagline": rec.get("tagline", ""),
        "phase": gap_phase,
        "solves": solves,
        "reason": gap_reason,
        "source": rec.get("source", "manual"),
        "source_url": rec.get("source_url", ""),
        "pricing": {
            "model": pricing_model,
            "details": pricing_details,
        },
    }


def build_explain_summary(context: dict, gaps: dict) -> dict:
    """Build explainability summary for recommendations output."""
    session_insights = context.get("session_insights", {}) or {}
    friction = session_insights.get("friction_signals", {}) or {}

    top_signals = []
    if isinstance(friction, dict):
        ordered = sorted(friction.items(), key=lambda x: x[1], reverse=True)
        for name, count in ordered:
            if not isinstance(count, (int, float)) or count <= 0:
                continue
            top_signals.append(
                {
                    "signal": str(name),
                    "count": int(count),
                    "description": FRICTION_LABELS.get(str(name), "Detected friction"),
                }
            )

    return {
        "top_friction_signals": top_signals[:10],
        "gaps_detected": {k: v for k, v in gaps.items() if v},
    }


def match_recommendations(
    context: dict,
    recs_dir: str,
    filter_category: str | None = None,
    user_context: str = "",
    explain: bool = False,
) -> dict:
    """Match recommendations based on SDLC gaps.

    Args:
        context: Environment and session analysis context
        recs_dir: Path to recommendations directory
        filter_category: Optional category filter
        user_context: Optional user-provided pain point description
    """
    recommendations = load_recommendations(recs_dir)
    gaps = detect_sdlc_gaps(context, user_context)

    # Group by phase
    by_phase = {
        "requirements": [],
        "planning": [],
        "implementation": [],
        "review": [],
        "testing": [],
        "documentation": [],
    }

    skipped = []

    for rec in recommendations:
        name = rec.get("name", "unknown")
        category = rec.get("category", "")

        # Filter by category if specified
        if filter_category and category != filter_category:
            continue

        # Check if already installed, dismissed, or has equivalent
        skip, reason = is_installed_or_dismissed(rec, context)
        if skip:
            skipped.append({"name": name, "category": category, "reason": reason})
            continue

        # Calculate relevance - only include if it fills a gap
        result = calculate_relevance(rec, context, gaps)
        if result:
            phase = result["phase"]
            if phase in by_phase:
                by_phase[phase].append(result)

    # Count total recommendations
    total = sum(len(recs) for recs in by_phase.values())

    # Filter out empty phases
    by_phase = {k: v for k, v in by_phase.items() if v}

    result = {
        "total": total,
        "gaps_detected": {k: v for k, v in gaps.items() if v},
        "recommendations_by_phase": by_phase,
        "skipped": skipped,
    }

    if explain:
        result["explain"] = build_explain_summary(context, gaps)

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Match recommendations based on SDLC gaps"
    )
    parser.add_argument(
        "context_file",
        nargs="?",
        help="Path to context JSON file (reads stdin if not provided)",
    )
    parser.add_argument(
        "--user-context",
        "-u",
        default="",
        help="User-provided pain point description to boost matching",
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        help="Include explainability data (signals, gaps) in output",
    )
    args = parser.parse_args()

    # Read context from file or stdin
    if args.context_file:
        with open(args.context_file) as f:
            context = json.load(f)
    else:
        context = json.load(sys.stdin)

    # Get recommendations directory
    recs_dir = os.environ.get(
        "NBENCH_RECS_DIR", os.path.expanduser("~/.nbench/recommendations")
    )

    # Get optional category filter
    filter_category = os.environ.get("NBENCH_FILTER_CATEGORY")

    # Match recommendations with user context
    results = match_recommendations(
        context,
        recs_dir,
        filter_category,
        args.user_context,
        args.explain,
    )

    # Output JSON
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
