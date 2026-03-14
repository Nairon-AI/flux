"""
fluxctl_pkg.config - Config loading/saving, defaults, deep_merge.
"""

import json
import os
import sys
from pathlib import Path

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


