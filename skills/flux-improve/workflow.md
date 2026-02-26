# Flux Improve Workflow

Follow these steps in order.

## Step 1: Parse Options

Check `$ARGUMENTS` for:
- `--skip-sessions` → set `SKIP_SESSIONS=true`
- `--category=<cat>` → set `FILTER_CATEGORY=<cat>`
- `--list` → skip to Step 6 (list mode)
- `--score` → skip to Step 5 (score only mode)
- `--detect` → run detection only, show installed tools, exit
- `--preferences` → show user preferences (dismissed, alternatives), exit
- `--dismiss <name>` → dismiss a recommendation, exit
- `--alternative <rec> <alt>` → record that user has alternative, exit
- `--clear-preferences` → clear all preferences, exit
- `--sessions always` → enable always allow sessions, exit
- `--sessions ask` → disable always allow (ask each time), exit
- `--discover` → include optional community discovery from X/Twitter
- `--explain` → include detailed explainability output

Set defaults before parsing:
- `DISCOVER=false`
- If `--discover` present, set `DISCOVER=true`
- `EXPLAIN=false`
- If `--explain` present, set `EXPLAIN=true`

### Handle Utility Commands

For `--detect`:
```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-${DROID_PLUGIN_ROOT}}"
"$PLUGIN_ROOT/scripts/detect-installed.sh" | jq .
# Display formatted output and exit
```

For `--preferences`:
```bash
"$PLUGIN_ROOT/scripts/manage-preferences.sh" list
# Display and exit
```

For `--dismiss <name>`:
```bash
"$PLUGIN_ROOT/scripts/manage-preferences.sh" dismiss "$NAME"
# Confirm and exit
```

For `--alternative <rec> <alt>`:
```bash
"$PLUGIN_ROOT/scripts/manage-preferences.sh" alternative "$REC" "$ALT"
# Confirm and exit
```

## Step 2: Privacy Notice & Consent

**Always display this privacy notice first:**

```
┌─ Flux Improve ──────────────────────────────────────────────┐
│                                                             │
│ This analyzes your local environment to find workflow       │
│ improvements. By default this stays local.                  │
│ If you pass --discover, search queries are sent to          │
│ Exa/Twitter APIs (optional).                                │
│                                                             │
│ What I'll check:                                            │
│ • Repo structure (package.json, configs, directory layout)  │
│ • Installed MCPs and plugins                                │
│ • Your settings and hooks                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Session Analysis Consent

First, check if user has "always allow" enabled in preferences:

```bash
ALWAYS_ALLOW=$(jq -r '.always_allow_sessions // false' .flux/preferences.json 2>/dev/null || echo "false")
```

Note: preferences live in project-local `.flux/preferences.json`.

**If `ALWAYS_ALLOW=true`**: Set `ANALYZE_SESSIONS=true` and skip the question.

**If `SKIP_SESSIONS=true`**: Set `ANALYZE_SESSIONS=false` and skip the question.

**Otherwise**, ask for consent using `mcp_question`:

```
mcp_question({
  questions: [{
    header: "Session Analysis",
    question: "Can I also analyze recent Claude Code sessions to find pain points? This checks ~/.claude/projects/ for error patterns, repeated failures, and knowledge gaps - all processed locally.",
    options: [
      { label: "Yes, include sessions", description: "Analyze recent sessions for patterns (recommended for best results)" },
      { label: "Yes, always allow", description: "Allow and don't ask again" },
      { label: "No, skip that", description: "Only analyze repo structure and installed tools" }
    ]
  }]
})
```

- "Yes, include sessions" → set `ANALYZE_SESSIONS=true`
- "Yes, always allow" → set `ANALYZE_SESSIONS=true` AND run: `$PLUGIN_ROOT/scripts/manage-preferences.sh sessions always`
- "No, skip that" → set `ANALYZE_SESSIONS=false`

**Important**: Session analysis is opt-in. Never read session files without explicit consent.

## Step 2b: Optional User Context

**After consent, ask for optional context to improve recommendations:**

```
mcp_question({
  questions: [{
    header: "Pain Points",
    question: "Optional but powerful: Describe your frustrations in a few words.\n\nEven brief context like 'fighting CSS' or 'keeps forgetting things' dramatically improves recommendation accuracy.\n\nLeave blank to rely on automated analysis only.",
    options: [
      { label: "Skip", description: "Rely on session analysis only" }
    ]
  }]
})
```

If user types custom text (not "Skip"), save as `USER_CONTEXT`.

**Map user context to friction signals:**

Pass the user context to the matching script:
```bash
# Later in Step 8, pass context:
echo "$CONTEXT" | python3 "$PLUGIN_ROOT/scripts/match-recommendations.py" --user-context "$USER_CONTEXT"
```

The script maps common phrases to friction signals:
- "CSS", "styling", "responsive", "layout" → `css_issues`, `ui_issues`
- "forgets", "forgetting", "repeating", "told you" → `context_forgotten`, `re_explaining`
- "wrong docs", "outdated", "doesn't exist", "hallucinating" → `api_hallucination`, `outdated_docs`
- "slow", "build time", "waiting" → `slow_builds`
- "edge cases", "missed", "shallow" → `shallow_answers`, `edge_case_misses`
- "lint", "linting", "formatting" → `lint_errors`
- "CI", "pipeline", "broke" → `ci_failures`
- "test", "regression" → `regressions`
- "can't find", "searching" → `search_needed`

This dramatically improves match quality when user provides context.

## Step 3: Environment Detection

Run installed tools detection first:

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-${DROID_PLUGIN_ROOT}}"

# 1. Detect installed tools, apps, and user preferences
INSTALLED=$("$PLUGIN_ROOT/scripts/detect-installed.sh" 2>/dev/null)

# 2. Analyze repo context
REPO_CONTEXT=$("$PLUGIN_ROOT/scripts/analyze-context.sh" 2>/dev/null)
```

**Display Step 1 results:**

```
Step 1: Environment Detection

Repo: <name> (<type>, <frameworks>)
MCPs: <count> installed (<list first 5>)
Plugins: <count> installed (<list>)
CLI Tools: <count> found (<notable ones like jq, fzf, git>)

Current setup:
  Tests: <yes/no>     CI: <yes/no>
  Linter: <yes/no>    Hooks: <yes/no>
```

## Step 4: Session Analysis (if consented)

**Only run this step if `ANALYZE_SESSIONS=true`.**

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-${DROID_PLUGIN_ROOT}}"

# Run session parser for CURRENT PROJECT ONLY (uses cwd by default)
SESSION_INSIGHTS=$("$PLUGIN_ROOT/scripts/parse-sessions.py" --max-sessions 50 2>/dev/null)
```

**Display Step 2 results - ALWAYS show what was found before matching:**

```
Step 2: Session Analysis

Analyzed <N> recent sessions in this project.

Frustrations detected:
```

**If error patterns found:**
```
  Errors & Failures:
  • <error_type>: <count> occurrences
    Example: "<sample context from error_patterns.samples>"
  • <error_type>: <count> occurrences
    ...
```

**If tool errors found:**
```
  Tool Failures:
  • <total> tool errors detected
    Example: "<first sample from tool_errors.samples>"
```

**If knowledge gaps found:**
```
  Knowledge Gaps:
  • <gap_type>: <count> times
    Example: "<sample context>"
```

**Always show friction signals with descriptions (name + count + what it means):**
```
  Friction Signals:
  • api_hallucination: <count> (model used APIs that don't exist)
  • lint_errors: <count> (lint/format errors recurring)
  • context_forgotten: <count> (model forgot previously stated context)
  • shallow_answers: <count> (insufficient depth in responses)
  • css_issues: <count> (styling/CSS issues)
```

Use these labels for each signal:
- `api_hallucination` → "model used APIs that don't exist"
- `outdated_docs` → "documentation/version mismatch"
- `search_needed` → "research or lookup needed"
- `context_forgotten` → "model forgot previously stated context"
- `re_explaining` → "user had to repeat requirements"
- `css_issues` → "styling/CSS issues"
- `ui_issues` → "UI quality/layout issues"
- `lint_errors` → "lint/format errors recurring"
- `ci_failures` → "CI/pipeline failures"
- `shallow_answers` → "insufficient depth in responses"
- `edge_case_misses` → "edge cases were missed"
- `regressions` → "bugs reappeared"

**If no issues found:**
```
  No significant pain points detected in recent sessions.
```

**Show tool usage stats:**
```
  Most used tools: <top 5 tools from tool_usage>
```

This gives users visibility into what session data revealed before seeing recommendations.

## Step 5: Merge Context

Combine all analysis into single context for matching:

```bash
# Merge all context (repo + installed + sessions)
if [ "$ANALYZE_SESSIONS" = "true" ]; then
    CONTEXT=$(echo "$REPO_CONTEXT" "$INSTALLED" | jq -s --argjson sessions "$SESSION_INSIGHTS" '.[0] * .[1] * {session_insights: $sessions}')
else
    CONTEXT=$(echo "$REPO_CONTEXT" "$INSTALLED" | jq -s '.[0] * .[1] * {session_insights: {enabled: false}}')
fi
```

Context now contains:
- `repo.name`, `repo.type`, `repo.frameworks`
- `repo.has_tests`, `repo.has_ci`, `repo.has_linter`, `repo.has_formatter`, `repo.has_hooks`
- `installed.mcps`, `installed.plugins`, `installed.cli_tools`, `installed.applications`
- `preferences.dismissed`, `preferences.alternatives`
- `session_insights` (with error_patterns, tool_errors, knowledge_gaps, tool_usage)
- `os` (macos, linux, windows)

## Step 6: Fetch Recommendations

Fetch all recommendation files from the database with offline graceful handling:

```bash
# Clone/update recommendations repo (shallow)
RECS_DIR="${HOME}/.flux/recommendations"
OFFLINE_MODE=false

if [ -d "$RECS_DIR/.git" ]; then
  # Try to update, but don't fail if offline
  if ! git -C "$RECS_DIR" pull --ff-only 2>/dev/null; then
    echo "Note: Could not update recommendations (offline?). Using cached version."
    OFFLINE_MODE=true
  fi
else
  # Try to clone
  if ! git clone --depth 1 https://github.com/Nairon-AI/flux-recommendations.git "$RECS_DIR" 2>/dev/null; then
    # Check if we have a cached version from a previous install
    if [ -d "$RECS_DIR" ] && [ "$(find "$RECS_DIR" -name "*.yaml" 2>/dev/null | wc -l)" -gt 0 ]; then
      echo "Note: Could not fetch recommendations (offline?). Using cached version."
      OFFLINE_MODE=true
    else
      echo "Error: Cannot fetch recommendations and no cache exists."
      echo ""
      echo "Please connect to the internet and try again, or manually clone:"
      echo "  git clone https://github.com/Nairon-AI/flux-recommendations.git ~/.flux/recommendations"
      exit 1
    fi
  fi
fi

# Show offline warning if applicable
if [ "$OFFLINE_MODE" = "true" ]; then
  CACHE_DATE=$(stat -f "%Sm" -t "%Y-%m-%d" "$RECS_DIR" 2>/dev/null || stat -c "%y" "$RECS_DIR" 2>/dev/null | cut -d' ' -f1)
  echo "Using cached recommendations from: $CACHE_DATE"
  echo ""
fi

# List all recommendation files
find "$RECS_DIR" -name "*.yaml" -not -path "*/pending/*" -not -name "schema.yaml" -not -name "accounts.yaml"
```

Parse each YAML file and build recommendations list.

If `FILTER_CATEGORY` is set, filter to only that category.

## Step 7: Calculate Workflow Score

Calculate score based on:

| Category | Weight | Scoring |
|----------|--------|---------|
| MCPs | 25% | 0-3 MCPs = 0-75%, 4+ = 100% |
| CLI Tools | 20% | Has linter + formatter = 100% |
| Plugins | 15% | 0-2 plugins = 0-100% |
| Skills | 15% | Has 1+ relevant skill = 100% |
| Patterns | 15% | Has AGENTS.md + pre-commit = 100% |
| Testing | 10% | Has test setup = 100% |

Display:
```
Workflow Score: <X>%

Category breakdown:
• MCPs: <X>% (4 installed)
• CLI Tools: <X>% (has oxlint, missing formatter)
• Plugins: <X>% (2 installed)
• Skills: <X>% (none detected)
• Patterns: <X>% (has AGENTS.md)
• Testing: <X>% (jest configured)
```

If `--score` mode, stop here.

## Step 8: Match & Rank Recommendations

Run the matching script with context and optional user input:

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-${DROID_PLUGIN_ROOT}}"

# Include user context if provided (dramatically improves accuracy)
if [ -n "$USER_CONTEXT" ]; then
    if [ "$EXPLAIN" = "true" ]; then
        MATCHES=$(echo "$CONTEXT" | python3 "$PLUGIN_ROOT/scripts/match-recommendations.py" --user-context "$USER_CONTEXT" --explain)
    else
        MATCHES=$(echo "$CONTEXT" | python3 "$PLUGIN_ROOT/scripts/match-recommendations.py" --user-context "$USER_CONTEXT")
    fi
else
    if [ "$EXPLAIN" = "true" ]; then
        MATCHES=$(echo "$CONTEXT" | python3 "$PLUGIN_ROOT/scripts/match-recommendations.py" --explain)
    else
        MATCHES=$(echo "$CONTEXT" | python3 "$PLUGIN_ROOT/scripts/match-recommendations.py")
    fi
fi
```

The script automatically:
- **Parses user context** into friction signals (e.g., "CSS battles" → css_issues)
- Skips already-installed tools
- Boosts recommendations that fill gaps (no linter, no hooks, etc.)
- Boosts recommendations matching repo type/frameworks
- Ranks by score: high (75+), medium (50-74), low (<50)

**High relevance if:**
- Fills an identified gap (no linter → oxlint/biome)
- Matches repo type (JS project → JS tools)
- Essential tool (jq, fzf, beads, context7)
- Few MCPs installed → boost MCP recommendations

**Skip if:**
- Already installed (in context.installed.mcps/plugins)

If `--list` mode, just show all recommendations without ranking.

## Step 9: Present Recommendations

**Display Step 3 header:**

```
Step 3: Recommendations

Based on your environment and session analysis, here's what would help:
```

**Group recommendations by WHY they're recommended:**

### Session-Driven Recommendations (if any)

If recommendations came from session analysis, show them first with clear attribution:

```
Based on your session frustrations:

1. [MCP] context7
   Current library docs - always up-to-date
   Addresses: "how to" queries detected 5 times in recent sessions
   Source: manual curation
   
2. [MCP] nia  
   Index and search external repos
   Addresses: "can't find" errors detected 3 times
```

### Gap-Driven Recommendations

For recommendations based on missing setup:

```
Based on missing workflow components:

3. [CLI] oxlint
   Fast linting - 50-100x faster than ESLint
   Addresses: No linter detected in project
   Source: manual curation
   
4. [CLI] lefthook
   Git hooks manager - catch errors before CI
   Addresses: No pre-commit hooks configured
```

### Full Recommendation Display

```
┌─ High Impact ───────────────────────────────────────────────┐
│                                                             │
│ 1. [<category>] <name>                                      │
│    <tagline>                                                │
│    Why: <specific reason - link to session data OR gap>     │
│    Setup: ~<X> min | Pricing: <free/freemium/paid>          │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─ Nice to Have ──────────────────────────────────────────────┐
│                                                             │
│ 2. [<category>] <name>                                      │
│    ...                                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Select to install: [1,2,3] or 'all' or 'none'
```

## Step 9b: Optional Community Discovery (`--discover`)

If `DISCOVER=true`, run an optional live search for novel optimizations:

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-${DROID_PLUGIN_ROOT}}"

if [ -n "$USER_CONTEXT" ]; then
  DISCOVERY=$(echo "$CONTEXT" | python3 "$PLUGIN_ROOT/scripts/discover-community.py" --user-context "$USER_CONTEXT" || echo '{"enabled":false,"source":"none","discoveries":[],"queries":[],"reason":"discovery script failed"}')
else
  DISCOVERY=$(echo "$CONTEXT" | python3 "$PLUGIN_ROOT/scripts/discover-community.py" || echo '{"enabled":false,"source":"none","discoveries":[],"queries":[],"reason":"discovery script failed"}')
fi
```

Behavior:
- **Exa first**: uses `exa_api_key` (env or `~/.flux/config.json`) to search X/Twitter domains
- **Fallback**: uses `twitter_api_key` with Twitter advanced search
- **No keys**: returns query suggestions for manual search and does not block normal recommendations

Display as:

```
Community Discoveries (Experimental)

1. <title>
   Source: <exa|twitter-api>
   Why relevant: <mapped friction signals>
   Link: <url>
   Signals: <likes/retweets if available>

2. ...
```

This step is optional and additive. Curated recommendations remain the primary output.

## Step 10: Installation

For each selected recommendation:

### 8a: Create Snapshot

```bash
mkdir -p ~/.flux/snapshots
SNAPSHOT_ID=$(date +%Y%m%d-%H%M%S)
SNAPSHOT_DIR="${HOME}/.flux/snapshots/${SNAPSHOT_ID}"
mkdir -p "$SNAPSHOT_DIR"

# Backup relevant configs
cp ~/.claude/settings.json "$SNAPSHOT_DIR/" 2>/dev/null
cp .mcp.json "$SNAPSHOT_DIR/" 2>/dev/null
cp package.json "$SNAPSHOT_DIR/" 2>/dev/null
```

### 8b: Install

Based on category, use the appropriate installer:

**For MCPs:**
```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-${DROID_PLUGIN_ROOT}}"
MCP_CONFIG='{"command":"npx","args":["-y","@context7/mcp"]}'
"$PLUGIN_ROOT/scripts/install-mcp.sh" "<name>" "$MCP_CONFIG"
```

**For CLI tools:**
```bash
"$PLUGIN_ROOT/scripts/install-cli.sh" "<name>" "<install_command>" "<type>"
# e.g., install-cli.sh jq "brew install jq" brew
```

**For Plugins:**
```bash
"$PLUGIN_ROOT/scripts/install-plugin.sh" "<name>" "<repo>"
# Returns instructions for user to run in Claude Code
```

**For Skills:**
```bash
"$PLUGIN_ROOT/scripts/install-skill.sh" "<name>" "<source>" "<scope>"
# scope: user (default) or project
```

**For Workflow Patterns:**
Patterns are documentation-only. Display the install instructions for user to follow manually.

Display progress:
```
Installing: <name>

• Type: <install.type>
• Running: <command>

<command output>

✓ Configuration updated
```

### 8c: Verify

Use the verification script:

```bash
"$PLUGIN_ROOT/scripts/verify-install.sh" "<name>" "<type>" "<arg>"
```

Types:
- `command_exists` - Check command is in PATH (arg: command name)
- `config_exists` - Check config file exists (arg: file path)
- `mcp_connect` - Check MCP is in ~/.mcp.json
- `manual` - Prompt user to verify (arg: instructions)

```
Verifying...
✓ <name> installed and verified
```

### 8d: Handle Failure

If installation fails:
```
✗ <name> installation failed

Error: <error message>

[Retry] [Skip] [Rollback]
```

If rollback requested:
```bash
"$PLUGIN_ROOT/scripts/rollback.sh" "<snapshot_id>"
```

To list available snapshots:
```bash
ls ~/.flux/snapshots/
```

## Step 11: Summary

Display final summary:

```
Installation Complete

Installed:
✓ <name> (<category>) - <tagline>
✓ <name> (<category>) - <tagline>

Skipped:
- <name> (user skipped)

Failed:
✗ <name> (error: <reason>)

Workflow Score: <old>% → <new>%

Snapshot saved: ~/.flux/snapshots/<id>
To rollback: /flux:improve --rollback <id>

Run /flux:improve again anytime for new recommendations.
```

## Step 12: Update Timestamp

```bash
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > ~/.flux/last_improve
```

This is checked by other flux commands for the daily nudge.
