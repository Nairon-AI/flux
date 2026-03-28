---
name: flux-receive-review
description: Use when handling review feedback from humans, RepoPrompt, Codex, Greptile, CodeRabbit, or GitHub PR comments before implementing requested changes.
user-invocable: false
---

# Receive Review

Review feedback is input to evaluate, not text to obediently echo back. Verify it against the codebase before changing anything.

## Core Loop

1. Read the full comment set
2. Restate the technical requirement in plain terms
3. Verify it against the current code and tests
4. Decide whether it is correct, unclear, or context-missing
5. Implement or push back with technical reasoning
6. Re-verify before replying or advancing workflow state

## Default Behavior

When feedback is clear and correct:
- fix it
- verify it
- reply briefly with what changed

When feedback is unclear:
- stop
- ask only the missing technical question

When feedback appears wrong:
- check whether the reviewer missed context
- check whether the current behavior is intentional
- push back factually if needed

## Pushback Is Required When

- The suggestion breaks existing behavior
- The code already satisfies the requirement
- The request adds unused complexity
- The reviewer is missing platform, compatibility, or architectural context
- The comment conflicts with a prior user decision

## Response Style

Prefer:
- `Fixed in <file>. Verified with <command>.`
- `Current behavior is intentional because <reason>.`
- `Need clarification on <specific point> before changing this.`

Avoid:
- performative agreement
- gratitude filler
- promising a fix before verification

## Flux Fit

Use this inside:
- `flux:impl-review` fix loops
- `flux:epic-review` fix loops
- `flux:autofix` handling of human or bot comments
- manual PR comment triage

## Gotchas

- Do not implement only the items you understand if other comments may change the same area
- Do not assume external reviewers understand local constraints
- Do not argue stylistically when the feedback is technically correct
- Do not claim a comment is addressed without fresh verification
