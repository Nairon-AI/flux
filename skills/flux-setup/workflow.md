# Flux Setup Workflow

Follow these steps in order. This workflow is **idempotent** - safe to re-run.

## Step 0: Resolve plugin path

The plugin root is the parent of this skill's directory. From this SKILL.md location, go up to find `scripts/` and `.claude-plugin/`.

Example: if this file is at `~/.claude/plugins/cache/.../flux/0.3.12/skills/flux-setup/workflow.md`, then plugin root is `~/.claude/plugins/cache/.../flux/0.3.12/`.

Store this as `PLUGIN_ROOT` for use in later steps.

## Step 1: Initialize .flux/

Use fluxctl init (idempotent - safe to re-run, handles upgrades):

```bash
"${PLUGIN_ROOT}/scripts/fluxctl" init --json
```

This creates/upgrades:
- `.flux/` directory structure (epics/, specs/, tasks/, memory/)
- `meta.json` with schema version
- `config.json` with defaults (merges new keys on upgrade)

## Step 2: Check existing setup

Read `.flux/meta.json` and check for `setup_version` field.

Also read plugin version from `${PLUGIN_ROOT}/.claude-plugin/plugin.json` (Claude Code) or `${PLUGIN_ROOT}/.factory-plugin/plugin.json` (Factory Droid) - check whichever exists.

**If `setup_version` exists (already set up):**
- If **same version**: tell user "Already set up with v<VERSION>. Re-run to update docs only? (y/n)"
  - If yes: skip to Step 6 (docs)
  - If no: done
- If **older version**: tell user "Updating from v<OLD> to v<NEW>" and continue

**If no `setup_version`:** continue (first-time setup)

## Step 3: Ask Installation Scope (FIRST)

**Before creating directories, ask where to install:**

Check if scope is already configured:
```bash
CURRENT_SCOPE=$("${PLUGIN_ROOT}/scripts/fluxctl" config get install.scope --json 2>/dev/null | jq -r '.value // empty')
```

If not set, use the question tool to ask:
```json
{
  "header": "Install Scope",
  "question": "Where should Flux be installed?",
  "options": [
    {"label": "Project (Recommended)", "description": "Install in .flux/ - isolated to this project, committed to git"},
    {"label": "User", "description": "Install in ~/.flux/ - shared scripts across all projects, project data stays local"},
    {"label": "Global", "description": "Install in /usr/local/flux/ - system-wide for all users (requires sudo)"}
  ]
}
```

**Set paths based on answer:**
- **Project**: `BIN_ROOT=".flux/bin"`, `CONFIG_ROOT=".flux"`
- **User**: `BIN_ROOT="$HOME/.flux/bin"`, `CONFIG_ROOT=".flux"` (scripts shared, epics/tasks local)
- **Global**: `BIN_ROOT="/usr/local/flux/bin"`, `CONFIG_ROOT=".flux"`

Persist the choice:
```bash
"${PLUGIN_ROOT}/scripts/fluxctl" config set install.scope "<project|user|global>" --json
```

## Step 4: Create directories and copy files

**IMPORTANT: Do NOT read fluxctl.py - it's too large. Just copy it.**

Based on the scope from Step 3:

**Project scope (default):**
```bash
mkdir -p .flux/bin
cp "${PLUGIN_ROOT}/scripts/fluxctl" .flux/bin/fluxctl
cp "${PLUGIN_ROOT}/scripts/fluxctl.py" .flux/bin/fluxctl.py
chmod +x .flux/bin/fluxctl
```

**User scope:**
```bash
mkdir -p ~/.flux/bin
cp "${PLUGIN_ROOT}/scripts/fluxctl" ~/.flux/bin/fluxctl
cp "${PLUGIN_ROOT}/scripts/fluxctl.py" ~/.flux/bin/fluxctl.py
chmod +x ~/.flux/bin/fluxctl
# Also create local .flux/ for project data
mkdir -p .flux
```
Note: Tell user to add `~/.flux/bin` to their PATH.

**Global scope:**
```bash
sudo mkdir -p /usr/local/flux/bin
sudo cp "${PLUGIN_ROOT}/scripts/fluxctl" /usr/local/flux/bin/fluxctl
sudo cp "${PLUGIN_ROOT}/scripts/fluxctl.py" /usr/local/flux/bin/fluxctl.py
sudo chmod +x /usr/local/flux/bin/fluxctl
# Also create local .flux/ for project data
mkdir -p .flux
```
Note: `/usr/local/flux/bin` is typically already in PATH on most systems.

Then read [templates/usage.md](templates/usage.md) and write it to `.flux/usage.md`.

## Step 4b: Install default skill (Claudeception)

Install Claudeception by default if not already present:

```bash
mkdir -p "${HOME}/.claude/skills"

if [ ! -d "${HOME}/.claude/skills/claudeception" ]; then
  git clone --depth 1 https://github.com/blader/Claudeception.git "${HOME}/.claude/skills/claudeception" 2>/dev/null || true
fi
```

If clone fails, continue setup and print this manual fallback command:

```bash
git clone https://github.com/blader/Claudeception.git ~/.claude/skills/claudeception
```

## Step 4c: Install recommended MCP servers

Install Context7 (library documentation) and Exa (web search) MCP servers if not already installed.

**Check if already installed:**

```bash
# Check for existing MCP servers
HAVE_CONTEXT7=$(claude mcp list 2>/dev/null | grep -q "context7" && echo 1 || echo 0)
HAVE_EXA=$(claude mcp list 2>/dev/null | grep -q "exa" && echo 1 || echo 0)
```

**Ask about API keys (use question tool):**

```json
{
  "header": "MCP API Keys",
  "question": "Flux installs Context7 (library docs) and Exa (web search) MCP servers. Both work without API keys, but keys unlock higher rate limits. Add API keys?",
  "options": [
    {"label": "Skip (Recommended)", "description": "Use free tier for both. You can add keys later."},
    {"label": "Add Context7 key", "description": "Get from context7.com/dashboard — higher rate limits"},
    {"label": "Add Exa key", "description": "Get from exa.ai — higher rate limits"},
    {"label": "Add both keys", "description": "Configure both Context7 and Exa API keys"}
  ]
}
```

**If user wants to add Context7 key:**

```json
{
  "header": "Context7 API Key",
  "question": "Enter your Context7 API key (from context7.com/dashboard):",
  "options": []
}
```

Store the key and use it in the installation command:

```bash
# With API key
claude mcp add context7 -s user -e CONTEXT7_API_KEY="<user_provided_key>" -- npx -y @upstash/context7-mcp 2>/dev/null || true
```

**If user wants to add Exa key:**

```json
{
  "header": "Exa API Key",
  "question": "Enter your Exa API key (from exa.ai):",
  "options": []
}
```

Store the key and use it in the installation command:

```bash
# With API key
claude mcp add exa -s user -e EXA_API_KEY="<user_provided_key>" -- npx -y exa-mcp-server 2>/dev/null || true
```

**Install without API keys (default):**

Context7 provides up-to-date, version-specific library documentation directly in prompts. Eliminates hallucinated APIs and outdated code examples.

```bash
if [ "$HAVE_CONTEXT7" = "0" ]; then
  # Remote URL version (no API key)
  claude mcp add --transport http context7 https://mcp.context7.com/mcp -s user 2>/dev/null || true
  echo "Installed: Context7 MCP (library documentation)"
fi
```

Exa provides fast, accurate web search optimized for AI. Enables real-time research during coding sessions.

```bash
if [ "$HAVE_EXA" = "0" ]; then
  # Remote URL version (no API key)
  claude mcp add --transport http exa https://mcp.exa.ai/mcp -s user 2>/dev/null || true
  echo "Installed: Exa MCP (web search)"
fi
```

If installation fails (e.g., `claude` CLI not available), continue setup and note in summary:

```
MCP servers (install manually if needed):
  claude mcp add --transport http context7 https://mcp.context7.com/mcp -s user
  claude mcp add --transport http exa https://mcp.exa.ai/mcp -s user
```

**Notes:**
- API keys are stored securely in Claude Code's MCP configuration
- Users can add/change keys later with: `claude mcp remove <name> && claude mcp add ...`
- Free tier works well for most users; keys mainly help with rate limits

## Step 5: Update meta.json

Read current `.flux/meta.json`, add/update these fields (preserve all others):

```json
{
  "setup_version": "<PLUGIN_VERSION>",
  "setup_date": "<ISO_DATE>"
}
```

## Step 6: Configuration Questions

### 6a: Detect current config and tools

Before asking questions, detect available tools and read current config:

```bash
# Detect available review backends
HAVE_RP=$(which rp-cli >/dev/null 2>&1 && echo 1 || echo 0)
HAVE_CODEX=$(which codex >/dev/null 2>&1 && echo 1 || echo 0)

# Read current config values if they exist
CURRENT_SCOPE=$("${PLUGIN_ROOT}/scripts/fluxctl" config get install.scope --json 2>/dev/null | jq -r '.value // empty')
CURRENT_BACKEND=$("${PLUGIN_ROOT}/scripts/fluxctl" config get review.backend --json 2>/dev/null | jq -r '.value // empty')
CURRENT_MEMORY=$("${PLUGIN_ROOT}/scripts/fluxctl" config get memory.enabled --json 2>/dev/null | jq -r '.value // empty')
CURRENT_PLANSYNC=$("${PLUGIN_ROOT}/scripts/fluxctl" config get planSync.enabled --json 2>/dev/null | jq -r '.value // empty')
CURRENT_CROSSEPIC=$("${PLUGIN_ROOT}/scripts/fluxctl" config get planSync.crossEpic --json 2>/dev/null | jq -r '.value // empty')
CURRENT_GITHUB_SCOUT=$("${PLUGIN_ROOT}/scripts/fluxctl" config get scouts.github --json 2>/dev/null | jq -r '.value // empty')
CURRENT_SCOUT_MODEL=$("${PLUGIN_ROOT}/scripts/fluxctl" config get scouts.model --json 2>/dev/null | jq -r '.value // empty')
```

Store detection results for use in questions. When showing options, indicate current value if set (e.g., "(current)" after the matching option label).

### 6b: Check docs status

Read the template from [templates/claude-md-snippet.md](templates/claude-md-snippet.md).

For each of CLAUDE.md and AGENTS.md:
1. Check if file exists
2. If exists, check if `<!-- BEGIN FLUX -->` marker exists
3. If marker exists, extract content between markers and compare with template

Determine status for each file:
- **missing**: file doesn't exist or no flux section
- **current**: section exists and matches template
- **outdated**: section exists but differs from template

### 6c: Show current config notice

If ANY config values are already set, print a notice before asking questions:

```
Current configuration:
- Install scope: <project|user|global> (change with: fluxctl config set install.scope <project|user|global>)
- Memory: <enabled|disabled> (change with: fluxctl config set memory.enabled <true|false>)
- Plan-Sync: <enabled|disabled> (change with: fluxctl config set planSync.enabled <true|false>)
- Plan-Sync cross-epic: <enabled|disabled> (change with: fluxctl config set planSync.crossEpic <true|false>)
- Review backend: <codex|rp|none> (change with: fluxctl config set review.backend <codex|rp|none>)
- GitHub scout: <enabled|disabled> (change with: fluxctl config set scouts.github <true|false>)
- Scout model: <model-name> (change with: fluxctl config set scouts.model <model-name>)
```

Only include lines for config values that are set. If no config is set, skip this notice.

### 6d: Build questions list

Build the questions array dynamically. **Only include questions for config values that are NOT already set.**

**Installation Scope question** (always ask FIRST if not already configured):

Check if scope is already set:
```bash
CURRENT_SCOPE=$("${PLUGIN_ROOT}/scripts/fluxctl" config get install.scope --json 2>/dev/null | jq -r '.value // empty')
```

If CURRENT_SCOPE is empty, include this question FIRST:
```json
{
  "header": "Install Scope",
  "question": "Where should Flux be installed?",
  "options": [
    {"label": "Project (Recommended)", "description": "Install in .flux/ - isolated to this project, committed to git"},
    {"label": "User", "description": "Install in ~/.flux/ - shared config across all projects, project data stays local"},
    {"label": "Global", "description": "Install in /usr/local/flux/ - system-wide for all users (requires sudo)"}
  ],
  "multiSelect": false
}
```

**Process scope answer immediately** (before other questions):
- If "Project": Set `INSTALL_ROOT=".flux"` and `CONFIG_ROOT=".flux"`
- If "User": Set `INSTALL_ROOT="$HOME/.flux"` and `CONFIG_ROOT=".flux"` (scripts shared, data local)
- If "Global": Set `INSTALL_ROOT="/usr/local/flux"` and `CONFIG_ROOT=".flux"`

Then persist:
```bash
"${PLUGIN_ROOT}/scripts/fluxctl" config set install.scope "<project|user|global>" --json
```

**Adjust Steps 3-4 based on scope:**
- **Project scope**: `mkdir -p .flux/bin` and copy scripts there
- **User scope**: `mkdir -p ~/.flux/bin` and copy scripts there, add to PATH hint
- **Global scope**: `sudo mkdir -p /usr/local/flux/bin` and copy scripts there

Available questions (include only if corresponding config is unset):

**Memory question** (include if CURRENT_MEMORY is empty):
```json
{
  "header": "Memory",
  "question": "Enable memory system? (Auto-captures learnings from NEEDS_WORK reviews)",
  "options": [
    {"label": "Yes (Recommended)", "description": "Auto-capture pitfalls and conventions from review feedback"},
    {"label": "No", "description": "Disable with: fluxctl config set memory.enabled false"}
  ],
  "multiSelect": false
}
```

**Plan-Sync question** (include if CURRENT_PLANSYNC is empty):
```json
{
  "header": "Plan-Sync",
  "question": "Enable plan-sync? (Updates downstream task specs after implementation drift)",
  "options": [
    {"label": "Yes (Recommended)", "description": "Sync task specs when implementation differs from original plan"},
    {"label": "No", "description": "Disable with: fluxctl config set planSync.enabled false"}
  ],
  "multiSelect": false
}
```

**Plan-Sync cross-epic question** (include if CURRENT_PLANSYNC is "true" AND CURRENT_CROSSEPIC is empty):
```json
{
  "header": "Cross-Epic",
  "question": "Enable cross-epic plan-sync? (Also checks other open epics for stale references)",
  "options": [
    {"label": "No (Recommended)", "description": "Only sync within current epic. Faster, avoids long Ralph loops."},
    {"label": "Yes", "description": "Also update tasks in other epics that reference changed APIs/patterns."}
  ],
  "multiSelect": false
}
```

**GitHub Scout question** (include if CURRENT_GITHUB_SCOUT is empty):
```json
{
  "header": "GitHub Scout",
  "question": "Enable GitHub scout? (Searches public/private repos for patterns during planning, requires gh CLI)",
  "options": [
    {"label": "No (Recommended)", "description": "Skip cross-repo search. Faster plans, no gh CLI needed."},
    {"label": "Yes", "description": "Search GitHub repos for patterns/examples during /flux:plan"}
  ],
  "multiSelect": false
}
```

**Scout Model question** (include if CURRENT_SCOUT_MODEL is empty):
```json
{
  "header": "Scout Model",
  "question": "Which model should scout agents use? (Scouts analyze your codebase during /flux:prime)",
  "options": [
    {"label": "claude-haiku-4-5 (Recommended)", "description": "Fast and cost-effective. Works with any Anthropic API access."},
    {"label": "gpt-5.3-codex-spark", "description": "OpenAI's fast model. Requires Codex Pro subscription."}
  ],
  "multiSelect": false
}
```

**Review question** (include if CURRENT_BACKEND is empty):
```json
{
  "header": "Review",
  "question": "Which review backend for Carmack-level reviews?",
  "options": [
    {"label": "Codex CLI", "description": "Cross-platform, uses GPT 5.2 High for reviews. Simple setup, works everywhere. <detected if HAVE_CODEX=1, (not detected) if HAVE_CODEX=0>"},
    {"label": "RepoPrompt", "description": "macOS only. Auto-discovers git diffs + context, reviews scoped to actual changes, ~65% fewer tokens than traditional approaches. <detected if HAVE_RP=1, (not detected) if HAVE_RP=0>"},
    {"label": "None", "description": "Skip reviews, can configure later with --review flag"}
  ],
  "multiSelect": false
}
```

**Docs question** (always include):
```json
{
  "header": "Docs",
  "question": "Update project documentation with Flux instructions?",
  "options": [
    {"label": "CLAUDE.md only", "description": "Add flux section to CLAUDE.md"},
    {"label": "AGENTS.md only", "description": "Add flux section to AGENTS.md"},
    {"label": "Both", "description": "Add flux section to both files"},
    {"label": "Skip", "description": "Don't update documentation"}
  ],
  "multiSelect": false
}
```

**Star question** (always include):
```json
{
  "header": "Star",
  "question": "Flux is free and open source. Star the repo on GitHub?",
  "options": [
    {"label": "Yes, star it", "description": "Uses gh CLI if available, otherwise shows link"},
    {"label": "No thanks", "description": "Skip starring"}
  ],
  "multiSelect": false
}
```

Use `AskUserQuestion` with the built questions array.

**Note:** If docs are already current, adjust the Docs question description to mention "(already up to date)" or skip that question entirely.

**Note:** If neither rp-cli nor codex is detected, add note to the Review question: "Neither rp-cli nor codex detected. Install one for review support."

## Step 7: Process Answers

Only process answers for questions that were asked (config values that were unset). Skip processing for config that was already set.

**Memory** (if question was asked):
- If "Yes": `"${PLUGIN_ROOT}/scripts/fluxctl" config set memory.enabled true --json`
- If "No": `"${PLUGIN_ROOT}/scripts/fluxctl" config set memory.enabled false --json`

**Plan-Sync** (if question was asked):
- If "Yes": `"${PLUGIN_ROOT}/scripts/fluxctl" config set planSync.enabled true --json`
- If "No": `"${PLUGIN_ROOT}/scripts/fluxctl" config set planSync.enabled false --json`

**Plan-Sync cross-epic** (if question was asked):
- If "Yes": `"${PLUGIN_ROOT}/scripts/fluxctl" config set planSync.crossEpic true --json`
- If "No": `"${PLUGIN_ROOT}/scripts/fluxctl" config set planSync.crossEpic false --json`

**GitHub Scout** (if question was asked):
- If "Yes": `"${PLUGIN_ROOT}/scripts/fluxctl" config set scouts.github true --json`
- If "No": `"${PLUGIN_ROOT}/scripts/fluxctl" config set scouts.github false --json`

**Scout Model** (if question was asked):
- If "claude-haiku-4-5": `"${PLUGIN_ROOT}/scripts/fluxctl" config set scouts.model "claude-haiku-4-5" --json`
- If "gpt-5.3-codex-spark": `"${PLUGIN_ROOT}/scripts/fluxctl" config set scouts.model "gpt-5.3-codex-spark" --json`

**Review** (if question was asked):
Map user's answer to config value and persist:

```bash
# Determine backend from answer
case "$review_answer" in
  "Codex"*) REVIEW_BACKEND="codex" ;;
  "RepoPrompt"*) REVIEW_BACKEND="rp" ;;
  *) REVIEW_BACKEND="none" ;;
esac

"${PLUGIN_ROOT}/scripts/fluxctl" config set review.backend "$REVIEW_BACKEND" --json
```

**Docs:**
For each chosen file (CLAUDE.md and/or AGENTS.md):
1. Read the file (create if doesn't exist)
2. If marker exists: replace everything between `<!-- BEGIN FLUX -->` and `<!-- END FLUX -->` (inclusive)
3. If no marker: append the snippet from [templates/claude-md-snippet.md](templates/claude-md-snippet.md)

**Star:**
- If "Yes, star it":
  1. Check if `gh` CLI is available: `which gh`
  2. If available, run: `gh api -X PUT /user/starred/Nairon-AI/flux`
  3. If `gh` not available or command fails, show: `Star manually: https://github.com/Nairon-AI/flux`

## Step 8: Print Summary

```
Flux setup complete!

Installation scope: <project|user|global>

Installed:
- <BIN_ROOT>/fluxctl (v<VERSION>)
- <BIN_ROOT>/fluxctl.py
- .flux/usage.md

MCP servers (user scope):
- Context7: library documentation (https://mcp.context7.com/mcp)
- Exa: web search (https://mcp.exa.ai/mcp)

To use from command line:
  # Project scope:
  export PATH=".flux/bin:$PATH"
  
  # User scope:
  export PATH="$HOME/.flux/bin:$PATH"  # Add to ~/.bashrc or ~/.zshrc
  
  # Global scope:
  # Already in PATH (/usr/local/flux/bin)
  
  fluxctl --help

Configuration (use fluxctl config set to change):
- Install scope: <project|user|global>
- Memory: <enabled|disabled>
- Plan-Sync: <enabled|disabled>
- Plan-Sync cross-epic: <enabled|disabled>
- GitHub scout: <enabled|disabled>
- Scout model: <claude-haiku-4-5|gpt-5.3-codex-spark>
- Review backend: <codex|rp|none>

Documentation updated:
- <files updated or "none">

Notes:
- Re-run /flux:setup after plugin updates to refresh scripts
- Interested in autonomous mode? Run /flux:ralph-init
- Default skill bootstrap: claudeception (installed if missing)
- MCP servers: Context7 + Exa installed at user scope (available in all projects)
- Uninstall (run manually): rm -rf .flux/bin .flux/usage.md and remove <!-- BEGIN/END FLUX --> block from docs
- This setup is optional - plugin works without it
```
