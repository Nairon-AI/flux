#!/usr/bin/env python3
"""
End-to-End Tests for N-bench Improve Pipeline

Tests the full flow:
1. parse-sessions.py extracts friction signals from session data
2. match-recommendations.py maps friction to solutions

Run with: python3 scripts/test_e2e.py
"""

import json
import os
import sys
import tempfile
import importlib.util
from pathlib import Path

script_dir = Path(__file__).parent

# Import parse-sessions module
spec = importlib.util.spec_from_file_location(
    "parse_sessions", script_dir / "parse-sessions.py"
)
parse_sessions = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parse_sessions)

# Import match-recommendations module
spec = importlib.util.spec_from_file_location(
    "match_recommendations", script_dir / "match-recommendations.py"
)
match_recs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(match_recs)

RECS_DIR = os.path.expanduser("~/.nbench/recommendations")


def test_friction_pattern_detection():
    """Test that FRICTION_PATTERNS correctly identify friction in text."""
    test_cases = [
        # (text, expected_signals)
        (
            "that method does not exist on the object",
            ["api_hallucination"],
        ),
        (
            "Property 'foo' does not exist on type 'Bar'",
            ["api_hallucination"],
        ),
        (
            "the docs seem outdated, this API changed",
            ["outdated_docs"],
        ),
        (
            "is there a way to do this faster?",
            ["search_needed"],
        ),
        (
            "I already told you about that requirement",
            ["context_forgotten"],
        ),
        (
            "as I said before, we need to handle errors",
            ["re_explaining"],
        ),
        (
            "the CSS isn't working on mobile",
            ["css_issues"],
        ),
        (
            "the UI looks broken on Safari",
            ["ui_issues"],
        ),
        (
            "think harder about the edge cases",
            ["shallow_answers"],
        ),
        (
            "you missed the edge case when input is empty",
            ["edge_case_misses"],
        ),
        (
            "there's a linting error on line 42",
            ["lint_errors"],
        ),
        (
            "CI failed again because of formatting",
            ["ci_failures"],
        ),
        (
            "forgot to lint before pushing",
            ["forgot_to_lint"],
        ),
        (
            "what was I working on yesterday?",
            ["task_tracking_issues"],
        ),
        (
            "this broke again, we fixed it last week",
            ["regressions"],
        ),
        (
            "the tests are flaky on CI",
            ["flaky_tests"],
        ),
        (
            "create a PR for this feature",
            ["github_friction"],
        ),
        (
            "the design doesn't match the mockup",
            ["design_friction"],
        ),
        (
            "in the meeting we decided to use Redis",
            ["meeting_context_lost"],
        ),
        (
            "that's not how we do things in this project",
            ["project_conventions_unknown"],
        ),
        (
            "draw a diagram of the architecture",
            ["needs_diagrams"],
        ),
    ]

    passed = 0
    failed = 0

    print("=" * 70)
    print("USER FRICTION PATTERN TESTS")
    print("=" * 70)
    print()

    for text, expected in test_cases:
        matches = parse_sessions.check_patterns(text, parse_sessions.FRICTION_PATTERNS)
        found_signals = [m[0] for m in matches]

        all_found = all(s in found_signals for s in expected)
        if all_found:
            print(f"✓ '{text[:50]}...'")
            print(f"  Found: {found_signals}")
            passed += 1
        else:
            print(f"✗ '{text[:50]}...'")
            print(f"  Expected: {expected}")
            print(f"  Found: {found_signals}")
            failed += 1

    return passed, failed


def test_tool_output_friction():
    """Test detection of friction from tool outputs (compiler errors, etc.)."""
    test_cases = [
        # TypeScript errors
        (
            "error TS2339: Property 'foo' does not exist on type 'Bar'",
            ["api_hallucination"],
        ),
        (
            "Module '\"@acme/sdk\"' has no exported member 'Widget'",
            ["api_hallucination"],
        ),
        (
            "Cannot find module 'lodash/fp'",
            ["api_hallucination"],
        ),
        (
            "Type 'string' is not assignable to type 'number'",
            ["api_hallucination"],
        ),
        (
            "TypeError: undefined is not a function",
            ["api_hallucination"],
        ),
        (
            "Cannot read properties of undefined (reading 'map')",
            ["api_hallucination"],
        ),
        # Python errors
        (
            "AttributeError: 'NoneType' object has no attribute 'items'",
            ["api_hallucination"],
        ),
        (
            "ModuleNotFoundError: No module named 'pandas'",
            ["api_hallucination"],
        ),
        # Lint errors in output
        (
            "eslint: 3 errors and 2 warnings found",
            ["lint_errors"],
        ),
        (
            "Parsing error: Unexpected token",
            ["lint_errors"],
        ),
        # Test failures
        (
            "FAIL src/utils.test.ts",
            ["regressions"],
        ),
        (
            "AssertionError: expected 5 to equal 3",
            ["regressions"],
        ),
        (
            "Expected 'hello' but received 'goodbye'",
            ["regressions"],
        ),
        # Build failures
        (
            "npm ERR! code ELIFECYCLE",
            ["ci_failures"],
        ),
        (
            "Build failed with exit code 1",
            ["ci_failures"],
        ),
    ]

    passed = 0
    failed = 0

    print()
    print("=" * 70)
    print("TOOL OUTPUT FRICTION TESTS (Agent Errors)")
    print("=" * 70)
    print()

    for text, expected in test_cases:
        matches = parse_sessions.check_patterns(
            text, parse_sessions.TOOL_OUTPUT_FRICTION
        )
        found_signals = [m[0] for m in matches]

        all_found = all(s in found_signals for s in expected)
        if all_found:
            print(f"✓ '{text[:50]}...'")
            print(f"  Found: {found_signals}")
            passed += 1
        else:
            print(f"✗ '{text[:50]}...'")
            print(f"  Expected: {expected}")
            print(f"  Found: {found_signals}")
            failed += 1

    return passed, failed


def test_agent_confusion():
    """Test detection of agent uncertainty/confusion patterns."""
    test_cases = [
        ("I apologize for the confusion", ["shallow_answers"]),
        ("That was my mistake, let me fix that", ["shallow_answers"]),
        ("I was wrong about the API", ["shallow_answers"]),
        ("Let me try a different approach", ["shallow_answers"]),
        ("That didn't work as expected", ["shallow_answers"]),
        ("I'm not sure how this library works", ["shallow_answers"]),
        ("I don't know the exact syntax", ["shallow_answers"]),
        ("I can't find that function in the docs", ["shallow_answers"]),
        ("Let me search for more information", ["search_needed"]),
    ]

    passed = 0
    failed = 0

    print()
    print("=" * 70)
    print("AGENT CONFUSION TESTS")
    print("=" * 70)
    print()

    for text, expected in test_cases:
        matches = parse_sessions.check_patterns(
            text, parse_sessions.AGENT_CONFUSION_PATTERNS
        )
        found_signals = [m[0] for m in matches]

        all_found = all(s in found_signals for s in expected)
        if all_found:
            print(f"✓ '{text[:50]}...'")
            print(f"  Found: {found_signals}")
            passed += 1
        else:
            print(f"✗ '{text[:50]}...'")
            print(f"  Expected: {expected}")
            print(f"  Found: {found_signals}")
            failed += 1

    return passed, failed


def test_full_pipeline():
    """Test the full parse-sessions → match-recommendations pipeline."""
    print()
    print("=" * 70)
    print("FULL PIPELINE TEST")
    print("=" * 70)
    print()

    # Create mock session data with friction-inducing content
    mock_session = [
        {
            "type": "user",
            "timestamp": "2026-02-22T10:00:00Z",
            "message": {"content": "that method does not exist on this object"},
        },
        {
            "type": "assistant",
            "timestamp": "2026-02-22T10:00:05Z",
            "message": {
                "content": [{"type": "text", "text": "Let me check the current API..."}]
            },
        },
        {
            "type": "user",
            "timestamp": "2026-02-22T10:01:00Z",
            "message": {"content": "the CSS isn't working properly on mobile"},
        },
    ]

    # Write to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        for entry in mock_session:
            f.write(json.dumps(entry) + "\n")
        temp_path = Path(f.name)

    try:
        # Parse the session
        result = parse_sessions.analyze_session(temp_path)

        print("Session analysis result:")
        print(f"  Messages: {result['messages']}")
        print(f"  Friction signals: {result['friction_signals']}")

        # Check friction signals were detected
        friction = result["friction_signals"]
        expected_signals = ["api_hallucination", "css_issues"]

        all_detected = all(friction.get(s, 0) > 0 for s in expected_signals)

        if all_detected:
            print(f"✓ All expected friction signals detected")
        else:
            print(f"✗ Missing friction signals")
            print(f"  Expected: {expected_signals}")
            print(f"  Got: {friction}")
            return False

        # Now test full pipeline with match-recommendations
        context = {
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
                "friction_signals": friction,
                "knowledge_gaps": {"by_type": {}},
                "tool_errors": {"total": 0},
            },
        }

        results = match_recs.match_recommendations(context, RECS_DIR)

        print()
        print("Match results:")
        print(f"  Total recommendations: {results['total']}")
        print(f"  Gaps detected: {results['gaps_detected']}")

        # Should recommend context7 for api_hallucination/outdated_docs
        # Should recommend frontend-models for css_issues
        all_recs = []
        for phase_recs in results["recommendations_by_phase"].values():
            all_recs.extend([r["name"] for r in phase_recs])

        print(f"  Recommendations: {all_recs}")

        if "context7" in all_recs and "frontend-models" in all_recs:
            print()
            print("✓ Full pipeline working correctly!")
            return True
        else:
            print()
            print("✗ Missing expected recommendations")
            print(f"  Expected: context7, frontend-models")
            print(f"  Got: {all_recs}")
            return False

    finally:
        temp_path.unlink()


def test_agent_tool_friction_pipeline():
    """Test that agent errors in tool outputs are detected."""
    print()
    print("=" * 70)
    print("AGENT TOOL ERRORS PIPELINE TEST")
    print("=" * 70)
    print()

    # Mock session where agent makes a mistake (TypeScript error in tool output)
    mock_session = [
        {
            "type": "assistant",
            "timestamp": "2026-02-22T10:00:00Z",
            "message": {
                "content": [{"type": "tool_use", "name": "bash", "id": "tool_1"}]
            },
        },
        {
            "type": "user",
            "timestamp": "2026-02-22T10:00:01Z",
            "message": {
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "tool_1",
                        "content": "error TS2339: Property 'foo' does not exist on type 'Bar'\nexit code 1",
                    }
                ]
            },
        },
        {
            "type": "assistant",
            "timestamp": "2026-02-22T10:00:05Z",
            "message": {
                "content": [
                    {"type": "text", "text": "I apologize, let me fix that error."}
                ]
            },
        },
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        for entry in mock_session:
            f.write(json.dumps(entry) + "\n")
        temp_path = Path(f.name)

    try:
        result = parse_sessions.analyze_session(temp_path)
        friction = result["friction_signals"]

        print(f"Detected friction: {friction}")

        # Should detect api_hallucination from TypeScript error
        # Should detect shallow_answers from "I apologize"
        expected = ["api_hallucination", "shallow_answers"]
        detected = [s for s in expected if friction.get(s, 0) > 0]

        if len(detected) == len(expected):
            print(f"✓ Agent errors detected: {detected}")
            return True
        else:
            print(
                f"✗ Missing signals. Expected: {expected}, Got: {list(friction.keys())}"
            )
            return False

    finally:
        temp_path.unlink()


def test_user_context_parsing():
    """Test that user-provided context is correctly parsed into friction signals."""
    test_cases = [
        # (user_context, expected_signals)
        ("fighting CSS and styling issues", ["css_issues", "ui_issues"]),
        ("keeps forgetting what I told it", ["context_forgotten", "re_explaining"]),
        ("wrong API docs, methods don't exist", ["api_hallucination", "outdated_docs"]),
        ("slow builds taking forever", ["slow_builds"]),
        ("missed edge cases, shallow answers", ["shallow_answers", "edge_case_misses"]),
        ("lint errors everywhere", ["lint_errors"]),
        ("CI keeps failing", ["ci_failures"]),
        ("tests are flaky, regressions", ["regressions", "flaky_tests"]),
        ("can't find anything", ["search_needed"]),
        ("", {}),  # Empty context should return empty
    ]

    passed = 0
    failed = 0

    print()
    print("=" * 70)
    print("USER CONTEXT PARSING TESTS")
    print("=" * 70)
    print()

    for user_context, expected in test_cases:
        signals = match_recs.parse_user_context(user_context)

        if isinstance(expected, dict):
            # Empty case
            if signals == expected:
                print(f"✓ Empty context returns empty signals")
                passed += 1
            else:
                print(f"✗ Empty context should return empty, got: {signals}")
                failed += 1
        else:
            all_found = all(s in signals for s in expected)
            if all_found:
                print(f"✓ '{user_context[:40]}...'")
                print(f"  Found signals: {list(signals.keys())}")
                passed += 1
            else:
                print(f"✗ '{user_context[:40]}...'")
                print(f"  Expected: {expected}")
                print(f"  Found: {list(signals.keys())}")
                failed += 1

    return passed, failed


def test_user_context_integration():
    """Test that user context boosts recommendations correctly."""
    print()
    print("=" * 70)
    print("USER CONTEXT INTEGRATION TEST")
    print("=" * 70)
    print()

    # Minimal context - no session insights
    context = {
        "installed": {"mcps": [], "plugins": [], "cli_tools": [], "applications": []},
        "repo": {},
        "preferences": {"dismissed": [], "alternatives": {}},
        "session_insights": {"enabled": False},
    }

    # Without user context - should get no recommendations (friction-first)
    results_without = match_recs.match_recommendations(context, RECS_DIR, None, "")
    print(f"Without user context: {results_without['total']} recommendations")

    # With user context - should get recommendations matching the context
    results_with = match_recs.match_recommendations(
        context.copy(), RECS_DIR, None, "CSS is killing me and keeps forgetting things"
    )
    print(f"With user context: {results_with['total']} recommendations")

    all_recs = []
    for phase_recs in results_with["recommendations_by_phase"].values():
        all_recs.extend([r["name"] for r in phase_recs])

    print(f"Recommendations: {all_recs}")

    # Should recommend frontend-models for CSS and supermemory for forgetting
    expected = ["frontend-models", "supermemory"]
    found = [r for r in expected if r in all_recs]

    if len(found) >= 1:  # At least one expected recommendation
        print(f"✓ User context triggered relevant recommendations: {found}")
        return True
    else:
        print(f"✗ Expected at least one of {expected}, got: {all_recs}")
        return False


def test_explain_and_source_output():
    """Test explain mode exposes signal summary and recommendation source."""
    print()
    print("=" * 70)
    print("EXPLAIN MODE OUTPUT TEST")
    print("=" * 70)
    print()

    context = {
        "installed": {"mcps": [], "plugins": [], "cli_tools": [], "applications": []},
        "repo": {},
        "preferences": {"dismissed": [], "alternatives": {}},
        "session_insights": {
            "enabled": True,
            "friction_signals": {"api_hallucination": 5, "lint_errors": 2},
            "knowledge_gaps": {"by_type": {}},
            "tool_errors": {"total": 0},
        },
    }

    results = match_recs.match_recommendations(context, RECS_DIR, None, "", True)

    explain = results.get("explain", {})
    top_signals = explain.get("top_friction_signals", [])

    if not top_signals:
        print("✗ Missing explain.top_friction_signals")
        return False

    if top_signals[0].get("signal") != "api_hallucination":
        print(f"✗ Expected top signal api_hallucination, got: {top_signals[0]}")
        return False

    found_source = False
    for phase_recs in results.get("recommendations_by_phase", {}).values():
        for rec in phase_recs:
            if "source" in rec:
                found_source = True
                break
        if found_source:
            break

    if not found_source:
        print("✗ No recommendation included source metadata")
        return False

    print("✓ Explain output includes signal summary and recommendation source")
    return True


def main():
    total_passed = 0
    total_failed = 0

    # User friction tests
    p, f = test_friction_pattern_detection()
    total_passed += p
    total_failed += f

    # Tool output friction tests
    p, f = test_tool_output_friction()
    total_passed += p
    total_failed += f

    # Agent confusion tests
    p, f = test_agent_confusion()
    total_passed += p
    total_failed += f

    # User context parsing tests
    p, f = test_user_context_parsing()
    total_passed += p
    total_failed += f

    # Pipeline tests (return bool)
    pipeline_results = []
    pipeline_results.append(("Full Pipeline (user friction)", test_full_pipeline()))
    pipeline_results.append(
        ("Agent Tool Errors Pipeline", test_agent_tool_friction_pipeline())
    )
    pipeline_results.append(
        ("User Context Integration", test_user_context_integration())
    )
    pipeline_results.append(("Explain Mode Output", test_explain_and_source_output()))

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Pattern tests: {total_passed} passed, {total_failed} failed")

    all_passed = total_failed == 0
    for name, passed in pipeline_results:
        status = "✓" if passed else "✗"
        print(f"{status} {name}")
        if not passed:
            all_passed = False

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
