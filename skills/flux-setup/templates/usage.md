# Flux Usage Guide

Task tracking for AI agents. All state lives in `.flux/`.

## CLI

```bash
.flux/bin/fluxctl --help              # All commands
.flux/bin/fluxctl <cmd> --help        # Command help
```

## File Structure

```
.flux/
├── bin/fluxctl             # CLI (this install)
├── context/                # Optional cached context artifacts (e.g., agentmap.yaml)
├── epics/fn-N-slug.json    # Epic metadata (e.g., fn-1-add-oauth.json)
├── specs/fn-N-slug.md      # Epic specifications
├── tasks/fn-N-slug.M.json  # Task metadata (e.g., fn-1-add-oauth.1.json)
├── tasks/fn-N-slug.M.md    # Task specifications
└── meta.json               # Project metadata
```

## IDs

- Epics: `fn-N-slug` where slug is derived from title (e.g., fn-1-add-oauth, fn-2-fix-login-bug)
- Tasks: `fn-N-slug.M` (e.g., fn-1-add-oauth.1, fn-2-fix-login-bug.2)

**Backwards compatibility**: Legacy formats `fn-N`, `fn-N-xxx`, `fn-N.M`, and `fn-N-xxx.M` still work.

## Common Commands

```bash
# List
.flux/bin/fluxctl list                          # All epics + tasks grouped
.flux/bin/fluxctl epics                         # All epics with progress
.flux/bin/fluxctl tasks                         # All tasks
.flux/bin/fluxctl tasks --epic fn-1-add-oauth   # Tasks for epic
.flux/bin/fluxctl tasks --status todo           # Filter by status

# View
.flux/bin/fluxctl show fn-1-add-oauth           # Epic with all tasks
.flux/bin/fluxctl show fn-1-add-oauth.2         # Single task
.flux/bin/fluxctl cat fn-1-add-oauth            # Epic spec (markdown)
.flux/bin/fluxctl cat fn-1-add-oauth.2          # Task spec (markdown)

# Status
.flux/bin/fluxctl ready --epic fn-1-add-oauth   # What's ready to work on
.flux/bin/fluxctl validate --all                # Check structure
.flux/bin/fluxctl state-path                    # Show state directory (for worktrees)
.flux/bin/fluxctl agentmap --check             # Check built-in agentmap support
.flux/bin/fluxctl agentmap --write             # Write .flux/context/agentmap.yaml

# Create
.flux/bin/fluxctl epic create --title "..."
.flux/bin/fluxctl task create --epic fn-1-add-oauth --title "..."
.flux/bin/fluxctl task create --epic fn-1-add-oauth --title "..." --deps fn-1-add-oauth.1,fn-1-add-oauth.2

# Dependencies
.flux/bin/fluxctl task set-deps fn-1-add-oauth.3 --deps fn-1-add-oauth.1,fn-1-add-oauth.2
.flux/bin/fluxctl dep add fn-1-add-oauth.3 fn-1-add-oauth.1

# Work
.flux/bin/fluxctl start fn-1-add-oauth.2        # Claim task
.flux/bin/fluxctl done fn-1-add-oauth.2 --summary-file s.md --evidence-json e.json
```

## Workflow

1. `.flux/bin/fluxctl epics` - list all epics
2. `.flux/bin/fluxctl ready --epic fn-N-slug` - find available tasks
3. `.flux/bin/fluxctl start fn-N-slug.M` - claim task
4. Implement the task
5. `.flux/bin/fluxctl done fn-N-slug.M --summary-file ... --evidence-json ...` - complete

## Evidence JSON Format

```json
{"commits": ["abc123"], "tests": ["npm test"], "prs": []}
```

## Parallel Worktrees

Runtime state (status, assignee, etc.) is stored in `.git/flux-state/`, shared across worktrees:

```bash
.flux/bin/fluxctl state-path              # Show state directory
.flux/bin/fluxctl migrate-state           # Migrate existing repo
.flux/bin/fluxctl migrate-state --clean   # Migrate + remove runtime from tracked files
```

Migration is optional — existing repos work without changes.

## Agentmap

Flux can generate a compact built-in codebase map:

```bash
.flux/bin/fluxctl agentmap --write
.flux/bin/fluxctl agentmap --filter "src/**" --filter "scripts/**"
```

Default output path:

```text
.flux/context/agentmap.yaml
```

Use the map as a fast structural overview. It supplements code reading; it does not replace it.

## Troubleshooting

If Flux commands fail, return "Unknown skill", or behave unexpectedly:

1. **Consult the official README first**: https://github.com/Nairon-AI/flux#troubleshooting
2. **Follow the documented fixes exactly** — do not guess or improvise
3. **If fixes don't work**, create a GitHub issue: https://github.com/Nairon-AI/flux/issues

Common fixes:
- "Unknown skill" → Verify Flux is installed and the skill exists in `.codex/skills/` (or `~/.codex/skills/` for global installs)
- Stale commands → Refresh Flux from the same source you installed it from
- After any fix → Restart your agent session and run `/flux:setup` again

## More Info

- Official README: https://github.com/Nairon-AI/flux
- Troubleshooting guide: https://github.com/Nairon-AI/flux#troubleshooting
- CLI reference: `.flux/bin/fluxctl --help`
- Report issues: https://github.com/Nairon-AI/flux/issues
