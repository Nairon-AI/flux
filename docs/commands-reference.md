# Flux Commands Reference

Complete reference for all available `/flux:*` commands.

Flux is designed to route from intent. In normal use, you should be able to tell the agent what you want to build, fix, refactor, or continue, and let Flux choose the right command. Treat this page as a reference, not the primary way to drive the workflow.

Important: examples in this document use `/flux:*` commands because they are precise and compact, but that is documentation shorthand. The default user experience is natural language first. In day-to-day use, a developer should be able to say things like "add role-based permissions", "fix the auth redirect bug", or "continue the notifications work", and Flux should route that request without requiring an explicit slash command.

Important for Codex users: Codex may not expose a Claude-style slash-command picker for custom Flux commands. Flux still treats literal `/flux:*` strings as explicit skill triggers in Codex. If Flux is installed and you restart Codex, prompts like `/flux:scope`, `/flux:prime`, and `/flux:work fn-1` should route even if there is no visible autocomplete dropdown.

For the formal workflow state machine (all states, transitions, and routing rules), see [state-machine.md](state-machine.md).

---

## Installation

<!-- TODO: Add video showing marketplace install + manual install -->
<details>
<summary>📹 Video: Installation walkthrough</summary>
<p><em>Coming soon</em></p>
</details>

```bash
# Codex CLI (recommended primary driver)
npm install -g @openai/codex
codex login
```

Flux setup can also install [PlaTo](https://github.com/Alt5r/Plato) so supported project skills go through `secureskills` and land in `.secureskills/` instead of loose repo-local skill folders.

Some optional project-installed skills do not have a `/flux:*` wrapper. Flux can still route to them implicitly when they are present in the repo.

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
| `/flux:dejank` | `/flux:dejank [component|path|symptom]` | Trigger the optional Dejank skill for React visual-jank audits and debugging |
| `/flux:grill` | `/flux:grill [epic-id|feature]` | Behavioral stress test of implemented behavior |
| `/flux:tdd` | `/flux:tdd <task-id|feature|bugfix>` | Run the TDD workflow explicitly |
| `/flux:design-interface` | `/flux:design-interface <module|API>` | Compare multiple interface designs |
| `/flux:ubiquitous-language` | `/flux:ubiquitous-language [domain area]` | Extract and formalize domain terminology |
| `/flux:export-context` | `/flux:export-context <plan <epic-id>|impl> [focus]` | Export a review pack for external LLMs |
| `/flux:autofix` | `/flux:autofix [pr-url|pr-number]` | Start Claude cloud auto-fix on a PR |
| `/flux:remember` | `/flux:remember <memory>` | Explicit memory-routing entrypoint for durable repo facts and rules |
| `/flux:gate` | `/flux:gate [staging-url|pr-number]` | Validate staging after merge and prepare production promotion |

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
5. **Learn** — write pitfall to brain vault, and when manual review confirms a repeatable anti-pattern, propose structural prevention (lint rules such as `lintcn`, type constraints, scripts)

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

Initializes Flux in your project. Creates `.flux/`, the canonical brain vault at `.flux/brain/`, and the centralized architecture note at `.flux/brain/codebase/architecture.md`, then configures preferences and optionally installs productivity tools (MCP servers, CLI tools, desktop apps). Supported skill installs now go through PlaTo so Flux can use a signed, verified `.secureskills/` store; in git repos Flux links that path to shared storage under the git common-dir so worktrees reuse the same secure-skill keys and enabled-agent state. In React-based repos, setup can also offer React Doctor as an optional CLI and wire it into a pre-commit hook, with the quality pass re-running it as a backstop before submit.

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

Executes a task with automatic context reload and drift checks. During the quality pass, React-based repos can also run a diff-scoped React Doctor scan when the tool is available, even if the pre-commit hook already ran.

The underlying `fluxctl` helper also exposes:

```bash
.flux/bin/fluxctl env --json
.flux/bin/fluxctl doctor --json
.flux/bin/fluxctl version
.flux/bin/fluxctl architecture status
.flux/bin/fluxctl architecture path
.flux/bin/fluxctl architecture write --file architecture.md --summary "Updated auth/data flow" --source flux:work
```

Use `env` or `doctor` when install/update behavior seems wrong for the current host. They report the detected primary driver, the authoritative repo-local runtime version, any Claude adapter version, and the exact host-specific update guidance.

### /flux:dejank

Explicit entrypoint for the optional `dejank` skill after it has been installed through `/flux:setup` in a React-based repo.

Use it when you want a dedicated visual-jank pass instead of hoping the model picks the skill implicitly:

```bash
/flux:dejank src/components/Sidebar.tsx
/flux:dejank the settings panel flashes blank on first render
```

When Flux is installed in the repo, casual React jank complaints like "this flickers", "the layout jumps", or "the pane feels rebuilt" should also route here automatically when `dejank` is installed.

If `dejank` is not installed in the repo yet, the command should stop and tell you to install it through `/flux:setup` or with `secureskills add`.

### /diffity-tour

Optional explicit entrypoint for the project-installed `diffity-tour` skill after it has been installed through `/flux:setup`.

Use it when you want an interactive walkthrough of an existing feature, subsystem, or codepath:

```bash
/diffity-tour how does authentication work?
/diffity-tour walk me through everything that touches checkout
```

When Flux is installed in the repo, understanding requests like "how does auth work", "help me understand the billing flow", or "show me what touches notifications" should also route here automatically when `diffity-tour` is installed.

If `diffity-tour` is not installed in the repo yet, Flux should continue with the normal routing path and point you to `/flux:setup` or:

```bash
secureskills add https://github.com/kamranahmedse/diffity --skill diffity-tour
secureskills enable codex
```

---

### Specialist Workflows

Flux also exposes these explicit specialist workflows when you want to jump directly to them instead of relying on implicit routing:

- `/flux:grill` — behavioral verification after implementation
- `/flux:tdd` — red-green-refactor execution
- `/flux:design-interface` — parallel interface design exploration
- `/flux:ubiquitous-language` — DDD glossary extraction
- `/flux:export-context` — external review-pack export
- `/flux:autofix` — post-submit cloud PR babysitting
- `/flux:remember` — explicit durable-memory routing
- `/flux:gate` — staging validation and promotion workflow
- `/flux:release` — Flux maintainer release publishing
- `/flux:improve-claude-md` — instruction-file adherence hardening

These are also part of the natural-language router when the request clearly matches them.

---

### Workflow-Embedded Utility Skills

Flux also uses internal utility skills that are **not** slash commands and therefore do not appear in `commands/flux/`. They are part of the workflow contract and are invoked from within existing phases:

- `flux-parallel-dispatch` — Prime scouts and Scope explore fan-out
- `flux-receive-review` — Impl Review, Epic Review, and Autofix comment handling
- `flux-verify-claims` — Work/Review/Autofix completion and SHIP claims

These utility skills stay inside the owning phase instead of becoming router targets.

---

## Knowledge & Memory

| Command | Usage | Purpose |
|---------|-------|---------|
| `/flux:reflect` | `/flux:reflect` | Capture learnings from the current session into brain vault |
| `/flux:ruminate` | `/flux:ruminate` | Mine past conversations for uncaptured patterns |
| `/flux:meditate` | `/flux:meditate` | Audit brain vault — prune stale content, promote patterns |
| `/flux:remember` | `/flux:remember <memory>` | Explicit alias for remember/don't-forget requests |
| "remember X" | `remember always use pnpm` | Smart routing — stores in `AGENTS.md` (actionable rules) or `.flux/brain/` (deeper context) |

### Natural Language Memory

You don't need a slash command. Just say:
- **"remember always use pnpm"** → adds to `AGENTS.md` (short rule, every session)
- **"remember Sarah is the PM"** → adds to `.flux/brain/business/` (team context)
- **"don't forget the API rate limit is 100/min"** → adds to `.flux/brain/codebase/` (technical context)
- **"from now on, run tests before committing"** → adds to `AGENTS.md` (constraint)

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

React-based repos can add an extra static gate here: when `react-doctor` is installed or runnable via `npx`, Flux runs `react-doctor . --diff HEAD --fail-on error` before submit.

---

## Security

| Command | Usage | Purpose |
|---------|-------|---------|
| `/flux:security-scan` | `/flux:security-scan [PR #N \| commit X..Y \| staged \| last N]` | Scan code changes for security vulnerabilities using STRIDE threat modeling |
| `/flux:security-review` | `/flux:security-review [--mode pr\|full\|staged] [--severity high]` | Comprehensive security review with STRIDE analysis and vulnerability validation |
| `/flux:threat-model` | `/flux:threat-model [--compliance SOC2,GDPR] [--update]` | Generate a STRIDE-based security threat model for the repository |
| `/flux:vuln-validate` | `/flux:vuln-validate [finding IDs] [--severity high]` | Validate security findings for exploitability and generate proof-of-concept |

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
| `/flux:gate` | `/flux:gate [staging-url\|pr-number]` | Validate staging and create the promotion path to production |
| `/flux:contribute` | `/flux:contribute <issue description>` | Report a Flux bug and create a PR to fix it |
| `/flux:skill-builder` | `/flux:skill-builder <what the skill should do>` | Autonomously create production-grade agent skills from a brief description |
| `/flux:upgrade` | `/flux:upgrade` | Upgrade Flux plugin and optionally update project setup |
| `/flux:release` | `/flux:release vX.Y.Z [--title "..."]` | Cut a Flux release with synced manifests, changelog, tag, and notes |
| `/flux:improve-claude-md` | `/flux:improve-claude-md [path-to-AGENTS-or-CLAUDE]` | Restructure instruction files for stronger conditional adherence |
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
