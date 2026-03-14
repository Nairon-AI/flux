"""
fluxctl_pkg.config - Config loading/saving, defaults, deep_merge, memory commands.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from .utils import (
    CONFIG_FILE,
    MEMORY_DIR,
    atomic_write,
    atomic_write_json,
    ensure_flux_exists,
    error_exit,
    get_flux_dir,
    json_output,
)


def get_default_config() -> dict:
    """Return default config structure."""
    return {
        "memory": {"enabled": True},
        "planSync": {"enabled": True, "crossEpic": False},
        "review": {
            "backend": None,
            "reviewer1": None,
            "reviewer2": None,
            "bot": None,
            "severities": ["critical", "major"],
        },
        "scouts": {"github": False},
        "tracker": {"provider": None, "teamId": None},
        "workflow": {
            "technicalLevel": "semi_technical",
            "defaultScopeMode": "shallow",
            "defaultImplementationTarget": "self_with_ai",
            "autoResume": True,
        },
    }


def deep_merge(base: dict, override: dict) -> dict:
    """Deep merge override into base. Override values win for conflicts."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_flux_config() -> dict:
    """Load .flux/config.json, merging with defaults for missing keys."""
    config_path = get_flux_dir() / CONFIG_FILE
    defaults = get_default_config()
    if not config_path.exists():
        return defaults
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return deep_merge(defaults, data)
        return defaults
    except (json.JSONDecodeError, Exception):
        return defaults


def get_config(key: str, default=None):
    """Get nested config value like 'memory.enabled'."""
    config = load_flux_config()
    for part in key.split("."):
        if not isinstance(config, dict):
            return default
        config = config.get(part, {})
        if config == {}:
            return default
    return config if config != {} else default


def set_config(key: str, value) -> dict:
    """Set nested config value and return updated config."""
    config_path = get_flux_dir() / CONFIG_FILE
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, Exception):
            config = get_default_config()
    else:
        config = get_default_config()

    # Navigate/create nested path
    parts = key.split(".")
    current = config
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]

    # Set the value (handle type conversion for common cases)
    if isinstance(value, str):
        if value.lower() == "true":
            value = True
        elif value.lower() == "false":
            value = False
        elif value.isdigit():
            value = int(value)

    current[parts[-1]] = value
    atomic_write_json(config_path, config)
    return config


MEMORY_TEMPLATES = {
    "pitfalls.md": """# Pitfalls

Lessons learned from NEEDS_WORK feedback. Things models tend to miss.

<!-- Entries added automatically by hooks or manually via `fluxctl memory add` -->
""",
    "conventions.md": """# Conventions

Project patterns discovered during work. Not in CLAUDE.md but important.

<!-- Entries added manually via `fluxctl memory add` -->
""",
    "decisions.md": """# Decisions

Architectural choices with rationale. Why we chose X over Y.

<!-- Entries added manually via `fluxctl memory add` -->
""",
}


def require_memory_enabled(args) -> Path:
    """Check memory is enabled and return memory dir. Exits on error."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    if not get_config("memory.enabled", False):
        if args.json:
            json_output(
                {
                    "error": "Memory not enabled. Run: fluxctl config set memory.enabled true"
                },
                success=False,
            )
        else:
            print("Error: Memory not enabled.")
            print("Enable with: fluxctl config set memory.enabled true")
        sys.exit(1)

    memory_dir = get_flux_dir() / MEMORY_DIR
    required_files = ["pitfalls.md", "conventions.md", "decisions.md"]
    missing = [f for f in required_files if not (memory_dir / f).exists()]
    if missing:
        if args.json:
            json_output(
                {"error": "Memory not initialized. Run: fluxctl memory init"},
                success=False,
            )
        else:
            print("Error: Memory not initialized.")
            print("Run: fluxctl memory init")
        sys.exit(1)

    return memory_dir


def cmd_config_get(args) -> None:
    """Get a config value."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    value = get_config(args.key)
    if args.json:
        json_output({"key": args.key, "value": value})
    else:
        if value is None:
            print(f"{args.key}: (not set)")
        elif isinstance(value, bool):
            print(f"{args.key}: {'true' if value else 'false'}")
        else:
            print(f"{args.key}: {value}")


def cmd_config_set(args) -> None:
    """Set a config value."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    set_config(args.key, args.value)
    new_value = get_config(args.key)

    if args.json:
        json_output({"key": args.key, "value": new_value, "message": f"{args.key} set"})
    else:
        print(f"{args.key} set to {new_value}")


def cmd_review_backend(args) -> None:
    """Get review backend for skill conditionals. Returns ASK if not configured."""
    # Priority: FLUX_REVIEW_BACKEND env > config > ASK
    env_val = os.environ.get("FLUX_REVIEW_BACKEND", "").strip()
    if env_val and env_val in ("rp", "codex", "none"):
        backend = env_val
        source = "env"
    elif ensure_flux_exists():
        cfg_val = get_config("review.backend")
        if cfg_val and cfg_val in ("rp", "codex", "none"):
            backend = cfg_val
            source = "config"
        else:
            backend = "ASK"
            source = "none"
    else:
        backend = "ASK"
        source = "none"

    if args.json:
        json_output({"backend": backend, "source": source})
    else:
        print(backend)


def cmd_memory_init(args) -> None:
    """Initialize memory directory with templates."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    # Check if memory is enabled
    if not get_config("memory.enabled", False):
        if args.json:
            json_output(
                {
                    "error": "Memory not enabled. Run: fluxctl config set memory.enabled true"
                },
                success=False,
            )
        else:
            print("Error: Memory not enabled.")
            print("Enable with: fluxctl config set memory.enabled true")
        sys.exit(1)

    flux_dir = get_flux_dir()
    memory_dir = flux_dir / MEMORY_DIR

    # Create memory dir if missing
    memory_dir.mkdir(parents=True, exist_ok=True)

    created = []
    for filename, content in MEMORY_TEMPLATES.items():
        filepath = memory_dir / filename
        if not filepath.exists():
            atomic_write(filepath, content)
            created.append(filename)

    if args.json:
        json_output(
            {
                "path": str(memory_dir),
                "created": created,
                "message": "Memory initialized"
                if created
                else "Memory already initialized",
            }
        )
    else:
        if created:
            print(f"Memory initialized at {memory_dir}")
            for f in created:
                print(f"  Created: {f}")
        else:
            print(f"Memory already initialized at {memory_dir}")


def cmd_memory_add(args) -> None:
    """Add a memory entry manually."""
    memory_dir = require_memory_enabled(args)

    # Map type to file
    type_map = {
        "pitfall": "pitfalls.md",
        "pitfalls": "pitfalls.md",
        "convention": "conventions.md",
        "conventions": "conventions.md",
        "decision": "decisions.md",
        "decisions": "decisions.md",
    }

    filename = type_map.get(args.type.lower())
    if not filename:
        error_exit(
            f"Invalid type '{args.type}'. Use: pitfall, convention, or decision",
            use_json=args.json,
        )

    filepath = memory_dir / filename
    if not filepath.exists():
        error_exit(
            f"Memory file {filename} not found. Run: fluxctl memory init",
            use_json=args.json,
        )

    # Format entry
    from datetime import datetime

    today = datetime.utcnow().strftime("%Y-%m-%d")

    # Normalize type name
    type_name = args.type.lower().rstrip("s")  # pitfalls -> pitfall

    entry = f"""
## {today} manual [{type_name}]
{args.content}
"""

    # Append to file
    with filepath.open("a", encoding="utf-8") as f:
        f.write(entry)

    if args.json:
        json_output(
            {"type": type_name, "file": filename, "message": f"Added {type_name} entry"}
        )
    else:
        print(f"Added {type_name} entry to {filename}")


def cmd_memory_read(args) -> None:
    """Read memory entries."""
    memory_dir = require_memory_enabled(args)

    # Determine which files to read
    if args.type:
        type_map = {
            "pitfall": "pitfalls.md",
            "pitfalls": "pitfalls.md",
            "convention": "conventions.md",
            "conventions": "conventions.md",
            "decision": "decisions.md",
            "decisions": "decisions.md",
        }
        filename = type_map.get(args.type.lower())
        if not filename:
            error_exit(
                f"Invalid type '{args.type}'. Use: pitfalls, conventions, or decisions",
                use_json=args.json,
            )
        files = [filename]
    else:
        files = ["pitfalls.md", "conventions.md", "decisions.md"]

    content = {}
    for filename in files:
        filepath = memory_dir / filename
        if filepath.exists():
            content[filename] = filepath.read_text(encoding="utf-8")
        else:
            content[filename] = ""

    if args.json:
        json_output({"files": content})
    else:
        for filename, text in content.items():
            if text.strip():
                print(f"=== {filename} ===")
                print(text)
                print()


def cmd_memory_list(args) -> None:
    """List memory entry counts."""
    memory_dir = require_memory_enabled(args)

    counts = {}
    for filename in ["pitfalls.md", "conventions.md", "decisions.md"]:
        filepath = memory_dir / filename
        if filepath.exists():
            text = filepath.read_text(encoding="utf-8")
            # Count ## entries (each entry starts with ## date)
            entries = len(re.findall(r"^## \d{4}-\d{2}-\d{2}", text, re.MULTILINE))
            counts[filename] = entries
        else:
            counts[filename] = 0

    if args.json:
        json_output({"counts": counts, "total": sum(counts.values())})
    else:
        total = 0
        for filename, count in counts.items():
            print(f"  {filename}: {count} entries")
            total += count
        print(f"  Total: {total} entries")


def cmd_memory_search(args) -> None:
    """Search memory entries."""
    memory_dir = require_memory_enabled(args)

    pattern = args.pattern

    # Validate regex pattern
    try:
        re.compile(pattern)
    except re.error as e:
        error_exit(f"Invalid regex pattern: {e}", use_json=args.json)

    matches = []

    for filename in ["pitfalls.md", "conventions.md", "decisions.md"]:
        filepath = memory_dir / filename
        if not filepath.exists():
            continue

        text = filepath.read_text(encoding="utf-8")
        # Split into entries
        entries = re.split(r"(?=^## \d{4}-\d{2}-\d{2})", text, flags=re.MULTILINE)

        for entry in entries:
            if not entry.strip():
                continue
            if re.search(pattern, entry, re.IGNORECASE):
                matches.append({"file": filename, "entry": entry.strip()})

    if args.json:
        json_output({"pattern": pattern, "matches": matches, "count": len(matches)})
    else:
        if matches:
            for m in matches:
                print(f"=== {m['file']} ===")
                print(m["entry"])
                print()
            print(f"Found {len(matches)} matches")
        else:
            print(f"No matches for '{pattern}'")
