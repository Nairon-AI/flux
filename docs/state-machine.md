# Flux Workflow State Machine

Formal definition of all workflow states, transitions, and routing rules. This is the single source of truth for where a user or agent is in the Flux workflow at any point.

This document mirrors and formalizes the architecture diagram in [README.md](../README.md#architecture). Every node, edge, subgraph, and conditional in that diagram has a corresponding state or transition here.

---

## Session States

Every Flux session begins with a state check (`fluxctl session-state --json`). The state determines which skill activates next.

| State | Description | Valid Transitions | Corresponds to (README) |
|-------|-------------|-------------------|------------------------|
| `session_start` | Startup hook fires. Injects brain vault index + workflow state into context. | `recommendation_pulse` | Session Start |
| `recommendation_pulse` | Daily check: new tools available? Brain vault health OK? Rate-limited 1x/day. | `needs_prime`, `fresh_session_no_objective`, `resume_scope`, `resume_work`, `idle_with_open_epics` | Recommendation Pulse |
| `needs_prime` | First run or stale setup. No `.flux/` or outdated setup version. | `prime` → `needs_ruminate` or `fresh_session` | Prime |
| `needs_ruminate` | Brain is thin (<5 files) and past sessions exist. Offered after prime via AskUserQuestion. | `ruminate` → `fresh_session`, or skip → `fresh_session` | Ruminate |
| `fresh_session_no_objective` | Primed, no active work. Ready for new work. | `scope`, `plan`, `propose`, `rca`, `improve`, `remember` | Scope / Propose / RCA |
| `resume_scope` | Scope was interrupted mid-session. | `scope` (resume from last step) | Scope |
| `scoping` | Actively in the scoping interview (Steps 1-6). | `stress_test`, `plan_creation`, `propose`, `rca` | Scope |
| `stress_testing` | Dialectic subagents spawned, arguing opposing positions. | `execution_choice` | Stress Test |
| `execution_choice` | User chooses: task-by-task (interactive) or Ralph mode (autonomous). | `ready_for_work`, `ralph_mode` | Execute how? |
| `plan_creation` | Creating epic + tasks via `/flux:plan`. | `needs_plan_review`, `ready_for_work` | Scope → Plan |
| `needs_plan_review` | Epic spec exists but hasn't been reviewed. | `plan_review` → `ready_for_work` | Plan Review |
| `ready_for_work` | Plan reviewed (or review not required). Tasks exist. | `in_progress` | Work |
| `ralph_mode` | Autonomous execution — runs all tasks + reviews unattended. | `epic_review` | Ralph |
| `in_progress` | Tasks are actively being worked on (task loop). | `impl_review`, `friction_check`, `next_task`, `needs_completion_review` | Work (task loop) |
| `impl_review` | Per-task lightweight review after worker completes. | `in_progress` (NEEDS_WORK), `friction_check` (SHIP) | Impl Review |
| `friction_check` | After SHIP — check for friction signals (build errors, lint failures, API hallucinations). | `inline_improve`, `feel_check` | Friction Check |
| `inline_improve` | Inline tool recommendation offered (install / skip / dismiss). | `feel_check` | Inline Recommend |
| `feel_check` | Human gut check — does it work? Does it feel right? | `adapt_plan` | Feel Check |
| `adapt_plan` | User decides: continue, update tasks, add task, remove task. | `plan_sync`, `in_progress` (next task) | Adapt Plan |
| `plan_sync` | Update downstream todo tasks based on implementation drift. | `in_progress` (next task) | Plan Sync |
| `needs_completion_review` | All tasks done. Epic review required. | `epic_review` | Epic Review |
| `epic_review` | Full review pipeline running. | `quality` (SHIP), `in_progress` (NEEDS_WORK fix loop) | Epic Review Pipeline |
| `quality` | Tests, repo-defined lint/format gates (for example `lintcn`), desloppify scan on changed files. | `submit` | Quality |
| `grill` | Behavioral stress test — walks decision tree verifying behavior matches intent. | `quality`, `in_progress` (if gaps found) | Grill |
| `submit` | Push + open PR. Code ready for review/merge. | `autofix`, `reflect` | Submit |
| `autofix` | Cloud auto-fix enabled on PR — Claude watches for CI failures and review comments remotely. Non-blocking. | `reflect` | Autofix |
| `reflect` | Capture session learnings to brain vault, extract skills. | `meditate`, `done` | Reflect |
| `meditate` | Prune stale brain notes, promote pitfalls to principles. | `done` | Meditate |
| `done` | Epic complete, all reviews passed, learnings captured. | `fresh_session_no_objective` | Done |
| `idle_with_open_epics` | Some epics open but no active task. | `in_progress` (next epic), `reflect` | — |
| `gate` | Staging validation after merge — browser QA against staging URL, then promotion PR. | `done` | Gate |

---

## Runtime Phase Tracking

The state machine is not just documentation — session phase is **persisted at runtime** via `fluxctl session-phase`. Every skill sets its phase on entry and resets to `idle` on completion.

### Commands

```bash
# Query current phase
$FLUXCTL session-phase get --json
# → {"phase": "work", "detail": null, "epic_id": "fn-1-add-auth", "task_id": "fn-1-add-auth.2", "updated_at": "..."}

# Set phase (skills do this automatically)
$FLUXCTL session-phase set work --epic-id fn-1-add-auth --task-id fn-1-add-auth.2
$FLUXCTL session-phase set idle
```

### Storage

Phase is stored in `{state-dir}/session_phase.json` (shared across worktrees). The `session-state --json` output includes `session_phase` alongside the coarse routing state.

Workflow-embedded utility skills such as `flux-parallel-dispatch`, `flux-receive-review`, and `flux-verify-claims` intentionally do **not** set their own session phases. They run inside an already-active parent phase such as `scope`, `work`, `impl_review`, `epic_review`, or `autofix`.

### Valid Phases

`setup`, `idle`, `prime`, `ruminate`, `scope`, `stress_test`, `plan`, `plan_review`, `work`, `impl_review`, `epic_review`, `grill`, `desloppify`, `quality`, `submit`, `autofix`, `reflect`, `meditate`, `gate`, `propose`, `rca`, `improve`, `remember`, `export_context`, `dejank`, `tdd`, `design_interface`, `ubiquitous_language`, `sync`, `security_scan`, `security_review`, `threat_model`, `vuln_validate`, `skill_build`, `profile`, `ralph`, `contribute`, `upgrade`, `release`, `improve-claude-md`

### Skill → Phase Mapping

| Skill | Phase set on entry |
|-------|--------------------|
| `/flux:setup` | `setup` |
| `/flux:prime` | `prime` |
| `/flux:ruminate` | `ruminate` |
| `/flux:scope` | `scope` |
| `/flux:plan` | `plan` |
| `/flux:plan-review` | `plan_review` |
| `/flux:work` | `work` |
| `/flux:impl-review` | `impl_review` |
| `/flux:epic-review` | `epic_review` |
| `/flux:reflect` | `reflect` |
| `/flux:meditate` | `meditate` |
| `/flux:autofix` | `autofix` |
| `/flux:export-context` | `export_context` |
| `/flux:gate` | `gate` |
| `/flux:propose` | `propose` |
| `/flux:rca` | `rca` |
| `/flux:improve` | `improve` |
| `/flux:remember` | `remember` |
| `/flux:dejank` | `dejank` |
| `/flux:grill` | `grill` |
| `/flux:desloppify` | `desloppify` |
| `/flux:tdd` | `tdd` |
| `/flux:design-interface` | `design_interface` |
| `/flux:ubiquitous-language` | `ubiquitous_language` |
| `/flux:sync` | `sync` |
| `/flux:security-scan` | `security_scan` |
| `/flux:security-review` | `security_review` |
| `/flux:threat-model` | `threat_model` |
| `/flux:vuln-validate` | `vuln_validate` |
| `/flux:skill-builder` | `skill_build` |
| `/flux:profile` | `profile` |
| `/flux:ralph-init` | `ralph` |
| `/flux:contribute` | `contribute` |
| `/flux:upgrade` | `upgrade` |
| `/flux:release` | `release` |
| `/flux:improve-claude-md` | `improve-claude-md` |

---

## Transition Diagram

This mirrors the README mermaid diagram exactly, adding state names for every node.

```
SESSION START (session_start)
  │
  ▼
RECOMMENDATION PULSE (recommendation_pulse)
  │ ─── new tools? nudge /flux:improve ─── ▶ [Improve offered]
  │
  ▼
[session-state check]
  │
  ├─ needs_prime ─────────────────────────▶ /flux:prime
  │                                            │
  │                                            ▼
  │                                    [brain thin + past sessions?]
  │                                      │ yes              │ no
  │                                      ▼                  │
  │                              ASK: ruminate?             │
  │                               │ yes     │ no            │
  │                               ▼         │               │
  │                          /flux:ruminate  │               │
  │                               │         │               │
  │                               ▼         ▼               ▼
  │                          fresh_session_no_objective
  │
  ├─ fresh_session_no_objective ──────────▶ DETECT INPUT TYPE
  │                                            │
  │                  ┌─────────────────────────┤
  │                  │                         │
  │           [stakeholder?]            [bug signals?]
  │             │ yes                      │ yes
  │             ▼                          ▼
  │        /flux:propose             ASK: RCA?
  │             │                      │ yes    │ no
  │             ▼                      ▼        │
  │        Proposal Created       /flux:rca     │
  │                                    │        │
  │                                    ▼        │
  │                               submit ───────│───▶ [Submit → Reflect → Done]
  │                                             │
  │                  ┌──────────────────────────┘
  │                  ▼
  │             /flux:scope (scoping)
  │                  │
  │                  ▼
  │           [viability gate — 2+ red flags?]
  │             │ pass (0-1 red flags)
  │             ▼
  │           [stress test signals?]
  │             │ yes (one-way door /           │ no tensions
  │             │  UX assumption /              │
  │             │  deferred authority)           │
  │             ▼                               │
  │        Spawn Opposing Subagents             │
  │        (stress_testing)                     │
  │             │ synthesize + user decides      │
  │             ▼                               ▼
  │           EXECUTION CHOICE (execution_choice)
  │             │                          │
  │             │ task-by-task             │ ralph mode
  │             │ (interactive)            │ (autonomous)
  │             ▼                          ▼
  │        plan_creation              ralph_mode
  │             │                          │
  │             ▼                          │
  │        [plan review required?]         │
  │          │ yes          │ no           │
  │          ▼              │              │
  │     /flux:plan-review   │              │
  │          │ SHIP         │              │
  │          ▼              ▼              │
  │        ready_for_work                  │
  │             │                          │
  │             ▼                          │
  ├─ resume_work ──▶ /flux:work            │
  │             │                          │
  │   ┌────────┤  TASK LOOP (per task)     │
  │   │        ▼                           │
  │   │  [find ready task]                 │
  │   │        │                           │
  │   │        ▼                           │
  │   │  start task (in_progress)          │
  │   │  → sync Linear "in progress"       │
  │   │        │                           │
  │   │        ▼                           │
  │   │  spawn worker subagent             │
  │   │        │                           │
  │   │        ▼                           │
  │   │  verify done                       │
  │   │  → sync Linear "done"             │
  │   │        │                           │
  │   │        ▼                           │
  │   │  /flux:impl-review (impl_review)   │
  │   │    │ NEEDS_WORK → back to worker   │
  │   │    │ SHIP ↓                        │
  │   │        ▼                           │
  │   │  FRICTION CHECK (friction_check)   │
  │   │    │ friction detected?            │
  │   │    │ yes → INLINE IMPROVE          │
  │   │    │        (install/skip/dismiss)  │
  │   │    │ no ↓                          │
  │   │        ▼                           │
  │   │  FEEL CHECK (feel_check)           │
  │   │  → human gut check                │
  │   │        │                           │
  │   │        ▼                           │
  │   │  ADAPT PLAN (adapt_plan)           │
  │   │  → continue / update / add / skip  │
  │   │        │                           │
  │   │        ▼                           │
  │   │  PLAN SYNC (plan_sync)             │
  │   │  → update downstream todo tasks    │
  │   │        │                           │
  │   │        ▼                           │
  │   │  [more tasks?]                     │
  │   │    │ yes                           │
  │   └────┘                               │
  │        │ no                            │
  │        ▼                               │
  │  needs_completion_review ◄─────────────┘
  │        │                    (ralph also arrives here)
  │        ▼
  │  EPIC REVIEW PIPELINE (epic_review)
  │  ┌──────────────────────────────────────┐
  │  │ 1. Spec Compliance                   │
  │  │ 2. Adversarial Review (Claude+OpenAI)│
  │  │ 3. STRIDE Security Scan              │
  │  │ 4. BYORB Self-Heal (optional)        │
  │  │ 5. Browser QA                        │
  │  │ 6. Learning Capture → write brain    │
  │  │ 7. Desloppify Scan                   │
  │  │ 8. Frustration Signal (score >= 3?)  │
  │  │    │ yes → auto-fetch recommendations│
  │  │    │ no  → continue                  │
  │  └──────────────────────────────────────┘
  │        │ SHIP
  │        │ (NEEDS_WORK → fix loop back to work)
  │        ▼
  │  ASK: Grill behavior? (offer /flux:grill)
  │    │ yes                    │ no
  │    ▼                        │
  │  GRILL (grill)              │
  │  → walk decision tree       │
  │  → verify edge cases        │
  │  → gaps? → create fix tasks │
  │    │ all verified            │
  │    ▼                        ▼
  │  QUALITY (quality)
  │  → tests, repo-defined lint/format gates, desloppify scan
  │        │
  │        ▼
  │  SUBMIT (submit)
  │  → push + open PR
  │        │
  │        ▼
  │  [post-submit routing]
  │    │                        │                       │
  │    │ autofix.enabled        │ !autofix +            │ neither
  │    │                        │ review.bot set        │
  │    ▼                        ▼                       │
  │  AUTOFIX (autofix)     BYORB (within submit)        │
  │  → cloud, handles all  → bot comments only         │
  │  → non-blocking        → max 2 iterations          │
  │    │                        │                       │
  │    ▼                        ▼                       ▼
  │  REFLECT (reflect)
  │  → capture learnings, extract skills
  │  → write brain (learnings + skills)
  │        │
  │        ├─ [pitfalls >= 20?] ──── yes ──▶ MEDITATE (meditate)
  │        │                                     │ prune/promote brain
  │        │                                     ▼
  │        └─ [brain healthy] ──────────────▶ DONE (done)
  │
  │  [After merge, optional:]
  │  GATE (gate)
  │  → verify staging deployment
  │  → browser QA against staging URL
  │  → create promotion PR (staging → production)
  │
  └─ resume_scope ──▶ /flux:scope (resume from last step)
```

---

## Brain Vault Interactions

The brain vault is stored in `.flux/brain/`. This maps every interaction:

| Phase | Direction | What |
|-------|-----------|------|
| **Scope** | READ | `.flux/brain/principles.md` + relevant principle files, `.flux/brain/pitfalls/<relevant-area>/`, `.flux/brain/business/context.md`, `.flux/brain/business/glossary.md`, `.flux/brain/codebase/architecture.md` |
| **Work** (per task) | READ | Re-anchor: `.flux/brain/pitfalls/<relevant-area>/`, `.flux/brain/principles.md`, `.flux/brain/codebase/architecture.md` |
| **Learning Capture** (during epic review) | WRITE | `.flux/brain/pitfalls/<area>/<new-pitfall>.md` |
| **Architecture Diagram** | READ+WRITE | `.flux/brain/codebase/architecture.md` — canonical whole-product diagram kept in sync during prime/work/review |
| **Reflect** | WRITE | `.flux/brain/` (learnings), project-local `.secureskills/` for secure extracted skills when available, with legacy `.codex/skills/` / `.claude/skills/` fallback |
| **Ruminate** | WRITE | `.flux/brain/` (mined patterns from past conversations) |
| **Meditate** | READ+WRITE | Prune stale notes, promote recurring pitfalls to principles |
| **Remember** (flux-brain) | WRITE | `.flux/brain/<category>/` or `CLAUDE.md` based on content analysis |
| **Propose** | READ+WRITE | Read `.flux/brain/business/`, write back new glossary terms and area context |
| **Ubiquitous Language** | READ+WRITE | Read `.flux/brain/business/glossary.md`, write canonical glossary with flagged ambiguities |
| **Grill** | READ+WRITE | Read epic spec + task specs + brain vault decisions; write resolved ambiguities and new fix tasks |

---

## Skill Routing Rules

### Primary Detection (from natural language input)

The following routing happens when a user provides natural language instead of an explicit `/flux:*` command:

| Signal | Route To | Priority |
|--------|----------|----------|
| Stakeholder language (outcomes, no implementation detail) | `/flux:propose` | 1 |
| React visual-jank signals ("flicker", "flash", "blink", "layout shift", "jank", "scroll reset", "feels rebuilt") and `dejank` is installed | `/flux:dejank` | 2 |
| Codebase-understanding signals ("how does X work", "walk me through Y", "help me understand Z", "show me what touches X") and `diffity-tour` is installed | `/diffity-tour` | 3 |
| Bug signals (error messages, "broken", stack traces) | `/flux:rca` (after confirmation) | 4 |
| "remember X" / "don't forget X" / "keep in mind X" / "from now on X" | `/flux:remember` | 5 |
| Feature/refactor description | `/flux:scope` | 6 |
| Flow ID pattern (`fn-N-slug` or `fn-N`) | `/flux:work` (epic) | 7 |
| Flow task ID pattern (`fn-N-slug.M` or `fn-N.M`) | `/flux:work` (single task) | 7 |
| "improve X" / "help me find tools for X" / "optimize my workflow for X" | `/flux:improve` (with context) | 8 |
| "what's the status" / "show me my tasks" / "list epics" | `/flux` (task management) | 9 |
| "review this" / "check my code" | `/flux:impl-review` | 10 |
| "grill me" / "stress test the behavior" / "verify behavior" | `/flux:grill` | 11 |
| "TDD" / "test first" / "red green refactor" | `/flux:tdd` | 12 |
| "design the interface" / "design it twice" / "compare interfaces" | `/flux:design-interface` | 13 |
| "ubiquitous language" / "define terms" / "domain glossary" / "DDD" | `/flux:ubiquitous-language` | 14 |
| "export this for ChatGPT/Claude web" / "external LLM review" / "review with ChatGPT" | `/flux:export-context` | 15 |
| "watch this PR" / "auto-fix" / "babysit" / "fix CI" | `/flux:autofix` | 16 |
| "reflect" / "what did we learn" | `/flux:reflect` | 17 |
| "validate staging" / "promote staging" / "ship staging to production" | `/flux:gate` | 18 |
| "cut a release" / "publish Flux vX.Y.Z" / "release this version" | `/flux:release` | 19 |
| "improve CLAUDE.md" / "restructure AGENTS.md" / "add important if blocks" | `/flux:improve-claude-md` | 20 |
| "export my setup" / "share this Flux profile" / "import a profile" | `/flux:profile` | 21 |
| "build me a skill" / "create a skill for X" | `/flux:skill-builder` | 22 |
| "upgrade Flux" / "update the plugin" | `/flux:upgrade` | 23 |
| "report a Flux bug" / "contribute a fix" | `/flux:contribute` | 24 |

### Intra-Skill Routing

Skills can route to other skills during execution:

| From | Condition | Routes To |
|------|-----------|-----------|
| `/flux:scope` | Stakeholder detected (3+ signals, 0 engineer signals) | `/flux:propose` |
| `/flux:scope` | React visual-jank signals + `dejank` installed + user confirms | `/flux:dejank` |
| `/flux:scope` | User is trying to understand an existing feature/codepath + `diffity-tour` installed + no change request yet | `/diffity-tour` |
| `/flux:scope` | Bug signals detected + user confirms | `/flux:rca` |
| `/flux:scope` | "remember X" detected | `/flux:remember` |
| `/flux:scope` | `--explore` flag | Explore mode (internal) |
| `/flux:scope` | Stress test signals detected | Dialectic subagents (internal) |
| `/flux:scope` | Scoping complete → user chooses execution mode | `/flux:work` (interactive) or Ralph mode |
| `/flux:prime` | Brain thin + past sessions + user confirms | `/flux:ruminate` |
| `/flux:work` | Task SHIP + friction detected | Inline improve (internal) |
| `/flux:work` | All tasks done | `/flux:epic-review` |
| `/flux:work` | Task complete + plan sync enabled | `flux:plan-sync` (subagent) |
| `/flux:epic-review` | Frustration score >= 3 | Auto-fetch recommendations |
| `/flux:epic-review` | NEEDS_WORK verdict | Fix loop → re-review |
| `/flux:epic-review` | SHIP → Quality → Submit | `/flux:reflect` (auto) |
| `/flux:work` | PR submitted + `autofix.enabled: true` | `/flux:autofix` (automatic, non-blocking, then reflect) |
| `/flux:reflect` | Pitfalls >= 20 | `/flux:meditate` (auto) |
| `/flux:epic-review` | SHIP verdict + user accepts grill offer | `/flux:grill` (user choice) |
| `/flux:grill` | Gaps found requiring new tasks | `in_progress` (fix tasks) |
| `/flux:grill` | All behaviors verified | `quality` |
| `/flux:work` | Worker spawn + TDD requested or `--tdd` flag | `/flux:tdd` (replaces standard worker) |
| `/flux:scope` | Solution phase + complex interface design needed | `/flux:design-interface` (user choice) |
| `/flux:scope` | Problem phase complete + domain terms ambiguous | `/flux:ubiquitous-language` (user choice) |
| `/flux:propose` | Domain terms ambiguous during interview | `/flux:ubiquitous-language` (user choice) |
| Recommendation pulse | New tools detected (1x/day) | Nudge `/flux:improve` |

### State Guards

These prevent invalid transitions:

| Guard | Blocks | Requires |
|-------|--------|----------|
| Prime not done | All skills except `prime`, `setup`, `status`, `upgrade` | Run `/flux:prime` first |
| No active epic | `/flux:work` without ID | Provide epic/task ID or run `/flux:scope` |
| Tasks not created | `/flux:work <epic>` | Epic must have tasks |
| Dependencies not met | `fluxctl start <task>` | All dependency tasks must be `done` |
| Review not passed | Epic close | `completion_review_status == ship` |
| Quality not passed | Submit | Tests pass, repo lint/format gates pass |

---

## Task Lifecycle

Individual tasks follow this state machine:

```
         ┌──────────────────┐
         ▼                  │
       todo ──▶ in_progress ──▶ done
                  │
                  ▼
               blocked (with reason)
                  │
                  ▼
               todo (after unblock)
```

| Command | Transition |
|---------|-----------|
| `fluxctl start <task>` | `todo` → `in_progress` |
| `fluxctl done <task>` | `in_progress` → `done` |
| `fluxctl block <task>` | `in_progress` → `blocked` |
| `fluxctl reset <task>` | any → `todo` |
| `fluxctl skip <task>` | any → `skipped` |

---

## Epic Lifecycle

```
       created ──▶ in_progress ──▶ review ──▶ quality ──▶ submit ──▶ done
                                     │
                                     ▼
                                 needs_work (fix loop)
                                     │
                                     ▼
                                   review (re-review)
```

### Review Statuses

Each epic tracks two independent review statuses:

| Status | Values | Set By |
|--------|--------|--------|
| `plan_review_status` | `unknown`, `ship`, `needs_work` | `/flux:plan-review` |
| `completion_review_status` | `unknown`, `ship`, `needs_work` | Caller after `/flux:epic-review` returns SHIP |

### Epic Review Pipeline (sub-states)

When `epic_review` is active, the review pipeline executes these steps in order:

| Step | Name | Purpose |
|------|------|---------|
| 1 | Spec Compliance | Verify implementation matches epic spec |
| 2 | Adversarial Review | Dual-model review (cross-lab or same-provider) |
| 3 | STRIDE Security Scan | Threat model analysis of changes |
| 4 | BYORB Self-Heal | External bot review (Greptile/CodeRabbit) — **optional**, skipped if no bot configured |
| 5 | Browser QA | Visual verification of UI changes — skipped if pure backend |
| 6 | Learning Capture | Write pitfalls to `.flux/brain/pitfalls/<area>/` |
| 7 | Desloppify Scan | Dead code, duplication, complexity check |
| 8 | Frustration Signal | If friction score >= 3, auto-fetch and offer tool recommendations |

---

## Linear Sync States

When Linear integration is active, Flux maps its lifecycle to Linear's custom workflow states:

| Flux Event | Linear State Match Strategy |
|---|---|
| Task started (`fluxctl start`) | State containing "progress" (fallback: "started", "active") |
| Task done (`fluxctl done`) | State containing "done" or "complete" (fallback: "closed") |
| Task blocked (`fluxctl block`) | State containing "block" (fallback: skip sync) |
| Epic work begins | Project status → "started" |

Override with `.flux/config.json`:
```json
{
  "linear": {
    "statusMap": {
      "in_progress": "In Development",
      "done": "Ready for QA",
      "blocked": "Blocked"
    }
  }
}
```

---

## Automatic vs Manual Transitions

| Transition | Trigger | Type |
|-----------|---------|------|
| Session start hook | Every session | **Automatic** — injects brain vault index + workflow state |
| Recommendation pulse | Every session (rate-limited 1x/day) | **Automatic** — nudges for new tools, brain vault health |
| `session-state` routing | Before any work-like request | **Automatic** — routes to prime/scope/work/review |
| Stress test | During scope, if one-way door / UX assumption / deferred authority | **Automatic** — spawns opposing subagents |
| Parallel dispatch utility | During Prime scouts or Scope explore fan-out | **Automatic within owning phase** — uses `flux-parallel-dispatch` to keep parallel work isolated |
| Friction check + inline improve | After each task SHIP | **Automatic** — checks for recurring friction signals |
| Verify claims utility | Before claiming fixed/green/done or advancing to SHIP | **Automatic within owning phase** — uses `flux-verify-claims` inside work/review/autofix |
| Receive review utility | When reviewer or bot comments need interpretation | **Automatic within owning phase** — uses `flux-receive-review` inside impl-review/epic-review/autofix |
| Plan sync | After task done, if enabled | **Automatic** — updates downstream todo tasks |
| Epic review pipeline | All tasks done | **Automatic** — full pipeline runs in order |
| Reflect | After submit | **Automatic** — captures learnings while context is fresh |
| Meditate | After reflect, if 20+ pitfall files | **Automatic** — prunes stale, promotes patterns |
| Ruminate | After prime, if brain thin + past sessions | **Automatic** (with user confirmation) |
| Improve recommendations | During epic review, if friction score >= 3 | **Automatic** — fetches and matches recommendations |
| Setup | First install; re-run after upgrades | **Manual** — Flux nudges if setup version is stale |
| Prime | First session per project | **Manual** — but `session-state` blocks until done |
| Scope | Start new work | **Manual** |
| Work | Execute tasks | **Manual** |
| Ralph | Autonomous execution | **Manual** — offered after scoping |
| Autofix | After PR submit, if `autofix.enabled: true` | **Automatic** (config-driven, non-blocking) |
| Gate | Validate staging after merge | **Manual** (or CI auto) |
| Upgrade | Get latest Flux version | **Manual** |

---

## Querying Current State

Users and agents can check the current state at any time:

```bash
# Full state check — returns current state + recommended next action
$FLUXCTL session-state --json

# Active epics
$FLUXCTL epics --json

# Active tasks for an epic
$FLUXCTL tasks --epic <id> --json

# Next ready task (all deps satisfied)
$FLUXCTL ready --epic <id> --json

# Task details
$FLUXCTL show <task-id> --json

# Epic details including review statuses
$FLUXCTL show <epic-id> --json

# Validate epic completeness
$FLUXCTL validate --epic <id> --json
```

---

## Philosophy

The state machine is **deterministic by design**. Given the same `.flux/` state, any agent should route to the same skill. This prevents:

- **Ghost states**: work happening outside `.flux/` that the system doesn't know about
- **Skill conflicts**: two skills activating simultaneously for the same input
- **Lost progress**: session breaks losing track of where the user was
- **Wrong routing**: a "remember" request going to scope instead of brain
- **Skipped phases**: jumping from work to done without quality/submit/reflect

Every state transition is recorded in `.flux/` as JSON. The state machine is inspectable, resumable, and portable across sessions.
