# Flux Troubleshooting

## `/flux:improve` shows no recommendations

Possible reasons:
- No meaningful friction detected in recent sessions
- Session analysis was skipped
- Relevant recommendations were dismissed
- Your current setup already covers detected gaps

Try:

```bash
/flux:improve --detect
/flux:improve --explain
```

## Session analysis says no sessions found

Flux analyzes sessions for the current project. If your project has no session history yet, start coding and run again later.

You can still run setup-only analysis:

```bash
/flux:improve --skip-sessions
```

## Recommendation clone/update failed (offline or network issue)

Flux uses `~/.flux/recommendations` as cache.

- If cache already exists, Flux should continue with cached recommendations.
- If cache does not exist, connect to network once and run `/flux:improve` again.

## Optional discover mode returns nothing

`--discover` is best-effort and can legitimately return empty results.

Check:
- `~/.flux/config.json` has valid `exa_api_key` or `twitter_api_key`
- query context is specific enough (`--explain` can help)

## `/flux:profile` publish fails

Check profile link service config:

- set env `FLUX_PROFILE_SERVICE_URL`, or
- set `profile_service_url` in `~/.flux/config.json`

Then retry `/flux:profile`.

## `/flux:profile` import skipped many items

This is expected when:

- items are already installed (default behavior is skip)
- items are OS-incompatible (compatible-only import policy)
- items are manual-only (shown as instructions, not auto-installed)

Use `/flux:profile view <url>` first to inspect the snapshot contents.

## `/flux:profile` tombstone fails

- Tombstone requires owner manage token (stored in `~/.flux/profile-state.json` after publish)
- If the snapshot was published elsewhere, provide a valid token explicitly

## Undo a failed install

Flux snapshots config before changes in `~/.flux/snapshots/`.

Use:

```bash
/flux:improve --rollback <snapshot-id>
```

## Consent and privacy

- Session analysis requires explicit opt-in unless user enabled always-allow.
- Local analysis is default.
- `--discover` sends search queries externally (Exa/Twitter API), by design.
