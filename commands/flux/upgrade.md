---
name: flux:upgrade
description: Upgrade Flux plugin and optionally update project setup
---

# Flux Upgrade

## Step 1: Check current versions

Run the version check to see where things stand:

```bash
bash "${CLAUDE_PLUGIN_ROOT:-${DROID_PLUGIN_ROOT:-$(dirname "$(dirname "$(dirname "$0")")")}}/scripts/version-check.sh"
```

Parse the JSON output. Report to the user:
- Local version: `local_version`
- Remote version: `remote_version`
- Update available: `update_available`

If no update is available, tell the user they're on the latest version.

## Step 2: Ask scope

Use `AskUserQuestion`:

**"How do you want to upgrade?"**
- "This project only" → upgrade plugin + re-run setup on current project
- "All Flux projects on this machine" → upgrade plugin + scan and update all projects
- "Plugin only (no project changes)" → just update the plugin, skip setup

## Step 3: Upgrade the plugin

```bash
/plugin add https://github.com/Nairon-AI/flux@latest
```

Tell the user:
> Plugin upgraded. You'll need to restart with `--resume` for the new plugin to take effect.
> After restarting, run `/flux:setup` to update this project's local files.

If the user chose **"Plugin only"**, stop here.

## Step 4: Re-run project setup

If the user chose **"This project only"**:
- Run `/flux:setup` which handles the upgrade path via `setup_version` comparison in `.flux/meta.json`
- This is idempotent — it merges new config keys, copies updated skills, and refreshes CLAUDE.md markers

If the user chose **"All Flux projects on this machine"**:

### Step 4a: Scan for Flux projects

```bash
# Find all directories with .flux/ on the machine
find ~/Developer ~/Projects ~/Code ~/repos ~/src ~/work ~/Desktop ~ -maxdepth 4 -name ".flux" -type d 2>/dev/null | while read flux_dir; do
  project_dir="$(dirname "$flux_dir")"
  version="unknown"
  if [[ -f "$flux_dir/meta.json" ]]; then
    version=$(jq -r '.setup_version // "unknown"' "$flux_dir/meta.json" 2>/dev/null)
  fi
  echo "$project_dir|$version"
done | sort -u | head -30
```

Present the list:

```
Found Flux in these projects:

  Project                          Setup Version
  /Users/you/project-a             v2.9.0
  /Users/you/project-b             v2.10.1
  /Users/you/test-repo             v2.10.1-dev

Select which to upgrade, or "all".
```

Use `AskUserQuestion`:
- "Upgrade all of them"
- "Let me pick" → show list, let user select
- "Cancel — just this project"

### Step 4b: Batch upgrade

For each selected project, report what will happen:

```
Upgrading /Users/you/project-a (v2.9.0 → v2.11.0)...
  - Updating .flux/bin/ scripts
  - Merging new config keys into .flux/config.json
  - Refreshing CLAUDE.md flux markers
  ✓ Done

Upgrading /Users/you/project-b (v2.10.1 → v2.11.0)...
  - Updating .flux/bin/ scripts
  - Merging new config keys into .flux/config.json
  - No CLAUDE.md changes needed
  ✓ Done
```

For each project, run the equivalent of `fluxctl init --json` in that directory, then copy updated bin scripts and refresh the CLAUDE.md markers. Do NOT touch `.flux/tasks/`, `.flux/epics/`, `.flux/preferences.json`, or any user data.

**Important:** The batch upgrade only updates Flux infrastructure files. It never modifies:
- `.flux/tasks/` or `.flux/epics/` (user work)
- `.flux/preferences.json` (user preferences)
- `.mcp.json` (project-specific MCP config — may differ per project)
- `.claude/skills/` installed from other sources

## Step 5: Report

```
Flux upgrade complete.

Plugin: v2.10.1 → v2.11.0
Projects updated: 3/3

Next steps:
- Restart Claude Code with --resume to load the new plugin
- Skills and config are already updated in each project
```

If any project failed, list it with the error so the user can fix manually.
