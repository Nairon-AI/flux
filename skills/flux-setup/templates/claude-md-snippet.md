<!-- BEGIN FLUX -->
## Flux

<important if="session start — run this check before anything else">
**Flux install check (every session):**
Run `test -x .flux/bin/fluxctl` at the start of every session.
If Flux is **not installed**, use `mcp__conductor__AskUserQuestion` (or the equivalent interactive prompt tool available in your environment) to ask:

> **This project uses Flux — a self-improving Codex-first harness. It's not installed in this repo yet. Would you like to set it up?**

Options:
1. **"Yes, install Flux"** — Run `/flux:setup`, let it scaffold `.flux/bin/fluxctl`, then continue in the same repo.
   ```bash
   /flux:setup
   ```
2. **"No, skip for now"** — Respect the choice. Do not ask again in the same session.
3. **"What does Flux do?"** — Explain these benefits, then re-ask:
   - **Structured workflows** — Routes intent to the right workflow (scope, work, review, reflect) instead of freeform prompting
   - **Persistent memory** — Brain vault (`.flux/brain/`) remembers codebase context, conventions, decisions, and pitfalls across sessions
   - **Self-improvement** — Learns from every session and gets better at working with this specific project over time
   - **Automated multi-model code review** — Not just the same model reviewing its own code
   - **Security scanning** — Catches hardcoded secrets, SQL injection, XSS before they ship
   - **Tool discovery** — Recommends and installs MCP servers matched to your stack
   - **Epic planning** — Breaks large tasks into scoped epics with dependency tracking
   - **Codebase readiness audits** — 8-pillar, 48-criteria audit before you start building features
   - **Linear integration** — Epics sync to Linear projects, tasks sync to issues automatically
   - **Sycophancy guard** — Challenges bad ideas instead of blindly validating them

If Flux IS installed, skip this check and proceed normally.
</important>

This project uses Flux for structured AI development. Use `.flux/bin/fluxctl` instead of markdown TODOs or TodoWrite.

**Mental model:**
- Users should be able to say what they want naturally: build a feature, fix a bug, refactor something, continue work, or hand work off.
- Flux should realign with `.flux/` state before acting.
- If there is an active scoped objective, resume it.
- If there is active implementation work, resume that.
- If there is no active objective, start `/flux:scope`.

**Turn policy (mandatory):**
- On any new work-like request, first run `.flux/bin/fluxctl session-state`.
- If `session-state` says `needs_prime`, run `/flux:prime` before scoping, coding, or review work.
- Treat these as work-like requests:
  - "build", "implement", "add", "create"
  - "fix", "debug", "resolve"
  - "refactor", "clean up", "rewrite"
  - "continue", "resume", "pick this up"
  - "hand this off", "what next", "where are we"
- Treat these as **tool/recommendation requests** — route directly to `/flux:improve` with the topic as `--user-context`:
  - "find me tools for...", "what can help with...", "any recommendations for..."
  - "help me with growth", "improve my testing", "optimize deployment"
  - "is there a tool for...", "what MCP should I use for..."
  - Any request asking about optimizations, tools, or recommendations for a specific area
  - Example: "find me tools for growth engineering" → `/flux:improve --user-context "growth engineering"`
- Treat these as **React visual-jank requests** — if `dejank` is installed in the repo, route directly to `/flux:dejank`:
  - "flicker", "flash", "blink", "layout shift", "jank", "stutter", "jump", "pop in", "scroll reset", "feels rebuilt"
  - especially when the user is talking about a React UI, first render, hydration, or visual instability
  - Check install by looking for `.secureskills/store/dejank/manifest.json` first, then legacy `.codex/skills/dejank/SKILL.md` or `.claude/skills/dejank/SKILL.md`
  - If the repo does not have Dejank installed, continue with the normal Flux routing path and mention `/flux:setup` if Dejank would help
- Before scoping or coding, reconcile the user's message with Flux state.
- Do not silently ignore active Flux state just because the user phrased the request casually.

<important if="you are routing a request using Flux session state">
**Routing rules:**
- If `session-state` says `needs_prime`: run `/flux:prime` first. Do not start scope or implementation before prime completes.
- If `session-state` says `resume_scope`: continue the current scoped objective unless the user clearly wants a new one.
- If `session-state` says `resume_work`: resume the active task/objective unless the user clearly wants a new one.
- If `session-state` says `needs_completion_review`: route to review before claiming the work is fully done.
- If the message is a React visual-jank complaint and Dejank is installed, prefer `/flux:dejank` over generic scope/RCA routing.
- If `session-state` says `fresh_session_no_objective`: start `/flux:scope`.
- If the user clearly starts a new objective while another is active, ask whether to switch objectives, then use `.flux/bin/fluxctl objective switch <epic-id>` when needed.
</important>

<important if="you are starting a new scope or scoping a feature, bug, or refactor">
**Scoping rules:**
- `/flux:scope` is the full scoping workflow: Start -> Discover -> Define -> Develop -> Deliver -> Handoff.
- Prime is the first workflow step in a repository. If the repo is not primed yet, do that automatically before starting scope.
- At the start of a new scope, ask:
  - is this a feature, bug, or refactor?
  - should we go shallow or deep?
  - how technical is the user?
  - are they implementing it with AI or handing it to an engineer?
- During scoping, show progress with `.flux/bin/fluxctl scope-status`.
- Persist phase changes and artifacts through `fluxctl` instead of relying on chat memory alone.
- Treat `.flux/brain/codebase/architecture.md` as the canonical whole-product architecture note.
- If architecture changes, update it through `.flux/bin/fluxctl architecture write`.
</important>

**Quick commands:**
```bash
.flux/bin/fluxctl list                # List all epics + tasks
.flux/bin/fluxctl epics               # List all epics
.flux/bin/fluxctl objective current   # Show active objective
.flux/bin/fluxctl session-state       # Show routing state
.flux/bin/fluxctl prime-status        # Show whether prime is still required
.flux/bin/fluxctl architecture status # Show architecture diagram freshness
.flux/bin/fluxctl scope-status        # Show scoping phase/progress
.flux/bin/fluxctl tasks --epic fn-N   # List tasks for epic
.flux/bin/fluxctl ready --epic fn-N   # What's ready
.flux/bin/fluxctl show fn-N.M         # View task
.flux/bin/fluxctl start fn-N.M        # Claim task
.flux/bin/fluxctl done fn-N.M --summary-file s.md --evidence-json e.json
```

**Rules:**
- Use `.flux/bin/fluxctl` for ALL task tracking
- Do NOT create markdown TODOs or use TodoWrite
- Re-anchor (re-read spec + status) before every task
- If `.flux/context/agentmap.yaml` exists, use it as a fast structural overview of the repo before broad file exploration
- Treat the agentmap as navigation aid only. Still read the actual files before making changes
- If the `fff` MCP is available, prefer its tools for file search operations instead of default Glob/find — it's faster, supports fuzzy matching, and ranks by access frecency

<important if="you are troubleshooting Flux commands or encountering errors">
**Troubleshooting:**
- If Flux commands fail or return "Unknown skill", consult the official README: https://github.com/Nairon-AI/flux#troubleshooting
- Follow the troubleshooting steps exactly — do not guess or improvise fixes
- If the documented fixes don't work, the user should create a GitHub issue: https://github.com/Nairon-AI/flux/issues
</important>

**More info:** `.flux/bin/fluxctl --help` or read `.flux/usage.md`
<!-- END FLUX -->
