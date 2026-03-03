# Flux 2.0 Roadmap: Agent Swarm Orchestration

> The future of Flux: enabling one-person dev teams to run swarms of agents that mostly autonomously build software, with the right human-in-the-loop checkpoints and trust embedded.

## Vision

Flux 1.x is a structured workflow for individual AI coding sessions. Flux 2.0 becomes the **orchestration layer** — spawning, monitoring, and coordinating multiple agents working in parallel.

Think: You describe what you want to build. Flux spawns 5 agents, each working on a different part. They create PRs, review each other's code, run tests. You get a Telegram/Slack ping when PRs are ready to merge. You review for 10 minutes. Ship.

## Inspiration

Based on the OpenClaw + Codex/Claude Code agent swarm pattern:

- **94 commits in one day** without opening an editor
- **7 PRs in 30 minutes** from idea to production
- Orchestrator holds business context, agents focus on code
- Multi-model code review (catches different issues)
- Self-improving prompts based on what shipped

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        YOU (Human)                          │
│                    Strategic decisions only                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    FLUX ORCHESTRATOR                        │
│  • Holds all business context (brain vault, meeting notes)  │
│  • Translates requirements into agent prompts               │
│  • Spawns/monitors/redirects agents                         │
│  • Picks right model for each task                          │
│  • Pings you when PRs ready                                 │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  Claude Code  │    │    Codex      │    │  Claude Code  │
│   Agent #1    │    │   Agent #2    │    │   Agent #3    │
│  feat/auth    │    │  feat/billing │    │  fix/bug-123  │
│  (own branch) │    │  (own branch) │    │  (own branch) │
└───────────────┘    └───────────────┘    └───────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    AUTOMATED PIPELINE                       │
│  • CI (lint, types, tests, E2E)                            │
│  • Multi-model code review                                  │
│  • Screenshot verification for UI changes                   │
│  • Definition of done enforcement                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     HUMAN CHECKPOINT                        │
│           5-10 min review → Merge → Ship                    │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Orchestrator Agent (Flux Core)

The brain. Holds context the coding agents don't have:
- Customer history, meeting notes, past decisions
- What worked, what failed, why
- Full business context from brain vault

Responsibilities:
- Translate high-level requests into precise agent prompts
- Pick the right model for each task (Codex for backend, Claude for frontend, Gemini for design)
- Monitor agent progress without expensive polling
- Redirect agents mid-task when they go wrong direction
- Respawn failed agents with better prompts (max 3 attempts)
- Learn from what ships (self-improving prompts)

### 2. Agent Spawning

Each agent gets:
- Own worktree (isolated branch)
- Own tmux session with terminal logging
- Specific prompt with exactly the context it needs
- Definition of done

```bash
# Example spawn
git worktree add ../feat-notifications -b feat/notifications origin/main
tmux new-session -d -s "agent-notifications" \
  "claude --model claude-opus-4 --dangerously-skip-permissions -p 'Your prompt'"
```

### 3. Monitoring Loop (Ralph Loop V2)

Cron job every 10 minutes:
- Check if tmux sessions alive
- Check for open PRs on tracked branches
- Check CI status
- Auto-respawn failed agents
- Alert only when human attention needed

Key insight: Don't poll agents directly (expensive). Check git and CI status (cheap).

### 4. Multi-Model Code Review

Every PR reviewed by multiple models:
- **Codex**: Edge cases, logic errors, race conditions
- **Claude**: Architecture, patterns (tends to be overcautious)
- **Gemini**: Security, scalability, specific fixes

All post comments directly on PR.

### 5. Definition of Done

PR is "ready for human review" only when:
- [ ] PR created
- [ ] Branch synced to main (no conflicts)
- [ ] CI passing (lint, types, unit tests, E2E)
- [ ] All AI reviews passed
- [ ] Screenshots included (if UI changes)

### 6. Human-in-the-Loop Checkpoints

Trust is embedded through strategic checkpoints:
- **Scope approval**: Human confirms what to build
- **PR review**: Human reviews before merge (5-10 min)
- **Production deploy**: Human triggers (or auto with confidence threshold)

Human stays in control. Agents execute fast.

### 7. Proactive Work Finding

Orchestrator doesn't wait for assignments:
- Morning: Scan Sentry → spawn agents to fix errors
- After meetings: Scan notes → spawn agents for feature requests
- Evening: Scan git log → update changelog and docs

## Implementation Phases

### Phase 1: Multi-Agent Foundation
- [ ] Agent registry (track active agents, branches, status)
- [ ] Worktree management (spawn, cleanup)
- [ ] Basic monitoring loop
- [ ] Telegram/Slack notifications

### Phase 2: Orchestration Intelligence
- [ ] Context injection from brain vault
- [ ] Model selection logic (task → best model)
- [ ] Mid-task redirection via tmux
- [ ] Respawn with improved prompts

### Phase 3: Automated Review Pipeline
- [ ] Multi-model PR review integration
- [ ] Definition of done enforcement
- [ ] Screenshot requirement for UI changes
- [ ] Auto-merge with confidence threshold

### Phase 4: Self-Improvement
- [ ] Log successful prompt patterns
- [ ] Learn from CI failures
- [ ] Track what ships vs what gets rejected
- [ ] Progressively better prompts over time

### Phase 5: Proactive Autonomy
- [ ] Sentry integration (auto-fix errors)
- [ ] Meeting notes scanning
- [ ] Changelog/docs automation
- [ ] Customer request → PR pipeline

## Resource Requirements

Current bottleneck: **RAM**

Each agent needs:
- Own worktree
- Own node_modules
- Parallel builds, type checks, tests

Estimates:
- 16GB RAM → 4-5 agents max
- 64GB RAM → 15-20 agents
- 128GB RAM → 30+ agents

Recommended: Mac Studio M4 Max with 128GB RAM for serious swarm work.

## Success Metrics

- **Commits per day**: Target 50+ without opening editor
- **PRs per hour**: Target 5+ during active development
- **Human review time**: Target <10 min per PR
- **One-shot success rate**: Target 80%+ for small/medium tasks
- **Time to production**: Target same-day for most features

## Related Work

- [OpenClaw](https://openclaw.ai) - Agent orchestration platform
- Stripe's "Minions" - Internal parallel agent system
- Ralph Loop - Iterative agent improvement pattern

## Philosophy

> "The next generation of entrepreneurs won't hire a team of 10 to do what one person with the right system can do. They'll build like this — staying small, moving fast, shipping daily."

Flux 2.0 enables the one-person million-dollar company. Not by replacing humans, but by giving them leverage. You maintain laser focus and full control while agents handle the execution.

---

*This roadmap is aspirational. Priorities may shift based on user feedback and ecosystem evolution.*
