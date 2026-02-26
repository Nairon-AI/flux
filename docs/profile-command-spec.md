# /flux:profile Command Spec

Defines command behavior for profile export/import/view/tombstone.

## Modes

- `export` (default)
- `view <url|id>`
- `import <url|id>`
- `tombstone <url|id>`

## Options

- `--skills=global|project|both`
- `--required=<csv>` (item names or IDs)

## Export UX

1. Ask skill scope unless provided by flag.
2. Detect setup using `scripts/profile-manager.py detect`.
3. Application curation behavior:
   - Auto-include previously saved installed apps.
   - Prompt only newly detected apps first.
   - Offer optional re-include for saved-but-missing apps.
   - Allow manual removal from saved list via `profile-manager.py saved-apps --remove`.
4. Optional required/optional tagging.
5. Build snapshot via `scripts/profile-manager.py export`.
6. Publish immutable link via `scripts/profile-manager.py publish`.

## Import UX

1. Fetch profile via `scripts/profile-manager.py fetch`.
2. Build import plan via `scripts/profile-manager.py plan-import`.
3. Show grouped actions:
   - Prompt install (required first, then optional)
   - Manual setup
   - Already installed (auto-skip default)
   - Unsupported OS
4. Per-item confirmation before each install.
5. Install with `scripts/profile-manager.py install-item`.
6. Show final import summary.

## Security and Privacy Rules

- Auto-redact sensitive values before publish.
- Public snapshots are anonymous and include minimal metadata only.
- Snapshot links are immutable and non-expiring.
- Owners may tombstone links (content hidden, link preserved).
