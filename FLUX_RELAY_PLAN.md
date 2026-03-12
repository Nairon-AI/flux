# Flux Relay Integration Plan

## Document Control

- Owner: Flux Engineering
- Status: Draft implementation plan
- Last updated: 2026-03-12
- Scope: Add the Relay orchestration layer to Flux without replacing Flux's existing planning and execution model
- Related:
  - `README.md`
  - `docs/architecture.md`
  - `docs/fluxctl.md`
  - `docs/codex-install.md`

## 1) Executive Summary

This document describes how to add Relay to Flux.

The core idea is:

- Flux remains the repo-local workflow and state engine.
- A new orchestration service becomes the outer control plane.
- The orchestration service watches an external work source such as Linear.
- For each eligible issue, it creates or reuses an isolated workspace.
- Inside that workspace, it runs Flux-native planning, implementation, review, and handoff flows.

This plan intentionally does not implement anything. It defines the target architecture, sequencing, data contracts, rollout stages, risks, and acceptance criteria required to build the orchestration layer safely.

## 2) Why This Exists

Flux already does these things well:

- Repo-local state and workflow alignment through `.flux/`
- Structured plan -> work -> review -> improve loops
- Worker-based execution with fresh context
- Task-level review gates and completion checks
- Multi-agent support in Codex-compatible environments

What Flux does not currently provide as a first-class product surface:

- A long-running daemon that continuously pulls work from a tracker
- Tracker-driven dispatch with bounded concurrency
- Per-issue workspace lifecycle management
- Retry scheduling, reconciliation, and stop/cleanup behavior
- Always-on runtime observability for many concurrent runs

Relay fills exactly that gap. The integration should therefore treat the new orchestration layer as a control plane above Flux, not as a replacement for Flux internals.

## 3) Target Outcome

At the end of this work, Flux should be able to support this flow:

1. An issue enters an eligible state in Linear.
2. Flux Orchestrator claims the issue.
3. Flux Orchestrator creates or reuses an isolated workspace for that issue.
4. Flux Orchestrator loads a repo-owned workflow contract.
5. Flux Orchestrator starts a Codex app-server session in that workspace.
6. The session uses Flux-native skills and `fluxctl` state to plan and execute the issue.
7. Review gates run automatically according to Flux policy.
8. The issue moves to a workflow-defined handoff state such as `Human Review`, `Rework`, `Merging`, or `Done`.
9. The orchestrator records logs, metrics, receipts, and runtime state for operators.
10. If the issue becomes ineligible, the orchestrator stops the run and reconciles workspace state safely.

## 4) Non-Goals

These items should not be part of the initial implementation:

- Replacing Flux commands with a new command system
- Rewriting Flux skills around a non-Flux workflow model
- Introducing a multi-tenant SaaS control plane
- Supporting every tracker on day one
- Full remote SSH worker execution in v1
- Auto-merge-to-main without explicit policy and safeguards
- Replacing `.flux/` as canonical repo workflow memory
- Requiring Elixir inside the Flux repository

## 5) Core Product Decision

### Recommendation

Implement Relay inside Flux as a new Python-based orchestration subsystem, not by embedding an external Elixir implementation directly.

### Rationale

- Flux already has meaningful Python infrastructure through `scripts/fluxctl.py`.
- Flux also uses shell scripts and Bun tests, but it does not currently have an OTP-style service runtime.
- Adding Elixir as a hard dependency would materially increase install, contributor, and CI complexity.
- A Python service is a better fit for the current repository and contributor profile.
- The implementation should borrow proven orchestration patterns and contracts, not another project's language choice.

## 6) Architectural Positioning

The integration should be split into five layers.

### 6.1 Policy Layer

- Repo-owned workflow contract, likely `WORKFLOW.md`
- Flux-specific orchestration instructions
- State mappings between tracker statuses and Flux workflow phases
- Guardrails for reviews, handoffs, retries, and landing

### 6.2 Coordination Layer

- Poll loop
- eligibility checks
- claim and release logic
- retry scheduling
- restart recovery
- cancellation and reconciliation

### 6.3 Execution Layer

- workspace creation and reuse
- app-server session management
- prompt rendering
- Flux command invocation inside workspace

### 6.4 Integration Layer

- Linear adapter in v1
- future adapters later

### 6.5 Observability Layer

- structured logs
- runtime state snapshots
- operator status output
- receipts and artifacts

## 7) Source of Truth Model

This integration will only be stable if source-of-truth boundaries are explicit.

### 7.1 External Work Source

- Linear is the upstream source of incoming work in v1.
- Linear issue state determines eligibility for orchestration.

### 7.2 Internal Workflow Source

- `.flux/` remains the canonical source of repo-local plan, task, and execution state.
- `fluxctl` remains the only supported write path for Flux plan/task state.

### 7.3 Runtime Orchestration Source

- A new runtime state store will track active sessions, claims, retries, workspace paths, and process metadata.
- This runtime state must be restart-safe but should not pollute tracked repo files.

### 7.4 Workflow Contract Source

- A repo-owned orchestration contract file should define orchestration policy and prompt body.
- Recommended file name: `WORKFLOW.md`
- Reason: it keeps orchestration policy versioned with the repo and separate from transient runtime state.

## 8) Mapping Model Between Linear and Flux

This is the most important design choice.

### Recommended v1 Mapping

- One Linear issue maps to one Flux epic.
- Flux may create one or more tasks under that epic.
- The orchestrator owns the workspace per Linear issue.
- The workspace persists across retries and across multiple Flux tasks within that issue.

### Why This Mapping

- It preserves Flux's planning depth.
- It allows one external ticket to decompose into multiple repo-local implementation tasks.
- It avoids forcing Flux into a one-ticket-one-task model that would be too narrow for real feature work.

### Optional v1.5 Mapping

- Support a "small ticket mode" where one Linear issue maps directly to one Flux task.
- This should be an explicit workflow setting, not implicit behavior.

## 9) Proposed Repository Additions

These are proposed targets for implementation. They are planning placeholders, not a commitment to exact filenames.

### Commands

- `commands/flux/orchestrate.md`
- Optional subcommands later:
  - `flux orchestrate start`
  - `flux orchestrate stop`
  - `flux orchestrate status`
  - `flux orchestrate run-once`
  - `flux orchestrate doctor`

### Skills

- `skills/flux-orchestrate/`
- `skills/flux-orchestrate/SKILL.md`
- `skills/flux-orchestrate/workflow.md`

### Scripts

- `scripts/orchestrator/daemon.py`
- `scripts/orchestrator/config.py`
- `scripts/orchestrator/workflow_loader.py`
- `scripts/orchestrator/state_store.py`
- `scripts/orchestrator/linear_client.py`
- `scripts/orchestrator/workspace_manager.py`
- `scripts/orchestrator/agent_runner.py`
- `scripts/orchestrator/retry_queue.py`
- `scripts/orchestrator/status.py`

### Documentation

- `docs/orchestration-requirements.md`
- `docs/orchestration-spec.md`
- `docs/orchestration-operator-guide.md`
- `docs/workflow-contract.md`

### Runtime State

- Preferred runtime location: `.git/flow-state/orchestrator/`
- Fallback when git common dir is unavailable: `.flux/runtime/orchestrator/`

## 10) Step-by-Step Implementation Plan

## Phase 0: Align on Product Boundaries

### Goals

- Confirm that Flux remains the workflow engine.
- Confirm that Relay is an outer daemon layer.
- Lock the v1 scope before code begins.

### Steps

1. Write requirements for tracker-driven orchestration.
2. Write a technical spec for orchestration architecture.
3. Document source-of-truth rules between Linear, `.flux/`, and runtime state.
4. Decide the v1 issue-to-epic mapping.
5. Decide the v1 command surface and operator UX.
6. Decide whether `WORKFLOW.md` lives at repo root or under `.flux/`.
7. Define the initial allowed tracker states and handoff states.

### Deliverables

- Approved requirements doc
- Approved technical spec
- Approved state model
- Approved workflow contract schema

### Exit Criteria

- No unresolved disagreement about who owns task state, tracker state, or orchestration state.

## Phase 1: Define the Workflow Contract

### Goals

- Introduce a repo-owned orchestration contract that Flux Orchestrator can load.
- Keep it compatible with the Relay architecture while remaining Flux-native.

### Steps

1. Define front matter fields for:
   - tracker config
   - workspace config
   - poll cadence
   - active states
   - terminal states
   - handoff states
   - concurrency limits
   - retry policy
   - Codex app-server command
   - hooks
   - Flux integration mode
2. Define a markdown body template for the per-issue prompt.
3. Add Flux-specific fields, for example:
   - epic mapping mode
   - whether planning is required before work
   - review backend override
   - completion review requirement
   - plan-sync behavior
4. Define validation rules and defaults.
5. Define reload semantics if `WORKFLOW.md` changes while the daemon is running.

### Deliverables

- Workflow contract schema
- Example `WORKFLOW.md`
- Validation rules

### Exit Criteria

- A single workflow file can drive orchestration behavior without extra hidden config.

## Phase 2: Build the Orchestrator Runtime Skeleton

### Goals

- Create a long-running service process that can start, stop, persist state, and run a single poll cycle.

### Steps

1. Add a daemon entrypoint.
2. Add a run-once mode for local debugging and tests.
3. Add startup config loading and validation.
4. Add structured log output.
5. Add runtime state initialization.
6. Add signal handling for clean shutdown.
7. Add lock or single-instance safeguards so multiple local daemons do not corrupt claims.

### Deliverables

- Daemon bootstrap
- Config loader
- Single-instance protection
- Basic log output

### Exit Criteria

- The daemon can boot with a valid `WORKFLOW.md`, print health state, and shut down cleanly.

## Phase 3: Add Linear Integration

### Goals

- Allow the orchestrator to discover candidate work from Linear.

### Steps

1. Define the normalized issue model.
2. Implement a Linear client with:
   - project filter
   - active state filtering
   - terminal state lookup
   - issue refresh by id
3. Normalize:
   - identifier
   - title
   - body
   - priority
   - labels
   - state
   - branch metadata
   - URL
   - blockers
4. Add typed errors and backoff behavior for tracker failures.
5. Add test fixtures for Linear responses.

### Deliverables

- Linear adapter
- Normalized issue model
- Tracker error taxonomy

### Exit Criteria

- A poll cycle can return normalized issues and classify them correctly as eligible, terminal, or ineligible.

## Phase 4: Add Workspace Management

### Goals

- Ensure each issue gets a deterministic isolated workspace.

### Steps

1. Define workspace naming rules from issue identifier.
2. Define workspace root configuration.
3. Implement workspace create/reuse logic.
4. Implement path sanitization and root-containment validation.
5. Implement lifecycle hooks:
   - `after_create`
   - `before_run`
   - `after_run`
   - `before_delete`
6. Decide cleanup behavior for terminal issues.
7. Decide retention behavior for successful handoff states.

### Deliverables

- Workspace manager
- Hook runner
- Cleanup policy

### Exit Criteria

- The daemon can create and reuse the correct workspace for an issue without escaping the configured root.

## Phase 5: Add Orchestration State and Claim Logic

### Goals

- Prevent duplicate work and make retries/restarts deterministic.

### Steps

1. Define runtime entities:
   - running entry
   - claim record
   - retry entry
   - session metadata
   - workspace metadata
2. Store runtime state outside tracked repo files.
3. Implement issue claim acquisition.
4. Implement release rules for:
   - success
   - handoff
   - terminal tracker state
   - retry exhaustion
   - operator stop
5. Implement startup recovery.
6. Implement reconciliation for issues whose tracker state changes mid-run.

### Deliverables

- State store
- Claim/release engine
- Recovery behavior

### Exit Criteria

- The daemon can restart and recover known runs without duplicating claims.

## Phase 6: Add the Agent Runner Interface

### Goals

- Create a single execution abstraction for app-server sessions.

### Steps

1. Define a runner interface independent of tracker logic.
2. Implement a Codex app-server runner in v1.
3. Ensure every run executes with:
   - `cwd` equal to the issue workspace
   - configured sandbox policy
   - configured approval policy
4. Stream session events back into orchestrator state.
5. Track:
   - thread id
   - turn id
   - token counts
   - latest event
   - timestamps
   - error reason
6. Define stop, timeout, and stall-detection behavior.

### Deliverables

- Runner interface
- Codex app-server runner
- Event normalization

### Exit Criteria

- The daemon can launch a real app-server session in the correct workspace and observe its lifecycle.

## Phase 7: Make Flux the Execution Policy Inside the Workspace

### Goals

- Ensure orchestration uses Flux-native workflows instead of bypassing them.

### Steps

1. Define a Flux orchestration prompt template.
2. Decide how the agent should bootstrap when it enters a workspace:
   - detect existing `.flux/` state
   - initialize `.flux/` if missing
   - map tracker issue to epic
3. Decide epic creation behavior:
   - create epic automatically if missing
   - attach issue metadata to epic
4. Decide whether planning is required before implementation.
5. Define the execution loop:
   - plan if necessary
   - select ready task
   - run worker
   - run impl review
   - run plan-sync if drift occurs
   - move to completion review when epic is done
6. Define how the agent updates Linear:
   - comments
   - state changes
   - PR links
   - receipts
7. Ensure all plan/task writes still go through `fluxctl`.

### Deliverables

- Flux-specific orchestration prompt
- Issue-to-epic lifecycle rules
- Workspace bootstrap behavior

### Exit Criteria

- A single orchestrated run can enter a workspace and complete a Flux-native workflow without bypassing `fluxctl`.

## Phase 8: Add Review, Handoff, and Landing Policy

### Goals

- Make the orchestrated workflow safe and auditable.

### Steps

1. Define handoff states, for example:
   - `Human Review`
   - `Rework`
   - `Merging`
   - `Done`
2. Map Flux review outcomes to tracker transitions.
3. Decide the minimum artifacts required before handoff:
   - tests
   - review verdict
   - commit hashes
   - summary
   - optional walkthrough
4. Decide whether v1 allows auto-land or always stops at human review.
5. Define rework loop behavior.
6. Define how failed reviews are surfaced to operators and back to the tracker.

### Deliverables

- Review-to-state transition matrix
- Handoff artifact requirements
- Landing policy

### Exit Criteria

- The orchestrator can move an issue into the correct next state with traceable evidence.

## Phase 9: Add Observability and Operator Controls

### Goals

- Make multi-run operation understandable without digging through raw logs.

### Steps

1. Add structured logs with issue id and session id correlation.
2. Add runtime snapshots for:
   - running sessions
   - retry queue
   - last poll results
   - recent errors
3. Add `status` output for local operators.
4. Add per-issue detail views in CLI or JSON.
5. Decide whether a lightweight web dashboard belongs in v1 or v1.5.
6. Add health reporting and last-success timestamps.

### Deliverables

- JSON status surface
- operator CLI status command
- structured log contract

### Exit Criteria

- An operator can answer "what is running, what is blocked, what failed, and why" without reading code.

## Phase 10: Add Reliability Controls

### Goals

- Make the daemon safe under tracker failures, app-server failures, and host restarts.

### Steps

1. Add exponential backoff for run failures.
2. Add short continuation retries after normal worker completion when issue state is still active.
3. Add stall detection for app-server inactivity.
4. Add shutdown recovery and state rehydration.
5. Add terminal issue cleanup on startup.
6. Add failure classification:
   - tracker error
   - workspace error
   - runner startup error
   - timeout
   - stall
   - unsupported tool request
   - approval or policy failure

### Deliverables

- Retry engine
- Failure taxonomy
- Recovery semantics

### Exit Criteria

- A single bad run does not wedge the whole daemon or cause silent duplicate execution.

## Phase 11: Add Security and Safety Guardrails

### Goals

- Keep the orchestration layer from becoming the weakest part of the system.

### Steps

1. Restrict app-server sessions to the issue workspace.
2. Validate workspace root containment on every launch.
3. Default to conservative approval and sandbox policies.
4. Limit tracker scope to a configured project or queue.
5. Avoid exposing raw tokens to the agent when possible.
6. Redact secrets from logs and receipts.
7. Define operator controls for pause, drain, and emergency stop.
8. Document trusted-environment assumptions explicitly.

### Deliverables

- Security model
- Logging redaction rules
- Operator stop controls

### Exit Criteria

- The orchestration layer has a documented trust model and defensible defaults.

## Phase 12: Add Test Coverage

### Goals

- Prove the orchestration layer works before exposing it to real issue queues.

### Test Categories

1. Unit tests
2. Contract tests for `WORKFLOW.md`
3. Linear adapter tests with fixtures
4. Workspace manager tests
5. State recovery tests
6. Retry scheduler tests
7. App-server protocol tests with mocks
8. End-to-end local tests with disposable workspaces
9. Controlled live tests against a disposable Linear project

### Critical Scenarios

- eligible issue dispatch
- terminal issue cleanup
- issue becomes ineligible while running
- daemon restart mid-run
- repeated tracker errors
- stall timeout and retry
- issue with missing epic state
- issue that requires plan then work
- review failure leading to rework
- handoff success with artifacts

### Deliverables

- Test matrix
- fixture library
- e2e harness

### Exit Criteria

- The team can run a repeatable local and CI validation flow before touching production tracker queues.

## Phase 13: Rollout Plan

### Stage 1: Internal Prototype

- Local daemon only
- One repo
- One Linear project
- One operator
- Run-once mode and basic status only

### Stage 2: Trusted Alpha

- Continuous polling
- Real app-server sessions
- Manual operator oversight
- Human review required before landing

### Stage 3: Production Beta

- Bounded concurrency
- recovery and retries enabled
- structured status surface
- documented on-call and operator playbook

### Stage 4: General Availability Candidate

- hardened docs
- richer status UX
- compatibility matrix
- migration guidance
- clear security posture

## 11) Detailed v1 Scope Recommendation

The initial release should be intentionally narrow.

### Include in v1

- Linear adapter
- root `WORKFLOW.md`
- local daemon
- deterministic local workspaces
- Codex app-server runner
- issue-to-epic mapping
- Flux-native plan/work/review execution
- structured logs
- CLI status
- retry and reconciliation basics
- human-review handoff state

### Exclude from v1

- SSH workers
- web dashboard
- multiple tracker adapters
- auto-merge to default branch
- cross-repo fleet management
- per-host scheduling
- advanced tenancy or access control

## 12) Open Design Questions

These questions should be resolved before implementation begins.

1. Should `WORKFLOW.md` live at repo root or under `.flux/`?
2. Should one Linear issue always map to one Flux epic, or should small-ticket mode exist in v1?
3. Should the orchestrator initialize `.flux/` automatically if absent?
4. Should planning always run before work, or can a workflow opt into "direct work" for small issues?
5. Should tracker writes happen only through app-server tools, or should the daemon support a small set of direct writes for safety-critical transitions?
6. Should successful runs stop at `Human Review` in v1, even if auto-land is technically possible?
7. Should orchestrator runtime state live only in `.git/flow-state`, or also support a user-global cache?
8. Should the first release support only Codex app-server, or define a more generic runner interface from day one?

## 13) Risks and Mitigations

### Risk: Dual sources of truth

- Problem: Linear, `.flux/`, and runtime state can drift.
- Mitigation: define explicit ownership boundaries and reconciliation rules up front.

### Risk: Prompt policy drift

- Problem: `WORKFLOW.md` and Flux skills may conflict.
- Mitigation: keep `WORKFLOW.md` orchestration-focused and delegate repo workflow behavior to Flux skills and `fluxctl`.

### Risk: Orchestrator bypasses Flux

- Problem: direct code-generation prompts could skip review gates and task state.
- Mitigation: require Flux-native bootstrap and `fluxctl` writes inside every issue workspace.

### Risk: Runtime complexity explodes

- Problem: retries, status, shutdown, and reconciliation become a second product.
- Mitigation: keep v1 narrow and local-first.

### Risk: Install friction increases sharply

- Problem: new daemon/runtime dependencies reduce adoption.
- Mitigation: implement in Python inside the current repository ecosystem and keep external dependencies minimal.

### Risk: Unsafe autonomy

- Problem: tracker-driven execution increases blast radius.
- Mitigation: start with trusted environments, conservative sandbox defaults, and human-review handoff.

## 14) Milestone Breakdown

### Milestone A: Specs and Contracts

- orchestration requirements
- orchestration technical spec
- workflow contract schema

### Milestone B: Runtime Foundation

- daemon bootstrap
- config loader
- state store
- status surface

### Milestone C: Tracker + Workspace

- Linear adapter
- workspace manager
- claim/reconciliation logic

### Milestone D: Runner + Flux Integration

- Codex app-server runner
- Flux bootstrap prompt
- issue-to-epic mapping
- review and handoff policy

### Milestone E: Reliability + Rollout

- retries
- recovery
- operator docs
- test harness
- alpha rollout

## 15) Definition of Done for the Integration

The Relay orchestration layer should be considered complete for v1 only when all of the following are true:

- A repo can define orchestration policy in `WORKFLOW.md`.
- The daemon can discover eligible Linear issues.
- The daemon can create and reuse deterministic workspaces safely.
- The daemon can launch Codex app-server sessions inside those workspaces.
- The session can execute Flux-native planning, work, and review flows.
- `fluxctl` remains the only write path for Flux task and epic state.
- The daemon can stop, retry, and recover runs deterministically.
- Operators can inspect runtime status without reading raw implementation logs.
- The system defaults to a human-review handoff state rather than silent autonomous landing.
- There is a repeatable local and CI test story.

## 16) Recommended Immediate Next Steps

If implementation starts, the first actions should be:

1. Write `docs/orchestration-requirements.md`.
2. Write `docs/orchestration-spec.md`.
3. Draft the first `WORKFLOW.md` schema and example.
4. Decide the issue-to-epic mapping formally.
5. Build a run-once daemon skeleton before any real tracker or app-server integration.

That sequence keeps the design disciplined and reduces the chance of building a scheduler that conflicts with Flux's existing workflow model.
