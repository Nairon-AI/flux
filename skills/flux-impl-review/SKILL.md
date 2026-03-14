---
name: flux-impl-review
description: Adversarial implementation review using two models from different labs to reach consensus. Supports RepoPrompt, Codex, and external bots (Greptile, CodeRabbit). Self-heals until all major issues resolved. Triggers on /flux:impl-review.
user-invocable: false
---

# Implementation Review Mode

**Read [workflow.md](workflow.md) for detailed phases and anti-patterns.**

Conduct an adversarial review of implementation changes using two models from different labs (Anthropic + OpenAI). Issues both models agree on get fixed automatically. Single-model findings are flagged but still addressed.

**Role**: Code Review Coordinator (NOT the reviewer)
**Backends**: RepoPrompt (rp) or Codex CLI (codex)
**Adversarial**: Two reviewer models reach consensus (configured in `.flux/config.json`)
**External bots**: Greptile (PR polling) or CodeRabbit (CLI or PR comments)

**CRITICAL: fluxctl is BUNDLED — NOT installed globally.** `which fluxctl` will fail (expected). Always use:
```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}"
[ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
```

## Backend Selection

**Priority** (first match wins):
1. `--review=rp|codex|export|none` argument
2. `FLUX_REVIEW_BACKEND` env var (`rp`, `codex`, `none`)
3. `.flux/config.json` → `review.backend`
4. **Error** - no auto-detection

### Parse from arguments first

Check $ARGUMENTS for:
- `--review=rp` or `--review rp` → use rp
- `--review=codex` or `--review codex` → use codex
- `--review=export` or `--review export` → use export
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
1. Use `$FLUXCTL codex impl-review` exclusively
2. Pass `--receipt` for session continuity on re-reviews
3. Parse verdict from command output

**For all backends:**
- If `REVIEW_RECEIPT_PATH` set: write receipt after review (any verdict)
- Any failure → output `<promise>RETRY</promise>` and stop

**FORBIDDEN**:
- Self-declaring SHIP without actual backend verdict
- Mixing backends mid-review (stick to one)
- Skipping review when backend is "none" without user consent

## Input

Arguments: $ARGUMENTS
Format: `[task ID] [--base <commit>] [focus areas]`

- `--base <commit>` - Compare against this commit instead of main/master (for task-scoped reviews)
- Task ID - Optional, for context and receipt tracking
- Focus areas - Optional, specific areas to examine

**Scope behavior:**
- With `--base`: Reviews only changes since that commit (task-scoped)
- Without `--base`: Reviews entire branch vs main/master (full branch review)

## Workflow

**See [workflow.md](workflow.md) for full details on each backend.**

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}"
[ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
```

### Step 0: Parse Arguments

Parse $ARGUMENTS for:
- `--base <commit>` → `BASE_COMMIT` (if provided, use for scoped diff)
- First positional arg matching `fn-*` → `TASK_ID`
- Remaining args → focus areas

If `--base` not provided, `BASE_COMMIT` stays empty (will fall back to main/master).

### Step 1: Detect Backend

Run backend detection from SKILL.md above. Then branch:

### Codex Backend

```bash
RECEIPT_PATH="${REVIEW_RECEIPT_PATH:-/tmp/impl-review-receipt.json}"

# Use BASE_COMMIT if provided, else fall back to main
if [[ -n "$BASE_COMMIT" ]]; then
  $FLUXCTL codex impl-review "$TASK_ID" --base "$BASE_COMMIT" --receipt "$RECEIPT_PATH"
else
  $FLUXCTL codex impl-review "$TASK_ID" --base main --receipt "$RECEIPT_PATH"
fi
# Output includes VERDICT=SHIP|NEEDS_WORK|MAJOR_RETHINK
```

On NEEDS_WORK: fix code, commit, re-run (receipt enables session continuity).

### RepoPrompt Backend

**⚠️ STOP: You MUST read and execute [workflow.md](workflow.md) now.**

Go to the "RepoPrompt Backend Workflow" section in workflow.md and execute those steps. Do not proceed here until workflow.md phases are complete.

The workflow covers:
1. Identify changes (use `BASE_COMMIT` if provided)
2. Atomic setup (setup-review) → sets `$W` and `$T`
3. Augment selection and build review prompt
4. Send review and parse verdict

**Return here only after workflow.md execution is complete.**

## Adversarial Review

Flux uses **two models from different labs** to review the same code independently. This eliminates single-model blind spots — issues both agree on are high-confidence and get fixed automatically.

### Step A1: Load reviewer config

```bash
REVIEWER_1=$($FLUXCTL config get review.reviewer1 2>/dev/null | awk '{print $2}')
REVIEWER_2=$($FLUXCTL config get review.reviewer2 2>/dev/null | awk '{print $2}')
REVIEW_BOT=$($FLUXCTL config get review.bot 2>/dev/null | awk '{print $2}')
```

If `REVIEWER_1` or `REVIEWER_2` is empty/not set, fall back to single-model review using the configured backend only (skip adversarial). This maintains backward compatibility.

### Step A2: Run first reviewer (Anthropic model)

The agent performing this review IS the first reviewer (it runs on an Anthropic model). Conduct the review yourself using the configured backend (RP or Codex) as usual. Collect all findings as `REVIEW_1_ISSUES`.

### Step A3: Run second reviewer (OpenAI model via Codex)

Run the second review using the OpenAI model via Codex CLI:

```bash
$FLUXCTL codex impl-review "$TASK_ID" --base "${BASE_COMMIT:-main}" --model "$REVIEWER_2" --receipt "$RECEIPT_PATH"
```

Collect findings as `REVIEW_2_ISSUES`.

### Step A4: Merge findings — consensus wins

Compare the two sets of findings:

| Scenario | Action |
|----------|--------|
| **Both agree** on same issue | **High confidence** — fix immediately, no debate |
| **Only one** flags an issue | **Medium confidence** — still fix, but note it was single-model |
| **Contradictory** findings | Flag for the fix loop — address the more conservative recommendation |

Build a merged issue list sorted by: consensus issues first (Critical → Major → Minor), then single-model issues.

## Fix Loop (INTERNAL - do not exit to Ralph)

**CRITICAL: Do NOT ask user for confirmation. Automatically fix ALL valid issues and re-review — our goal is production-grade world-class software and architecture. Never use AskUserQuestion in this loop.**

If verdict is NEEDS_WORK, loop internally until SHIP:

1. **Parse issues** from merged adversarial findings (Consensus → Critical → Major → Minor)
2. **Fix code** and run tests/lints
3. **Commit fixes** (mandatory before re-review)
4. **Re-review**:
   - **Codex**: Re-run `fluxctl codex impl-review` (receipt enables context)
   - **RP**: `$FLUXCTL rp chat-send --window "$W" --tab "$T" --message-file /tmp/re-review.md` (NO `--new-chat`)
5. **Repeat** until `<verdict>SHIP</verdict>`

**CRITICAL**: For RP, re-reviews must stay in the SAME chat so reviewer has context. Only use `--new-chat` on the FIRST review.

## External Bot Self-Heal (Post-PR)

After the internal review loop reaches SHIP and a PR has been created/pushed, check if an external review bot is configured.

### Greptile Self-Heal

If `REVIEW_BOT=greptile`:

1. **Wait for Greptile** — poll the PR description every 15 seconds for the Greptile summary:
   ```bash
   gh pr view <PR_NUMBER> --json body --jq '.body'
   ```
   Look for `## Greptile Summary` or `Confidence Score:` in the body. If not found after 10 minutes, warn and continue.

2. **Parse confidence score** — extract `Confidence Score: X/5` from the PR description.

3. **If confidence < 5/5**:
   - Parse the "Issue found:" section and bullet points under the Greptile summary
   - Fix the identified issues
   - Commit and push
   - Re-trigger Greptile by commenting on the PR:
     ```bash
     gh pr comment <PR_NUMBER> --body "@greptile review"
     ```
   - Wait 15 seconds, then poll again for updated Greptile summary
   - **Loop until confidence is 5/5** or max 5 iterations

4. **If confidence = 5/5**: Self-heal complete. Continue to Learning Capture.

### CodeRabbit Self-Heal

If `REVIEW_BOT=coderabbit`:

1. **Check if CodeRabbit CLI is available**:
   ```bash
   which coderabbit >/dev/null 2>&1 && HAVE_CR_CLI=1 || HAVE_CR_CLI=0
   ```

2. **If CLI available** — run locally:
   ```bash
   coderabbit review
   ```
   Parse output for issues. Fix, commit, re-run. Loop until clean.

3. **If CLI not available** — poll PR comments:
   ```bash
   gh pr view <PR_NUMBER> --json comments --jq '.comments[] | select(.author.login == "coderabbitai") | .body'
   ```
   Parse CodeRabbit's review comments for actionable issues. Fix, commit, push. Wait for new CodeRabbit review. Loop until no major issues.

4. **Max 5 iterations** for either path.

### No Bot

If `REVIEW_BOT=none` or not set: skip this section entirely.

## Learning Capture

**After every review cycle** (whether internal adversarial or external bot), extract learnings and persist them to `.flux/memory/pitfalls.md`.

### What to capture

From the review findings, extract **patterns** — not individual fixes, but reusable lessons:

- Mistakes the models made that a reviewer caught (e.g. "raw SQL in handlers", "missing error boundary")
- Patterns that triggered consensus issues (both models agreed = strong signal)
- External bot findings that were valid (Greptile/CodeRabbit caught something the models missed)

### How to capture

```bash
$FLUXCTL memory add pitfalls "<learning>"
```

Format each learning as:
```
[<date>] [<source>] <pattern>: <description>. Applies to: <file pattern or area>.
```

Examples:
```
[2026-03-14] [adversarial-consensus] avoid-raw-sql: Always use parameterized queries via ORM, never raw SQL in route handlers. Applies to: src/api/**
[2026-03-14] [greptile] status-field-in-payload: Don't include status field in PATCH payloads unconditionally — check if it changed first. Applies to: src/api/listings/**
[2026-03-14] [coderabbit] missing-error-boundary: Wrap async operations in try/catch with user-facing error states. Applies to: src/components/**
```

### When learnings are used

These pitfalls are automatically loaded by `/flux:work` at the start of each task. The agent reads `.flux/memory/pitfalls.md` and actively avoids repeating the same mistakes. This creates a **feedback loop**: reviews catch issues → learnings prevent recurrence → fewer issues in future reviews.

**Only capture learnings that are generalizable** — skip one-off typos or task-specific issues. The goal is patterns that apply to future work in this codebase.

---

## Update Check (End of Command)

**ALWAYS run at the very end of /flux:impl-review execution:**

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
