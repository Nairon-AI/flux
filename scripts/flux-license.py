#!/usr/bin/env python3
"""Flux Pro License Management.

Validates and caches Polar.sh license keys for Flux Pro features.

Usage:
    python3 flux-license.py activate <key>       # Validate + store license key
    python3 flux-license.py deactivate            # Remove license key
    python3 flux-license.py status                # Show license status
    python3 flux-license.py status --format json  # JSON output
    python3 flux-license.py check                 # Exit 0 if Pro, 1 if free (for scripts)
"""

import argparse
import hashlib
import json
import os
import platform
import re
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# =============================================================================
# CONSTANTS
# =============================================================================

CONFIG_FILE = Path.home() / ".flux" / "config.json"
POLAR_VALIDATE_URL = "https://api.polar.sh/v1/customer-portal/license-keys/validate"
POLAR_ACTIVATE_URL = "https://api.polar.sh/v1/customer-portal/license-keys/activate"
POLAR_DEACTIVATE_URL = "https://api.polar.sh/v1/customer-portal/license-keys/deactivate"
POLAR_ORG_ID = "3a10c412-6423-45ee-97f5-439501dbc2c2"
PRODUCT_IDS = {
    "monthly": "f8a4ce6e-9034-4881-8fbe-f45186368864",
    "yearly": "768ef726-83d0-42fc-9dd8-4a2a17490193",
}
CACHE_TTL_SECONDS = 24 * 60 * 60  # 24 hours
CHECKOUT_URL = "https://buy.polar.sh/polar_cl_mvTstXLrEX4XyDe0dzS7WMdpnaSCmxPkIVjq01dbj0D"


# =============================================================================
# DEBUG LOGGING
# =============================================================================


def debug_log(msg: str) -> None:
    """Log to stderr when FLUX_LICENSE_DEBUG=1 or FLUX_UNIVERSE_DEBUG=1."""
    if os.environ.get("FLUX_LICENSE_DEBUG") != "1" and os.environ.get("FLUX_UNIVERSE_DEBUG") != "1":
        return
    # Redact license keys
    # Redact any license key patterns (Polar keys are UUIDs or custom format)
    redacted = re.sub(r"[A-Z0-9]{8}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{12}", "****-****-****-****-****", msg, flags=re.IGNORECASE)
    print(f"[flux-license] {redacted}", file=sys.stderr)


# =============================================================================
# MACHINE ID
# =============================================================================


def get_machine_id() -> str:
    """Generate a stable machine identifier for license activation.

    Uses hostname + platform info hashed to a short ID. Not PII.
    """
    raw = f"{platform.node()}-{platform.system()}-{platform.machine()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# =============================================================================
# CONFIG FILE MANAGEMENT
# =============================================================================


def load_config() -> dict:
    """Load config from ~/.flux/config.json. Returns empty dict if missing."""
    if not CONFIG_FILE.exists():
        return {}
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(config: dict) -> None:
    """Save config atomically with 0600 permissions."""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(
        dir=str(CONFIG_FILE.parent),
        prefix=".config-",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(config, f, indent=2)
        os.chmod(tmp_path, 0o600)
        os.replace(tmp_path, str(CONFIG_FILE))
        debug_log("Config saved")
    except OSError:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# =============================================================================
# POLAR API
# =============================================================================


def _polar_request(url: str, body: dict, timeout: int = 10) -> tuple[int, dict]:
    """Make a POST request to Polar API. Returns (status, body)."""
    debug_log(f"POST {url}")
    data = json.dumps(body).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")

    try:
        with urlopen(req, timeout=timeout) as resp:
            resp_body = resp.read().decode("utf-8")
            parsed = json.loads(resp_body) if resp_body else {}
            debug_log(f"HTTP {resp.status}")
            return (resp.status, parsed)
    except HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
            parsed = json.loads(err_body) if err_body else {}
            return (e.code, parsed)
        except (json.JSONDecodeError, OSError):
            return (e.code, {"error": str(e)})
    except URLError as e:
        debug_log(f"Network error: {e}")
        return (0, {"error": f"Network error: {e.reason}"})
    except OSError as e:
        debug_log(f"Connection error: {e}")
        return (0, {"error": str(e)})


def validate_key(key: str) -> tuple[bool, dict]:
    """Validate a license key via Polar API (no auth needed).

    Returns (is_valid, response_data).
    """
    status, body = _polar_request(POLAR_VALIDATE_URL, {"key": key, "organization_id": POLAR_ORG_ID})

    if status == 0:
        debug_log("Network error during validation")
        return (False, {"error": "network_error", "message": body.get("error", "Could not reach Polar API")})

    if status == 200:
        is_valid = body.get("valid", body.get("is_valid", False))
        return (is_valid, body)

    return (False, body)


def activate_key(key: str) -> tuple[bool, dict]:
    """Activate a license key instance via Polar API.

    Returns (success, response_data).
    """
    machine_id = get_machine_id()
    status, body = _polar_request(POLAR_ACTIVATE_URL, {
        "key": key,
        "organization_id": POLAR_ORG_ID,
        "label": f"flux-cli-{platform.node()[:20]}",
    })

    if status == 200:
        return (True, body)
    return (False, body)


# =============================================================================
# LICENSE STATE
# =============================================================================


def get_license() -> dict | None:
    """Get current license from config. Returns None if no license."""
    config = load_config()
    license_data = config.get("license")
    if not license_data or not license_data.get("key"):
        return None
    return license_data


def is_pro() -> bool:
    """Check if user has a valid Pro license (cached, no network).

    Returns True if license exists and cache hasn't expired.
    For strict validation, use validate_or_cache().
    """
    license_data = get_license()
    if not license_data:
        return False

    validated_at = license_data.get("validated_at", "")
    if not validated_at:
        return False

    try:
        from datetime import datetime, timezone
        validated_time = datetime.fromisoformat(validated_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        age_seconds = (now - validated_time).total_seconds()
        return age_seconds < CACHE_TTL_SECONDS
    except (ValueError, TypeError):
        return False


def validate_or_cache(key: str | None = None) -> tuple[bool, str]:
    """Validate license key, using cache if fresh enough.

    Returns (is_valid, message).
    """
    config = load_config()
    license_data = config.get("license", {})

    if key is None:
        key = license_data.get("key")
    if not key:
        return (False, "No license key configured")

    # Check cache freshness
    validated_at = license_data.get("validated_at", "")
    if validated_at and license_data.get("key") == key:
        try:
            from datetime import datetime, timezone
            validated_time = datetime.fromisoformat(validated_at.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            age_seconds = (now - validated_time).total_seconds()
            if age_seconds < CACHE_TTL_SECONDS:
                debug_log(f"Cache hit (age: {int(age_seconds)}s)")
                return (True, "License valid (cached)")
        except (ValueError, TypeError):
            pass

    # Cache miss or expired — validate with Polar
    debug_log("Cache miss, validating with Polar")
    is_valid, resp = validate_key(key)

    if is_valid:
        license_data["key"] = key
        license_data["tier"] = "pro"
        license_data["validated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        license_data["valid"] = True
        config["license"] = license_data
        save_config(config)
        return (True, "License valid")

    # Network error — be graceful, use stale cache if exists
    if resp.get("error") == "network_error" and license_data.get("valid"):
        debug_log("Network error but have stale cache, accepting")
        return (True, "License valid (offline, cached)")

    # Invalid key — clear cache
    if license_data.get("key") == key:
        license_data["valid"] = False
        license_data["validated_at"] = ""
        config["license"] = license_data
        save_config(config)

    msg = resp.get("message", resp.get("detail", "License key is not valid"))
    return (False, msg)


def should_show_upgrade_prompt() -> bool:
    """Check if we should show upgrade prompt (max 1x per session).

    Uses a timestamp file to track. Returns True if no prompt shown today.
    """
    prompt_file = Path.home() / ".flux" / ".last_upgrade_prompt"
    if not prompt_file.exists():
        return True

    try:
        last_ts = prompt_file.read_text().strip()
        from datetime import datetime, timezone
        last_time = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        # Allow one prompt per 8 hours (roughly per session)
        return (now - last_time).total_seconds() > 8 * 60 * 60
    except (ValueError, TypeError, OSError):
        return True


def mark_upgrade_prompt_shown() -> None:
    """Record that upgrade prompt was shown."""
    prompt_file = Path.home() / ".flux" / ".last_upgrade_prompt"
    prompt_file.parent.mkdir(parents=True, exist_ok=True)
    prompt_file.write_text(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))


# =============================================================================
# COMMANDS
# =============================================================================


def cmd_activate(args) -> int:
    """Activate a Flux Pro license key."""
    key = args.key.strip()

    if not key:
        print("Please provide a license key.", file=sys.stderr)
        print(f"Get one at: {CHECKOUT_URL}", file=sys.stderr)
        return 1

    print("Validating license key...")
    is_valid, resp = validate_key(key)

    if not is_valid:
        msg = resp.get("message", resp.get("detail", "Unknown error"))
        if resp.get("error") == "network_error":
            print(f"Could not reach Polar API: {msg}", file=sys.stderr)
            print("Check your internet connection and try again.", file=sys.stderr)
        else:
            print(f"Invalid license key: {msg}", file=sys.stderr)
            print(f"Get a valid key at: {CHECKOUT_URL}", file=sys.stderr)
        return 1

    # Activate instance
    print("Activating on this machine...")
    activated, act_resp = activate_key(key)
    activation_id = act_resp.get("id", "") if activated else ""

    # Store in config
    config = load_config()
    config["license"] = {
        "key": key,
        "tier": "pro",
        "valid": True,
        "validated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "activation_id": activation_id,
    }
    save_config(config)

    print("")
    print("Flux Pro activated!")
    print("You now have access to:")
    print("  - Stack-aware recommendations ranked by community data")
    print("  - Weekly-updated recommendation database (50+ tools)")
    print("  - Friction signal resurface with fresh recommendations")
    print("")
    print("Run /flux:improve to get your first Pro recommendations.")
    return 0


def cmd_deactivate(args) -> int:
    """Deactivate and remove license key."""
    config = load_config()
    license_data = config.get("license", {})

    if not license_data.get("key"):
        print("No license key configured.")
        return 0

    # Deactivate with Polar if we have an activation ID
    activation_id = license_data.get("activation_id")
    if activation_id:
        print("Deactivating license...")
        _polar_request(POLAR_DEACTIVATE_URL, {"key": license_data["key"], "organization_id": POLAR_ORG_ID, "activation_id": activation_id})

    # Remove from config
    config.pop("license", None)
    save_config(config)

    print("License key removed. Flux will use free recommendations.")
    return 0


def cmd_status(args) -> int:
    """Show license status."""
    license_data = get_license()

    if args.format == "json":
        if license_data and license_data.get("valid"):
            result = {
                "tier": "pro",
                "valid": True,
                "validated_at": license_data.get("validated_at", ""),
                "key_prefix": license_data.get("key", "")[:9] + "...",
            }
        else:
            result = {"tier": "free", "valid": False}
        print(json.dumps(result, indent=2))
        return 0

    if license_data and license_data.get("valid"):
        key = license_data.get("key", "")
        key_display = key[:9] + "..." + key[-4:] if len(key) > 13 else key[:9] + "..."
        print(f"Flux Pro (active)")
        print(f"  Key: {key_display}")
        print(f"  Validated: {license_data.get('validated_at', 'unknown')}")

        # Check cache freshness
        valid = is_pro()
        if not valid:
            print("  Cache: expired (will re-validate on next use)")
        else:
            print("  Cache: fresh")
    else:
        print("Flux Free")
        print(f"  Upgrade to Pro: {CHECKOUT_URL}")
        print("  Run: python3 flux-license.py activate <YOUR-KEY>")

    return 0


def cmd_check(args) -> int:
    """Silent check — exit 0 if Pro, exit 1 if free. For scripting."""
    if is_pro():
        return 0

    # Try revalidation if we have a key
    license_data = get_license()
    if license_data and license_data.get("key"):
        valid, _ = validate_or_cache(license_data["key"])
        return 0 if valid else 1

    return 1


# =============================================================================
# CLI
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Manage Flux Pro license",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  flux-license.py activate <YOUR-LICENSE-KEY>     # Activate Pro
  flux-license.py deactivate                       # Remove license
  flux-license.py status                           # Show status
  flux-license.py check                            # Script check (exit code)

Get Flux Pro: {CHECKOUT_URL}
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="License commands")

    activate_parser = subparsers.add_parser("activate", help="Activate a license key")
    activate_parser.add_argument("key", help="Flux Pro license key (from your Polar checkout email)")

    subparsers.add_parser("deactivate", help="Remove license key")

    status_parser = subparsers.add_parser("status", help="Show license status")
    status_parser.add_argument(
        "--format", "-f",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )

    subparsers.add_parser("check", help="Exit 0 if Pro, 1 if free (for scripts)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        "activate": cmd_activate,
        "deactivate": cmd_deactivate,
        "status": cmd_status,
        "check": cmd_check,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
