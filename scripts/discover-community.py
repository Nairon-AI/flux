#!/usr/bin/env python3
"""
N-bench Improve - Community discovery for novel workflow optimizations.

Searches X/Twitter for recent high-signal discussions based on detected friction.
Priority order:
1) Exa API key (search Twitter/X domains)
2) TwitterAPI.io key (advanced search)
3) Return query suggestions for manual/agent MCP search

Input: context JSON from stdin (or optional file path)
Output: JSON with queries + discoveries
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path


EXA_SEARCH_API = "https://api.exa.ai/search"
TWITTER_SEARCH_API = "https://api.twitterapi.io/twitter/tweet/advanced_search"
CONFIG_PATH = Path.home() / ".nbench" / "config.json"

SIGNAL_QUERY_HINTS = {
    "api_hallucination": ["context7", "docs mcp", "api docs"],
    "outdated_docs": ["latest docs workflow", "versioned docs"],
    "css_issues": ["tailwind", "responsive css", "frontend workflow"],
    "ui_issues": ["ui polish", "design system", "agent ui"],
    "context_forgotten": ["memory mcp", "session memory", "context management"],
    "re_explaining": ["persistent context", "workflow memory"],
    "search_needed": ["research workflow", "exa mcp", "web search mcp"],
    "lint_errors": ["oxlint", "biome", "pre-commit lint"],
    "ci_failures": ["lefthook", "pre-commit hooks", "local ci checks"],
    "forgot_to_lint": ["git hooks", "pre-commit checks"],
    "regressions": ["test-first", "e2e testing", "stagehand"],
    "flaky_tests": ["test stability", "deterministic tests"],
    "shallow_answers": ["reasoning model", "extended thinking"],
    "edge_case_misses": ["edge case checklist", "testing strategy"],
}

NOISE_TERMS = {
    "the",
    "this",
    "that",
    "with",
    "from",
    "just",
    "your",
    "about",
    "agent",
    "agents",
    "coding",
}

SECRET_PATTERNS = [
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    r"https?://[^\s]+",
    r"\b(sk-[A-Za-z0-9]{10,})\b",
    r"\b(ghp_[A-Za-z0-9]{20,})\b",
    r"\b[A-Za-z0-9_-]{24,}\b",
]


def load_config() -> dict:
    """Load ~/.nbench/config.json if present."""
    if not CONFIG_PATH.exists():
        return {}
    try:
        with open(CONFIG_PATH) as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def read_context(path: str | None) -> dict:
    """Read context JSON from file or stdin."""
    if path:
        with open(path) as f:
            return json.load(f)
    return json.load(sys.stdin)


def extract_signal_counts(context: dict) -> dict[str, int]:
    """Extract friction signal counts from parsed sessions."""
    session_insights = context.get("session_insights", {}) or {}
    signals = session_insights.get("friction_signals", {}) or {}
    if not isinstance(signals, dict):
        return {}

    out = {}
    for key, value in signals.items():
        if isinstance(value, (int, float)):
            out[str(key)] = int(value)
    return out


def top_signals(signal_counts: dict[str, int], limit: int = 4) -> list[str]:
    """Return top signals by count."""
    ordered = sorted(signal_counts.items(), key=lambda x: x[1], reverse=True)
    return [name for name, count in ordered if count > 0][:limit]


def extract_keywords_from_text(text: str, limit: int = 5) -> list[str]:
    """Extract lightweight keywords from user context."""
    if not text:
        return []
    text = sanitize_user_context(text)
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9-]{2,}", text.lower())
    seen = set()
    out = []
    for word in words:
        if word in NOISE_TERMS or word in seen:
            continue
        seen.add(word)
        out.append(word)
        if len(out) >= limit:
            break
    return out


def sanitize_user_context(text: str) -> str:
    """Redact likely sensitive content before external search."""
    sanitized = text
    for pattern in SECRET_PATTERNS:
        sanitized = re.sub(pattern, " ", sanitized)
    sanitized = re.sub(r"\s+", " ", sanitized).strip()
    return sanitized


def canonicalize_url(url: str) -> str:
    """Canonicalize URLs to reduce duplicate entries."""
    try:
        parsed = urllib.parse.urlparse(url)
    except ValueError:
        return url
    host = parsed.netloc.lower().replace("www.", "")
    if host == "twitter.com":
        host = "x.com"
    path = parsed.path.rstrip("/")
    return f"https://{host}{path}"


def build_queries(
    signal_counts: dict[str, int], user_context: str, days: int, max_queries: int = 4
) -> list[dict]:
    """Build search queries from friction signals + optional user context."""
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    queries = []

    for signal in top_signals(signal_counts, limit=max_queries):
        hints = SIGNAL_QUERY_HINTS.get(signal, [])
        if not hints:
            continue
        hint_text = " OR ".join([f'"{h}"' for h in hints[:3]])
        query = (
            f'(site:x.com OR site:twitter.com) "claude code" ({hint_text}) '
            f'"ai coding" since:{since}'
        )
        queries.append({"query": query, "signals": [signal]})

    extra = extract_keywords_from_text(user_context)
    if extra:
        keyword_query = (
            f'(site:x.com OR site:twitter.com) "claude code" '
            f"({' OR '.join([f'"{k}"' for k in extra[:4]])}) since:{since}"
        )
        queries.insert(0, {"query": keyword_query, "signals": ["user_context"]})

    if not queries:
        queries = [
            {
                "query": (
                    f'(site:x.com OR site:twitter.com) "claude code" '
                    f'"workflow optimization" since:{since}'
                ),
                "signals": ["default"],
            }
        ]

    return queries[:max_queries]


def _safe_int(value) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def discovery_score(item: dict) -> int:
    """Compute engagement score for ranking."""
    likes = _safe_int(item.get("likeCount") or item.get("likes"))
    retweets = _safe_int(item.get("retweetCount") or item.get("retweets"))
    quotes = _safe_int(item.get("quoteCount") or item.get("quotes"))
    views = _safe_int(item.get("viewCount") or item.get("views"))
    return likes + (retweets * 3) + (quotes * 2) + (views // 1000)


def extract_tool_candidates(text: str, url: str = "") -> list[str]:
    """Extract likely tool names from text/url."""
    candidates = []

    for mention in re.findall(r"@([a-zA-Z0-9_]{3,})", text):
        if mention.lower() not in NOISE_TERMS:
            candidates.append(mention)

    for match in re.findall(
        r"(?:using|use|try|install|tool|mcp|skill|plugin)\s+([A-Za-z][A-Za-z0-9._\-/]{2,})",
        text,
        flags=re.IGNORECASE,
    ):
        cleaned = match.strip(".,:;()[]{}").lower()
        if cleaned not in NOISE_TERMS:
            candidates.append(match.strip(".,:;()[]{}"))

    domain_match = re.search(r"https?://(?:www\.)?([^/\s]+)", url)
    if domain_match:
        host = domain_match.group(1).lower()
        if host not in {"x.com", "twitter.com"}:
            root = host.split(".")[0]
            if root and root not in NOISE_TERMS:
                candidates.append(root)

    deduped = []
    seen = set()
    for item in candidates:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped[:5]


def _extract_tweets_from_response(payload: dict) -> list[dict]:
    """Handle TwitterAPI.io response shape differences."""
    if not isinstance(payload, dict):
        return []
    for key_path in [
        ("tweets",),
        ("data", "tweets"),
        ("data", "statuses"),
        ("result", "tweets"),
    ]:
        value = payload
        for part in key_path:
            if not isinstance(value, dict):
                value = None
                break
            value = value.get(part)
        if isinstance(value, list):
            return value
    return []


def search_twitter(
    query: str, api_key: str, query_type: str = "Top"
) -> tuple[list[dict], str | None]:
    """Search TwitterAPI.io advanced search endpoint."""
    params = urllib.parse.urlencode({"query": query, "queryType": query_type})
    url = f"{TWITTER_SEARCH_API}?{params}"
    req = urllib.request.Request(url)
    req.add_header("X-API-Key", api_key)
    req.add_header("User-Agent", "N-benchDiscover/1.0")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode())
        return _extract_tweets_from_response(payload), None
    except urllib.error.HTTPError as exc:
        return [], f"twitter_http_{exc.code}"
    except urllib.error.URLError:
        return [], "twitter_network_error"
    except TimeoutError:
        return [], "twitter_timeout"
    except json.JSONDecodeError:
        return [], "twitter_invalid_json"


def search_exa(
    query: str, api_key: str, max_results: int = 6
) -> tuple[list[dict], str | None]:
    """Search Exa for Twitter/X pages."""
    body = json.dumps(
        {
            "query": query,
            "numResults": max_results,
            "type": "auto",
            "includeDomains": ["x.com", "twitter.com"],
        }
    ).encode()

    req = urllib.request.Request(EXA_SEARCH_API, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("x-api-key", api_key)
    req.add_header("User-Agent", "N-benchDiscover/1.0")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode())
        results = payload.get("results", [])
        if isinstance(results, list):
            return results, None
        return [], "exa_invalid_shape"
    except urllib.error.HTTPError as exc:
        return [], f"exa_http_{exc.code}"
    except urllib.error.URLError:
        return [], "exa_network_error"
    except TimeoutError:
        return [], "exa_timeout"
    except json.JSONDecodeError:
        return [], "exa_invalid_json"


def _normalize_twitter_result(tweet: dict, query_meta: dict) -> dict | None:
    url = tweet.get("url")
    if not url:
        tweet_id = tweet.get("id")
        author = tweet.get("author", {}) or {}
        username = author.get("userName") or author.get("username")
        if tweet_id and username:
            url = f"https://x.com/{username}/status/{tweet_id}"

    text = (tweet.get("text") or "").strip()
    if not url or not text:
        return None

    author = tweet.get("author", {}) or {}
    author_name = author.get("userName") or author.get("username") or "unknown"
    score = discovery_score(tweet)

    return {
        "source": "twitter-api",
        "url": url,
        "title": f"Tweet by @{author_name}",
        "snippet": text[:240],
        "author": f"@{author_name}",
        "likes": _safe_int(tweet.get("likeCount")),
        "retweets": _safe_int(tweet.get("retweetCount")),
        "views": _safe_int(tweet.get("viewCount")),
        "engagement_score": score,
        "tool_candidates": extract_tool_candidates(text, url),
        "signals": query_meta.get("signals", []),
    }


def _normalize_exa_result(result: dict, query_meta: dict) -> dict | None:
    url = result.get("url")
    if not url:
        return None

    title = result.get("title") or "X/Twitter result"
    text = (result.get("text") or result.get("summary") or "").strip()
    snippet = text[:240] if text else title

    return {
        "source": "exa",
        "url": url,
        "title": title,
        "snippet": snippet,
        "author": result.get("author") or "unknown",
        "likes": 0,
        "retweets": 0,
        "views": 0,
        "engagement_score": 0,
        "tool_candidates": extract_tool_candidates(f"{title} {text}", url),
        "signals": query_meta.get("signals", []),
    }


def dedupe_and_rank(discoveries: list[dict], max_results: int) -> list[dict]:
    """Dedupe by URL and rank by engagement score."""
    by_url = {}
    for item in discoveries:
        url = item.get("url")
        if not url:
            continue
        canonical = canonicalize_url(url)
        existing = by_url.get(canonical)
        if not existing or item.get("engagement_score", 0) > existing.get(
            "engagement_score", 0
        ):
            item["url"] = canonical
            by_url[canonical] = item

    ranked = sorted(
        by_url.values(),
        key=lambda x: (x.get("engagement_score", 0), x.get("likes", 0)),
        reverse=True,
    )
    return ranked[:max_results]


def discover(context: dict, user_context: str, max_results: int, days: int) -> dict:
    """Main discovery flow."""
    config = load_config()
    exa_api_key = os.environ.get("EXA_API_KEY") or config.get("exa_api_key")
    twitter_api_key = os.environ.get("TWITTER_API_KEY") or config.get("twitter_api_key")

    installed = context.get("installed", {}) or {}
    installed_mcps = [
        str(m).lower() for m in (installed.get("mcps") or []) if m is not None
    ]
    signal_counts = extract_signal_counts(context)
    queries = build_queries(signal_counts, sanitize_user_context(user_context), days)

    discoveries = []
    source = "none"
    reason = ""
    errors = []
    attempts = []

    def collect_with_exa() -> list[dict]:
        collected = []
        if not exa_api_key:
            return collected
        for query_meta in queries:
            results, error = search_exa(
                query_meta["query"], str(exa_api_key), max_results=6
            )
            if error:
                errors.append(error)
                continue
            for result in results:
                normalized = _normalize_exa_result(result, query_meta)
                if normalized:
                    collected.append(normalized)
        return collected

    def collect_with_twitter() -> list[dict]:
        collected = []
        if not twitter_api_key:
            return collected
        for query_meta in queries:
            twitter_query = (
                query_meta["query"]
                .replace("(site:x.com OR site:twitter.com)", "")
                .strip()
            )
            twitter_query = f"{twitter_query} min_faves:20"
            tweets, error = search_twitter(twitter_query, str(twitter_api_key))
            if error:
                errors.append(error)
                continue
            for tweet in tweets:
                normalized = _normalize_twitter_result(tweet, query_meta)
                if normalized:
                    collected.append(normalized)
        return collected

    if exa_api_key:
        attempts.append("exa")
        discoveries = collect_with_exa()
        if discoveries:
            source = "exa"

    if not discoveries and twitter_api_key:
        attempts.append("twitter-api")
        discoveries = collect_with_twitter()
        if discoveries:
            source = "twitter-api"

    if not discoveries and not exa_api_key and not twitter_api_key:
        if "exa" in installed_mcps:
            source = "exa-mcp-suggested"
            reason = (
                "Exa MCP detected but no API key configured. "
                "Use the queries below with Exa MCP or add exa_api_key to ~/.nbench/config.json"
            )
        else:
            reason = (
                "No exa_api_key or twitter_api_key found in ~/.nbench/config.json. "
                "Add one key to enable optional community discovery."
            )
    elif not discoveries and attempts:
        source = "_then_".join(attempts) + "_empty"
        reason = "Search completed but returned no matching community discoveries."

    ranked = dedupe_and_rank(discoveries, max_results=max_results)

    return {
        "enabled": bool(ranked or queries),
        "source": source,
        "source_attempts": attempts,
        "queries": queries,
        "discoveries": ranked,
        "reason": reason,
        "errors": errors,
        "privacy_note": "Optional discovery sends search queries to external providers (Exa/TwitterAPI).",
        "config_path": str(CONFIG_PATH),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Discover novel community recommendations"
    )
    parser.add_argument(
        "context_file",
        nargs="?",
        help="Path to context JSON file (reads stdin if omitted)",
    )
    parser.add_argument(
        "--user-context",
        default="",
        help="Optional user-provided pain points",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=8,
        help="Max discoveries to return",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Lookback window in days",
    )
    args = parser.parse_args()

    try:
        context = read_context(args.context_file)
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"enabled": False, "source": "none", "error": str(exc)}))
        sys.exit(1)

    output = discover(context, args.user_context, args.max_results, args.days)
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
