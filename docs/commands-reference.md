# Flux Commands Reference

Complete reference for all available `/flux:*` commands.

## Core Workflow

| Command | Usage | Purpose |
|---------|-------|---------|
| `/nbench:setup` | `/nbench:setup` | Optional local setup (installs local `fluxctl` + project docs) |
| `/nbench:interview` | `/nbench:interview <epic|task|file|idea>` | Deep requirements interview and refinement |
| `/nbench:plan` | `/nbench:plan <idea or fn-N>` | Convert request into structured epic + tasks |
| `/nbench:work` | `/nbench:work <fn-N or fn-N.M>` | Execute plan with checks and drift controls |

## Improve and Discovery

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

## Profiles

| Command | Usage | Purpose |
|---------|-------|---------|
| `/nbench:profile` | `/nbench:profile` | Export current SDLC setup and publish immutable share link |
| `/nbench:profile export` | `/nbench:profile export [--skills=global\|project\|both]` | Export snapshot with skill-scope selection and app curation memory |
| `/nbench:profile view` | `/nbench:profile view <url\|id>` | View a published profile snapshot |
| `/nbench:profile import` | `/nbench:profile import <url\|id>` | Import profile with compatible-only filtering and per-item consent |
| `/nbench:profile tombstone` | `/nbench:profile tombstone <url\|id>` | Tombstone a previously published immutable link |

## Reviews and Quality Gates

| Command | Usage | Purpose |
|---------|-------|---------|
| `/nbench:plan-review` | `/nbench:plan-review <fn-N> [--review=rp\|codex\|export]` | Review plan quality before execution |
| `/nbench:impl-review` | `/nbench:impl-review [--review=rp\|codex\|export]` | Review implementation quality |
| `/nbench:epic-review` | `/nbench:epic-review <fn-N> [--review=rp\|codex\|none]` | Confirm epic completion aligns with spec |

## Utilities

| Command | Usage | Purpose |
|---------|-------|---------|
| `/nbench:prime` | `/nbench:prime [--report-only\|--fix-all\|path]` | Run readiness audit and optional fixes |
| `/nbench:sync` | `/nbench:sync <id> [--dry-run]` | Sync downstream specs after implementation drift |
| `/nbench:ralph-init` | `/nbench:ralph-init` | Scaffold repo-local Ralph autonomous harness |
| `/nbench:uninstall` | `/nbench:uninstall` | Remove Flux project-local files |

## Typical Paths

New feature:

```bash
/nbench:interview Add role-based permissions
/nbench:plan Add role-based permissions
/nbench:work fn-1.1
/nbench:impl-review --review=codex
```

Workflow optimization:

```bash
/nbench:improve
/nbench:improve --discover
```
