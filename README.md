<div align="center">

# Flux

[![Discord](https://img.shields.io/badge/Discord-Join-5865F2?logo=discord&logoColor=white)](https://discord.gg/CEQMd6fmXk)
[![Version](https://img.shields.io/badge/version-v1.9.1-green)](https://github.com/Nairon-AI/flux/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Plugin-blueviolet)](https://claude.ai/code)

**Your AI workflow has gaps. Flux finds them.**

</div>

---

### Platform Compatibility

| Platform | Status | Install |
|----------|--------|---------|
| [Claude Code](https://claude.ai/code) | ✅ Recommended | `/plugin add https://github.com/Nairon-AI/flux@latest` |
| [Factory Droid](https://factory.ai) | ✅ Supported | `droid plugin marketplace add https://github.com/Nairon-AI/flux` |
| [OpenAI Codex](https://openai.com/index/introducing-codex/) | ✅ Supported | `git clone` + `./scripts/install-codex.sh flux` |
| [OpenCode](https://github.com/anomalyco/opencode) | `[██████████░] 96%` | [flux-opencode](https://github.com/Nairon-AI/flux-opencode) |

---

## The Problem

You're using Claude Code, but something's off:

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

**Flux gives you three things:**

1. **A structured workflow** — Scope → Build → Review
2. **Continuous improvement** — Analyze your sessions, detect optimisations, install them to improve your agent and your Agentic workflow
3. **Observability** — Tap into your entire worklow to get full visibility into your harness (the tools you're using, the quality of your sessions, and and more)

---

## Recommended Installation

### Step 1: Install

> **⚠️ IMPORTANT:** The install command is `/plugin add` (NOT `/install`). Type it exactly as shown below.
>
> Slash commands run in Claude Code chat input, not in a terminal shell. Do **not** run `/plugin add` via Bash.

**Option A:** Run this slash command directly in Claude Code:

```
/plugin add https://github.com/Nairon-AI/flux@latest
```

> **Note:** If you have an older version cached, clear it first: `rm -rf ~/.claude/plugins/cache/nairon-flux`

**Option B:** Paste this prompt and let the agent guide you:

```
I want to install Flux for structured AI development.
The plugin is at: https://github.com/Nairon-AI/flux

Help me install and setup the plugin.

Then explain the core workflow (scope → build → review).

The install command is: /plugin add https://github.com/Nairon-AI/flux@latest

Do NOT run /plugin add in bash or via `claude plugin add` inside this active Claude session.
When a manual slash command is needed, ask me to run exactly:
/plugin add https://github.com/Nairon-AI/flux@latest
I will run it in this Claude chat and reply "done".

After I reply "done", continue automatically:
1) Verify Flux commands are available.
2) Run /flux:setup (or load the flux-setup skill and execute setup workflow).
3) If setup is unavailable, tell me to restart Claude Code once, then continue setup.

Guide me on anything I need to do manually and do the rest automatically.
```

### Claude Code Agent Execution Rules

- **Human runs in chat input:** `/plugin add ...` and any UI auth steps (for example `/mcp` sign-in dialogs).
- **Agent runs automatically:** repository checks, shell commands, config/file updates, and the full `/flux:setup` workflow after install is confirmed.
- **Agent must not do:** run `/plugin add` in bash, run `claude plugin add` from inside an active Claude Code session, or stop after saying "installed" without setup.
- **Completion criteria:** install confirmed, `/flux:setup` completed, and core workflow commands explained (`/flux:scope -> /flux:work -> /flux:impl-review`).

### Upgrading (Existing Users)

Use the same command as install (always targets latest):

```
/plugin add https://github.com/Nairon-AI/flux@latest
```

Then:
1. Restart Claude Code fully
2. Run `/flux:setup` to refresh local scripts/docs
3. Continue with `/flux:scope` or `/flux:work`

### Step 2: Setup

After installation, **restart Claude Code** (plugins load at session start), then run:

```bash
/flux:setup
```

This scaffolds `.flux/` in your project and configures your preferences.

### Project-Only Install Smoke Test (Local)

Want to verify Flux installs only inside one local repo? Use a throwaway test repo:

1. Create test repo on desktop (for example `~/Desktop/flux-install-smoke-test`)
2. Open it in Claude Code
3. Run `/plugin add https://github.com/Nairon-AI/flux@latest`
4. Run `/flux:setup` and choose **Project** install scope
5. Verify only that repo now contains `.flux/` (for example `.flux/bin/fluxctl`, `.flux/meta.json`, `.flux/usage.md`)
6. Delete the test repo when done

This is the safest way to validate project-scoped setup end-to-end before onboarding a real codebase.

### Step 3: Build Your First Feature

Once setup completes, you're ready. Start with:

```bash
/flux:scope Add user notifications
```

This runs the **Double Diamond** process:
1. **Problem Space** — Flux interviews you: *What are we really solving? Who's affected? What are the risks?*
2. **Solution Space** — Researches your codebase, then creates a sized epic with tasks (e.g., `fn-1.1`, `fn-1.2`)

Then execute and review:

```bash
/flux:work fn-1.1          # Execute first task with full context
/flux:work fn-1.2          # Next task

/flux:impl-review          # Review implementation before moving on
/flux:epic-review fn-1     # Verify the epic is complete
```

**That's the core loop: Scope → Build → Review.** Repeat for every feature.

### Step 4: Optimize Your Workflow

Once you've been using Flux for a while, run:

```bash
/flux:improve
```

This analyzes your sessions to detect friction patterns (shallow prompts, blind acceptance, no docs lookup) and recommends specific tools, MCPs, and workflow changes to close the gaps.

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

**Cause**: This is Claude Code's default behavior for marketplace URLs.

**Fix**: This is expected. From the Discover tab:
1. Find "flux" in the list
2. Click Install
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

#### `/flux:scope` — The Double Diamond

This is your starting point. It guides you through:

1. **Problem Space** — WHY are we building this?
   - Core desire, reasoning validation, user perspective
   - Surface blind spots and risks
   - Converge to clear problem statement

2. **Solution Space** — HOW should we build it?
   - Research codebase patterns
   - Create epic with sized tasks

**Modes:**
```bash
/flux:scope Add notifications          # Quick (~10 min) - MVP focus
/flux:scope Add notifications --deep   # Deep (~45 min) - thorough scoping
/flux:scope Add notifications --explore 3  # Generate 3 competing approaches
```

`--explore` scaffolds multiple approaches in parallel (git worktrees), generates previews, and lets you compare before committing to one.

### Linear Integration (Optional)

Connect Flux to Linear for team workflows. Select a Linear project, scope it with Double Diamond, and create tasks directly in Linear.

```bash
/flux:scope --linear              # Browse teams → projects, select one to scope
/flux:scope LIN-42                # Scope specific Linear issue
/flux:scope PROJ-123 --deep       # Deep scope with Linear context
```

**What it does:**
1. Checks if Linear MCP is available (guides setup if not)
2. Lists teams → projects (Linear project = Flux epic)
3. Pulls project description, milestones, existing issues
4. Runs Double Diamond scoping with Linear context
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

That's it. Scope → Build → Review → Improve → Clean. Repeat.

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
| `/flux:scope <idea>` | **Double Diamond scoping** — interview + plan (`--deep`, `--explore N`, `--linear`) |
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
