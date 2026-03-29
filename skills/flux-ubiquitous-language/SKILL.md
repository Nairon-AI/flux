---
name: flux-ubiquitous-language
description: >-
  Extract a DDD-style ubiquitous language glossary from conversation and codebase, flagging
  ambiguities and proposing canonical terms. Saves to .flux/brain/business/glossary.md.
  Use when user wants to define domain terms, build a glossary, harden terminology, create
  a ubiquitous language, or mentions "domain model" or "DDD". Triggers on literal
  `/flux:ubiquitous-language`.
user-invocable: false
---

# Ubiquitous Language

Extract and formalize domain terminology into a consistent glossary, stored in the brain vault.

> "If developers and domain experts use different terms for the same concept, bugs hide in the translation."

**IMPORTANT**: This plugin uses `.flux/` for ALL task tracking. Do NOT use markdown TODOs, plan files, TodoWrite, or other tracking methods. All task state must be read and written via `fluxctl`.

**CRITICAL: fluxctl is BUNDLED — NOT installed globally.** `which fluxctl` will fail (expected). Always use:
```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
[ ! -d "$PLUGIN_ROOT/scripts" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
$FLUXCTL <command>
```

## Session Phase Tracking

On entry, set the session phase:
```bash
$FLUXCTL session-phase set ubiquitous_language
```
On completion, reset:
```bash
$FLUXCTL session-phase set idle
```

**Agent Compatibility**: This skill works across Codex, OpenCode, and legacy Claude environments. See [agent-compat.md](../../docs/agent-compat.md) for tool differences.

## Input

Full request: $ARGUMENTS

## Process

### 1. Gather Terms

Scan two sources for domain terminology:

**From conversation**: Identify domain-relevant nouns, verbs, and concepts discussed so far.

**From codebase**: Explore models, types, and naming conventions:
```bash
# Check for existing glossary
cat .flux/brain/business/glossary.md 2>/dev/null
# Look at domain models
```

Use Glob and Grep to find:
- Model/entity definitions (database schemas, TypeScript types, class definitions)
- API route names and parameters
- UI labels and copy
- Variable names in core business logic

### 2. Identify Problems

- **Ambiguity**: Same word used for different concepts (e.g., "account" meaning both a user login and a billing entity)
- **Synonyms**: Different words for the same concept (e.g., "customer", "client", "buyer" all meaning the same thing)
- **Vague terms**: Overloaded words that mean different things in different contexts

### 3. Propose Canonical Glossary

For each concept, pick **one** canonical term. Be opinionated — the value is in making a clear choice, not listing options.

### 4. Write to Brain Vault

Write or update `.flux/brain/business/glossary.md`:

```markdown
# Ubiquitous Language

## [Domain Area 1]

| Term | Definition | Aliases to avoid |
|------|-----------|-----------------|
| **Order** | A customer's request to purchase one or more items | Purchase, transaction |
| **Invoice** | A request for payment sent after delivery | Bill, payment request |

## [Domain Area 2]

| Term | Definition | Aliases to avoid |
|------|-----------|-----------------|
| ... | ... | ... |

## Relationships

- An **Invoice** belongs to exactly one **Customer**
- An **Order** produces one or more **Invoices**

## Example Dialogue

> **Dev:** "When a **Customer** places an **Order**, do we create the **Invoice** immediately?"
> **Domain expert:** "No — an **Invoice** is only generated once a **Fulfillment** is confirmed."

## Flagged Ambiguities

- "account" was used to mean both **Customer** and **User** — these are distinct concepts
```

### 5. Confirm

After writing, state:

> I've written/updated `.flux/brain/business/glossary.md`. From this point forward I will use these terms consistently. If I drift from this language or you notice a term that should be added, let me know.

## Rules

- **Be opinionated.** Pick the best term, list others as aliases to avoid.
- **Flag conflicts explicitly.** If a term is ambiguous, call it out with a clear recommendation.
- **Keep definitions tight.** One sentence max. Define what it IS, not what it does.
- **Show relationships.** Use bold term names and express cardinality where obvious.
- **Only include domain terms.** Skip generic programming concepts unless they have domain-specific meaning.
- **Group terms** when natural clusters emerge (by subdomain, lifecycle, or actor).
- **Write an example dialogue** (3-5 exchanges) showing terms used precisely.

## Re-running

When invoked again:

1. Read existing `.flux/brain/business/glossary.md`
2. Incorporate new terms from subsequent discussion
3. Update definitions if understanding has evolved
4. Mark changed entries with "(updated)" and new entries with "(new)"
5. Re-flag any new ambiguities
6. Rewrite the example dialogue to incorporate new terms

## Update Check (End of Command)

**ALWAYS run at the very end of /flux:ubiquitous-language execution:**

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
[ ! -d "$PLUGIN_ROOT/scripts" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
UPDATE_JSON=$("$PLUGIN_ROOT/scripts/version-check.sh" 2>/dev/null || echo '{"update_available":false}')
UPDATE_AVAILABLE=$(echo "$UPDATE_JSON" | jq -r '.update_available')
LOCAL_VER=$(echo "$UPDATE_JSON" | jq -r '.local_version')
REMOTE_VER=$(echo "$UPDATE_JSON" | jq -r '.remote_version')
```

**If update available**, append to output:

```
---
Flux update available: v${LOCAL_VER} → v${REMOTE_VER}
Update Flux from the same source you installed it from, then restart your agent session.
---
```

**If no update**: Show nothing (silent).

## Gotchas

- The glossary lives in `.flux/brain/business/glossary.md`, not a standalone file. This integrates with `flux-propose` and other skills that read business context.
- If `.flux/brain/business/` doesn't exist yet, create it.
- Don't confuse this with code-level naming conventions. This is about *domain* language — what things are called in the business, not what variables are named.
- The glossary is a living document. It should be updated as the domain understanding evolves, not treated as a one-time artifact.
