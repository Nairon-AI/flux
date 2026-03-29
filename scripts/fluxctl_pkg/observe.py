"""
fluxctl_pkg.observe - Background observer runtime-state helpers and commands.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from pathlib import Path

from .utils import (
    LOCK_EX,
    LOCK_UN,
    OBSERVE_MODES,
    _flock,
    atomic_write_json,
    ensure_flux_exists,
    error_exit,
    get_state_dir,
    json_output,
    load_json,
    now_iso,
)

OBSERVE_STATE_FILE = "observe_state.json"


def observe_state_path() -> Path:
    """Return the persisted observer runtime-state path."""
    return get_state_dir() / OBSERVE_STATE_FILE


def default_observe_state() -> dict:
    """Default observer state when no runtime file exists yet."""
    return {
        "mode": "off",
        "started_at": None,
        "stopped_at": None,
        "updated_at": None,
        "last_event_at": None,
        "target": None,
        "session_name": None,
        "last_error": None,
        "findings_queued": 0,
    }


def normalize_observe_state(value: object) -> dict:
    """Normalize observer state loaded from disk."""
    state = default_observe_state()
    if isinstance(value, dict):
        state.update({k: v for k, v in value.items() if k in state})
    if state["mode"] not in OBSERVE_MODES:
        state["mode"] = "degraded"
        state["last_error"] = state.get("last_error") or "invalid observe state"
    findings = state.get("findings_queued")
    state["findings_queued"] = findings if isinstance(findings, int) and findings >= 0 else 0
    return state


def get_observe_state(use_json: bool = True) -> dict:
    """Return normalized observer state without creating the file."""
    if not ensure_flux_exists():
        error_exit(".flux/ does not exist. Run 'fluxctl init' first.", use_json=use_json)

    path = observe_state_path()
    if not path.exists():
        return annotate_observe_state(default_observe_state())

    try:
        state = load_json(path)
    except Exception as exc:
        return annotate_observe_state(
            {
                **default_observe_state(),
                "mode": "degraded",
                "last_error": f"failed to read observe state: {exc}",
                "updated_at": now_iso(),
            }
        )
    return annotate_observe_state(normalize_observe_state(state))


def annotate_observe_state(state: dict) -> dict:
    """Add computed convenience fields for UX/reporting."""
    annotated = dict(state)
    annotated["running"] = annotated["mode"] != "off"
    annotated["attached"] = annotated["mode"] == "attached"
    return annotated


@contextmanager
def _observe_lock():
    """Lock the observer state file for exclusive updates."""
    locks_dir = get_state_dir() / "locks"
    locks_dir.mkdir(parents=True, exist_ok=True)
    lock_path = locks_dir / "observe.lock"
    with open(lock_path, "w", encoding="utf-8") as handle:
        try:
            _flock(handle, LOCK_EX)
            yield
        finally:
            _flock(handle, LOCK_UN)


def save_observe_state(state: dict) -> dict:
    """Persist observer state and return the normalized payload."""
    path = observe_state_path()
    normalized = normalize_observe_state(state)
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(path, normalized)
    return annotate_observe_state(normalized)


def set_observe_mode(mode: str) -> dict:
    """Transition observer state to the requested mode."""
    with _observe_lock():
        current = normalize_observe_state(get_observe_state(use_json=True))
        timestamp = now_iso()
        if mode == "idle":
            current["mode"] = "idle"
            current["started_at"] = current.get("started_at") or timestamp
            current["stopped_at"] = None
            current["last_error"] = None
        elif mode == "off":
            current["mode"] = "off"
            current["stopped_at"] = timestamp
        else:
            current["mode"] = mode
        current["updated_at"] = timestamp
        return save_observe_state(current)


def render_observe_text(state: dict, state_path: Path) -> str:
    """Human-readable observer status output."""
    lines = []
    if state["mode"] == "off":
        lines.append("Observe: OFF")
    else:
        lines.append(f"Observe: ON ({state['mode']})")
    lines.append(f"State file: {state_path}")
    if state.get("started_at"):
        lines.append(f"Started: {state['started_at']}")
    if state.get("updated_at"):
        lines.append(f"Updated: {state['updated_at']}")
    lines.append(f"Findings queued: {state['findings_queued']}")
    if state.get("target"):
        lines.append(f"Target: {state['target']}")
    if state.get("last_error"):
        lines.append(f"Last error: {state['last_error']}")
    return "\n".join(lines)


def cmd_observe_status(args: argparse.Namespace) -> None:
    """Show observer runtime status."""
    state = get_observe_state(use_json=args.json)
    path = observe_state_path()
    if args.json:
        json_output({"observe": state, "state_path": str(path)})
    else:
        print(render_observe_text(state, path))


def cmd_observe_on(args: argparse.Namespace) -> None:
    """Enable the observer sidecar runtime state."""
    if not ensure_flux_exists():
        error_exit(".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json)

    current = get_observe_state(use_json=args.json)
    if current["mode"] not in {"off", "degraded"}:
        message = f"Observe already on ({current['mode']})"
        state = current
    else:
        state = set_observe_mode("idle")
        message = "Observe enabled (idle)"

    if args.json:
        json_output({"message": message, "observe": state, "state_path": str(observe_state_path())})
    else:
        print(message)
        print(render_observe_text(state, observe_state_path()))


def cmd_observe_off(args: argparse.Namespace) -> None:
    """Disable the observer sidecar runtime state."""
    if not ensure_flux_exists():
        error_exit(".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json)

    current = get_observe_state(use_json=args.json)
    if current["mode"] == "off":
        message = "Observe already off"
        state = current
    else:
        state = set_observe_mode("off")
        message = "Observe disabled"

    if args.json:
        json_output({"message": message, "observe": state, "state_path": str(observe_state_path())})
    else:
        print(message)
        print(render_observe_text(state, observe_state_path()))
