# Flux Agentmap Integration Plan

## Document Control

- Owner: Flux Engineering
- Status: Draft implementation plan
- Last updated: 2026-03-12
- Scope: Integrate `agentmap` into Flux as a native context artifact and workflow accelerator
- Related:
  - `skills/flux-setup/SKILL.md`
  - `skills/flux-setup/workflow.md`
  - `scripts/detect-installed.sh`
  - `scripts/fluxctl.py`

## 1) Objective

Flux now treats codebase mapping as a native capability. This plan describes how Flux-owned repo mapping fits into setup, workflow acceleration, and orchestration.

The integration goal is:

- make agentmap functionality native to Flux
- make it first-class inside Flux
- generate repo maps in predictable Flux-owned locations
- use the maps to improve startup context, planning, worker execution, and orchestration

## 2) Why Agentmap Fits Flux

The mapping system provides:

- a compact YAML inventory of files and responsibilities
- top-level definitions with line numbers
- fast structural context for fresh agent sessions
- filtering and ignore controls so maps can stay narrow

This aligns well with Flux because Flux already optimizes for:

- deterministic workflow state
- reduced context drift
- fresh-context worker execution
- faster repo realignment at session start

## 3) Product Positioning

The integration should treat `agentmap` as:

- a context artifact
- a navigation accelerator
- a cacheable repo summary

It should not be treated as:

- canonical repo documentation
- a replacement for reading code
- a required dependency for Flux setup or task execution

## 4) Desired User Experience

### For users

- Flux continues to work normally.
- No separate mapping install should be required.
- Commands should degrade gracefully only when a repo cannot be mapped safely.

### Built-in behavior

- Flux can generate a repo map through `fluxctl`.
- Flux stores maps in predictable project-local paths.
- Agents can be told where to find current maps.
- Planning and execution flows can inject filtered maps into fresh context when useful.

## 5) Integration Strategy

Implement the integration in three layers.

### 5.1 Tool Detection Layer

- expose built-in map generation through Flux
- surface availability in setup and diagnostics

### 5.2 Artifact Generation Layer

- add a Flux-native wrapper command
- generate map output into stable paths
- support filter and ignore patterns
- support stdout and file output modes

### 5.3 Workflow Consumption Layer

- make generated maps discoverable to agents
- optionally inject them into planning or worker prompts
- use them in Relay workspaces later

## 6) Proposed Commands

Recommended new `fluxctl` surface:

```bash
.flux/bin/fluxctl agentmap
.flux/bin/fluxctl agentmap --write
.flux/bin/fluxctl agentmap --out .flux/context/agentmap.yaml
.flux/bin/fluxctl agentmap --filter "src/**" --filter "scripts/**"
.flux/bin/fluxctl agentmap --ignore "dist/**" --ignore "**/*.test.ts"
.flux/bin/fluxctl agentmap --check
```

### Suggested behavior

- default: print generated YAML to stdout
- `--write`: write to Flux default path
- `--out`: custom output path
- `--check`: report built-in availability and Flux version metadata
- `--filter` and `--ignore`: apply Flux-native file filtering

## 7) Proposed Artifact Paths

Recommended paths:

- project-local stable output: `.flux/context/agentmap.yaml`
- optional issue-scoped output later: `.git/flow-state/agentmap/<scope>.yaml`

Reasons:

- easy for agents to find
- does not mix with task specs
- works well with setup-time docs and instructions

## 8) Step-by-Step Implementation Plan

## Phase 1: Native Wrapper

### Goals

- give Flux a stable native way to generate an agent map

### Steps

1. Add a new `fluxctl agentmap` command.
2. Implement generation logic directly inside Flux.
3. Return structured JSON metadata and safe empty maps for unsupported repo states.
4. Support passthrough of `--filter`, `--ignore`, and `--out`.
5. Add `--write` shortcut for `.flux/context/agentmap.yaml`.

### Exit Criteria

- users can generate the map through `fluxctl` without any external install step

## Phase 2: Setup and Docs

### Goals

- make the feature discoverable and usable

### Steps

1. Update `.flux/usage.md` template with `agentmap` examples.
2. Update Flux setup snippets to mention `.flux/context/agentmap.yaml` when present.
3. Update documentation to explain when to use the map and when to ignore it.
4. Add troubleshooting guidance for repos that produce sparse maps.

### Exit Criteria

- setup and generated docs clearly explain how Flux uses agent maps

## Phase 3: Prime Integration

### Goals

- use `agentmap` to improve repo readiness and onboarding

### Steps

1. During `/flux:prime`, optionally generate a base repo map.
2. If a repo produces no useful map entries, continue as usual and explain why.
4. Later, measure map coverage quality by checking whether important files include header comments.

### Exit Criteria

- prime can recognize and leverage built-in agent maps without any setup dependency

## Phase 4: Planning and Work Integration

### Goals

- use maps to reduce startup cost for fresh-context workers

### Steps

1. Allow plan/work skills to reference a generated map when present.
2. Prefer filtered maps scoped to relevant directories.
3. Avoid blindly injecting huge maps into every prompt.
4. Add guardrails so maps supplement, rather than replace, code reading.

### Exit Criteria

- fresh workers can use a targeted structural snapshot before repo exploration

## Phase 5: Relay Integration

### Goals

- use maps in orchestrated issue workspaces

### Steps

1. On workspace creation, generate an issue-scoped agent map.
2. Use the map as part of the workspace bootstrap context.
3. Refresh the map when important files in the workspace change.

### Exit Criteria

- Relay runs start with a useful structural view of the workspace

## 9) Guardrails

- the feature must be native to Flux
- Flux must not rely on a separate `agentmap` binary
- generated maps should be filtered when possible
- maps should not be treated as authoritative truth
- maps should be stored in predictable, Flux-owned paths

## 10) Risks

### Risk: Low map quality

- Cause: files without header comments are excluded
- Mitigation: recommend targeted comment bootstrapping on important files only

### Risk: Prompt bloat

- Cause: large map injected into every session
- Mitigation: use filtered maps and explicit opt-in consumption

### Risk: False confidence

- Cause: agent trusts the map too much and skips reading code
- Mitigation: document that the map is navigation aid only

## 11) Definition of Done

The integration should be considered successful when:

- Flux can generate an `agentmap` artifact via `fluxctl`
- generated maps have a stable default location
- generated setup docs mention the map when relevant
- Flux workflows can consume the map without requiring it
- the feature is tested and degrades gracefully when a repo cannot produce useful map entries
