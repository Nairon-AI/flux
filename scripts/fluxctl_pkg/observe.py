"""
fluxctl_pkg.observe - agent-browser-backed observer runtime-state helpers and commands.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from .utils import (
    LOCK_EX,
    LOCK_UN,
    OBSERVE_MODES,
    _flock,
    atomic_write_json,
    ensure_flux_exists,
    error_exit,
    get_repo_root,
    get_state_dir,
    json_output,
    load_json,
    now_iso,
)

OBSERVE_STATE_FILE = "observe_state.json"
OBSERVE_DIR = "observe"
OBSERVE_ARTIFACTS_DIR = "artifacts"
OBSERVE_LOG_FILE = "observe.log"
OBSERVE_FINDINGS_FILE = "findings.jsonl"
DEFAULT_POLL_INTERVAL_SECS = 3.0
DEFAULT_ATTACH_MODE = "auto_connect"
ATTACH_MODES = ["auto_connect", "session"]

_SHUTDOWN_REQUESTED = False


def _mark_shutdown_requested(_signum, _frame) -> None:
    global _SHUTDOWN_REQUESTED
    _SHUTDOWN_REQUESTED = True


def observe_state_path() -> Path:
    """Return the persisted observer runtime-state path."""
    return (get_state_dir() / OBSERVE_STATE_FILE).resolve()


def observe_runtime_dir() -> Path:
    """Return the observer runtime directory."""
    return (get_state_dir() / OBSERVE_DIR).resolve()


def observe_artifacts_dir() -> Path:
    """Return the observer artifacts directory."""
    return observe_runtime_dir() / OBSERVE_ARTIFACTS_DIR


def observe_log_path() -> Path:
    """Return the observer log path."""
    return observe_runtime_dir() / OBSERVE_LOG_FILE


def observe_findings_path() -> Path:
    """Return the observer findings JSONL path."""
    return observe_runtime_dir() / OBSERVE_FINDINGS_FILE


def _agent_browser_bin() -> str:
    """Resolve agent-browser executable, allowing test override."""
    return os.environ.get("FLUX_OBSERVE_AGENT_BROWSER", "agent-browser")


def _resolve_poll_interval(raw: Optional[object]) -> float:
    try:
        value = float(raw if raw is not None else DEFAULT_POLL_INTERVAL_SECS)
    except (TypeError, ValueError):
        value = DEFAULT_POLL_INTERVAL_SECS
    return max(0.25, value)


def _pid_is_running(pid: Optional[object]) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _pid_matches_observer(pid: Optional[object]) -> bool:
    if not _pid_is_running(pid):
        return False
    try:
        result = subprocess.run(
            ["ps", "-p", str(pid), "-o", "command="],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except Exception:
        return False
    command = (result.stdout or "").strip()
    return "fluxctl.py observe run-loop" in command or "fluxctl observe run-loop" in command


def _current_pid() -> int:
    return os.getpid()


def default_observe_state() -> dict:
    """Default observer state when no runtime file exists yet."""
    return {
        "mode": "off",
        "pid": None,
        "started_at": None,
        "stopped_at": None,
        "updated_at": None,
        "last_poll_at": None,
        "last_event_at": None,
        "attach_mode": DEFAULT_ATTACH_MODE,
        "target": None,
        "session_name": None,
        "last_error": None,
        "findings_queued": 0,
        "log_path": None,
        "artifacts_dir": None,
        "findings_path": None,
        "last_url": None,
        "last_screenshot_path": None,
        "poll_interval_secs": DEFAULT_POLL_INTERVAL_SECS,
    }


def normalize_observe_state(value: object) -> dict:
    """Normalize observer state loaded from disk."""
    state = default_observe_state()
    if isinstance(value, dict):
        state.update({k: v for k, v in value.items() if k in state})
    if state["mode"] not in OBSERVE_MODES:
        state["mode"] = "degraded"
        state["last_error"] = state.get("last_error") or "invalid observe state"
    if state.get("attach_mode") not in ATTACH_MODES:
        state["attach_mode"] = DEFAULT_ATTACH_MODE
    findings = state.get("findings_queued")
    state["findings_queued"] = findings if isinstance(findings, int) and findings >= 0 else 0
    state["poll_interval_secs"] = _resolve_poll_interval(state.get("poll_interval_secs"))
    return state


def annotate_observe_state(state: dict) -> dict:
    """Add computed convenience fields for UX/reporting."""
    annotated = dict(state)
    worker_running = _pid_matches_observer(annotated.get("pid"))
    annotated["enabled"] = annotated["mode"] != "off"
    annotated["worker_running"] = worker_running
    annotated["running"] = worker_running or (annotated["enabled"] and annotated.get("pid") is None)
    annotated["attached"] = annotated["mode"] == "attached"
    annotated["healthy"] = annotated["mode"] in {"idle", "attached", "paused"} and (
        annotated["running"] or annotated["mode"] == "idle"
    )
    return annotated


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


def update_observe_state(updates: dict) -> dict:
    """Merge updates into persisted observer state."""
    with _observe_lock():
        current = normalize_observe_state(get_observe_state(use_json=True))
        merged = {**current, **updates}
        return save_observe_state(merged)


def _build_agent_browser_prefix(state: dict) -> list[str]:
    cmd = [_agent_browser_bin()]
    attach_mode = state.get("attach_mode") or DEFAULT_ATTACH_MODE
    if attach_mode == "session":
        session_name = state.get("session_name")
        if session_name:
            cmd.extend(["--session", session_name])
    else:
        cmd.append("--auto-connect")
    return cmd


def _run_agent_browser_json(state: dict, args: list[str], timeout: float = 10.0) -> dict:
    cmd = _build_agent_browser_prefix(state) + args + ["--json"]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    payload = (result.stdout or result.stderr or "").strip()
    if not payload:
        return {"success": False, "error": "empty agent-browser output"}
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return {"success": False, "error": payload}


def _capture_screenshot(state: dict) -> Optional[str]:
    timestamp = int(time.time() * 1000)
    path = observe_artifacts_dir() / f"observe-{timestamp}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    cmd = _build_agent_browser_prefix(state) + ["screenshot", str(path)]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return str(path) if result.returncode == 0 and path.exists() else None


def _append_findings(records: list[dict]) -> None:
    if not records:
        return
    path = observe_findings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(record, sort_keys=True) + "\n" for record in records)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(payload)


def _initial_console_cursor(state: dict) -> int:
    payload = _run_agent_browser_json(state, ["console"])
    if not payload.get("success") or not isinstance(payload.get("data"), dict):
        return 0
    messages = payload["data"].get("messages") or []
    timestamps = [m.get("timestamp") for m in messages if isinstance(m.get("timestamp"), int)]
    return max(timestamps) if timestamps else 0


def _worker_state_updates(base: dict) -> dict:
    return {
        "updated_at": now_iso(),
        "log_path": str(observe_log_path()),
        "artifacts_dir": str(observe_artifacts_dir()),
        "findings_path": str(observe_findings_path()),
        "poll_interval_secs": _resolve_poll_interval(base.get("poll_interval_secs")),
        "attach_mode": base.get("attach_mode") or DEFAULT_ATTACH_MODE,
    }


def _collect_once(state: dict, last_console_ts: int) -> tuple[dict, int]:
    url_payload = _run_agent_browser_json(state, ["get", "url"])
    console_payload = _run_agent_browser_json(state, ["console"])
    errors_payload = _run_agent_browser_json(state, ["errors"])

    updates = {
        "last_poll_at": now_iso(),
        "last_error": None,
    }
    findings: list[dict] = []
    screenshot_path = None
    max_console_ts = last_console_ts

    url = None
    if url_payload.get("success") and isinstance(url_payload.get("data"), dict):
        url = url_payload["data"].get("url")
        updates["last_url"] = url
        updates["target"] = url
        updates["mode"] = "attached"
    else:
        updates["mode"] = "degraded"
        updates["last_error"] = url_payload.get("error") or "failed to read current browser URL"
        return updates, last_console_ts

    messages = []
    if console_payload.get("success") and isinstance(console_payload.get("data"), dict):
        messages = console_payload["data"].get("messages") or []

    page_errors = []
    if errors_payload.get("success") and isinstance(errors_payload.get("data"), dict):
        page_errors = errors_payload["data"].get("errors") or []

    new_error_messages = []
    for message in messages:
        timestamp = message.get("timestamp")
        if isinstance(timestamp, int):
            max_console_ts = max(max_console_ts, timestamp)
        if not isinstance(timestamp, int) or timestamp <= last_console_ts:
            continue
        if message.get("type") != "error":
            continue
        new_error_messages.append(message)

    if page_errors and not new_error_messages:
        for page_error in page_errors:
            text = page_error.get("message") or page_error.get("text")
            if text:
                new_error_messages.append(
                    {"text": text, "timestamp": int(time.time() * 1000), "type": "error"}
                )

    if new_error_messages:
        screenshot_path = _capture_screenshot(state)
        captured_at = now_iso()
        for message in new_error_messages:
            findings.append(
                {
                    "captured_at": captured_at,
                    "source": "console",
                    "type": message.get("type") or "error",
                    "text": message.get("text"),
                    "timestamp": message.get("timestamp"),
                    "url": url,
                    "screenshot_path": screenshot_path,
                }
            )
        updates["last_event_at"] = captured_at
        updates["findings_queued"] = state.get("findings_queued", 0) + len(findings)
        if screenshot_path:
            updates["last_screenshot_path"] = screenshot_path

    _append_findings(findings)
    return updates, max_console_ts


def _repo_fluxctl_path() -> Path:
    scripts_dir = Path(__file__).resolve().parents[1]
    return scripts_dir / "fluxctl.py"


def _start_observer_process(state: dict) -> subprocess.Popen:
    log_path = observe_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [str(Path(__file__).resolve().parents[1]), env.get("PYTHONPATH", "")]
    ).strip(os.pathsep)
    cmd = [
        sys.executable,
        str(_repo_fluxctl_path()),
        "observe",
        "run-loop",
        "--attach-mode",
        state["attach_mode"],
        "--poll-interval-secs",
        str(state["poll_interval_secs"]),
    ]
    if state.get("session_name"):
        cmd.extend(["--session-name", state["session_name"]])

    with open(log_path, "a", encoding="utf-8") as handle:
        return subprocess.Popen(
            cmd,
            cwd=str(get_repo_root()),
            env=env,
            stdout=handle,
            stderr=handle,
            start_new_session=True,
        )


def _stop_observer_process(pid: Optional[int]) -> None:
    if not _pid_matches_observer(pid):
        return
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        return
    for _ in range(20):
        if not _pid_is_running(pid):
            return
        time.sleep(0.1)
    try:
        os.kill(pid, signal.SIGKILL)
    except OSError:
        pass


def render_observe_text(state: dict, state_path: Path) -> str:
    """Human-readable observer status output."""
    lines = [f"Observe: {state['mode'].upper()}"]
    lines.append(f"State file: {state_path}")
    if state.get("pid"):
        lines.append(f"PID: {state['pid']}")
    lines.append(f"Worker running: {'yes' if state['worker_running'] else 'no'}")
    lines.append(f"Attach mode: {state['attach_mode']}")
    if state.get("session_name"):
        lines.append(f"Session: {state['session_name']}")
    if state.get("started_at"):
        lines.append(f"Started: {state['started_at']}")
    if state.get("updated_at"):
        lines.append(f"Updated: {state['updated_at']}")
    if state.get("last_poll_at"):
        lines.append(f"Last poll: {state['last_poll_at']}")
    lines.append(f"Findings queued: {state['findings_queued']}")
    if state.get("target"):
        lines.append(f"Target: {state['target']}")
    if state.get("last_screenshot_path"):
        lines.append(f"Last screenshot: {state['last_screenshot_path']}")
    if state.get("log_path"):
        lines.append(f"Log: {state['log_path']}")
    if state.get("findings_path"):
        lines.append(f"Findings: {state['findings_path']}")
    if state.get("last_error"):
        lines.append(f"Last error: {state['last_error']}")
    return "\n".join(lines)


def _ensure_agent_browser_available(use_json: bool) -> None:
    bin_name = _agent_browser_bin()
    resolved = shutil.which(bin_name) if not os.path.isabs(bin_name) else bin_name
    if not resolved or not Path(resolved).exists():
        error_exit(
            f"agent-browser not found ({bin_name}). Install it first or set FLUX_OBSERVE_AGENT_BROWSER.",
            use_json=use_json,
        )


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
    _ensure_agent_browser_available(use_json=args.json)

    with _observe_lock():
        current = normalize_observe_state(get_observe_state(use_json=True))
        if _pid_matches_observer(current.get("pid")):
            state = annotate_observe_state(current)
            message = f"Observe already on ({state['mode']})"
        else:
            timestamp = now_iso()
            desired = {
                **current,
                "mode": "idle",
                "pid": None,
                "started_at": current.get("started_at") or timestamp,
                "stopped_at": None,
                "updated_at": timestamp,
                "last_error": None,
                "attach_mode": args.attach_mode or current.get("attach_mode") or DEFAULT_ATTACH_MODE,
                "session_name": args.session_name if args.session_name is not None else current.get("session_name"),
                "poll_interval_secs": _resolve_poll_interval(
                    args.poll_interval_secs if args.poll_interval_secs is not None else current.get("poll_interval_secs")
                ),
                "log_path": str(observe_log_path()),
                "artifacts_dir": str(observe_artifacts_dir()),
                "findings_path": str(observe_findings_path()),
            }
            save_observe_state(desired)
            proc = _start_observer_process(desired)
            state = save_observe_state({**desired, "pid": proc.pid, "updated_at": now_iso()})
            message = "Observe enabled"

    if args.json:
        json_output({"message": message, "observe": state, "state_path": str(observe_state_path())})
    else:
        print(message)
        print(render_observe_text(state, observe_state_path()))


def cmd_observe_off(args: argparse.Namespace) -> None:
    """Disable the observer sidecar runtime state."""
    if not ensure_flux_exists():
        error_exit(".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json)

    with _observe_lock():
        current = normalize_observe_state(get_observe_state(use_json=True))
        pid = current.get("pid")
        if current["mode"] == "off" and not _pid_matches_observer(pid):
            state = annotate_observe_state(current)
            message = "Observe already off"
        else:
            _stop_observer_process(pid if isinstance(pid, int) else None)
            timestamp = now_iso()
            state = save_observe_state(
                {
                    **current,
                    "mode": "off",
                    "pid": None,
                    "stopped_at": timestamp,
                    "updated_at": timestamp,
                }
            )
            message = "Observe disabled"

    if args.json:
        json_output({"message": message, "observe": state, "state_path": str(observe_state_path())})
    else:
        print(message)
        print(render_observe_text(state, observe_state_path()))


def cmd_observe_run_loop(args: argparse.Namespace) -> None:
    """Internal observer worker loop. Not user-facing."""
    signal.signal(signal.SIGTERM, _mark_shutdown_requested)
    signal.signal(signal.SIGINT, _mark_shutdown_requested)

    with _observe_lock():
        state = normalize_observe_state(get_observe_state(use_json=True))
        updated = {
            **state,
            "pid": _current_pid(),
            "mode": "idle",
            "attach_mode": args.attach_mode or state.get("attach_mode") or DEFAULT_ATTACH_MODE,
            "session_name": args.session_name if args.session_name is not None else state.get("session_name"),
            "poll_interval_secs": _resolve_poll_interval(args.poll_interval_secs),
        }
        updated.update(_worker_state_updates(updated))
        state = save_observe_state(updated)

    last_console_ts = _initial_console_cursor(state)
    while not _SHUTDOWN_REQUESTED:
        try:
            current = normalize_observe_state(get_observe_state(use_json=True))
            updates, last_console_ts = _collect_once(current, last_console_ts)
            merged = {**current, **updates}
            merged.update(_worker_state_updates(merged))
            save_observe_state(merged)
        except Exception as exc:
            save_observe_state(
                {
                    **normalize_observe_state(get_observe_state(use_json=True)),
                    "mode": "degraded",
                    "last_error": str(exc),
                    "updated_at": now_iso(),
                }
            )
        time.sleep(_resolve_poll_interval(args.poll_interval_secs))

    with _observe_lock():
        current = normalize_observe_state(get_observe_state(use_json=True))
        if current.get("pid") == _current_pid():
            save_observe_state(
                {
                    **current,
                    "pid": None,
                    "updated_at": now_iso(),
                    "mode": "off" if current.get("mode") == "off" else current.get("mode"),
                }
            )
