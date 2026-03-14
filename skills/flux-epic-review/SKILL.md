---
name: flux-epic-review
description: Epic completion review - adversarial dual-model review, external bot self-heal, browser QA, and learning capture. Full thorough review at epic level. Triggers on /flux:epic-review.
user-invocable: false
---

# Epic Completion Review Mode

**Read [workflow.md](workflow.md) for detailed phases and anti-patterns.**

Thorough review at epic completion. Combines adversarial dual-model review (Anthropic + OpenAI consensus), external bot self-heal (Greptile/CodeRabbit), browser QA, and learning capture. Per-task lightweight reviews happen via `/flux:impl-review` — this is the heavy-weight pass.

**Role**: Epic Review Coordinator (NOT the reviewer)
**Backends**: RepoPrompt (rp) or Codex CLI (codex)

**CRITICAL: fluxctl is BUNDLED — NOT installed globally.** `which fluxctl` will fail (expected). Always use:
```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}"
[ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
```

## Backend Selection

**Priority** (first match wins):
1. `--review=rp|codex|none` argument
2. `FLUX_REVIEW_BACKEND` env var (`rp`, `codex`, `none`)
3. `.flux/config.json` → `review.backend`
4. **Error** - no auto-detection

### Parse from arguments first

Check $ARGUMENTS for:
- `--review=rp` or `--review rp` → use rp
- `--review=codex` or `--review codex` → use codex
- `--review=none` or `--review none` → skip review

If found, use that backend and skip all other detection.

### Otherwise read from config

```bash
BACKEND=$($FLUXCTL review-backend)

if [[ "$BACKEND" == "ASK" ]]; then
  echo "Error: No review backend configured."
  echo "Run /flux:setup to configure, or pass --review=rp|codex|none"
  exit 1
fi

echo "Review backend: $BACKEND (override: --review=rp|codex|none)"
```

## Critical Rules

**For rp backend:**
1. **DO NOT REVIEW CODE YOURSELF** - you coordinate, RepoPrompt reviews
2. **MUST WAIT for actual RP response** - never simulate/skip the review
3. **MUST use `setup-review`** - handles window selection + builder atomically
4. **DO NOT add --json flag to chat-send** - it suppresses the review response
5. **Re-reviews MUST stay in SAME chat** - omit `--new-chat` after first review

**For codex backend:**
1. Use `$FLUXCTL codex completion-review` exclusively
2. Pass `--receipt` for session continuity on re-reviews
3. Parse verdict from command output

**For all backends:**
- If `REVIEW_RECEIPT_PATH` set: write receipt after SHIP verdict (RP writes manually after fix loop; codex writes automatically via `--receipt`)
- Any failure → output `<promise>RETRY</promise>` and stop

**FORBIDDEN**:
- Self-declaring SHIP without actual backend verdict
- Mixing backends mid-review (stick to one)
- Skipping review silently (must inform user and exit cleanly when backend is "none")

## Input

Arguments: $ARGUMENTS
Format: `<epic-id> [--review=rp|codex|none]`

- Epic ID - Required, e.g. `fn-1` or `fn-22-53k`
- `--review` - Optional backend override

## Workflow Overview

**See [workflow.md](workflow.md) for full details on each phase.**

The epic review is a multi-phase pipeline:

1. **Spec Compliance Review** — verify all epic requirements are implemented (via backend)
2. **Adversarial Review** — dual-model consensus review (if reviewer1 + reviewer2 configured)
3. **Severity Filtering** — split issues into fix-list vs log-only based on configured threshold
4. **Fix Loop** — auto-fix issues at/above threshold, re-review until SHIP
5. **External Bot Self-Heal** — poll Greptile/CodeRabbit for additional issues (if configured)
6. **Browser QA** — test acceptance criteria in browser (if agent-browser available)
7. **Learning Capture** — extract patterns from NEEDS_WORK iterations to pitfalls.md

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}"
[ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
```

### Step 0: Parse Arguments

Parse $ARGUMENTS for:
- First positional arg matching `fn-*` → `EPIC_ID`
- `--review=<backend>` → backend override
- Remaining args → focus areas

### Step 1: Load Review Config

```bash
# Read adversarial reviewers and bot config
REVIEWER1=$($FLUXCTL config get review.reviewer1 2>/dev/null || echo "")
REVIEWER2=$($FLUXCTL config get review.reviewer2 2>/dev/null || echo "")
REVIEW_BOT=$($FLUXCTL config get review.bot 2>/dev/null || echo "")
SEVERITIES=$($FLUXCTL config get review.severities 2>/dev/null || echo "critical,major")
```

- `REVIEWER1`: Anthropic model (e.g., `claude-sonnet-4-5-20250514`)
- `REVIEWER2`: OpenAI model (e.g., `o3`)
- `REVIEW_BOT`: `greptile`, `coderabbit`, or empty
- `SEVERITIES`: comma-separated list of severity levels to auto-fix (e.g., `critical,major`)

### Step 2: Detect Backend & Run Spec Compliance Review

Run backend detection from above. Then branch:

#### Codex Backend

```bash
RECEIPT_PATH="${REVIEW_RECEIPT_PATH:-/tmp/completion-review-receipt.json}"

$FLUXCTL codex completion-review "$EPIC_ID" --receipt "$RECEIPT_PATH"
# Output includes VERDICT=SHIP|NEEDS_WORK
```

On NEEDS_WORK: fix code, commit, re-run (receipt enables session continuity).

#### RepoPrompt Backend

**Stop: You MUST read and execute [workflow.md](workflow.md) now.**

Go to the "RepoPrompt Backend Workflow" section in workflow.md and execute those steps. Do not proceed here until workflow.md phases are complete.

**Return here only after workflow.md spec compliance review is complete.**

### Step 3: Adversarial Review (if configured)

**Only runs if BOTH `reviewer1` AND `reviewer2` are configured.**

If only one reviewer or neither is configured, skip to Step 4.

See [workflow.md](workflow.md) "Adversarial Review Phase" for full details. Summary:

1. **Reviewer 1** (Anthropic) reviews the diff independently via Codex/RP
2. **Reviewer 2** (OpenAI) reviews the same diff independently via Codex
3. **Consensus merge**: Issues flagged by BOTH reviewers = high-confidence (auto-fix). Issues flagged by only one = log-only (unless at/above severity threshold).

The adversarial approach catches more issues than a single model while reducing false positives through consensus.

### Step 4: Severity Filtering

Split all issues (from spec review + adversarial review) into two buckets:

- **Fix list**: Issues at or above the configured severity threshold → auto-fix
- **Log only**: Issues below threshold → log to review output but don't fix

Severity ranking: `critical` > `major` > `minor` > `style`

If `SEVERITIES` = `["critical", "major"]`, then critical and major issues are auto-fixed; minor and style are logged only.

### Step 5: Fix Loop (INTERNAL - do not exit to Ralph)

**CRITICAL: Do NOT ask user for confirmation. Automatically fix ALL issues in the fix-list and re-review. Never use AskUserQuestion in this loop.**

If verdict is NEEDS_WORK and fix-list is non-empty, loop internally until SHIP:

1. **Parse issues** from reviewer feedback (filter by severity threshold)
2. **Fix code** and run tests/lints
3. **Commit fixes** (mandatory before re-review)
4. **Re-review**:
   - **Codex**: Re-run `fluxctl codex completion-review` (receipt enables context)
   - **RP**: `$FLUXCTL rp chat-send --window "$W" --tab "$T" --message-file /tmp/re-review.md` (NO `--new-chat`)
5. **Repeat** until `<verdict>SHIP</verdict>`

**CRITICAL**: For RP, re-reviews must stay in the SAME chat so reviewer has context. Only use `--new-chat` on the FIRST review.

**MAX ITERATIONS**: Limit fix+re-review cycles to **${MAX_REVIEW_ITERATIONS:-3}** iterations. If still NEEDS_WORK after max rounds, output `<promise>RETRY</promise>` and stop.

### Step 6: External Bot Self-Heal (if configured)

**Only runs if `review.bot` is configured AND a PR exists for the branch.**

See [workflow.md](workflow.md) "External Bot Self-Heal Phase" for full details. Summary:

#### Greptile

1. Push branch and ensure PR exists
2. Poll PR description for Greptile confidence summary (check every 15s, timeout 5 min)
3. Parse confidence score and issue list
4. Fix any issues at/above severity threshold
5. Push fixes and re-poll until confidence is acceptable

#### CodeRabbit

1. Push branch and ensure PR exists
2. Run `coderabbit review` CLI or poll PR comments for CodeRabbit review
3. Parse issue list from review output
4. Fix any issues at/above severity threshold
5. Push fixes and wait for re-review

### Step 7: Browser QA (if agent-browser available)

**Only runs if `agent-browser` is detected on PATH and epic spec contains acceptance criteria with URLs or testable UI flows.**

See [workflow.md](workflow.md) "Browser QA Phase" for full details. Summary:

1. Check if `agent-browser` is available: `command -v agent-browser >/dev/null 2>&1`
2. Extract testable acceptance criteria from epic spec (URLs, UI flows, visual checks)
3. For each testable criterion:
   - Open URL with `agent-browser open <url>`
   - Take snapshot with `agent-browser snapshot -i`
   - Verify expected elements/text exist
   - Take screenshot for evidence
4. If any criterion fails: fix code, commit, re-test
5. Close browser session when done

### Step 8: Learning Capture

After the full review pipeline reaches SHIP, extract learnings from any NEEDS_WORK iterations and persist them:

```bash
$FLUXCTL memory add pitfalls "<learning>"
```

Format: `[<date>] [epic-review] <pattern>: <description>. Applies to: <area>.`

**What to capture:**
- Spec compliance gaps — requirements that drifted from spec
- Adversarial consensus patterns — issues both models flagged (high-signal)
- External bot patterns — recurring issues caught by Greptile/CodeRabbit
- Browser QA failures — UI/UX issues missed during implementation

Only capture generalizable patterns, not one-off fixes. These feed back into the worker via `.flux/memory/pitfalls.md` which is read during re-anchor (Phase 1 of `/flux:work`).

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
Run: /plugin uninstall flux@nairon-flux && /plugin add https://github.com/Nairon-AI/flux@latest
Then restart Claude Code for changes to take effect.
---
```
