# /nbench:profile Launch Checklist

## Export

- [ ] `detect` returns valid JSON with all categories
- [ ] Skill scope prompt works (`global`, `project`, `both`)
- [ ] `both` mode de-dupes skills by name+hash
- [ ] App curation shows new apps first
- [ ] Saved apps persist across exports
- [ ] Saved missing apps can be re-included
- [ ] Required/optional tagging stored in snapshot

## Privacy and Security

- [ ] Sensitive values auto-redacted in snapshot payload
- [ ] Snapshot metadata only includes minimal anonymous fields
- [ ] No usernames/paths/hostnames leak into published payload

## Link Service

- [ ] Publish returns immutable, non-expiring link
- [ ] Fetch returns active snapshot
- [ ] Tombstone hides content while keeping link
- [ ] Tombstone requires owner manage token

## Import

- [ ] Plan filters unsupported OS items
- [ ] Already installed items default to skip
- [ ] Per-item confirmation flow works
- [ ] Manual-only items shown with instructions
- [ ] Installer + verification hooks execute for supported items

## Regression

- [ ] `bun test tests/scripts.test.ts` passes
- [ ] `python3 scripts/test_profile_manager.py` passes
