---
name: flux-export-context
description: Export RepoPrompt context for external LLM review (ChatGPT, Claude web, etc.). Use when you want to review code or plans with an external model. Triggers on /flux:export-context.
---

# Export Context Mode

Build RepoPrompt context and export to a markdown file for use with external LLMs (ChatGPT Pro, Claude web, etc.).

**Use case**: When you want Carmack-level review but prefer to use an external model.

**CRITICAL: fluxctl is BUNDLED — NOT installed globally.** `which fluxctl` will fail (expected). Always use:
```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}"
[ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
$FLUXCTL <command>
```

## Input

Arguments: $ARGUMENTS
Format: `<type> <target> [focus areas]`

Types:
- `plan <epic-id>` - Export plan review context
- `impl` - Export implementation review context (current branch)

Examples:
- `/flux:export-context plan fn-1 focus on security`
- `/flux:export-context impl focus on the auth changes`

## Setup

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}"
[ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
```

## Workflow

### Step 1: Determine Type

Parse arguments to determine if this is a plan or impl export.

### Step 2: Gather Content

**For plan export:**
```bash
$FLUXCTL show <epic-id> --json
$FLUXCTL cat <epic-id>
```

**For impl export:**
```bash
git branch --show-current
git log main..HEAD --oneline 2>/dev/null || git log master..HEAD --oneline
git diff main..HEAD --name-only 2>/dev/null || git diff master..HEAD --name-only
```

### Step 3: Setup RepoPrompt

```bash
eval "$($FLUXCTL rp setup-review --repo-root "$REPO_ROOT" --summary "<summary based on type>" --create)"
```

### Step 4: Augment Selection

```bash
$FLUXCTL rp select-get --window "$W" --tab "$T"

# Add relevant files
$FLUXCTL rp select-add --window "$W" --tab "$T" <files>
```

### Step 5: Build Review Prompt

Get builder's handoff:
```bash
$FLUXCTL rp prompt-get --window "$W" --tab "$T"
```

Build combined prompt with review criteria (same as plan-review or impl-review).

Set the prompt:
```bash
cat > /tmp/export-prompt.md << 'EOF'
[COMBINED PROMPT WITH REVIEW CRITERIA]
EOF

$FLUXCTL rp prompt-set --window "$W" --tab "$T" --message-file /tmp/export-prompt.md
```

### Step 6: Export

```bash
OUTPUT_FILE=~/Desktop/review-export-$(date +%Y%m%d-%H%M%S).md
$FLUXCTL rp prompt-export --window "$W" --tab "$T" --out "$OUTPUT_FILE"
open "$OUTPUT_FILE"
```

### Step 7: Inform User

```
Exported review context to: $OUTPUT_FILE

The file contains:
- Full file tree with selected files marked
- Code maps (signatures/structure)
- Complete file contents
- Review prompt with Carmack-level criteria

Paste into ChatGPT Pro, Claude web, or your preferred LLM.
After receiving feedback, return here to implement fixes.
```

## Note

This skill is for **manual** external review only. It does not work with Ralph autonomous mode (no receipts, no status updates).


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
