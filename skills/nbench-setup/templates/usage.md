# Flux Usage Guide

Task tracking for AI agents. All state lives in `.flux/`.

## CLI

```bash
.flux/bin/nbenchctl --help              # All commands
.flux/bin/nbenchctl <cmd> --help        # Command help
```

## File Structure

```
.flux/
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
.flux/bin/nbenchctl list                          # All epics + tasks grouped
.flux/bin/nbenchctl epics                         # All epics with progress
.flux/bin/nbenchctl tasks                         # All tasks
.flux/bin/nbenchctl tasks --epic fn-1-add-oauth   # Tasks for epic
.flux/bin/nbenchctl tasks --status todo           # Filter by status

# View
.flux/bin/nbenchctl show fn-1-add-oauth           # Epic with all tasks
.flux/bin/nbenchctl show fn-1-add-oauth.2         # Single task
.flux/bin/nbenchctl cat fn-1-add-oauth            # Epic spec (markdown)
.flux/bin/nbenchctl cat fn-1-add-oauth.2          # Task spec (markdown)

# Status
.flux/bin/nbenchctl ready --epic fn-1-add-oauth   # What's ready to work on
.flux/bin/nbenchctl validate --all                # Check structure
.flux/bin/nbenchctl state-path                    # Show state directory (for worktrees)

# Create
.flux/bin/nbenchctl epic create --title "..."
.flux/bin/nbenchctl task create --epic fn-1-add-oauth --title "..."
.flux/bin/nbenchctl task create --epic fn-1-add-oauth --title "..." --deps fn-1-add-oauth.1,fn-1-add-oauth.2

# Dependencies
.flux/bin/nbenchctl task set-deps fn-1-add-oauth.3 --deps fn-1-add-oauth.1,fn-1-add-oauth.2
.flux/bin/nbenchctl dep add fn-1-add-oauth.3 fn-1-add-oauth.1

# Work
.flux/bin/nbenchctl start fn-1-add-oauth.2        # Claim task
.flux/bin/nbenchctl done fn-1-add-oauth.2 --summary-file s.md --evidence-json e.json
```

## Workflow

1. `.flux/bin/nbenchctl epics` - list all epics
2. `.flux/bin/nbenchctl ready --epic fn-N-slug` - find available tasks
3. `.flux/bin/nbenchctl start fn-N-slug.M` - claim task
4. Implement the task
5. `.flux/bin/nbenchctl done fn-N-slug.M --summary-file ... --evidence-json ...` - complete

## Evidence JSON Format

```json
{"commits": ["abc123"], "tests": ["npm test"], "prs": []}
```

## Parallel Worktrees

Runtime state (status, assignee, etc.) is stored in `.git/flow-state/`, shared across worktrees:

```bash
.flux/bin/nbenchctl state-path              # Show state directory
.flux/bin/nbenchctl migrate-state           # Migrate existing repo
.flux/bin/nbenchctl migrate-state --clean   # Migrate + remove runtime from tracked files
```

Migration is optional — existing repos work without changes.

## More Info

- Human docs: https://github.com/Nairon-AI/n-bench/blob/main/plugins/flux/docs/nbenchctl.md
- CLI reference: `.flux/bin/nbenchctl --help`
