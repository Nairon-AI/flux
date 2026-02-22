# Flux Profile Schema (v1)

## Snapshot payload

```json
{
  "schema_version": "1.0",
  "profile_kind": "flux-sdlc-profile",
  "profile_name": "Team Baseline",
  "created_at": "2026-02-22T12:00:00Z",
  "visibility": "public-anonymous",
  "link_policy": {
    "immutable": true,
    "non_expiring": true,
    "tombstone_supported": true
  },
  "metadata": {
    "os": "macos"
  },
  "policies": {
    "secret_redaction": "auto",
    "import_confirmation": "per-item",
    "already_installed_default": "skip",
    "cross_os": "compatible-only",
    "manual_items": "allowed"
  },
  "items": [
    {
      "id": "mcp:context7",
      "name": "context7",
      "category": "mcp",
      "priority": "required",
      "sdlc_phase": "implementation",
      "install": {
        "type": "mcp",
        "command": "",
        "config_snippet": {
          "command": "npx",
          "args": ["-y", "@context7/mcp"],
          "env": {
            "CONTEXT7_API_KEY": "<redacted>"
          }
        }
      },
      "verification": {
        "type": "mcp_connect",
        "test_command": "Use MCP: context7"
      },
      "os_support": ["macos", "linux", "windows"],
      "manual_only": false
    }
  ],
  "counts": {
    "total": 1,
    "required": 1,
    "optional": 0,
    "by_category": {
      "mcp": 1
    }
  }
}
```

## Local profile state

`~/.flux/profile-state.json`

```json
{
  "schema_version": "1",
  "saved_applications": {
    "granola": {
      "first_saved_at": "2026-02-22T12:00:00Z",
      "last_selected_at": "2026-02-22T12:00:00Z",
      "last_seen_state": "installed",
      "priority": "optional"
    }
  },
  "published_profiles": {
    "prf-123": {
      "url": "https://profiles.example/p/prf-123",
      "manage_token": "token-xyz",
      "status": "active",
      "created_at": "2026-02-22T12:00:00Z"
    }
  },
  "last_exported_at": "2026-02-22T12:00:00Z"
}
```

## Notes

- Skills de-dup identity in `both` mode is `name + content hash`.
- Missing saved apps remain in state with `last_seen_state=missing`.
- Saved app entries can be removed with `profile-manager.py saved-apps --remove <csv>`.
- Snapshot metadata excludes usernames, repo paths, hostnames, and local absolute paths.
