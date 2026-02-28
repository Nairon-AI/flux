---
name: flux-rp-explorer
description: Token-efficient codebase exploration using RepoPrompt CLI. Use when user says "use rp to..." or "use repoprompt to..." followed by explore, find, understand, search, or similar actions.
---

# RP-Explorer

Token-efficient codebase exploration using RepoPrompt CLI.

## Trigger Phrases

Activates when user combines "use rp" or "use repoprompt" with an action:
- "use rp to explore how auth works"
- "use repoprompt to find similar patterns"
- "use rp to understand the data flow"
- "use repoprompt to search for API endpoints"

## CLI Reference

Read [cli-reference.md](cli-reference.md) for complete command documentation.

## Quick Start

### Step 1: Get Overview
```bash
rp-cli -e 'tree'
rp-cli -e 'structure .'
```

### Step 2: Find Relevant Files
```bash
rp-cli -e 'search "auth" --context-lines 2'
rp-cli -e 'builder "understand authentication"'
```

### Step 3: Deep Dive
```bash
rp-cli -e 'select set src/auth/'
rp-cli -e 'structure --scope selected'
rp-cli -e 'read src/auth/login.ts'
```

### Step 4: Export Context
```bash
rp-cli -e 'context --all > codebase-map.md'
```

## Token Efficiency

- Use `structure` instead of reading full files (10x fewer tokens)
- Use `builder` for AI-powered file discovery
- Select only relevant files before exporting context

## Tab Isolation

`builder` creates an isolated compose tab automatically. Use `-t` to target it:
```bash
# Builder returns: Tab: <UUID> • <Name>
rp-cli -w W -t "<Name>" -e 'select add extra.ts && context'

# Or chain commands:
rp-cli -w W -e 'builder "find auth" && select add extra.ts && context'
```

## Requirements

RepoPrompt v1.5.62+ with rp-cli installed.


---

## Update Check (End of Command)

**ALWAYS run at the very end of command execution:**

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}"
[ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
UPDATE_JSON=$("$PLUGIN_ROOT/scripts/version-check.sh" 2>/dev/null || echo '{"update_available":false}')
UPDATE_AVAILABLE=$(echo "$UPDATE_JSON" | jq -r '.update_available')
LOCAL_VER=$(echo "$UPDATE_JSON" | jq -r '.local_version')
REMOTE_VER=$(echo "$UPDATE_JSON" | jq -r '.remote_version')
```

**If update available**, append to output:

```
---
Flux update available: v${LOCAL_VER} → v${REMOTE_VER}
Run: /plugin marketplace update nairon-flux
Then restart Claude Code for changes to take effect.
---
```
