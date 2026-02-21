# Changelog

All notable changes to Flux will be documented in this file.

## [flux 0.3.0] - 2026-02-21

### Added

- **SDLC-aware recommendation engine** — Analyzes gaps across requirements, planning, implementation, review, testing, and documentation phases. Only recommends tools that fill actual workflow gaps.

- **Installed tools detection** — `detect-installed.sh` auto-detects CLI tools, macOS/Linux applications, MCPs, and plugins. Skips recommendations for tools you already have.

- **Equivalent tool detection** — Recognizes alternatives (e.g., if you have ESLint, won't recommend OxLint/Biome). Prevents redundant suggestions.

- **User preferences system** — `manage-preferences.sh` for persistent settings:
  - Dismiss recommendations you don't want
  - Record alternatives ("I use Otter instead of Granola")
  - "Always allow" session analysis (skip consent prompt)
  - Stored in `~/.flux/preferences.json`

- **New command flags**:
  - `--detect` — Show detected installed tools
  - `--preferences` — Show/manage user preferences  
  - `--dismiss <name>` — Dismiss a recommendation
  - `--alternative <rec> <alt>` — Record that you use an alternative
  - `--sessions always|ask` — Control session consent behavior

- **Pricing information** — Each recommendation includes pricing model (free, freemium, paid, open-source) and cost details.

- **"Solves" field** — Each recommendation explains what specific workflow problem it addresses.

### Changed

- **Recommendations reorganized** — MCPs split into design/, search/, productivity/, dev/. Applications split into individual/ vs collaboration/. CLI tools grouped by function.

- **Smarter matching** — Reduced from spray-and-pray to targeted recommendations based on detected SDLC gaps.

## [flux 0.2.0] - 2026-02-21

### Added

- **`/flux:improve` command** — Analyze environment and recommend workflow optimizations (MCPs, plugins, skills, CLI tools, patterns). Fetches recommendations from `Nairon-AI/flux-recommendations` database.

- **Session analysis consent flow** — Privacy-first approach using `mcp_question` for explicit user consent before analyzing Claude Code sessions. Displays what data is analyzed and confirms local-only processing.

- **`analyze-sessions.sh` script** — Stub for Phase 3 pattern detection. Scans `~/.claude/projects/` for recent sessions and returns structured JSON for error patterns, knowledge gaps, and repeated queries.

- **`analyze-context.sh` enhancements** — New `--include-sessions` flag integrates session analysis. Output now includes `session_insights` field when user consents.

- **Installer scripts** — Complete installation tooling:
  - `install-mcp.sh` — Merges MCP config into `~/.mcp.json`
  - `install-cli.sh` — Runs brew/npm install commands
  - `install-plugin.sh` — Claude Code plugin installation instructions
  - `install-skill.sh` — Copies skills to `~/.claude/skills/`

- **Verification script** — `verify-install.sh` confirms installations via command existence, config checks, or MCP connectivity.

- **Rollback system** — `rollback.sh` restores from timestamped snapshots in `~/.flux/snapshots/`.

- **23 recommendations** in flux-recommendations database:
  - MCPs (7): context7, exa, linear, supermemory, github, figma, excalidraw
  - CLI tools (6): lefthook, oxlint, beads, biome, jq, fzf
  - Applications (4): wispr-flow, granola, raycast, dia
  - Skills (3): stagehand-e2e, remotion, repoprompt
  - Workflow patterns (5): agents-md-structure, pre-commit-hooks, test-first-debugging, atomic-commits, context-management

### Changed

- **Context analysis output** — Now includes `session_insights` in JSON output structure.

## [flux 0.1.0] - 2026-02-20

### Added

- **Initial release** — AI-augmented SDLC workflow plugin for Claude Code.

- **`/flux:plan`** — AI-augmented planning with spec validation and worker subagent architecture.

- **`/flux:work`** — Worker subagent execution per task with context isolation.

- **`/flux:prime`** — Codebase health assessment.

- **`/flux:sync`** — State synchronization across sessions.

- **`/flux:setup`** — Project initialization and configuration.

- **Subagent architecture** — Context isolation per task prevents cross-contamination.

- **Skills** — `flux-plan-check`, `flux-pr-integration` for plan validation and PR workflows.
