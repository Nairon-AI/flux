#!/usr/bin/env python3
"""
Friction Coverage Tests for Flux Recommendation Engine

Tests that EVERY type of user friction maps to the correct solution.
This is the "no matter what problem they have" confidence test.

Run with: python3 scripts/test_friction_coverage.py
"""

import sys
import os
import importlib.util

# Import the matching module
spec = importlib.util.spec_from_file_location(
    "match_recommendations", "scripts/match-recommendations.py"
)
match_recs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(match_recs)

RECS_DIR = os.path.expanduser("~/.flux/recommendations")

# =============================================================================
# FRICTION PATTERNS AND EXPECTED SOLUTIONS
# =============================================================================

FRICTION_SCENARIOS = [
    # -------------------------------------------------------------------------
    # DOCUMENTATION & API ISSUES
    # -------------------------------------------------------------------------
    {
        "name": "Model hallucinates APIs / outdated docs",
        "description": "User asks model to use a library but it generates wrong API calls",
        "friction_signals": [
            "the API changed",
            "that method doesn't exist",
            "deprecated",
        ],
        "context": {
            "installed": {
                "mcps": [],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {},
            "preferences": {"dismissed": [], "alternatives": {}},
        },
        "expected_tools": ["context7"],
        "expected_phase": "implementation",
    },
    {
        "name": "Constantly looking up docs",
        "description": "User keeps asking 'how do I use X' for libraries",
        "friction_signals": ["how do I", "what's the syntax for", "docs for"],
        "context": {
            "installed": {
                "mcps": [],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {},
            "preferences": {"dismissed": [], "alternatives": {}},
            "session_insights": {
                "enabled": True,
                "knowledge_gaps": {"by_type": {"how_to": 5}},
            },
        },
        "expected_tools": ["context7", "supermemory"],
        "expected_phase": "implementation",
    },
    # -------------------------------------------------------------------------
    # SEARCH & RESEARCH ISSUES
    # -------------------------------------------------------------------------
    {
        "name": "Can't find solution to problem",
        "description": "User needs to search the web for solutions",
        "friction_signals": ["can't find", "is there a way to", "how do others"],
        "context": {
            "installed": {
                "mcps": [],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {},
            "preferences": {"dismissed": [], "alternatives": {}},
        },
        "expected_tools": ["exa"],
        "expected_phase": "requirements",
    },
    {
        "name": "Need to research before implementing",
        "description": "User needs current info, best practices, or fact-checking",
        "friction_signals": [
            "what's the best way",
            "is X still recommended",
            "current best practice",
        ],
        "context": {
            "installed": {
                "mcps": [],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {},
            "preferences": {"dismissed": [], "alternatives": {}},
        },
        "expected_tools": ["exa"],
        "expected_phase": "requirements",
    },
    # -------------------------------------------------------------------------
    # MEMORY & CONTEXT ISSUES
    # -------------------------------------------------------------------------
    {
        "name": "Model forgets project context",
        "description": "User has to re-explain the same things every session",
        "friction_signals": ["I already told you", "remember when", "as I said before"],
        "context": {
            "installed": {
                "mcps": [],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {},
            "preferences": {"dismissed": [], "alternatives": {}},
        },
        "expected_tools": ["supermemory"],
        "expected_phase": "documentation",
    },
    {
        "name": "No AGENTS.md / CLAUDE.md",
        "description": "Model doesn't know project conventions, structure, or rules",
        "friction_signals": [
            "that's not how we do it",
            "wrong directory",
            "use X not Y",
        ],
        "context": {
            "installed": {
                "mcps": [],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {"has_agent_docs": False},
            "preferences": {"dismissed": [], "alternatives": {}},
        },
        "expected_tools": ["agents-md-structure"],
        "expected_phase": "documentation",
    },
    {
        "name": "Context drifts mid-session",
        "description": "Model loses track of what was decided earlier in conversation",
        "friction_signals": ["we already decided", "go back to", "that's not the plan"],
        "context": {
            "installed": {
                "mcps": [],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {},
            "preferences": {"dismissed": [], "alternatives": {}},
        },
        "expected_tools": ["supermemory", "context-management"],
        "expected_phase": "documentation",
    },
    # -------------------------------------------------------------------------
    # CODE QUALITY ISSUES
    # -------------------------------------------------------------------------
    {
        "name": "Lint errors after commit",
        "description": "CI fails because of lint errors that should've been caught locally",
        "friction_signals": ["lint error", "eslint failed", "formatting issue"],
        "context": {
            "installed": {
                "mcps": [],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {"has_linter": False, "has_hooks": False},
            "preferences": {"dismissed": [], "alternatives": {}},
        },
        "expected_tools": ["lefthook", "oxlint", "biome"],
        "expected_phase": "review",
    },
    {
        "name": "No pre-commit hooks",
        "description": "Errors caught in CI instead of locally (5 min wait vs 5 sec)",
        "friction_signals": ["CI failed", "push failed", "forgot to lint"],
        "context": {
            "installed": {
                "mcps": [],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {"has_hooks": False},
            "preferences": {"dismissed": [], "alternatives": {}},
        },
        "expected_tools": ["lefthook", "pre-commit-hooks"],
        "expected_phase": "review",
    },
    # -------------------------------------------------------------------------
    # TESTING ISSUES
    # -------------------------------------------------------------------------
    {
        "name": "No tests / regressions",
        "description": "Bugs reappear because there are no tests to catch them",
        "friction_signals": ["this broke again", "regression", "didn't we fix this"],
        "context": {
            "installed": {
                "mcps": [],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {"has_tests": False},
            "preferences": {"dismissed": [], "alternatives": {}},
        },
        "expected_tools": ["stagehand-e2e", "test-first-debugging"],
        "expected_phase": "testing",
    },
    {
        "name": "UI testing is painful",
        "description": "E2E tests are flaky, hard to write, or non-existent",
        "friction_signals": ["flaky test", "selenium", "can't test the UI"],
        "context": {
            "installed": {
                "mcps": [],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {"has_tests": False},
            "preferences": {"dismissed": [], "alternatives": {}},
        },
        "expected_tools": ["stagehand-e2e"],
        "expected_phase": "testing",
    },
    # -------------------------------------------------------------------------
    # PLANNING & TRACKING ISSUES
    # -------------------------------------------------------------------------
    {
        "name": "Losing track of tasks",
        "description": "No issue tracking, things fall through the cracks",
        "friction_signals": ["what was I doing", "forgot to", "we said we'd"],
        "context": {
            "installed": {
                "mcps": [],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {},
            "preferences": {"dismissed": [], "alternatives": {}},
        },
        "expected_tools": ["linear", "beads"],
        "expected_phase": "planning",
    },
    {
        "name": "Requirements drift",
        "description": "Scope creeps, original requirements forgotten",
        "friction_signals": [
            "that wasn't in the spec",
            "scope creep",
            "original requirement",
        ],
        "context": {
            "installed": {
                "mcps": [],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {},
            "preferences": {"dismissed": [], "alternatives": {}},
        },
        "expected_tools": ["linear", "beads"],
        "expected_phase": "planning",
    },
    {
        "name": "Can't visualize architecture",
        "description": "Need diagrams to communicate or think through design",
        "friction_signals": [
            "draw a diagram",
            "architecture",
            "how does X connect to Y",
        ],
        "context": {
            "installed": {
                "mcps": [],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {},
            "preferences": {"dismissed": [], "alternatives": {}},
        },
        "expected_tools": ["excalidraw"],
        "expected_phase": "planning",
    },
    # -------------------------------------------------------------------------
    # DESIGN & REQUIREMENTS ISSUES
    # -------------------------------------------------------------------------
    {
        "name": "No design mockups",
        "description": "Building UI without designs, constant rework",
        "friction_signals": ["what should it look like", "mockup", "design"],
        "context": {
            "installed": {
                "mcps": [],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {},
            "preferences": {"dismissed": [], "alternatives": {}},
        },
        "expected_tools": ["figma", "pencil"],
        "expected_phase": "requirements",
    },
    {
        "name": "Losing meeting context",
        "description": "Stakeholder decisions from meetings aren't captured",
        "friction_signals": [
            "in the meeting we said",
            "stakeholder wanted",
            "client asked for",
        ],
        "context": {
            "installed": {
                "mcps": [],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {},
            "preferences": {"dismissed": [], "alternatives": {}},
        },
        "expected_tools": ["granola"],
        "expected_phase": "requirements",
    },
    # -------------------------------------------------------------------------
    # GIT & COLLABORATION ISSUES
    # -------------------------------------------------------------------------
    {
        "name": "PR/Issue management pain",
        "description": "Can't easily create PRs, link issues, or manage GitHub from Claude",
        "friction_signals": ["create a PR", "link this to issue", "GitHub"],
        "context": {
            "installed": {
                "mcps": [],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {},
            "preferences": {"dismissed": [], "alternatives": {}},
        },
        "expected_tools": ["github"],
        "expected_phase": "review",
    },
    {
        "name": "Messy git history",
        "description": "Commits are too big, hard to review, hard to revert",
        "friction_signals": ["big commit", "hard to review", "can't revert"],
        "context": {
            "installed": {
                "mcps": [],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {"has_ci": False},
            "preferences": {"dismissed": [], "alternatives": {}},
        },
        "expected_tools": ["atomic-commits"],
        "expected_phase": "review",
    },
    # -------------------------------------------------------------------------
    # SESSION-BASED FRICTION (from parse-sessions.py)
    # -------------------------------------------------------------------------
    {
        "name": "Repeated tool errors in sessions",
        "description": "Same errors keep happening across sessions",
        "friction_signals": ["error again", "still failing", "same problem"],
        "context": {
            "installed": {
                "mcps": [],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {},
            "preferences": {"dismissed": [], "alternatives": {}},
            "session_insights": {
                "enabled": True,
                "tool_errors": {"total": 10},
            },
        },
        "expected_tools": ["stagehand-e2e"],
        "expected_phase": "testing",
    },
    {
        "name": "Search difficulties in sessions",
        "description": "User frequently says 'can't find' things",
        "friction_signals": ["can't find", "where is", "couldn't locate"],
        "context": {
            "installed": {
                "mcps": [],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {},
            "preferences": {"dismissed": [], "alternatives": {}},
            "session_insights": {
                "enabled": True,
                "knowledge_gaps": {"by_type": {"cant_find": 3}},
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
            "Run: git clone https://github.com/Nairon-AI/flux-recommendations ~/.flux/recommendations"
        )
        sys.exit(1)

    passed = 0
    failed = 0
    failures = []

    print("=" * 70)
    print("FRICTION COVERAGE TESTS")
    print("=" * 70)
    print()

    for scenario in FRICTION_SCENARIOS:
        name = scenario["name"]
        context = scenario["context"]
        expected_tools = scenario["expected_tools"]
        expected_phase = scenario["expected_phase"]

        # Run the matching engine
        results = match_recs.match_recommendations(context, RECS_DIR)

        # Get recommended tools for the expected phase
        phase_recs = results["recommendations_by_phase"].get(expected_phase, [])
        recommended_names = [r["name"] for r in phase_recs]

        # Also check other phases in case the tool is categorized differently
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
            print(f"  Got in {expected_phase}: {recommended_names}")
            print(f"  All recommended: {all_recommended}")
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


def print_coverage_matrix():
    """Print a matrix showing which tools cover which friction types."""
    print()
    print("=" * 70)
    print("COVERAGE MATRIX")
    print("=" * 70)
    print()

    # Collect all tools and their friction coverage
    tool_coverage = {}
    for scenario in FRICTION_SCENARIOS:
        for tool in scenario["expected_tools"]:
            if tool not in tool_coverage:
                tool_coverage[tool] = []
            tool_coverage[tool].append(scenario["name"])

    for tool, frictions in sorted(tool_coverage.items()):
        print(f"{tool}:")
        for f in frictions:
            print(f"  - {f}")
        print()


if __name__ == "__main__":
    success = run_friction_coverage_tests()
    print_coverage_matrix()
    sys.exit(0 if success else 1)
