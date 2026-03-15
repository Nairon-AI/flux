---
name: flux-release
description: Release a new version of Flux. Bumps version in all manifest files, commits, creates GitHub release. Prevents the stale-version bug where plugin.json is out of sync with the release tag.
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
3. **`README.md`** → version badge `version-vX.Y.Z-green`

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

Update all three files with the new version:

1. **`package.json`** — update the `"version"` field to `"$VERSION"`
2. **`.claude-plugin/plugin.json`** — update the `"version"` field to `"$VERSION"`
3. **`README.md`** — update the badge from `version-v*-green` to `version-v$VERSION-green`

### Step 4: Commit

```bash
git add package.json .claude-plugin/plugin.json README.md
git commit -m "release: v$VERSION"
git push origin "$BRANCH"
```

### Step 5: Create GitHub Release

```bash
gh release create "v$VERSION" --target "$BRANCH" --title "$TITLE" --generate-notes
```

### Step 6: Verify

```bash
# Confirm the tag exists
gh release view "v$VERSION" --json tagName,name --jq '"\(.tagName) — \(.name)"'

# Confirm manifest files match
PACKAGE_VER=$(jq -r '.version' package.json)
PLUGIN_VER=$(jq -r '.version' .claude-plugin/plugin.json)

if [[ "$PACKAGE_VER" != "$VERSION" || "$PLUGIN_VER" != "$VERSION" ]]; then
  echo "ERROR: Version mismatch after release!"
  echo "  package.json: $PACKAGE_VER"
  echo "  plugin.json:  $PLUGIN_VER"
  echo "  Expected:     $VERSION"
  exit 1
fi

echo "Released v$VERSION — all manifest files in sync."
```
