<div align="center">

# Flux

[![Discord](https://img.shields.io/badge/Discord-Join-5865F2?logo=discord&logoColor=white)](https://discord.gg/CEQMd6fmXk)
[![Version](https://img.shields.io/badge/version-v2.13.1--dev-green)](https://github.com/Nairon-AI/flux/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Plugin-blueviolet)](https://claude.ai/code)

**The missing (self-improving) harness for Claude Code.**<br>
Build software reliably.

> Recommended orchestrator: [SuperSet](https://superset.sh/) — parallel Claude Code sessions with git worktree isolation.

</div>

## The Problem

You're using an AI coding agent, but something's off:

- **No structure** → You said "build me a dashboard" and came back to a mess of half-finished components
- **Context amnesia** → You've explained the auth flow three times this week. To the same agent.
- **Groundhog Day** → The agent tried the same broken import path five times in a row and you watched it happen
- **Tool FOMO** → You found out about Context7 after spending two hours debugging stale docs
- **Requirements drift** → You asked for a login page and got a full user management system with email verification
- **Blind acceptance** → You shipped the agent's suggestion without reading it. It's in production now. Good luck.
- **Security roulette** → Someone found the hardcoded API key the agent left in your config. On GitHub. Publicly.
- **Echo chamber** → The same model you used to write the code, reviewed its own code, said "looks good", and you believed it (lmao)
- **Long tasks implode** → 20 minutes into a complex refactor, the agent forgot what it was doing and started over
- **Flying blind** → You have no idea if you're getting better at this or just getting faster at making mistakes

<p align="center">
  <img src="https://media1.tenor.com/m/KBShDXgDMsUAAAAC/green-mile-im-tired-boss.gif" alt="I'm tired, boss" width="400">
</p>

These aren't model failures. They're **process failures**.

**This is where Flux comes in.**

- **Repeatable workflows** — enforces structure across sessions so you and the agent never lose track of what's next
- **Multi-model adversarial reviews** — catches what no single model spots alone
- **Long tasks without drift** — Flux keeps the agent on rails even when context gets deep
- **Session analysis** — detect inefficiencies and get recommended optimisations from an engine that learns your patterns
- **Always up-to-date** — stays current with the latest harness and context engineering best practices so you can stop doom-scrolling

Ship with confidence. Sleep better at night.

---

## Contents

- [Install](#install)
- [Getting Started](#getting-started)
- [Architecture](#architecture)
- [Features](#features)
- [Commands](#commands)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Roadmap](#roadmap)
- [Community](#community)

---

## Install

| Agent | Status | Install |
|-------|--------|---------|
| [Claude Code](https://claude.ai/code) | ✅ First-Class Support | `/plugin add https://github.com/Nairon-AI/flux@latest` |
| [OpenCode](https://github.com/anomalyco/opencode) | `[█████░░░░░░] ~45%` | [flux-opencode](https://github.com/Nairon-AI/flux-opencode) — core workflow ported, v2.0+ features pending |

**Install** — say this in Claude Code:
```
Install the Flux plugin. Here's the README: https://github.com/Nairon-AI/flux
```

**Upgrade** — type `/flux:upgrade` in Claude Code, then restart with `--resume`. Your project setup is untouched.

**Uninstall** — say this in Claude Code:
```
Uninstall the Flux plugin and clean up. README: https://github.com/Nairon-AI/flux
```

After setup, just talk to the agent. Flux parses your message intent and routes to the right workflow — scope, work, review, or reflect — based on session state and what's currently in progress. You and the agent always know what's next.

> **Everything is project-local.** MCP servers go in `.mcp.json`, skills in `.claude/skills/`, config in `.flux/`. Nothing touches your global `~/.claude/settings.json`. No two projects need the same harness — different MCPs, skills, tools, and agentic patterns. Flux starts as a one-size-fits-all setup, then self-improves daily into the best harness for *that specific project*.

<details>
<summary><strong>Plugin CLI Reference</strong></summary>

Flux uses Claude Code's [plugin system](https://docs.anthropic.com/en/docs/claude-code/plugins). These are the `claude plugin` CLI commands used for install, upgrade, and uninstall. They can be run in a terminal or via Claude Code's bash tool.

#### Install
1. Add the marketplace and install the plugin:
   ```bash
   claude plugin marketplace add https://github.com/Nairon-AI/flux 2>&1
   claude plugin install flux@nairon-flux 2>&1
   ```
2. Clear any stale cache and re-clone to ensure the latest version:
   ```bash
   rm -rf ~/.claude/plugins/cache/nairon-flux
   claude plugin marketplace add https://github.com/Nairon-AI/flux 2>&1
   ```
3. Tell the user to restart their agent/session with `--resume` to load the plugin.
4. After restart, run `/flux:setup` to scaffold `.flux/` and configure preferences.
5. If setup installs new MCP servers, tell the user to restart with `--resume` once more.
6. After restart, run `/flux:prime` if the repo hasn't been primed yet.

#### Upgrade
Run `/flux:upgrade` inside Claude Code, then restart with `--resume`. Project-local files (`.flux/`, brain vault, CLAUDE.md, MCP servers) are never affected.

#### Uninstall
1. Read `.flux/meta.json` for the `installed_by_flux` manifest to see what Flux added.
2. Ask the user per-category what to keep vs. remove (MCP servers, skills, desktop apps, CLI tools) — many aren't Flux-specific.
3. Uninstall the plugin and remove the marketplace:
   ```bash
   claude plugin uninstall flux@nairon-flux 2>&1
   claude plugin marketplace remove nairon-flux 2>&1
   ```
4. Remove project artifacts:
   ```bash
   rm -rf .flux .mcp.json .claude/skills/
   ```
5. Remove the `<!-- BEGIN FLUX -->` ... `<!-- END FLUX -->` section from CLAUDE.md and AGENTS.md.
6. Optionally remove plugin cache: `rm -rf ~/.claude/plugins/cache/nairon-flux`
7. Restart Claude Code.

For **OpenCode**, use the [flux-opencode](https://github.com/Nairon-AI/flux-opencode) port instead.
</details>

---

## Getting Started

### 1. Setup

`/flux:setup` scaffolds `.flux/` in your project, configures your preferences, and optionally installs productivity tools. Everything is opt-in — you pick what you want.

<details>
<summary><b>What Flux offers to install</b></summary>

**MCP Servers** — extend what Claude can do:

| MCP | Why |
|-----|-----|
| [FFF](https://github.com/dmtrKovalenko/fff.nvim) | 10x faster file search — fuzzy, frecency-aware, git-status-aware (replaces default Glob/find) |
| [Context7](https://context7.com) | Up-to-date, version-specific library docs — no more hallucinated APIs |
| [Exa](https://exa.ai) | Fastest AI web search — real-time research without leaving your session |
| [GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/github) | PRs, issues, actions in Claude — no context switching to browser |
| [Firecrawl](https://firecrawl.dev) | Scrape websites and PDFs into clean markdown for agents |

**CLI Tools** — terminal essentials:

| Tool | Why |
|------|-----|
| [gh](https://cli.github.com) | GitHub from the terminal — PRs, issues, releases |
| [jq](https://jqlang.github.io/jq/) | JSON parsing for Flux internals |
| [fzf](https://github.com/junegunn/fzf) | Fuzzy finder for interactive selection |
| [Lefthook](https://github.com/evilmartians/lefthook) | Fast git hooks for pre-commit checks |
| [agent-browser](https://github.com/nichochar/agent-browser) | Headless browser for automated UI QA during epic reviews |
| [CLI Continues](https://github.com/nichochar/continues) | Session handoff — pick up where you left off across terminals |

**Desktop Apps** (macOS):

| App | Why |
|-----|-----|
| [Superset](https://superset.dev) | Parallel Claude sessions with git worktree workspace management |
| [Raycast](https://raycast.com) | Launcher with AI, snippets, clipboard history |
| [Wispr Flow](https://wisprflow.com) | Voice-to-text dictation — 4x faster than typing |
| [Granola](https://granola.ai) | AI meeting notes without a bot joining your calls |


</details>

### 2. Prime

`/flux:prime` audits your codebase for agent readiness across 8 pillars and 48 criteria. It runs once per repo and Flux detects when it's needed.

### 3. Build

After prime, just tell the agent what you want — *build a feature, fix a bug, refactor something, continue work*. Flux uses repo state plus your message to decide whether to scope, resume, review, or hand off.

> **Why both Claude and Codex?** Flux works best with both a Claude and an OpenAI Codex subscription. During epic reviews, Flux runs adversarial dual-model review — two models with different training data review independently and consensus issues get auto-fixed. You can also bring your own review bot (Greptile, CodeRabbit) for a third perspective. See [Reviews](#reviews--two-tier-architecture) below.

---

## Architecture

```mermaid
flowchart TD
    SessionStart["Session Start<br/>(startup hook)"]
    Pulse{"recommendation<br/>pulse"}
    Prime["Prime<br/>(readiness audit)"]
    Propose["Propose<br/>(stakeholder intake)"]
    RCA["RCA<br/>(root cause analysis)"]
    Scope["Scope<br/>(problem definition)"]
    Work["Work<br/>(task loop)"]
    ImplReview["Impl Review<br/>(per-task, lightweight)"]
    EpicReview["Epic Review<br/>(per-epic, thorough)"]
    Quality["Quality<br/>(tests + desloppify scan)"]
    Submit["Submit<br/>(push + PR)"]
    Reflect["Reflect<br/>(capture learnings)"]
    Meditate["Meditate<br/>(prune + promote)"]
    Ruminate["Ruminate<br/>(mine past sessions)"]
    Improve["Improve<br/>(recommendations engine)"]

    SessionStart --> Pulse
    Pulse -->|"new tools?<br/>nudge /flux:improve"| Prime
    Pulse -->|"all clear"| Prime
    Prime -->|"brain thin +<br/>past sessions exist"| Ruminate
    Prime -->|"brain ready"| Scope
    Ruminate -->|"bootstrap brain<br/>from history"| Scope
    Scope -->|"non-technical user<br/>detected"| Propose
    Propose -->|"creates proposal PR<br/>for engineering"| ProposeDone["Proposal Created"]
    Scope -->|"bug detected"| RCA
    RCA -->|"fix + regression test<br/>+ pitfall written"| Submit
    Scope -->|"creates epic + tasks<br/>+ Browser QA checklist"| ExecChoice{"Execute how?"}

    ExecChoice -->|"task-by-task<br/>(interactive)"| Work
    ExecChoice -->|"ralph mode<br/>(autonomous)"| Ralph["Ralph<br/>(autonomous harness)"]
    Ralph -->|"runs all tasks<br/>+ reviews unattended"| EpicReview

    subgraph task_loop ["Task Loop (per task)"]
        Work -->|"spawn worker"| ImplReview
        ImplReview -->|"NEEDS_WORK"| Work
        ImplReview -->|"SHIP"| FrictionCheck{"friction<br/>detected?"}
        FrictionCheck -->|"yes + not dismissed"| InlineImprove["Inline Recommend<br/>(install / skip / dismiss)"]
        InlineImprove --> NextTask["Next Task"]
        FrictionCheck -->|"no / dismissed"| NextTask
        NextTask -->|"more tasks"| Work
    end

    NextTask -->|"all tasks done"| EpicReview

    subgraph review_pipeline ["Epic Review Pipeline"]
        direction TB
        SpecCompliance["Spec Compliance"]
        Adversarial["Adversarial Review<br/>(Anthropic + OpenAI)"]
        SecurityScan["STRIDE Security Scan"]
        BotSelfHeal["BYORB Self-Heal<br/>(Greptile / CodeRabbit)<br/><i>optional</i>"]
        BrowserQA["Browser QA"]
        LearningCapture["Learning Capture"]
        DesloppifyScan["Desloppify Scan"]
        FrustrationSignal{"friction<br/>score >= 3?"}

        SpecCompliance --> Adversarial
        Adversarial --> SecurityScan
        SecurityScan --> BotSelfHeal
        SecurityScan -->|"no bot configured"| BrowserQA
        BotSelfHeal --> BrowserQA
        BrowserQA --> LearningCapture
        LearningCapture --> DesloppifyScan
        DesloppifyScan --> FrustrationSignal
    end

    EpicReview --> SpecCompliance
    FrustrationSignal -->|"no"| Quality
    FrustrationSignal -->|"yes: auto-fetch<br/>recommendations +<br/>offer installs"| Quality
    Quality --> Submit
    Submit --> Reflect
    Reflect -->|"20+ pitfall files"| Meditate
    Reflect -->|"brain healthy"| Done["Done"]
    Meditate --> Done

    Brain["Brain Vault<br/>(pitfalls, principles,<br/>conventions, decisions)"]

    Brain -.->|"read: principles +<br/>relevant pitfalls"| Scope
    Brain -.->|"read: re-anchor<br/>per task"| Work
    LearningCapture -.->|"write: pitfalls<br/>by area"| Brain
    Reflect -.->|"write: learnings<br/>+ skills"| Brain
    Ruminate -.->|"write: mined<br/>patterns"| Brain
    Meditate -.->|"prune/promote"| Brain
    Pulse -.->|"nudge when<br/>new tools"| Improve
```

| Phase | What happens | Why it exists |
|-------|-------------|---------------|
| **Session Start** | Startup hook injects brain vault index + workflow state. Recommendation pulse checks for new tools and brain health (once/day). | Without this, every session starts from zero — the agent doesn't know what it learned yesterday, what work is in progress, or what the project's conventions are. The hook gives it continuity. |
| **Prime** | One-time readiness audit: 8 pillars, 48 criteria. | Agents routinely skip foundational setup (testing, CI, linting, security) and jump straight to features. Prime forces a baseline before any real work starts, catching gaps that would otherwise surface as bugs weeks later. |
| **Ruminate** | *Auto after Prime (conditional):* mines past Claude Code conversations to bootstrap the brain vault. Triggers when brain has < 5 files and past sessions exist. | You've already taught the agent things in prior sessions — corrections, preferences, domain knowledge — but that knowledge dies with each session. Ruminate recovers it so you don't repeat yourself. Only runs once when the brain is empty. |
| **Propose** | Stakeholder feature proposal: conversational planning with engineering pushback, cost/complexity estimates, documented handoff via PR. | Non-technical team members describe features without implementation detail. Without Propose, vague requests go straight to engineering as ambiguous tickets. Propose forces clarity and estimates before engineering time is spent. |
| **RCA** | Bug-specific flow: backward trace from symptom to root cause, adversarial verification, regression test, embedded learnings. | Agents fix symptoms, not causes. They'll patch the crash without understanding why it crashed. RCA forces backward tracing from symptom → root cause, mandates regression tests, and writes a pitfall so the same class of bug is caught earlier next time. |
| **Scope** | Double Diamond interview: classify work, surface blind spots, create epic with sized tasks. After scoping, choose execution mode: **task-by-task** (interactive `/flux:work`) or **Ralph mode** (autonomous — runs all tasks + reviews unattended). | Agents start building the moment you describe a feature. Without scoping, they miss edge cases, build the wrong thing, or over-engineer. The interview catches blind spots before a single line of code is written. |
| **Work** | Task loop: spawn worker per task with fresh context, brain re-anchor, impl-review after each. After each task, checks for friction signals (build errors, lint failures, API hallucinations) and offers targeted tool recommendations inline — install, skip, or snooze for 7 days. Snoozed signals automatically resurface to check for new tooling. In Ralph mode, this loop runs autonomously without stopping. | Long tasks degrade agent quality — context bloats, the agent forgets constraints, output gets sloppy. Fresh workers per task keep context tight. Inline friction detection catches recurring pain points *during* the build, not after — so you can unblock immediately instead of suffering through an entire epic before getting a recommendation. |
| **Review** | Per-task lightweight (`impl-review`), per-epic thorough (`epic-review` — adversarial, security, BYORB *optional*, browser QA, learning capture). | Self-review is unreliable — the same model that wrote the code reviews it. Adversarial review (multiple models reaching consensus) catches what single-model review misses. BYORB (Greptile, CodeRabbit, etc.) is optional — skipped if no bot is configured. Browser QA catches what code review can't see at all. |
| **Quality** | Tests, lint/format, desloppify scan on changed files. | Agents skip tests, ignore lint errors, and leave dead code. Quality is the gate before Submit — nothing ships without passing. |
| **Submit** | Push + open PR. Code is ready for review/merge. | Separates "code is done" from "code is shipped." The PR is the handoff point where human reviewers and CI take over. |
| **Reflect** | *Auto after Submit:* captures session learnings to brain vault and extracts reusable skills while context is fresh. | The agent just spent an entire session learning your codebase, hitting bugs, getting corrected. If you don't capture those learnings *now*, they're gone — the next session starts from scratch. Reflect is the difference between an agent that gets smarter over time and one that makes the same mistakes forever. |
| **Meditate** | *Auto after Reflect (conditional):* prunes stale notes, promotes pitfalls to principles. Triggers when 20+ pitfall files accumulate. | The brain vault grows without bound. Old pitfalls become irrelevant (code was refactored), recurring patterns deserve promotion to principles (stronger signal). Without periodic curation, the brain becomes noise — too many files, contradictory advice, stale warnings about code that no longer exists. |
| **Ship** | PR merged + deployed. | Happens outside Flux's session scope — CI/CD, human review, merge. Flux's job ends at Submit. |
| **Gate** | *After staging merge:* verifies staging deployment is live, runs browser QA or manual review against staging URL, then creates promotion PR (staging → production). | Code that passes CI can still break in staging — env variables differ, APIs behave differently, CDN caching causes stale assets. Gate is the checkpoint between "code compiles" and "code actually works in a real environment." Without it, production deploys are a leap of faith. |
| **Improve** | *Inline:* after each task, friction signals trigger a targeted recommendation (install / skip / snooze). Snoozed signals enter a 7-day cooldown, then resurface: "It's been a week — want to check for new optimizations?" *Epic-level (score >= 3):* recommendations matched to your friction patterns. | When the same friction keeps recurring, the problem isn't the code — it's a missing tool. Inline detection catches it during the build so you can unblock immediately. The 7-day cooldown prevents recommendation fatigue while still giving the ecosystem time to develop new tooling — what had no good fix last week might have one today. |

### What's Automatic vs Manual

| Action | Trigger | Type |
|--------|---------|------|
| **Session start hook** | Every session | Automatic — injects brain vault index + workflow state |
| **Recommendation pulse** | Every session (rate-limited 1x/day) | Automatic — nudges for new tools, brain vault health |
| **`session-state` routing** | Before any work-like request | Automatic — routes to prime/scope/work/review |
| **Reflect** | After PR is submitted | Automatic — captures learnings while context is fresh |
| **Meditate** | After Reflect, if 20+ pitfall files | Automatic — prunes stale, promotes patterns |
| **Ruminate** | After Prime, if brain thin + past sessions exist | Automatic — bootstraps brain from conversation history |
| **Improve** | During epic review, if friction score >= 3 | Automatic — fetches and matches recommendations |
| **Setup** (`/flux:setup`) | First install; re-run after major upgrades | Manual — Flux nudges if setup version is stale after upgrade |
| **Prime** (`/flux:prime`) | First session per project | Manual — but `session-state` blocks until done |
| **Scope** (`/flux:scope`) | Start new work | Manual |
| **Work** (`/flux:work`) | Execute a plan task-by-task | Manual |
| **Ralph** (`/flux:ralph-init`) | Execute an entire epic autonomously | Manual — offered after scoping |
| **Upgrade** (`/flux:upgrade`) | Get latest Flux version | Manual |
| **Gate** (`/flux:gate`) | Validate staging after merge | Manual (or CI auto) |

After upgrading, if your project's setup version is behind the plugin version, Flux will nudge you to re-run `/flux:setup` to pick up new configuration options.

---

## Features

### Deterministic State Engine

`.flux/` is the canonical workflow state. `session-state` tells Flux whether to prime, start fresh, resume scoping, resume implementation, or route to review. `brain/` is the persistent knowledge store — principles, pitfalls, conventions, and decisions. Startup hooks realign the agent with Flux state before acting on new requests.

### Built-in Agentmap

Flux generates YAML repo maps from git-tracked files for faster agent navigation.

```bash
fluxctl agentmap --write   # Writes .flux/context/agentmap.yaml
```

### Brain Vault — Single Knowledge Store

Flux's brain is an Obsidian-compatible vault (`brain/`) that serves as the single knowledge store for the entire system. Adapted from [brainmaxxing](https://github.com/poteto/brainmaxxing), it's wired into every core workflow:

- **Scoping** reads brain principles and pitfalls to ground research and plan structure
- **Worker** reads pitfalls (only from relevant area) and principles during re-anchor before each task
- **Epic review** writes learnings back to `brain/pitfalls/<area>/` after SHIP, categorized by domain
- **Meditate** promotes recurring pitfalls into proper principles and prunes one-offs

```
brain/
  principles/    # Engineering principles (curated via meditate)
  pitfalls/      # Auto-captured from review iterations, organized by area
    frontend/    #   e.g., missing-error-states.md
    security/    #   e.g., greptile-auth-gap.md
    async/       #   e.g., consensus-race-condition.md
  conventions/   # Project-specific patterns
  decisions/     # Architectural decisions with rationale
  plans/         # From scope/plan
```

```bash
/flux:reflect    # Capture session learnings + extract reusable skills
/flux:ruminate   # Mine past conversations for missed patterns
/flux:meditate   # Prune stale notes, promote pitfalls → principles
```

These are maintenance skills designed to run between epics, not during active development. They audit, prune, and evolve the brain vault when you have breathing room.

### Self-Improving Harness

Flux autonomously finds ways to improve itself for every project it's used in. The recommendation engine surfaces tools matched to friction patterns at every natural touchpoint — not just when you ask for it:

| Touchpoint | What fires | How heavy |
|---|---|---|
| **Session start** | Recommendation pulse — checks for new tools and brain vault health | ~2s, once/day |
| **During work** | Qualitative friction analysis — detects frustration topic from developer messages | Zero cost |
| **After epic review** | Targeted `/flux:improve` suggestion with pre-filled friction context | Zero cost |
| **After shipping** | `/flux:reflect` suggestion to capture learnings | Zero cost |
| **Between epics** | Full `/flux:improve` analysis, `/flux:meditate` for brain pruning | Heavyweight |

The **recommendation pulse** runs as a startup hook every session (rate-limited to once per day). It checks for new recommendations matched to your stack. If anything is actionable, it surfaces a brief nudge — you multi-select to install or dismiss.

The **friction signal** fires during epic review using two layers: a quantitative friction score (review iterations, security findings, QA failures, repeated pitfalls) and qualitative analysis that scans developer messages and reviewer feedback to identify *what* you're struggling with. When the score hits 3+, Flux suggests `/flux:improve` with the friction domain pre-filled (e.g., `--user-context "responsive, CSS, mobile"`) so the recommendation engine skips discovery and goes straight to relevant tools.

The result: Flux gets smarter every session — new tools surface proactively, friction domains get diagnosed automatically, and the brain vault stays lean through meditate nudges. You don't have to remember to run maintenance commands.

### Desloppify

Systematic code quality improvement powered by [desloppify](https://github.com/peteromallet/desloppify). Combines mechanical detection with LLM-based review. The scoring system resists gaming — you can't suppress warnings, you have to actually fix the code.

When installed, Flux automatically runs a lightweight desloppify scan after epic review to surface quality regressions introduced during the epic. If the score drops below 85, it suggests a full fix pass.

```bash
/flux:desloppify scan     # See your score
/flux:desloppify next     # Get next priority fix
```

### Reviews — Two-Tier Architecture

Flux splits reviews into two tiers so you get fast feedback per-task without slowing down, and thorough verification per-epic before shipping.

**Per-task: Lightweight** (`/flux:impl-review`)
Single-model pass after each task. Catches obvious bugs, logic errors, and spec drift in seconds. Fast enough to run on every task without breaking flow.

**Per-epic: Thorough** (`/flux:epic-review`)
Full pipeline that runs once when all epic tasks are done:

| Phase | What happens |
|-------|-------------|
| Spec compliance | Verify every requirement from the epic spec is implemented |
| Adversarial review | Two models from different labs (Anthropic + OpenAI) review independently — consensus issues = high confidence |
| Severity filtering | Only auto-fix issues at/above your configured threshold (critical, major, minor, style) |
| Security scan | STRIDE-based vulnerability scan — auto-triggered when changes touch auth, API, secrets, or permissions |
| BYORB self-heal | Bring Your Own Review Bot — Greptile or CodeRabbit catch what models miss |
| Browser QA | Test acceptance criteria from scoping checklist via [agent-browser](https://github.com/AgnBc/agent-browser) |
| Learning capture | Extract patterns from review feedback into `brain/pitfalls/` |

> **Why adversarial?** A single model has blind spots. Two models from different labs (e.g., Claude + GPT) with different training data and biases catch issues that neither finds alone. When both models flag the same issue, it's almost certainly real. When only one does, Flux uses your severity threshold to decide whether to fix or log.

#### Security — Built Into the Review Pipeline

Security scanning is not a separate step you remember to run — it's baked into the epic review pipeline. When your changes touch security-sensitive files (auth, API routes, middleware, secrets, permissions), Flux automatically runs a [STRIDE](https://docs.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats)-based scan adapted from [Factory AI](https://github.com/Factory-AI/factory-plugins). Findings are validated for exploitability (confidence >= 0.8 only), filtered by your severity threshold, and auto-fixed.

You can also run security tools standalone when needed:

```bash
/flux:threat-model           # Generate STRIDE threat model
/flux:security-scan PR #123  # Scan PR changes
/flux:security-review        # Full repository audit
```

#### BYORB — Bring Your Own Review Bot

Flux integrates with external code review bots that run on your PR. Configure during `/flux:setup`:

| Bot | How it works |
|-----|-------------|
| [Greptile](https://greptile.com) | Attaches a confidence summary to your PR description. Flux polls for it, parses the score and issue list, and auto-fixes issues above your severity threshold. |
| [CodeRabbit](https://coderabbit.ai) | Posts review comments on your PR. Flux polls for comments (or uses the CLI), parses issues, and auto-fixes above threshold. |

Bots catch patterns that LLMs miss — dependency conflicts, project-specific conventions, security rules from your org config. Combined with adversarial model review, you get three independent perspectives on every epic.

#### Browser QA — Scoping Creates the Test Plan

During `/flux:scope`, Flux detects frontend/web epics and auto-creates a **Browser QA Checklist** task with testable criteria (URLs, expected elements, user flows). At epic review time, `agent-browser` follows this checklist — no manual test plan needed.

#### Learning Capture — Reviews That Pay for Themselves

Every NEEDS_WORK iteration teaches Flux something. After reaching SHIP, Flux extracts generalizable patterns and writes them to `brain/pitfalls/`. The worker reads these during re-anchor at the start of every task. Over time, `/flux:meditate` promotes recurring pitfalls into proper principles and prunes one-offs — the brain gets smarter, not bigger.

**The result:** mistakes caught in review today are avoided in implementation tomorrow. Over time, you get fewer NEEDS_WORK iterations, shorter review cycles, and lower token spend — regardless of which review strategy you use. The learning feedback loop works with single-model, adversarial, or bot-assisted reviews.

```bash
/flux:setup   # Configure reviewers, bots, and severity threshold
```

### Linear Integration

Connect Flux to [Linear](https://linear.app) during `/flux:setup` — epics auto-create Linear projects, tasks auto-create issues, and status changes (start, done, block) sync in real-time. Your team gets full visibility without leaving Linear.

```bash
/flux:setup              # Select "Linear" when prompted for task tracker
fluxctl config get tracker.provider   # Check current tracker config
```

---

## Commands

**Core SDLC**

| Command | What it does | When it happens |
|---------|-------------|-----------------|
| `/flux:setup` | Initialize Flux in your project | 1. First time using Flux — scaffolds `.flux/`, configures preferences, installs tools |
| `/flux:prime` | Codebase readiness audit (8 pillars, 48 criteria) | 2. After setup — Flux detects unprimed repos and prompts you. Runs once per repo |
| `/flux:propose` | Stakeholder feature proposal with engineering pushback | 2.5. A non-technical teammate describes a feature — Flux interviews them, pushes back on complexity/cost, documents the proposal, and creates a PR for engineering handoff. Also detected implicitly during `/flux:scope` |
| `/flux:rca` | Root cause analysis for bugs | 2.5. You paste an error or describe a bug — Flux traces backward to the root cause, verifies with adversarial review, writes the fix with regression test, and embeds learnings. Also detected implicitly during `/flux:scope` |
| `/flux:scope <idea>` | Guided scoping workflow (`--deep`, `--explore N`) | 3. You say "build me a dashboard" — Flux interviews you, creates an epic with sized tasks |
| `/flux:plan <idea>` | Create tasks only (skip interview) | 3. You already know exactly what to build — skip the Double Diamond interview, go straight to task creation |
| `/flux:work <task>` | Execute task with context reload | 4. After scoping — spawns a worker per task, each re-anchors from brain vault before implementing |
| `/flux:impl-review` | Lightweight per-task review (single model) | 5. Auto-triggered after each task completes inside `/flux:work` — you don't call this manually |
| `/flux:epic-review <epic>` | Thorough epic review (adversarial + BYORB + browser QA + learning + desloppify) | 6. Auto-triggered when all tasks in an epic are done — runs the full review pipeline before shipping |
| `/flux:sync <epic>` | Sync specs after drift | Anytime — you realized task 3 invalidated task 5's approach, sync updates downstream specs |
| `/flux:desloppify` | Code quality improvement (also runs as scan after epic review) | 7. After epic review flags a low score, or manually when you want to improve code quality |

**Security**

| Command | What it does | When it happens |
|---------|-------------|-----------------|
| `/flux:security-scan` | Scan for vulnerabilities | Auto-triggered inside epic review when changed files touch auth/API/secrets/permissions. Also callable standalone on any PR |
| `/flux:threat-model` | STRIDE-based threat model | Before building security-sensitive features — generates threat model to inform your design |
| `/flux:security-review` | Full security review | Before shipping to production — comprehensive repo-wide security audit |
| `/flux:vuln-validate` | Validate findings with PoC | After a scan finds issues — generates proof-of-concept exploits to confirm real vs false positive |

**Maintenance (between epics)**

| Command | What it does | When it happens |
|---------|-------------|-----------------|
| `/flux:reflect` | Capture session learnings to brain vault and extract reusable skills | 8. After shipping an epic — Flux suggests this so you capture learnings while context is fresh |
| `/flux:ruminate` | Mine past conversations for missed patterns | Between epics — when you have breathing room, mine old sessions for patterns you missed in the moment |
| `/flux:meditate` | Prune brain vault, promote pitfalls to principles | Auto-nudged at session start when 5+ new pitfalls accumulate or 30+ days since last meditation. Also run manually between epics |
| `/flux:improve` | Analyze sessions, recommend tools from the recommendation engine | Auto-nudged at session start when new tools available. Auto-suggested with pre-filled context when epic review detects friction (score >= 3) |

**Utilities**

| Command | What it does | When it happens |
|---------|-------------|-----------------|
| `/flux:score` | AI-native capability score | Anytime — benchmark your repo's AI-readiness |
| `/flux:profile` | Export/share SDLC profile | Anytime — share your Flux setup with teammates or the community |
| `/flux:contribute` | Report bug and auto-create fix PR | When you find a Flux bug — auto-creates a fix PR on the Flux repo |

Full reference: `docs/commands-reference.md`

### Prerequisites

Python 3.9+, jq, git. Flux checks for these during execution and tells you what's missing.

---

## Troubleshooting

> **AI Agents**: If you're debugging a Flux installation issue, follow these steps exactly. Do not guess.

<details>
<summary><strong>"Unknown skill: flux:setup"</strong></summary>

The plugin is registered but not enabled. Add to `~/.claude/settings.json`:

```bash
jq '.enabledPlugins["flux@nairon-flux"] = true' ~/.claude/settings.json > tmp.json && mv tmp.json ~/.claude/settings.json
```
Then restart Claude Code.
</details>

<details>
<summary><strong>Agent tried to run /plugin add in bash</strong></summary>

`/plugin` is a Claude Code slash command, not a shell command. Run it directly in the chat input, then restart.
</details>

<details>
<summary><strong>Commands still not working after enabling</strong></summary>

Clear cache and reinstall:
```bash
rm -rf ~/.claude/plugins/cache/nairon-flux ~/.claude/plugins/marketplaces/nairon-flux
```
Restart Claude Code, run `/plugin marketplace add https://github.com/Nairon-AI/flux`, then `/plugin add https://github.com/Nairon-AI/flux@latest`, restart again.
</details>

<details>
<summary><strong>Old version / missing new commands</strong></summary>

```bash
rm -rf ~/.claude/plugins/cache/nairon-flux
claude plugin marketplace add https://github.com/Nairon-AI/flux
```
Restart Claude Code.
</details>

<details>
<summary><strong>Nuclear option: complete reset</strong></summary>

```bash
rm -rf ~/.claude/plugins/cache/nairon-flux ~/.claude/plugins/marketplaces/nairon-flux
# Edit ~/.claude/plugins/installed_plugins.json — remove "nairon-flux" entries
# Edit ~/.claude/settings.json — remove "flux@nairon-flux" from enabledPlugins
```
Restart Claude Code, run `/plugin marketplace add https://github.com/Nairon-AI/flux`, then `/plugin add https://github.com/Nairon-AI/flux@latest`, restart, run `/flux:setup`.
</details>

**Still stuck?** Join [Discord](https://discord.gg/CEQMd6fmXk) or open a [GitHub issue](https://github.com/Nairon-AI/flux/issues).

---

## FAQ

<details>
<summary><strong>Do I have to follow every step Flux suggests?</strong></summary>

No — Flux is a guide, not a gatekeeper. You can skip steps, override suggestions, or exit any flow whenever you want.

The reason Flux has structured flows is to stop the AI agent from going rogue — without guardrails, agents tend to start building before they understand what they're building, skip testing, or forget context halfway through. Flux prevents that. But **you** are always in control. If a step feels unnecessary for your situation, skip it.

In practice, most devs use `/flux:scope` for complex or ambiguous features (where the interview catches blind spots), and just talk naturally for everything else ("fix the bug in auth.ts" — Flux routes straight to work, no ceremony).
</details>

<details>
<summary><strong>Will Flux slow me down on small tasks?</strong></summary>

No. Flux reads your message and figures out what kind of task it is.

- **Quick fix** ("fix the typo in header.tsx") → goes straight to implementation. No scoping interview, no epic creation — just does the work.
- **Clear task** ("add a loading spinner to the dashboard") → creates a lightweight plan and starts building.
- **Ambiguous feature** ("add user notifications") → triggers the scoping flow to make sure you've thought through edge cases before the agent writes code.

The full Product OS scoping flow (the interview, problem statement, task breakdown) only activates when you explicitly run `/flux:scope` or when the request is vague enough that building without clarification would waste time. For day-to-day work, Flux stays out of your way.
</details>

<details>
<summary><strong>What data does Flux read and where does it store things?</strong></summary>

Flux reads your **repo structure** (files, directories, dependencies), your **installed MCP servers** (from `.mcp.json`), and optionally your **Claude Code session transcripts** (only when you run `/flux:improve` and give explicit consent).

Everything Flux creates lives in a `.flux/` directory inside your project — task state, brain vault notes, session metadata. It never writes to your home directory or global config. Each project gets its own independent Flux setup, so different repos can have different tools, skills, and configurations without interfering with each other.

The only global change Flux makes is during `/flux:setup` if you choose to install CLI tools (like `jq` or `gh`) — but even that is opt-in and asks you first.
</details>

<details>
<summary><strong>Is any data sent externally? Is there telemetry?</strong></summary>

**No telemetry. No usage tracking. No analytics.**

The only network request Flux makes is **checking for plugin updates** — a version check against the GitHub release tag at the end of commands.

That's it. All analysis (session parsing, friction detection, scoring) runs entirely on your machine. Your code never leaves your laptop.
</details>

<details>
<summary><strong>Can I use Flux alongside other task tracking tools (Beads, TodoWrite, etc.)?</strong></summary>

Not recommended. Flux uses its own task tracking system (`.flux/` + `fluxctl`) to maintain state across sessions — what's been scoped, what's in progress, what's done. If you also use Beads, TodoWrite, or markdown TODO files, the agent will see two conflicting sources of truth and get confused about what to work on next.

Pick one system and stick with it. If you prefer Beads, use Beads. If you want the full Flux workflow (scoping, brain vault, reviews, recommendations), use Flux. Mixing them creates more problems than it solves.
</details>

<details>
<summary><strong>Can Flux run autonomously without me watching?</strong></summary>

Yes — that's what Ralph mode is for. After scoping an epic, Flux offers you two execution modes:

1. **Task-by-task** (`/flux:work`) — you stay in the loop, review each task as it completes, and guide the agent interactively.
2. **Ralph mode** (`/flux:ralph-init`) — a repo-local autonomous harness that works through every task in the epic unattended. It runs plan review, implementation, code review, and completion review for each task without stopping. You start it from your terminal (`./scripts/ralph/ralph.sh`) and check results in the morning.

Ralph uses multi-model review gates and produces receipts as proof-of-work. It can be paused and resumed at any point.
</details>

<details>
<summary><strong>Why does the version on main show "X.Y.Z-dev" instead of matching the latest release?</strong></summary>

By design. When a release is published (e.g., `v2.7.0`), a post-release workflow automatically bumps the version on main to `2.7.1-dev`. This ensures:

1. **Cache prevention** — the `-dev` suffix gives the plugin a distinct semver on main so users installing `@latest` always get the actual release, not a development snapshot.
2. **Development clarity** — you can immediately tell whether you're looking at released code (`2.7.0`) or in-progress development (`2.7.1-dev`).

The `0.0.1` difference is just a placeholder — the next release will be whatever the conventional commits dictate (patch, minor, or major), not necessarily `2.7.1`.
</details>

---

## Roadmap

### Next — Relay

A parallel orchestration layer for Flux. Heavily inspired by [OpenAI Symphony](https://github.com/openai/symphony).

Ralph already handles autonomous *serial* execution (one task at a time, unattended). Relay will coordinate multiple agents working *in parallel* across worktrees, manage task dependencies, and handle handoffs — so you can kick off a complex build, go for a walk, and come back to a PR.

### Feature Roadmap

| Command | Enhancement |
|---------|-------------|
| `/flux:work` | Git worktree support for parallel development |
| `/flux:scope` | Meeting transcript ingestion |

---

## Philosophy

1. **AI amplifies your skill level, it doesn't replace it.**
2. **Disagreement is a feature.** The best AI collaborators push back constantly.
3. **Process beats raw talent.** Structured approach > vibes-based prompting.
4. **What gets measured gets improved.** You can't fix what you can't see.
5. **The agent should do the work.** Analysis, installation — AI handles it. You decide.

---

## Community

No hype. No AI slop. Just practical discussions on becoming the strongest developers alive.

[discord.gg/CEQMd6fmXk](https://discord.gg/CEQMd6fmXk)

---

## Docs

- `docs/commands-reference.md` — Full command reference
- `docs/architecture.md` — How Flux works internally

---

## License

MIT

---

<p align="center">
  <em>Stop hoping AI makes you better. Start measuring it.</em>
</p>
