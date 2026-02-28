# Changelog

All notable changes to Flux will be documented in this file.

## [1.6.0] - 2026-03-01

### Added

- **Brain Vault** — Persistent memory system that makes the agent smarter over time
  - Obsidian-compatible markdown vault at `brain/`
  - 16 battle-tested engineering principles included as starter content
  - Session-start hook auto-injects brain index for context
  - Auto-index hook maintains `brain/index.md` when files change

- **`/flux:reflect`** — Capture learnings from current session
  - Scans conversation for mistakes, corrections, and knowledge gained
  - Routes learnings to brain, skills, or structural enforcement
  - Run at end of sessions or after corrections

- **`/flux:ruminate`** — Mine past Claude Code conversations
  - Extracts uncaptured patterns from conversation history
  - Cross-references with existing brain content
  - Filters by frequency and impact

- **`/flux:meditate`** — Audit and evolve the brain vault
  - Prunes outdated/redundant notes
  - Discovers cross-cutting principles from patterns
  - Reviews skills for structural encoding opportunities

- **`flux-brain` skill** — Conventions for reading/writing brain files

### Credits

Brain vault system adapted from [brainmaxxing](https://github.com/poteto/brainmaxxing) by [@poteto](https://github.com/poteto).

---

## [1.0.0] - 2026-02-23

### Rebrand: Flux → Flux

Flux is the new name. Same workflow engine, now with AI-native capability scoring.

### Added

- **Flux Score** (`/flux:score`) — Compute your AI-native capability score from Claude Code session data
  - 5 dimensions: Interview Depth, Pushback Ratio, Prompt Quality, Iteration Efficiency, Tool Breadth
  - Weighted composite score (0-100) with letter grades (S/A/B/C/D/F)
  - Output formats: table, JSON, YAML
  - Date filtering: `--since`, `--until`
  - Evidence export for recruiting: `--export evidence.yaml`

- **Score Schema** (`docs/flux-score-schema.md`) — Full specification of scoring dimensions with SQL queries and evidence format

- **Session Analysis Script** (`scripts/flux-score.py`) — Python implementation based on ccql patterns
  - Loads history, transcripts, todos from `~/.claude/projects/`
  - Computes all 5 dimension scores
  - CLI with flexible output options

### Changed

- All commands renamed: `/flux:*` → `/flux:*`
- Plugin name: `flux` → `flux`
- GitHub repos renamed:
  - `Nairon-AI/flux` → `Nairon-AI/flux`
  - `Nairon-AI/flux-recommendations` → `Nairon-AI/flux-recommendations`

### Migration

If upgrading from Flux:
1. Uninstall old plugin: `/plugin uninstall nairon-flux`
2. Install Flux: `/plugin marketplace add Nairon-AI/flux`
3. Commands work the same, just with `/flux:` prefix

---

## [0.9.0] - 2026-02-23

### Added

- **Community Discord** — Join at [discord.gg/CEQMd6fmXk](https://discord.gg/CEQMd6fmXk)
- README polish: "I'm tired, boss" gif and Community section

### Changed

- Edge-case hardening in `detect-installed.sh`:
  - Graceful handling of malformed `~/.mcp.json`, `~/.claude.json`, `~/.claude/preferences.json`
  - Warnings output in JSON diagnostics instead of crash
- AUDIT.md updated with completion status emojis

### Fixed

- Malformed JSON no longer crashes detection scripts

## [flux 0.8.0] - 2026-02-22

### Added

- **Profile workflows** via `/flux:profile`:
  - export machine setup as immutable public-anonymous snapshots
  - import teammate profiles with compatible-only filtering + per-item consent
  - view snapshots and owner tombstone support
  - app curation memory (`~/.flux/profile-state.json`) and skills scope selection (`global|project|both`)

- **New script**: `scripts/profile-manager.py`
  - setup detection for MCP/CLI/skills/apps/patterns/model preferences
  - auto-redaction of sensitive values before publish
  - link service integration: publish, fetch, tombstone
  - import planning + install orchestration helpers

- **New tests/docs**:
  - `scripts/test_profile_manager.py`
  - profile coverage in `tests/scripts.test.ts`
  - `docs/profile-command-spec.md`, `docs/profile-schema.md`, `docs/profile-launch-checklist.md`

- **Community discovery mode** for `/flux:improve`:
  - `--discover` enables optional live search for novel optimizations from X/Twitter sources
  - Exa-first search with Twitter API fallback
  - BYOK support via `~/.flux/config.json` (`exa_api_key`, `twitter_api_key`)

- **Explainability mode** for recommendation transparency:
  - `--explain` includes top friction signals and detected gap summary
  - recommendation output now includes source metadata (`source`, `source_url`)

- **New script**: `scripts/discover-community.py`
  - friction-aware query generation
  - URL canonical dedupe + ranking
  - non-blocking failure behavior

- **New tests**:
  - `scripts/test_discover_community.py`
  - explain/source assertions in `scripts/test_e2e.py`

### Changed

- README onboarding and quick demo flow clarified
- full command reference added in `docs/commands-reference.md`
- privacy copy updated to reflect optional external search behavior

## [flux 0.7.0] - 2026-02-22

### Added

- **Optional user context boost** for `/flux:improve`:
  - asks user for short pain-point description
  - maps plain-language frustrations into friction signals
  - significantly improves recommendation precision when provided

- `--user-context` support in `match-recommendations.py`

- Extended end-to-end tests for user-context parsing and integration

### Changed

- README restructured around interview -> plan -> implement -> review workflow
- Added product vision section for engineering observability

## [flux 0.6.0] - 2026-02-21

### Added

- **Friction-first recommendation engine**
  - recommendations are triggered by detected friction, not just missing tools
  - expanded friction signal mapping for docs, linting, CI, memory, UI, and reasoning gaps

- **Session analysis enhancements**
  - broader pattern detection for user frustration, tool output errors, and agent confusion
  - stronger end-to-end coverage and friction coverage tests

### Changed

- `/flux:improve` output and docs improved for clarity and FAQ coverage

## [flux 0.5.0] - 2026-02-21

### Added

- **Session analysis** — `parse-sessions.py` analyzes Claude Code sessions to detect pain points:
  - API errors and retry patterns
  - Tool failures (is_error, exit codes, file not found)
  - Knowledge gaps ("I don't know how to...", repeated lookups)
  - Tool usage statistics across sessions

- **Pattern-to-recommendation mapping** — Session insights now drive recommendations:
  - `unknown_skill` errors → plugin management suggestions
  - `file_not_found` patterns → file navigation tools (fzf)
  - `timeout` issues → performance optimizations
  - Knowledge gaps → documentation tools (context7, supermemory)

- **9 new tests** for session analysis in `tests/scripts.test.ts`

### Changed

- `analyze-sessions.sh` now delegates to Python parser for full analysis
- `match-recommendations.py` integrates session insights into gap detection

## [flux 0.4.0] - 2026-02-21

### Added

- **E2E test suite** — Comprehensive tests using tuistory (Playwright for TUIs):
  - `tests/scripts.test.ts` — 25 fast tests for all Flux scripts (detect-installed, analyze-context, manage-preferences, etc.)
  - `tests/claude-commands.test.ts` — 13 tests for Claude Code command invocation
  - Verifies plugin installation, skill loading, and command execution

- **Test infrastructure** — Added `package.json` with test scripts:
  - `bun test:scripts` — Fast CI-friendly tests (~1s)
  - `bun test:claude` — Full E2E tests with Claude Code (~98s)
  - `bun test:all` — Complete test suite

### Developer Experience

- All `/flux:*` commands verified working via automated tests
- tuistory enables TUI testing for Claude Code plugins
- Scripts output validated (JSON structure, expected fields)

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
