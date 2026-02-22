#!/usr/bin/env python3
"""
Flux Improve - SDLC-Aware Recommendation Engine

Analyzes workflow gaps across the SDLC and recommends tools that solve
specific problems. Not spray-and-pray - only recommends what fills real gaps.
"""

import json
import sys
import os
import re
from pathlib import Path


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


def detect_sdlc_gaps(context: dict) -> dict:
    """Analyze context to identify gaps in each SDLC phase."""
    repo = context.get("repo", {})
    installed = context.get("installed", {})
    session_insights = context.get("session_insights", {})

    gaps = {
        "requirements": [],
        "planning": [],
        "implementation": [],
        "review": [],
        "testing": [],
        "documentation": [],
    }

    # Requirements phase gaps
    installed_mcps = [m.lower() for m in installed.get("mcps", [])]
    if not any(m in installed_mcps for m in ["exa", "google-search"]):
        gaps["requirements"].append("no_web_search")
    if not any(m in installed_mcps for m in ["figma", "pencil"]):
        gaps["requirements"].append("no_design_tools")
    # Meeting capture is always a potential gap (can't easily detect)
    gaps["requirements"].append("no_meeting_capture")

    # Planning phase gaps
    if not any(m in installed_mcps for m in ["linear", "github"]):
        gaps["planning"].append("no_issue_tracking")
    if not any(m in installed_mcps for m in ["excalidraw"]):
        gaps["planning"].append("no_diagramming")

    # Implementation phase gaps
    if not repo.get("has_linter"):
        gaps["implementation"].append("no_linter")
    if not repo.get("has_formatter"):
        gaps["implementation"].append("no_formatter")
    if "context7" not in installed_mcps:
        gaps["implementation"].append("no_doc_lookup")

    # Review phase gaps
    if not repo.get("has_hooks"):
        gaps["review"].append("no_git_hooks")
    if not repo.get("has_ci"):
        gaps["review"].append("no_ci")
    if "github" not in installed_mcps:
        gaps["review"].append("no_github_mcp")

    # Testing phase gaps
    if not repo.get("has_tests"):
        gaps["testing"].append("no_tests")

    # Documentation phase gaps
    if not repo.get("has_agent_docs"):
        gaps["documentation"].append("no_agents_md")
    if "supermemory" not in installed_mcps:
        gaps["documentation"].append("no_memory")

    # Session-based gaps (from parse-sessions.py output)
    if session_insights.get("enabled"):
        # Error pattern analysis
        error_patterns = session_insights.get("error_patterns", {})
        error_by_type = error_patterns.get("by_type", {})

        # Specific error type mappings
        if error_by_type.get("unknown_skill", 0) > 0:
            gaps["implementation"].append("plugin_issues")
        if error_by_type.get("file_not_found", 0) > 2:
            gaps["implementation"].append("missing_files")
        if error_by_type.get("command_not_found", 0) > 0:
            gaps["implementation"].append("missing_cli_tools")
        if error_by_type.get("timeout", 0) > 0:
            gaps["implementation"].append("slow_operations")
        if error_by_type.get("permission_denied", 0) > 0:
            gaps["implementation"].append("permission_issues")

        # Tool errors indicate need for better testing/validation
        tool_errors = session_insights.get("tool_errors", {})
        if tool_errors.get("total", 0) > 3:
            gaps["testing"].append("recurring_tool_errors")

        # Knowledge gap analysis
        knowledge_gaps = session_insights.get("knowledge_gaps", {})
        gap_by_type = knowledge_gaps.get("by_type", {})

        if gap_by_type.get("dont_know", 0) > 0 or gap_by_type.get("not_sure", 0) > 0:
            gaps["implementation"].append("knowledge_gaps")
        if (
            gap_by_type.get("cant_find", 0) > 0
            or gap_by_type.get("couldnt_find", 0) > 0
        ):
            gaps["implementation"].append("search_difficulties")
        if gap_by_type.get("how_to", 0) > 2:
            gaps["documentation"].append("frequent_lookups")

        # API errors indicate connectivity/reliability issues
        api_errors = session_insights.get("api_errors", {})
        if api_errors.get("total", 0) > 5:
            gaps["implementation"].append("api_reliability")

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
        # Review
        "lefthook": [("review", "no_git_hooks", "Catch errors before CI")],
        "github": [("review", "no_github_mcp", "PR/issue management")],
        "repoprompt": [("review", "no_github_mcp", "Code context for reviews")],
        "pre-commit-hooks": [("review", "no_git_hooks", "Catch errors locally")],
        "atomic-commits": [("review", "no_ci", "Better git history")],
        # Testing
        "stagehand-e2e": [
            ("testing", "no_tests", "Self-healing E2E tests"),
            ("testing", "recurring_tool_errors", "Catch UI errors before they repeat"),
        ],
        "test-first-debugging": [("testing", "no_tests", "Regression protection")],
        # Documentation
        "agents-md-structure": [
            ("documentation", "no_agents_md", "AI knows your project")
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
        "pricing": {
            "model": pricing_model,
            "details": pricing_details,
        },
    }


def match_recommendations(
    context: dict, recs_dir: str, filter_category: str | None = None
) -> dict:
    """Match recommendations based on SDLC gaps."""
    recommendations = load_recommendations(recs_dir)
    gaps = detect_sdlc_gaps(context)

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

    return {
        "total": total,
        "gaps_detected": {k: v for k, v in gaps.items() if v},
        "recommendations_by_phase": by_phase,
        "skipped": skipped,
    }


def main():
    # Read context from stdin or file
    if len(sys.argv) > 1:
        context_file = sys.argv[1]
        with open(context_file) as f:
            context = json.load(f)
    else:
        context = json.load(sys.stdin)

    # Get recommendations directory
    recs_dir = os.environ.get(
        "FLUX_RECS_DIR", os.path.expanduser("~/.flux/recommendations")
    )

    # Get optional category filter
    filter_category = os.environ.get("FLUX_FILTER_CATEGORY")

    # Match recommendations
    results = match_recommendations(context, recs_dir, filter_category)

    # Output JSON
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
