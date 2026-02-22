#!/usr/bin/env python3
"""Unit tests for discover-community.py."""

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).parent / "discover-community.py"
SPEC = importlib.util.spec_from_file_location("discover_community", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
discover_community = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(discover_community)


def test_build_queries_from_signals():
    signals = {"css_issues": 3, "context_forgotten": 2}
    queries = discover_community.build_queries(signals, "", days=30, max_queries=3)

    assert len(queries) >= 2
    query_texts = [q["query"] for q in queries]
    assert any("tailwind" in q.lower() for q in query_texts)
    assert any("memory" in q.lower() for q in query_texts)


def test_build_queries_with_user_context_keywords():
    signals = {}
    queries = discover_community.build_queries(
        signals,
        "struggling with vite plugin compatibility",
        days=30,
        max_queries=3,
    )

    assert len(queries) >= 1
    assert "vite" in queries[0]["query"].lower()


def test_extract_tool_candidates_from_text_and_url():
    text = "Try @context7 and install supermemory for this workflow"
    url = "https://github.com/supermemoryai/supermemory"
    tools = discover_community.extract_tool_candidates(text, url)

    lowered = [t.lower() for t in tools]
    assert "context7" in lowered
    assert "supermemory" in lowered


def test_discovery_score_prefers_retweets_and_likes():
    a = {"likeCount": 50, "retweetCount": 10, "quoteCount": 0, "viewCount": 0}
    b = {"likeCount": 70, "retweetCount": 1, "quoteCount": 0, "viewCount": 0}

    assert discover_community.discovery_score(a) > discover_community.discovery_score(b)


def test_dedupe_and_rank_keeps_best_entry():
    items = [
        {
            "url": "https://x.com/a/status/1",
            "likes": 5,
            "engagement_score": 10,
        },
        {
            "url": "https://x.com/a/status/1",
            "likes": 15,
            "engagement_score": 40,
        },
        {
            "url": "https://x.com/b/status/2",
            "likes": 7,
            "engagement_score": 20,
        },
    ]

    ranked = discover_community.dedupe_and_rank(items, max_results=5)
    assert len(ranked) == 2
    assert ranked[0]["url"] == "https://x.com/a/status/1"
    assert ranked[0]["engagement_score"] == 40


def test_sanitize_user_context_redacts_sensitive_values():
    raw = "my email is test@example.com token sk-abcdefghijklmnop123456 and https://secret.url"
    sanitized = discover_community.sanitize_user_context(raw)
    assert "example.com" not in sanitized
    assert "sk-" not in sanitized
    assert "https://" not in sanitized


def test_discover_falls_back_exa_to_twitter():
    original_search_exa = discover_community.search_exa
    original_search_twitter = discover_community.search_twitter

    def fake_exa(_query, _key, max_results=6):
        return [], "exa_http_500"

    def fake_twitter(_query, _key, query_type="Top"):
        return [
            {
                "id": "1",
                "url": "https://x.com/dev/status/1",
                "text": "Use context7 for up-to-date docs",
                "likeCount": 50,
                "retweetCount": 10,
                "viewCount": 1000,
                "author": {"userName": "dev"},
            }
        ], None

    setattr(discover_community, "search_exa", fake_exa)
    setattr(discover_community, "search_twitter", fake_twitter)

    old_exa = discover_community.os.environ.get("EXA_API_KEY")
    old_twitter = discover_community.os.environ.get("TWITTER_API_KEY")
    discover_community.os.environ["EXA_API_KEY"] = "exa-key"
    discover_community.os.environ["TWITTER_API_KEY"] = "twitter-key"

    try:
        context = {"installed": {"mcps": ["exa"]}, "session_insights": {}}
        output = discover_community.discover(context, "docs are outdated", 5, 30)
        assert output["source"] == "twitter-api"
        assert len(output["discoveries"]) == 1
        assert "exa_http_500" in output["errors"]
    finally:
        setattr(discover_community, "search_exa", original_search_exa)
        setattr(discover_community, "search_twitter", original_search_twitter)
        if old_exa is None:
            discover_community.os.environ.pop("EXA_API_KEY", None)
        else:
            discover_community.os.environ["EXA_API_KEY"] = old_exa
        if old_twitter is None:
            discover_community.os.environ.pop("TWITTER_API_KEY", None)
        else:
            discover_community.os.environ["TWITTER_API_KEY"] = old_twitter


def test_discover_handles_non_string_mcps():
    context = {
        "installed": {"mcps": ["exa", None, 123]},
        "session_insights": {"friction_signals": {"search_needed": 1}},
    }
    output = discover_community.discover(context, "", 5, 30)
    assert "source" in output
    assert "queries" in output


def run_all_tests():
    test_build_queries_from_signals()
    test_build_queries_with_user_context_keywords()
    test_extract_tool_candidates_from_text_and_url()
    test_discovery_score_prefers_retweets_and_likes()
    test_dedupe_and_rank_keeps_best_entry()
    test_sanitize_user_context_redacts_sensitive_values()
    test_discover_falls_back_exa_to_twitter()
    test_discover_handles_non_string_mcps()
    print("All discover-community tests passed")


if __name__ == "__main__":
    run_all_tests()
