# N-bench Troubleshooting

Common issues and solutions.

---

## Installation Issues

### Plugin not found after install

1. Verify files exist: `ls ~/.claude/plugins/n-bench/commands/nbench/`
2. Restart Claude Code
3. Try manual install if marketplace failed

### Prerequisites missing

N-bench requires Python 3.9+, jq, and git. Install:

```bash
# macOS
brew install python jq git

# Ubuntu/Debian
sudo apt install python3 jq git

# Fedora
sudo dnf install python3 jq git
```

---

## `/nbench:improve` Issues

### Shows no recommendations

Possible reasons:
- No meaningful friction detected in recent sessions
- Session analysis was skipped
- Relevant recommendations were dismissed
- Your current setup already covers detected gaps

Try:

```bash
/nbench:improve --detect    # See what was detected
/nbench:improve --explain   # See matching rationale
```

### Session analysis says no sessions found

N-bench analyzes sessions for the current project. If your project has no session history yet, start coding and run again later.

You can still run setup-only analysis:

```bash
/nbench:improve --skip-sessions
```

### Recommendation clone/update failed (offline or network issue)

N-bench uses `~/.nbench/recommendations` as cache.

- If cache already exists, N-bench continues with cached recommendations
- If cache does not exist, connect to network once and run `/nbench:improve` again

### Optional discover mode returns nothing

`--discover` is best-effort and can legitimately return empty results.

Check:
- `~/.nbench/config.json` has valid `exa_api_key` or `twitter_api_key`
- Query context is specific enough (`--explain` can help)

---

## `/nbench:score` Issues

### Score shows all zeros

Session data not found or not parsed correctly. Verify:
- Sessions exist in `~/.claude/projects/`
- Date range includes sessions: `--since 2026-02-01`

### Score seems inaccurate

N-bench scores based on detected patterns. Run with `--format json` to see raw metrics and verify data sources.

---

## `/nbench:profile` Issues

### Publish fails

Check profile link service config:

- Set env `NBENCH_PROFILE_SERVICE_URL`, or
- Set `profile_service_url` in `~/.nbench/config.json`

Then retry `/nbench:profile`.

### Import skipped many items

This is expected when:

- Items are already installed (default behavior is skip)
- Items are OS-incompatible (compatible-only import policy)
- Items are manual-only (shown as instructions, not auto-installed)

Use `/nbench:profile view <url>` first to inspect the snapshot contents.

### Tombstone fails

- Tombstone requires owner manage token (stored in `~/.nbench/profile-state.json` after publish)
- If the snapshot was published elsewhere, provide a valid token explicitly

---

## General Issues

### Undo a failed install

N-bench snapshots config before changes in `~/.nbench/snapshots/`.

Use:

```bash
/nbench:improve --rollback <snapshot-id>
```

### Windows support

N-bench is best-effort on Windows. Use WSL for full compatibility:

```bash
wsl --install
# Then install N-bench inside WSL
```

---

## Privacy & Consent

- Session analysis requires explicit opt-in unless user enabled always-allow
- Local analysis is default
- `--discover` sends search queries externally (Exa/Twitter API), by design
- `/nbench:score --export` creates local files only (you control sharing)
