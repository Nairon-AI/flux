---
name: flux-ralph-init
description: Scaffold repo-local Ralph autonomous harness under scripts/ralph/. Use when user runs /flux:ralph-init.
user-invocable: false
---

# Ralph init

Scaffold or update repo-local Ralph harness. Opt-in only.

## Rules

- Only create/update `scripts/ralph/` in the current repo.
- If `scripts/ralph/` already exists, offer to update (preserves config.env).
- Copy templates from `templates/` into `scripts/ralph/`.
- Copy `fluxctl` and `fluxctl.py` from `${PLUGIN_ROOT}/scripts/` into `scripts/ralph/`.
- Set executable bit on `scripts/ralph/ralph.sh`, `scripts/ralph/ralph_once.sh`, and `scripts/ralph/fluxctl`.

## Workflow

1. Resolve repo root: `git rev-parse --show-toplevel`

2. Check if `scripts/ralph/` exists:
   - If exists: ask "Update existing Ralph setup? (preserves config.env and runs/) [y/n]"
     - If no: stop
     - If yes: set UPDATE_MODE=1
   - If not exists: set UPDATE_MODE=0

3. Detect available review backends (skip if UPDATE_MODE=1):
   ```bash
   HAVE_RP=$(which rp-cli >/dev/null 2>&1 && echo 1 || echo 0)
   HAVE_CODEX=$(which codex >/dev/null 2>&1 && echo 1 || echo 0)
   ```

4. Determine review backend (skip if UPDATE_MODE=1):
   - If BOTH available, ask user (do NOT use AskUserQuestion tool):
     ```
     Both RepoPrompt and Codex available. Which review backend?
     a) RepoPrompt (macOS, visual builder)
     b) Codex CLI (cross-platform, GPT 5.2 High)

     (Reply: "a", "rp", "b", "codex", or just tell me)
     ```
     Wait for response. Default if empty/ambiguous: `rp`
   - If only rp-cli available: use `rp`
   - If only codex available: use `codex`
   - If neither available: use `none`

5. Copy files using bash (MUST use cp, NOT Write tool):

   **If UPDATE_MODE=1 (updating):**
   ```bash
   # Backup config.env
   cp scripts/ralph/config.env /tmp/ralph-config-backup.env

   # Update templates (preserves runs/)
   cp "${PLUGIN_ROOT}/skills/flux-ralph-init/templates/ralph.sh" scripts/ralph/
   cp "${PLUGIN_ROOT}/skills/flux-ralph-init/templates/ralph_once.sh" scripts/ralph/
   cp "${PLUGIN_ROOT}/skills/flux-ralph-init/templates/prompt_plan.md" scripts/ralph/
   cp "${PLUGIN_ROOT}/skills/flux-ralph-init/templates/prompt_work.md" scripts/ralph/
   cp "${PLUGIN_ROOT}/skills/flux-ralph-init/templates/prompt_completion.md" scripts/ralph/
   cp "${PLUGIN_ROOT}/skills/flux-ralph-init/templates/watch-filter.py" scripts/ralph/
   cp "${PLUGIN_ROOT}/scripts/fluxctl" "${PLUGIN_ROOT}/scripts/fluxctl.py" scripts/ralph/
   mkdir -p scripts/ralph/hooks
   cp "${PLUGIN_ROOT}/scripts/hooks/ralph-guard.py" scripts/ralph/hooks/
   chmod +x scripts/ralph/ralph.sh scripts/ralph/ralph_once.sh scripts/ralph/fluxctl scripts/ralph/hooks/ralph-guard.py

   # Restore config.env
   cp /tmp/ralph-config-backup.env scripts/ralph/config.env
   ```

   **If UPDATE_MODE=0 (fresh install):**
   ```bash
   mkdir -p scripts/ralph/runs scripts/ralph/hooks
   cp -R "${PLUGIN_ROOT}/skills/flux-ralph-init/templates/." scripts/ralph/
   cp "${PLUGIN_ROOT}/scripts/fluxctl" "${PLUGIN_ROOT}/scripts/fluxctl.py" scripts/ralph/
   cp "${PLUGIN_ROOT}/scripts/hooks/ralph-guard.py" scripts/ralph/hooks/
   chmod +x scripts/ralph/ralph.sh scripts/ralph/ralph_once.sh scripts/ralph/fluxctl scripts/ralph/hooks/ralph-guard.py
   ```
   Note: `cp -R templates/.` copies all files including dotfiles (.gitignore).

6. Edit `scripts/ralph/config.env` to set the chosen review backend (skip if UPDATE_MODE=1):
   - Replace `PLAN_REVIEW={{PLAN_REVIEW}}` with `PLAN_REVIEW=<chosen>`
   - Replace `WORK_REVIEW={{WORK_REVIEW}}` with `WORK_REVIEW=<chosen>`
   - Replace `COMPLETION_REVIEW={{COMPLETION_REVIEW}}` with `COMPLETION_REVIEW=<chosen>`

7. Print next steps (run from terminal, NOT inside Claude Code):

   **If UPDATE_MODE=1:**
   ```
   Ralph updated! Your config.env was preserved.

   Changes in this version:
   - Removed local hooks requirement (plugin hooks work when installed normally)

   Run from terminal:
   - ./scripts/ralph/ralph_once.sh (one iteration, observe)
   - ./scripts/ralph/ralph.sh (full loop, AFK)
   ```

   **If UPDATE_MODE=0:**
   ```
   Ralph initialized!

   Next steps (run from terminal, NOT inside Claude Code):
   - Edit scripts/ralph/config.env to customize settings
   - ./scripts/ralph/ralph_once.sh (one iteration, observe)
   - ./scripts/ralph/ralph.sh (full loop, AFK)

   Maintenance:
   - Re-run /flux:ralph-init after plugin updates to refresh scripts
   - Uninstall (run manually): rm -rf scripts/ralph/
   ```


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
