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

## Step 4c: Install recommended MCP servers (Optional)

Flux recommends MCP servers that enhance your AI development workflow. Installation is **optional** — users can skip or select which ones to install.

### Available MCP Servers

<!-- 
  TO ADD A NEW MCP/SKILL/TOOL:
  1. Add entry to the RECOMMENDED_MCPS table below
  2. Add conflict detection in "Detect conflicts"
  3. Add option to the question in "Ask which to install"
  4. Add installation logic in "Install selected servers"
  5. Add API key question if applicable (for MCPs with optional keys)
-->

| ID | Name | Category | Benefit | Free | Install Command |
|----|------|----------|---------|------|-----------------|
| `context7` | Context7 | search | **No more hallucinated APIs** — up-to-date, version-specific library docs in every prompt | Yes | `claude mcp add --transport http context7 https://mcp.context7.com/mcp -s user` |
| `exa` | Exa | search | **Fastest AI web search** — real-time research without leaving your session | Yes | `claude mcp add --transport http exa https://mcp.exa.ai/mcp -s user` |
| `github` | GitHub | dev | **PRs, issues, actions in Claude** — no context switching to browser | Yes | `claude mcp add github -s user -- npx -y @modelcontextprotocol/server-github` |
| `supermemory` | Supermemory | memory | **Never re-explain context** — persistent memory across all sessions | Yes | `claude mcp add --transport http supermemory https://mcp.supermemory.ai/mcp -s user` |

### Conflict Detection

Before offering to install, detect potential conflicts with existing tools:

```bash
# Get installed MCPs
MCP_LIST=$(claude mcp list 2>/dev/null || echo "")

# Check each recommended MCP
HAVE_CONTEXT7=$(echo "$MCP_LIST" | grep -qi "context7" && echo 1 || echo 0)
HAVE_EXA=$(echo "$MCP_LIST" | grep -qi "exa" && echo 1 || echo 0)
HAVE_GITHUB=$(echo "$MCP_LIST" | grep -qi "github" && echo 1 || echo 0)
HAVE_SUPERMEMORY=$(echo "$MCP_LIST" | grep -qi "supermemory" && echo 1 || echo 0)

# Detect conflicting/similar tools
# Search category conflicts
HAVE_PERPLEXITY=$(echo "$MCP_LIST" | grep -qi "perplexity" && echo 1 || echo 0)
HAVE_TAVILY=$(echo "$MCP_LIST" | grep -qi "tavily" && echo 1 || echo 0)
HAVE_BRAVE=$(echo "$MCP_LIST" | grep -qi "brave" && echo 1 || echo 0)
HAVE_SERPER=$(echo "$MCP_LIST" | grep -qi "serper" && echo 1 || echo 0)

# Memory category conflicts
HAVE_MEM0=$(echo "$MCP_LIST" | grep -qi "mem0" && echo 1 || echo 0)
HAVE_LANGMEM=$(echo "$MCP_LIST" | grep -qi "langmem\|langchain.*memory" && echo 1 || echo 0)

# Docs category conflicts  
HAVE_DEVDOCS=$(echo "$MCP_LIST" | grep -qi "devdocs" && echo 1 || echo 0)

# GitHub conflicts (check for gh CLI too)
HAVE_GH_CLI=$(which gh >/dev/null 2>&1 && echo 1 || echo 0)
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
  "question": "Flux recommends these free MCP servers. Which would you like to install?",
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
claude mcp remove perplexity -s user 2>/dev/null || true
claude mcp add --transport http exa https://mcp.exa.ai/mcp -s user
```

### Install selected servers

For each selected server (that passed conflict resolution), install it:

**Context7:**
```bash
claude mcp add --transport http context7 https://mcp.context7.com/mcp -s user 2>/dev/null || true
```

**Exa:**
```bash
claude mcp add --transport http exa https://mcp.exa.ai/mcp -s user 2>/dev/null || true
```

**GitHub:**
```bash
# Requires GITHUB_PERSONAL_ACCESS_TOKEN - ask user if they want to configure
claude mcp add github -s user -- npx -y @modelcontextprotocol/server-github 2>/dev/null || true
```

**Supermemory:**
```bash
claude mcp add --transport http supermemory https://mcp.supermemory.ai/mcp -s user 2>/dev/null || true
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
claude mcp remove github 2>/dev/null || true
claude mcp add github -s user -e GITHUB_PERSONAL_ACCESS_TOKEN="<user_provided_token>" -- npx -y @modelcontextprotocol/server-github
```

**Context7 / Exa / Supermemory API keys:**

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
    {"label": "Skip", "description": "Use free tier for all (can add keys later)"}
  ]
}
```

### Track installation results

Store for summary:
- `INSTALLED_MCPS` — list of MCP names installed this session
- `REMOVED_MCPS` — list of MCPs removed due to switch
- `CONFIGURED_TOKENS` — list of MCPs with tokens/keys configured
- `SKIPPED_MCPS` — list of MCPs user chose to skip
- `CONFLICTS_RESOLVED` — list of conflict resolutions made

### Manual fallback

If `claude` CLI is not available, print manual instructions:

```
MCP servers (install manually with Claude Code):
  claude mcp add --transport http context7 https://mcp.context7.com/mcp -s user
  claude mcp add --transport http exa https://mcp.exa.ai/mcp -s user
  claude mcp add --transport http supermemory https://mcp.supermemory.ai/mcp -s user
  claude mcp add github -s user -- npx -y @modelcontextprotocol/server-github
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
| `wispr-flow` | Wispr Flow | Yes | No | No | **Voice-to-text 4x faster** — dictate anywhere | Freemium | Manual download |
| `granola` | Granola | Yes | No | Yes | **AI meeting notes** — no bot joins calls | Freemium | Manual download |

### OS Compatibility Matrix

```
macOS:   Raycast, Ghostty, Wispr Flow, Granola (all 4)
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

### Ask which to install (OS-specific questions)

**For macOS users** (all 4 apps available):

```json
{
  "header": "Desktop Apps (macOS)",
  "question": "Flux recommends these productivity apps. Which would you like to install?",
  "multiple": true,
  "options": [
    // Only include apps NOT already installed
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

| ID | Name | Benefit | Free | Install (macOS) | Install (Linux) |
|----|------|---------|------|-----------------|-----------------|
| `gh` | GitHub CLI | **PRs, issues, releases from terminal** — no browser context switching | Yes | `brew install gh` | `sudo apt install gh` |

### Detect existing tools

```bash
# Check if tools already installed
HAVE_GH_CLI=$(which gh >/dev/null 2>&1 && echo 1 || echo 0)

# gh CLI complements (not conflicts with) GitHub MCP
# If user installed GitHub MCP in step 4c, recommend gh CLI as complement
```

### Ask which to install

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

**Option templates:**
```json
{"label": "GitHub CLI (gh)", "description": "PRs, issues, releases from terminal — complements GitHub MCP (free)"}
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

**If gh is already installed:**
Skip this question or show "already installed" in summary.

### Install selected tools

**GitHub CLI:**
```bash
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
  echo "Install: winget install --id GitHub.cli"
fi

# Prompt for authentication if installed
if which gh >/dev/null 2>&1; then
  echo "Run 'gh auth login' to authenticate with GitHub"
fi
```

### Track installation results

Store for summary:
- `INSTALLED_CLI` — list of CLI tools installed this session
- `SKIPPED_CLI` — list of CLI tools user chose to skip

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
```

**MCP servers section** (only show if any were installed, removed, or already existed):

```
MCP servers:
- Context7: <installed | installed + key | already installed | skipped>
- Exa: <installed | installed + key | already installed | skipped>
- GitHub: <installed | installed + token | already installed | skipped>
- Supermemory: <installed | installed + key | already installed | skipped>
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
- Wispr Flow: <installed | already installed | skipped>
- Granola: <installed | already installed | skipped>
```

Use tracking variables from Step 4d to determine status. Only show apps compatible with user's OS:
- macOS: show all 4 apps
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
```

Use tracking variables from Step 4e. If gh was already installed before setup, show "already installed".

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
- MCP servers installed at user scope are available in all projects
- Desktop apps and CLI tools are optional productivity boosters
- Uninstall (run manually): rm -rf .flux/bin .flux/usage.md and remove <!-- BEGIN/END FLUX --> block from docs
- This setup is optional - plugin works without it
```
