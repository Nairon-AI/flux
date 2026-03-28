---
name: flux-scope
description: Use when scoping a new feature, refactor, or ambiguous bugfix into a concrete Flow objective. Guides Start, Discover, Define, Develop, Deliver, and Handoff; supports shallow mode by default and `--deep` for the full staged flow.
user-invocable: false
---

# Flow scope

Turn a rough idea into a well-defined objective using a Product OS-style workflow adapted for engineering.

**Flux Scope Flow:**
```
START -> DISCOVER -> DEFINE -> DEVELOP -> DELIVER -> HANDOFF
```

**Modes**:
- **Shallow (default)**: ~10 min total. Compressed scoping for smaller or clearer work.
- **Deep (`--deep`)**: ~45 min total. Full staged workflow with stronger gates, more edge cases, and richer handoff.
- **Explore (`--explore [N]`)**: Generate N competing approaches, scaffold each in parallel, compare visually, pick winner.

> "Understand the problem before solving it. Most failed features solve the wrong problem."
> "Write ten specs. Test them all. Throw away nine."

**IMPORTANT**: This plugin uses `.flux/` for ALL task tracking. Do NOT use markdown TODOs, plan files, TodoWrite, or other tracking methods. All task state must be read and written via `fluxctl`.

**CRITICAL: fluxctl is BUNDLED — NOT installed globally.** `which fluxctl` will fail (expected). Always use:
```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
[ ! -d "$PLUGIN_ROOT/scripts" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
$FLUXCTL <command>
```

## Session Phase Tracking

On entry, set the session phase:
```bash
$FLUXCTL session-phase set scope
```
On completion (handoff done), reset:
```bash
$FLUXCTL session-phase set idle
```

**Agent Compatibility**: This skill works across Codex, OpenCode, and legacy Claude environments. See [agent-compat.md](../../docs/agent-compat.md) for tool differences.

**Question Tool**: Use the appropriate tool for your agent:
- Claude: `AskUserQuestion`
- OpenCode: `mcp_question`
- Codex: `AskUserTool`
- Other: Output question as text, wait for response

## Pre-check: Local setup version

If `.flux/meta.json` exists and has `setup_version`, compare to plugin version:
```bash
SETUP_VER=$(jq -r '.setup_version // empty' .flux/meta.json 2>/dev/null)
PLUGIN_ROOT="${PLUGIN_ROOT}"
[ ! -d "$PLUGIN_ROOT/scripts" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
PLUGIN_JSON="${PLUGIN_ROOT}/.claude-plugin/plugin.json"
PLUGIN_VER=$(jq -r '.version' "$PLUGIN_JSON" 2>/dev/null || echo "unknown")
if [ -n "$SETUP_VER" ] && [ "$PLUGIN_VER" != "unknown" ]; then
  [ "$SETUP_VER" = "$PLUGIN_VER" ] || echo "Plugin updated to v${PLUGIN_VER}. Run /flux:setup to refresh local scripts (current: v${SETUP_VER})."
fi
```
Continue regardless (non-blocking).

**State Machine**: See [docs/state-machine.md](../../docs/state-machine.md) for the formal workflow state diagram, valid transitions, and routing rules. This skill is the primary entry point from `fresh_session_no_objective` state.

**Role**: product-minded technical interviewer and planner
**Goal**: understand the problem deeply, keep the user aligned to the current workflow, then create actionable implementation context

## Input

Full request: $ARGUMENTS

**Options**:
- `--quick` / default shallow mode: compressed Product OS flow, ~10 min total
- `--deep`: Full staged scoping, ~45 min total
- `--explore [N]`: Generate N approaches (default 3), scaffold each in parallel, compare visually
- `--linear`: Connect to Linear MCP, browse teams/projects, select issue to scope
- `LIN-123` (or any `XXX-123` pattern): Directly scope a specific Linear issue

Accepts:
- Feature/bug description in natural language
- File path to spec document
- Linear issue identifier (e.g., `LIN-123`, `PROJ-456`)

Examples:
- `/flux:scope Add OAuth login for users`
- `/flux:scope Add user notifications --deep`
- `/flux:scope docs/feature-spec.md`
- `/flux:scope Add permissions system --explore 4`
- `/flux:scope Add dashboard --explore --deep`
- `/flux:scope --linear` — Browse Linear, select issue to scope
- `/flux:scope LIN-42` — Scope Linear issue LIN-42 directly
- `/flux:scope PROJ-123 --deep` — Deep scope Linear issue PROJ-123

If empty, ask: "What should I scope? Describe the feature or bug in 1-5 sentences."

## Load Business And Architecture Context

Before starting any detection or interview, silently load business context if it exists:

```bash
cat .flux/brain/business/context.md 2>/dev/null
cat .flux/brain/business/glossary.md 2>/dev/null
cat .flux/brain/codebase/architecture.md 2>/dev/null
.flux/bin/fluxctl architecture status --json 2>/dev/null
```

If business context exists:
- **Product stage** informs how hard the viability gate pushes on user validation (pre-launch = push harder on "who would use this?"; established product = ask for data/metrics)
- **Glossary** ensures domain terms are interpreted correctly throughout the interview — never misinterpret domain-specific language
- **Team structure** determines whether to watch for deferred authority signals ("my co-founder said...") and whether to route to propose
- **Area-specific files** (`.flux/brain/business/billing.md`, etc.) provide context when the scope touches those areas — read them when relevant
- **Architecture diagram** provides the current high-level system map — use it when reasoning about boundaries, integrations, trust zones, and likely blast radius

If no business context exists: continue normally.

## Detect Stakeholder vs Engineer

Before detecting mode, check if the user is a non-technical stakeholder rather than an engineer.

**Skip detection entirely if ANY of these are present** (strong engineer signals):
- Mentions specific files, paths, or line numbers
- References APIs, endpoints, databases, schemas, components, services, or architecture
- Uses technical verbs: "refactor", "migrate", "deploy", "integrate", "implement"
- Includes code snippets, error messages, or stack traces

**Detection signals** (check the input text if no engineer signals found):
- Language focuses on **outcomes** not implementation ("I want users to be able to..." vs "Add an API endpoint for...")
- Describes **what** without **how**
- Talks about business goals, customer needs, revenue, or user experience
- Uses non-technical framing: "customers want...", "our team needs...", "it would be great if..."

If 3+ signals are present and zero engineer signals, ask:

> "It sounds like you're describing what you'd like built rather than how to build it. Are you an engineer planning to implement this, or are you proposing a feature for the engineering team?"

- If **stakeholder** → hand off to `flux-propose` skill with their input preserved. Stop here.
- If **engineer** → continue with `/flux:scope` normally.

## Detect Bug vs Feature

After stakeholder detection, check if this is a bug report that should route to RCA.

**Bug signals** (check the input text):
- Contains error messages, stack traces, or exception names
- Uses bug language: "broken", "not working", "crash", "fails", "regression", "wrong output", "bug"
- Describes incorrect behavior: "X does Y instead of Z", "used to work but now..."
- References a defect ticket or incident

If bug signals are strong, ask:

> "This looks like a bug report. Would you like me to run a root cause analysis instead of the standard scoping flow? RCA traces backward from the symptom to find the real source of the problem."

- If **yes** → hand off to `flux-rca` skill with their input preserved. Stop here.
- If **no** → continue with `/flux:scope` normally (user may want to scope a larger fix around the bug).

If unclear (could be a bug or a feature gap), ask:

> "Am I right in thinking this is a bug? Or is this more of a missing feature / improvement?"

## Detect Mode

Parse arguments for `--deep` flag. Default is shallow mode.

```
SCOPE_MODE = "--deep" in arguments ? "deep" : "shallow"
```

## Detect "Remember" Request

Before scoping, check if the user is actually asking to remember something, not to scope a feature.

**Detection signals:**
- Input starts with "remember", "don't forget", "keep in mind", "note that", "from now on"
- Input contains "always ..." or "never ..." as a rule/constraint (not a question)

If detected → **hand off to `flux-brain` skill** (which handles the "Remember" flow). Stop here.

## Session Realignment

Before asking new scoping questions, check current workflow state:

```bash
$FLUXCTL session-state --json
```

If there is an active scoped objective, resume it instead of silently starting over.
If there is active implementation work, tell the user and only re-enter scope if they clearly want to switch objectives.
Flux should always prefer alignment with `.flux/` state over treating each prompt as stateless.

## Detect Linear Mode

Check for `--linear` flag or Linear issue ID pattern (e.g., `LIN-123`, `PROJ-456`).

```
LINEAR_MODE = "--linear" in arguments
LINEAR_ISSUE_ID = extract pattern matching /[A-Z]+-\d+/ from arguments
```

If `LINEAR_ISSUE_ID` is found, set `LINEAR_MODE = true`.

**If LINEAR_MODE**: Read [linear.md](linear.md) for the full Linear integration flow (Steps 0.1-0.7). After completing, continue to Phase 1 with Linear context pre-loaded.

## Setup

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
[ ! -d "$PLUGIN_ROOT/scripts" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
$FLUXCTL init --json
```

---

# PHASE 1: PROBLEM SPACE

**Read [questions.md](questions.md) for the full question bank and guidelines.**
**See [phases.md](phases.md) for phase overview and anti-patterns.**

Walk through Steps 1-6 using the question tool. Each step has quick-mode and deep-mode variants.

| Step | Focus | Goal |
|------|-------|------|
| 1. Core Desire | WHY | Understand why this is being requested |
| 2. Reasoning Chain | LOGIC | Validate the logic from problem to solution |
| 3. User Perspective | WHO | Understand how users will experience this |
| 4. Blind Spots | GAPS | Surface what might be missing |
| 5. Risks | DANGER | Identify what could go wrong |
| 5.5. Viability Gate | SHOULD WE? | Honest assessment — is this worth building? |
| 6. Problem Statement | CONVERGE | Synthesize into one clear statement |

### Step 5.5: Viability Gate (SHOULD WE BUILD THIS?)

After Steps 1-5, the agent has heard the user's reasoning, user perspective, blind spots, and risks. Before writing a problem statement, **honestly evaluate whether this should be built at all**.

Synthesize everything heard so far and check for these red flags:

| Red Flag | Signal |
|----------|--------|
| **No real user need** | User can't articulate who wants this or their current workaround. "It would be cool" is not a need. |
| **Solution looking for a problem** | The reasoning goes technology → feature, not problem → solution. "We should use X" instead of "users struggle with Y." |
| **Cost of inaction is zero** | When asked "what happens if we don't build this?" the answer was vague or trivial. |
| **Simpler alternative exists** | A config change, existing tool, or 10-line fix would solve 80% of the problem. |
| **Building on unvalidated assumptions** | Core UX or architecture decisions are based on "I think users want..." without any evidence. |
| **Scope exceeds value** | The estimated effort far exceeds the problem's impact. |

**If 2+ red flags are present**, the agent MUST present an honest assessment:

```
Before I write the problem statement, I want to be direct:

Based on what you've told me, I have concerns about building this:

- [Red flag 1]: [specific evidence from conversation]
- [Red flag 2]: [specific evidence from conversation]

My honest recommendation: [one of:]
  - "This isn't worth building right now. Here's why: [reason]"
  - "A simpler approach would solve this: [alternative]"
  - "This is worth building, but not the way we discussed. Here's what I'd change: [reframe]"
  - "We don't have enough information to build this well. Before writing code, we need: [what to validate]"

You know your context better than I do — if you disagree, tell me why and we'll continue.
But I'd rather push back now than let you build something that doesn't make sense.
```

**If 0-1 red flags** → proceed to Step 6 normally.

**This is not a gate that blocks progress.** The user can override it. But the agent must give its honest opinion — not just validate whatever the user wants to hear. The goal is to catch the cases where Claude would normally say "great idea, let me build that" when it should be saying "are you sure?"

---

**Step 6 output** — present synthesis and confirm:
```
Based on our discussion:
- Core need: [summary]
- Key assumptions: [list]
- User impact: [summary]
- Main risk: [summary]

Proposed problem statement:
"[One sentence problem statement]"

Does this capture it? What would you change?
```

---

# STEP 6.05: UBIQUITOUS LANGUAGE CHECK (auto after Step 6)

After the problem statement is confirmed, check if domain terminology is ambiguous. Signals:
- The user used different words for the same concept during Steps 1-6
- Domain terms overlap with technical terms (e.g., "account" meaning both billing and auth)
- The codebase uses inconsistent naming for the same domain concept (found during business context load)
- No `.flux/brain/business/glossary.md` exists yet and this is a domain-heavy feature

If signals are present, offer:

```
I noticed some domain terms were used inconsistently during scoping
(e.g., "[term A]" and "[term B]" seem to mean the same thing).

Want to harden the terminology before we plan? This takes ~3 min and
produces a glossary that all future tasks will reference.
[y/n]
```

- If **yes** → invoke `/flux:ubiquitous-language`. The glossary feeds into task specs and is read by workers during re-anchor.
- If **no** → continue to Step 6.1.

---

# STEP 6.1: ASSUMPTION STRESS TEST (auto-triggers after Step 6)

After the problem statement is confirmed, scan the conversation (Steps 1-6) for these signals:

**Detection signals** (check conversation for ANY match):
- **One-way door decisions** — architecture choices, auth strategy, data model, API contracts, technology lock-in, security model
- **UX assumptions without user research** — "users would prefer...", "most people want...", auth/onboarding chosen without user input, workflow assumptions
- **Deferred authority** — "my senior said...", "my lead told me...", "we've always done it this way", "the competitor does X"
- **Competing approaches** — user mentioned alternatives, dismissed an option quickly, or contradicted themselves across steps

**If NO signals detected** — run the Quick Assumptions Audit (inline, ~2 min):

```
Before we move to the solution, here are the key assumptions we're making:

1. [Assumption from Core Desire]
2. [Assumption from Reasoning Chain]
3. [Assumption from User Perspective]
4. [Technical assumption]

For each: are you confident, or is this worth questioning?
```

If user confirms all → proceed to Step 7.
If ANY flagged as uncertain → treat as a detected signal.

**If signals detected** → **Read [stress-test.md](stress-test.md) now** for the full dialectic execution (spawns two opposing subagents, synthesizes recommendation, ~8-12 min). Do NOT read stress-test.md unless signals are detected.

The stress test output (decisions, rationale, reversal signals) feeds into the epic spec at Step 7 under "Stress-Tested Assumptions".

---

# EXPLORE MODE (if --explore)

If `--explore` flag is set, diverge on approaches before converging to solution.

**Read [explore.md](explore.md) for architecture overview.**
**Read [approaches.md](approaches.md) for approach pattern reference.**
**Read [explore-steps.md](explore-steps.md) for detailed execution (Steps 6.5-6.11).**

Summary: Generate N fundamentally different approaches (varying on axes like interaction pattern, architecture, or where logic lives), scaffold each in a parallel git worktree, generate visual previews, present comparison matrix, and let the user pick a winner, request a hybrid, or refine.

---

# PHASE 2: SOLUTION SPACE

**Read [solution.md](solution.md) for detailed Steps 7-12.**

| Step | Focus |
|------|-------|
| 7. Create Epic | Persist problem statement as epic |
| 7.5. Stakeholder Check | Identify who's affected |
| 8. Research | Run scouts in parallel (repo, practice, docs, epic, docs-gap) |
| 9. Gap Analysis | Run gap analyst, fold into plan |
| 9.5. Epic Dependencies | Set cross-epic dependencies |
| 10. Task Creation | Size and create tasks (target M, split L) |
| 10.5. Browser QA | Auto-create QA checklist for frontend epics |
| 11. Update Epic Spec | Write full scope + acceptance |
| 12. Validate | Run `$FLUXCTL validate` |

---

# LINEAR TASK CREATION (if Linear mode)

If `LINEAR_MODE` is true, sync tasks back to Linear after local epic/tasks are created.

**Read [linear.md](linear.md) for Steps 13-16** (create issues, set dependencies, store mapping, report sync).

---

# COMPLETION

**Read [completion.md](completion.md) for summary, Ralph mode offer, update check, and philosophy.**

After showing the completion summary:
1. **Ralph mode offer** — always offer to run the epic autonomously overnight
2. **Update check** — check for Flux plugin updates (silent if none)

## Gotchas

- Scope must stay aligned with `.flux/` state. Do not silently start a fresh objective if active scoped work already exists.
- Route correctly before continuing: stakeholder asks go to `flux-propose`, bug investigations go to `flux-rca`, and memory requests go to `flux-brain`.
- Scoping is not implementation. Do not leak into code changes, todo files, or side-task execution while defining the objective.
