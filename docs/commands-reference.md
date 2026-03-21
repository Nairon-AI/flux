# Flux Commands Reference

Complete reference for all available `/flux:*` commands.

Flux is designed to route from intent. In normal use, you should be able to tell the agent what you want to build, fix, refactor, or continue, and let Flux choose the right command. Treat this page as a reference, not the primary way to drive the workflow.

For the formal workflow state machine (all states, transitions, and routing rules), see [state-machine.md](state-machine.md).

---

## Installation

<!-- TODO: Add video showing marketplace install + manual install -->
<details>
<summary>📹 Video: Installation walkthrough</summary>
<p><em>Coming soon</em></p>
</details>

```bash
# Claude Code (recommended)
/plugin add https://github.com/Nairon-AI/flux@latest
```

Important: `/plugin add` is a Claude Code slash command. Run it in Claude Code chat input, not in your terminal.

---

## Core Workflow

| Command | Usage | Purpose |
|---------|-------|---------|
| `/flux:setup` | `/flux:setup` | Optional local setup (installs local `fluxctl` + project docs) |
| `/flux:propose` | `/flux:propose` | Stakeholder feature proposal — conversational planning with engineering pushback and PR handoff |
| `/flux:rca` | `/flux:rca [error/bug description]` | Root cause analysis — backward trace, adversarial verify, fix with regression test, embed learnings |
| `/flux:scope` | `/flux:scope <idea> [--deep] [--explore N]` | **Full guided scoping workflow** (recommended) |
| `/flux:plan` | `/flux:plan <idea or fn-N>` | Convert request into structured epic + tasks only |
| `/flux:work` | `/flux:work <fn-N or fn-N.M>` | Execute plan with checks and drift controls |

### /flux:propose

<!-- TODO: Add video showing propose flow -->
<details>
<summary>Video: Stakeholder feature proposal</summary>
<p><em>Coming soon</em></p>
</details>

**For non-technical team members.** Guides stakeholders through a conversational feature proposal:

1. **Understand** — what's the problem, who's affected, why now
2. **Push back** — engineering complexity, third-party costs, timeline reality
3. **Simplify** — probe for an MVP that delivers 80% of the value
4. **Document** — write a proposal doc and create a PR for engineering handoff

Engineers scope the proposal by running `/flux:scope docs/proposals/YYYY-MM-DD-feature-name.md`.

Also detected **implicitly** — if someone uses `/flux:scope` with non-technical language, Flux asks whether they're an engineer or a stakeholder and routes accordingly.

### /flux:rca

<!-- TODO: Add video showing RCA flow -->
<details>
<summary>Video: Root cause analysis</summary>
<p><em>Coming soon</em></p>
</details>

**For bugs, not features.** A dedicated debugging workflow that traces backward from symptom to root cause:

1. **Reproduce** — confirm the bug, classify severity (Quick / Standard / Critical)
2. **Investigate** — choose Flux's backward trace or RepoPrompt Investigate (if installed)
3. **Verify** — adversarial review of root cause analysis (Standard + Critical)
4. **Fix** — write fix at the source, not the symptom, with mandatory regression test
5. **Learn** — write pitfall to brain vault, propose structural prevention (lint rules, type constraints)

Also detected **implicitly** — if someone uses `/flux:scope` with bug signals (error messages, "broken", "not working"), Flux asks if they want RCA instead of standard scoping.

### /flux:scope

<!-- TODO: Add video showing scope flow -->
<details>
<summary>Video: Scoping a feature</summary>
<p><em>Coming soon</em></p>
</details>

**Recommended starting point.** Runs Flux's Product OS-style scoping workflow:

1. **Start**
   - classify feature, bug, or refactor
   - choose shallow vs deep
   - capture technical level and implementation target
2. **Discover / Define**
   - clarify the actual problem before solutioning
3. **Develop / Deliver / Handoff**
   - shape the solution
   - create epic + tasks
   - route into `/flux:work` or engineer handoff

**Usage:**
```bash
/flux:scope Add user notifications           # Shallow mode (~10 min)
/flux:scope Add user notifications --deep    # Deep mode (~45 min)
```

Use `--deep` for high-stakes or ambiguous features.

### /flux:setup

<!-- TODO: Add video showing setup flow -->
<details>
<summary>📹 Video: Setup walkthrough</summary>
<p><em>Coming soon</em></p>
</details>

Initializes Flux in your project. Creates `.flux/` and the canonical brain vault at `.flux/brain/`, configures preferences, and optionally installs productivity tools (MCP servers, CLI tools, desktop apps).

### /flux:plan

<!-- TODO: Add video showing plan creation -->
<details>
<summary>📹 Video: Planning a feature</summary>
<p><em>Coming soon</em></p>
</details>

Breaks down an idea into atomic tasks with dependencies and acceptance criteria.

### /flux:work

<!-- TODO: Add video showing work execution -->
<details>
<summary>📹 Video: Executing tasks</summary>
<p><em>Coming soon</em></p>
</details>

Executes a task with automatic context reload and drift checks.

---

## Knowledge & Memory

| Command | Usage | Purpose |
|---------|-------|---------|
| `/flux:reflect` | `/flux:reflect` | Capture learnings from the current session into brain vault |
| `/flux:ruminate` | `/flux:ruminate` | Mine past conversations for uncaptured patterns |
| `/flux:meditate` | `/flux:meditate` | Audit brain vault — prune stale content, promote patterns |
| "remember X" | `remember always use pnpm` | Smart routing — stores in CLAUDE.md (actionable rules) or `.flux/brain/` (deeper context) |

### Natural Language Memory

You don't need a slash command. Just say:
- **"remember always use pnpm"** → adds to CLAUDE.md (short rule, every session)
- **"remember Sarah is the PM"** → adds to `.flux/brain/business/` (team context)
- **"don't forget the API rate limit is 100/min"** → adds to `.flux/brain/codebase/` (technical context)
- **"from now on, run tests before committing"** → adds to CLAUDE.md (constraint)

Flux classifies the content and asks you to confirm the destination before writing.

---

## Improve and Discovery

<!-- TODO: Add video showing /flux:improve full flow -->
<details>
<summary>📹 Video: Tool discovery and recommendations</summary>
<p><em>Coming soon</em></p>
</details>

| Command | Usage | Purpose |
|---------|-------|---------|
| `/flux:improve` | `/flux:improve` | Analyze environment + sessions and recommend improvements |
| `/flux:improve --detect` | `/flux:improve --detect` | Show detected setup only |
| `/flux:improve --score` | `/flux:improve --score` | Show workflow score only |
| `/flux:improve --list` | `/flux:improve --list` | List available recommendations |
| `/flux:improve --skip-sessions` | `/flux:improve --skip-sessions` | Skip session analysis (repo/setup only) |
| `/flux:improve --discover` | `/flux:improve --discover` | Optional live community discovery (Exa/Twitter) |
| `/flux:improve --explain` | `/flux:improve --explain` | Include detailed explainability output |
| `/flux:improve --category` | `/flux:improve --category=<mcp\|cli\|plugin\|skill\|pattern>` | Filter recommendation category |
| `/flux:improve --dismiss` | `/flux:improve --dismiss <name>` | Dismiss recommendation |
| `/flux:improve --alternative` | `/flux:improve --alternative <rec> <alt>` | Store alternative tool |
| `/flux:improve --preferences` | `/flux:improve --preferences` | Show preference state |
| `/flux:improve --clear-preferences` | `/flux:improve --clear-preferences` | Reset recommendation preferences |
| `/flux:improve --sessions always` | `/flux:improve --sessions always` | Always allow session analysis |
| `/flux:improve --sessions ask` | `/flux:improve --sessions ask` | Ask each run for session analysis |

---

## Flux Score

<!-- TODO: Add video showing /flux:score output -->
<details>
<summary>📹 Video: AI-native capability scoring</summary>
<p><em>Coming soon</em></p>
</details>

| Command | Usage | Purpose |
|---------|-------|---------|
| `/flux:score` | `/flux:score` | Compute AI-native capability score |
| `/flux:score --since` | `/flux:score --since 2026-02-01` | Score from specific date |
| `/flux:score --format` | `/flux:score --format json` | Output as JSON/YAML |
| `/flux:score --export` | `/flux:score --export evidence.yaml` | Export for recruiting

---

## Universe Auth

| Command | Usage | Purpose |
|---------|-------|---------|
| `/flux:login` | `/flux:login` | Connect Flux to Universe via device flow |
| `/flux:logout` | `/flux:logout` | Remove local Universe token on this machine |
| `/flux:status` | `/flux:status [--format json]` | Show connected/disconnected auth state |

`/flux:login` also runs an immediate score pass after successful auth so Universe receives the first stats snapshot without waiting for a separate `/flux:score`.

---

## Profiles

<!-- TODO: Add video showing profile export/import -->
<details>
<summary>📹 Video: Sharing your SDLC setup</summary>
<p><em>Coming soon</em></p>
</details>

| Command | Usage | Purpose |
|---------|-------|---------|
| `/flux:profile` | `/flux:profile` | Export current SDLC setup and publish immutable share link |
| `/flux:profile export` | `/flux:profile export [--skills=global\|project\|both]` | Export snapshot with skill-scope selection and app curation memory |
| `/flux:profile view` | `/flux:profile view <url\|id>` | View a published profile snapshot |
| `/flux:profile import` | `/flux:profile import <url\|id>` | Import profile with compatible-only filtering and per-item consent |
| `/flux:profile tombstone` | `/flux:profile tombstone <url\|id>` | Tombstone a previously published immutable link |

---

## Reviews and Quality Gates

<!-- TODO: Add video showing review workflows -->
<details>
<summary>📹 Video: Code review with Flux</summary>
<p><em>Coming soon</em></p>
</details>

| Command | Usage | Purpose |
|---------|-------|---------|
| `/flux:plan-review` | `/flux:plan-review <fn-N> [--review=rp\|codex\|export]` | Review plan quality before execution |
| `/flux:impl-review` | `/flux:impl-review [--review=rp\|codex\|export]` | Review implementation quality |
| `/flux:epic-review` | `/flux:epic-review <fn-N> [--review=rp\|codex\|none]` | Confirm epic completion aligns with spec |

---

## Utilities

<!-- TODO: Add video showing prime, sync, ralph -->
<details>
<summary>📹 Video: Utility commands</summary>
<p><em>Coming soon</em></p>
</details>

| Command | Usage | Purpose |
|---------|-------|---------|
| `/flux:prime` | `/flux:prime [--report-only\|--fix-all\|path]` | Run readiness audit and optional fixes |
| `/flux:desloppify` | `/flux:desloppify [scan\|status\|next\|plan]` | Systematic codebase quality improvement |
| `/flux:sync` | `/flux:sync <id> [--dry-run]` | Sync downstream specs after implementation drift |
| `/flux:ralph-init` | `/flux:ralph-init` | Scaffold repo-local Ralph autonomous harness |
| `/flux:uninstall` | `/flux:uninstall` | Remove Flux project-local files |

---

## Workflow State Machine

At any point, you can check where you are in the Flux workflow:

```bash
# Check current state
fluxctl session-state --json

# See active epics and tasks
fluxctl epics --json
fluxctl tasks --epic fn-1 --json
```

For the full state diagram, transitions, and routing rules, see [state-machine.md](state-machine.md).

---

## Typical Paths

### New Feature (end-to-end)

<!-- TODO: Add video showing full feature development flow -->
<details>
<summary>Video: Building a feature from scratch</summary>
<p><em>Coming soon</em></p>
</details>

**Recommended (combined scope):**
```bash
/flux:scope Add role-based permissions       # Requirements + planning (~10 min)
/flux:work fn-1.1                            # Execute first task
/flux:work fn-1.2                            # Continue...
/flux:impl-review --review=codex             # Review implementation
/flux:epic-review fn-1                       # Verify completion
```

**Alternative (plan only, skip interview):**
```bash
/flux:plan fn-1                              # Create tasks (~5-15 min)
/flux:work fn-1.1                            # Execute first task
```

### Workflow Optimization

<!-- TODO: Add video showing improve + discover flow -->
<details>
<summary>📹 Video: Finding better tools</summary>
<p><em>Coming soon</em></p>
</details>

```bash
/flux:improve                    # Analyze and recommend
/flux:improve --discover         # Include community discoveries
/flux:improve --explain          # See matching rationale
```

### AI-Native Scoring

<!-- TODO: Add video showing score generation -->
<details>
<summary>📹 Video: Generating your Flux score</summary>
<p><em>Coming soon</em></p>
</details>

```bash
/flux:score                      # Full score report
/flux:score --since 2026-02-01   # Last month only
/flux:score --export resume.yaml # For recruiting
```

### Team Onboarding

<!-- TODO: Add video showing profile sharing -->
<details>
<summary>📹 Video: Sharing setup with teammates</summary>
<p><em>Coming soon</em></p>
</details>

```bash
/flux:profile export             # Generate shareable link
/flux:profile import <link>      # Import teammate's setup
```
