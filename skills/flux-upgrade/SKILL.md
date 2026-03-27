---
name: flux-upgrade
description: Use when upgrading Flux itself after a new release or when legacy plugin metadata/cache drift leaves Flux on an older version. Refresh marketplace metadata, clear plugin cache, update the install record, and route `/flux:upgrade`.
user-invocable: true
---

# Upgrade Flux

Upgrades the Flux plugin to the latest version from GitHub. Handles all three layers of the plugin cache, shows the user what changed, and tells them exactly what to do next.

## What This Does

Flux's legacy plugin packaging has three separate caches that must all agree:

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

Save `OLD_VERSION` — you'll need it for the changelog summary later.

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

Update `installed_plugins.json` so the legacy plugin install loads the new version on restart:

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

### Step 6: Fetch what changed (release notes)

This is the key step that makes the upgrade feel useful. Fetch GitHub release notes for every version between `OLD_VERSION` and `NEW_VERSION`:

```bash
# Get all releases between old and new version
gh release list --repo Nairon-AI/flux --limit 30 --json tagName,name,body,publishedAt 2>/dev/null
```

From the JSON output, filter to only releases where the tag (stripped of `v` prefix) is:
- Greater than `OLD_VERSION`
- Less than or equal to `NEW_VERSION`

Use semver comparison (`sort -V`) to determine which releases fall in range.

If `gh` is not available or the API call fails, fall back to reading `CHANGELOG.md` from the marketplace dir:

```bash
MARKETPLACE_DIR="$HOME/.claude/plugins/marketplaces/nairon-flux"
cat "$MARKETPLACE_DIR/CHANGELOG.md"
```

Parse the changelog to extract entries between the old and new version headers.

### Step 7: Build the "What's New" summary

From the release notes or changelog entries gathered in Step 6, produce a **concise, non-technical summary** of what improved. This is what the user actually cares about.

**Rules for the summary:**
- Lead with benefits, not implementation details
- Group changes into 2-4 themes max (e.g., "Better planning", "New security scanning", "Faster setup")
- Each theme gets 1-2 sentences explaining the value
- Skip version bump PRs, CI fixes, and internal refactors — they don't matter to the user
- Skip individual file changes — the user doesn't care which `.md` was edited
- If a new skill/command was added, name it and say what it does in one line
- If something was fixed, say what was broken and that it's now fixed

**Output format:**

```
## What's new since v{OLD_VERSION}

**[Theme 1 — e.g., "Smarter scoping"]**
[1-2 sentences on the benefit. Example: "The /flux:scope command now tracks your progress
through each phase, so you can pick up where you left off after a restart."]

**[Theme 2 — e.g., "Built-in code maps"]**
[1-2 sentences. Example: "Flux now generates project structure maps natively — no need to
install the separate agentmap CLI anymore."]

**[Theme 3 — e.g., "Bug fixes"]**  *(only if meaningful fixes)*
[Brief description of what was broken and that it works now.]
```

If only one version was skipped and changes are minor, a single paragraph is fine — no need for themes.

### Step 8: Check if setup needs re-run

Compare the new plugin version to `setup_version` in `.flux/meta.json`:

```bash
SETUP_VER=$(jq -r '.setup_version // "none"' .flux/meta.json 2>/dev/null || echo "none")
echo "Setup version: $SETUP_VER"
echo "Plugin version: $NEW_VERSION"
```

Determine whether `/flux:setup` needs to be re-run. This depends on **what changed**, not just version drift:

**Setup re-run IS needed when** (check changelog/release notes for these):
- New MCP servers were added to the setup menu
- New CLI tools or desktop apps were added to the setup menu
- New skills became installable through setup
- CLAUDE.md markers or instructions format changed
- fluxctl got new subcommands that need PATH setup
- The `.flux/` directory structure changed (new directories, renamed files)

**Setup re-run is NOT needed when** (most upgrades):
- Only skills/commands within the plugin changed (these load from the plugin, not `.flux/`)
- Bug fixes to existing behavior
- Release process or CI improvements
- Documentation-only changes
- New plugin-only features (like `/flux:score`, `/flux:security-scan`)

**How to determine this**: Scan the release notes/changelog entries from Step 6. Look for mentions of `/flux:setup`, `CLAUDE.md`, `fluxctl`, `.flux/bin`, `meta.json`, MCP, CLI tool, desktop app, or skill install changes. If none are found, setup re-run is NOT needed.

### Step 9: Report result

Present the full upgrade report to the user. The format adapts based on what happened:

**Always show:**

```
Flux upgraded: v{OLD_VERSION} → v{NEW_VERSION}
```

**Then show the "What's New" summary from Step 7.**

**Then show next steps:**

If setup re-run IS needed:
```
## What to do now

1. Restart your agent session to load the new version
   (use `--resume` to keep your current context)

2. After restart, run `/flux:setup` to pick up new options:
   [1-line explanation of what's new in setup, e.g., "New Expect browser QA tool
   and X Research skill are now available in the setup menu."]

Your existing project files (.flux/, brain vault, CLAUDE.md) were not modified.
Setup will only add new options — it won't change anything you've already configured.
```

If setup re-run is NOT needed:
```
## What to do now

Restart your agent session to load the new version.
(Use `--resume` to keep your current context.)

That's it — no need to re-run `/flux:setup`. All changes in this
upgrade are plugin-level and will be active after restart.
Your project files (.flux/, brain vault, CLAUDE.md) were not modified.
```

If already on latest (from Step 3):
```
You're already on the latest version (v{OLD_VERSION}).
No upgrade needed.
```

## Gotchas

- Upgrade is not complete until Claude restarts and reloads the plugin. Clearing cache without restart still leaves the running session on the old code.
- `setup_version` drift does NOT always mean re-run is needed. Only recommend re-running setup when the changelog shows setup-relevant changes. False "re-run setup" warnings erode trust.
- The `gh` CLI is the preferred source for release notes (richer content). Fall back to CHANGELOG.md only when `gh` is unavailable or fails.
- This skill is for Flux/plugin upgrades, not for upgrading arbitrary project dependencies.
- If `OLD_VERSION` is "unknown" (first-time or corrupted state), skip the changelog diff and just show the latest release notes as the summary.
