#!/usr/bin/env python3
"""Flux Universe Auth.

Manages device-flow authentication with Universe for syncing Flux data.

Usage:
    python3 flux-auth.py login                  # Device login flow
    python3 flux-auth.py logout                 # Remove auth file
    python3 flux-auth.py status                 # Show connection status
    python3 flux-auth.py status --format json   # JSON output
"""

import argparse
import json
import os
import re
import stat
import sys
import tempfile
import time
import webbrowser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# =============================================================================
# CONSTANTS
# =============================================================================

AUTH_FILE = Path.home() / ".flux" / "universe-auth.json"
CONFIG_FILE = Path.home() / ".flux" / "config.json"
SCHEMA_VERSION = 1
DEFAULT_API_URL = "https://universe.naironai.com"
FLUX_CLIENT_ID = "flux-cli"
FLUX_CLIENT_VERSION = "0.1.0"


# =============================================================================
# DEBUG LOGGING
# =============================================================================


def debug_log(msg: str) -> None:
    """Log to stderr when FLUX_UNIVERSE_DEBUG=1.

    Never logs secrets. Redacts tokens, bearer values, and deviceCode.
    """
    if os.environ.get("FLUX_UNIVERSE_DEBUG") != "1":
        return

    redacted = msg
    redacted = re.sub(
        r'("(?:accessToken|deviceCode|token)"\s*:\s*")[^"]+(")',
        r"\1***REDACTED***\2",
        redacted,
    )
    redacted = re.sub(r"(Bearer\s+)[^\s]+", r"\1***REDACTED***", redacted)
    redacted = re.sub(r"(flux_)[A-Za-z0-9._-]+", r"\1***REDACTED***", redacted)
    print(f"[flux-auth] {redacted}", file=sys.stderr)


# =============================================================================
# API URL RESOLUTION
# =============================================================================


def get_api_url() -> str:
    """Resolve Universe API URL from env > config > default."""
    env_url = os.environ.get("FLUX_UNIVERSE_API_URL")
    if env_url:
        debug_log(f"API URL from env: {env_url}")
        return env_url.rstrip("/")

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
            url = config.get("universe_api_url")
            if url:
                debug_log(f"API URL from config: {url}")
                return url.rstrip("/")
        except (json.JSONDecodeError, OSError):
            pass

    debug_log(f"API URL default: {DEFAULT_API_URL}")
    return DEFAULT_API_URL


# =============================================================================
# HTTP HELPER
# =============================================================================


def api_request(
    method: str,
    path: str,
    body: dict | None = None,
    token: str | None = None,
    timeout: int = 10,
) -> tuple:
    """Make an HTTP request to the Universe API.

    Returns (status_code, response_body_dict).
    On network error, returns (0, {"error": "message"}).
    """
    url = f"{get_api_url()}{path}"
    debug_log(f"{method} {url}")

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = Request(url, data=data, headers=headers, method=method)

    try:
        with urlopen(req, timeout=timeout) as resp:
            resp_body = resp.read().decode("utf-8")
            try:
                parsed = json.loads(resp_body) if resp_body else {}
                debug_log(f"HTTP {resp.status} body={json.dumps(parsed)}")
                return (resp.status, parsed)
            except json.JSONDecodeError:
                return (resp.status, {"raw": resp_body})
    except HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
            parsed = json.loads(err_body) if err_body else {}
            debug_log(f"HTTP {e.code} body={json.dumps(parsed)}")
            return (e.code, parsed)
        except (json.JSONDecodeError, OSError):
            return (e.code, {"error": str(e)})
    except URLError as e:
        debug_log(f"Network error: {e}")
        return (0, {"error": f"Network error: {e.reason}"})
    except OSError as e:
        debug_log(f"Connection error: {e}")
        return (0, {"error": str(e)})


# =============================================================================
# AUTH FILE MANAGEMENT
# =============================================================================


def load_auth() -> dict | None:
    """Load auth data from ~/.flux/universe-auth.json.

    Returns None if file doesn't exist, is corrupt, or has wrong schema version.
    """
    if not AUTH_FILE.exists():
        debug_log("Auth file not found")
        return None

    try:
        with open(AUTH_FILE, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        debug_log(f"Auth file corrupt: {e}")
        return None

    if data.get("schemaVersion") != SCHEMA_VERSION:
        debug_log(
            f"Schema version mismatch: {data.get('schemaVersion')} != {SCHEMA_VERSION}"
        )
        return None

    return data


def save_auth(data: dict) -> None:
    """Save auth data atomically with 0600 permissions."""
    AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)

    data["schemaVersion"] = SCHEMA_VERSION
    data["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if "issuedAt" not in data:
        data["issuedAt"] = data["updatedAt"]

    fd, tmp_path = tempfile.mkstemp(
        dir=str(AUTH_FILE.parent),
        prefix=".universe-auth-",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
        os.chmod(tmp_path, stat.S_IRUSR | stat.S_IWUSR)
        os.replace(tmp_path, str(AUTH_FILE))
        debug_log("Auth file saved")
    except OSError:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def delete_auth() -> None:
    """Delete auth file. Idempotent - no error if missing."""
    try:
        AUTH_FILE.unlink()
        debug_log("Auth file deleted")
    except FileNotFoundError:
        debug_log("Auth file already absent")


# =============================================================================
# LOGIN FLOW
# =============================================================================


def _device_login() -> tuple[bool, dict]:
    """Run device login flow.

    Returns (success, approved_body).
    """
    status, body = api_request(
        "POST",
        "/api/flux/device/start",
        {"clientId": FLUX_CLIENT_ID, "clientVersion": FLUX_CLIENT_VERSION},
    )

    if status == 0:
        print(f"Could not reach Universe: {body.get('error', 'unknown')}", file=sys.stderr)
        return (False, {})

    if status != 200:
        print(f"Device login start failed (HTTP {status}).", file=sys.stderr)
        return (False, {})

    device_code = body.get("deviceCode")
    user_code = body.get("userCode")
    verification_uri = body.get("verificationUri")
    verification_uri_complete = body.get("verificationUriComplete")
    expires_in = int(body.get("expiresIn", 0) or 0)
    interval = int(body.get("interval", 5) or 5)

    if not device_code or not user_code or not verification_uri:
        print("Invalid device login response from server.", file=sys.stderr)
        return (False, {})

    print("Opening browser...")
    print(f"Sign in at {verification_uri}")
    print(f"Your code: {user_code}")

    try:
        webbrowser.open(verification_uri_complete or verification_uri)
    except Exception:
        pass

    deadline = time.time() + max(1, expires_in)
    poll_delay = max(1, interval)

    while time.time() < deadline:
        time.sleep(poll_delay)
        poll_status, poll_body = api_request(
            "POST", "/api/flux/device/poll", {"deviceCode": device_code}
        )

        state = poll_body.get("status")

        if poll_status == 202 and state == "pending":
            continue

        if poll_status == 200 and state == "approved":
            if poll_body.get("accessToken"):
                return (True, poll_body)
            print("Invalid approval response from server.", file=sys.stderr)
            return (False, {})

        if poll_status == 400 and state == "denied":
            print("Authentication was denied.", file=sys.stderr)
            return (False, {})

        if poll_status == 400 and state == "expired":
            print("Authentication expired. Please run login again.", file=sys.stderr)
            return (False, {})

        if poll_status == 0:
            continue

        print("Unexpected response while waiting for approval.", file=sys.stderr)
        return (False, {})

    print("Authentication expired. Please run login again.", file=sys.stderr)
    return (False, {})


def _save_login_response(body: dict) -> None:
    """Save a successful login response to auth file."""
    user = body.get("user") if isinstance(body.get("user"), dict) else None
    if not user:
        username = body.get("username")
        user = {"handle": username} if username else {}

    auth_data = {
        "accessToken": body.get("accessToken", ""),
        "tokenType": body.get("tokenType", "Bearer"),
        "user": user,
    }
    save_auth(auth_data)


# =============================================================================
# COMMANDS
# =============================================================================


def cmd_login(args) -> int:
    """Handle the login subcommand."""
    existing = load_auth()
    if existing:
        prev_handle = existing.get("user", {}).get(
            "handle", existing.get("user", {}).get("email", "unknown")
        )
        print(f"Already connected as {prev_handle}. Re-authenticating...")

    success, body = _device_login()
    if not success:
        return 1

    _save_login_response(body)
    handle = body.get("username") or body.get("user", {}).get("handle") or "unknown"
    print(f"✓ Logged in as @{handle}")
    print("Flux will sync stats to your Universe profile.")
    return 0


def cmd_logout(args) -> int:
    """Handle the logout subcommand."""
    auth = load_auth()
    delete_auth()
    if auth:
        handle = auth.get("user", {}).get("handle", auth.get("user", {}).get("email", "unknown"))
        print(f"Disconnected {handle} from Universe.")
    else:
        print("Not connected to Universe.")
    return 0


def cmd_status(args) -> int:
    """Handle the status subcommand."""
    auth = load_auth()

    if args.format == "json":
        if auth:
            safe = {
                "connected": True,
                "user": auth.get("user", {}),
                "issuedAt": auth.get("issuedAt"),
                "updatedAt": auth.get("updatedAt"),
            }
        else:
            safe = {"connected": False}
        print(json.dumps(safe, indent=2))
        return 0

    if auth:
        user = auth.get("user", {})
        handle = user.get("handle", user.get("email", "unknown"))
        print(f"Connected to Universe as @{handle}")
        if user.get("email"):
            print(f"  Email: {user['email']}")
        if auth.get("issuedAt"):
            print(f"  Since: {auth['issuedAt']}")
    else:
        print("Not connected to Universe.")
        print("Run 'flux-auth.py login' to connect.")

    return 0


# =============================================================================
# CLI
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Manage Flux Universe authentication",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  flux-auth.py login                  # Device login flow
  flux-auth.py logout                 # Disconnect
  flux-auth.py status                 # Show connection status
  flux-auth.py status --format json   # JSON output
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Auth commands")

    subparsers.add_parser("login", help="Connect to Universe")
    subparsers.add_parser("logout", help="Disconnect from Universe")

    status_parser = subparsers.add_parser("status", help="Show connection status")
    status_parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        "login": cmd_login,
        "logout": cmd_logout,
        "status": cmd_status,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
