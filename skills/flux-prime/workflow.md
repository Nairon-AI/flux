# Flow Prime Workflow

**State Machine**: See [docs/state-machine.md](../../docs/state-machine.md) for the formal workflow state diagram. This skill handles the `needs_prime` state and transitions to `fresh_session_no_objective` (optionally via `needs_ruminate`).

Execute these phases in order. Reference [pillars.md](pillars.md) for scoring criteria and [remediation.md](remediation.md) for fix templates.

**Model guidance**: This skill uses sonnet for synthesis and report generation. Scouts use the model configured during `/flux:setup`.

---

## Phase 0: Read Scout Model Config

Before launching scouts, read the configured scout model:

```bash
SCOUT_MODEL=$(.flux/bin/fluxctl config get scouts.model --json 2>/dev/null | jq -r '.value // empty')
```

If `SCOUT_MODEL` is empty, default to `claude-sonnet-4-6`.

Determine the scout backend:
- If `SCOUT_MODEL` starts with `claude-` → use **Claude backend** (Task tool with agent definitions)
- If `SCOUT_MODEL` starts with `gpt-` or `o1` or `o3` or `o4` → use **Codex backend** (`codex exec` CLI)
- Otherwise → use **Claude backend** as fallback

---

## Phase 1: Parallel Assessment

### Claude backend (default)

If using Claude backend, run all 9 scouts in parallel using the Task tool:

#### Agent Readiness Scouts (Pillars 1-5)

```
Task flux:tooling-scout    # linters, formatters, pre-commit, type checking
Task flux:claude-md-scout  # CLAUDE.md/AGENTS.md quality
Task flux:env-scout        # .env.example, docker, devcontainer
Task flux:testing-scout    # test framework, coverage, commands
Task flux:build-scout      # build system, scripts, CI
Task flux:docs-gap-scout   # README, ADRs, architecture docs
```

#### Production Readiness Scouts (Pillars 6-8)

```
Task flux:observability-scout  # logging, tracing, metrics, health
Task flux:security-scout       # branch protection, CODEOWNERS, secrets
Task flux:workflow-scout       # CI/CD, templates, automation
```

### Codex backend

If using Codex backend, first run a single preflight check to verify codex + model access before launching all 9 scouts:

#### Preflight check

```bash
# 1. Is codex installed?
which codex >/dev/null 2>&1 && echo "CODEX_OK" || echo "CODEX_MISSING"
```

If `CODEX_MISSING`: skip Codex backend, fall back to Claude backend, and warn:

```
⚠️  Codex CLI not found. Falling back to Claude scouts.
Install codex: npm install -g @openai/codex
Then run: codex login
```

```bash
# 2. Is codex authenticated?
codex login status 2>&1
```

If not authenticated (output doesn't contain "Logged in"): skip Codex backend, fall back to Claude backend, and warn:

```
⚠️  Codex CLI not authenticated. Falling back to Claude scouts.
Run in a separate terminal: codex login
```

```bash
# 3. Can we reach the configured model? (single quick probe)
timeout 30 codex exec -m "$SCOUT_MODEL" --ephemeral --sandbox read-only -o /dev/null "Say ok" 2>&1 | head -3
```

If the probe fails (timeout, error, or model access denied): skip Codex backend, fall back to Claude backend, and warn:

```
⚠️  Cannot access model <SCOUT_MODEL>. This may require a ChatGPT Pro subscription.
Falling back to Claude scouts for this run.

To fix permanently, run: .flux/bin/fluxctl config set scouts.model "claude-haiku-4-5"
Or upgrade your OpenAI plan and retry.
```

**Only proceed with Codex scouts if all 3 checks pass.** On any failure, fall through to the Claude backend section above — do not fail the entire prime.

#### Launch scouts (after preflight passes)

Run all 9 in parallel using background Bash commands:

```bash
# Read each scout's prompt from agents/*.md (strip the YAML frontmatter)
# Launch all 9 concurrently, each writing to a temp output file

SCOUT_MODEL="<configured model>"  # e.g. gpt-5.3-codex-spark

for scout in tooling-scout claude-md-scout env-scout testing-scout build-scout docs-gap-scout observability-scout security-scout workflow-scout; do
  PROMPT=$(sed '1,/^---$/{ /^---$/!d; /^---$/d; }' "agents/${scout}.md" | sed '/^---$/d')
  codex exec -m "$SCOUT_MODEL" --sandbox read-only --ephemeral -o "/tmp/flux-scout-${scout}.md" "$PROMPT" &
done
wait
```

After all complete, read each output file:

```bash
for scout in tooling-scout claude-md-scout env-scout testing-scout build-scout docs-gap-scout observability-scout security-scout workflow-scout; do
  echo "=== ${scout} ==="
  cat "/tmp/flux-scout-${scout}.md" 2>/dev/null || echo "(no output)"
  echo ""
done
```

If any individual scout output is empty or missing, note the failure but continue with the scouts that did produce output.

### Common

**Important**: Launch all 9 scouts in parallel for speed (~15-20 seconds total).

Wait for all scouts to complete. Collect findings.

---

## Phase 2: Verification (Optional but Recommended)

After scouts complete, verify key commands actually work.

### Test Verification

If test framework detected by testing-scout, verify tests are runnable using the **appropriate command for the detected framework**.

**Common examples** (adapt to whatever framework is detected):

| Framework | Verification Command |
|-----------|---------------------|
| pytest | `pytest --collect-only` |
| Jest | `npx jest --listTests` |
| Vitest | `npx vitest --run --reporter=dot` |
| Mocha | `npx mocha --dry-run` |
| Go test | `go test ./... -list .` |
| Cargo test | `cargo test --no-run` |
| PHPUnit | `phpunit --list-tests` |

These are examples. For other frameworks, find the equivalent "list tests" or "dry run" command. The goal is to verify tests are discoverable without actually running them.

**For monorepos**: Run verification in each app directory that has tests.

**Adapt to project**: Use the package manager detected (pnpm/npm/yarn/bun). If venv detected for Python, activate it first.

Example:
```bash
# Python with venv
cd apps/api && source .venv/bin/activate && pytest --collect-only 2>&1 | head -20

# JS with pnpm
pnpm test --passWithNoTests 2>&1 | head -10

# Go
go test ./... -list . 2>&1 | head -20
```

Mark TS4 as ✅ only if verification succeeds (tests are discoverable and runnable).

### Build Verification (Quick)

```bash
# Check if build command exists and is valid
pnpm build --help 2>&1 | head -5 || npm run build --help 2>&1 | head -5
```

---

## Phase 3: Score & Synthesize

Read [pillars.md](pillars.md) for pillar definitions and criteria.

### Agent Readiness Score (Pillars 1-5)

For each pillar (1-5):
1. Map scout findings to criteria (pass/fail)
2. Calculate pillar score: `(passed / total) * 100`

Calculate:
- **Agent Readiness Score**: average of Pillars 1-5 scores
- **Maturity Level**: based on thresholds in pillars.md

### Production Readiness Score (Pillars 6-8)

For each pillar (6-8):
1. Map scout findings to criteria (pass/fail)
2. Calculate pillar score: `(passed / total) * 100`

Calculate:
- **Production Readiness Score**: average of Pillars 6-8 scores

### Overall Score

**Overall Score** = average of all 8 pillar scores

### Infrastructure Provider Detection

Scan the codebase to identify cloud providers and services. This feeds the "Infrastructure MCPs & CLIs" question in Phase 5.

```bash
# 1. Config files — existence implies usage
for f in vercel.json railway.json railway.toml netlify.toml fly.toml render.yaml wrangler.toml wrangler.jsonc amplify.yml firebase.json .firebaserc supabase/.temp/project-ref doppler.yaml; do
  [ -f "$f" ] && echo "CONFIG: $f"
done

# 2. Dependencies — scan manifests
for manifest in package.json apps/*/package.json packages/*/package.json requirements*.txt Pipfile pyproject.toml Cargo.toml go.mod; do
  [ -f "$manifest" ] && grep -oE '@vercel/|@neondatabase/|@supabase/|@planetscale/|@cloudflare/workers|@aws-sdk/|@google-cloud/|firebase-admin|stripe|resend|@upstash/|@libsql/|@prisma/' "$manifest" 2>/dev/null | sort -u | sed "s/^/DEP ($manifest): /"
done

# 3. Environment variable prefixes — scan .env examples
for envfile in .env.example .env.local.example .env.template; do
  [ -f "$envfile" ] && grep -oE '^(VERCEL|RAILWAY|NEON|SUPABASE|PLANETSCALE|CLOUDFLARE|AWS|GOOGLE_CLOUD|FIREBASE|FLY|RENDER|NETLIFY|STRIPE|RESEND|UPSTASH|TURSO|DOPPLER)_' "$envfile" 2>/dev/null | sort -u | sed "s/^/ENV ($envfile): /"
done
```

Build a list of detected providers. For each, check if the corresponding MCP or CLI is already installed:

```bash
# Check existing tooling (skip recommendations for already-installed tools)
which vercel netlify railway flyctl render wrangler firebase pscale turso doppler stripe 2>/dev/null
# Check MCP configs
cat ~/.claude/settings.json 2>/dev/null | grep -o '"[^"]*mcp[^"]*"' | head -20
```

Only recommend MCPs/CLIs for providers that are detected AND whose tooling is NOT already installed.

### Prioritize Recommendations

Generate prioritized recommendations from **Pillars 1-5 only**:
1. Critical first (CLAUDE.md, .env.example)
2. High impact second (pre-commit hooks, lint commands)
3. Medium last (build scripts, .gitignore)

**Never offer fixes for Pillars 6-8** — these are informational only.

---

## Phase 4: Present Report

```markdown
# Agent Readiness Report

**Repository**: [name]
**Assessed**: [timestamp]

## Scores Summary

| Category | Score | Level |
|----------|-------|-------|
| **Agent Readiness** (Pillars 1-5) | X% | Level N - [Name] |
| Production Readiness (Pillars 6-8) | X% | — |
| **Overall** | X% | — |

## Agent Readiness (Pillars 1-5)

These affect your maturity level and are eligible for fixes.

| Pillar | Score | Status |
|--------|-------|--------|
| Style & Validation | X% (N/6) | ✅ ≥80% / ⚠️ 40-79% / ❌ <40% |
| Build System | X% (N/6) | ✅/⚠️/❌ |
| Testing | X% (N/6) | ✅/⚠️/❌ |
| Documentation | X% (N/6) | ✅/⚠️/❌ |
| Dev Environment | X% (N/6) | ✅/⚠️/❌ |

## Production Readiness (Pillars 6-8)

Informational only. No fixes offered — address independently if desired.

| Pillar | Score | Status |
|--------|-------|--------|
| Observability | X% (N/6) | ✅/⚠️/❌ |
| Security | X% (N/6) | ✅/⚠️/❌ |
| Workflow & Process | X% (N/6) | ✅/⚠️/❌ |

## Detailed Findings

### Pillar 1: Style & Validation (X%)

| Criterion | Status | Evidence |
|-----------|--------|----------|
| SV1: Linter | ✅/❌ | [details] |
| SV2: Formatter | ✅/❌ | [details] |
| ... | ... | ... |

[Repeat for each pillar]

## Top Recommendations (Agent Readiness)

1. **[Category]**: [specific action] — [why it helps agents]
2. **[Category]**: [specific action] — [why it helps agents]
3. **[Category]**: [specific action] — [why it helps agents]

## Production Readiness Notes

[Key observations from Pillars 6-8 that the team should be aware of]

## Infrastructure Providers Detected

| Provider | Signal | Agent Tooling | Status |
|----------|--------|---------------|--------|
| [Provider] | [config file / dep / env var] | [MCP/CLI name] | ✅ Installed / ❌ Not installed |

[If no providers detected, omit this section entirely]
```

**If `--report-only`**: Show report, then skip to Phase 8 (mark prime complete) and exit.

---

## Phase 5: Interactive Remediation

**If `--fix-all`**: Skip to Phase 6, apply all recommendations from Pillars 1-5.

**CRITICAL**: You MUST use the `AskUserQuestion` tool for consent. Do NOT just print questions as text.

### Using AskUserQuestion Correctly

The tool provides an interactive UI. Each question should:
- Have a clear header (max 12 chars)
- Explain what each option does and WHY it helps agents
- Use `multiSelect: true` so users can pick multiple items
- Include impact description for each option

### Question Structure

Ask ONE question per category that has recommendations. Skip categories with no gaps.

**Question 1: Documentation (if gaps exist)**

```json
{
  "questions": [{
    "question": "Which documentation improvements should I create? These help agents understand your project without guessing.",
    "header": "Docs",
    "multiSelect": true,
    "options": [
      {
        "label": "Create CLAUDE.md (Recommended)",
        "description": "Agent instruction file with commands, conventions, and project structure. Critical for agents to work effectively."
      },
      {
        "label": "Create .env.example",
        "description": "Template with [N] detected env vars. Prevents agents from guessing required configuration."
      }
    ]
  }]
}
```

**Question 2: Tooling (if gaps exist)**

```json
{
  "questions": [{
    "question": "Which tooling improvements should I add? These give agents instant feedback instead of waiting for CI.",
    "header": "Tooling",
    "multiSelect": true,
    "options": [
      {
        "label": "Add pre-commit hooks (Recommended)",
        "description": "Husky + lint-staged for instant lint/format feedback. Catches errors in 5 seconds instead of 10 minutes."
      },
      {
        "label": "Add linter config",
        "description": "[Tool] configuration for code quality checks. Agents can run lint to verify their changes."
      },
      {
        "label": "Add formatter config",
        "description": "[Tool] configuration for consistent code style. Prevents style drift across agent sessions."
      },
      {
        "label": "Add runtime version file",
        "description": "Pin [runtime] version. Ensures consistent environment across machines."
      }
    ]
  }]
}
```

**Question 3: Testing (if gaps exist)**

```json
{
  "questions": [{
    "question": "Which testing improvements should I add? These let agents verify their work.",
    "header": "Testing",
    "multiSelect": true,
    "options": [
      {
        "label": "Add test config (Recommended)",
        "description": "[Framework] configuration file. Enables test command for agents to verify changes."
      },
      {
        "label": "Add test script",
        "description": "Adds 'test' command that agents can discover and run."
      }
    ]
  }]
}
```

**Question 4: Browser Automation (if web app detected AND no browser automation tool)**

Only ask this if the testing scout detected a web app (React, Next, Vue, Svelte, etc.) but found no browser automation tool (Playwright, Cypress, Puppeteer, Stagehand, agent-browser).

```json
{
  "questions": [{
    "question": "Your web app has no browser automation tool. This means agents can't visually verify UI changes or run E2E tests. Install one?",
    "header": "Browser",
    "multiSelect": true,
    "options": [
      {
        "label": "Install agent-browser (Recommended)",
        "description": "Browser automation CLI built for coding agents. Enables visual QA and reproducible evidence. Install: npm i -g agent-browser"
      },
      {
        "label": "Skip",
        "description": "Set up browser automation later"
      }
    ]
  }]
}
```

If "Install agent-browser" selected, run in Phase 6:

```bash
npm i -g agent-browser 2>&1 | tail -5
# Verify install
which agent-browser >/dev/null 2>&1 && echo "agent-browser installed successfully" || echo "agent-browser install failed"
```

**Question 5: Environment (if gaps exist)**

```json
{
  "questions": [{
    "question": "Which environment improvements should I add?",
    "header": "Environment",
    "multiSelect": true,
    "options": [
      {
        "label": "Add .gitignore entries (Recommended)",
        "description": "Ignore .env, build outputs, node_modules. Prevents accidental commits of sensitive data."
      },
      {
        "label": "Create devcontainer (Bonus)",
        "description": "VS Code devcontainer config for reproducible environment. Nice-to-have, not essential for agents."
      }
    ]
  }]
}
```

**Question 6: Infrastructure MCPs & CLIs (if providers detected)**

Scan the codebase for infrastructure providers and recommend MCPs or CLIs that let agents interact with them directly — without the user needing to context-switch to dashboards.

**Detection**: Search for provider signals across the codebase:

```bash
# Config files
ls vercel.json railway.json railway.toml netlify.toml fly.toml render.yaml supabase/.temp/project-ref wrangler.toml wrangler.jsonc amplify.yml firebase.json .firebaserc 2>/dev/null

# Package dependencies (check package.json, requirements.txt, Cargo.toml, go.mod)
# Look for: @vercel/*, @neondatabase/*, @supabase/*, @prisma/*, @planetscale/*, @cloudflare/workers-*, @aws-sdk/*, @google-cloud/*, firebase-admin, stripe, resend, @upstash/*

# Environment variables
grep -rh 'VERCEL\|RAILWAY\|NEON_\|SUPABASE\|DATABASE_URL.*neon\|DATABASE_URL.*supabase\|PLANETSCALE\|CLOUDFLARE\|AWS_\|GOOGLE_CLOUD\|FIREBASE\|FLY_\|RENDER_\|NETLIFY\|STRIPE_\|RESEND_\|UPSTASH_\|TURSO_\|DOPPLER_' .env.example .env.local.example *.env 2>/dev/null | head -20
```

**Provider → MCP/CLI catalog** (see [remediation.md](remediation.md#infrastructure-mcps--clis) for full catalog):

Only include providers actually detected in the codebase. Build the options list dynamically from matches. Prioritize MCPs (richer agent integration) over bare CLIs.

```json
{
  "questions": [{
    "question": "I detected these infrastructure providers in your codebase. Installing their MCPs/CLIs lets agents manage deployments, query databases, and check logs without you switching to dashboards.",
    "header": "Infra",
    "multiSelect": true,
    "options": [
      {
        "label": "Install [Provider] MCP (Recommended)",
        "description": "[What it enables for agents]. Install: [command]"
      },
      {
        "label": "Skip infrastructure tooling",
        "description": "Set up provider CLIs/MCPs later"
      }
    ]
  }]
}
```

If items selected, install in Phase 6 using the commands from the catalog. Verify each install succeeds before moving to the next.

### Rules for Questions

1. **MUST use AskUserQuestion tool** — Never just print questions
2. **Mark recommended items** — Add "(Recommended)" to high-impact options
3. **Mark bonus items** — Add "(Bonus)" to nice-to-have options
4. **Explain agent benefit** — Each description should say WHY it helps agents
5. **Skip empty categories** — Don't ask if no recommendations
6. **Max 4 options per question** — Tool limit, prioritize if more. For infra, group by category (hosting, database, services) if >4 detected
7. **Never offer Pillar 6-8 items** — Production readiness is informational only

---

## Phase 6: Apply Fixes

For each approved fix:
1. Read [remediation.md](remediation.md) for the template
2. Detect project conventions (indent style, quote style, etc.)
3. Adapt template to match conventions
4. Check if target file exists:
   - **New file**: Create it
   - **Existing file**: Show diff and ask before modifying
5. Report what was created/modified

**Non-destructive rules:**
- Never overwrite without explicit consent
- Merge with existing configs when possible
- Use detected project style
- Don't add unused features

---

## Phase 7: Summary

After fixes applied:

```markdown
## Changes Applied

### Created
- `CLAUDE.md` — Project conventions for agents
- `.env.example` — Environment variable template

### Modified
- `package.json` — Added lint-staged config

### Skipped (user declined)
- Pre-commit hooks

### Not Offered (production readiness)
- CI/CD, PR templates, observability, security — address independently if desired
```

Offer re-assessment only if changes were made:

```
Run assessment again to see updated score?
```

If yes, run Phase 1-4 again and show:
- New Agent Readiness score and maturity level
- Score changes per pillar
- Remaining recommendations

---

## Phase 8: Mark Prime Complete

**CRITICAL**: After Phase 7 (or Phase 4 if `--report-only`), mark prime as done so `session-state` knows priming has completed:

```bash
.flux/bin/fluxctl prime-mark --status done --version "$(date +%Y-%m-%d)"
```

Without this step, `session-state` will always report `needs_prime` and block the user from scoping or implementation.

---

## Phase 9: Ruminate Offer (conditional)

After marking prime complete, check if the brain vault is thin and past conversations exist. If so, **ask the user** if they want to populate the brain from their past sessions.

**Trigger conditions** (ALL must be true):
1. Brain vault has fewer than 5 files across `.flux/brain/pitfalls/` and `.flux/brain/principles/`
2. Past Claude Code conversations exist (`~/.claude/projects/` has session data for this project)

```bash
# Count brain files (directories may not exist yet — 2>/dev/null handles this)
BRAIN_FILES=$(find .flux/brain/pitfalls .flux/brain/principles -name "*.md" 2>/dev/null | wc -l | xargs)

# Match project sessions — use the absolute repo path as-is for the Claude projects dir name
REPO_ROOT="$(pwd)"
PROJECT_DIR="$HOME/.claude/projects"
PAST_SESSIONS=0
if [ -d "$PROJECT_DIR" ]; then
  # Claude stores projects under a sanitized path — find dirs containing our repo path
  for d in "$PROJECT_DIR"/*; do
    # The dir name is the repo path with / replaced by -
    SANITIZED=$(echo "$REPO_ROOT" | sed 's|^/||; s|/|-|g')
    if [ -d "$d" ] && echo "$(basename "$d")" | grep -q "$SANITIZED"; then
      PAST_SESSIONS=$(find "$d" -name "*.jsonl" 2>/dev/null | wc -l | xargs)
      break
    fi
  done
fi
```

If `BRAIN_FILES < 5` and `PAST_SESSIONS > 0`, use `AskUserQuestion` to ask:

```json
{
  "questions": [{
    "question": "Your brain vault is thin but you have past Claude Code sessions in this project. Want to mine them for patterns and learnings? This will populate the brain vault so Flux doesn't start from zero.",
    "header": "Ruminate",
    "multiSelect": false,
    "options": [
      {
        "label": "Yes — populate brain from past sessions",
        "description": "Runs /flux:ruminate now to extract pitfalls, patterns, and corrections from your conversation history. Takes a few minutes."
      },
      {
        "label": "Skip for now",
        "description": "Start with an empty brain. It'll fill up naturally as you scope, build, and reflect."
      }
    ]
  }]
}
```

If the user selects **"Yes"**: immediately invoke the Skill tool with `skill: "flux:ruminate"`. Do NOT say "you can run this later" or "that's a separate workflow" — just run it as part of prime.

If the user selects **"Skip"**: continue silently to the "What to do next" summary.

If the trigger conditions are not met (brain is already populated, or no past sessions), skip this phase silently.
