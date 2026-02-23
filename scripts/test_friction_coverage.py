#!/usr/bin/env python3
"""
Friction Coverage Tests for Flux Recommendation Engine

Tests that EVERY type of user friction maps to the correct solution.
This is the "no matter what problem they have" confidence test.

Now uses FRICTION-FIRST approach - recommendations only appear when
session_insights.friction_signals indicate actual problems.

Run with: python3 scripts/test_friction_coverage.py
"""

import sys
import os
import importlib.util

# Import the matching module
script_dir = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "match_recommendations", os.path.join(script_dir, "match-recommendations.py")
)
match_recs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(match_recs)

RECS_DIR = os.path.expanduser("~/.flux/recommendations")


def make_context(
    friction_signals: dict, repo: dict = None, installed_mcps: list = None
):
    """Helper to create context with proper friction signals."""
    return {
        "installed": {
            "mcps": installed_mcps or [],
            "plugins": [],
            "cli_tools": [],
            "applications": [],
        },
        "repo": repo or {},
        "preferences": {"dismissed": [], "alternatives": {}},
        "session_insights": {
            "enabled": True,
            "friction_signals": friction_signals,
            "knowledge_gaps": {"by_type": {}},
            "tool_errors": {"total": 0},
        },
    }


# =============================================================================
# FRICTION PATTERNS AND EXPECTED SOLUTIONS
# Each scenario now includes the exact friction_signals keys the engine looks for
# =============================================================================

FRICTION_SCENARIOS = [
    # -------------------------------------------------------------------------
    # DOCUMENTATION & API ISSUES
    # -------------------------------------------------------------------------
    {
        "name": "Model hallucinates APIs / outdated docs",
        "context": make_context({"api_hallucination": 3, "outdated_docs": 2}),
        "expected_tools": ["context7"],
        "expected_phase": "implementation",
    },
    {
        "name": "Constantly looking up docs (how_to)",
        "context": {
            **make_context({}),
            "session_insights": {
                "enabled": True,
                "friction_signals": {},
                "knowledge_gaps": {"by_type": {"how_to": 5}},
                "tool_errors": {"total": 0},
            },
        },
        "expected_tools": ["context7", "supermemory"],
        "expected_phase": "implementation",
    },
    # -------------------------------------------------------------------------
    # SEARCH & RESEARCH ISSUES
    # -------------------------------------------------------------------------
    {
        "name": "Can't find solution - needs web search",
        "context": make_context({"search_needed": 3}),
        "expected_tools": ["exa"],
        "expected_phase": "requirements",
    },
    # -------------------------------------------------------------------------
    # MEMORY & CONTEXT ISSUES
    # -------------------------------------------------------------------------
    {
        "name": "Model forgets project context",
        "context": make_context({"context_forgotten": 2, "re_explaining": 3}),
        "expected_tools": ["supermemory"],
        "expected_phase": "documentation",
    },
    {
        "name": "No AGENTS.md - model doesn't know project conventions",
        "context": make_context(
            {"project_conventions_unknown": 2}, repo={"has_agent_docs": False}
        ),
        "expected_tools": ["agents-md-structure"],
        "expected_phase": "documentation",
    },
    # -------------------------------------------------------------------------
    # CODE QUALITY ISSUES
    # -------------------------------------------------------------------------
    {
        "name": "Lint errors showing up repeatedly",
        "context": make_context({"lint_errors": 5}, repo={"has_linter": False}),
        "expected_tools": ["oxlint", "biome"],
        "expected_phase": "implementation",
    },
    {
        "name": "CI failures from missing pre-commit hooks",
        "context": make_context(
            {"ci_failures": 3, "forgot_to_lint": 2}, repo={"has_hooks": False}
        ),
        "expected_tools": ["lefthook", "pre-commit-hooks"],
        "expected_phase": "review",
    },
    # -------------------------------------------------------------------------
    # TESTING ISSUES
    # -------------------------------------------------------------------------
    {
        "name": "Regressions - same bugs keep coming back",
        "context": make_context({"regressions": 3}, repo={"has_tests": False}),
        "expected_tools": ["stagehand-e2e", "test-first-debugging"],
        "expected_phase": "testing",
    },
    {
        "name": "Recurring tool errors in sessions",
        "context": {
            **make_context({}),
            "session_insights": {
                "enabled": True,
                "friction_signals": {},
                "knowledge_gaps": {"by_type": {}},
                "tool_errors": {"total": 10},
            },
        },
        "expected_tools": ["stagehand-e2e"],
        "expected_phase": "testing",
    },
    # -------------------------------------------------------------------------
    # PLANNING & TRACKING ISSUES
    # -------------------------------------------------------------------------
    {
        "name": "Losing track of tasks",
        "context": make_context({"task_tracking_issues": 3}),
        "expected_tools": ["linear", "beads"],
        "expected_phase": "planning",
    },
    {
        "name": "Need architecture diagrams",
        "context": make_context({"needs_diagrams": 2}),
        "expected_tools": ["excalidraw"],
        "expected_phase": "planning",
    },
    {
        "name": "Complex reasoning - shallow answers",
        "context": make_context({"shallow_answers": 3, "edge_case_misses": 2}),
        "expected_tools": ["reasoning-models"],
        "expected_phase": "planning",
    },
    # -------------------------------------------------------------------------
    # DESIGN & REQUIREMENTS ISSUES
    # -------------------------------------------------------------------------
    {
        "name": "Design friction - UI doesn't match mockups",
        "context": make_context({"design_friction": 3}),
        "expected_tools": ["figma", "pencil"],
        "expected_phase": "requirements",
    },
    {
        "name": "Losing meeting context",
        "context": make_context({"meeting_context_lost": 2}),
        "expected_tools": ["granola"],
        "expected_phase": "requirements",
    },
    # -------------------------------------------------------------------------
    # FRONTEND/UI MODEL ISSUES
    # -------------------------------------------------------------------------
    {
        "name": "Frontend code quality issues - wrong model",
        "context": make_context({"ui_issues": 3, "css_issues": 2}),
        "expected_tools": ["frontend-models"],
        "expected_phase": "implementation",
    },
    # -------------------------------------------------------------------------
    # GIT & COLLABORATION ISSUES
    # -------------------------------------------------------------------------
    {
        "name": "GitHub PR/issue friction",
        "context": make_context({"github_friction": 3}),
        "expected_tools": ["github"],
        "expected_phase": "review",
    },
    {
        "name": "Git history issues - hard to revert",
        "context": make_context({"git_history_issues": 2}),
        "expected_tools": ["atomic-commits"],
        "expected_phase": "review",
    },
    # -------------------------------------------------------------------------
    # SEARCH/NAVIGATION FRICTION
    # -------------------------------------------------------------------------
    {
        "name": "Can't find files in codebase",
        "context": {
            **make_context({}),
            "session_insights": {
                "enabled": True,
                "friction_signals": {},
                "knowledge_gaps": {"by_type": {"cant_find": 3}},
                "tool_errors": {"total": 0},
            },
        },
        "expected_tools": ["fzf", "nia"],
        "expected_phase": "implementation",
    },
]


def run_friction_coverage_tests():
    """Run all friction coverage tests."""
    if not os.path.exists(RECS_DIR):
        print(f"ERROR: Recommendations not installed at {RECS_DIR}")
        print(
            "Run: git clone https://github.com/Nairon-AI/n-bench-recommendations ~/.flux/recommendations"
        )
        sys.exit(1)

    passed = 0
    failed = 0
    failures = []

    print("=" * 70)
    print("FRICTION COVERAGE TESTS (Friction-First Approach)")
    print("=" * 70)
    print()

    for scenario in FRICTION_SCENARIOS:
        name = scenario["name"]
        context = scenario["context"]
        expected_tools = scenario["expected_tools"]
        expected_phase = scenario["expected_phase"]

        # Run the matching engine
        results = match_recs.match_recommendations(context, RECS_DIR)

        # Get all recommended tools across all phases
        all_recommended = []
        for phase, recs in results["recommendations_by_phase"].items():
            all_recommended.extend([r["name"] for r in recs])

        # Check if at least one expected tool is recommended
        found_tools = [t for t in expected_tools if t in all_recommended]

        if found_tools:
            print(f"✓ {name}")
            print(f"  Found: {found_tools}")
            passed += 1
        else:
            print(f"✗ {name}")
            print(f"  Expected one of: {expected_tools}")
            print(f"  Got: {all_recommended}")
            failed += 1
            failures.append(
                {
                    "name": name,
                    "expected": expected_tools,
                    "got": all_recommended,
                    "gaps_detected": results["gaps_detected"],
                }
            )

        print()

    print("=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)

    if failures:
        print()
        print("FAILURE DETAILS:")
        print("-" * 70)
        for f in failures:
            print(f"\n{f['name']}:")
            print(f"  Expected: {f['expected']}")
            print(f"  Got: {f['got']}")
            print(f"  Gaps detected: {f['gaps_detected']}")

    return failed == 0


def test_no_friction_no_recommendations():
    """Test that without friction signals, nothing is recommended."""
    print()
    print("=" * 70)
    print("NO FRICTION = NO RECOMMENDATIONS TEST")
    print("=" * 70)
    print()

    context = {
        "installed": {"mcps": [], "plugins": [], "cli_tools": [], "applications": []},
        "repo": {},
        "preferences": {"dismissed": [], "alternatives": {}},
        # No session_insights = no friction detected
    }

    results = match_recs.match_recommendations(context, RECS_DIR)
    total = results["total"]

    if total == 0:
        print(f"✓ No friction signals → {total} recommendations (correct)")
        return True
    else:
        print(f"✗ No friction signals → {total} recommendations (should be 0)")
        for phase, recs in results["recommendations_by_phase"].items():
            print(f"  {phase}: {[r['name'] for r in recs]}")
        return False


def print_coverage_matrix():
    """Print a matrix showing which friction signals trigger which tools."""
    print()
    print("=" * 70)
    print("FRICTION → SOLUTION COVERAGE MATRIX")
    print("=" * 70)
    print()

    # Map friction signals to tools
    friction_to_tool = {}
    for scenario in FRICTION_SCENARIOS:
        friction_type = scenario["name"]
        for tool in scenario["expected_tools"]:
            if tool not in friction_to_tool:
                friction_to_tool[tool] = []
            friction_to_tool[tool].append(friction_type)

    for tool, frictions in sorted(friction_to_tool.items()):
        print(f"{tool}:")
        for f in frictions:
            print(f"  ← {f}")
        print()


if __name__ == "__main__":
    success1 = run_friction_coverage_tests()
    success2 = test_no_friction_no_recommendations()
    print_coverage_matrix()
    sys.exit(0 if (success1 and success2) else 1)
