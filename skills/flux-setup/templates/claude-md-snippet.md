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
- Treat these as **memory capture requests** — route directly to `/flux:remember`:
  - "remember ...", "don't forget ...", "keep in mind ...", "from now on ..."
  - "always ..." / "never ..." when the user is setting an ongoing rule, not asking a question
- Treat these as **task management requests** — route to the `flux` skill:
  - "what's the status", "show me my tasks", "list epics", "what's ready", "show fn-1"
- Treat these as **Flux config requests** — route to the `flux` skill:
  - "show my Flux config", "what did setup configure", "show Flux settings", "edit Flux settings"
  - When the user wants to inspect config, prefer `.flux/bin/fluxctl config list`
  - When the user wants to change several settings interactively, prefer `.flux/bin/fluxctl config edit`
- Treat these as **React visual-jank requests** — if `dejank` is installed in the repo, route directly to `/flux:dejank`:
  - "flicker", "flash", "blink", "layout shift", "jank", "stutter", "jump", "pop in", "scroll reset", "feels rebuilt"
  - especially when the user is talking about a React UI, first render, hydration, or visual instability
  - Check install by looking for `.secureskills/store/dejank/manifest.json` first, then legacy `.codex/skills/dejank/SKILL.md` or `.claude/skills/dejank/SKILL.md`
  - If the repo does not have Dejank installed, continue with the normal Flux routing path and mention `/flux:setup` if Dejank would help
- Treat these as **codebase understanding requests** — if `diffity-tour` is installed in the repo, route directly to `/diffity-tour`:
  - "how does this work", "walk me through auth", "help me understand the billing flow", "show me what touches checkout"
  - especially when the user wants a guided explanation of an existing feature, subsystem, codepath, or cross-cutting behavior
  - Do not use this route when the user is clearly asking you to change or build something rather than understand it
  - Check install by looking for `.secureskills/store/diffity-tour/manifest.json` first, then legacy `.codex/skills/diffity-tour/SKILL.md` or `.claude/skills/diffity-tour/SKILL.md`
  - If the repo does not have Diffity Tour installed, continue with the normal Flux routing path and mention `/flux:setup` if Diffity Tour would help
- Treat these as **specialist workflow requests** — route directly instead of making the user rephrase:
  - "grill me", "stress test the behavior", "verify behavior" → `/flux:grill`
  - "TDD", "test first", "red green refactor" → `/flux:tdd`
  - "design the interface", "design it twice", "compare interfaces" → `/flux:design-interface`
  - "ubiquitous language", "define terms", "domain glossary", "DDD" → `/flux:ubiquitous-language`
  - "export this for ChatGPT", "external LLM review", "review this with Claude web" → `/flux:export-context`
  - "watch this PR", "auto-fix", "babysit this PR", "fix CI after submit" → `/flux:autofix`
  - "validate staging", "promote staging", "ship staging to production" → `/flux:gate`
  - "cut a release", "publish Flux vX.Y.Z", "release this version" → `/flux:release`
  - "improve CLAUDE.md", "restructure AGENTS.md", "add important if blocks" → `/flux:improve-claude-md`
  - "share my Flux setup", "export a profile", "import a profile" → `/flux:profile`
  - "build me a skill", "create a skill for...", "scaffold a skill" → `/flux:skill-builder`
  - "upgrade Flux", "update the plugin" → `/flux:upgrade`
  - "report a Flux bug", "contribute a fix to Flux" → `/flux:contribute`
- Before scoping or coding, reconcile the user's message with Flux state.
- Do not silently ignore active Flux state just because the user phrased the request casually.

<important if="you are routing a request using Flux session state">
**Routing rules:**
- If `session-state` says `needs_prime`: run `/flux:prime` first. Do not start scope or implementation before prime completes.
- If the user is explicitly trying to remember a repo rule or durable fact, prefer `/flux:remember` over scoping.
- If `session-state` says `resume_scope`: continue the current scoped objective unless the user clearly wants a new one.
- If `session-state` says `resume_work`: resume the active task/objective unless the user clearly wants a new one.
- If `session-state` says `needs_completion_review`: route to review before claiming the work is fully done.
- If the message is a React visual-jank complaint and Dejank is installed, prefer `/flux:dejank` over generic scope/RCA routing.
- If the user asks how an existing feature or subsystem works and Diffity Tour is installed, prefer `/diffity-tour` over generic scoping as long as they are not asking for code changes yet.
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

<important if="you are building, redesigning, or restyling a user-facing frontend">
**Frontend rules:**
- If project-local frontend skills exist, you MUST load and follow them before making UI changes. Check `.secureskills/store/<skill>/manifest.json` first, then `.codex/skills/`, then `.claude/skills/` mirrors.
- Treat `taste-skill` as mandatory for frontend generation when present.
- Treat installed UI skills as mandatory guardrails when present. At minimum, load `baseline-ui`; also load `fixing-accessibility`, `fixing-motion-performance`, and `fixing-metadata` when the task touches those concerns.
- If the repo has substantive frontend work to do and these skills are missing, strongly recommend running `/flux:setup` to install `UI Skills` and `Taste Skill` before large UI changes.
- Define the design system and constraints before coding: typography, color roles/tokens, spacing rhythm, image treatment, and the primary CTA.
- Treat the first viewport as one composition, not a pile of cards. On branded pages, make the brand/product a hero-level signal.
- On landing or promo pages, default to one H1, one short supporting sentence, one CTA group, and one dominant visual. Prefer a full-bleed hero image/background over inset media cards unless the existing design system clearly says otherwise.
- Avoid generic UI patterns by default: weak visual hierarchy, flat single-color backgrounds, hero cards, floating badges on hero media, and card-heavy layouts where borders/backgrounds are not doing real interaction work.
- Use real visual anchors and 2-3 intentional motions. Motion should create hierarchy or presence, not noise.
- Preserve the existing design system when the repo already has one. Only push for bolder visual direction when the surface is actually being designed or refreshed.
- Verify user-facing frontend work in a browser before calling it done. Check desktop and mobile layouts, ensure fixed/floating elements do not cover primary content, and confirm the final UI matches the scoped design intent.
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
- In Flux quality/review passes for React repos, run `react-doctor` on the current diff when available. Prefer an installed `react-doctor` binary; otherwise use `npx -y react-doctor@latest . --diff HEAD --fail-on error`. This complements `/flux:dejank`; it does not replace the jank-specific workflow.

<important if="you are troubleshooting Flux commands or encountering errors">
**Troubleshooting:**
- If Flux commands fail or return "Unknown skill", consult the official README: https://github.com/Nairon-AI/flux#troubleshooting
- Follow the troubleshooting steps exactly — do not guess or improvise fixes
- If the documented fixes don't work, the user should create a GitHub issue: https://github.com/Nairon-AI/flux/issues
</important>

**More info:** `.flux/bin/fluxctl --help` or read `.flux/usage.md`
<!-- END FLUX -->
