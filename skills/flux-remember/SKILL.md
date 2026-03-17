---
name: flux-remember
description: >-
  Smart "remember" routing — when user says "remember X", "don't forget X", or "keep in mind X",
  this skill decides whether to store in CLAUDE.md (short actionable rules for every session)
  or the brain vault (deeper context, decisions, business knowledge). Routes through flux-brain's
  "Remember" flow. Triggers: "remember", "don't forget", "keep in mind", "note that".
user-invocable: false
---

# Remember

Routes "remember X" requests to the right destination: **CLAUDE.md** or **brain/**.

This is a thin routing skill that delegates to the `flux-brain` skill's "Remember" flow after classifying the input.

## Detection

Trigger on any of these patterns in user input:
- "remember ..."
- "don't forget ..."
- "keep in mind ..."
- "note that ..."
- "from now on ..."
- "always ..." (when giving a rule, not asking a question)
- "never ..." (when giving a constraint, not asking a question)

**Do NOT trigger** if the user is asking a question ("do you remember...?", "can you remember...?").

## Process

### Step 1: Extract the thing to remember

Parse the user's input to extract the core content. Strip the trigger phrase:
- "remember that we use pnpm" → "we use pnpm"
- "don't forget: the API key is in Vault" → "the API key is in Vault"
- "always run tests before committing" → "run tests before committing"

### Step 2: Classify destination

Use this heuristic to pre-select CLAUDE.md vs brain/:

**→ CLAUDE.md** (short, actionable, every-session rules):
- Commands and how to run them ("use `pnpm test`", "run `make build`")
- Hard constraints ("never import from `legacy/`", "always use TypeScript")
- Code style rules ("use camelCase for APIs", "4-space indent")
- Build/test/deploy instructions
- Things that prevent common mistakes on ANY task
- Patterns: "always X", "never Y", "use X instead of Y", "run X before Y"

**→ brain/** (deeper knowledge, context, decisions):
- Why a decision was made ("we chose Supabase because...")
- Business context ("Sarah is the PM", "we have 500 users", "launch is March 15")
- Team information ("John handles frontend", "Maria approves API changes")
- Domain knowledge ("a 'workspace' is a tenant in our system")
- Pitfalls and lessons learned ("migration script doesn't handle NULLs")
- Architecture decisions ("we use event sourcing for audit trail because...")
- Anything that needs explanation beyond a single bullet point

**Rule of thumb:** If it fits in one bullet point and the agent needs it on every task → CLAUDE.md. If it needs context, rationale, or only matters in specific situations → brain/.

### Step 3: Delegate to flux-brain

Invoke the `flux-brain` skill's "Remember" flow with:
1. The extracted content
2. The pre-selected destination (CLAUDE.md or brain/)
3. The user's original phrasing (for context)

The flux-brain skill handles:
- Asking the user to confirm the destination (with AskUserQuestion)
- Writing to CLAUDE.md (finding the right section, appending as bullet)
- Writing to brain/ (asking category, creating file, updating index)

## Examples

| User says | Destination | Reasoning |
|-----------|-------------|-----------|
| "remember to always use pnpm, not npm" | CLAUDE.md | Short rule, every task |
| "remember that Sarah is the PM and approves all UX changes" | brain/business/ | Team context, specific situations |
| "don't forget: the deploy script needs AWS_REGION set" | CLAUDE.md | Command/constraint, prevents mistakes |
| "keep in mind we chose Postgres over Mongo because of ACID compliance" | brain/decisions/ | Decision with rationale |
| "remember our API rate limit is 100 req/min per user" | brain/codebase/ | Technical context, not every-task rule |
| "always run `pnpm lint` before committing" | CLAUDE.md | Command, every task |
| "note that the billing team uses 'subscription' not 'plan'" | brain/business/glossary | Domain language |
