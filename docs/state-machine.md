# Flux Workflow State Machine

Formal definition of all workflow states, transitions, and routing rules. This is the single source of truth for where a user or agent is in the Flux workflow at any point.

---

## States

Every Flux session begins with a state check (`fluxctl session-state --json`). The state determines which skill activates next.

| State | Description | Valid Transitions |
|-------|-------------|-------------------|
| `needs_prime` | First run or stale setup. No `.flux/` or outdated setup version. | `prime` |
| `needs_ruminate` | Brain is thin (<5 files) and past sessions exist. Offered after prime. | `ruminate` → `fresh_session` |
| `fresh_session_no_objective` | Primed, no active work. Ready for new work. | `scope`, `plan`, `propose`, `rca`, `improve` |
| `resume_scope` | Scope was interrupted mid-session. | `scope` (resume) |
| `resume_work` | Work was interrupted mid-session. | `work` (resume) |
| `needs_plan_review` | Epic spec exists but hasn't been reviewed. | `plan_review` → `work` |
| `ready_for_work` | Plan reviewed (or review not required). Tasks exist. | `work` |
| `in_progress` | Tasks are actively being worked on. | `work` (continue), `impl_review` |
| `needs_completion_review` | All tasks done. Epic review required. | `epic_review` → `done` |
| `idle_with_open_epics` | Some epics open but no active task. | `work` (next epic), `reflect` |
| `done` | Epic complete, all reviews passed. | `reflect`, `meditate`, `fresh_session` |

---

## Transition Diagram

```
SESSION START
  │
  ▼
[session-state check]
  │
  ├─ needs_prime ─────────────────────────▶ /flux:prime
  │                                            │
  │                                            ▼
  │                                    [brain thin + sessions?]
  │                                      │ yes         │ no
  │                                      ▼             │
  │                              ASK: ruminate?        │
  │                               │ yes    │ no        │
  │                               ▼        │           │
  │                          /flux:ruminate │           │
  │                               │        │           │
  │                               ▼        ▼           ▼
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
  │                                    │ yes    │ no
  │                                    ▼        │
  │                               /flux:rca     │
  │                                             │
  │                  ┌──────────────────────────┘
  │                  ▼
  │             /flux:scope
  │                  │
  │                  ▼
  │           [viability gate]
  │             │ pass
  │             ▼
  │           [stress test?]
  │             │ done
  │             ▼
  │           /flux:plan (create epic + tasks)
  │                  │
  │                  ▼
  │           [plan review required?]
  │             │ yes              │ no
  │             ▼                  │
  │        /flux:plan-review       │
  │             │ SHIP             │
  │             ▼                  ▼
  │           ready_for_work
  │                  │
  │                  ▼
  ├─ resume_work ──▶ /flux:work
  │                  │
  │                  ├──────────── per task loop ────────────┐
  │                  │                                       │
  │                  ▼                                       │
  │            [find ready task]                             │
  │                  │                                       │
  │                  ▼                                       │
  │            start task → sync Linear "in progress"        │
  │                  │                                       │
  │                  ▼                                       │
  │            spawn worker subagent                         │
  │                  │                                       │
  │                  ▼                                       │
  │            verify done → sync Linear "done"              │
  │                  │                                       │
  │                  ▼                                       │
  │            [impl review] (lightweight per-task)          │
  │                  │                                       │
  │                  ▼                                       │
  │            feel check (human)                            │
  │                  │                                       │
  │                  ▼                                       │
  │            adapt plan?                                   │
  │                  │                                       │
  │                  ▼                                       │
  │            plan-sync (if enabled)                        │
  │                  │                                       │
  │                  ▼                                       │
  │            [more tasks?] ─── yes ────────────────────────┘
  │                  │ no
  │                  ▼
  │           needs_completion_review
  │                  │
  │                  ▼
  │           /flux:epic-review
  │             │ SHIP
  │             ▼
  │            done
  │                  │
  │                  ▼
  │           /flux:reflect (capture learnings)
  │                  │
  │                  ▼
  │           [pitfalls >= 20?]
  │             │ yes
  │             ▼
  │           /flux:meditate (prune brain)
  │
  └─ resume_scope ─▶ /flux:scope (resume from last step)
```

---

## Skill Routing Rules

### Primary Detection (from natural language input)

The following routing happens when a user provides natural language instead of an explicit `/flux:*` command:

| Signal | Route To | Priority |
|--------|----------|----------|
| Stakeholder language (outcomes, no implementation detail) | `/flux:propose` | 1 |
| Bug signals (error messages, "broken", stack traces) | `/flux:rca` (after confirmation) | 2 |
| Feature/refactor description | `/flux:scope` | 3 |
| Flow ID pattern (`fn-N-slug` or `fn-N`) | `/flux:work` (epic) or `/flux:work` (task) | 4 |
| Flow task ID pattern (`fn-N-slug.M` or `fn-N.M`) | `/flux:work` (single task) | 4 |
| "remember X" / "don't forget X" / "keep in mind X" | `/flux:brain` ("Remember" flow) | 5 |
| "improve X" / "help me find tools for X" / "optimize my workflow for X" | `/flux:improve` (with context) | 6 |
| "what's the status" / "show me my tasks" / "list epics" | `/flux` (task management) | 7 |
| "review this" / "check my code" | `/flux:impl-review` | 8 |
| "reflect" / "what did we learn" | `/flux:reflect` | 9 |

### Intra-Skill Routing

Skills can route to other skills during execution:

| From | Condition | Routes To |
|------|-----------|-----------|
| `/flux:scope` | Stakeholder detected (3+ signals, 0 engineer signals) | `/flux:propose` |
| `/flux:scope` | Bug signals detected + user confirms | `/flux:rca` |
| `/flux:scope` | `--explore` flag | Explore mode (internal) |
| `/flux:scope` | Stress test signals detected | Dialectic subagents (internal) |
| `/flux:scope` | Scoping complete | `/flux:work` (via user) or Ralph mode |
| `/flux:prime` | Brain thin + past sessions + user confirms | `/flux:ruminate` |
| `/flux:work` | All tasks done | `/flux:epic-review` |
| `/flux:work` | Task complete + plan sync enabled | `flux:plan-sync` (subagent) |
| `/flux:reflect` | Pitfalls >= 20 | `/flux:meditate` (auto) |
| `/flux:epic-review` | NEEDS_WORK verdict | Fix loop → re-review |

### State Guards

These prevent invalid transitions:

| Guard | Blocks | Requires |
|-------|--------|----------|
| Prime not done | All skills except `prime`, `setup`, `status` | Run `/flux:prime` first |
| No active epic | `/flux:work` without ID | Provide epic/task ID or run `/flux:scope` |
| Tasks not created | `/flux:work <epic>` | Epic must have tasks |
| Dependencies not met | `fluxctl start <task>` | All dependency tasks must be `done` |
| Review not passed | Epic close | `completion_review_status == ship` |

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
       created ──▶ in_progress ──▶ review ──▶ done
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

## Querying Current State

Users and agents can check the current state at any time:

```bash
# Full state check
$FLUXCTL session-state --json

# Active epics
$FLUXCTL epics --json

# Active tasks for an epic
$FLUXCTL tasks --epic <id> --json

# Next ready task
$FLUXCTL ready --epic <id> --json

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

Every state transition is recorded in `.flux/` as JSON. The state machine is inspectable, resumable, and portable across sessions.
