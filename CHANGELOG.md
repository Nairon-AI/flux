# Changelog

All notable changes to Flux will be documented in this file.

## [Unreleased]

### Fixed

- Version guard CI now runs on PRs (not just push to main) to catch missing `-dev` suffix before merge

## [2.3.1] - 2026-03-14

### Fixed

- Reordered epic-review pipeline: Desloppify → Human Review → Learning Capture → Frustration Signal (was Learning Capture first)
- Reverted "Sub-Agent Model" label back to "Scout Model" (config only applies to prime scouts)
- Added `-dev` suffix to version files on main to fix version guard CI

## [2.3.0] - 2026-03-14

### Added

- **Human Review via Critique TUI** — opt-in during `/flux:setup`, non-blocking terminal diff review after AI reviews finish
  - Per-task: after impl-review SHIP verdict
  - Per-epic: after all automated passes complete
  - Prints `bunx critique main` command for a separate terminal

## [2.2.1] - 2026-03-14

### Fixed

- **Anti-sycophancy review hardening** — addresses the problem where AI reviewers confirm rather than challenge
  - Brain vault principles + pitfalls now loaded into review prompts as evaluation criteria
  - Anti-sycophancy preamble: "Your job is to find problems, not confirm quality"
  - Adversarial reviewers must form independent verdicts before consensus merge

## [2.2.0] - 2026-03-14

### Added

- **`/flux:rca`** — dedicated root cause analysis workflow for bugs
  - Flow: Reproduce → Investigate → Root Cause → Verify → Fix → Desloppify → Learn
  - Implicit detection: `/flux:scope` catches bug signals and routes to RCA
  - Three severity tiers: Quick, Standard, Critical
  - Two investigation engines: Flux backward trace or RepoPrompt Investigate
  - Mandatory regression testing (manual checklist if no test infra)
  - Embedded learning: pitfall notes + structural prevention proposals

## [2.1.0] - 2026-03-14

### Added

- **`/flux:propose`** — stakeholder feature proposal skill
  - Implicit detection in `/flux:scope` for non-technical users
  - Engineering pushback with codebase-grounded assessments and cost research
  - Conservative complexity/time estimates with vibe-coding grounding statement
  - Outputs to `docs/proposals/` with PR for engineering handoff
  - Duplicate proposal detection

## [2.0.4] - 2026-03-14

### Changed

- Removed Claudeception (redundant with brain vault + reflect)
- Enhanced `/flux:reflect` with skill extraction capability (ported from Claudeception)

## [2.0.3] - 2026-03-14

### Changed

- Removed Supermemory MCP (redundant with brain vault and `.flux/` state)
- Recommended MCPs now: FFF, Context7, Exa, GitHub, Firecrawl

## [2.0.2] - 2026-03-14

### Added

- **FFF (Fast File Finder) MCP** — 10x faster fuzzy file search, recommended during `/flux:setup`
- README setup section now lists every recommended tool with descriptions

## [2.0.1] - 2026-03-14

### Improved

- **Progressive disclosure for `/flux:scope`** — split from 1,709 → 208 lines (88% reduction)
  - Reference files loaded on-demand: `linear.md`, `explore-steps.md`, `solution.md`, `completion.md`
  - Follows Anthropic's 500-line SKILL.md guideline

## [2.0.0] - 2026-03-14

### Added

- **Two-tier review architecture**
  - `/flux:impl-review` — lightweight per-task review
  - `/flux:epic-review` — full 9-phase pipeline (spec compliance → adversarial → security → bot self-heal → browser QA → desloppify → human review → learning capture → frustration signal)
- **Adversarial dual-model review** — configure two reviewer models (Anthropic + OpenAI), independent verdicts with consensus merge
- **BYORB (Bring Your Own Review Bot)** — Greptile and CodeRabbit integration with self-heal loop
- **Browser QA** — agent-browser testing during epic review, checklist generated during scoping
- **Security scan in review pipeline** — auto-triggered STRIDE analysis on security-sensitive changes
- **Brain vault as single knowledge store** — replaced `.flux/memory/` with `brain/` (pitfalls, principles, conventions, decisions)
  - Area-organized pitfalls: `brain/pitfalls/<area>/<pattern>.md`
  - Wired into scope (read), work (re-anchor), review (write), meditate (prune/promote)
- **Self-improving harness**
  - Recommendation pulse at session start (once/day)
  - Two-layer frustration detection (quantitative + qualitative)
  - Meditate auto-nudge when brain vault is stale
  - `/flux:reflect` suggestion after shipping
- **Configurable review severity threshold** — multi-select which severities to auto-fix (critical, major, minor, style)
- **SDLC state engine mermaid diagram** in README
- **Desloppify scan** integrated into epic-review pipeline
- **`/flux:release` skill** — version-safe releases with manifest sync

### Changed

- Deprecated `.flux/memory/` subsystem (replaced by brain vault)
- Removed `memory-scout` agent and `fluxctl memory` CLI commands

## [1.9.10] - 2026-03-13

### Added

- Ralph mode prompt after scoping — asks if you want to run the epic autonomously overnight

### Fixed

- `/plugin remove` → `/plugin uninstall` across all 19 skill files

## [1.9.9] - 2026-03-13

### Added

- **Linear task tracker integration** — epics sync as projects, tasks as issues, status changes auto-update
- Linear CLI skill installed via `npx skills add` during setup
- Tracker hooks in `fluxctl_pkg/tracker.py`

## [1.9.8] - 2026-03-13

### Changed

- **fluxctl modular refactor** — 9,095-line monolith split into 10 focused modules under `fluxctl_pkg/`
- Renamed all `flow` → `flux` references (22 files, env vars, function names)
- Agent-driven uninstall flow — agent handles cleanup, user only runs `/plugin uninstall`

## [1.9.7] - 2026-03-13

### Added

- **Codex-powered scouts** — `/flux:prime` respects configured scout model with preflight check and graceful fallback
- Codex auth verification during `/flux:setup`
- Browser automation detection in prime testing scout
- **Project-local installs** — all MCPs, skills, and config are project-scoped (nothing touches global config)

### Changed

- README restructured: "The Problem" leads, bullet-point overview, `--resume` in all restart instructions
- Removed Ghostty and unused `assets/` directory

## [1.9.6] - 2026-03-12

### Added

- **Plugin cache guard** — post-release bump + version guard CI
- **Adversarial multi-model reviews** — plans and implementations reviewed by a second model
- Clear "what to do next" after `/flux:setup`

### Changed

- Claude Code is now the only supported platform (removed Factory Droid and Codex platform support)
- Removed Cartographer skill (redundant with built-in agentmap)

## [1.9.5] - 2026-03-12

### Added

- **Native `agentmap` wrapper in `fluxctl`**
  - `fluxctl agentmap --check` reports whether `agentmap` is available in `PATH`
  - `fluxctl agentmap --write` writes a project-local map to `.flux/context/agentmap.yaml`

### Changed

- `fluxctl agentmap` now uses a built-in implementation instead of requiring an external CLI
- `/flux:setup` no longer recommends `agentmap` as a separate tool

## [1.9.4] - 2026-03-11

### Added

- **Deterministic workflow state engine** — `session-state` for startup routing, `scope-status` for active objective tracking
- **Product OS-style scope persistence** — `.flux/artifacts/` stores resumable scoping phase outputs

## [1.9.3] - 2026-03-10

### Improved

- Core workflow messaging: `Prime → Scope → Work → Impl-Review → Improve`, `Reflect` at end of session
- `/flux:setup` final reminder prints the full sequence plus Superset orchestrator guidance

## [1.9.2] - 2026-03-10

### Added

- Expanded `/flux:setup` optional install packs: Firecrawl MCP, jq, fzf, Lefthook, Agent Browser, CLI Continues, Agentmap, Superset, and 8 agent skills

## [1.9.1] - 2026-03-08

### Fixed

- Safe upgrade path unified — all update prompts use `/plugin add https://github.com/Nairon-AI/flux@latest`
- Nested session install failures in setup guidance
- Plugin helper install output normalization

## [1.9.0] - 2026-03-03

### Added

- **Universe Authentication** — `/flux:login`, `/flux:logout`, `/flux:status`

### Fixed

- Plugin installation — added `$schema` and `category` fields to marketplace.json

### Contributors

- [@Lukaeric14](https://github.com/Lukaeric14) — Universe auth commands and score sync

---

## [1.8.0] - 2026-03-02

### Fixed

- Install command documentation updated to use `/plugin add`
- Added cache clearing instructions for version upgrades

---

## [1.7.0] - 2026-03-01

### Added

- **STRIDE Security Analysis** — `/flux:threat-model`, `/flux:security-scan`, `/flux:security-review`, `/flux:vuln-validate`

### Credits

Security skills adapted from [Factory AI security-engineer plugin](https://github.com/Factory-AI/factory-plugins).

---

## [1.6.0] - 2026-03-01

### Added

- **Brain Vault** — Obsidian-compatible persistent memory at `brain/`
- **`/flux:reflect`**, **`/flux:ruminate`**, **`/flux:meditate`** — learning capture, history mining, vault auditing

### Credits

Brain vault system adapted from [brainmaxxing](https://github.com/poteto/brainmaxxing) by [@poteto](https://github.com/poteto).

---

## [1.0.0] - 2026-02-23

### Added

- **Flux Score** (`/flux:score`) — AI-native capability scoring (5 dimensions, letter grades, evidence export)

### Changed

- Rebranded from Flux to Flux with `/flux:*` command prefix

---

## [0.9.0] - 2026-02-23

### Added

- Community Discord

### Fixed

- Malformed JSON no longer crashes detection scripts

## [0.8.0] - 2026-02-22

### Added

- **Profile workflows** (`/flux:profile`) — export/import/view machine setup snapshots
- **Community discovery** for `/flux:improve` — `--discover` flag with Exa/Twitter search
- **Explainability mode** — `--explain` for recommendation transparency

## [0.7.0] - 2026-02-22

### Added

- Optional `--user-context` for `/flux:improve` — maps plain-language frustrations to friction signals

## [0.6.0] - 2026-02-21

### Added

- Friction-first recommendation engine — recommendations triggered by detected friction, not just missing tools

## [0.5.0] - 2026-02-21

### Added

- Session analysis (`parse-sessions.py`) — detects API errors, tool failures, knowledge gaps
- Pattern-to-recommendation mapping

## [0.4.0] - 2026-02-21

### Added

- E2E test suite with tuistory (Playwright for TUIs) — 25 script tests + 13 command tests

## [0.3.0] - 2026-02-21

### Added

- SDLC-aware recommendation engine with installed tools detection and user preferences

## [0.2.0] - 2026-02-21

### Added

- `/flux:improve` command, session analysis consent flow, installer scripts, rollback system

## [0.1.0] - 2026-02-20

### Added

- Initial release — `/flux:plan`, `/flux:work`, `/flux:prime`, `/flux:sync`, `/flux:setup`
- Subagent architecture with context isolation per task
