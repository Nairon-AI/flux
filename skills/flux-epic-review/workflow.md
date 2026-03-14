# Epic Completion Review Workflow

## Philosophy

Epic completion review is the thorough review gate. It combines:
- **Spec compliance** — verify all requirements are implemented (single-model, same as before)
- **Adversarial review** — dual-model consensus (Anthropic + OpenAI) for high-confidence issue detection
- **Severity filtering** — only auto-fix issues at/above configured threshold
- **External bot self-heal** — Greptile/CodeRabbit catch what models miss
- **Browser QA** — verify acceptance criteria in actual browser
- **Learning capture** — feed patterns back into brain vault (pitfalls + principles)

Per-task lightweight reviews happen via `/flux:impl-review`. This is the heavy-weight pass that runs once when all epic tasks are done.

---

## Phase 0: Backend Detection

**Run this first. Do not skip.**

**CRITICAL: fluxctl is BUNDLED — NOT installed globally.** `which fluxctl` will fail (expected). Always use:

```bash
set -e
FLUXCTL="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}/scripts/fluxctl"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Priority: --review flag > env > config (flag parsed in SKILL.md)
BACKEND=$($FLUXCTL review-backend)

if [[ "$BACKEND" == "ASK" ]]; then
  echo "Error: No review backend configured."
  echo "Run /flux:setup to configure, or pass --review=rp|codex|none"
  exit 1
fi

echo "Review backend: $BACKEND"
```

**If backend is "none"**: Skip review, inform user, and exit cleanly (no error).

**Load review config:**

```bash
REVIEWER1=$($FLUXCTL config get review.reviewer1 2>/dev/null || echo "")
REVIEWER2=$($FLUXCTL config get review.reviewer2 2>/dev/null || echo "")
REVIEW_BOT=$($FLUXCTL config get review.bot 2>/dev/null || echo "")
SEVERITIES=$($FLUXCTL config get review.severities 2>/dev/null || echo "critical,major")

# Parse severities into a list for filtering
# Valid levels: critical, major, minor, style
```

**Then branch to backend-specific workflow below.**

---

## Codex Backend Workflow

Use when `BACKEND="codex"`.

### Step 1: Identify Epic

```bash
# EPIC_ID from arguments (e.g., fn-1, fn-22-53k)
$FLUXCTL show "$EPIC_ID" --json
```

### Step 2: Execute Spec Compliance Review

```bash
RECEIPT_PATH="${REVIEW_RECEIPT_PATH:-/tmp/completion-review-receipt.json}"

$FLUXCTL codex completion-review "$EPIC_ID" --receipt "$RECEIPT_PATH"
```

**Output includes `VERDICT=SHIP|NEEDS_WORK`.**

### Step 3: Handle Verdict

If `VERDICT=NEEDS_WORK`:
1. Parse issues from output, filter by severity threshold
2. Fix code and run tests
3. Commit fixes
4. Re-run step 2 (receipt enables session continuity)
5. Repeat until SHIP

### Step 4: Receipt

Receipt is written automatically by `fluxctl codex completion-review` when `--receipt` provided.
Format: `{"type":"completion_review","id":"<epic-id>","mode":"codex","verdict":"<verdict>","session_id":"<thread_id>","timestamp":"..."}`

**After SHIP from codex: proceed to Adversarial Review Phase (if configured).**

---

## RepoPrompt Backend Workflow

Use when `BACKEND="rp"`.

## Phase 1: Gather Context (RP)

**Run this BEFORE setup-review so the builder gets a real summary.**

```bash
BRANCH="$(git branch --show-current)"

# Get epic spec and task list
EPIC_SPEC="$($FLUXCTL cat "$EPIC_ID")"
TASKS_JSON="$($FLUXCTL tasks --epic "$EPIC_ID" --json)"

# Get changed files on branch
DIFF_BASE="main"
git rev-parse main >/dev/null 2>&1 || DIFF_BASE="master"
git log ${DIFF_BASE}..HEAD --oneline
CHANGED_FILES="$(git diff ${DIFF_BASE}..HEAD --name-only)"
git diff ${DIFF_BASE}..HEAD --stat
```

Save:
- Epic ID and spec
- Task list (IDs and titles)
- Branch name
- Changed files list

Compose a 1-2 sentence `REVIEW_SUMMARY` for the setup-review command below.

---

### Atomic Setup Block

**Only run ONCE. Uses the summary composed in Phase 1.**

```bash
# Atomic: pick-window + builder (uses REVIEW_SUMMARY from Phase 1)
eval "$($FLUXCTL rp setup-review --repo-root "$REPO_ROOT" --summary "$REVIEW_SUMMARY" --create)"

# Verify we have W and T
if [[ -z "${W:-}" || -z "${T:-}" ]]; then
  echo "<promise>RETRY</promise>"
  exit 0
fi

echo "Setup complete: W=$W T=$T"
```

If this block fails, output `<promise>RETRY</promise>` and stop. Do not improvise.
**Do NOT re-run setup-review** — the builder runs inside it. Re-running = double context build.

---

## Phase 2: Augment Selection (RP)

Builder selects context automatically. Review and add must-haves:

```bash
# See what builder selected
$FLUXCTL rp select-get --window "$W" --tab "$T"

# Add epic spec
$FLUXCTL rp select-add --window "$W" --tab "$T" ".flux/specs/$EPIC_ID.md"

# Add all task specs
for task_id in $(echo "$TASKS_JSON" | jq -r '.[].id'); do
  $FLUXCTL rp select-add --window "$W" --tab "$T" ".flux/tasks/$task_id.md"
done

# Add ALL changed files
for f in $CHANGED_FILES; do
  $FLUXCTL rp select-add --window "$W" --tab "$T" "$f"
done
```

**Why this matters:** Chat only sees selected files.

---

## Phase 3: Execute Spec Compliance Review (RP)

### Build combined prompt

Get builder's handoff:
```bash
HANDOFF="$($FLUXCTL rp prompt-get --window "$W" --tab "$T")"
```

Write combined prompt:
```bash
cat > /tmp/completion-review-prompt.md << 'EOF'
[PASTE HANDOFF HERE]

---

## IMPORTANT: File Contents
RepoPrompt includes the actual source code of selected files in a `<file_contents>` XML section at the end of this message. You MUST:
1. Locate the `<file_contents>` section
2. Read and analyze the actual source code within it
3. Base your review on the code, not summaries or descriptions

If you cannot find `<file_contents>`, ask for the files to be re-attached before proceeding.

## Epic Under Review
Epic: [EPIC_ID]
Branch: [BRANCH_NAME]
Tasks: [LIST TASK IDs]

## Epic Spec
[PASTE EPIC SPEC]

## Review Focus: Spec Compliance

This is NOT a code quality review — impl-review handles that per-task.

Your job: Verify the combined implementation delivers everything the spec requires.

### Two-Phase Approach

**Phase 1: Extract Requirements**
Read the epic spec and list ALL explicit requirements as bullets:
- Features/functionality to implement
- Docs to update (README, API docs, etc.)
- Tests to add
- Config/schema changes
- Any other deliverables

**Phase 2: Verify Implementation**
For each requirement from Phase 1:
- [ ] Is it implemented in the changed files?
- [ ] Is the implementation complete (not partial)?
- [ ] Does it match the spec intent?

### What to Check
- Requirements that never became tasks (decomposition gaps)
- Requirements partially implemented across tasks (cross-task gaps)
- Scope drift (task marked done without fully addressing spec intent)
- Missing doc updates specified in acceptance criteria

### What NOT to Check
- Code style, patterns, architecture (impl-review covers this)
- Test quality (impl-review covers this)
- Performance (impl-review covers this)

## Output Format

For each issue found, tag with severity:

- **Severity**: Critical / Major / Minor / Style
- **Requirement**: What the spec says
- **Status**: Missing / Partial / Wrong
- **Evidence**: What you found (or didn't find) in the code

**REQUIRED**: You MUST end your response with exactly one verdict tag. This is mandatory:
`<verdict>SHIP</verdict>` or `<verdict>NEEDS_WORK</verdict>`

- SHIP: All spec requirements are implemented
- NEEDS_WORK: One or more requirements are missing, partial, or wrong

Do NOT skip this tag. The automation depends on it.
EOF
```

**Note:** Replace bracket placeholders (`[EPIC_ID]`, `[BRANCH_NAME]`, etc.) with actual values before sending.

### Send to RepoPrompt and Parse Verdict

```bash
# Send review and capture response
REVIEW_RESPONSE="$($FLUXCTL rp chat-send --window "$W" --tab "$T" --message-file /tmp/completion-review-prompt.md --new-chat --chat-name "Epic Review: $EPIC_ID")"
echo "$REVIEW_RESPONSE"

# Extract verdict tag from response
VERDICT="$(echo "$REVIEW_RESPONSE" \
  | tr -d '\r' \
  | grep -oE '<verdict>(SHIP|NEEDS_WORK)</verdict>' \
  | tail -n 1 \
  | sed -E 's#</?verdict>##g')"

if [[ -z "$VERDICT" ]]; then
  echo "No verdict tag found in response"
  echo "<promise>RETRY</promise>"
  exit 0
fi

echo "VERDICT=$VERDICT"
```

**WAIT** for response. Takes 1-5+ minutes.

---

## Phase 4: Receipt + Status (RP)

### Write receipt (if REVIEW_RECEIPT_PATH set)

Receipt written after SHIP verdict (not on NEEDS_WORK):

```bash
if [[ -n "${REVIEW_RECEIPT_PATH:-}" ]]; then
  ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  mkdir -p "$(dirname "$REVIEW_RECEIPT_PATH")"
  cat > "$REVIEW_RECEIPT_PATH" <<EOF
{"type":"completion_review","id":"$EPIC_ID","mode":"rp","verdict":"SHIP","timestamp":"$ts"}
EOF
  echo "REVIEW_RECEIPT_WRITTEN: $REVIEW_RECEIPT_PATH"
fi
```

**After SHIP from RP: proceed to Adversarial Review Phase (if configured).**

---

## Spec Compliance Fix Loop

**CRITICAL: Do NOT ask user for confirmation. Automatically fix ALL valid issues and re-review. Never use AskUserQuestion in this loop.**

**CRITICAL: You MUST fix the code BEFORE re-reviewing. Never re-review without making changes.**

**MAX ITERATIONS**: Limit fix+re-review cycles to **${MAX_REVIEW_ITERATIONS:-3}** iterations (default 3, configurable in Ralph's config.env). If still NEEDS_WORK after max rounds, output `<promise>RETRY</promise>` and stop.

If verdict is NEEDS_WORK:

1. **Parse issues** - Extract ALL gaps, tag each with severity
2. **Filter by threshold** - Only fix issues where severity is in `SEVERITIES` list
3. **Log below-threshold issues** - Print them but don't fix
4. **Fix the code** - Implement missing functionality for above-threshold issues
5. **Run tests/lints** - Verify fixes don't break anything
6. **Commit fixes** (MANDATORY before re-review):
   ```bash
   git add -A
   git commit -m "fix: address completion review gaps"
   ```
7. **Request re-review** (only AFTER step 6):

   **IMPORTANT**: Do NOT re-add files already in the selection (RP auto-refreshes).

   ```bash
   cat > /tmp/re-review.md << 'EOF'
   Gaps addressed. Please re-review for spec compliance.

   **REQUIRED**: End with `<verdict>SHIP</verdict>` or `<verdict>NEEDS_WORK</verdict>`
   EOF

   $FLUXCTL rp chat-send --window "$W" --tab "$T" --message-file /tmp/re-review.md
   ```
8. **Repeat** until SHIP

**Anti-pattern**: Re-adding already-selected files before re-review. RP auto-refreshes; re-adding can cause issues.

---

## Adversarial Review Phase

**Only runs if BOTH `REVIEWER1` AND `REVIEWER2` are configured in `.flux/config.json`.**

If only one or neither is set, skip directly to External Bot Self-Heal Phase.

### Purpose

Two models from different labs (Anthropic + OpenAI) review the same diff independently. Issues flagged by both = high-confidence consensus issues that almost certainly need fixing. Issues from only one model = lower confidence, filtered by severity threshold.

### Step 1: Prepare Adversarial Diff

```bash
DIFF_BASE="main"
git rev-parse main >/dev/null 2>&1 || DIFF_BASE="master"

# Generate the diff for both reviewers
git diff ${DIFF_BASE}..HEAD > /tmp/adversarial-diff.patch
git diff ${DIFF_BASE}..HEAD --stat > /tmp/adversarial-stat.txt

# Get epic spec for context
EPIC_SPEC="$($FLUXCTL cat "$EPIC_ID")"
```

### Step 2: Build Adversarial Review Prompt

Write a prompt that both models receive (identical input):

```bash
cat > /tmp/adversarial-prompt.md << 'ADVEOF'
## Adversarial Code Review

You are reviewing the implementation of epic [EPIC_ID].

### Epic Spec
[PASTE EPIC SPEC]

### Diff Statistics
[PASTE STAT OUTPUT]

### Full Diff
[PASTE DIFF]

### Instructions

Review this diff for:
1. **Correctness** - Logic errors, missed edge cases, race conditions
2. **Spec compliance** - Does the implementation match the spec?
3. **Architecture** - Data flow, clear boundaries, proper abstractions
4. **Security** - Injection, auth gaps, data exposure
5. **Tests** - Adequate coverage for new functionality

For each issue found:
- **ID**: A-1, A-2, etc. (sequential)
- **Severity**: Critical / Major / Minor / Style
- **File**: File path and line range
- **Problem**: What's wrong
- **Fix**: How to fix it

End with: `<verdict>SHIP</verdict>` or `<verdict>NEEDS_WORK</verdict>`
ADVEOF
```

### Step 3: Send to Both Reviewers

**Reviewer 1** (Anthropic model via Codex or RP — uses same backend as spec review):
```bash
# If using codex backend:
$FLUXCTL codex adversarial-review "$EPIC_ID" --model "$REVIEWER1" --prompt-file /tmp/adversarial-prompt.md > /tmp/review1-response.txt

# If using rp backend, send via RP chat (new chat for adversarial):
$FLUXCTL rp chat-send --window "$W" --tab "$T" --message-file /tmp/adversarial-prompt.md --new-chat --chat-name "Adversarial R1: $EPIC_ID"
```

**Reviewer 2** (OpenAI model via Codex):
```bash
$FLUXCTL codex adversarial-review "$EPIC_ID" --model "$REVIEWER2" --prompt-file /tmp/adversarial-prompt.md > /tmp/review2-response.txt
```

### Step 4: Consensus Merge

Parse issues from both responses and classify:

- **Consensus issues** (flagged by BOTH models): High confidence — add to fix-list regardless of severity
- **Single-model issues** (flagged by only ONE model): Filter by severity threshold
  - At/above `SEVERITIES` threshold → add to fix-list
  - Below threshold → log-only

```
Example:
  R1 flags: A-1 (Critical), A-2 (Major), A-3 (Minor)
  R2 flags: B-1 (Critical, same as A-1), B-2 (Minor, same as A-3)

  Consensus: A-1/B-1 (Critical) → fix
  R1-only: A-2 (Major) → fix (if major in SEVERITIES)
  Consensus: A-3/B-2 (Minor) → fix (consensus overrides threshold)
```

### Step 5: Fix Consensus Issues

If the consensus + filtered issues produce a non-empty fix-list:

1. Fix all issues in fix-list
2. Run tests/lints
3. Commit: `git commit -m "fix: address adversarial review consensus issues"`
4. Optionally re-run adversarial review if critical issues were found (max 2 iterations)

---

## Security Scan Phase

**Auto-triggered when changed files touch security-sensitive areas.**

### Step 1: Detect Security-Sensitive Changes

```bash
DIFF_BASE="main"
git rev-parse main >/dev/null 2>&1 || DIFF_BASE="master"
CHANGED_FILES="$(git diff ${DIFF_BASE}..HEAD --name-only)"

# Security-sensitive patterns
SECURITY_FILES=$(echo "$CHANGED_FILES" | grep -iE '(auth|login|session|token|middleware|permission|rbac|acl|secret|credential|api[-_]?key|security|crypto|encrypt|password|oauth|jwt|cors|csrf|sanitiz|valid)' || echo "")
```

**If `SECURITY_FILES` is empty**: Skip to External Bot Self-Heal Phase.

### Step 2: Run STRIDE Scan

Invoke the `flux-security-review` skill in `staged` mode against the branch diff. This runs the full STRIDE analysis:

- **S** — Spoofing: weak auth, session vulnerabilities, API key exposure
- **T** — Tampering: SQL injection, command injection, XSS, mass assignment
- **R** — Repudiation: missing audit logs, insufficient logging
- **I** — Information Disclosure: IDOR, verbose errors, hardcoded secrets, data leaks
- **D** — Denial of Service: missing rate limiting, ReDoS, resource exhaustion
- **E** — Elevation of Privilege: missing authz checks, privilege escalation

The skill outputs `.flux/security/validated-findings.json` with confirmed vulnerabilities (confidence >= 0.8).

### Step 3: Process Findings

```bash
if [[ -f ".flux/security/validated-findings.json" ]]; then
  FINDINGS_COUNT=$(jq '.summary.confirmed' .flux/security/validated-findings.json)
  echo "Security scan: $FINDINGS_COUNT confirmed findings"
fi
```

1. Parse findings from `validated-findings.json`
2. Filter by severity threshold (same `SEVERITIES` config — map security severities: critical→critical, high→major, medium→minor, low→style)
3. Auto-fix findings in fix-list
4. Commit: `git commit -m "fix: address STRIDE security scan findings"`
5. Re-scan if critical findings were found (max 1 re-scan)

### Step 4: Log Security Summary

Even if all findings are below threshold, log the summary:
```
Security scan complete: N files scanned, M findings (X fixed, Y logged)
```

Security findings are also captured in the Learning Capture phase.

---

## External Bot Self-Heal Phase

**Only runs if `REVIEW_BOT` is configured (`greptile` or `coderabbit`) AND a PR exists.**

### Prerequisite: Ensure PR Exists

```bash
BRANCH="$(git branch --show-current)"
git push -u origin "$BRANCH" 2>/dev/null || true

# Check if PR exists
PR_URL=$(gh pr view --json url -q '.url' 2>/dev/null || echo "")

if [[ -z "$PR_URL" ]]; then
  echo "No PR found for branch $BRANCH. Skipping bot self-heal."
  # Skip to Browser QA
fi
```

### Greptile Backend

Greptile attaches a confidence summary to the PR description. Poll for it:

```bash
MAX_POLLS=20  # 20 × 15s = 5 min timeout
POLL_INTERVAL=15

for i in $(seq 1 $MAX_POLLS); do
  PR_BODY=$(gh pr view --json body -q '.body' 2>/dev/null || echo "")

  # Look for Greptile confidence block
  if echo "$PR_BODY" | grep -q "greptile-confidence"; then
    CONFIDENCE=$(echo "$PR_BODY" | grep -oE 'confidence[: ]+[0-9]+' | grep -oE '[0-9]+' | head -1)
    echo "Greptile confidence: ${CONFIDENCE}%"
    break
  fi

  echo "Waiting for Greptile review... (${i}/${MAX_POLLS})"
  sleep $POLL_INTERVAL
done
```

If confidence is below 80% or Greptile flagged issues:

1. Parse issue list from PR description (Greptile embeds issues in the confidence block)
2. Filter by severity threshold
3. Fix issues in fix-list
4. Commit and push
5. Re-poll for updated confidence (max 2 iterations)

### CodeRabbit Backend

CodeRabbit posts review comments on the PR:

```bash
# Option 1: CLI (if installed)
if command -v coderabbit >/dev/null 2>&1; then
  coderabbit review --pr "$PR_URL" > /tmp/coderabbit-review.txt
fi

# Option 2: Poll PR comments
MAX_POLLS=20
POLL_INTERVAL=15

for i in $(seq 1 $MAX_POLLS); do
  COMMENTS=$(gh api "repos/{owner}/{repo}/pulls/$(gh pr view --json number -q '.number')/comments" 2>/dev/null || echo "[]")

  # Look for CodeRabbit comments
  CR_COMMENTS=$(echo "$COMMENTS" | jq '[.[] | select(.user.login == "coderabbitai")]')
  CR_COUNT=$(echo "$CR_COMMENTS" | jq 'length')

  if [[ "$CR_COUNT" -gt 0 ]]; then
    echo "CodeRabbit posted $CR_COUNT review comments"
    break
  fi

  echo "Waiting for CodeRabbit review... (${i}/${MAX_POLLS})"
  sleep $POLL_INTERVAL
done
```

If CodeRabbit flagged issues:

1. Parse issues from comments (each comment = one issue)
2. Filter by severity threshold
3. Fix issues in fix-list
4. Commit and push
5. Wait for CodeRabbit to re-review (max 2 iterations)

### Bot Self-Heal Fix Loop

**Same rules as spec compliance fix loop: no user confirmation, auto-fix, commit before re-check.**

1. Parse bot issues
2. Filter by severity → fix-list vs log-only
3. Fix code for fix-list items
4. Run tests/lints
5. Commit: `git commit -m "fix: address <bot-name> review feedback"`
6. Push: `git push`
7. Re-poll bot for updated verdict (max 2 iterations)

---

## Browser QA Phase

**Only runs if ALL of these are true:**
1. `agent-browser` is available: `command -v agent-browser >/dev/null 2>&1`
2. A "Browser QA Checklist" task exists for this epic (created during `/flux:scope`)

During scoping, Flux auto-creates a Browser QA Checklist task for epics involving frontend/web changes. This task contains structured, testable criteria that this phase follows — no guesswork needed.

### Step 1: Check Prerequisites

```bash
if ! command -v agent-browser >/dev/null 2>&1; then
  echo "agent-browser not found. Skipping browser QA."
  # Skip to Learning Capture
fi

# Look for Browser QA Checklist task in this epic
QA_TASK=$($FLUXCTL tasks --epic "$EPIC_ID" --json | jq -r '.[] | select(.title | test("Browser QA|browser.qa"; "i")) | .id' | head -1)

if [[ -z "$QA_TASK" ]]; then
  echo "No Browser QA Checklist task found for $EPIC_ID. Skipping browser QA."
  # Skip to Learning Capture
fi
```

### Step 2: Read QA Checklist

```bash
# Get the QA task spec with acceptance criteria
QA_SPEC=$($FLUXCTL task show "$QA_TASK" --json)
```

The checklist task contains structured acceptance criteria like:
```
- [ ] Navigate to /dashboard — verify stats cards render with data
- [ ] Click "Add Item" button — verify modal opens with form fields
- [ ] Submit form with valid data — verify success toast and item appears in list
- [ ] Navigate to /settings — verify all toggle switches reflect saved state
```

Each criterion specifies: URL/action, expected result, and what to verify.

### Step 3: Execute Browser Tests

For each criterion in the checklist:

```bash
# Open the target URL
agent-browser open <url>
agent-browser wait --load networkidle

# Take snapshot to discover interactive elements
agent-browser snapshot -i

# Perform action (click, fill, navigate) based on criterion
agent-browser click @e1  # or fill, select, etc.

# Verify expected result
agent-browser wait --text "Expected text"
agent-browser snapshot -i  # Re-snapshot after action

# Take screenshot for evidence
agent-browser screenshot "/tmp/qa-${EPIC_ID}-${n}.png"
```

### Step 4: Handle Failures

If any criterion fails:

1. Log the failure with screenshot path and expected vs actual
2. Fix the code to address the UI issue
3. Run tests/lints
4. Commit: `git commit -m "fix: address browser QA failure - <criterion>"`
5. Re-test the failing criterion
6. Max 2 fix iterations per criterion

### Step 5: Mark QA Task Complete

After all criteria pass:

```bash
$FLUXCTL done "$QA_TASK"
agent-browser close
```

---

## Learning Capture Phase

**Always runs after the full pipeline reaches SHIP (or after max iterations).**

### What to Capture

Review all NEEDS_WORK iterations across the pipeline and extract generalizable patterns:

1. **Spec compliance gaps** — requirements that drifted from spec during implementation
2. **Adversarial consensus patterns** — issues both models flagged (these are high-signal patterns the worker should learn)
3. **Security scan findings** — STRIDE vulnerabilities caught post-implementation (auth gaps, injection vectors, data exposure)
4. **Bot-caught patterns** — recurring issues Greptile/CodeRabbit caught that models missed
5. **Browser QA failures** — UI/UX issues missed during implementation

### How to Capture

Write each learning to a separate file in `brain/pitfalls/<area>/`, organized by area of concern:

```bash
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
PITFALLS_DIR="$REPO_ROOT/brain/pitfalls"

# 1. Determine the area from the pitfall's domain
#    Check existing areas first: ls "$PITFALLS_DIR"
#    Common areas: frontend, backend, security, async, api, database, testing, infra
#    Create new area directory if none of the existing ones fit
AREA="frontend"
mkdir -p "$PITFALLS_DIR/$AREA"

# 2. One file per learning, filename = pattern slug
cat > "$PITFALLS_DIR/$AREA/missing-error-states.md" << 'EOF'
# Missing Error States

UI components lacked error/empty states specified in acceptance criteria.

**Source**: epic-review (fn-3-dashboard)
**Date**: 2026-03-14
EOF
```

**Area selection rules:**
1. Check existing area directories in `brain/pitfalls/` — use one if it fits
2. If no existing area matches, create a new directory with a short, descriptive slug
3. Keep areas broad enough to group related pitfalls (e.g., `frontend` not `react-forms`)
4. When in doubt, check what's already there: `ls brain/pitfalls/`

After writing pitfall files, update `brain/index.md` to include new entries under the `## Pitfalls` section.

Examples:
- `brain/pitfalls/frontend/missing-error-states.md` — UI components lacked error/empty states
- `brain/pitfalls/async/consensus-race-condition.md` — Both models flagged unsynchronized state updates
- `brain/pitfalls/security/greptile-auth-gap.md` — Greptile caught missing auth check on new endpoint

### Feedback Loop

These pitfalls feed back into the worker automatically:
- Worker reads only the relevant `brain/pitfalls/<area>/` subdirectories during re-anchor (matched to the current task's domain)
- Worker reads `brain/principles/` for engineering principles that guide implementation
- Future tasks benefit from patterns learned in past epic reviews — without loading irrelevant pitfalls
- Over time, fewer NEEDS_WORK iterations as the worker learns common mistakes
- `/flux:meditate` periodically promotes recurring pitfalls into proper principles and prunes one-offs

Only capture generalizable patterns, not one-off fixes.

---

## Desloppify Scan Phase

**Optional. Only runs if `desloppify` is installed. Scan-only — no fix loop.**

The purpose is to surface quality regressions (dead code, duplication, complexity) introduced during the epic, not to fix them inline.

```bash
if command -v desloppify >/dev/null 2>&1; then
  # Get top-level directories touched in this epic
  CHANGED_DIRS=$(git diff "${DIFF_BASE}"..HEAD --name-only | xargs -I{} dirname {} | sort -u | grep -v '^\.$')

  if [ -n "$CHANGED_DIRS" ]; then
    echo "=== Desloppify Scan (changed directories) ==="
    for DIR in $CHANGED_DIRS; do
      if [ -d "$DIR" ]; then
        desloppify scan --path "$DIR" 2>/dev/null
      fi
    done
  fi
fi
```

- If score is below 85, suggest: `"Consider running /flux:desloppify to address quality issues introduced in this epic."`
- Do NOT auto-install desloppify — skip silently if not available.
- Do NOT enter a fix loop — this is informational only.

---

## Frustration Signal

Track `NEEDS_WORK_COUNT` across all fix loops in this pipeline (spec compliance, adversarial, bot self-heal). Increment the counter each time a NEEDS_WORK verdict is received from any reviewer or bot.

If `NEEDS_WORK_COUNT >= 3` after the pipeline completes, output:

```
---
**Friction detected**: This epic required {NEEDS_WORK_COUNT} review fix iterations.
Repeated rework may indicate workflow gaps — missing linters, outdated
conventions, or tools that could catch these issues earlier.

Consider running `/flux:improve` to analyze your patterns and get
targeted recommendations from the Flux recommendations engine.
---
```

This is a suggestion only — do not auto-invoke `/flux:improve`. The user decides whether to act on it.

Common causes of high iteration counts:
- Missing lint/format rules that reviewers keep catching
- Stale brain pitfalls that haven't been promoted to structural enforcement
- Missing test coverage for edge cases
- Tools that could pre-validate (e.g., desloppify, security-scan) not installed

---

## Anti-patterns

**All backends:**
- **Reviewing yourself** - You coordinate; the backend reviews
- **No receipt** - If REVIEW_RECEIPT_PATH is set, you MUST write receipt
- **Ignoring verdict** - Must extract and act on verdict tag
- **Mixing backends** - Stick to one backend for the entire review session
- **Checking code quality** - That's impl-review's job; focus on spec compliance
- **Skipping severity filter** - Always filter issues by configured threshold
- **Fixing log-only issues** - Below-threshold issues are logged, not fixed (unless consensus)

**RP backend only:**
- **Calling builder directly** - Must use `setup-review` which wraps it
- **Skipping setup-review** - Window selection MUST happen via this command
- **Hard-coding window IDs** - Never write `--window 1`
- **Missing task specs** - Add ALL task specs to selection

**Codex backend only:**
- **Using `--last` flag** - Conflicts with parallel usage; use `--receipt` instead
- **Direct codex calls** - Must use `fluxctl codex` wrappers

**Adversarial review:**
- **Using same lab for both models** - Must be different labs (Anthropic + OpenAI)
- **Skipping consensus merge** - Both responses must be parsed and merged
- **Auto-fixing single-model minor issues** - Only consensus or above-threshold

**Security scan:**
- **Scanning non-security changes** - Only run when security-sensitive files are changed
- **Ignoring confidence scores** - Only act on findings with confidence >= 0.8
- **Re-scanning endlessly** - Max 1 re-scan after fixes

**Bot self-heal:**
- **Polling without timeout** - Always use max poll count
- **Pushing without PR** - Bot needs a PR to review
- **Infinite fix loops** - Max 2 iterations per bot

**Browser QA:**
- **Testing without checklist** - Skip if no Browser QA Checklist task exists
- **Guessing test criteria** - Always follow the checklist from scoping, don't invent tests
- **Leaving browser open** - Always close session when done
