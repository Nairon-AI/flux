---
name: nbench-profile
description: Export, publish, view, import, and tombstone N-bench SDLC profiles. Use for shareable immutable setup links and team setup replication.
user-invocable: false
---

# N-bench Profile

Create and consume shareable SDLC profiles (`/nbench:profile`).

## What this skill does

1. Detects machine setup (MCPs, CLI tools, skills, apps, patterns, model prefs)
2. Asks skill scope each export: global, project, or both with de-dup (name + hash)
3. Applies application curation memory (saved apps, new apps, optional re-include missing)
4. Builds public-anonymous immutable snapshot payload with auto-redaction
5. Publishes to N-bench profile link service
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
