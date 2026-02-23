---
name: nbench-setup
description: Optional local install of nbenchctl CLI and CLAUDE.md/AGENTS.md instructions. Use when user runs /nbench:setup.
user-invocable: false
---

# Flux Setup (Optional)

Install nbenchctl locally and add instructions to project docs. **Fully optional** - flux works without this via the plugin.

## Benefits

- `nbenchctl` accessible from command line (add `.nbench/bin` to PATH)
- Other AI agents (Codex, Cursor, etc.) can read instructions from CLAUDE.md/AGENTS.md
- Works without Claude Code plugin installed
- Installs `claudeception` by default (if missing) for continuous learning

## Workflow

Read [workflow.md](workflow.md) and follow each step in order.

## Notes

- **Fully optional** - standard plugin usage works without local setup
- Copies scripts (not symlinks) for portability across environments
- Safe to re-run - will detect existing setup and offer to update
