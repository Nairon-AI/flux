---
name: flux
description: "Manage .flux/ tasks and epics. Triggers: 'show me my tasks', 'list epics', 'what tasks are there', 'add a task', 'create task', 'what's ready', 'task status', 'show fn-1-add-oauth'. NOT for /flux:plan or /flux:work."
---

# Flux Task Management

Quick task operations in `.flux/`. For planning features use `/flux:plan`, for executing use `/flux:work`.

## Setup

**CRITICAL: fluxctl is BUNDLED — NOT installed globally.** `which fluxctl` will fail (expected). Always use:

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}"
[ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
```

Then run commands with `$FLUXCTL <command>`.

**Discover all commands/options:**
```bash
$FLUXCTL --help
$FLUXCTL <command> --help   # e.g., $FLUXCTL task --help
```

## Quick Reference

```bash
# Check if .flow exists
$FLUXCTL detect --json

# Initialize (if needed)
$FLUXCTL init --json

# List everything (epics + tasks grouped)
$FLUXCTL list --json

# List all epics
$FLUXCTL epics --json

# List all tasks (or filter by epic/status)
$FLUXCTL tasks --json
$FLUXCTL tasks --epic fn-1-add-oauth --json
$FLUXCTL tasks --status todo --json

# View epic with all tasks
$FLUXCTL show fn-1-add-oauth --json
$FLUXCTL cat fn-1-add-oauth              # Spec markdown

# View single task
$FLUXCTL show fn-1-add-oauth.2 --json
$FLUXCTL cat fn-1-add-oauth.2            # Task spec

# What's ready to work on?
$FLUXCTL ready --epic fn-1-add-oauth --json

# Create task under existing epic
$FLUXCTL task create --epic fn-1-add-oauth --title "Fix bug X" --json

# Set task description and acceptance (combined, fewer writes)
$FLUXCTL task set-spec fn-1-add-oauth.2 --description /tmp/desc.md --acceptance /tmp/accept.md --json

# Or use stdin with heredoc (no temp file):
$FLUXCTL task set-description fn-1-add-oauth.2 --file - --json <<'EOF'
Description here
EOF

# Start working on task
$FLUXCTL start fn-1-add-oauth.2 --json

# Mark task done
echo "What was done" > /tmp/summary.md
echo '{"commits":["abc123"],"tests":["npm test"],"prs":[]}' > /tmp/evidence.json
$FLUXCTL done fn-1-add-oauth.2 --summary-file /tmp/summary.md --evidence-json /tmp/evidence.json --json

# Validate structure
$FLUXCTL validate --epic fn-1-add-oauth --json
$FLUXCTL validate --all --json
```

## Common Patterns

### "Add a task for X"

1. Find relevant epic:
   ```bash
   # List all epics
   $FLUXCTL epics --json

   # Or show a specific epic to check its scope
   $FLUXCTL show fn-1 --json
   ```

2. Create task:
   ```bash
   $FLUXCTL task create --epic fn-N --title "Short title" --json
   ```

3. Add description + acceptance (combined):
   ```bash
   cat > /tmp/desc.md << 'EOF'
   **Bug/Feature:** Brief description

   **Details:**
   - Point 1
   - Point 2
   EOF
   cat > /tmp/accept.md << 'EOF'
   - [ ] Criterion 1
   - [ ] Criterion 2
   EOF
   $FLUXCTL task set-spec fn-N.M --description /tmp/desc.md --acceptance /tmp/accept.md --json
   ```

### "What tasks are there?"

```bash
# All epics
$FLUXCTL epics --json

# All tasks
$FLUXCTL tasks --json

# Tasks for specific epic
$FLUXCTL tasks --epic fn-1-add-oauth --json

# Ready tasks for an epic
$FLUXCTL ready --epic fn-1-add-oauth --json
```

### "Show me task X"

```bash
$FLUXCTL show fn-1-add-oauth.2 --json   # Metadata
$FLUXCTL cat fn-1-add-oauth.2           # Full spec
```

(Legacy `fn-1.2` / `fn-1-xxx.2` still works.)

### Create new epic (rare - usually via /flux:plan)

```bash
$FLUXCTL epic create --title "Epic title" --json
# Returns: {"success": true, "id": "fn-N-epic-title", ...}
```

## ID Format

- Epic: `fn-N-slug` where slug is derived from title (e.g., `fn-1-add-oauth`, `fn-2-fix-login-bug`)
- Task: `fn-N-slug.M` (e.g., `fn-1-add-oauth.1`, `fn-2-fix-login-bug.2`)

Legacy formats `fn-N` and `fn-N-xxx` (random 3-char suffix) are still supported.

## Notes

- Run `$FLUXCTL --help` to discover all commands and options
- All writes go through fluxctl (don't edit JSON/MD files directly)
- `--json` flag gives machine-readable output
- For complex planning/execution, use `/flux:plan` and `/flux:work`


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
