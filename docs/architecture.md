# Flux Architecture

How Flux executes commands and turns workflow friction into actionable improvements.

## High-Level Flow

1. User runs `/flux:*` command.
2. Command file in `commands/flux/*.md` routes to a skill.
3. Skill orchestrates scripts in `scripts/`.
4. Scripts return structured JSON.
5. Skill presents output and executes selected actions.

## Core Components

### Command Layer

- Location: `commands/flux/`
- Purpose: thin routing layer from command to skill.

Example:
- `/flux:improve` -> `skills/flux-improve/`
- `/flux:plan` -> `skills/flux-plan/`
- `/flux:work` -> `skills/flux-work/`

### Skill Layer

- Location: `skills/`
- Purpose: deterministic workflow instructions and UX behavior.
- Each skill defines steps, prompts, and command/script execution strategy.

### Script Layer

- Location: `scripts/`
- Purpose: programmatic operations and analysis.

Important scripts:
- `analyze-context.sh` - repo/framework/tooling detection
- `detect-installed.sh` - installed MCP/plugin/CLI/application detection
- `parse-sessions.py` - session friction extraction
- `match-recommendations.py` - friction-first recommendation matching
- `discover-community.py` - optional live discovery from X/Twitter sources
- `profile-manager.py` - profile export/import/view/tombstone orchestration

### Recommendations Database

- Default path: `~/.flux/recommendations`
- Source: `https://github.com/Nairon-AI/flux-recommendations`
- Categories: MCPs, CLI tools, skills, applications, workflow patterns, models

## Data Model

### Project-Local State

- `.flux/preferences.json` - dismissed recommendations, alternatives, consent preference
- `.flux/` task graph/specs for plan/work workflows

### User-Global State

- `~/.flux/recommendations` - cloned recommendations database
- `~/.flux/last_improve` - timestamp used by periodic nudge
- `~/.flux/config.json` - optional BYOK keys (`exa_api_key`, `twitter_api_key`)
- `~/.flux/profile-state.json` - saved application curation + published profile tokens

## Privacy Model

- Default behavior is local analysis.
- Session analysis requires explicit consent unless user enabled always-allow.
- Optional `/flux:improve --discover` sends search queries to external providers.
- `/flux:profile` publishes public-anonymous snapshots with automatic secret redaction and minimal metadata.

## Reliability Model

- Friction-first matching: no friction -> no recommendation.
- Install flow uses snapshot/rollback workflow.
- Non-blocking improvements: optional discovery failures do not block core recommendations.
