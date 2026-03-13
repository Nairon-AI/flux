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

Also read plugin version from `${PLUGIN_ROOT}/.claude-plugin/plugin.json`.

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

## Step 4c: Install recommended MCP servers (Optional)

Flux recommends MCP servers that enhance your AI development workflow. Installation is **optional** — users can skip or select which ones to install.

### Critical execution rule

Do **NOT** run `claude ...` CLI commands from inside `/flux:setup`.

Why: `/flux:setup` runs inside an active Claude Code session, and nested `claude` invocations fail with "cannot be launched inside another Claude Code session".

Use direct config updates to `~/.claude/settings.json` (preferred), then tell the user to restart Claude Code with `--resume`.

### Available MCP Servers

<!-- 
  TO ADD A NEW MCP/SKILL/TOOL:
  1. Add entry to the RECOMMENDED_MCPS table below
  2. Add conflict detection in "Detect conflicts"
  3. Add option to the question in "Ask which to install"
  4. Add installation logic in "Install selected servers"
  5. Add API key question if applicable (for MCPs with optional keys)
-->

| ID | Name | Category | Benefit | Free | Install Method |
|----|------|----------|---------|------|----------------|
| `context7` | Context7 | search | **No more hallucinated APIs** — up-to-date, version-specific library docs in every prompt | Yes | Add `mcpServers.context7` to `~/.claude/settings.json` |
| `exa` | Exa | search | **Fastest AI web search** — real-time research without leaving your session | Yes | Add `mcpServers.exa` to `~/.claude/settings.json` |
| `github` | GitHub | dev | **PRs, issues, actions in Claude** — no context switching to browser | Yes | Add `mcpServers.github` to `~/.claude/settings.json` |
| `supermemory` | Supermemory | memory | **Never re-explain context** — persistent memory across all sessions | Yes | Add `mcpServers.supermemory` to `~/.claude/settings.json` |
| `firecrawl` | Firecrawl | search | **Clean markdown + PDF parsing for agents** — crawl and scrape hard websites | Freemium | Add `mcpServers.firecrawl` to `~/.claude/settings.json` |

### Conflict Detection

Before offering to install, detect potential conflicts with existing tools:

```bash
SETTINGS_FILE="$HOME/.claude/settings.json"
GLOBAL_MCP_FILE="$HOME/.mcp.json"
PROJECT_MCP_FILE=".mcp.json"

list_mcp_names() {
  local file="$1"
  [ -f "$file" ] || return 0
  jq -r '.mcpServers // {} | if type == "object" then keys[] else empty end' "$file" 2>/dev/null || true
}

MCP_LIST=$(
  {
    list_mcp_names "$SETTINGS_FILE"
    list_mcp_names "$GLOBAL_MCP_FILE"
    list_mcp_names "$PROJECT_MCP_FILE"
  } | tr '[:upper:]' '[:lower:]' | sort -u
)

# Check each recommended MCP
HAVE_CONTEXT7=$(echo "$MCP_LIST" | grep -qx "context7" && echo 1 || echo 0)
HAVE_EXA=$(echo "$MCP_LIST" | grep -qx "exa" && echo 1 || echo 0)
HAVE_GITHUB=$(echo "$MCP_LIST" | grep -qx "github" && echo 1 || echo 0)
HAVE_SUPERMEMORY=$(echo "$MCP_LIST" | grep -qx "supermemory" && echo 1 || echo 0)
HAVE_FIRECRAWL=$(echo "$MCP_LIST" | grep -qx "firecrawl" && echo 1 || echo 0)

# Detect conflicting/similar tools
HAVE_PERPLEXITY=$(echo "$MCP_LIST" | grep -qx "perplexity" && echo 1 || echo 0)
HAVE_TAVILY=$(echo "$MCP_LIST" | grep -qx "tavily" && echo 1 || echo 0)
HAVE_BRAVE=$(echo "$MCP_LIST" | grep -qx "brave" && echo 1 || echo 0)
HAVE_SERPER=$(echo "$MCP_LIST" | grep -qx "serper" && echo 1 || echo 0)

# Memory category conflicts
HAVE_MEM0=$(echo "$MCP_LIST" | grep -qx "mem0" && echo 1 || echo 0)
HAVE_LANGMEM=$(echo "$MCP_LIST" | grep -Eiq "^langmem$|langchain.*memory" && echo 1 || echo 0)

# Docs category conflicts
HAVE_DEVDOCS=$(echo "$MCP_LIST" | grep -qx "devdocs" && echo 1 || echo 0)

# GitHub conflicts (check for gh CLI too)
HAVE_GH_CLI=$(which gh >/dev/null 2>&1 && echo 1 || echo 0)
```

Before writing MCP settings, ensure settings file exists and is valid JSON:

```bash
mkdir -p "$HOME/.claude"
[ -f "$SETTINGS_FILE" ] || printf '{"mcpServers":{}}\n' > "$SETTINGS_FILE"

if ! jq -e . "$SETTINGS_FILE" >/dev/null 2>&1; then
  cp "$SETTINGS_FILE" "$SETTINGS_FILE.bak.$(date +%Y%m%d-%H%M%S)"
  printf '{"mcpServers":{}}\n' > "$SETTINGS_FILE"
fi
```

### Build installation options with conflict awareness

For each recommended MCP, determine its status and any conflicts:

**Status types:**
- `installed` — Already installed, skip
- `available` — Not installed, no conflicts, offer to install
- `conflict` — Not installed, but similar tool exists, ask how to handle

### Ask which to install (with conflict handling)

Build the question dynamically. For items with conflicts, explain the situation:

```json
{
  "header": "MCP Servers",
  "question": "Flux recommends these MCP servers. Which would you like to install?",
  "multiple": true,
  "options": [
    // Only include options for MCPs not already installed
  ]
}
```

**Option templates:**

For **available** MCPs (no conflict):
```json
{"label": "Context7", "description": "No more hallucinated APIs — up-to-date library docs (free)"}
{"label": "Exa", "description": "Fastest AI web search — real-time research (free)"}
{"label": "GitHub", "description": "PRs, issues, actions without leaving Claude (free)"}
{"label": "Supermemory", "description": "Never re-explain context — persistent memory (free)"}
{"label": "Firecrawl", "description": "Scrape websites/PDFs into clean markdown for agents (freemium)"}
```

For MCPs with **conflicts**, use a separate question per conflict:

**Example: Exa conflicts with existing Perplexity:**
```json
{
  "header": "Search MCP Conflict",
  "question": "You have Perplexity MCP installed. Exa is faster and optimized for AI. How to proceed?",
  "options": [
    {"label": "Keep Perplexity", "description": "Don't install Exa, keep your current setup"},
    {"label": "Switch to Exa", "description": "Remove Perplexity, install Exa (recommended for speed)"},
    {"label": "Keep both", "description": "Install Exa alongside Perplexity (may cause duplicate results)"},
    {"label": "Skip", "description": "Decide later"}
  ]
}
```

**Example: Supermemory conflicts with mem0:**
```json
{
  "header": "Memory MCP Conflict",
  "question": "You have mem0 installed. Supermemory offers cross-app sync and knowledge graphs. How to proceed?",
  "options": [
    {"label": "Keep mem0", "description": "Don't install Supermemory"},
    {"label": "Switch to Supermemory", "description": "Remove mem0, install Supermemory"},
    {"label": "Keep both", "description": "Use both memory systems (may duplicate memories)"},
    {"label": "Skip", "description": "Decide later"}
  ]
}
```

**Example: GitHub MCP when gh CLI exists:**
```json
{
  "header": "GitHub Integration",
  "question": "You have gh CLI installed. GitHub MCP adds richer integration (browse code, manage PRs via Claude). How to proceed?",
  "options": [
    {"label": "Add GitHub MCP", "description": "Install alongside gh CLI (recommended, they complement each other)"},
    {"label": "Skip", "description": "Keep using gh CLI only"}
  ]
}
```

**Always include skip option:**
```json
{"label": "Skip all", "description": "Don't install any MCP servers"}
```

### Process conflict resolutions

Based on user's choice:

- **Keep existing**: Do nothing for that category
- **Switch**: Remove old MCP, install new one
- **Keep both**: Install new one without removing old
- **Skip**: Do nothing

```bash
# Example: Switch from Perplexity to Exa
tmp=$(mktemp)
jq '.mcpServers = (.mcpServers // {}) | del(.mcpServers.perplexity) | .mcpServers.exa = {"type":"http","url":"https://mcp.exa.ai/mcp"}' "$SETTINGS_FILE" > "$tmp" && mv "$tmp" "$SETTINGS_FILE"
```

### Install selected servers

For each selected server (that passed conflict resolution), install it:

**Context7:**
```bash
tmp=$(mktemp)
jq '.mcpServers = (.mcpServers // {}) | .mcpServers.context7 = {"type":"http","url":"https://mcp.context7.com/mcp"}' "$SETTINGS_FILE" > "$tmp" && mv "$tmp" "$SETTINGS_FILE"
```

**Exa:**
```bash
tmp=$(mktemp)
jq '.mcpServers = (.mcpServers // {}) | .mcpServers.exa = {"type":"http","url":"https://mcp.exa.ai/mcp"}' "$SETTINGS_FILE" > "$tmp" && mv "$tmp" "$SETTINGS_FILE"
```

**GitHub:**
```bash
# Requires GITHUB_PERSONAL_ACCESS_TOKEN - ask user if they want to configure
tmp=$(mktemp)
jq '.mcpServers = (.mcpServers // {}) | .mcpServers.github = {"command":"npx","args":["-y","@modelcontextprotocol/server-github"]}' "$SETTINGS_FILE" > "$tmp" && mv "$tmp" "$SETTINGS_FILE"
```

**Supermemory:**
```bash
tmp=$(mktemp)
jq '.mcpServers = (.mcpServers // {}) | .mcpServers.supermemory = {"type":"http","url":"https://mcp.supermemory.ai/mcp"}' "$SETTINGS_FILE" > "$tmp" && mv "$tmp" "$SETTINGS_FILE"
```

**Firecrawl:**
```bash
tmp=$(mktemp)
jq '.mcpServers = (.mcpServers // {}) | .mcpServers.firecrawl = {"command":"npx","args":["-y","firecrawl-mcp"]}' "$SETTINGS_FILE" > "$tmp" && mv "$tmp" "$SETTINGS_FILE"
```

### Ask about API keys / tokens (only for installed servers that need them)

Only ask for servers that were just installed AND benefit from keys:

**GitHub Personal Access Token (required for private repos):**
```json
{
  "header": "GitHub Token (Optional)",
  "question": "GitHub MCP works with public repos. For private repos, add a Personal Access Token?",
  "options": [
    {"label": "Add token", "description": "Configure PAT for private repo access (get from github.com/settings/tokens)"},
    {"label": "Skip", "description": "Use public repos only (can add token later)"}
  ]
}
```

If user chooses to add token:
```json
{
  "header": "GitHub PAT",
  "question": "Enter your GitHub Personal Access Token (from github.com/settings/tokens with 'repo' scope):",
  "options": []
}
```

Then reconfigure:
```bash
tmp=$(mktemp)
jq --arg token "<user_provided_token>" '.mcpServers = (.mcpServers // {}) | .mcpServers.github = {"command":"npx","args":["-y","@modelcontextprotocol/server-github"],"env":{"GITHUB_PERSONAL_ACCESS_TOKEN":$token}}' "$SETTINGS_FILE" > "$tmp" && mv "$tmp" "$SETTINGS_FILE"
```

**Context7 / Exa / Supermemory / Firecrawl API keys:**

These work without keys but keys unlock higher rate limits. Only ask if user installed them:

```json
{
  "header": "API Keys (Optional)",
  "question": "These MCPs work without API keys, but keys unlock higher rate limits. Add any?",
  "multiple": true,
  "options": [
    // Only show options for MCPs that were just installed
    {"label": "Context7 key", "description": "Higher rate limits (free key from context7.com/dashboard)"},
    {"label": "Exa key", "description": "Higher rate limits (free key from exa.ai)"},
    {"label": "Supermemory key", "description": "Higher rate limits (free key from supermemory.ai)"},
    {"label": "Firecrawl key", "description": "Required for higher quotas (free tier at firecrawl.dev)"},
    {"label": "Skip", "description": "Use free tier for all (can add keys later)"}
  ]
}
```

If user selects any key option, ask for each selected key value and patch `~/.claude/settings.json`:

```bash
# Example helper to set one env key on an MCP server
set_mcp_env_key() {
  local server="$1"
  local env_key="$2"
  local env_val="$3"
  local tmp
  tmp=$(mktemp)
  jq --arg s "$server" --arg k "$env_key" --arg v "$env_val" \
    '.mcpServers = (.mcpServers // {}) | .mcpServers[$s] = ((.mcpServers[$s] // {}) + {env: ((.mcpServers[$s].env // {}) + {($k): $v})})' \
    "$SETTINGS_FILE" > "$tmp" && mv "$tmp" "$SETTINGS_FILE"
}

# Call based on user selections:
# set_mcp_env_key "exa" "EXA_API_KEY" "<user_provided_exa_key>"
# set_mcp_env_key "supermemory" "SUPERMEMORY_API_KEY" "<user_provided_supermemory_key>"
# set_mcp_env_key "firecrawl" "FIRECRAWL_API_KEY" "<user_provided_firecrawl_key>"
# Context7 key support may vary by provider release; skip if no documented env var.
```

### Track installation results

Store for summary:
- `INSTALLED_MCPS` — list of MCP names installed this session
- `REMOVED_MCPS` — list of MCPs removed due to switch
- `CONFIGURED_TOKENS` — list of MCPs with tokens/keys configured
- `SKIPPED_MCPS` — list of MCPs user chose to skip
- `CONFLICTS_RESOLVED` — list of conflict resolutions made

### Manual fallback

If settings are not writable or `jq` is missing, print manual instructions:

```
MCP servers (install manually in Claude Code):
  1. Run /mcp in chat
  2. Add these servers:
     - context7: https://mcp.context7.com/mcp
     - exa: https://mcp.exa.ai/mcp
     - supermemory: https://mcp.supermemory.ai/mcp
     - firecrawl: npx -y firecrawl-mcp
     - github: npx -y @modelcontextprotocol/server-github
  3. Restart Claude Code with `--resume` to pick up where you left off
```

## Step 4d: Install recommended desktop applications (Optional)

Flux recommends productivity applications that enhance AI-augmented development. Installation is **optional** — users can skip or select which ones to install.

### Detect OS FIRST

**CRITICAL: Detect OS before showing any options. Only offer apps compatible with the user's OS.**

```bash
# Detect OS - run this FIRST
OS_TYPE="unknown"
case "$(uname -s)" in
  Darwin*) OS_TYPE="macos" ;;
  Linux*)  OS_TYPE="linux" ;;
  MINGW*|MSYS*|CYGWIN*) OS_TYPE="windows" ;;
esac

echo "Detected OS: $OS_TYPE"
```

### Available Desktop Applications (by OS)

<!-- 
  TO ADD A NEW APPLICATION:
  1. Add entry to the RECOMMENDED_APPS table below
  2. Add OS check in "Detect OS and conflicts"
  3. Add conflict detection for that category
  4. Add option to the question
  5. Add installation logic
-->

| ID | Name | macOS | Linux | Windows | Benefit | Free | Install |
|----|------|-------|-------|---------|---------|------|---------|
| `raycast` | Raycast | Yes | No | No | **Launcher on steroids** — AI, snippets, clipboard history | Freemium | `brew install --cask raycast` |
| `ghostty` | Ghostty | Yes | Yes | No | **Fast terminal** — GPU-accelerated, split-pane workflows | Yes | `brew install --cask ghostty` |
| `superset` | Superset | Yes | No | No | **Primary orchestrator for parallel Claude sessions** — git worktree workspace manager | Yes | `brew install --cask superset` |
| `wispr-flow` | Wispr Flow | Yes | No | No | **Voice-to-text 4x faster** — dictate anywhere | Freemium | Manual download |
| `granola` | Granola | Yes | No | Yes | **AI meeting notes** — no bot joins calls | Freemium | Manual download |

### OS Compatibility Matrix

```
macOS:   Raycast, Ghostty, Superset, Wispr Flow, Granola (all 5)
Linux:   Ghostty only
Windows: Granola only
```

### Detect conflicts (only for compatible apps)

```bash
# Only run conflict detection for apps compatible with current OS

if [ "$OS_TYPE" = "macos" ]; then
  # Launcher category (Raycast conflicts) - macOS only
  HAVE_ALFRED=$([ -d "/Applications/Alfred 5.app" ] || [ -d "/Applications/Alfred 4.app" ] && echo 1 || echo 0)
  HAVE_LAUNCHBAR=$([ -d "/Applications/LaunchBar.app" ] && echo 1 || echo 0)
  
  # Voice dictation category (Wispr Flow) - macOS only
  HAVE_TALON=$([ -d "/Applications/Talon.app" ] && echo 1 || echo 0)
  
  # Check if already installed - macOS
  HAVE_RAYCAST=$([ -d "/Applications/Raycast.app" ] && echo 1 || echo 0)
  HAVE_SUPERSET=$([ -d "/Applications/Superset.app" ] && echo 1 || echo 0)
  HAVE_WISPR=$([ -d "/Applications/Wispr Flow.app" ] && echo 1 || echo 0)
fi

if [ "$OS_TYPE" = "macos" ] || [ "$OS_TYPE" = "linux" ]; then
  # Terminal category (Ghostty conflicts) - macOS and Linux
  HAVE_ITERM=$([ -d "/Applications/iTerm.app" ] && echo 1 || echo 0)
  HAVE_WARP=$([ -d "/Applications/Warp.app" ] && echo 1 || echo 0)
  HAVE_ALACRITTY=$([ -d "/Applications/Alacritty.app" ] || which alacritty >/dev/null 2>&1 && echo 1 || echo 0)
  HAVE_KITTY=$([ -d "/Applications/kitty.app" ] || which kitty >/dev/null 2>&1 && echo 1 || echo 0)
  
  # Check if already installed
  HAVE_GHOSTTY=$([ -d "/Applications/Ghostty.app" ] || which ghostty >/dev/null 2>&1 && echo 1 || echo 0)
fi

if [ "$OS_TYPE" = "macos" ] || [ "$OS_TYPE" = "windows" ]; then
  # Meeting notes category (Granola) - macOS and Windows
  HAVE_OTTER=$([ -d "/Applications/Otter.app" ] && echo 1 || echo 0)
  HAVE_FATHOM=$([ -d "/Applications/Fathom.app" ] && echo 1 || echo 0)
  
  # Check if already installed
  HAVE_GRANOLA=$([ -d "/Applications/Granola.app" ] && echo 1 || echo 0)
fi
```

### Build options based on OS

**IMPORTANT: Only include apps compatible with detected OS. Skip this entire step if no apps are compatible.**

**REQUIRED behavior:** Always execute this desktop-apps step before CLI tools/skills on supported OS (`macos`, `linux`, `windows`). Do not silently skip it.

If all compatible apps are already installed, print an explicit status line and continue:
```
Desktop apps already installed: <comma-separated list>
```

### Ask which to install (OS-specific questions)

**For macOS users** (all 5 apps available):

```json
{
  "header": "Desktop Apps (macOS)",
  "question": "Flux recommends these productivity apps. Which would you like to install?",
  "multiple": true,
  "options": [
    // Only include apps NOT already installed
    {"label": "Superset (Recommended)", "description": "Primary orchestrator for parallel Claude Code sessions using git worktrees (free)"},
    {"label": "Raycast", "description": "Launcher with AI, snippets, clipboard history (free, Pro $10/mo)"},
    {"label": "Ghostty", "description": "Fast GPU terminal with split panes for parallel agents (free)"},
    {"label": "Wispr Flow", "description": "Voice-to-text 4x faster than typing (free tier available)"},
    {"label": "Granola", "description": "AI meeting notes without bot joining calls (25 free/mo)"}
  ]
}
```

**For Linux users** (only Ghostty):

```json
{
  "header": "Desktop Apps (Linux)",
  "question": "Flux recommends Ghostty terminal for Linux. Install it?",
  "options": [
    {"label": "Yes, install Ghostty", "description": "Fast GPU terminal with split panes (free, open-source)"},
    {"label": "Skip", "description": "Keep current terminal setup"}
  ]
}
```

**For Windows users** (only Granola):

```json
{
  "header": "Desktop Apps (Windows)", 
  "question": "Flux recommends Granola for meeting notes on Windows. Install it?",
  "options": [
    {"label": "Yes, install Granola", "description": "AI meeting notes without bot joining calls (25 free/mo)"},
    {"label": "Skip", "description": "Skip desktop apps"}
  ]
}
```

**If OS is unknown or no compatible apps:**
Skip desktop apps section entirely and note in summary: "Desktop apps: skipped (unsupported OS)"

### Handle conflicts with separate questions

**Example: Raycast conflicts with Alfred:**
```json
{
  "header": "Launcher Conflict",
  "question": "You have Alfred installed. Raycast offers similar features plus built-in AI. How to proceed?",
  "options": [
    {"label": "Keep Alfred", "description": "Don't install Raycast, keep your current setup"},
    {"label": "Try Raycast", "description": "Install Raycast alongside Alfred (can switch later)"},
    {"label": "Skip", "description": "Decide later"}
  ]
}
```

**Example: Ghostty conflicts with iTerm:**
```json
{
  "header": "Terminal Conflict",
  "question": "You have iTerm installed. Ghostty is faster with better split-pane focus. How to proceed?",
  "options": [
    {"label": "Keep iTerm", "description": "Don't install Ghostty"},
    {"label": "Try Ghostty", "description": "Install alongside iTerm (can switch later)"},
    {"label": "Skip", "description": "Decide later"}
  ]
}
```

**Example: Ghostty conflicts with Warp:**
```json
{
  "header": "Terminal Conflict",
  "question": "You have Warp installed. Ghostty is simpler with better split-pane workflows. How to proceed?",
  "options": [
    {"label": "Keep Warp", "description": "Don't install Ghostty (Warp has its own AI features)"},
    {"label": "Try Ghostty", "description": "Install alongside Warp (can switch later)"},
    {"label": "Skip", "description": "Decide later"}
  ]
}
```

### Install selected applications

**Raycast (macOS only):**
```bash
if [ "$OS_TYPE" = "macos" ]; then
  brew install --cask raycast 2>/dev/null || {
    echo "Install manually: https://raycast.com"
  }
fi
```

**Ghostty (macOS/Linux):**
```bash
if [ "$OS_TYPE" = "macos" ]; then
  brew install --cask ghostty 2>/dev/null || {
    echo "Install manually: https://ghostty.org"
  }
elif [ "$OS_TYPE" = "linux" ]; then
  # Check package manager
  if which apt-get >/dev/null 2>&1; then
    echo "Install from: https://ghostty.org/docs/install/linux"
  elif which pacman >/dev/null 2>&1; then
    echo "Install: pacman -S ghostty"
  else
    echo "Install manually: https://ghostty.org"
  fi
fi
```

**Superset (macOS only, recommended orchestrator):**
```bash
if [ "$OS_TYPE" = "macos" ]; then
  brew install --cask superset 2>/dev/null || {
    echo "Download Superset: https://github.com/superset-sh/superset/releases/latest/download/Superset-arm64.dmg"
    open "https://superset.sh" 2>/dev/null || true
  }
fi
```

**Wispr Flow (macOS/iOS - manual):**
```bash
if [ "$OS_TYPE" = "macos" ]; then
  echo "Download Wispr Flow: https://www.wispr.ai"
  open "https://www.wispr.ai" 2>/dev/null || true
fi
```

**Granola (macOS/Windows/iOS - manual):**
```bash
echo "Download Granola: https://www.granola.ai"
open "https://www.granola.ai" 2>/dev/null || true
```

### Track installation results

Store for summary:
- `INSTALLED_APPS` — list of apps installed this session
- `SKIPPED_APPS` — list of apps user chose to skip
- `CONFLICTS_APPS` — list of app conflicts and resolutions

## Step 4e: Install recommended CLI tools (Optional)

Flux recommends CLI tools that complement the AI development workflow.

**Note:** This step uses `OS_TYPE` detected in Step 4d. CLI tools work on all platforms.

### Available CLI Tools

<!-- 
  TO ADD A NEW CLI TOOL:
  1. Add entry to the RECOMMENDED_CLI table below
  2. Add detection check
  3. Add option to the question
  4. Add installation logic
-->

| ID | Name | Benefit | Free | Install (macOS) | Install (Linux) | Install (Windows) |
|----|------|---------|------|-----------------|-----------------|-------------------|
| `gh` | GitHub CLI | **PRs, issues, releases from terminal** — no browser context switching | Yes | `brew install gh` | `sudo apt install gh` | `winget install --id GitHub.cli` |
| `jq` | jq | **JSON plumbing for agent scripts** — parse API/config output quickly | Yes | `brew install jq` | `sudo apt install jq` | `winget install --id jqlang.jq` |
| `fzf` | fzf | **Fuzzy finder for shell + git navigation** — faster local workflows | Yes | `brew install fzf` | `sudo apt install fzf` | `winget install --id junegunn.fzf` |
| `lefthook` | Lefthook | **Fast pre-commit hooks** — catch issues before CI | Yes | `npm i -g lefthook` | `npm i -g lefthook` | `npm i -g lefthook` |
| `agent-browser` | Agent Browser | **Browser automation for coding agents** — UI QA and reproducible evidence | Yes | `npm i -g agent-browser` | `npm i -g agent-browser` | `npm i -g agent-browser` |
| `cli-continues` | CLI Continues | **Session handoff between agents** — resume context across tools | Yes | `npm i -g continues` | `npm i -g continues` | `npm i -g continues` |
### Detect existing tools

```bash
# Check if tools already installed
HAVE_GH_CLI=$(which gh >/dev/null 2>&1 && echo 1 || echo 0)
HAVE_JQ_CLI=$(which jq >/dev/null 2>&1 && echo 1 || echo 0)
HAVE_FZF_CLI=$(which fzf >/dev/null 2>&1 && echo 1 || echo 0)
HAVE_LEFTHOOK_CLI=$(which lefthook >/dev/null 2>&1 && echo 1 || echo 0)
HAVE_AGENT_BROWSER_CLI=$(which agent-browser >/dev/null 2>&1 && echo 1 || echo 0)
HAVE_CONTINUES_CLI=$( (which continues >/dev/null 2>&1 || which cont >/dev/null 2>&1) && echo 1 || echo 0)
HAVE_NPM=$(which npm >/dev/null 2>&1 && echo 1 || echo 0)
HAVE_WINGET=$(which winget >/dev/null 2>&1 && echo 1 || echo 0)

# gh CLI complements (not conflicts with) GitHub MCP
# If user installed GitHub MCP in step 4c, recommend gh CLI as complement
```

### Ask which to install

Build recommendations by platform so users only see installable options for their machine:

- macOS: recommend brew-based tools plus npm-based tools when `npm` exists
- Windows: recommend winget-based tools when `winget` exists, plus npm-based tools when `npm` exists
- If `npm` is missing, do not offer npm-only tools and print: `Install Node.js first: https://nodejs.org`

Only show tools not already installed:

```json
{
  "header": "CLI Tools",
  "question": "Flux recommends these CLI tools. Which would you like to install?",
  "multiple": true,
  "options": [
    // Only include tools not already installed
  ]
}
```

Map selected CLI options to install flags:

```bash
INSTALL_GH=0
INSTALL_JQ=0
INSTALL_FZF=0
INSTALL_LEFTHOOK=0
INSTALL_AGENT_BROWSER=0
INSTALL_CONTINUES=0

# Set each to 1 if selected by user
```

**Option templates:**
```json
{"label": "GitHub CLI (gh)", "description": "PRs, issues, releases from terminal — complements GitHub MCP (free)"}
{"label": "jq", "description": "JSON parsing for scripts and API output (free)"}
{"label": "fzf", "description": "Fuzzy finder for terminal, history, and git navigation (free)"}
{"label": "Lefthook", "description": "Fast pre-commit hooks to catch issues before CI (free)"}
{"label": "Agent Browser", "description": "Headless browser automation CLI for agent-driven QA (free)"}
{"label": "CLI Continues", "description": "Resume/switch coding session context across agent CLIs (free)"}
```

**If GitHub MCP was installed in step 4c, mention the synergy:**
```json
{
  "header": "CLI Tools",
  "question": "You installed GitHub MCP. The gh CLI complements it for terminal workflows. Install it?",
  "options": [
    {"label": "Yes, install gh", "description": "Create PRs, triage issues from terminal (free, open-source)"},
    {"label": "Skip", "description": "Use GitHub MCP only"}
  ]
}
```

**If all tools are already installed:**
Skip this question and show "already installed" in summary.

### Install selected tools

**GitHub CLI:**
```bash
if [ "$INSTALL_GH" = "1" ]; then
  if [ "$OS_TYPE" = "macos" ]; then
    brew install gh 2>/dev/null || {
      echo "Install manually: https://cli.github.com"
    }
  elif [ "$OS_TYPE" = "linux" ]; then
    if which apt-get >/dev/null 2>&1; then
      sudo apt install gh 2>/dev/null || {
        echo "Install: https://github.com/cli/cli/blob/trunk/docs/install_linux.md"
      }
    elif which pacman >/dev/null 2>&1; then
      sudo pacman -S github-cli 2>/dev/null || true
    elif which dnf >/dev/null 2>&1; then
      sudo dnf install gh 2>/dev/null || true
    else
      echo "Install manually: https://cli.github.com"
    fi
  elif [ "$OS_TYPE" = "windows" ]; then
    if which winget >/dev/null 2>&1; then
      winget install --id GitHub.cli --exact --accept-package-agreements --accept-source-agreements 2>/dev/null || {
        echo "Install manually: https://cli.github.com"
      }
    else
      echo "Install manually: https://cli.github.com"
    fi
  else
    echo "Install manually: https://cli.github.com"
  fi

  # Prompt for authentication if installed
  if which gh >/dev/null 2>&1; then
    echo "Run 'gh auth login' to authenticate with GitHub"
  fi
fi
```

**jq:**
```bash
if [ "$INSTALL_JQ" = "1" ]; then
  if [ "$OS_TYPE" = "macos" ]; then
    brew install jq 2>/dev/null || echo "Install manually: https://jqlang.github.io/jq/"
  elif [ "$OS_TYPE" = "linux" ]; then
    if which apt-get >/dev/null 2>&1; then
      sudo apt install jq 2>/dev/null || echo "Install manually: https://jqlang.github.io/jq/download/"
    elif which pacman >/dev/null 2>&1; then
      sudo pacman -S jq 2>/dev/null || true
    elif which dnf >/dev/null 2>&1; then
      sudo dnf install jq 2>/dev/null || true
    fi
  elif [ "$OS_TYPE" = "windows" ]; then
    if which winget >/dev/null 2>&1; then
      winget install --id jqlang.jq --exact --accept-package-agreements --accept-source-agreements 2>/dev/null || {
        echo "Install manually: https://jqlang.github.io/jq/download/"
      }
    else
      echo "Install manually: https://jqlang.github.io/jq/download/"
    fi
  fi
fi
```

**fzf:**
```bash
if [ "$INSTALL_FZF" = "1" ]; then
  if [ "$OS_TYPE" = "macos" ]; then
    brew install fzf 2>/dev/null || echo "Install manually: https://github.com/junegunn/fzf"
  elif [ "$OS_TYPE" = "linux" ]; then
    if which apt-get >/dev/null 2>&1; then
      sudo apt install fzf 2>/dev/null || echo "Install manually: https://github.com/junegunn/fzf"
    elif which pacman >/dev/null 2>&1; then
      sudo pacman -S fzf 2>/dev/null || true
    elif which dnf >/dev/null 2>&1; then
      sudo dnf install fzf 2>/dev/null || true
    fi
  elif [ "$OS_TYPE" = "windows" ]; then
    if which winget >/dev/null 2>&1; then
      winget install --id junegunn.fzf --exact --accept-package-agreements --accept-source-agreements 2>/dev/null || {
        echo "Install manually: https://github.com/junegunn/fzf"
      }
    else
      echo "Install manually: https://github.com/junegunn/fzf"
    fi
  fi
fi
```

**Lefthook / Agent Browser / CLI Continues (Node-based):**
```bash
if which npm >/dev/null 2>&1; then
  [ "$INSTALL_LEFTHOOK" = "1" ] && npm i -g lefthook 2>/dev/null || true
  [ "$INSTALL_AGENT_BROWSER" = "1" ] && npm i -g agent-browser 2>/dev/null || true
  [ "$INSTALL_CONTINUES" = "1" ] && npm i -g continues 2>/dev/null || true
else
  echo "npm not found. Install Node.js first: https://nodejs.org"
fi
```

### Track installation results

Store for summary:
- `INSTALLED_CLI` — list of CLI tools installed this session
- `SKIPPED_CLI` — list of CLI tools user chose to skip

## Step 4f: Install optional agent skills (Optional)

Offer lightweight, generally useful agent skills that improve onboarding and execution quality across most repos.

### Available skills

| ID | Name | Benefit | Install |
|----|------|---------|---------|
| `ui-skills` | UI Skills | **Fix ugly agent UIs** — accessibility, motion, metadata, design polish | `npx -y ui-skills add --all` |
| `taste-skill` | Taste Skill | **Anti-generic UI taste layer** — more distinctive, intentional frontend output | `curl .../taste-skill/SKILL.md -> ~/.claude/skills/taste-skill/SKILL.md` |
| `semver-changelog` | Semver Changelog | **Release hygiene automation** — structured changelog updates from commits | `npx skills add https://github.com/prulloac/agent-skills --skill semver-changelog` |
| `agent-skills-vercel` | Agent Skills (Vercel) | **Broad skill catalog** — reusable workflows across stacks | `git clone https://github.com/vercel-labs/agent-skills.git ~/.claude/skills/agent-skills-vercel` |
| `x-research-skill` | X Research Skill | **Faster ecosystem intel** — summarize high-signal X threads quickly | `git clone https://github.com/rohunvora/x-research-skill.git ~/.claude/skills/x-research-skill` |

### Detect existing skills

```bash
HAVE_UI_SKILLS=$(([ -f "$HOME/.claude/skills/baseline-ui/SKILL.md" ] || [ -f "$HOME/.claude/skills/fixing-accessibility/SKILL.md" ] || [ -d "$HOME/.claude/skills/ui-skills" ]) && echo 1 || echo 0)
HAVE_TASTE_SKILL=$([ -f "$HOME/.claude/skills/taste-skill/SKILL.md" ] && echo 1 || echo 0)
HAVE_SEMVER_CHANGELOG=$(([ -d "$HOME/.claude/skills/semver-changelog" ] || [ -d "$HOME/.claude/skills/semantic-version-changelog-generator" ]) && echo 1 || echo 0)
HAVE_AGENT_SKILLS_VERCEL=$([ -d "$HOME/.claude/skills/agent-skills-vercel" ] && echo 1 || echo 0)
HAVE_X_RESEARCH_SKILL=$([ -d "$HOME/.claude/skills/x-research-skill" ] && echo 1 || echo 0)
HAVE_NPX=$(which npx >/dev/null 2>&1 && echo 1 || echo 0)
HAVE_GIT=$(which git >/dev/null 2>&1 && echo 1 || echo 0)
```

### Ask which skills to install

```json
{
  "header": "Agent Skills",
  "question": "Flux can install optional agent skills. Which would you like?",
  "multiple": true,
  "options": [
    {"label": "UI Skills", "description": "Polish frontend output: accessibility, metadata, motion, design"},
    {"label": "Taste Skill", "description": "Reduce generic/sloppy UI generation"},
    {"label": "Semver Changelog", "description": "Generate/update CHANGELOG with semantic version structure"},
    {"label": "Agent Skills (Vercel)", "description": "Install a broad catalog of production-ready agent skills"},
    {"label": "X Research Skill", "description": "Summarize high-signal X threads for research"},
    {"label": "Skip", "description": "No additional skills"}
  ]
}
```

Map selected skill options to install flags:

```bash
INSTALL_UI_SKILLS=0
INSTALL_TASTE_SKILL=0
INSTALL_SEMVER_CHANGELOG=0
INSTALL_AGENT_SKILLS_VERCEL=0
INSTALL_X_RESEARCH_SKILL=0

# Set each to 1 if selected by user
```

### Install selected skills

```bash
if [ "$INSTALL_UI_SKILLS" = "1" ]; then
  if which npx >/dev/null 2>&1; then
    npx -y ui-skills add --all 2>/dev/null || true
  else
    echo "npx not found. Install manually: npx -y ui-skills add --all"
  fi

  if [ ! -f "$HOME/.claude/skills/baseline-ui/SKILL.md" ] && [ ! -f "$HOME/.claude/skills/fixing-accessibility/SKILL.md" ]; then
    echo "Install manually: npx -y ui-skills add --all"
  fi
fi

if [ "$INSTALL_TASTE_SKILL" = "1" ]; then
  mkdir -p "$HOME/.claude/skills/taste-skill"
  curl -fsSL https://raw.githubusercontent.com/Leonxlnx/taste-skill/main/taste-skill/SKILL.md -o "$HOME/.claude/skills/taste-skill/SKILL.md" 2>/dev/null || {
    if which git >/dev/null 2>&1; then
      TMP_TASTE_DIR=$(mktemp -d 2>/dev/null || echo "")
      if [ -n "$TMP_TASTE_DIR" ] && git clone --depth 1 https://github.com/Leonxlnx/taste-skill.git "$TMP_TASTE_DIR/taste-skill" 2>/dev/null; then
        cp "$TMP_TASTE_DIR/taste-skill/taste-skill/SKILL.md" "$HOME/.claude/skills/taste-skill/SKILL.md" 2>/dev/null || true
        rm -rf "$TMP_TASTE_DIR"
      fi
    fi
  }

  if [ ! -s "$HOME/.claude/skills/taste-skill/SKILL.md" ]; then
    echo "Install manually: https://github.com/Leonxlnx/taste-skill"
  fi
fi

if [ "$INSTALL_SEMVER_CHANGELOG" = "1" ]; then
  if which npx >/dev/null 2>&1; then
    npx skills add https://github.com/prulloac/agent-skills --skill semver-changelog 2>/dev/null || {
      echo "Install manually: https://skills.sh/prulloac/agent-skills/semver-changelog"
    }
  else
    echo "npx not found. Install manually: https://skills.sh/prulloac/agent-skills/semver-changelog"
  fi
fi

if [ "$INSTALL_AGENT_SKILLS_VERCEL" = "1" ]; then
  if [ -d "$HOME/.claude/skills/agent-skills-vercel" ]; then
    git -C "$HOME/.claude/skills/agent-skills-vercel" pull --ff-only 2>/dev/null || true
  else
    git clone --depth 1 https://github.com/vercel-labs/agent-skills.git "$HOME/.claude/skills/agent-skills-vercel" 2>/dev/null || {
      echo "Install manually: https://github.com/vercel-labs/agent-skills"
    }
  fi
fi

if [ "$INSTALL_X_RESEARCH_SKILL" = "1" ]; then
  if [ -d "$HOME/.claude/skills/x-research-skill" ]; then
    git -C "$HOME/.claude/skills/x-research-skill" pull --ff-only 2>/dev/null || true
  else
    git clone --depth 1 https://github.com/rohunvora/x-research-skill.git "$HOME/.claude/skills/x-research-skill" 2>/dev/null || {
      echo "Install manually: https://github.com/rohunvora/x-research-skill"
    }
  fi
fi
```

### Verify skill installs (required)

After running installs, verify each selected skill path exists before marking success:

- UI Skills: `$HOME/.claude/skills/baseline-ui/SKILL.md` (or `fixing-accessibility/SKILL.md`)
- Taste Skill: `$HOME/.claude/skills/taste-skill/SKILL.md`
- Semver Changelog: `$HOME/.claude/skills/semver-changelog` or `$HOME/.claude/skills/semantic-version-changelog-generator`
- Agent Skills (Vercel): `$HOME/.claude/skills/agent-skills-vercel` directory
- X Research Skill: `$HOME/.claude/skills/x-research-skill` directory

If verification fails, mark the skill as `failed` in summary and show manual install URL/command. Do **not** report global "skills installed" unless selected skills verified.

### Track installation results

Store for summary:
- `INSTALLED_SKILLS` — list of skills installed this session
- `SKIPPED_SKILLS` — list of skills user chose to skip

## Step 5: Update meta.json

Read current `.flux/meta.json`, add/update these fields (preserve all others):

```json
{
  "setup_version": "<PLUGIN_VERSION>",
  "setup_date": "<ISO_DATE>",
  "installed_by_flux": {
    "mcp_servers": ["<list of MCP server names installed this session, e.g. context7, exa, github, supermemory, firecrawl>"],
    "skills": ["<list of skill names installed this session, e.g. ui-skills, taste-skill, agent-skills-vercel>"],
    "desktop_apps": ["<list of desktop apps installed this session, e.g. raycast, ghostty, superset, wispr-flow, granola>"],
    "cli_tools": ["<list of CLI tools installed this session, e.g. gh, jq, fzf, lefthook, agent-browser, cli-continues>"]
  }
}
```

Only include items that were **installed by this setup session** (not items that were "already installed"). This manifest is used by the uninstall flow to know what Flux added.

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
```

**MCP servers section** (only show if any were installed, removed, or already existed):

```
MCP servers:
- Context7: <installed | installed + key | already installed | skipped>
- Exa: <installed | installed + key | already installed | skipped>
- GitHub: <installed | installed + token | already installed | skipped>
- Supermemory: <installed | installed + key | already installed | skipped>
- Firecrawl: <installed | installed + key | already installed | skipped>
```

Use tracking variables from Step 4c to determine status:
- "installed" — installed this session without API key/token
- "installed + key/token" — installed this session with credentials configured
- "already installed" — was already present before setup
- "skipped" — user chose not to install
- "switched from X" — replaced existing tool X with this one

**If conflicts were resolved, show:**
```
Conflicts resolved:
- Switched from Perplexity to Exa (faster, AI-optimized)
- Kept mem0 alongside Supermemory
```

If all were skipped, show:
```
MCP servers: skipped (install later with /flux:setup or manually)
```

**Desktop applications section** (only show if OS had compatible apps):

```
Desktop applications (<OS_TYPE>):
- Raycast: <installed | already installed | skipped | conflict: kept Alfred>
- Ghostty: <installed | already installed | skipped | conflict: kept iTerm>
- Superset: <installed | already installed | skipped>
- Wispr Flow: <installed | already installed | skipped>
- Granola: <installed | already installed | skipped>
```

Use tracking variables from Step 4d to determine status. Only show apps compatible with user's OS:
- macOS: show all 5 apps
- Linux: show only Ghostty
- Windows: show only Granola

If OS was unsupported or user skipped all:
```
Desktop applications: skipped (<reason>)
```

**CLI tools section** (only show if any were offered):

```
CLI tools:
- GitHub CLI (gh): <installed | already installed | skipped>
- jq: <installed | already installed | skipped>
- fzf: <installed | already installed | skipped>
- Lefthook: <installed | already installed | skipped>
- Agent Browser: <installed | already installed | skipped>
- CLI Continues: <installed | already installed | skipped>
```

Use tracking variables from Step 4e. If gh was already installed before setup, show "already installed".

**Agent skills section** (only show if offered):

```
Agent skills:
- UI Skills: <installed | already installed | skipped | failed>
- Taste Skill: <installed | already installed | skipped | failed>
- Semver Changelog: <installed | already installed | skipped | failed>
- Agent Skills (Vercel): <installed | already installed | skipped | failed>
- X Research Skill: <installed | already installed | skipped | failed>
```

Use tracking variables from Step 4f.

Continue summary:

```
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
- Optional agent skills can be installed/updated via /flux:setup
- MCP servers installed at user scope are available in all projects
- Desktop apps and CLI tools are optional productivity boosters
- Uninstall (run manually): rm -rf .flux/bin .flux/usage.md and remove <!-- BEGIN/END FLUX --> block from docs
- This setup is optional - plugin works without it
```

### What to do next (always print at the end, visually separated from summary)

Print this **exactly** after the summary block, with a blank line before it:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

What to do next:

  1. Restart Claude Code with `--resume` (required for new MCP servers to activate)
  2. Run /flux:prime — this audits the repo for agent-readiness and inefficiencies. It only runs once.

After prime completes, the core loop is:
  /flux:scope → /flux:work → /flux:impl-review → /flux:improve

End each session with /flux:reflect to capture learnings.
```

---

## Uninstall Flow

When the user asks to uninstall Flux, follow this flow. The goal is to let them choose exactly what to remove.

### Step U1: Read the install manifest

```bash
MANIFEST=$(jq -r '.installed_by_flux // empty' .flux/meta.json 2>/dev/null)
```

If `.flux/meta.json` has no `installed_by_flux` field (older install), skip to Step U3 and only offer core Flux removal.

### Step U2: Ask what to remove

Present each category that has items, and let the user choose per-category. Use the question tool:

```json
{
  "header": "Uninstall Flux",
  "question": "Flux installed these items during setup. Which do you want to remove? (Flux core files are always removed)",
  "multiple": true,
  "options": [
    {"label": "MCP servers", "description": "<list from manifest, e.g. Firecrawl, Exa>"},
    {"label": "Agent skills", "description": "<list from manifest, e.g. UI Skills, Taste Skill>"},
    {"label": "Desktop apps", "description": "<list from manifest, e.g. Raycast, Ghostty> (manual uninstall instructions)"},
    {"label": "CLI tools", "description": "<list from manifest, e.g. jq, fzf> (manual uninstall instructions)"},
    {"label": "Just remove Flux core", "description": "Only remove .flux/, plugin, and CLAUDE.md section"}
  ]
}
```

### Step U3: Remove Flux core (always)

```bash
# Remove Flux plugin
# Tell user to run: /plugin remove flux@nairon-flux

# Remove project artifacts
rm -rf .flux

# Remove CLAUDE.md / AGENTS.md flux section
# Strip everything between <!-- BEGIN FLUX --> and <!-- END FLUX --> (inclusive)
```

### Step U4: Remove selected extras

**MCP servers** (if selected):
For each MCP server in the manifest, remove its entry from `~/.claude/settings.json` under `mcpServers`.

**Agent skills** (if selected):
```bash
# Remove each skill directory
rm -rf ~/.claude/skills/<skill-name>
```

Map skill names to directories:
- `ui-skills` → `~/.claude/skills/baseline-ui`, `~/.claude/skills/fixing-accessibility`, etc.
- `taste-skill` → `~/.claude/skills/taste-skill`
- `agent-skills-vercel` → `~/.claude/skills/agent-skills-vercel`
- `x-research-skill` → `~/.claude/skills/x-research-skill`

**Desktop apps** (if selected):
Cannot auto-uninstall GUI apps. Print manual instructions:
```
To uninstall desktop apps, use your OS app removal method:
- macOS: drag from /Applications to Trash, or use AppCleaner
- <list each app that was installed>
```

**CLI tools** (if selected):
Print uninstall commands for each:
```bash
# Examples — adapt based on what was installed
brew uninstall gh        # GitHub CLI
brew uninstall jq
brew uninstall fzf
brew uninstall lefthook
# etc.
```

### Step U5: Confirm

```
Flux has been uninstalled.

Removed:
- Flux plugin (run /plugin remove flux@nairon-flux to complete)
- .flux/ directory
- CLAUDE.md / AGENTS.md flux sections
- <list any extras that were removed>

Kept:
- <list any extras the user chose to keep>

Restart Claude Code with `--resume` for changes to take effect.
```
