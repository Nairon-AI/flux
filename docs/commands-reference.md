# Flux Commands Reference

Complete reference for all available `/flux:*` commands.

## Core Workflow

| Command | Usage | Purpose |
|---------|-------|---------|
| `/flux:setup` | `/flux:setup` | Optional local setup (installs local `fluxctl` + project docs) |
| `/flux:interview` | `/flux:interview <epic|task|file|idea>` | Deep requirements interview and refinement |
| `/flux:plan` | `/flux:plan <idea or fn-N>` | Convert request into structured epic + tasks |
| `/flux:work` | `/flux:work <fn-N or fn-N.M>` | Execute plan with checks and drift controls |

## Improve and Discovery

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

## Profiles

| Command | Usage | Purpose |
|---------|-------|---------|
| `/flux:profile` | `/flux:profile` | Export current SDLC setup and publish immutable share link |
| `/flux:profile export` | `/flux:profile export [--skills=global\|project\|both]` | Export snapshot with skill-scope selection and app curation memory |
| `/flux:profile view` | `/flux:profile view <url\|id>` | View a published profile snapshot |
| `/flux:profile import` | `/flux:profile import <url\|id>` | Import profile with compatible-only filtering and per-item consent |
| `/flux:profile tombstone` | `/flux:profile tombstone <url\|id>` | Tombstone a previously published immutable link |

## Reviews and Quality Gates

| Command | Usage | Purpose |
|---------|-------|---------|
| `/flux:plan-review` | `/flux:plan-review <fn-N> [--review=rp\|codex\|export]` | Review plan quality before execution |
| `/flux:impl-review` | `/flux:impl-review [--review=rp\|codex\|export]` | Review implementation quality |
| `/flux:epic-review` | `/flux:epic-review <fn-N> [--review=rp\|codex\|none]` | Confirm epic completion aligns with spec |

## Utilities

| Command | Usage | Purpose |
|---------|-------|---------|
| `/flux:prime` | `/flux:prime [--report-only\|--fix-all\|path]` | Run readiness audit and optional fixes |
| `/flux:sync` | `/flux:sync <id> [--dry-run]` | Sync downstream specs after implementation drift |
| `/flux:ralph-init` | `/flux:ralph-init` | Scaffold repo-local Ralph autonomous harness |
| `/flux:uninstall` | `/flux:uninstall` | Remove Flux project-local files |

## Typical Paths

New feature:

```bash
/flux:interview Add role-based permissions
/flux:plan Add role-based permissions
/flux:work fn-1.1
/flux:impl-review --review=codex
```

Workflow optimization:

```bash
/flux:improve
/flux:improve --discover
```
