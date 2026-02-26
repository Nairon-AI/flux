# Flux Commands Reference

Complete reference for all available `/flux:*` commands.

---

## Installation

<!-- TODO: Add video showing marketplace install + manual install -->
<details>
<summary>📹 Video: Installation walkthrough</summary>
<p><em>Coming soon</em></p>
</details>

```bash
# Marketplace
/plugin marketplace add Nairon-AI/flux
/plugin install flux@nairon-flux

# Manual
git clone https://github.com/Nairon-AI/flux.git ~/.claude/plugins/flux
```

---

## Core Workflow

| Command | Usage | Purpose |
|---------|-------|---------|
| `/flux:setup` | `/flux:setup` | Optional local setup (installs local `fluxctl` + project docs) |
| `/flux:interview` | `/flux:interview <epic|task|file|idea>` | Deep requirements interview and refinement |
| `/flux:plan` | `/flux:plan <idea or fn-N>` | Convert request into structured epic + tasks |
| `/flux:work` | `/flux:work <fn-N or fn-N.M>` | Execute plan with checks and drift controls |

### /flux:setup

<!-- TODO: Add video showing setup flow -->
<details>
<summary>📹 Video: Setup walkthrough</summary>
<p><em>Coming soon</em></p>
</details>

Initializes Flux in your project. Creates `.flux/` directory structure and bootstraps claudeception skill.

### /flux:interview

<!-- TODO: Add video showing interview flow -->
<details>
<summary>📹 Video: Interview in action</summary>
<p><em>Coming soon</em></p>
</details>

Gathers requirements through structured questions. Use `--deep` for high-risk features.

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
| `/flux:sync` | `/flux:sync <id> [--dry-run]` | Sync downstream specs after implementation drift |
| `/flux:ralph-init` | `/flux:ralph-init` | Scaffold repo-local Ralph autonomous harness |
| `/flux:uninstall` | `/flux:uninstall` | Remove Flux project-local files |

---

## Typical Paths

### New Feature (end-to-end)

<!-- TODO: Add video showing full feature development flow -->
<details>
<summary>📹 Video: Building a feature from scratch</summary>
<p><em>Coming soon</em></p>
</details>

```bash
/flux:interview Add role-based permissions   # Gather requirements
/flux:plan Add role-based permissions        # Create tasks
/flux:work fn-1.1                            # Execute first task
/flux:work fn-1.2                            # Continue...
/flux:impl-review --review=codex             # Review implementation
/flux:epic-review fn-1                       # Verify completion
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
