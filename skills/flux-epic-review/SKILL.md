---
name: flux-epic-review
description: Epic completion review - adversarial dual-model review, external bot self-heal, browser QA, and learning capture. Full thorough review at epic level. Triggers on /flux:epic-review.
user-invocable: false
---

# Epic Completion Review Mode

**Read [workflow.md](workflow.md) for detailed phases and anti-patterns.**

Thorough review at epic completion. Combines adversarial dual-model review (two different models reach consensus), external bot self-heal (Greptile/CodeRabbit), browser QA, and learning capture. Cross-lab pairs (Anthropic + OpenAI) are strongest, but same-provider pairs work too. Per-task lightweight reviews happen via `/flux:impl-review` — this is the heavy-weight pass.

**Role**: Epic Review Coordinator (NOT the reviewer)
**Backends**: RepoPrompt (rp) or Codex CLI (codex)

## Session Phase Tracking

On entry (after FLUXCTL is resolved), set the session phase:
```bash
$FLUXCTL session-phase set epic_review
```
On completion, reset:
```bash
$FLUXCTL session-phase set idle
```

**CRITICAL: fluxctl is BUNDLED — NOT installed globally.** `which fluxctl` will fail (expected). Always use:
```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
[ ! -d "$PLUGIN_ROOT/scripts" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
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
- Use `flux-receive-review` when sorting valid issues from reviewer or bot feedback.

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
5. **Security Scan** — STRIDE-based vulnerability scan on changed files (auto-triggered for security-sensitive changes)
6. **External Bot Self-Heal** — poll Greptile/CodeRabbit for additional issues (if configured)
7. **Browser QA** — test acceptance criteria via QA checklist from scoping (if agent-browser available)
8. **Learning Capture** — extract patterns from NEEDS_WORK iterations and human-confirmed review anti-patterns to `.flux/brain/pitfalls/` or structural rule candidates
9. **Desloppify Scan** — lightweight quality scan on changed files (if desloppify installed)
10. **Frustration Signal** — auto-trigger recommendation search if friction score >= 3

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
[ ! -d "$PLUGIN_ROOT/scripts" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
$FLUXCTL architecture status --json
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

- `REVIEWER1`: First review model (e.g., `claude-sonnet-4-6`, `gpt-5.4`)
- `REVIEWER2`: Second review model — must be different from REVIEWER1 (e.g., `gpt-5.3-codex`, `claude-opus-4-6`)
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

Missing architecture-diagram updates are in scope here when the epic changed the product's
high-level architecture. `.flux/brain/codebase/architecture.md` is a canonical artifact, not optional docs.

#### RepoPrompt Backend

**Stop: You MUST read and execute [workflow.md](workflow.md) now.**

Go to the "RepoPrompt Backend Workflow" section in workflow.md and execute those steps. Do not proceed here until workflow.md phases are complete.

**Return here only after workflow.md spec compliance review is complete.**

### Step 3: Adversarial Review (if configured)

**Only runs if BOTH `reviewer1` AND `reviewer2` are configured.**

If only one reviewer or neither is configured, skip to Step 4.

See [workflow.md](workflow.md) "Adversarial Review Phase" for full details. Summary:

1. **Reviewer 1** reviews the diff independently via Codex/RP
2. **Reviewer 2** reviews the same diff independently via Codex/RP
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

Before declaring SHIP at any phase boundary, apply `flux-verify-claims`.

### Step 6: Security Scan (auto-triggered)

**Runs automatically when changed files touch security-sensitive areas.**

Detect if the epic's changed files include security-sensitive patterns:

```bash
CHANGED_FILES="$(git diff main..HEAD --name-only 2>/dev/null || git diff master..HEAD --name-only)"

# Security-sensitive patterns: auth, API routes, middleware, config, secrets, permissions
SECURITY_FILES=$(echo "$CHANGED_FILES" | grep -iE '(auth|login|session|token|middleware|permission|rbac|acl|secret|credential|api[-_]?key|security|crypto|encrypt|password|oauth|jwt|cors|csrf|sanitiz|valid)' || echo "")
```

**If `SECURITY_FILES` is non-empty**: Run the `flux-security-review` skill in `staged` mode against the branch diff. This invokes the full STRIDE scan (Spoofing, Tampering, Repudiation, Information Disclosure, DoS, Elevation of Privilege) with exploitability validation.

**If `SECURITY_FILES` is empty**: Skip security scan (pure UI or non-security changes).

After scan:
1. Parse `validated-findings.json` for confirmed vulnerabilities (confidence >= 0.8)
2. Filter by severity threshold (same `SEVERITIES` config)
3. Auto-fix findings in fix-list
4. Commit: `git commit -m "fix: address security scan findings"`
5. Re-scan if critical findings were found (max 1 re-scan)

Security findings are also captured in the Learning Capture phase.

### Step 7: External Bot Self-Heal (if configured)

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

### Step 8: Browser QA (if applicable)

**Only runs if `agent-browser` is detected on PATH AND a Browser QA Checklist task exists for this epic.**

During scoping (`/flux:scope`), Flux auto-creates a "Browser QA Checklist" task for epics that involve frontend/web changes. This task contains testable criteria — URLs, expected elements, user flows — that the browser QA phase follows.

See [workflow.md](workflow.md) "Browser QA Phase" for full details. Summary:

1. Check if `agent-browser` is available: `command -v agent-browser >/dev/null 2>&1`
2. Look for a Browser QA Checklist task in the epic: `$FLUXCTL tasks --epic "$EPIC_ID" --json | jq '.[] | select(.title | test("Browser QA|browser.qa"; "i"))'`
3. If no checklist task exists, skip browser QA
4. Read the checklist task's acceptance criteria
5. For each criterion:
   - Open URL with `agent-browser open <url>`
   - Take snapshot with `agent-browser snapshot -i`
   - Verify expected elements/text exist
   - Take screenshot for evidence: `agent-browser screenshot "/tmp/qa-${EPIC_ID}-${n}.png"`
6. If any criterion fails: fix code, commit, re-test (max 2 iterations)
7. Close browser session: `agent-browser close`

### Step 9: Learning Capture

After the full review pipeline reaches SHIP, extract learnings from any NEEDS_WORK iterations and persist them to the brain vault.

Pitfalls are organized by area of concern under `.flux/brain/pitfalls/<area>/`. The agent decides the area intelligently based on the pitfall's domain.

```bash
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
PITFALLS_DIR="$REPO_ROOT/.flux/brain/pitfalls"

# Determine area from the pitfall's domain
# Common areas: frontend, backend, security, async, api, database, testing, infra
# Create new area if none of the existing ones fit
AREA="<area>"  # e.g., "frontend", "security", "async"
mkdir -p "$PITFALLS_DIR/$AREA"

# Write one file per learning (slug from pattern name)
cat > "$PITFALLS_DIR/$AREA/<pattern-slug>.md" << 'EOF'
# <Pattern Name>

<description>

**Source**: epic-review (<epic-id>)
**Date**: <date>
EOF
```

**Area selection rules:**
1. Check existing area directories in `.flux/brain/pitfalls/` — use one if it fits
2. If no existing area matches, create a new directory with a short, descriptive slug
3. Keep areas broad enough to group related pitfalls (e.g., `frontend` not `react-forms`)
4. When in doubt, check what's already there: `ls .flux/brain/pitfalls/`

Update `.flux/brain/index.md` to include new pitfall area entries.

Format: one file per pattern, organized by area (e.g., `.flux/brain/pitfalls/frontend/missing-error-states.md`).

**What to capture:**
- Spec compliance gaps — requirements that drifted from spec
- Adversarial consensus patterns — issues both models flagged (high-signal)
- Security scan findings — STRIDE vulnerabilities caught post-implementation
- External bot patterns — recurring issues caught by Greptile/CodeRabbit
- Browser QA failures — UI/UX issues missed during implementation

Only capture generalizable patterns, not one-off fixes. These feed back into the worker via `.flux/brain/pitfalls/` which is read during re-anchor — but only the relevant area subdirectories are loaded, keeping context lean. Over time, `/flux:meditate` promotes recurring pitfalls into proper principles and prunes one-offs.

### Step 10: Desloppify Scan (optional)

**Only runs if `desloppify` is installed.** This is a scan-only pass — no fix loop, no auto-fix. The purpose is to surface quality regressions introduced during the epic.

```bash
if command -v desloppify >/dev/null 2>&1; then
  # Get directories touched in this epic
  CHANGED_DIRS=$(git diff "${DIFF_BASE}"..HEAD --name-only | xargs -I{} dirname {} | sort -u | grep -v '^\.$')

  if [ -n "$CHANGED_DIRS" ]; then
    for DIR in $CHANGED_DIRS; do
      desloppify scan --path "$DIR" 2>/dev/null
    done
  fi
fi
```

- If score is below 85, suggest: `"Consider running /flux:desloppify to address quality issues introduced in this epic."`
- Do NOT auto-install desloppify. Skip silently if not available.
- Do NOT enter a fix loop — this is informational only.

### Step 11: Frustration Signal

**See [workflow.md](workflow.md) "Frustration Signal" for full detection logic (quantitative + qualitative).**

Two-part detection system:

**Part 1 — Quantitative friction score** from pipeline counters:

```
FRICTION_SCORE = NEEDS_WORK_COUNT + SECURITY_FINDINGS + BROWSER_QA_FAILURES + (SAME_CATEGORY_PITFALLS * 2)
```

**Part 2 — Qualitative friction analysis** from three sources:
1. **Developer messages** during fix loops — scan for frustration language and extract the *topic* (e.g., "wtf is this UI? Still not responsive" → `responsive, css_issues, ui_issues`)
2. **Review issue categories** — classify reviewer feedback into domains (CSS/auth/testing/etc.)
3. **Pitfall areas** from learning capture — `.flux/brain/pitfalls/frontend/` → `frontend, ui_issues`

Combined into `FRICTION_DOMAINS` (what's broken) and `FRICTION_SIGNALS` (what `/flux:improve` should search for).

**If `FRICTION_SCORE >= 3`**, auto-trigger `/flux:improve` with the detected friction context:

1. Tell the user what friction was detected:
```
---
**Friction detected** (score: {FRICTION_SCORE}):

Quantitative:
- Review iterations: {NEEDS_WORK_COUNT}
- Security findings: {SECURITY_FINDINGS}
- Browser QA failures: {BROWSER_QA_FAILURES}
- Repeated pitfall categories: {SAME_CATEGORY_PITFALLS} (2x weight)

Diagnosis: {primary friction domain} — {one-sentence summary}
Evidence:
{top 2-3 quotes/issues/pitfalls}

Auto-searching for recommendations to address this...
---
```

2. Fresh-fetch the latest recommendations index (with timeout and error handling):
```bash
RECS_RAW=$(curl -sL --connect-timeout 10 --max-time 30 "https://raw.githubusercontent.com/Nairon-AI/flux-recommendations/main/recommendations.json")
CURL_EXIT=$?
```
If `CURL_EXIT != 0` or `RECS_RAW` is empty, tell the user recommendations are unavailable and skip steps 3-4. Do not fail the entire epic review.

3. Guard against empty friction domains — if `FRICTION_DOMAINS` is empty but score >= 3 (can happen when score comes purely from quantitative counters), use the quantitative signal types as search terms instead (e.g., `NEEDS_WORK` → "linting, formatting", `SECURITY_FINDINGS` → "security scanning", `BROWSER_QA_FAILURES` → "visual regression testing").

4. Search the recommendations for entries matching `FRICTION_DOMAINS` and `FRICTION_SIGNALS`. Score each recommendation by how many friction signals it addresses. Present the top 3-5 matches with:
   - Tool name and what it does
   - Which specific friction it addresses
   - Install command or setup steps

5. Ask the user which (if any) to install now. Do not auto-install — the user picks.

The `--user-context` flag pre-fills the detected friction domains so `/flux:improve`'s matching engine can skip discovery and go straight to relevant tool recommendations.

---

## Update Check (End of Command)

**ALWAYS run at the very end of command execution:**

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
[ ! -d "$PLUGIN_ROOT/scripts" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
UPDATE_JSON=$("$PLUGIN_ROOT/scripts/version-check.sh" 2>/dev/null || echo '{"update_available":false}')
UPDATE_AVAILABLE=$(echo "$UPDATE_JSON" | jq -r '.update_available')
LOCAL_VER=$(echo "$UPDATE_JSON" | jq -r '.local_version')
REMOTE_VER=$(echo "$UPDATE_JSON" | jq -r '.remote_version')
```

**If update available**, append to output:

```
---
Flux update available: v${LOCAL_VER} → v${REMOTE_VER}
Update Flux from the same source you installed it from, then restart your agent session.
---
```
