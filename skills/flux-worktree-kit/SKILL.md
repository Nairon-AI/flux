---
name: flux-worktree-kit
description: Manage git worktrees (create/list/switch/cleanup) and copy .env files. Use for parallel feature work, isolated review, clean workspace, or when user mentions worktrees.
---

# Worktree kit

Use the manager script for all worktree actions.

```bash
bash ${PLUGIN_ROOT}/skills/flux-worktree-kit/scripts/worktree.sh <command> [args]
```

Commands:
- `create <name> [base]`
- `list`
- `switch <name>` (prints path)
- `cleanup`
- `copy-env <name>`

Safety notes:
- `create` does not change the current branch
- `cleanup` does not force-remove worktrees and does not delete branches
- `cleanup` deletes the worktree directory (including ignored files); removal fails if the worktree is not clean
- `.env*` is copied with no overwrite (symlinks skipped)
- refuses to operate if `.worktrees/` or any worktree path component is a symlink
- `copy-env` only targets registered worktrees
- `origin` fetch is optional; local base refs are allowed
- fetch from `origin` only when base looks like a branch
- Worktrees live under `.worktrees/`


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
