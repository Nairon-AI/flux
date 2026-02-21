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
│ improvements. Everything happens locally - no data leaves   │
│ your machine.                                               │
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
ALWAYS_ALLOW=$(jq -r '.always_allow_sessions // false' ~/.flux/preferences.json 2>/dev/null || echo "false")
```

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

## Step 3: Context Analysis

Run both context analysis and installed tools detection:

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-${DROID_PLUGIN_ROOT}}"

# 1. Analyze repo context
if [ "$ANALYZE_SESSIONS" = "true" ]; then
    REPO_CONTEXT=$("$PLUGIN_ROOT/scripts/analyze-context.sh" --include-sessions 2>/dev/null)
else
    REPO_CONTEXT=$("$PLUGIN_ROOT/scripts/analyze-context.sh" 2>/dev/null)
fi

# 2. Detect installed tools, apps, and user preferences
INSTALLED=$("$PLUGIN_ROOT/scripts/detect-installed.sh" 2>/dev/null)

# 3. Merge into single context object
CONTEXT=$(echo "$REPO_CONTEXT" "$INSTALLED" | jq -s '.[0] * .[1]')
```

This returns JSON with:
- `repo.name`, `repo.type`, `repo.frameworks`
- `repo.has_tests`, `repo.has_ci`, `repo.has_linter`, `repo.has_formatter`, `repo.has_hooks`
- `installed.mcps`, `installed.plugins`, `installed.cli_tools`, `installed.applications`
- `preferences.dismissed`, `preferences.alternatives`
- `session_insights` (if consented)
- `os` (macos, linux, windows)

### Session Insights (if consented)

When `ANALYZE_SESSIONS=true`, the context script automatically runs session analysis and includes `session_insights` in the output.

The session analysis looks for:
- Error messages and stack traces
- "I don't know" or "I'm not sure" patterns
- Repeated queries about the same topic
- Tool failures or retries
- Knowledge gaps (questions without good answers)

Example `session_insights` when enabled:
```json
{
  "enabled": true,
  "sessions_analyzed": 5,
  "patterns": {
    "errors": ["TypeScript errors in api/", "Test failures in auth module"],
    "knowledge_gaps": ["convex schema syntax", "drizzle migrations"],
    "repeated_queries": ["how to fix type error X"]
  }
}
```

When disabled or failed:
```json
{"enabled": false, "reason": "User declined or no sessions found"}
```

Use session insights to boost recommendations that address identified pain points.

### Display Summary

```
Environment Analysis

Repo: <name> (<type>, <frameworks>)
MCPs: <count> installed (<names>)
Plugins: <count> installed (<names>)

Setup:
• Tests: <yes/no>
• CI: <yes/no>
• Linter: <yes/no>
• Hooks: <yes/no>

Detected gaps:
• <gap 1 based on missing setup>
• <gap 2>
```

## Step 4: Fetch Recommendations

Fetch all recommendation files from the database:

```bash
# Clone/update recommendations repo (shallow)
RECS_DIR="${HOME}/.flux/recommendations"
if [ -d "$RECS_DIR/.git" ]; then
  git -C "$RECS_DIR" pull --ff-only 2>/dev/null
else
  git clone --depth 1 https://github.com/Nairon-AI/flux-recommendations.git "$RECS_DIR" 2>/dev/null
fi

# List all recommendation files
find "$RECS_DIR" -name "*.yaml" -not -path "*/pending/*" -not -name "schema.yaml" -not -name "accounts.yaml"
```

Parse each YAML file and build recommendations list.

If `FILTER_CATEGORY` is set, filter to only that category.

## Step 5: Calculate Workflow Score

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

## Step 6: Match & Rank Recommendations

Run the matching script with context:

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-${DROID_PLUGIN_ROOT}}"
MATCHES=$(echo "$CONTEXT" | python3 "$PLUGIN_ROOT/scripts/match-recommendations.py")
```

The script automatically:
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

## Step 7: Present Recommendations

Display ranked recommendations:

```
Recommended Improvements (<N> found)

┌─ High Impact ───────────────────────────────────────────────┐
│                                                             │
│ 1. [<category>] <name>                                      │
│    <tagline>                                                │
│    Why: <specific reason based on your context>             │
│    Setup: ~<X> min | Difficulty: <1-5>                      │
│                                                             │
│ 2. [<category>] <name>                                      │
│    ...                                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─ Nice to Have ──────────────────────────────────────────────┐
│                                                             │
│ 3. [<category>] <name>                                      │
│    ...                                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Select to install: [1,2,3] or 'all' or 'none'
```

## Step 8: Installation

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

## Step 9: Summary

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

## Step 10: Update Timestamp

```bash
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > ~/.flux/last_improve
```

This is checked by other flux commands for the daily nudge.
