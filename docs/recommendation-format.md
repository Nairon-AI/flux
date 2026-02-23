# Recommendation Format Guide

Flux recommendations are YAML files stored in `~/.nbench/recommendations`.

Schema reference: `~/.nbench/recommendations/schema.yaml`

## Required Fields

- `name` - unique slug (lowercase, hyphenated)
- `category` - `mcp | plugin | skill | cli-tool | application | workflow-pattern`
- `tagline` - short value proposition
- `description` - detailed explanation and use cases
- `install` - installation type/command/config
- `verification` - how to verify install success

## Core Matching Fields

- `sdlc_phase` - where this helps (`requirements|planning|implementation|review|testing|documentation`)
- `solves` - specific workflow gap it addresses
- `tags` - searchable terms used for matching and discovery

## Transparency Fields

- `source` - `manual | x-discovery | community`
- `source_url` - original discovery URL (if any)
- `mentions[]` - social proof references (tweet URL, author, likes)

## Example

```yaml
name: gh
category: cli-tool
tagline: GitHub CLI for issues, PRs, and repo workflows
description: |
  GitHub's official CLI. Manage issues, PRs, reviews, releases, and checks
  from terminal workflows and agent automation.
install:
  type: brew
  command: brew install gh
verification:
  type: command_exists
  test_command: gh --version
  success_indicator: Prints gh version
sdlc_phase: review
solves: Faster PR/issue operations without browser context switching
source: manual
tags:
  - github
  - cli
  - pull-request
```

## Quality Checklist

- Define clear, practical `solves` statement.
- Include realistic installation and verification commands.
- Use tags users would actually search for.
- Keep tagline concrete and outcome-focused.
- Add source metadata for explainability when available.
