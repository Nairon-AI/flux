# Flux Profile Workflow

Follow steps in order.

## Step 1: Parse mode and options

Set:
- `PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-${DROID_PLUGIN_ROOT}}"`
- `PROFILE_SCRIPT="$PLUGIN_ROOT/scripts/profile-manager.py"`

Parse `$ARGUMENTS`:
- `import <target>` -> mode `import`
- `view <target>` -> mode `view`
- `tombstone <target>` -> mode `tombstone`
- default -> mode `export`

Parse optional flags:
- `--skills=global|project|both`
- `--required=<csv>`

If `--skills` not provided and mode is `export`, ask:

```
mcp_question({
  questions: [{
    header: "Skill Scope",
    question: "For profile export, which skills should be included?",
    options: [
      { label: "Both (dedupe)", description: "Combine global + project skills, dedupe by name+hash" },
      { label: "Global only", description: "Include only ~/.claude/skills" },
      { label: "Project only", description: "Include only .claude/skills in current repo" }
    ]
  }]
})
```

Map answer to `SKILLS_SCOPE` (`both`, `global`, `project`).

## Step 2: Export mode (default)

### 2a) Detect setup + app memory

Run:

```bash
DETECTED=$(python3 "$PROFILE_SCRIPT" detect --skills-scope "$SKILLS_SCOPE")
```

Show summary:
- counts by category
- app buckets from `application_selection`:
  - `saved_installed`
  - `new_candidates`
  - `saved_missing`

### 2b) Choose applications to include

Behavior requirements:
- Primary prompt: show only `new_candidates`.
- Previously saved apps are auto-included by default.
- Saved missing apps are not included unless user explicitly chooses them.
- If user wants to remove saved apps, run:

```bash
python3 "$PROFILE_SCRIPT" saved-apps --remove "app1,app2"
```

Ask for new app selection when `new_candidates` is non-empty:

```
mcp_question({
  questions: [{
    header: "New Applications",
    question: "Select newly detected applications to add to your saved profile set.",
    multiple: true,
    options: [/* build from new_candidates */]
  }]
})
```

If `saved_missing` has entries, ask whether to include any this export:

```
mcp_question({
  questions: [{
    header: "Saved Missing Apps",
    question: "You have previously saved apps not currently installed. Re-include any in this snapshot?",
    multiple: true,
    options: [/* build from saved_missing */]
  }]
})
```

### 2c) Mark required items (optional)

If user provided `--required=<csv>`, use it.
Otherwise ask optional question:

```
mcp_question({
  questions: [{
    header: "Required Items",
    question: "Optional: choose any tools that teammates should treat as required. Unselected items stay optional.",
    multiple: true,
    options: [/* build from selected profile item IDs/names */]
  }]
})
```

### 2d) Build snapshot

Run:

```bash
python3 "$PROFILE_SCRIPT" export \
  --skills-scope "$SKILLS_SCOPE" \
  --selected-new-apps "$SELECTED_NEW_APPS_CSV" \
  --include-saved-missing-apps "$SELECTED_SAVED_MISSING_APPS_CSV" \
  --required-items "$REQUIRED_ITEMS_CSV" \
  --output-file /tmp/flux-profile-export.json
```

This updates app memory state in `~/.flux/profile-state.json` (unless dry-run).

### 2e) Publish immutable link

Run:

```bash
PUBLISHED=$(python3 "$PROFILE_SCRIPT" publish --input-file /tmp/flux-profile-export.json)
```

If publish fails due missing service URL, configure one of:
- env `FLUX_PROFILE_SERVICE_URL`
- `~/.flux/config.json` key `profile_service_url`

Show:
- shareable URL
- immutable/non-expiring note
- tombstone available note

## Step 3: View mode

Run:

```bash
PROFILE=$(python3 "$PROFILE_SCRIPT" fetch "$TARGET")
```

If tombstoned, show tombstone message.
Else show:
- profile name
- created at
- OS
- counts by category
- required vs optional counts

## Step 4: Import mode

### 4a) Fetch + plan

Run:

```bash
python3 "$PROFILE_SCRIPT" fetch "$TARGET" > /tmp/flux-profile-fetch.json
python3 "$PROFILE_SCRIPT" plan-import --profile-file /tmp/flux-profile-fetch.json > /tmp/flux-profile-plan.json
```

Show grouped plan:
- `prompt_required`
- `prompt_optional`
- `manual_required`
- `manual_optional`
- `already_installed` (auto-skip default)
- `unsupported` (cross-OS filtered)

### 4b) Per-item confirmation + install

For each item in `prompt_required` then `prompt_optional`, ask one question per item:

```
mcp_question({
  questions: [{
    header: "Install Item",
    question: "Install <name> (<category>)?",
    options: [
      { label: "Install", description: "Run install + verify" },
      { label: "Skip", description: "Skip this item" }
    ]
  }]
})
```

If install chosen, run:

```bash
python3 "$PROFILE_SCRIPT" install-item --item-file /tmp/item.json
```

For manual groups, show instructions and ask acknowledge/skip (no auto install).

### 4c) Final import summary

Show:
- installed count
- skipped count
- already-installed skipped count
- unsupported count
- manual follow-up count

## Step 5: Tombstone mode

Run:

```bash
python3 "$PROFILE_SCRIPT" tombstone "$TARGET"
```

Show confirmation and resulting link status.
