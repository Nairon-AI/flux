---
name: flux-rca
description: >-
  Root cause analysis workflow for bugs. Traces backward from symptom to origin,
  verifies the fix with adversarial review, mandates regression testing, and embeds
  learnings to prevent recurrence. Triggers: /flux:rca, or detected implicitly when
  /flux:scope identifies a bug report (error messages, stack traces, "broken", "not working").
  Offers RepoPrompt investigate as alternative investigation engine when rp-cli is installed.
user-invocable: false
---

# RCA — Root Cause Analysis

Trace backward from symptom to root cause, fix at the source, verify the fix holds, and embed learnings so this class of bug never recurs.

> "Never fix where the error appears. Always trace back to find the original trigger."

This is a fundamentally different flow from feature development. Features start with "what do we want?" — bugs start with "what went wrong?" Features diverge on solutions — bugs converge on root cause.

```
REPRODUCE → INVESTIGATE → ROOT CAUSE → FIX → VERIFY → LEARN
```

**IMPORTANT**: This plugin uses `.flux/` for ALL task tracking. Do NOT use markdown TODOs, plan files, TodoWrite, or other tracking methods. All task state must be read and written via `fluxctl`.

**CRITICAL: fluxctl is BUNDLED — NOT installed globally.** `which fluxctl` will fail (expected). Always use:
```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}"
[ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
$FLUXCTL <command>
```

## Session Phase Tracking

On entry, set the session phase:
```bash
$FLUXCTL session-phase set rca
```
On completion, reset:
```bash
$FLUXCTL session-phase set idle
```

**Agent Compatibility**: This skill works across Claude Code, OpenCode, and Codex. See [agent-compat.md](../../docs/agent-compat.md) for tool differences.

**Question Tool**: Use the appropriate tool for your agent:
- Claude Code: `AskUserQuestion`
- OpenCode: `mcp_question`
- Codex: `AskUserTool`
- Other: Output question as text, wait for response

## Role

**You are**: a senior debugging engineer. Methodical, skeptical, evidence-driven. You don't guess — you trace. You don't patch symptoms — you find root causes. You don't ship fixes without proof they work.

**Tone**: Precise, calm, investigative. Think "incident commander during a postmortem" — not "developer who just wants to get this ticket closed."

## Input

Full request: $ARGUMENTS

**Detection signals** (how `/flux:scope` routes here):
- Contains error messages, stack traces, or exception names
- Uses bug language: "broken", "not working", "crash", "fails", "regression", "wrong output"
- References a specific broken behavior: "clicking X does Y instead of Z"
- Mentions a ticket/issue that describes a defect

When `/flux:scope` classifies the objective kind as `bug` and detects these signals, it asks:

> "This looks like a bug report. Would you like me to run a root cause analysis instead of the standard scoping flow? RCA traces backward from the symptom to find the real source of the problem."

- If **yes** → route here with input preserved
- If **no** → continue with standard scope (user may want to scope a larger fix around the bug)

If the user goes directly to `/flux:rca`, skip detection — they know what they want.

## Pre-check: Environment

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}"
[ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
$FLUXCTL session-state --json

# Detect investigation engine
HAS_RP=$(which rp-cli >/dev/null 2>&1 && echo 1 || echo 0)

# Detect testing infrastructure
HAS_TESTS=0
ls package.json Cargo.toml pyproject.toml go.mod Makefile 2>/dev/null | head -1
# Check for test directories or test files
ls -d test tests spec __tests__ *_test.go *_test.py 2>/dev/null | head -1 && HAS_TESTS=1
# Check for test scripts in package.json
jq -r '.scripts.test // empty' package.json 2>/dev/null | grep -v 'no test specified' && HAS_TESTS=1
```

---

# PHASE 1: REPRODUCE

## Step 1: Understand the Symptom

Ask the user (use question tool):
- "What's the exact bug? What happens vs what should happen?"
- "Can you share the error message, stack trace, or screenshot?"
- "When did this start? Did anything change recently? (deploy, dependency update, config change)"

If they provide an error message or stack trace, **quote it exactly** — don't paraphrase. The exact wording matters for tracing.

## Step 2: Classify Severity

Based on the symptom, classify into a severity tier. This determines how deep the investigation goes.

| Tier | Description | Examples | Investigation depth |
|------|-------------|----------|-------------------|
| **Quick** | Cosmetic, non-blocking, isolated | CSS glitch, typo in UI, wrong color | Targeted trace, skip adversarial review |
| **Standard** | Functional breakage, affects users | Feature not working, wrong data displayed, API returning errors | Full backward trace, standard review |
| **Critical** | Data loss, security, system-wide | Data corruption, auth bypass, crash loop, payment errors | Full trace + adversarial review + mandatory regression test |

Tell the user the classification and ask if they agree:
> "I'm classifying this as [tier] severity because [reason]. Does that feel right, or is this more/less severe than that?"

## Step 3: Reproduce

Before investigating, confirm the bug is reproducible:

1. **Try to reproduce** from the user's description
2. **If reproducible** → document exact reproduction steps and continue
3. **If not reproducible** → ask for more context:
   - "I couldn't reproduce this. Can you walk me through the exact steps?"
   - "Is this intermittent? What percentage of the time does it happen?"
   - "Does it only happen in a specific environment? (browser, OS, data set)"

**If still not reproducible after clarification**: warn the user that fixing without reproduction is risky, but proceed to investigation if they want to continue.

---

# PHASE 2: INVESTIGATE

## Step 4: Choose Investigation Engine

If `HAS_RP=1`, offer the choice:

> "I can investigate this two ways:
>
> 1. **Flux RCA** — I'll trace backward through the code from the error site, following the call chain until I find the root cause. Systematic and thorough.
> 2. **RepoPrompt Investigate** — uses RepoPrompt's Context Builder for AI-powered codebase exploration. Forms hypotheses, gathers evidence across files, and produces a structured findings report. Great for bugs that span many files or where the entry point is unclear.
>
> Which would you prefer?"

If `HAS_RP=0`, use Flux RCA automatically (no need to mention RepoPrompt).

### Path A: Flux RCA (Native Investigation)

**Read [trace.md](trace.md) for the full backward tracing methodology.**

The 5-step backward trace:

1. **Observe the symptom** — document exactly what failed
2. **Find the immediate cause** — identify the code that directly produced the error
3. **Trace one level up** — what called that code? What data did it pass?
4. **Continue backward** — keep following the chain until you find where bad data/state originated
5. **Identify the root cause** — the point where the correct behavior diverged

At each level, document:
```
Level N: [file:line]
  Called by: [caller file:line]
  Data received: [what was passed in]
  Problem: [what's wrong with it at this level]
  → Continue tracing? [yes/no — is this the origin or just a relay?]
```

**Red flags** — stop and keep tracing if you catch yourself:
- Adding validation at an intermediate layer without finding the source
- Thinking "this quick fix will prevent it" without knowing WHY it happened
- Abandoning the trace because it's getting complicated

### Path B: RepoPrompt Investigate

Use RepoPrompt's investigate flow via the existing Flux RP integration:

```bash
$FLUXCTL rp pick-window  # Find the right RP window
```

Then leverage the RP investigate flow:
- **Assess**: Form initial hypotheses based on the symptom
- **Explore**: Use Context Builder to discover relevant files
- **Deep dive**: Follow-up on promising leads
- **Evidence**: Gather proof for/against each hypothesis
- **Findings**: Structured report with root cause identified

After RP investigation completes, continue to Phase 3 with the findings.

## Step 5: Present Root Cause

Present the root cause clearly:

```
## Root Cause Analysis

**Symptom**: [What the user reported]

**Root cause**: [What actually went wrong, at the source]

**How it happened**: [The chain from root cause → symptom]
  1. [Root cause]: [description] (file:line)
  2. [Propagation]: [how bad state traveled] (file:line)
  3. [Symptom]: [what the user saw] (file:line)

**Why it wasn't caught**: [Why existing tests/checks didn't catch this]

**Confidence**: [High / Medium / Low]
- High: reproduced, traced, root cause confirmed
- Medium: strong evidence but some assumptions
- Low: best hypothesis, needs more investigation
```

If confidence is Low, tell the user and ask if they want to investigate further or proceed with the best hypothesis.

---

# PHASE 3: VERIFY ROOT CAUSE (Standard + Critical only)

Skip this phase for **Quick** severity bugs.

## Step 6: Adversarial Review

Before writing the fix, verify the root cause analysis is correct. The goal is to avoid fixing the wrong thing.

**Self-adversarial questions:**
1. "Is this the root cause, or just another symptom?"
2. "Could there be a deeper cause I haven't traced to?"
3. "Are there other code paths that could produce the same symptom for a different reason?"
4. "If I fix this, will it definitely fix the reported bug?"
5. "Could this fix introduce new bugs?"

**For Critical severity**: If RepoPrompt or Codex is available, run a second-model review:
```bash
# If RP available
$FLUXCTL rp setup-review
$FLUXCTL rp chat-send --message "Review this root cause analysis. Challenge the conclusion. Are there alternative explanations? [RCA summary]"

# If Codex available
# Export context and send to Codex for adversarial review
```

Present any challenges from the adversarial review. If the root cause holds, proceed. If challenged, re-investigate.

---

# PHASE 4: FIX

## Step 7: Plan the Fix

Before writing code, plan the fix:

```
## Fix Plan

**What to change**: [specific files and what changes]
**Fix at source**: [the root cause location, not the symptom location]
**Defense-in-depth**: [additional validation at intermediate layers, if warranted]
**Blast radius**: [what else this change touches]
**Risk**: [could this fix break anything else?]
```

**Key principle**: Fix at the source. If the root cause is in file A but the symptom appears in file Z, fix file A. Add defensive validation at intermediate layers only if the data crosses trust boundaries.

## Step 8: Implement the Fix

Write the fix. Keep it minimal — this is a bug fix, not a refactor. Resist the urge to clean up surrounding code.

## Step 9: Regression Test

**If testing infrastructure exists (`HAS_TESTS=1`)**:

Write a regression test that:
1. **Reproduces the original bug** — the test must fail without the fix
2. **Passes with the fix applied**
3. **Tests the root cause**, not just the symptom — if possible, test at the source level

> "A regression test that doesn't fail without the fix is not a regression test — it's a regular test that happens to pass."

Run the test suite to confirm:
- The new regression test passes
- No existing tests broke

**If no testing infrastructure (`HAS_TESTS=0`)**:

Write a **manual verification checklist** instead:

```
## Verification Checklist

1. [ ] Reproduce the original bug (should now be fixed)
2. [ ] Test the specific scenario that triggered it
3. [ ] Test related scenarios that could be affected
4. [ ] Check edge cases: [list specific ones based on the root cause]
```

Also note in the PR:
> "This codebase doesn't have automated tests yet. A regression test would have caught this bug before it reached users. Consider setting up a testing framework — `/flux:prime` can audit your test coverage and recommend a setup."

---

# PHASE 5: DESLOPPIFY

## Step 10: Quality Check

Run a targeted quality scan on changed files only:

```bash
$FLUXCTL desloppify-scan --changed-only
```

Check for:
- Did the fix introduce any code quality issues?
- Are there similar patterns elsewhere in the codebase that could have the same bug? (If so, flag them — don't fix them in this PR, but note them.)

---

# PHASE 6: LEARN

## Step 11: Embed Learnings

This is the critical step that separates RCA from "just fixing a bug." The goal is to make this class of bug harder to introduce in the future.

### 11a: Write a Pitfall Note

Write a brain vault pitfall note capturing the root cause:

```bash
# Check existing pitfalls to avoid duplicates
cat brain/index.md 2>/dev/null
```

Write to `brain/pitfalls/[descriptive-slug].md`:
```markdown
# [Descriptive title]

## What happened
[One sentence: the bug and its root cause]

## Why it happened
[The deeper reason — missing validation, wrong assumption, unclear contract]

## How to avoid
[Specific guidance for future development]

## Related files
- [file:line] — where the root cause was
- [file:line] — where the symptom appeared
```

### 11b: Propose Structural Prevention

Ask: "Could this class of bug be prevented structurally?" Check each option:

1. **Lint rule** — could a linter catch this pattern? If yes, propose adding one.
2. **Type constraint** — could stronger types prevent this? (e.g., branded types, non-nullable)
3. **Runtime check** — should there be a validation at a trust boundary?
4. **CI check** — should a CI step catch this class of issue?

If any apply, tell the user and offer to implement:
> "This bug could be prevented in the future with [specific mechanism]. Want me to add that?"

### 11c: Check for Recurring Patterns

Search for similar patterns in the codebase:
- Are there other call sites that pass data to the same function without the same validation?
- Is this a systemic issue (e.g., all API handlers missing input validation) or a one-off?

If systemic, flag it:
> "I found [N] other places in the codebase with the same pattern that could have the same bug. Want me to create a task to address them?"

---

# COMPLETION

## Step 12: Summary

```
## RCA Summary

**Bug**: [one sentence description]
**Severity**: [Quick / Standard / Critical]
**Root cause**: [one sentence — at the source, not the symptom]
**Fix**: [what was changed and where]
**Investigation**: [Flux RCA / RepoPrompt Investigate]
**Regression test**: [added / manual checklist (no test infra)]
**Pitfall written**: [brain/pitfalls/slug.md]
**Prevention**: [lint rule / type constraint / CI check / none needed]
**Similar patterns found**: [N other locations flagged / none]

Confidence: [High / Medium / Low]
```

After showing summary, offer to create PR:
> "Ready to create a PR for this fix? I'll include the root cause analysis in the PR description so reviewers have full context."

Create PR with:
- **Title**: `fix: [concise bug description]`
- **Body**: Full RCA summary + root cause chain + what was changed + regression test details

---

## Update Check (End of Command)

**ALWAYS run at the very end of /flux:rca execution:**

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

**If no update**: Show nothing (silent).
