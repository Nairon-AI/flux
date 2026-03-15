---
name: flux-upgrade
description: Upgrade Flux to the latest version. Refreshes marketplace metadata, clears plugin cache, and updates the install record. Triggers on /flux:upgrade.
user-invocable: true
---

# Upgrade Flux

Upgrades the Flux plugin to the latest version from GitHub. Handles all three layers of the plugin cache that Claude Code maintains.

## What This Does

Claude Code's plugin system has three separate caches that must all agree:

1. **Marketplace metadata** (`~/.claude/plugins/marketplaces/nairon-flux/`) — git clone with marketplace.json
2. **Plugin code cache** (`~/.claude/plugins/cache/nairon-flux/`) — extracted plugin files, keyed by version
3. **Install record** (`~/.claude/plugins/installed_plugins.json`) — tracks which version + path is active

The built-in "Update" button often only refreshes #1 but not #2 or #3, leaving the plugin stuck on the old version. This skill fixes all three.

**Project-local files are never touched**: `.flux/`, brain vault, CLAUDE.md, MCP servers, `.mcp.json` — all untouched.

## Workflow

### Step 1: Record current version

```bash
INSTALLED_JSON="$HOME/.claude/plugins/installed_plugins.json"
OLD_VERSION=$(jq -r '.plugins["flux@nairon-flux"][0].version // "unknown"' "$INSTALLED_JSON" 2>/dev/null || echo "unknown")
echo "Current version: $OLD_VERSION"
```

### Step 2: Refresh marketplace metadata

Pull the latest from the Flux repo so the marketplace knows the current version:

```bash
MARKETPLACE_DIR="$HOME/.claude/plugins/marketplaces/nairon-flux"
if [ -d "$MARKETPLACE_DIR/.git" ]; then
  git -C "$MARKETPLACE_DIR" fetch origin main --quiet 2>&1
  git -C "$MARKETPLACE_DIR" reset --hard origin/main --quiet 2>&1
  echo "Marketplace refreshed via git pull"
else
  # Marketplace dir missing or not a git repo — re-add it
  claude plugin marketplace add https://github.com/Nairon-AI/flux 2>&1
  echo "Marketplace re-added"
fi
```

### Step 3: Read new version from marketplace

```bash
MARKETPLACE_DIR="$HOME/.claude/plugins/marketplaces/nairon-flux"
NEW_VERSION=$(jq -r '.plugins[0].version' "$MARKETPLACE_DIR/.claude-plugin/marketplace.json" 2>/dev/null || echo "unknown")
echo "Latest version: $NEW_VERSION"
```

If `NEW_VERSION` equals `OLD_VERSION`, tell the user they're already on the latest and stop here.

### Step 4: Clear old plugin code cache

```bash
rm -rf "$HOME/.claude/plugins/cache/nairon-flux"
echo "Plugin cache cleared"
```

### Step 5: Update install record

Update `installed_plugins.json` so Claude Code loads the new version on restart:

```bash
INSTALLED_JSON="$HOME/.claude/plugins/installed_plugins.json"
MARKETPLACE_DIR="$HOME/.claude/plugins/marketplaces/nairon-flux"
NEW_VERSION=$(jq -r '.plugins[0].version' "$MARKETPLACE_DIR/.claude-plugin/marketplace.json")
CACHE_DIR="$HOME/.claude/plugins/cache/nairon-flux/flux/$NEW_VERSION"
NOW=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")
SHA=$(git -C "$MARKETPLACE_DIR" rev-parse HEAD 2>/dev/null || echo "")

jq --arg v "$NEW_VERSION" \
   --arg p "$CACHE_DIR" \
   --arg t "$NOW" \
   --arg s "$SHA" \
   '.plugins["flux@nairon-flux"][0].version = $v |
    .plugins["flux@nairon-flux"][0].installPath = $p |
    .plugins["flux@nairon-flux"][0].lastUpdated = $t |
    .plugins["flux@nairon-flux"][0].gitCommitSha = $s' \
   "$INSTALLED_JSON" > "${INSTALLED_JSON}.tmp" && mv "${INSTALLED_JSON}.tmp" "$INSTALLED_JSON"

echo "Install record updated to $NEW_VERSION"
```

### Step 6: Report result

Show the user what happened:

```
✅ Flux upgraded: v{OLD_VERSION} → v{NEW_VERSION}
Restart Claude Code to load the new version (use --resume to keep context).
Your project setup (.flux/, brain vault, CLAUDE.md) was not modified.
```
