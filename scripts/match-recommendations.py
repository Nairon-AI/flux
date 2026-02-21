#!/usr/bin/env python3
"""
Flux Improve - Recommendation Matching Engine

Takes context analysis and recommendations, returns ranked matches.
Uses simple YAML parsing (no external dependencies).
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

        # Key-value pair
        if ":" in stripped:
            # Check if it's a list item with key
            if stripped.startswith("- "):
                if current_list is not None:
                    # Parse the item
                    item_content = stripped[2:]
                    if ":" in item_content:
                        # It's a dict item
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

            # Check for list start
            if value == "":
                # Could be start of a list or nested object
                current_key = key
                # Look ahead to see if next line is a list
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line.startswith("- "):
                        result[key] = []
                        current_list = result[key]
            elif value.startswith("[") and value.endswith("]"):
                # Inline list
                items = value[1:-1].split(",")
                result[key] = [
                    item.strip().strip("\"'") for item in items if item.strip()
                ]
            elif value.startswith("{"):
                # Inline dict - simplified handling
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
            # List item
            item = stripped[2:].strip().strip("\"'")
            if current_list is not None:
                current_list.append(item)

        i += 1

    # Handle final multiline
    if multiline_key:
        result[multiline_key] = "\n".join(multiline_value).strip()

    return result


def load_recommendations(recs_dir: str) -> list:
    """Load all recommendation YAML files."""
    recs = []
    recs_path = Path(recs_dir)

    if not recs_path.exists():
        return recs

    for yaml_file in recs_path.rglob("*.yaml"):
        # Skip non-recommendation files
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
                    rec["_category_folder"] = yaml_file.parent.name
                    recs.append(rec)
        except Exception as e:
            print(f"Warning: Failed to parse {yaml_file}: {e}", file=sys.stderr)

    return recs


def is_installed(rec: dict, context: dict) -> bool:
    """Check if recommendation is already installed."""
    name = rec.get("name", "").lower()
    category = rec.get("category", "")

    installed_mcps = [m.lower() for m in context.get("installed", {}).get("mcps", [])]
    installed_plugins = [
        p.lower() for p in context.get("installed", {}).get("plugins", [])
    ]

    if category == "mcp" and name in installed_mcps:
        return True
    if category == "plugin" and name in installed_plugins:
        return True

    return False


def calculate_relevance(rec: dict, context: dict) -> dict:
    """Calculate relevance score and reason for a recommendation."""
    score = 50  # Base score
    reasons = []

    repo = context.get("repo", {})
    repo_type = repo.get("type", "unknown")
    frameworks = repo.get("frameworks", [])

    category = rec.get("category", "")
    tags = rec.get("tags", []) if isinstance(rec.get("tags"), list) else []
    name = rec.get("name", "")

    # Boost for matching repo type
    if repo_type == "javascript":
        js_tools = [
            "biome",
            "oxlint",
            "lefthook",
            "typescript",
            "eslint",
            "prettier",
            "bun",
        ]
        if name in js_tools or any(
            t in tags for t in ["javascript", "typescript", "node"]
        ):
            score += 20
            reasons.append(f"Matches your {repo_type} project")

    if repo_type == "python":
        py_tools = ["uv", "ruff", "pytest"]
        if name in py_tools or "python" in tags:
            score += 20
            reasons.append(f"Matches your {repo_type} project")

    # Boost for matching frameworks
    if isinstance(frameworks, list):
        for framework in frameworks:
            framework_lower = framework.lower()
            if framework_lower in [t.lower() for t in tags]:
                score += 15
                reasons.append(f"Works well with {framework}")

    # Boost for filling gaps
    if not repo.get("has_linter") and name in ["oxlint", "biome", "eslint"]:
        score += 30
        reasons.append("No linter detected")

    if not repo.get("has_formatter") and name in ["biome", "prettier"]:
        score += 25
        reasons.append("No formatter detected")

    if not repo.get("has_hooks") and name in ["lefthook", "husky", "pre-commit-hooks"]:
        score += 25
        reasons.append("No git hooks - catch errors before CI")

    if not repo.get("has_tests") and "testing" in tags:
        score += 20
        reasons.append("No tests detected")

    if not repo.get("has_agent_docs") and name == "agents-md-structure":
        score += 30
        reasons.append("No AGENTS.md found")

    # Boost for essential tools
    essential = ["jq", "fzf", "beads", "context7", "github"]
    if name in essential:
        score += 10
        reasons.append("Essential tool")

    # Boost MCPs if few installed
    installed_mcps = context.get("installed", {}).get("mcps", [])
    if category == "mcp" and len(installed_mcps) < 3:
        score += 15
        reasons.append("Expand your MCP toolkit")

    # Adjust by setup difficulty
    ratings = rec.get("ratings", {})
    if isinstance(ratings, dict):
        difficulty = ratings.get("setup_difficulty", 3)
        if isinstance(difficulty, int):
            score += (5 - difficulty) * 5

        usefulness = ratings.get("usefulness", 3)
        if isinstance(usefulness, int):
            score += usefulness * 5

    # Cap score
    score = min(100, max(0, score))

    # Determine impact tier
    if score >= 75:
        impact = "high"
    elif score >= 50:
        impact = "medium"
    else:
        impact = "low"

    return {
        "score": score,
        "impact": impact,
        "reasons": reasons if reasons else ["General productivity improvement"],
    }


def match_recommendations(
    context: dict, recs_dir: str, filter_category: str | None = None
) -> dict:
    """Match and rank recommendations based on context."""
    recommendations = load_recommendations(recs_dir)

    matched = []
    skipped = []

    for rec in recommendations:
        name = rec.get("name", "unknown")
        category = rec.get("category", "")

        # Filter by category if specified
        if filter_category and category != filter_category:
            continue

        # Check if already installed
        if is_installed(rec, context):
            skipped.append(
                {"name": name, "category": category, "reason": "Already installed"}
            )
            continue

        # Calculate relevance
        relevance = calculate_relevance(rec, context)

        matched.append(
            {
                "name": name,
                "category": category,
                "tagline": rec.get("tagline", ""),
                "score": relevance["score"],
                "impact": relevance["impact"],
                "reasons": relevance["reasons"],
            }
        )

    # Sort by score descending
    matched.sort(key=lambda x: x["score"], reverse=True)

    # Group by impact
    high_impact = [r for r in matched if r["impact"] == "high"]
    medium_impact = [r for r in matched if r["impact"] == "medium"]
    low_impact = [r for r in matched if r["impact"] == "low"]

    return {
        "total": len(matched),
        "high_impact": high_impact,
        "medium_impact": medium_impact,
        "low_impact": low_impact,
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
