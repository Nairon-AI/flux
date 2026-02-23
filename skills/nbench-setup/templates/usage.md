# Flux Usage Guide

Task tracking for AI agents. All state lives in `.nbench/`.

## CLI

```bash
.nbench/bin/nbenchctl --help              # All commands
.nbench/bin/nbenchctl <cmd> --help        # Command help
```

## File Structure

```
.nbench/
├── bin/nbenchctl             # CLI (this install)
├── epics/fn-N-slug.json    # Epic metadata (e.g., fn-1-add-oauth.json)
├── specs/fn-N-slug.md      # Epic specifications
├── tasks/fn-N-slug.M.json  # Task metadata (e.g., fn-1-add-oauth.1.json)
├── tasks/fn-N-slug.M.md    # Task specifications
├── memory/                 # Context memory
└── meta.json               # Project metadata
```

## IDs

- Epics: `fn-N-slug` where slug is derived from title (e.g., fn-1-add-oauth, fn-2-fix-login-bug)
- Tasks: `fn-N-slug.M` (e.g., fn-1-add-oauth.1, fn-2-fix-login-bug.2)

**Backwards compatibility**: Legacy formats `fn-N`, `fn-N-xxx`, `fn-N.M`, and `fn-N-xxx.M` still work.

## Common Commands

```bash
# List
.nbench/bin/nbenchctl list                          # All epics + tasks grouped
.nbench/bin/nbenchctl epics                         # All epics with progress
.nbench/bin/nbenchctl tasks                         # All tasks
.nbench/bin/nbenchctl tasks --epic fn-1-add-oauth   # Tasks for epic
.nbench/bin/nbenchctl tasks --status todo           # Filter by status

# View
.nbench/bin/nbenchctl show fn-1-add-oauth           # Epic with all tasks
.nbench/bin/nbenchctl show fn-1-add-oauth.2         # Single task
.nbench/bin/nbenchctl cat fn-1-add-oauth            # Epic spec (markdown)
.nbench/bin/nbenchctl cat fn-1-add-oauth.2          # Task spec (markdown)

# Status
.nbench/bin/nbenchctl ready --epic fn-1-add-oauth   # What's ready to work on
.nbench/bin/nbenchctl validate --all                # Check structure
.nbench/bin/nbenchctl state-path                    # Show state directory (for worktrees)

# Create
.nbench/bin/nbenchctl epic create --title "..."
.nbench/bin/nbenchctl task create --epic fn-1-add-oauth --title "..."
.nbench/bin/nbenchctl task create --epic fn-1-add-oauth --title "..." --deps fn-1-add-oauth.1,fn-1-add-oauth.2

# Dependencies
.nbench/bin/nbenchctl task set-deps fn-1-add-oauth.3 --deps fn-1-add-oauth.1,fn-1-add-oauth.2
.nbench/bin/nbenchctl dep add fn-1-add-oauth.3 fn-1-add-oauth.1

# Work
.nbench/bin/nbenchctl start fn-1-add-oauth.2        # Claim task
.nbench/bin/nbenchctl done fn-1-add-oauth.2 --summary-file s.md --evidence-json e.json
```

## Workflow

1. `.nbench/bin/nbenchctl epics` - list all epics
2. `.nbench/bin/nbenchctl ready --epic fn-N-slug` - find available tasks
3. `.nbench/bin/nbenchctl start fn-N-slug.M` - claim task
4. Implement the task
5. `.nbench/bin/nbenchctl done fn-N-slug.M --summary-file ... --evidence-json ...` - complete

## Evidence JSON Format

```json
{"commits": ["abc123"], "tests": ["npm test"], "prs": []}
```

## Parallel Worktrees

Runtime state (status, assignee, etc.) is stored in `.git/flow-state/`, shared across worktrees:

```bash
.nbench/bin/nbenchctl state-path              # Show state directory
.nbench/bin/nbenchctl migrate-state           # Migrate existing repo
.nbench/bin/nbenchctl migrate-state --clean   # Migrate + remove runtime from tracked files
```

Migration is optional — existing repos work without changes.

## More Info

- Human docs: https://github.com/Nairon-AI/n-bench/blob/main/plugins/flux/docs/nbenchctl.md
- CLI reference: `.nbench/bin/nbenchctl --help`
