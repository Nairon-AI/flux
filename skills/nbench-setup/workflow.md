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

## Step 3: Create .flux/bin/

```bash
mkdir -p .flux/bin
```

## Step 4: Copy files

**IMPORTANT: Do NOT read fluxctl.py - it's too large. Just copy it.**

Copy using Bash `cp` with absolute paths:

```bash
cp "${PLUGIN_ROOT}/scripts/fluxctl" .flux/bin/fluxctl
cp "${PLUGIN_ROOT}/scripts/fluxctl.py" .flux/bin/fluxctl.py
chmod +x .flux/bin/fluxctl
```

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
    {"label": "Yes", "description": "Search GitHub repos for patterns/examples during /nbench:plan"}
  ],
  "multiSelect": false
}
```

**Scout Model question** (include if CURRENT_SCOUT_MODEL is empty):
```json
{
  "header": "Scout Model",
  "question": "Which model should scout agents use? (Scouts analyze your codebase during /nbench:prime)",
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
  2. If available, run: `gh api -X PUT /user/starred/Nairon-AI/n-bench`
  3. If `gh` not available or command fails, show: `Star manually: https://github.com/Nairon-AI/n-bench`

## Step 8: Print Summary

```
Flux setup complete!

Installed:
- .flux/bin/fluxctl (v<VERSION>)
- .flux/bin/fluxctl.py
- .flux/usage.md

To use from command line:
  export PATH=".flux/bin:$PATH"
  fluxctl --help

Configuration (use fluxctl config set to change):
- Memory: <enabled|disabled>
- Plan-Sync: <enabled|disabled>
- Plan-Sync cross-epic: <enabled|disabled>
- GitHub scout: <enabled|disabled>
- Scout model: <claude-haiku-4-5|gpt-5.3-codex-spark>
- Review backend: <codex|rp|none>

Documentation updated:
- <files updated or "none">

Notes:
- Re-run /nbench:setup after plugin updates to refresh scripts
- Interested in autonomous mode? Run /nbench:ralph-init
- Default skill bootstrap: claudeception (installed if missing)
- Uninstall (run manually): rm -rf .flux/bin .flux/usage.md and remove <!-- BEGIN/END FLUX --> block from docs
- This setup is optional - plugin works without it
```
