# Agent Compatibility Guide

Flux skills work across multiple AI coding agents. This guide documents differences to handle.

## Question Tools

Different agents have different tools for asking users questions:

| Agent | Tool Name | Notes |
|-------|-----------|-------|
| **Claude Code** | `AskUserQuestion` | Supports options, multiple questions |
| **OpenCode** | `mcp_question` | MCP-based, similar to Claude Code |
| **Codex** | `AskUserTool` | Simpler interface |
| **Cursor** | (text output) | No structured question tool |
| **Windsurf** | (text output) | No structured question tool |

## Detection

Detect which agent is running via environment variables:

```bash
# Claude Code
[[ -n "$CLAUDE_PLUGIN_ROOT" ]] && AGENT="claude"

# OpenCode (Droid)
[[ -n "$DROID_PLUGIN_ROOT" ]] && AGENT="opencode"

# Codex
[[ -n "$CODEX_HOME" ]] && AGENT="codex"

# Fallback
AGENT="${AGENT:-unknown}"
```

## Skill Instructions

When writing skills that need user input, use this pattern:

```markdown
**Ask the user using the appropriate question tool:**
- Claude Code: `AskUserQuestion`
- OpenCode: `mcp_question`  
- Codex: `AskUserTool`
- Other agents: Output the question as text and wait for response

Question: "[Your question here]"
Options (if applicable):
- Option A: [description]
- Option B: [description]
```

## Plugin Root

Different agents use different env vars for plugin location:

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-${CODEX_SKILLS_DIR}}}"
```

## Agent-Specific Behaviors

### Claude Code
- Has `Task` tool for spawning subagents
- Uses `CLAUDE.md` for instructions
- Supports `AskUserQuestion` with rich options

### OpenCode
- Has `mcp_task` for spawning subagents
- Uses `AGENTS.md` for instructions
- Supports `mcp_question` with similar interface

### Codex
- Has multi-agent roles (0.102.0+)
- Uses `AGENTS.md` for instructions
- Simpler `AskUserTool` interface
- Sandbox restrictions may apply

### Cursor / Windsurf
- No subagent spawning
- Uses `AGENTS.md` or `.cursorrules`
- Output questions as text, wait for user response

## Writing Portable Skills

1. **Question tools**: Reference this guide, don't hardcode one tool name
2. **Subagents**: Check if Task/mcp_task available before spawning
3. **Plugin paths**: Use fallback chain for env vars
4. **Instructions file**: Mention both CLAUDE.md and AGENTS.md patterns
