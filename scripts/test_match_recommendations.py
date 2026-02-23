#!/usr/bin/env python3
"""
Unit tests for N-bench recommendation matching engine.

Tests that the right recommendations are matched for different user setups.
Run with: python -m pytest scripts/test_match_recommendations.py -v
"""

import pytest
import os
import sys

# Import from the same directory
sys.path.insert(0, os.path.dirname(__file__))
from importlib import import_module

# Import the module (handles the dash in filename)
match_recs = __import__("match-recommendations")

detect_sdlc_gaps = match_recs.detect_sdlc_gaps
is_installed_or_dismissed = match_recs.is_installed_or_dismissed
recommendation_fills_gap = match_recs.recommendation_fills_gap
match_recommendations = match_recs.match_recommendations


# =============================================================================
# GAP DETECTION TESTS
# =============================================================================


class TestGapDetection:
    """Test that gaps are correctly detected from user context."""

    def test_empty_setup_has_all_gaps(self):
        """User with nothing installed should have all gaps detected."""
        context = {
            "installed": {
                "mcps": [],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {},
        }
        gaps = detect_sdlc_gaps(context)

        # Should detect missing essentials
        assert "no_web_search" in gaps["requirements"]
        assert "no_design_tools" in gaps["requirements"]
        assert "no_issue_tracking" in gaps["planning"]
        assert "no_diagramming" in gaps["planning"]
        assert "no_doc_lookup" in gaps["implementation"]
        assert "no_git_hooks" in gaps["review"]
        assert "no_agents_md" in gaps["documentation"]
        assert "no_memory" in gaps["documentation"]

    def test_exa_installed_no_web_search_gap(self):
        """User with Exa should not have web search gap."""
        context = {
            "installed": {
                "mcps": ["exa"],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {},
        }
        gaps = detect_sdlc_gaps(context)
        assert "no_web_search" not in gaps["requirements"]

    def test_google_search_also_fills_web_search(self):
        """Google Search MCP should also fill web search gap."""
        context = {
            "installed": {
                "mcps": ["google-search"],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {},
        }
        gaps = detect_sdlc_gaps(context)
        assert "no_web_search" not in gaps["requirements"]

    def test_figma_fills_design_gap(self):
        """User with Figma MCP should not have design tools gap."""
        context = {
            "installed": {
                "mcps": ["figma"],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {},
        }
        gaps = detect_sdlc_gaps(context)
        assert "no_design_tools" not in gaps["requirements"]

    def test_pencil_also_fills_design_gap(self):
        """Pencil MCP should also fill design tools gap."""
        context = {
            "installed": {
                "mcps": ["pencil"],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {},
        }
        gaps = detect_sdlc_gaps(context)
        assert "no_design_tools" not in gaps["requirements"]

    def test_linear_fills_issue_tracking(self):
        """Linear MCP fills issue tracking gap."""
        context = {
            "installed": {
                "mcps": ["linear"],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {},
        }
        gaps = detect_sdlc_gaps(context)
        assert "no_issue_tracking" not in gaps["planning"]

    def test_github_also_fills_issue_tracking(self):
        """GitHub MCP also fills issue tracking gap."""
        context = {
            "installed": {
                "mcps": ["github"],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {},
        }
        gaps = detect_sdlc_gaps(context)
        assert "no_issue_tracking" not in gaps["planning"]

    def test_repo_with_linter_no_linter_gap(self):
        """Repo with linter should not have linter gap."""
        context = {
            "installed": {
                "mcps": [],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {"has_linter": True},
        }
        gaps = detect_sdlc_gaps(context)
        assert "no_linter" not in gaps["implementation"]

    def test_repo_with_hooks_no_hooks_gap(self):
        """Repo with git hooks should not have hooks gap."""
        context = {
            "installed": {
                "mcps": [],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {"has_hooks": True},
        }
        gaps = detect_sdlc_gaps(context)
        assert "no_git_hooks" not in gaps["review"]

    def test_repo_with_tests_no_tests_gap(self):
        """Repo with tests should not have tests gap."""
        context = {
            "installed": {
                "mcps": [],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {"has_tests": True},
        }
        gaps = detect_sdlc_gaps(context)
        assert "no_tests" not in gaps["testing"]

    def test_repo_with_agents_md_no_docs_gap(self):
        """Repo with AGENTS.md should not have agent docs gap."""
        context = {
            "installed": {
                "mcps": [],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {"has_agent_docs": True},
        }
        gaps = detect_sdlc_gaps(context)
        assert "no_agents_md" not in gaps["documentation"]

    def test_supermemory_fills_memory_gap(self):
        """Supermemory MCP fills memory gap."""
        context = {
            "installed": {
                "mcps": ["supermemory"],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {},
        }
        gaps = detect_sdlc_gaps(context)
        assert "no_memory" not in gaps["documentation"]

    def test_context7_fills_doc_lookup_gap(self):
        """Context7 MCP fills doc lookup gap."""
        context = {
            "installed": {
                "mcps": ["context7"],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {},
        }
        gaps = detect_sdlc_gaps(context)
        assert "no_doc_lookup" not in gaps["implementation"]


class TestSessionBasedGaps:
    """Test gap detection from session analysis insights."""

    def test_frequent_errors_trigger_testing_gap(self):
        """Many tool errors should suggest testing improvements."""
        context = {
            "installed": {
                "mcps": [],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {},
            "session_insights": {
                "enabled": True,
                "tool_errors": {"total": 5},
            },
        }
        gaps = detect_sdlc_gaps(context)
        assert "recurring_tool_errors" in gaps["testing"]

    def test_knowledge_gaps_detected(self):
        """'Don't know' phrases should trigger knowledge gap."""
        context = {
            "installed": {
                "mcps": [],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {},
            "session_insights": {
                "enabled": True,
                "knowledge_gaps": {"by_type": {"dont_know": 3}},
            },
        }
        gaps = detect_sdlc_gaps(context)
        assert "knowledge_gaps" in gaps["implementation"]

    def test_search_difficulties_detected(self):
        """'Can't find' phrases should trigger search difficulties gap."""
        context = {
            "installed": {
                "mcps": [],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {},
            "session_insights": {
                "enabled": True,
                "knowledge_gaps": {"by_type": {"cant_find": 2}},
            },
        }
        gaps = detect_sdlc_gaps(context)
        assert "search_difficulties" in gaps["implementation"]

    def test_frequent_lookups_detected(self):
        """Many 'how to' questions should trigger frequent lookups gap."""
        context = {
            "installed": {
                "mcps": [],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {},
            "session_insights": {
                "enabled": True,
                "knowledge_gaps": {"by_type": {"how_to": 5}},
            },
        }
        gaps = detect_sdlc_gaps(context)
        assert "frequent_lookups" in gaps["documentation"]


# =============================================================================
# INSTALLED/DISMISSED FILTERING TESTS
# =============================================================================


class TestInstalledOrDismissed:
    """Test filtering of already installed or dismissed recommendations."""

    def test_installed_mcp_is_skipped(self):
        """MCP that's already installed should be skipped."""
        rec = {"name": "exa", "category": "mcp"}
        context = {
            "installed": {"mcps": ["exa"]},
            "preferences": {},
        }
        skip, reason = is_installed_or_dismissed(rec, context)
        assert skip is True
        assert "Already installed" in reason

    def test_dismissed_tool_is_skipped(self):
        """Dismissed tool should be skipped."""
        rec = {"name": "figma", "category": "mcp"}
        context = {
            "installed": {"mcps": []},
            "preferences": {"dismissed": ["figma"]},
        }
        skip, reason = is_installed_or_dismissed(rec, context)
        assert skip is True
        assert "Dismissed" in reason

    def test_alternative_shows_in_reason(self):
        """If user has alternative, it should show in skip reason."""
        rec = {"name": "figma", "category": "mcp"}
        context = {
            "installed": {"mcps": []},
            "preferences": {
                "dismissed": ["figma"],
                "alternatives": {"figma": "sketch"},
            },
        }
        skip, reason = is_installed_or_dismissed(rec, context)
        assert skip is True
        assert "sketch" in reason

    def test_equivalent_tool_skips_recommendation(self):
        """Having an equivalent tool should skip the recommendation."""
        rec = {"name": "granola", "category": "application"}
        context = {
            "installed": {"mcps": [], "applications": ["otter"]},
            "preferences": {},
        }
        skip, reason = is_installed_or_dismissed(rec, context)
        assert skip is True
        assert "equivalent" in reason.lower()

    def test_raycast_skipped_if_has_alfred(self):
        """Raycast should be skipped if user has Alfred."""
        rec = {"name": "raycast", "category": "application"}
        context = {
            "installed": {"mcps": [], "applications": ["alfred"]},
            "preferences": {},
        }
        skip, reason = is_installed_or_dismissed(rec, context)
        assert skip is True
        assert "alfred" in reason.lower()

    def test_oxlint_skipped_if_has_eslint(self):
        """Oxlint should be skipped if user has ESLint."""
        rec = {"name": "oxlint", "category": "cli-tool"}
        context = {
            "installed": {"mcps": [], "cli_tools": ["eslint"]},
            "preferences": {},
        }
        skip, reason = is_installed_or_dismissed(rec, context)
        assert skip is True
        assert "eslint" in reason.lower()

    def test_case_insensitive_matching(self):
        """Matching should be case insensitive."""
        rec = {"name": "Exa", "category": "mcp"}
        context = {
            "installed": {"mcps": ["EXA"]},
            "preferences": {},
        }
        skip, reason = is_installed_or_dismissed(rec, context)
        assert skip is True


# =============================================================================
# RECOMMENDATION MATCHING TESTS
# =============================================================================


class TestRecommendationMatching:
    """Test that recommendations correctly match to gaps."""

    def test_lefthook_matches_no_hooks_gap(self):
        """Lefthook should match when no git hooks detected."""
        rec = {"name": "lefthook", "sdlc_phase": "review"}
        gaps = {"review": ["no_git_hooks"]}
        fills, phase, reason = recommendation_fills_gap(rec, gaps)
        assert fills is True
        assert phase == "review"

    def test_exa_matches_no_web_search_gap(self):
        """Exa should match when no web search detected."""
        rec = {"name": "exa", "sdlc_phase": "requirements"}
        gaps = {"requirements": ["no_web_search"]}
        fills, phase, reason = recommendation_fills_gap(rec, gaps)
        assert fills is True
        assert phase == "requirements"

    def test_supermemory_matches_no_memory_gap(self):
        """Supermemory should match when no memory tool detected."""
        rec = {"name": "supermemory", "sdlc_phase": "documentation"}
        gaps = {"documentation": ["no_memory"]}
        fills, phase, reason = recommendation_fills_gap(rec, gaps)
        assert fills is True
        assert phase == "documentation"

    def test_context7_matches_no_doc_lookup_gap(self):
        """Context7 should match when no doc lookup detected."""
        rec = {"name": "context7", "sdlc_phase": "implementation"}
        gaps = {"implementation": ["no_doc_lookup"]}
        fills, phase, reason = recommendation_fills_gap(rec, gaps)
        assert fills is True
        assert phase == "implementation"

    def test_stagehand_matches_no_tests_gap(self):
        """Stagehand E2E should match when no tests detected."""
        rec = {"name": "stagehand-e2e", "sdlc_phase": "testing"}
        gaps = {"testing": ["no_tests"]}
        fills, phase, reason = recommendation_fills_gap(rec, gaps)
        assert fills is True
        assert phase == "testing"

    def test_agents_md_matches_no_agents_md_gap(self):
        """AGENTS.md pattern should match when no agent docs detected."""
        rec = {"name": "agents-md-structure", "sdlc_phase": "documentation"}
        gaps = {"documentation": ["no_agents_md"]}
        fills, phase, reason = recommendation_fills_gap(rec, gaps)
        assert fills is True
        assert phase == "documentation"

    def test_linear_matches_no_issue_tracking_gap(self):
        """Linear should match when no issue tracking detected."""
        rec = {"name": "linear", "sdlc_phase": "planning"}
        gaps = {"planning": ["no_issue_tracking"]}
        fills, phase, reason = recommendation_fills_gap(rec, gaps)
        assert fills is True
        assert phase == "planning"

    def test_no_match_when_gap_not_present(self):
        """Recommendation should not match if its gap isn't present."""
        rec = {"name": "lefthook", "sdlc_phase": "review"}
        gaps = {"review": []}  # No hooks gap
        fills, phase, reason = recommendation_fills_gap(rec, gaps)
        assert fills is False


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestFullMatchingPipeline:
    """Integration tests for the full matching pipeline."""

    @pytest.fixture
    def recs_dir(self):
        """Get the recommendations directory."""
        return os.path.expanduser("~/.nbench/recommendations")

    def test_empty_setup_gets_recommendations(self, recs_dir):
        """User with empty setup should get multiple recommendations."""
        if not os.path.exists(recs_dir):
            pytest.skip("Recommendations not installed")

        context = {
            "installed": {
                "mcps": [],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {},
            "preferences": {"dismissed": [], "alternatives": {}},
        }
        results = match_recommendations(context, recs_dir)

        assert results["total"] > 0
        assert len(results["gaps_detected"]) > 0
        # Should have recommendations in multiple phases
        assert len(results["recommendations_by_phase"]) >= 2

    def test_well_equipped_setup_gets_fewer_recommendations(self, recs_dir):
        """User with many tools should get fewer recommendations."""
        if not os.path.exists(recs_dir):
            pytest.skip("Recommendations not installed")

        context = {
            "installed": {
                "mcps": [
                    "exa",
                    "context7",
                    "linear",
                    "github",
                    "supermemory",
                    "figma",
                    "excalidraw",
                ],
                "plugins": [],
                "cli_tools": ["lefthook", "jq", "fzf"],
                "applications": ["granola", "raycast"],
            },
            "repo": {
                "has_linter": True,
                "has_formatter": True,
                "has_hooks": True,
                "has_tests": True,
                "has_agent_docs": True,
                "has_ci": True,
            },
            "preferences": {"dismissed": [], "alternatives": {}},
        }
        results = match_recommendations(context, recs_dir)

        # Should have very few or no recommendations
        assert results["total"] < 5

    def test_dismissed_tools_not_recommended(self, recs_dir):
        """Dismissed tools should not appear in recommendations."""
        if not os.path.exists(recs_dir):
            pytest.skip("Recommendations not installed")

        context = {
            "installed": {
                "mcps": [],
                "plugins": [],
                "cli_tools": [],
                "applications": [],
            },
            "repo": {},
            "preferences": {
                "dismissed": ["exa", "lefthook", "supermemory"],
                "alternatives": {},
            },
        }
        results = match_recommendations(context, recs_dir)

        # Check dismissed tools are in skipped, not recommendations
        recommended_names = []
        for phase_recs in results["recommendations_by_phase"].values():
            recommended_names.extend([r["name"] for r in phase_recs])

        assert "exa" not in recommended_names
        assert "lefthook" not in recommended_names
        assert "supermemory" not in recommended_names

        # Should be in skipped list
        skipped_names = [s["name"] for s in results["skipped"]]
        assert "exa" in skipped_names

    def test_session_insights_influence_recommendations(self, recs_dir):
        """Session insights should influence which tools are recommended."""
        if not os.path.exists(recs_dir):
            pytest.skip("Recommendations not installed")

        # Context with frequent lookups pattern
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
                "knowledge_gaps": {"by_type": {"how_to": 10}},
            },
        }
        results = match_recommendations(context, recs_dir)

        # Should have frequent_lookups in gaps
        assert "frequent_lookups" in results["gaps_detected"].get("documentation", [])


# =============================================================================
# EDGE CASES
# =============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_context(self):
        """Empty context should not crash."""
        context = {}
        gaps = detect_sdlc_gaps(context)
        assert isinstance(gaps, dict)

    def test_missing_installed_key(self):
        """Missing installed key should not crash."""
        context = {"repo": {}}
        gaps = detect_sdlc_gaps(context)
        assert isinstance(gaps, dict)

    def test_missing_repo_key(self):
        """Missing repo key should not crash."""
        context = {"installed": {"mcps": []}}
        gaps = detect_sdlc_gaps(context)
        assert isinstance(gaps, dict)

    def test_none_values_in_context(self):
        """None values should be handled gracefully."""
        context = {
            "installed": {"mcps": None},
            "repo": None,
        }
        # Should not raise exception
        try:
            gaps = detect_sdlc_gaps(context)
        except (TypeError, AttributeError):
            pytest.fail("Should handle None values gracefully")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
