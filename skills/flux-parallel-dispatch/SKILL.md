---
name: flux-parallel-dispatch
description: Use when 2 or more investigations, scaffolds, reviews, or fixes are independent enough to run in parallel without shared files, shared state, or sequential dependency.
user-invocable: false
---

# Parallel Dispatch

Dispatch parallel subagents only when the work cleanly separates. Speed comes from independence, not from spawning aggressively.

## When to Use

Use this skill when:
- Multiple failing areas have different likely root causes
- `flux:prime` or `flux:scope --explore` needs several independent scouts
- Review work can be split by subsystem or concern
- A large task has disjoint write sets and one agent can integrate later

Do not use this skill when:
- The next local step is blocked on a single urgent result
- Agents would edit the same files or depend on the same evolving state
- Failures may share one root cause

## Decision Test

Parallelize only if all of these are true:
1. Each unit of work can be described in one paragraph
2. Each agent can succeed with task-local context only
3. The write sets are disjoint, or the work is read-only
4. One result is unlikely to invalidate the others

If any check fails, keep the work local or run sequentially.

## Dispatch Pattern

1. Split by problem domain, not by arbitrary count
2. Keep one owner in the main thread for integration
3. Give each agent explicit scope, constraints, and expected output
4. Ask for summaries, not long transcripts
5. Verify and integrate before claiming success

Good task shapes:
- One failing test file
- One scout domain
- One review concern
- One bounded implementation slice with clear file ownership

Bad task shapes:
- "Fix all the tests"
- "Review everything"
- "Refactor the auth system and update related code"

## Prompt Requirements

Each dispatched task should include:
- Goal
- Exact scope
- Files or subsystem owned
- Constraints
- Expected return format

Example:

```text
Investigate auth middleware failures in tests/auth-middleware.test.ts only.
Find root cause, fix that file or its direct implementation dependencies, and report:
- root cause
- files changed
- verification run
Do not edit billing or session code.
```

## Flux Fit

Best fits:
- `flux:prime` scouts
- `flux:scope --explore`
- multi-domain debugging during `flux:work`
- independent fix lanes inside review workflows

## Gotchas

- Parallel is wrong when one failing domain may be a symptom of another
- Do not dispatch urgent critical-path work that you need immediately
- Do not let multiple agents edit the same hot files without explicit ownership
- Always re-run shared verification after integration
