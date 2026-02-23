# N-bench Commands Reference

Complete reference for all available `/nbench:*` commands.

---

## Installation

<!-- TODO: Add video showing marketplace install + manual install -->
<details>
<summary>📹 Video: Installation walkthrough</summary>
<p><em>Coming soon</em></p>
</details>

```bash
# Marketplace
/plugin marketplace add Nairon-AI/n-bench
/plugin install flux@nairon-flux

# Manual
git clone https://github.com/Nairon-AI/n-bench.git ~/.claude/plugins/n-bench
```

---

## Core Workflow

| Command | Usage | Purpose |
|---------|-------|---------|
| `/nbench:setup` | `/nbench:setup` | Optional local setup (installs local `nbenchctl` + project docs) |
| `/nbench:interview` | `/nbench:interview <epic|task|file|idea>` | Deep requirements interview and refinement |
| `/nbench:plan` | `/nbench:plan <idea or fn-N>` | Convert request into structured epic + tasks |
| `/nbench:work` | `/nbench:work <fn-N or fn-N.M>` | Execute plan with checks and drift controls |

### /nbench:setup

<!-- TODO: Add video showing setup flow -->
<details>
<summary>📹 Video: Setup walkthrough</summary>
<p><em>Coming soon</em></p>
</details>

Initializes N-bench in your project. Creates `.nbench/` directory structure and bootstraps claudeception skill.

### /nbench:interview

<!-- TODO: Add video showing interview flow -->
<details>
<summary>📹 Video: Interview in action</summary>
<p><em>Coming soon</em></p>
</details>

Gathers requirements through structured questions. Use `--deep` for high-risk features.

### /nbench:plan

<!-- TODO: Add video showing plan creation -->
<details>
<summary>📹 Video: Planning a feature</summary>
<p><em>Coming soon</em></p>
</details>

Breaks down an idea into atomic tasks with dependencies and acceptance criteria.

### /nbench:work

<!-- TODO: Add video showing work execution -->
<details>
<summary>📹 Video: Executing tasks</summary>
<p><em>Coming soon</em></p>
</details>

Executes a task with automatic context reload and drift checks.

---

## Improve and Discovery

<!-- TODO: Add video showing /nbench:improve full flow -->
<details>
<summary>📹 Video: Tool discovery and recommendations</summary>
<p><em>Coming soon</em></p>
</details>

| Command | Usage | Purpose |
|---------|-------|---------|
| `/nbench:improve` | `/nbench:improve` | Analyze environment + sessions and recommend improvements |
| `/nbench:improve --detect` | `/nbench:improve --detect` | Show detected setup only |
| `/nbench:improve --score` | `/nbench:improve --score` | Show workflow score only |
| `/nbench:improve --list` | `/nbench:improve --list` | List available recommendations |
| `/nbench:improve --skip-sessions` | `/nbench:improve --skip-sessions` | Skip session analysis (repo/setup only) |
| `/nbench:improve --discover` | `/nbench:improve --discover` | Optional live community discovery (Exa/Twitter) |
| `/nbench:improve --explain` | `/nbench:improve --explain` | Include detailed explainability output |
| `/nbench:improve --category` | `/nbench:improve --category=<mcp\|cli\|plugin\|skill\|pattern>` | Filter recommendation category |
| `/nbench:improve --dismiss` | `/nbench:improve --dismiss <name>` | Dismiss recommendation |
| `/nbench:improve --alternative` | `/nbench:improve --alternative <rec> <alt>` | Store alternative tool |
| `/nbench:improve --preferences` | `/nbench:improve --preferences` | Show preference state |
| `/nbench:improve --clear-preferences` | `/nbench:improve --clear-preferences` | Reset recommendation preferences |
| `/nbench:improve --sessions always` | `/nbench:improve --sessions always` | Always allow session analysis |
| `/nbench:improve --sessions ask` | `/nbench:improve --sessions ask` | Ask each run for session analysis |

---

## N-bench Score

<!-- TODO: Add video showing /nbench:score output -->
<details>
<summary>📹 Video: AI-native capability scoring</summary>
<p><em>Coming soon</em></p>
</details>

| Command | Usage | Purpose |
|---------|-------|---------|
| `/nbench:score` | `/nbench:score` | Compute AI-native capability score |
| `/nbench:score --since` | `/nbench:score --since 2026-02-01` | Score from specific date |
| `/nbench:score --format` | `/nbench:score --format json` | Output as JSON/YAML |
| `/nbench:score --export` | `/nbench:score --export evidence.yaml` | Export for recruiting

---

## Profiles

<!-- TODO: Add video showing profile export/import -->
<details>
<summary>📹 Video: Sharing your SDLC setup</summary>
<p><em>Coming soon</em></p>
</details>

| Command | Usage | Purpose |
|---------|-------|---------|
| `/nbench:profile` | `/nbench:profile` | Export current SDLC setup and publish immutable share link |
| `/nbench:profile export` | `/nbench:profile export [--skills=global\|project\|both]` | Export snapshot with skill-scope selection and app curation memory |
| `/nbench:profile view` | `/nbench:profile view <url\|id>` | View a published profile snapshot |
| `/nbench:profile import` | `/nbench:profile import <url\|id>` | Import profile with compatible-only filtering and per-item consent |
| `/nbench:profile tombstone` | `/nbench:profile tombstone <url\|id>` | Tombstone a previously published immutable link |

---

## Reviews and Quality Gates

<!-- TODO: Add video showing review workflows -->
<details>
<summary>📹 Video: Code review with N-bench</summary>
<p><em>Coming soon</em></p>
</details>

| Command | Usage | Purpose |
|---------|-------|---------|
| `/nbench:plan-review` | `/nbench:plan-review <fn-N> [--review=rp\|codex\|export]` | Review plan quality before execution |
| `/nbench:impl-review` | `/nbench:impl-review [--review=rp\|codex\|export]` | Review implementation quality |
| `/nbench:epic-review` | `/nbench:epic-review <fn-N> [--review=rp\|codex\|none]` | Confirm epic completion aligns with spec |

---

## Utilities

<!-- TODO: Add video showing prime, sync, ralph -->
<details>
<summary>📹 Video: Utility commands</summary>
<p><em>Coming soon</em></p>
</details>

| Command | Usage | Purpose |
|---------|-------|---------|
| `/nbench:prime` | `/nbench:prime [--report-only\|--fix-all\|path]` | Run readiness audit and optional fixes |
| `/nbench:sync` | `/nbench:sync <id> [--dry-run]` | Sync downstream specs after implementation drift |
| `/nbench:ralph-init` | `/nbench:ralph-init` | Scaffold repo-local Ralph autonomous harness |
| `/nbench:uninstall` | `/nbench:uninstall` | Remove N-bench project-local files |

---

## Typical Paths

### New Feature (end-to-end)

<!-- TODO: Add video showing full feature development flow -->
<details>
<summary>📹 Video: Building a feature from scratch</summary>
<p><em>Coming soon</em></p>
</details>

```bash
/nbench:interview Add role-based permissions   # Gather requirements
/nbench:plan Add role-based permissions        # Create tasks
/nbench:work fn-1.1                            # Execute first task
/nbench:work fn-1.2                            # Continue...
/nbench:impl-review --review=codex             # Review implementation
/nbench:epic-review fn-1                       # Verify completion
```

### Workflow Optimization

<!-- TODO: Add video showing improve + discover flow -->
<details>
<summary>📹 Video: Finding better tools</summary>
<p><em>Coming soon</em></p>
</details>

```bash
/nbench:improve                    # Analyze and recommend
/nbench:improve --discover         # Include community discoveries
/nbench:improve --explain          # See matching rationale
```

### AI-Native Scoring

<!-- TODO: Add video showing score generation -->
<details>
<summary>📹 Video: Generating your N-bench score</summary>
<p><em>Coming soon</em></p>
</details>

```bash
/nbench:score                      # Full score report
/nbench:score --since 2026-02-01   # Last month only
/nbench:score --export resume.yaml # For recruiting
```

### Team Onboarding

<!-- TODO: Add video showing profile sharing -->
<details>
<summary>📹 Video: Sharing setup with teammates</summary>
<p><em>Coming soon</em></p>
</details>

```bash
/nbench:profile export             # Generate shareable link
/nbench:profile import <link>      # Import teammate's setup
```
