---
name: flux-release
description: Use when cutting a new Flux release. Bump all manifest versions in sync, tag the release, create GitHub release notes, and prevent stale plugin metadata from drifting from the published tag. Triggers on literal `/flux:release`.
user-invocable: true
---

# Release Flux

Bumps version across all manifest files, commits to main, and creates a GitHub release. This ensures `claude plugin marketplace add` always pulls the correct version.

## Session Phase Tracking

On entry, set the session phase:
```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
[ ! -d "$PLUGIN_ROOT/scripts" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
$FLUXCTL session-phase set release
```

On completion, reset:
```bash
$FLUXCTL session-phase set idle
```

## Arguments

`$ARGUMENTS` format: `<version> [--title "Release title"]`

Examples:
- `/flux:release v2.4.0`
- `/flux:release v2.4.0 --title "Parallel Workers"`

If no `--title` is provided, the release title defaults to the version number.

## Version Files (ALL must be updated)

These files contain the version string and MUST stay in sync:

1. **`package.json`** → `"version": "X.Y.Z"`
2. **`.claude-plugin/plugin.json`** → `"version": "X.Y.Z"`
3. **`.claude-plugin/marketplace.json`** → `"version": "X.Y.Z"` (inside `plugins[0]`)
4. **`README.md`** → version badge `version-vX.Y.Z-green`
5. **`CHANGELOG.md`** → move `[Unreleased]` entries under a new `[X.Y.Z] - YYYY-MM-DD` heading

## Workflow

### Step 1: Parse Arguments

Extract version from `$ARGUMENTS`. Strip leading `v` if present for the manifest files (e.g., `v2.4.0` → `2.4.0` in JSON, `v2.4.0` in git tag).

Parse optional `--title "..."` — if not provided, default title to the version.

### Step 2: Validate

```bash
# Must be on main or a release branch
BRANCH=$(git branch --show-current)
if [[ "$BRANCH" != "main" && "$BRANCH" != release/* ]]; then
  echo "Error: Must be on main or a release/* branch. Currently on: $BRANCH"
  exit 1
fi

# Version must be valid semver
if ! echo "$VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$'; then
  echo "Error: Invalid semver: $VERSION"
  exit 1
fi

# Check we're not re-releasing an existing tag
if git rev-parse "v$VERSION" >/dev/null 2>&1; then
  echo "Error: Tag v$VERSION already exists"
  exit 1
fi
```

### Step 3: Bump Version in All Files

Update all five files with the new version:

1. **`package.json`** — update the `"version"` field to `"$VERSION"`
2. **`.claude-plugin/plugin.json`** — update the `"version"` field to `"$VERSION"`
3. **`.claude-plugin/marketplace.json`** — update `plugins[0].version` to `"$VERSION"`
4. **`README.md`** — update the badge from `version-v*-green` to `version-v$VERSION-green`
5. **`CHANGELOG.md`** — move everything under `## [Unreleased]` into a new `## [$VERSION] - YYYY-MM-DD` section (use today's date). Add a fresh empty `## [Unreleased]` heading at the top. If there are no unreleased entries, create the version heading with a summary of what's in this release based on the GitHub release notes.

### Step 4: Commit

```bash
git add package.json .claude-plugin/plugin.json .claude-plugin/marketplace.json README.md CHANGELOG.md
git commit -m "release: v$VERSION"
git push origin "$BRANCH"
```

### Step 5: Create GitHub Release

Build release notes that explain **why** each change matters, not just what files changed. **Do NOT use `--generate-notes`**.

1. Get merged PRs since last release:
```bash
LAST_TAG=$(git tag --sort=-v:refname | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | head -1)
TAG_DATE=$(git log -1 --format=%aI "$LAST_TAG")
gh pr list --state merged --base main --search "merged:>=${TAG_DATE}" --limit 50 --json number,title,body
```

2. For each PR, extract the "What this PR does" section from its body. Use that as the description — it already explains the change in the author's own words.

3. Write release notes in this format:
```markdown
## What's New

### [Descriptive heading that explains the value, not the implementation] (#PR)

[2-4 sentences explaining what changed and WHY it matters to users.
Lead with the problem being solved, then explain how this release addresses it.
Be specific — name the skills, commands, or behaviors that changed.
This is what users read first. Make it worth reading.]

### [Second feature heading] (#PR)

[Same structure — problem, solution, impact.]

---

## PRs

- #N — PR title
- #N — PR title

## Full Changelog

https://github.com/Nairon-AI/flux/compare/$LAST_TAG...v$VERSION
```

**Writing guidelines:**
- Lead each section with the **problem** ("Claude ignores testing instructions"), then the **solution** ("Conditional blocks give Claude a clearer signal")
- Never list "Files Changed" — users don't care which `.md` files were edited
- Never dump raw commit messages as descriptions — rewrite them as user-facing prose
- Group by PRs, not by commit type — each PR gets its own heading with a narrative
- Skip chore/CI/version-bump PRs entirely
- Use `---` between major sections for visual separation

4. Save notes and create the release:
```bash
gh release create "v$VERSION" --target "$BRANCH" --title "$TITLE" --notes-file /tmp/release-notes.md
```

**Release title format:** `v$VERSION — [short description of primary change]` (e.g., `v2.14.0 — Anti-Sycophancy & Viability Gate`). If `--title` was provided by the user, use that instead.

### Step 6: Verify

```bash
# Confirm the tag exists
gh release view "v$VERSION" --json tagName,name --jq '"\(.tagName) — \(.name)"'

# Confirm manifest files match
PACKAGE_VER=$(jq -r '.version' package.json)
PLUGIN_VER=$(jq -r '.version' .claude-plugin/plugin.json)
MARKETPLACE_VER=$(jq -r '.plugins[0].version' .claude-plugin/marketplace.json)

if [[ "$PACKAGE_VER" != "$VERSION" || "$PLUGIN_VER" != "$VERSION" || "$MARKETPLACE_VER" != "$VERSION" ]]; then
  echo "ERROR: Version mismatch after release!"
  echo "  package.json:      $PACKAGE_VER"
  echo "  plugin.json:       $PLUGIN_VER"
  echo "  marketplace.json:  $MARKETPLACE_VER"
  echo "  Expected:          $VERSION"
  exit 1
fi

echo "Released v$VERSION — all manifest files in sync."
```

## Gotchas

- Flux release integrity depends on all manifest files matching the tag. A single stale file recreates the exact upgrade bug this skill exists to prevent.
- Do not release from an unverified or dirty branch. Version bumps, notes, and tags should reflect the code that is actually shipping.
- Generated release notes still need sanity checking; vague or misleading notes make upgrades harder to trust.
