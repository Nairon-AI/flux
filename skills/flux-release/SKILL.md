---
name: flux-release
description: Use when cutting a new Flux release. Bump all manifest versions in sync, tag the release, create GitHub release notes, and prevent stale plugin metadata from drifting from the published tag. Triggers on /flux:release.
user-invocable: true
---

# Release Flux

Bumps version across all manifest files, commits to main, and creates a GitHub release. This ensures `claude plugin marketplace add` always pulls the correct version.

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

Build a structured release summary before creating the release. **Do NOT use `--generate-notes`** — write a proper "What's New" section.

1. Get all commits since the last release tag:
```bash
LAST_TAG=$(git tag --sort=-v:refname | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | head -1)
git log "$LAST_TAG..HEAD" --pretty=format:"%s" | grep -v "chore: bump version" | grep -v "\[skip ci\]"
```

2. Write release notes in this format:
```markdown
## What's New

### [Primary feature/change — descriptive heading]

[2-4 sentences explaining what changed, why it matters, and how it works.
Be specific — name the files, commands, or behaviors that changed.
This is what users see first. Make it count.]

**Key changes:**
- [Bullet point for each significant change]
- [Include concrete details, not vague summaries]

## What's Changed
* [commit message 1]
* [commit message 2]

**Full Changelog**: https://github.com/Nairon-AI/flux/compare/$LAST_TAG...v$VERSION
```

3. Save notes to a temp file and create the release:
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
