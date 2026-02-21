# Flux

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Plugin-blueviolet)](https://claude.ai/code)

> Structure your AI coding sessions. Ship faster, forget less.

## What is Flux?

Flux is a workflow engine for Claude Code that enforces a simple discipline: **plan before you code**. 

Every feature gets broken into trackable tasks stored in `.flux/`. Every task re-anchors to the plan before execution. Nothing slips through the cracks.

## Get Started

```bash
/plugin marketplace add Nairon-AI/flux
/plugin install flux@nairon-flux
/flux:setup
```

Then start building:

```bash
/flux:plan Add user authentication with OAuth
/flux:work fx-1
```

## Core Commands

| Command | What it does |
|---------|--------------|
| `/flux:plan` | Break a feature into dependency-aware tasks |
| `/flux:work` | Execute a task with automatic context reload |
| `/flux:prime` | Analyze codebase before planning |
| `/flux:interview` | Refine requirements through Q&A |
| `/flux:setup` | Initialize flux in your project |

## How Flux Solves Common AI Coding Problems

**Context gets lost mid-session?**  
Flux re-reads `.flux/` specs and git state before every task. You always start with the right context.

**Token limits force you to start fresh?**  
Each task runs in a clean subagent. Long projects don't mean degraded quality.

**AI forgets what it already built?**  
Tasks declare dependencies. Flux won't let you build step 3 before step 2 is done.

**Debugging "what changed"?**  
Every task logs commits, test results, and PR links. Full traceability.

**Stuck in retry loops?**  
Tasks auto-block after N failed attempts. Flux moves on, you unblock later.

**Multiple devs, same codebase?**  
Scan-based IDs and soft claims. No coordination server needed.

## Staying Updated

**Auto-update (recommended):**
```
/plugin → Marketplaces tab → nairon-flux → Enable auto-update
```

**Manual update:**
```bash
/plugin marketplace update nairon-flux
```

Flux commands also check for updates automatically and notify you when a new version is available.

## Docs

Full documentation: [docs.nairon.ai/flux](https://docs.nairon.ai/flux) *(coming soon)*

## Community

Join the most AI-native developer community on the planet. No hype. No AI slop. Just practical discussions on becoming the strongest developers alive.

[discord.gg/nairon](https://discord.gg/nairon) *(coming soon)*

## License

MIT
