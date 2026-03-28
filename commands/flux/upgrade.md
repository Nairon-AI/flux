---
name: flux:upgrade
description: Upgrade Flux and optionally refresh project setup
---

# Flux Upgrade

Upgrades Flux, shows the user what changed since their version, and tells them exactly what to do next.

## Step 1: Check current versions

Run the version check to see where things stand:

```bash
bash "${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || dirname "$(dirname "$(dirname "$0")")")}}/scripts/version-check.sh"
```

Parse the JSON output. Save `local_version` as `OLD_VERSION` — you'll need it later.

Report to the user:
- Current version: `local_version`
- Latest version: `remote_version`

If no update is available, tell the user they're on the latest version and stop.

## Step 2: Upgrade the plugin

Follow the SKILL.md workflow Steps 2-5 to refresh marketplace metadata, clear plugin cache, and update the install record. This is the mechanical upgrade.

If any step fails, report the specific error and stop. Do not continue with a partial upgrade.

## Step 3: Fetch what changed

This step is what makes the upgrade informative. Get release notes for every version between `OLD_VERSION` and the new version.

**Primary source — GitHub releases:**

```bash
gh release list --repo Nairon-AI/flux --limit 30 --json tagName,name,body,publishedAt 2>/dev/null
```

Filter to releases where the tag version is greater than `OLD_VERSION` and less than or equal to the new version.

**Fallback — CHANGELOG.md from legacy marketplace dir:**

```bash
MARKETPLACE_DIR="$HOME/.claude/plugins/marketplaces/nairon-flux"
cat "$MARKETPLACE_DIR/CHANGELOG.md"
```

Parse entries between the old and new version headers.

## Step 4: Build the "What's New" summary

From the release notes, produce a concise, non-technical summary. The user wants to know **why this upgrade was worth it**, not what files changed.

**Rules:**
- Group into 2-4 themes max (e.g., "Better planning", "New security tools")
- Each theme: 1-2 sentences on the benefit
- Skip version bumps, CI fixes, internal refactors
- If a new skill/command was added, name it and say what it does in one line
- If something was fixed, say what was broken and that it works now

**Format:**

```
## What's new since v{OLD_VERSION}

**[Theme]** — [1-2 sentence benefit]

**[Theme]** — [1-2 sentence benefit]
```

If changes are minor (one patch version), a single short paragraph is fine.

## Step 5: Determine if `/flux:setup` needs re-running

Scan the release notes/changelog for setup-relevant changes. This is NOT a blind version comparison — it's a content-based decision.

**Re-run IS needed when the changelog mentions:**
- New MCP servers, CLI tools, desktop apps, or skills added to the setup menu
- AGENTS.md / legacy CLAUDE.md markers or instruction format changes
- fluxctl new subcommands requiring PATH setup
- `.flux/` directory structure changes

**Re-run is NOT needed when** (most upgrades):
- Only plugin-level skills/commands changed
- Bug fixes, docs changes, CI improvements
- New plugin-only features (e.g., `/flux:score`)

## Step 6: Report to the user

Present a clean upgrade report:

```
Flux upgraded: v{OLD_VERSION} → v{NEW_VERSION}
```

Then the "What's New" summary from Step 4.

Then next steps — adapt based on Step 5:

**If setup re-run IS needed:**

```
## What to do now

1. Restart your agent session to load the new version

2. After restart, run /flux:setup to pick up new options:
   [1-line explanation of what's new in setup]

Your existing project files were not modified.
Setup will only offer new options — nothing you've configured will change.
```

**If setup re-run is NOT needed:**

```
## What to do now

Restart your agent session to load the new version.

That's it — no need to re-run /flux:setup.
All changes in this upgrade are plugin-level and activate after restart.
```

## Step 7 (optional): Batch project upgrade

If the user asks to upgrade multiple projects, or if you detect this is relevant:

### Scan for Flux projects

```bash
find ~/Developer ~/Projects ~/Code ~/repos ~/src ~/work ~/Desktop ~ -maxdepth 4 -name ".flux" -type d 2>/dev/null | while read flux_dir; do
  project_dir="$(dirname "$flux_dir")"
  version="unknown"
  if [[ -f "$flux_dir/meta.json" ]]; then
    version=$(jq -r '.setup_version // "unknown"' "$flux_dir/meta.json" 2>/dev/null)
  fi
  echo "$project_dir|$version"
done | sort -u | head -30
```

Present the list and ask which to upgrade. For each selected project, update `.flux/bin/` scripts and `AGENTS.md` / legacy `CLAUDE.md` markers only. **Never touch** `.flux/tasks/`, `.flux/epics/`, `.flux/preferences.json`, `.mcp.json`, or user data.

Report per-project results and flag any failures for manual follow-up.
