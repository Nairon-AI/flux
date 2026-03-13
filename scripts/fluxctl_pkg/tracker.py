"""
Tracker integration hooks.

When a tracker provider is configured (e.g. Linear), these hooks sync
Flux state changes to the external tracker. If no tracker is configured,
all hooks are no-ops.

Phase 1: Config and setup only (hooks are stubs).
Phase 2+: Epic/task sync implementation.
"""

from .config import get_config


def _is_enabled() -> bool:
    """Check if a tracker provider is configured and not 'none'."""
    provider = get_config("tracker.provider")
    return provider is not None and provider != "none"


def _get_provider() -> str | None:
    """Get configured tracker provider name."""
    if not _is_enabled():
        return None
    return get_config("tracker.provider")


# --- Hooks (called by cmd_ functions after local writes) ---


def on_epic_created(epic_data: dict) -> None:
    """Called after a new epic is created locally."""
    if not _is_enabled():
        return
    # Phase 2: Create Linear project


def on_task_created(task_data: dict) -> None:
    """Called after a new task is created locally."""
    if not _is_enabled():
        return
    # Phase 3: Create Linear issue


def on_status_changed(task_id: str, old_status: str, new_status: str) -> None:
    """Called after a task status changes (start, done, block)."""
    if not _is_enabled():
        return
    # Phase 3: Update Linear issue status


def on_blocked(task_id: str, reason: str) -> None:
    """Called after a task is blocked."""
    if not _is_enabled():
        return
    # Phase 3: Update Linear issue status + add comment
