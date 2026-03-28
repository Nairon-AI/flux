"""
fluxctl_pkg.architecture - Canonical architecture diagram helpers and commands.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from .state import load_meta, save_meta
from .utils import (
    atomic_write,
    ensure_flux_exists,
    error_exit,
    get_flux_dir,
    get_repo_root,
    json_output,
    now_iso,
    read_file_or_stdin,
)

ARCHITECTURE_STATUSES = ["missing", "seeded", "current", "needs_update"]
ARCHITECTURE_REL_PATH = Path("brain/codebase/architecture.md")
ARCHITECTURE_REPO_REL_PATH = Path(".flux") / ARCHITECTURE_REL_PATH
ARCHITECTURE_PLACEHOLDER_MARKER = "<!-- flux:architecture status=seeded -->"

ARCHITECTURE_TEMPLATE = f"""# System Architecture Diagram

{ARCHITECTURE_PLACEHOLDER_MARKER}

Central high-level architecture map for this product. Flux reads this note during scoping,
implementation, and review work whenever whole-system context matters.

## Status

- State: seeded
- Last updated: not yet captured
- Owner: Flux
- Refresh when: components, boundaries, data flow, auth, integrations, or deployment topology change

## Diagram

```mermaid
flowchart TD
  Users["Users / Operators"]
  Entry["Clients / Entry Points"]
  Core["Core Services / Jobs"]
  Data["Datastores / External Systems"]

  Users --> Entry
  Entry --> Core
  Core --> Data
```

## Components

- `Users / Operators`: who or what drives the system.
- `Clients / Entry Points`: apps, APIs, CLIs, webhooks, cron triggers, queues.
- `Core Services / Jobs`: the main application modules, workers, background jobs, and critical internal boundaries.
- `Datastores / External Systems`: databases, caches, object storage, third-party APIs, analytics, auth providers.

## Critical Flows

- Request / event ingress:
- State mutation path:
- Read path / query path:
- Async / background processing:
- Auth / trust boundaries:

## Notes

- Keep this diagram high-level. Do not turn it into a file inventory.
- Prefer one diagram plus concise bullets over prose-heavy architecture essays.
- Update this note in the same change whenever the product architecture materially changes.
"""


def architecture_doc_path() -> Path:
    """Return the canonical architecture doc path."""
    return get_flux_dir() / ARCHITECTURE_REL_PATH


def default_architecture_state() -> dict:
    """Default architecture metadata stored in meta.json."""
    return {
        "status": "missing",
        "updated_at": None,
        "summary": None,
        "source": None,
    }


def normalize_architecture_state(value: object) -> dict:
    """Normalize architecture metadata loaded from meta.json."""
    state = default_architecture_state()
    if isinstance(value, dict):
        for key in state:
            if key in value:
                state[key] = value[key]
    if state["status"] not in ARCHITECTURE_STATUSES:
        state["status"] = "missing"
    return state


def is_seeded_architecture(content: str) -> bool:
    """Return True when the architecture doc is still the seeded template."""
    return ARCHITECTURE_PLACEHOLDER_MARKER in content


def get_architecture_state(use_json: bool = True) -> dict:
    """Return the current architecture artifact state."""
    path = architecture_doc_path()
    meta = load_meta(use_json=use_json) if ensure_flux_exists() else {}
    state = normalize_architecture_state(meta.get("architecture"))
    exists = path.exists()

    content = ""
    if exists:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            content = ""

    if not exists:
        state["status"] = "missing"
    elif is_seeded_architecture(content):
        state["status"] = "seeded"
    elif state["status"] == "missing":
        state["status"] = "current"

    return {
        "path": str(ARCHITECTURE_REPO_REL_PATH),
        "exists": exists,
        "status": state["status"],
        "needs_refresh": state["status"] in {"missing", "seeded", "needs_update"},
        "updated_at": state.get("updated_at"),
        "summary": state.get("summary"),
        "source": state.get("source"),
    }


def set_architecture_state(
    status: str,
    *,
    summary: Optional[str] = None,
    source: Optional[str] = None,
    updated_at: Optional[str] = None,
    use_json: bool = True,
) -> dict:
    """Persist architecture metadata and return the normalized state."""
    if status not in ARCHITECTURE_STATUSES:
        status = "missing"
    meta = load_meta(use_json=use_json)
    state = normalize_architecture_state(meta.get("architecture"))
    state["status"] = status
    state["updated_at"] = updated_at or now_iso()
    if summary is not None:
        state["summary"] = summary.strip() or None
    if source is not None:
        state["source"] = source.strip() or None
    meta["architecture"] = state
    save_meta(meta)
    return state


def read_architecture_context() -> Optional[str]:
    """Read the architecture doc for prompt context when available."""
    path = architecture_doc_path()
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return None


def build_architecture_prompt_context() -> str:
    """Build a structured prompt section for review/scoping commands."""
    state = get_architecture_state()
    content = read_architecture_context()
    lines = [
        f"Path: {state['path']}",
        f"Exists: {'yes' if state['exists'] else 'no'}",
        f"Status: {state['status']}",
        f"Needs refresh: {'yes' if state['needs_refresh'] else 'no'}",
    ]
    if state.get("updated_at"):
        lines.append(f"Updated at: {state['updated_at']}")
    if state.get("summary"):
        lines.append(f"Summary: {state['summary']}")
    if state.get("source"):
        lines.append(f"Source: {state['source']}")
    if content:
        lines.extend(["", "Document:", content])
    else:
        lines.extend(
            [
                "",
                "Document:",
                "No architecture diagram has been written yet. If the work changes high-level",
                "system boundaries or flows, require the canonical architecture doc to be updated.",
            ]
        )
    return "\n".join(lines).strip()


def cmd_architecture_status(args: argparse.Namespace) -> None:
    """Show architecture artifact status."""
    state = get_architecture_state(use_json=args.json)
    if args.json:
        json_output({"architecture": state})
    else:
        print(
            f"{state['status']} - {state['path']}"
            + (" (refresh required)" if state["needs_refresh"] else "")
        )


def cmd_architecture_path(args: argparse.Namespace) -> None:
    """Print the canonical architecture doc path."""
    path = architecture_doc_path()
    if args.json:
        json_output({"path": str(path), "relative_path": str(ARCHITECTURE_REPO_REL_PATH)})
    else:
        print(path)


def cmd_architecture_write(args: argparse.Namespace) -> None:
    """Write the canonical architecture doc and update its metadata."""
    if not ensure_flux_exists():
        error_exit(".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json)

    content = read_file_or_stdin(args.file, "Architecture file", use_json=args.json)
    status = args.status or ("seeded" if is_seeded_architecture(content) else "current")
    if status not in ARCHITECTURE_STATUSES:
        error_exit(
            f"Invalid architecture status: {status}. Allowed: {', '.join(ARCHITECTURE_STATUSES)}",
            use_json=args.json,
        )

    path = architecture_doc_path()
    atomic_write(path, content)
    state = set_architecture_state(
        status,
        summary=args.summary,
        source=args.source,
        use_json=args.json,
    )
    result = {
        "path": str(path.relative_to(get_repo_root())),
        "architecture": {
            "status": state["status"],
            "updated_at": state["updated_at"],
            "summary": state.get("summary"),
            "source": state.get("source"),
        },
        "message": "Architecture diagram updated",
    }
    if args.json:
        json_output(result)
    else:
        print(result["message"])

