"""
fluxctl_pkg.config - Config loading/saving, defaults, deep_merge.
"""

import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from .utils import (
    CONFIG_FILE,
    atomic_write_json,
    ensure_flux_exists,
    error_exit,
    get_flux_dir,
    json_output,
)


def get_default_config() -> dict:
    """Return default config structure."""
    return {
        "planSync": {"enabled": True, "crossEpic": False},
        "review": {
            "backend": None,
            "reviewer1": None,
            "reviewer2": None,
            "bot": None,
            "severities": ["critical", "major"],
            "humanReview": False,
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


def ensure_config_file() -> Path:
    """Create config.json with defaults if it does not exist."""
    config_path = get_flux_dir() / CONFIG_FILE
    if not config_path.exists():
        atomic_write_json(config_path, get_default_config())
    return config_path


def load_raw_config(strict: bool = False) -> dict:
    """Load config.json without merging defaults."""
    config_path = get_flux_dir() / CONFIG_FILE
    if not config_path.exists():
        return {}

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        if strict:
            raise ValueError(f"Invalid JSON in {config_path}: {exc}") from exc
        return {}
    except Exception as exc:
        if strict:
            raise ValueError(f"Unable to read {config_path}: {exc}") from exc
        return {}

    if not isinstance(data, dict):
        if strict:
            raise ValueError(f"{config_path} must contain a JSON object.")
        return {}

    return data


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
    defaults = get_default_config()
    data = load_raw_config(strict=False)
    return deep_merge(defaults, data)


def get_config(key: str, default=None):
    """Get nested config value like 'review.backend'."""
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
    config_path = ensure_config_file()
    config = load_raw_config(strict=False) or get_default_config()

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


def resolve_editor(editor: Optional[str] = None) -> Optional[List[str]]:
    """Resolve an editor command to execute."""
    candidates: List[str] = []

    if editor:
        candidates.append(editor)

    for env_key in ("VISUAL", "EDITOR"):
        env_val = os.environ.get(env_key, "").strip()
        if env_val:
            candidates.append(env_val)

    if os.name == "nt":
        candidates.extend(["code --wait", "notepad"])
    else:
        candidates.extend(["code --wait", "nano", "vi"])

    for candidate in candidates:
        parts = shlex.split(candidate)
        if parts and shutil.which(parts[0]):
            return parts

    return None


def cmd_config_list(args) -> None:
    """List the full config."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    config_path = get_flux_dir() / CONFIG_FILE
    try:
        config = deep_merge(get_default_config(), load_raw_config(strict=True))
    except ValueError as exc:
        error_exit(str(exc), use_json=args.json)
        return

    if args.json:
        json_output({"path": str(config_path), "config": config})
    else:
        print(f"Config path: {config_path}")
        print(json.dumps(config, indent=2, sort_keys=True))


def cmd_config_toggle(args) -> None:
    """Toggle a boolean config value."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    current = get_config(args.key)
    if not isinstance(current, bool):
        error_exit(
            f"{args.key} is not a boolean config value and cannot be toggled.",
            use_json=args.json,
        )

    new_value = not current
    set_config(args.key, new_value)

    if args.json:
        json_output({"key": args.key, "value": new_value, "message": f"{args.key} toggled"})
    else:
        print(f"{args.key} set to {new_value}")


def cmd_config_edit(args) -> None:
    """Open config.json in the user's editor."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    config_path = ensure_config_file()
    editor_cmd = resolve_editor(args.editor)
    if not editor_cmd:
        error_exit(
            f"No editor found. Set $EDITOR or use --editor. Config file: {config_path}",
            use_json=args.json,
        )

    try:
        result = subprocess.run([*editor_cmd, str(config_path)], check=False)
    except Exception as exc:
        error_exit(
            f"Failed to launch editor {' '.join(editor_cmd)}: {exc}",
            use_json=args.json,
        )
        return

    if result.returncode != 0:
        error_exit(
            f"Editor exited with status {result.returncode}. Config file: {config_path}",
            code=result.returncode,
            use_json=args.json,
        )

    if args.json:
        json_output({"path": str(config_path), "editor": " ".join(editor_cmd)})
    else:
        print(f"Edited {config_path} with {' '.join(editor_cmd)}")


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
