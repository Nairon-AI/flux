---
name: flux-profile
description: Export, publish, view, import, and tombstone Flux SDLC profiles. Use for shareable immutable setup links and team setup replication.
user-invocable: false
---

# Flux Profile

Create and consume shareable SDLC profiles (`/flux:profile`).

## What this skill does

1. Detects machine setup (MCPs, CLI tools, skills, apps, patterns, model prefs)
2. Asks skill scope each export: global, project, or both with de-dup (name + hash)
3. Applies application curation memory (saved apps, new apps, optional re-include missing)
4. Builds public-anonymous immutable snapshot payload with auto-redaction
5. Publishes to Flux profile link service
6. Imports with compatibility checks and per-item consent before install
7. Supports owner tombstone for immutable links

## Product constraints

- Secret handling: auto-redact and publish
- Visibility: public anonymous, minimal metadata only
- Link policy: immutable, non-expiring snapshots
- Owner control: tombstone supported
- Import defaults: skip already-installed, compatible-only OS filtering
- Manual-only entries: allowed with setup notes + verification guidance
- Priority tags: every item supports `required` or `optional`

## Input

`$ARGUMENTS`

Supported modes:
- `export` (default)
- `view <url|id>`
- `import <url|id>`
- `tombstone <url|id>`

Supported options:
- `--skills=global|project|both`
- `--required=<csv>`

## Workflow

Follow `workflow.md` exactly.

## Future: Universe Sync

When cloud component launches, `/flux:profile` will gain a `sync` mode:

```bash
/flux:profile sync              # Push profile to Universe portal
/flux:profile sync --public     # Include public metrics
```

**Public data (opt-in):**
- Session count, token usage
- Tools and MCPs in use
- Activity timestamps

**Private data (dashboard only):**
- AI-native score (5 dimensions)
- Detailed radar chart
- Improvement trends

Auth will use Universe accounts. ETA: Q2 2026.
