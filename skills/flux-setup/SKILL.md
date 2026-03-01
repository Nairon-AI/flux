---
name: flux-setup
description: Optional local install of fluxctl CLI and CLAUDE.md/AGENTS.md instructions. Use when user runs /flux:setup.
user-invocable: false
---

# Flux Setup (Optional)

Install fluxctl locally and add instructions to project docs. **Fully optional** - flux works without this via the plugin.

## Benefits

- `fluxctl` accessible from command line (add `.flux/bin` to PATH)
- Other AI agents (Codex, Cursor, etc.) can read instructions from CLAUDE.md/AGENTS.md
- Works without Claude Code plugin installed
- Installs `claudeception` by default (if missing) for continuous learning
- Installs recommended MCP servers:
  - **Context7** — up-to-date library documentation (no more hallucinated APIs)
  - **Exa** — fast, accurate web search for real-time research

## Workflow

Read [workflow.md](workflow.md) and follow each step in order.

## Notes

- **Fully optional** - standard plugin usage works without local setup
- Copies scripts (not symlinks) for portability across environments
- Safe to re-run - will detect existing setup and offer to update

---

## Update Check (End of Command)

**ALWAYS run at the very end of /flux:setup execution:**

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
