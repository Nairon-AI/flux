# Agent Compatibility Guide

Flux skills work across multiple AI coding agents. This guide documents differences to handle.

## Question Tools

Different agents have different tools for asking users questions:

| Agent | Tool Name | Notes |
|-------|-----------|-------|
| **Codex** | `AskUserTool` | Primary target |
| **OpenCode** | `mcp_question` | MCP-based structured prompts |
| **Claude** | `AskUserQuestion` | Secondary compatibility and review-only workflows |
| **Cursor** | (text output) | No structured question tool |
| **Windsurf** | (text output) | No structured question tool |

## Detection

Detect which agent is running via environment variables:

```bash
# Codex
[[ -n "$CODEX_HOME" ]] && AGENT="codex"

# OpenCode (Droid)
[[ -n "$DROID_PLUGIN_ROOT" ]] && AGENT="opencode"

# Claude
[[ -n "$CLAUDE_PLUGIN_ROOT" ]] && AGENT="claude"

# Fallback
AGENT="${AGENT:-unknown}"
```

Flux also exposes the same decision through runtime diagnostics:

```bash
.flux/bin/fluxctl env --json
```

Prefer `fluxctl env` or `fluxctl doctor` when you need install/update/troubleshooting behavior, because they also report which version is authoritative and whether the current host adapter is in sync.

## Skill Instructions

When writing skills that need user input, use this pattern:

```markdown
**Ask the user using the appropriate question tool:**
- Codex: `AskUserTool`
- OpenCode: `mcp_question`
- Claude: `AskUserQuestion`
- Other agents: Output the question as text and wait for response

Question: "[Your question here]"
Options (if applicable):
- Option A: [description]
- Option B: [description]
```

## Plugin Root

Different agents use different env vars for plugin location:

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
```

## Agent-Specific Behaviors

### Codex
- Has multi-agent roles (0.102.0+)
- Uses `AGENTS.md` for instructions
- Simpler `AskUserTool` interface
- Sandbox restrictions may apply

### OpenCode
- Has `mcp_task` for spawning subagents
- Uses `AGENTS.md` for instructions
- Supports `mcp_question` with similar interface

### Claude
- Keep only for secondary compatibility, adversarial review, or optional auto-fix flows
- Supports `AskUserQuestion` with rich options
- Reads `CLAUDE.md` if present

### Cursor / Windsurf
- No subagent spawning
- Uses `AGENTS.md` or `.cursorrules`
- Output questions as text, wait for user response

## Writing Portable Skills

1. **Question tools**: Reference this guide, don't hardcode one tool name
2. **Subagents**: Check if Task/mcp_task available before spawning
3. **Plugin paths**: Use fallback chain for env vars
4. **Instructions file**: Prefer `AGENTS.md`; mention `CLAUDE.md` only as legacy/secondary compatibility
