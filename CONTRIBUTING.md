# Contributing to Flux

We welcome contributions, but we have **strict requirements** designed to filter out low-effort AI slop and ensure every PR adds genuine value.

## The Rules

### 1. You MUST use AI

We're building tools for AI-native development. If you're not using AI to build your contribution, you're not dogfooding the product. Use Claude Code, Cursor, Copilot, or any AI coding tool.

### 2. You MUST export and link your conversation history

Every PR must include a link to the exported conversation(s) that helped you implement the fix/feature. This shows:
- How much thinking went into the change
- Your problem-solving process
- That you actually worked through the implementation (not just copy-pasted)

**How to export:**
- Claude Code: Use `/export` or copy the conversation
- Cursor: Export chat history
- Other tools: Screenshot or export however you can

Upload to a gist, paste.gg, or include in the PR description.

### 3. You MUST include a demo video

Record yourself demoing the change/fix. This can be:
- A Loom video
- A screen recording uploaded to YouTube (unlisted is fine)
- A gif for small changes

The video proves the feature works and shows you actually tested it.

### 4. You MUST post to social media

Help us with visibility. Before your PR can be merged, you must post about your contribution on at least one of:
- Twitter/X
- LinkedIn
- Bluesky
- Threads

Include a link to the PR and tag [@naaboromern](https://x.com/naaboromern). Add the link to your social post in the PR description.

## PR Template

Your PR description must include:

```markdown
## What this PR does
[Brief description]

## Conversation history
[Link to exported AI conversation(s)]

## Demo video
[Link to video/gif]

## Social post
[Link to your social media post about this contribution]

## Checklist
- [ ] I used AI to build this
- [ ] I exported and linked my conversation history
- [ ] I included a demo video
- [ ] I posted to social media and linked it above
```

## Automatic Filtering

We have GitHub Actions that automatically check PRs. PRs that don't follow these guidelines will be:
1. Flagged with a `needs-requirements` label
2. Given 48 hours to add the missing items
3. Automatically closed if requirements aren't met

## Bans

Contributors who repeatedly submit low-effort PRs or try to game the system will be banned from the repository.

## Why So Strict?

Open source is drowning in AI-generated slop PRs from people who:
- Don't use the product
- Don't care about quality
- Just want GitHub activity for their profile

We want contributors who:
- Actually use Flux
- Care about making it better
- Are willing to help spread the word

If these requirements feel too high, this project isn't for you. If you genuinely care about building great developer tools, welcome aboard.

## Getting Started

1. Fork the repo
2. Create a feature branch
3. Use Flux itself (`/flux:scope`, `/flux:work`) to plan and implement your change
4. Record your demo
5. Post to social
6. Submit your PR with all requirements

## Questions?

Join our [Discord](https://discord.gg/CEQMd6fmXk) and ask in the #contributors channel.
