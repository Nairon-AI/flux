---
name: flux-prime
description: Comprehensive codebase assessment for agent and production readiness. Scans 8 pillars (48 criteria), verifies commands work, checks GitHub settings. Reports everything, fixes agent readiness only. Triggers on /flux:prime.
user-invocable: false
---

# Flow Prime

Comprehensive codebase assessment inspired by [Factory.ai's Agent Readiness framework](https://factory.ai/news/agent-readiness).

**Role**: readiness assessor, improvement proposer
**Goal**: full visibility into codebase health, targeted fixes for agent readiness

## Two-Tier Assessment

| Category | Pillars | What Happens |
|----------|---------|--------------|
| **Agent Readiness** | 1-5 (30 criteria) | Scored, maturity level calculated, fixes offered |
| **Production Readiness** | 6-8 (18 criteria) | Reported for awareness, no fixes offered |

This gives you **full visibility** while keeping remediation focused on what actually helps agents work.

## Why This Matters

Agents waste cycles when:
- No pre-commit hooks → waits 10min for CI instead of 5sec local feedback
- Undocumented env vars → guesses, fails, guesses again
- No CLAUDE.md → doesn't know project conventions
- Missing test commands → can't verify changes work
- No provider CLIs/MCPs → user has to context-switch to Vercel/Railway/Neon dashboards for every deploy or DB query

These are **environment problems**, not agent problems. Prime helps fix them.

## Infrastructure Provider Detection

Prime scans the codebase for cloud providers (Vercel, Railway, Neon, Supabase, Cloudflare, AWS, Stripe, etc.) and recommends MCPs or CLIs that give agents direct access. This means agents can deploy, query databases, check logs, and manage secrets without the user needing to open provider dashboards.

## Session Phase Tracking

On entry, set the session phase:
```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
[ ! -d "$PLUGIN_ROOT/scripts" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
$FLUXCTL session-phase set prime
```

On completion, reset to idle:
```bash
$FLUXCTL session-phase set idle
```

## Input

Full request: $ARGUMENTS

Accepts:
- No arguments (scans current repo)
- `--report-only` or `report only` (skip remediation, just show report)
- `--fix-all` or `fix all` (apply all agent readiness fixes without asking)
- Path to different repo root

Examples:
- `/flux:prime`
- `/flux:prime --report-only`
- `/flux:prime ~/other-project`

## The Eight Pillars

### Agent Readiness (Pillars 1-5) — Fixes Offered

| Pillar | What It Checks |
|--------|----------------|
| **1. Style & Validation** | Linters, formatters, type checking, pre-commit hooks |
| **2. Build System** | Build tools, commands, lock files, monorepo tooling |
| **3. Testing** | Test framework, commands, coverage, verification |
| **4. Documentation** | README, CLAUDE.md, setup docs, architecture |
| **5. Dev Environment** | .env.example, Docker, devcontainer, runtime version |

### Production Readiness (Pillars 6-8) — Report Only

| Pillar | What It Checks |
|--------|----------------|
| **6. Observability** | Logging, tracing, metrics, error tracking, health endpoints |
| **7. Security** | Branch protection, secret scanning, CODEOWNERS, Dependabot |
| **8. Workflow & Process** | CI/CD, PR templates, issue templates, release automation |

## Workflow

Read [workflow.md](workflow.md) and execute each phase in order.

**Key phases:**
1. **Parallel Assessment** — 9 Codex scouts run in parallel by default (~15-20 seconds)
2. **Verification** — Verify test commands actually work
3. **Score & Synthesize** — Calculate scores, determine maturity level
4. **Present Report** — Full report with all 8 pillars
5. **Interactive Remediation** — AskUserQuestion for agent readiness fixes only
6. **Apply Fixes** — Create/modify files based on selections
7. **Architecture Diagram** — Seed or refresh `.flux/brain/codebase/architecture.md` as the canonical whole-product map
8. **Summary** — Show what was changed
9. **Mark Prime Complete** — So session-state knows priming is done
10. **Ruminate Offer** — If brain is thin + past sessions exist, ask the user if they want to populate the brain from past conversations. If they say yes, run `/flux:ruminate` immediately as part of prime — not as a separate workflow suggestion.

Prime's scout fan-out should apply `flux-parallel-dispatch`: launch all read-only, independent scouts together; do not serialize them.

## Maturity Levels (Agent Readiness)

| Level | Name | Description | Score |
|-------|------|-------------|-------|
| 1 | Minimal | Basic project structure only | <30% |
| 2 | Functional | Can build and run, limited docs | 30-49% |
| 3 | **Standardized** | Agent-ready for routine work | 50-69% |
| 4 | Optimized | Fast feedback loops, comprehensive docs | 70-84% |
| 5 | Autonomous | Full autonomous operation capable | 85%+ |

**Level 3 is the target** for most teams. Don't over-engineer.

## What Gets Fixed vs Reported

| Pillars | Category | Remediation |
|---------|----------|-------------|
| 1-5 | Agent Readiness | ✅ Fixes offered via AskUserQuestion |
| 6-8 | Production Readiness | ❌ Reported only, address independently |

## Guardrails

### General
- Never modify code files (only config, docs, scripts)
- Never commit changes (leave for user to review)
- Never delete files
- Respect .gitignore patterns

### User Consent
- **MUST use AskUserQuestion tool** for consent — never just print questions as text
- Always ask before modifying existing files
- Don't add dependencies without consent

### Scope Control
- **Never create LICENSE files** — license choice requires explicit user decision
- **Never offer Pillar 6-8 fixes** — production readiness is informational only
- Focus fixes on what helps agents work (not team governance)

## Scouts

### Agent Readiness (haiku, fast)
- `tooling-scout` — linters, formatters, pre-commit, type checking
- `claude-md-scout` — CLAUDE.md/AGENTS.md analysis
- `env-scout` — environment setup
- `testing-scout` — test infrastructure
- `build-scout` — build system
- `docs-gap-scout` — README, ADRs, architecture

### Production Readiness (haiku, fast)
- `observability-scout` — logging, tracing, metrics, health
- `security-scout` — GitHub settings, CODEOWNERS, secrets
- `workflow-scout` — CI/CD, templates, automation

All 9 scouts run in parallel for speed.


---

## Update Check (End of Command)

**ALWAYS run at the very end of command execution:**

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
[ ! -d "$PLUGIN_ROOT/scripts" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
UPDATE_JSON=$("$PLUGIN_ROOT/scripts/version-check.sh" 2>/dev/null || echo '{"update_available":false}')
UPDATE_AVAILABLE=$(echo "$UPDATE_JSON" | jq -r '.update_available')
LOCAL_VER=$(echo "$UPDATE_JSON" | jq -r '.local_version')
REMOTE_VER=$(echo "$UPDATE_JSON" | jq -r '.remote_version')
```

**If update available**, append to output:

```
---
Flux update available: v${LOCAL_VER} → v${REMOTE_VER}
Update Flux from the same source you installed it from, then restart your agent session.
---
```
