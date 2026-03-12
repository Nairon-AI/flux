<div align="center">

# Flux

[![Discord](https://img.shields.io/badge/Discord-Join-5865F2?logo=discord&logoColor=white)](https://discord.gg/CEQMd6fmXk)
[![Version](https://img.shields.io/badge/version-v1.9.6-green)](https://github.com/Nairon-AI/flux/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Plugin-blueviolet)](https://claude.ai/code)

**Your AI workflow has gaps. Flux finds them.**

</div>

---

### Platform Compatibility

| Platform | Status | Install |
|----------|--------|---------|
| [Claude Code](https://claude.ai/code) | ✅ Recommended | `/plugin add https://github.com/Nairon-AI/flux@latest` |
| [OpenCode](https://github.com/anomalyco/opencode) | `[██████████░] 96%` | [flux-opencode](https://github.com/Nairon-AI/flux-opencode) |

---

## The Problem

You're using an AI coding agent, but something's off:

- **No structure** → You jump straight into code and watch the agent go off the rails
- **Context amnesia** → You keep re-explaining the same thing every session
- **Groundhog Day** → The agent tries the same broken approach 5 times in a row
- **Tool FOMO** → You discover a tool that would've saved hours... after the fact
- **Requirements drift** → Scope creeps mid-session and you don't notice until it's too late
- **Blind acceptance** → You accept suggestions without questioning them (the AI is wrong more than you think)
- **No observability** → You have no idea how "AI-native" you are compared to others or where your gaps are

<p align="center">
  <img src="https://media1.tenor.com/m/KBShDXgDMsUAAAAC/green-mile-im-tired-boss.gif" alt="I'm tired, boss" width="400">
</p>


These aren't model failures. They're **process failures**.

**This is where Flux comes in.**

---

## What Flux Does

Flux is the accumulation of our learnings working at enterprise and building startups over the last 12 months, watching the SDLC evolve in real-time.

The insight: in the age of agentic development, **you still need a framework**—but it's compressed, morphed, and must prepare for increasingly autonomous building. The right human-in-the-loop checkpoints maintain your understanding of the system as it evolves, whether you're building solo or with a team.

**Flux gives you six things:**

1. **A deterministic state engine** — `.flux/` tracks the active objective, workflow phase, next action, and scoping artifacts so Flux can realign the agent without drift
2. **A structured workflow** — Prime once, then Scope -> Build -> Review -> Improve (and Reflect at session end)
3. **Native repo context mapping** — Flux can generate a built-in codebase map from tracked files for faster repo navigation and fresh-session realignment
4. **Adversarial reviews** — Plans and implementations are reviewed by a second model (Codex CLI / GPT) to reach multi-model consensus before shipping
5. **Continuous improvement** — Analyze your sessions, detect optimisations, install them to improve your agent and your Agentic workflow
6. **Observability** — Tap into your entire workflow to get full visibility into your harness (the tools you're using, the quality of your sessions, and more)

> **Why both Claude and Codex?** Flux works best with both a Claude and an OpenAI Codex subscription. During `/flux:impl-review` and `/flux:epic-review`, Flux uses the Codex CLI as an adversarial reviewer — a second model with different training data and biases that independently evaluates your plans and code. Multiple models reaching consensus catches blind spots that no single model finds alone. This is one of Flux's biggest advantages over single-model workflows.

### Deterministic State Engine

Flux now treats `.flux/` as the canonical workflow memory for the current repository.

- `session-state` tells Flux whether to prime first, start fresh, resume scoping, resume implementation, or route to review
- `scope-status` shows the active objective, current scoping phase, progress, and next action
- an active objective pointer keeps feature, bug, and refactor work anchored even across long sessions
- startup hooks and setup-installed agent instructions tell the agent to realign with Flux state before acting on new work-like requests

## Architecture

Flux is split into a few clear layers:

1. **Deterministic repo state** — `.flux/` stores tracked workflow data like objectives, epics, tasks, specs, memory, and config.
2. **Runtime coordination state** — shared runtime task state lives outside tracked repo files so multiple worktrees and agents can coordinate safely.
3. **Workflow control plane** — `fluxctl` is the single write path for workflow mutations, status inspection, validation, and routing.
4. **Agent interface layer** — slash commands and skills translate natural-language intent into deterministic Flux operations.
5. **Context acceleration layer** — Flux now includes a built-in `agentmap` implementation that generates YAML repo maps from git-tracked files, including README summaries and top-level definitions.

### Built-in Agentmap

Flux includes a built-in codebase mapping system.

- `fluxctl agentmap --check` reports built-in availability
- `fluxctl agentmap --write` writes `.flux/context/agentmap.yaml`
- the map is generated from git-tracked files only
- README files are included as high-signal project summaries
- file header comments, shebangs, and top-level definitions are used to improve agent startup context

The map is a navigation aid, not a source of truth. It helps fresh agents understand the repo faster, but it does not replace reading the code.

---

## Install Flux

> **⚠️ IMPORTANT:** If your agent uses slash commands, run them in the agent UI, not terminal bash.

### Agent-driven path (recommended)

```
Install Flux. Fetch the README at https://github.com/Nairon-AI/flux for install instructions.
```

The agent will detect your platform, install Flux, run setup, and prime the repo. You only step in when a platform command or restart is needed.

### Manual path (choose your platform)

Use the install path that matches your agent environment:

**Claude Code**
```
/plugin add https://github.com/Nairon-AI/flux@latest
```

**OpenCode**
- Use the [flux-opencode](https://github.com/Nairon-AI/flux-opencode) port.

Then:
1. Restart the agent/session if your platform requires it.
2. Let your agent complete Flux setup where supported.

After setup succeeds, restart once more if your platform loads plugins/prompts at session start.
After that, your agent should prime the repository automatically if needed, then route based on your intent.

### Upgrade Flux (existing users)

Use either:

```
/plugin update flux@nairon-flux
```

or:

```
/plugin add https://github.com/Nairon-AI/flux@latest
```

Then restart your agent/session and let the agent finish Flux setup.

## Uninstall Flux (complete removal)

### Agent-driven path (recommended)

```
Uninstall Flux. Fetch the README at https://github.com/Nairon-AI/flux for uninstall instructions.
```

### Manual path

For plugin-based agents, remove the Flux plugin from that agent first, then remove project-local state:

**Claude Code**
```
/plugin uninstall flux@nairon-flux
/plugin marketplace remove nairon-flux
```

If uninstall says plugin not found:

```
/plugin uninstall flux
```

Then run local cleanup:

```bash
# Plugin cache and marketplace metadata (Claude example)
rm -rf ~/.claude/plugins/cache/nairon-flux
rm -rf ~/.claude/plugins/marketplaces/nairon-flux

# Current project artifacts created by /flux:setup (run from project root)
rm -rf .flux

# Optional: remove user-level Flux data (all projects)
rm -rf ~/.flux
```

Restart your agent/session if needed and verify Flux is gone.

### First-Run Setup

On supported platforms, Flux performs a first-run setup step that scaffolds `.flux/` in your project and configures your preferences.

Your agent should handle this automatically after installation. If the platform requires a restart for new commands/prompts to load, restart once and let the agent continue.

Flux also ships with built-in agentmap support, so there is no separate `agentmap` install step during setup.

`/flux:setup` also offers optional, OS-aware productivity app installs:
- macOS: Superset, Ghostty, Raycast, Wispr Flow, Granola
- Linux: Ghostty
- Windows: Granola

These are optional, but recommended when relevant to your workflow.

### Prime Then Build

Prime is the first workflow step in a repository.

`/flux:prime` audits your codebase for agent readiness, finds inefficiencies, and surfaces what to improve before feature work begins. Flux now tracks whether prime has completed, so the agent can detect this automatically and run it first when needed.

After prime, you should not need to remember workflow commands. Just tell the agent what you want:
- build a feature
- fix a bug
- refactor something
- continue work

Flux should use repo state plus your message to decide whether to scope, resume implementation, review, or hand work off.

**Core pattern:** Prime first, then let Flux route the workflow based on intent. Use the command table below as a reference, not as the primary way to drive Flux.

### Optimize Your Workflow

Once you've been using Flux for a while, the agent can run improve to analyze your environment + sessions, detect inefficiencies, and recommend concrete workflow upgrades.

It can break down:
- what you do most frequently,
- what should become skills,
- what should become plugins,
- what should become autonomous agents,
- what belongs in `CLAUDE.md`.

### When to Use Each Command

| Situation | Command |
|-----------|---------|
| Starting a new feature or bug fix | `/flux:scope <description>` |
| Ready to work on a task | `/flux:work <task-id>` |
| Finished some code, want a sanity check | `/flux:impl-review` |
| Finished all tasks in an epic | `/flux:epic-review <epic-id>` |
| End of session, want to capture learnings | `/flux:reflect` |
| Codebase feels messy | `/flux:desloppify` |
| Audit codebase for agent readiness | `/flux:prime` |
| Want tool recommendations based on your patterns | `/flux:improve` |

### Troubleshooting

> **AI Agents**: If you're Claude Code debugging a Flux installation issue, follow this guide step-by-step. Do not guess — these are the verified fixes.

---

#### Problem: "Unknown skill: flux:setup"

**Cause**: The plugin is registered in `installed_plugins.json` but NOT enabled in `settings.json`. This happens when the install flow silently fails to add the `enabledPlugins` entry.

**Fix**:

```bash
# Step 1: Check if flux is enabled
cat ~/.claude/settings.json | grep -A2 enabledPlugins

# Step 2: If "flux@nairon-flux" is NOT listed, add it manually
# Open ~/.claude/settings.json and add to "enabledPlugins":
"flux@nairon-flux": true

# Step 3: Restart Claude Code
```

If the file is hard to edit, run this (backup first):
```bash
# Backup
cp ~/.claude/settings.json ~/.claude/settings.json.backup

# Add flux to enabledPlugins (requires jq)
jq '.enabledPlugins["flux@nairon-flux"] = true' ~/.claude/settings.json > tmp.json && mv tmp.json ~/.claude/settings.json
```

---

#### Problem: Agent tried to run `/plugin add` in bash (or `claude` inside Claude Code)

**Cause**: `/plugin` is a Claude Code slash command, not a shell command. Running `claude ...` inside an active Claude Code session is blocked (nested session).

**Fix**:

1. Run this directly in Claude Code chat input:
   ```
   /plugin add https://github.com/Nairon-AI/flux@latest
   ```
2. Restart Claude Code fully.
3. Run `/flux:setup`.

---

#### Problem: Commands still not working after enabling

**Cause**: Corrupted or stale cache from a previous install attempt.

**Fix**:

```bash
# Step 1: Clear ALL flux-related caches
rm -rf ~/.claude/plugins/cache/nairon-flux
rm -rf ~/.claude/plugins/marketplaces/nairon-flux

# Step 2: Restart Claude Code completely (not just the session)

# Step 3: Reinstall
/plugin add https://github.com/Nairon-AI/flux@latest

# Step 4: Restart Claude Code again (plugins load at session start)

# Step 5: Run setup
/flux:setup
```

---

#### Problem: Old version / missing new commands

**Cause**: Claude Code caches plugins aggressively. Even after updating, you might have an old version.

**Fix**:

```bash
# Step 1: Check current cached version
ls ~/.claude/plugins/cache/nairon-flux/flux/

# Step 2: Clear cache
rm -rf ~/.claude/plugins/cache/nairon-flux

# Step 3: Restart Claude Code and reinstall
/plugin add https://github.com/Nairon-AI/flux@latest

# Step 4: Verify new version loaded
/flux:status
```

---

#### Problem: Plugin shows in /plugin list but commands don't autocomplete

**Cause**: Plugin loaded but skills/commands not registered. Usually a restart issue.

**Fix**:

```bash
# Step 1: Fully quit Claude Code (not just close window)
# On Mac: Cmd+Q or right-click dock icon → Quit

# Step 2: Reopen Claude Code

# Step 3: Test
/flux:setup
```

---

#### Problem: "/plugin add" opens Discover tab instead of installing

**Cause**: On some Claude Code versions, URL installs open Discover. If no marketplace is configured yet, Discover may show "Add a marketplace first." 

**Fix** (most reliable):
1. Run `/plugin marketplace add https://github.com/Nairon-AI/flux`
2. Run `/plugin install flux@nairon-flux`
3. Restart Claude Code
4. Run `/flux:setup`

Or use the manual install method above (clear cache + reinstall).

---

#### Problem: Permission errors or "access denied"

**Cause**: File permission issues in the plugins directory.

**Fix**:

```bash
# Fix permissions
chmod -R u+rw ~/.claude/plugins/

# Then clear and reinstall
rm -rf ~/.claude/plugins/cache/nairon-flux
rm -rf ~/.claude/plugins/marketplaces/nairon-flux
```

---

#### Problem: Commands work but .flux/ directory not created

**Cause**: `/flux:setup` wasn't run, or it failed silently.

**Fix**:

```bash
# Run setup explicitly
/flux:setup

# If that fails, create manually and re-run
mkdir -p .flux
/flux:setup
```

---

#### Nuclear Option: Complete Reset

If nothing else works:

```bash
# Step 1: Remove ALL flux data
rm -rf ~/.claude/plugins/cache/nairon-flux
rm -rf ~/.claude/plugins/marketplaces/nairon-flux

# Step 2: Remove from installed plugins list
# Edit ~/.claude/plugins/installed_plugins.json
# Remove any entries containing "nairon-flux" or "flux"

# Step 3: Remove from enabled plugins
# Edit ~/.claude/settings.json
# Remove "flux@nairon-flux" from "enabledPlugins"

# Step 4: Restart Claude Code

# Step 5: Fresh install
/plugin add https://github.com/Nairon-AI/flux@latest

# Step 6: Restart Claude Code

# Step 7: Verify
/flux:setup
```

---

#### Still stuck?

1. Run `/flux:help` for command reference
2. Check `.flux/usage.md` in your project
3. Join [Discord](https://discord.gg/CEQMd6fmXk) — we respond fast
4. Open an issue: [GitHub Issues](https://github.com/Nairon-AI/flux/issues)

---

#### `/flux:scope` — The Guided Scoping Workflow

This is your starting point. Flux uses the deterministic state engine in `.flux/` to keep the agent aligned while it guides you through:

1. **Start**
   - classify feature, bug, or refactor
   - choose shallow vs deep
   - capture technical level and implementation target
   - realign with current `.flux/` state if work already exists

2. **Discover / Define**
   - understand why the work matters
   - surface blind spots and risks
   - converge to a defendable problem statement

3. **Develop / Deliver / Handoff**
   - shape the solution
   - create epic with sized tasks
   - route into `/flux:work` or engineer handoff
   - show scoping progress so you always know where you are

**Modes:**
```bash
/flux:scope Add notifications          # Shallow (~10 min) - compressed scoping
/flux:scope Add notifications --deep   # Deep (~45 min) - full staged workflow
/flux:scope Add notifications --explore 3  # Generate 3 competing approaches
```

`--explore` scaffolds multiple approaches in parallel (git worktrees), generates previews, and lets you compare before committing to one.

### Linear Integration (Optional)

Connect Flux to Linear for team workflows. Select a Linear project, scope it with the same Product OS-style shallow or deep flow, and create tasks directly in Linear.

```bash
/flux:scope --linear              # Browse teams → projects, select one to scope
/flux:scope LIN-42                # Scope specific Linear issue
/flux:scope PROJ-123 --deep       # Deep scope with Linear context
```

**What it does:**
1. Checks if Linear MCP is available (guides setup if not)
2. Lists teams → projects (Linear project = Flux epic)
3. Pulls project description, milestones, existing issues
4. Runs Product OS-style scoping with Linear context
5. Creates tasks in Linear with proper dependencies
6. Stores mapping in `.flux/epics/<id>/linear.json`

**Setup:** Requires [Linear MCP](https://linear.app/docs/mcp).

**Claude Code:**
- In chat, run `/mcp`
- Add server URL: `https://mcp.linear.app/mcp`
- Authenticate in the MCP dialog

If you prefer CLI, run this in an external terminal (not inside an active Claude Code chat session):
```bash
claude mcp add --transport http linear-server https://mcp.linear.app/mcp
```

**Other clients (Cursor, VS Code, Windsurf):**
```json
{
  "mcpServers": {
    "linear": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.linear.app/mcp"]
    }
  }
}
```

Full setup guide: https://linear.app/docs/mcp

<details>
<summary>Alternative: Skip interview, plan only</summary>

```bash
# If you already have a clear spec:
/flux:plan fn-1                          # ~5-15 min
```
</details>

### Find Better Tools

```bash
# Analyze your sessions, get personalized recommendations
/flux:improve

# Include community discoveries
/flux:improve --discover
```

### Clean Up Your Codebase

```bash
# Scan and systematically fix code quality issues
/flux:desloppify
```

Powered by [desloppify](https://github.com/peteromallet/desloppify) — a codebase quality scanner that combines mechanical detection (dead code, duplication, complexity) with LLM-based subjective review (naming, abstractions, architecture).

**Why it's different:** The scoring system is designed to resist gaming. You can't just suppress warnings — the only way to raise the score is to actually make the code better.

| Tier | What It Catches |
|------|-----------------|
| T1 | Auto-fixable: unused imports, debug logs |
| T2 | Quick manual: unused vars, dead exports |
| T3 | Judgment calls: near-dupes, single-use abstractions |
| T4 | Major refactors: god components, mixed concerns |

```bash
/flux:desloppify scan          # See your score
/flux:desloppify next          # Get next priority fix
/flux:desloppify status        # Track progress
```

Target: **95+ strict score** = codebase a senior engineer would respect.

That's it. Prime once, then Scope -> Build -> Review -> Improve. End sessions with Reflect. Keep the codebase clean. Repeat.

### Build Persistent Memory

Flux includes a **brain vault** — persistent memory that makes the agent smarter over time. Adapted from [brainmaxxing](https://github.com/poteto/brainmaxxing).

```bash
# After a session — capture what was learned
/flux:reflect

# Weekly — mine past conversations for patterns you missed
/flux:ruminate

# Monthly — prune stale notes, extract new principles
/flux:meditate
```

**What it does:**
- Mistakes don't repeat (they're captured via `/flux:reflect`)
- Codebase gotchas persist across sessions
- Engineering principles ground decisions (16 battle-tested principles included)
- Past conversations get mined for patterns you missed

The brain vault lives at `brain/` and is Obsidian-compatible. Session start automatically injects the brain index so the agent knows what knowledge is available.

### Secure by Design

Flux includes **STRIDE-based security analysis** to catch vulnerabilities during scoping and review. Adapted from [Factory AI security-engineer plugin](https://github.com/Factory-AI/factory-plugins).

```bash
# Generate threat model for your codebase
/flux:threat-model

# Scan code changes for vulnerabilities
/flux:security-scan PR #123

# Full security review with validation
/flux:security-review --mode full
```

**What it catches:**
- SQL injection, XSS, command injection (Tampering)
- Authentication bypass, session hijacking (Spoofing)
- IDOR, hardcoded secrets, data leaks (Information Disclosure)
- Missing auth checks, privilege escalation (Elevation of Privilege)
- Missing rate limits, resource exhaustion (Denial of Service)
- Missing audit logs (Repudiation)

Security findings are validated for exploitability with proof-of-concept generation. False positives are filtered automatically.

> **You can stop reading here.** Everything below is optional deep-dives.

---

## How `/flux:improve` Works

Flux analyzes your **actual coding sessions** to find friction—then recommends specific tools that would help.

### What It Detects

| Signal | What It Means |
|--------|---------------|
| `shallow_prompts` | "Implement this" without context |
| `blind_acceptance` | Never disagreeing with AI suggestions |
| `no_docs_lookup` | Relying on outdated training data |
| `undo_loops` | AI producing slop, needs better planning |
| `memory_loss` | Context not persisting across sessions |

### What It Recommends

A curated database of **battle-tested solutions** mapped to your specific friction:

| Category | Examples |
|----------|----------|
| **MCP Servers** | Context7 (live docs), Nia (repo research), Supermemory (persistence) |
| **Skills** | Workflow templates, prompt libraries |
| **CLI Tools** | Lefthook (git hooks), Beads (task tracking) |
| **Workflows** | Clarify-first, test-driven-prompting |

Browse or contribute: **[flux-recommendations](https://github.com/Nairon-AI/flux-recommendations)**

### Example Output

```
Friction Patterns Detected:
━━━━━━━━━━━━━━━━━━━━━━━━━━

  shallow_prompts (8 occurrences)
     Prompts lack sufficient context for quality responses.

  no_docs_lookup (5 occurrences)
     Not consulting documentation before implementation.

Recommended Improvements:
━━━━━━━━━━━━━━━━━━━━━━━━

  1. Context7 MCP Server
     ├─ Fetches live, version-specific documentation
     └─ Addresses: no_docs_lookup

  2. prompt-templates skill
     ├─ Pre-built templates for common tasks
     └─ Addresses: shallow_prompts

Would you like me to install any of these?
```

The agent handles installation. You just say "yes."

---

## The Vision

### For Individual Engineers

Get better at AI collaboration through data, not vibes.

> "Your sessions are 40% shallower than top performers. They disagree with AI suggestions 3x more often. Here's what to install to close the gap."

### For Teams

- Who's actually leveraging AI effectively
- Where the team needs skill development
- Which workflows produce the highest quality output
- Share your entire setup with new engineers for instant 10x onboarding

### For Engineering Leaders (Coming Soon)

CTO-level observability:
- Team benchmarks and improvement trends
- Quality-of-thinking metrics (not just velocity)
- Recruiting signals: "This candidate demonstrates sophisticated AI collaboration patterns"

---

## Commands

| Command | What it does |
|---------|--------------|
| `/flux:setup` | Initialize Flux in your project |
| `/flux:scope <idea>` | **Guided scoping workflow** — staged interview, progress, and handoff (`--deep`, `--explore N`, `--linear`) |
| `/flux:plan <idea>` | Create tasks only (skip problem space interview) |
| `/flux:work <task>` | Execute task with context reload |
| `/flux:sync <epic>` | Sync specs after drift |
| `/flux:impl-review` | Implementation review |
| `/flux:epic-review <epic>` | Verify epic completion |
| `/flux:prime` | Codebase readiness audit (8 pillars, 48 criteria) |
| `/flux:desloppify` | Systematic code quality improvement (scan → fix loop) |
| `/flux:improve` | Analyze sessions, recommend tools |
| `/flux:reflect` | Capture learnings from current session into brain vault |
| `/flux:ruminate` | Mine past conversations for uncaptured patterns |
| `/flux:meditate` | Audit and prune brain vault, extract new principles |
| `/flux:threat-model` | Generate STRIDE-based security threat model |
| `/flux:security-scan` | Scan code changes for security vulnerabilities |
| `/flux:security-review` | Comprehensive security review with STRIDE analysis |
| `/flux:vuln-validate` | Validate findings and generate proof-of-concept |
| `/flux:score` | Compute AI-native capability score |
| `/flux:profile` | Export/share SDLC profile |
| `/flux:contribute` | Report bug and auto-create PR to fix Flux |

Full reference: `docs/commands-reference.md`

---

## Prerequisites

| Requirement | Install |
|-------------|---------|
| Python 3.9+ | `brew install python` / `apt install python3` |
| jq | `brew install jq` / `apt install jq` |
| git | Usually pre-installed |

Flux checks for these during execution and tells you what's missing.

---

## FAQ

**What data does Flux read?**
- Repo structure (package.json, configs)
- Installed MCPs from `~/.mcp.json`
- Optionally: Claude Code session files (with consent)

**Is any data sent externally?**
Analysis runs locally. Network only used to fetch recommendations repo.

**Where do recommendations come from?**
[Nairon-AI/flux-recommendations](https://github.com/Nairon-AI/flux-recommendations) — 30+ curated tools, community-driven.

**Can I use Flux with Beads?**
Not recommended. Both are task tracking systems — Flux uses `.flux/` + `fluxctl`, Beads uses `.beads/` + `bd`. Having both in your AGENTS.md will confuse the agent about which to use. Pick one:
- **Flux** if you want the full workflow (scope → plan → work → review)
- **Beads** if you just want lightweight issue tracking

If migrating from Beads: remove the beads section from AGENTS.md and run `/flux:setup`.

---

## Philosophy

1. **AI amplifies your skill level, it doesn't replace it.** A mediocre engineer with AI is still mediocre.

2. **Disagreement is a feature.** The best AI collaborators push back constantly.

3. **Process beats raw talent.** Structured approach > vibes-based prompting.

4. **What gets measured gets improved.** You can't fix what you can't see.

5. **The agent should do the work.** Analysis, installation—AI handles it. You decide.

---

## Feature Roadmap

Upcoming enhancements to core commands:

| Command | Enhancement | Description |
|---------|-------------|-------------|
| `/flux:work` | Git worktree support | Isolate task work in separate worktrees for parallel development and clean rollbacks |
| `/flux:scope` | Transcript ingestion | Ingest meeting transcripts, auto-detect affected issues, ask clarifying questions, update task details |

Want to contribute? Check out the [issues](https://github.com/Nairon-AI/flux/issues) or join the [Discord](https://discord.gg/CEQMd6fmXk).

---

## Roadmap: Universe Integration

Flux will sync to [Nairon Universe](https://nairon.ai/universe) — a public portal for AI-native engineers.

**Public Profile (visible to others):**
| Data | Example |
|------|---------|
| Sessions | "350 sessions with Claude Code" |
| Tokens | "15M tokens used this month" |
| Tools | MCP servers, skills, CLI tools you use |
| Activity | Recent projects, contributions |

**Private Dashboard (for you):**
| Data | What It Shows |
|------|---------------|
| AI-Native Score | Your grade across 5 dimensions |
| Radar Chart | Interview depth, pushback ratio, prompt quality, iteration efficiency |
| Trends | How you're improving over time |

**Why this matters:** When you follow an engineer on Universe, you can see exactly what tools they use and how they work with AI. No more guessing — just copy what works.

*Status: Coming Q2 2026. Auth will use Universe accounts.*

---

## Community

No hype. No AI slop. Just practical discussions on becoming the strongest developers alive.

[discord.gg/CEQMd6fmXk](https://discord.gg/CEQMd6fmXk)

---

## Docs

- `docs/commands-reference.md` — Full command reference
- `docs/architecture.md` — How Flux works internally
- `docs/troubleshooting.md` — Common issues and fixes

---

## License

MIT

---

<p align="center">
  <em>Stop hoping AI makes you better. Start measuring it.</em>
</p>
