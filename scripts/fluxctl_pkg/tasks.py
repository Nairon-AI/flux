"""
fluxctl_pkg.tasks - Task normalization, CRUD, spec patching, ready/next/start/done/block, dependency management.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Optional

from .utils import (
    EPICS_DIR,
    FLUX_DIR,
    RUNTIME_FIELDS,
    SPECS_DIR,
    TASK_SPEC_HEADINGS,
    TASKS_DIR,
    TASK_STATUS,
    atomic_write,
    atomic_write_json,
    ensure_flux_exists,
    epic_id_from_task,
    error_exit,
    get_actor,
    get_flux_dir,
    is_epic_id,
    is_task_id,
    json_output,
    load_json,
    load_json_or_exit,
    now_iso,
    parse_id,
    read_file_or_stdin,
    read_text_or_exit,
    require_keys,
    scan_max_task_id,
    task_priority,
    workflow_phases_for_mode,
)
from .state import (
    normalize_epic,
    load_task_definition,
    load_task_with_state,
    save_task_runtime,
    save_task_definition,
    reset_task_runtime,
    delete_task_runtime,
    get_state_store,
    load_meta,
    save_meta,
    get_active_objective,
    set_active_objective,
    tasks_for_epic,
    ready_state_for_epic,
    load_all_epics,
    workflow_progress,
    artifact_dir_for_epic,
)
from .config import load_flux_config, get_config


def normalize_task(task_data: dict) -> dict:
    """Apply defaults for optional task fields and migrate legacy keys."""
    if "priority" not in task_data:
        task_data["priority"] = None
    # Migrate legacy 'deps' key to 'depends_on'
    if "depends_on" not in task_data:
        task_data["depends_on"] = task_data.get("deps", [])
    # Backend spec defaults (for orchestration products like flux-swarm)
    if "impl" not in task_data:
        task_data["impl"] = None
    if "review" not in task_data:
        task_data["review"] = None
    if "sync" not in task_data:
        task_data["sync"] = None
    return task_data


def create_epic_spec(id_str: str, title: str) -> str:
    """Create epic spec markdown content."""
    return f"""# {id_str} {title}

## Overview
TBD

## Scope
TBD

## Approach
TBD

## Quick commands
<!-- Required: at least one smoke command for the repo -->
- `# e.g., npm test, bun test, make test`

## Acceptance
- [ ] TBD

## References
- TBD
"""


def create_task_spec(id_str: str, title: str, acceptance: Optional[str] = None) -> str:
    """Create task spec markdown content."""
    acceptance_content = acceptance if acceptance else "- [ ] TBD"
    return f"""# {id_str} {title}

## Description
TBD

## Acceptance
{acceptance_content}

## Done summary
TBD

## Evidence
- Commits:
- Tests:
- PRs:
"""


def patch_task_section(content: str, section: str, new_content: str) -> str:
    """Patch a specific section in task spec. Preserves other sections.

    Raises ValueError on invalid content (duplicate/missing headings).
    """
    # Check for duplicate headings first (defensive)
    pattern = rf"^{re.escape(section)}\s*$"
    matches = len(re.findall(pattern, content, flags=re.MULTILINE))
    if matches > 1:
        raise ValueError(
            f"Cannot patch: duplicate heading '{section}' found ({matches} times)"
        )

    # Strip leading section heading from new_content if present (defensive)
    # Handles case where agent includes "## Description" in temp file
    new_lines = new_content.lstrip().split("\n")
    if new_lines and new_lines[0].strip() == section:
        new_content = "\n".join(new_lines[1:]).lstrip()

    lines = content.split("\n")
    result = []
    in_target_section = False
    section_found = False

    for i, line in enumerate(lines):
        if line.startswith("## "):
            if line.strip() == section:
                in_target_section = True
                section_found = True
                result.append(line)
                # Add new content
                result.append(new_content.rstrip())
                continue
            else:
                in_target_section = False

        if not in_target_section:
            result.append(line)

    if not section_found:
        raise ValueError(f"Section '{section}' not found in task spec")

    return "\n".join(result)


def get_task_section(content: str, section: str) -> str:
    """Get content under a task section heading."""
    lines = content.split("\n")
    in_target = False
    collected = []
    for line in lines:
        if line.startswith("## "):
            if line.strip() == section:
                in_target = True
                continue
            if in_target:
                break
        if in_target:
            collected.append(line)
    return "\n".join(collected).strip()


def validate_task_spec_headings(content: str) -> list[str]:
    """Validate task spec has required headings exactly once. Returns errors."""
    errors = []
    for heading in TASK_SPEC_HEADINGS:
        # Use regex anchored to line start to avoid matching inside code blocks
        pattern = rf"^{re.escape(heading)}\s*$"
        count = len(re.findall(pattern, content, flags=re.MULTILINE))
        if count == 0:
            errors.append(f"Missing required heading: {heading}")
        elif count > 1:
            errors.append(f"Duplicate heading: {heading} (found {count} times)")
    return errors


def clear_task_evidence(task_id: str) -> None:
    """Clear ## Evidence section contents but keep the heading with empty template."""
    flux_dir = get_flux_dir()
    spec_path = flux_dir / TASKS_DIR / f"{task_id}.md"
    if not spec_path.exists():
        return
    content = spec_path.read_text(encoding="utf-8")

    # Replace contents under ## Evidence with empty template, keeping heading
    # Pattern: ## Evidence\n<content until next ## or end of file>
    # Handle both LF and CRLF line endings
    pattern = r"(## Evidence\s*\r?\n).*?(?=\r?\n## |\Z)"
    replacement = r"\g<1>- Commits:\n- Tests:\n- PRs:\n"
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    if new_content != content:
        atomic_write(spec_path, new_content)


def find_dependents(task_id: str, same_epic: bool = False) -> list[str]:
    """Find tasks that depend on task_id (recursive). Returns list of dependent task IDs."""
    flux_dir = get_flux_dir()
    tasks_dir = flux_dir / TASKS_DIR
    if not tasks_dir.exists():
        return []

    epic_id = epic_id_from_task(task_id) if same_epic else None
    dependents: set[str] = set()  # Use set to avoid duplicates
    to_check = [task_id]
    checked = set()

    while to_check:
        checking = to_check.pop(0)
        if checking in checked:
            continue
        checked.add(checking)

        for task_file in tasks_dir.glob("fn-*.json"):
            if not is_task_id(task_file.stem):
                continue  # Skip non-task files (e.g., fn-1.2-review.json)
            try:
                task_data = load_json(task_file)
                tid = task_data.get("id", task_file.stem)
                if tid in checked or tid in dependents:
                    continue
                # Skip if same_epic filter and different epic
                if same_epic and epic_id_from_task(tid) != epic_id:
                    continue
                # Support both legacy "deps" and current "depends_on"
                deps = task_data.get("depends_on", task_data.get("deps", []))
                if checking in deps:
                    dependents.add(tid)
                    to_check.append(tid)
            except Exception:
                pass

    return sorted(dependents)


def cmd_task_create(args: argparse.Namespace) -> None:
    """Create a new task under an epic."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    if not is_epic_id(args.epic):
        error_exit(
            f"Invalid epic ID: {args.epic}. Expected format: fn-N or fn-N-slug (e.g., fn-1, fn-1-add-auth)", use_json=args.json
        )

    flux_dir = get_flux_dir()
    epic_path = flux_dir / EPICS_DIR / f"{args.epic}.json"

    load_json_or_exit(epic_path, f"Epic {args.epic}", use_json=args.json)

    # MU-1: Scan-based allocation for merge safety
    # Scan existing tasks to determine next ID (don't rely on counter)
    max_task = scan_max_task_id(flux_dir, args.epic)
    task_num = max_task + 1
    task_id = f"{args.epic}.{task_num}"

    # Double-check no collision (shouldn't happen with scan-based allocation)
    task_json_path = flux_dir / TASKS_DIR / f"{task_id}.json"
    task_spec_path = flux_dir / TASKS_DIR / f"{task_id}.md"
    if task_json_path.exists() or task_spec_path.exists():
        error_exit(
            f"Refusing to overwrite existing task {task_id}. "
            f"This shouldn't happen - check for orphaned files.",
            use_json=args.json,
        )

    # Parse dependencies
    deps = []
    if args.deps:
        deps = [d.strip() for d in args.deps.split(",")]
        # Validate deps are valid task IDs within same epic
        for dep in deps:
            if not is_task_id(dep):
                error_exit(
                    f"Invalid dependency ID: {dep}. Expected format: fn-N.M or fn-N-slug.M (e.g., fn-1.2, fn-1-add-auth.2)",
                    use_json=args.json,
                )
            if epic_id_from_task(dep) != args.epic:
                error_exit(
                    f"Dependency {dep} must be within the same epic ({args.epic})",
                    use_json=args.json,
                )

    # Read acceptance from file if provided
    acceptance = None
    if args.acceptance_file:
        acceptance = read_text_or_exit(
            Path(args.acceptance_file), "Acceptance file", use_json=args.json
        )

    # Create task JSON (MU-2: includes soft-claim fields)
    task_data = {
        "id": task_id,
        "epic": args.epic,
        "title": args.title,
        "status": "todo",
        "priority": args.priority,
        "depends_on": deps,
        "assignee": None,
        "claimed_at": None,
        "claim_note": "",
        "spec_path": f"{FLUX_DIR}/{TASKS_DIR}/{task_id}.md",
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    atomic_write_json(flux_dir / TASKS_DIR / f"{task_id}.json", task_data)

    # Create task spec
    spec_content = create_task_spec(task_id, args.title, acceptance)
    atomic_write(flux_dir / TASKS_DIR / f"{task_id}.md", spec_content)

    # NOTE: We no longer update epic["next_task"] since scan-based allocation
    # is the source of truth. This reduces merge conflicts.

    if args.json:
        json_output(
            {
                "id": task_id,
                "epic": args.epic,
                "title": args.title,
                "depends_on": deps,
                "spec_path": task_data["spec_path"],
                "message": f"Task {task_id} created",
            }
        )
    else:
        print(f"Task {task_id} created: {args.title}")


def cmd_dep_add(args: argparse.Namespace) -> None:
    """Add a dependency to a task."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    if not is_task_id(args.task):
        error_exit(
            f"Invalid task ID: {args.task}. Expected format: fn-N.M or fn-N-slug.M (e.g., fn-1.2, fn-1-add-auth.2)", use_json=args.json
        )

    if not is_task_id(args.depends_on):
        error_exit(
            f"Invalid dependency ID: {args.depends_on}. Expected format: fn-N.M or fn-N-slug.M (e.g., fn-1.2, fn-1-add-auth.2)",
            use_json=args.json,
        )

    # Validate same epic
    task_epic = epic_id_from_task(args.task)
    dep_epic = epic_id_from_task(args.depends_on)
    if task_epic != dep_epic:
        error_exit(
            f"Dependencies must be within the same epic. Task {args.task} is in {task_epic}, dependency {args.depends_on} is in {dep_epic}",
            use_json=args.json,
        )

    flux_dir = get_flux_dir()
    task_path = flux_dir / TASKS_DIR / f"{args.task}.json"

    task_data = load_json_or_exit(task_path, f"Task {args.task}", use_json=args.json)

    # Migrate old 'deps' key to 'depends_on' if needed
    if "depends_on" not in task_data:
        task_data["depends_on"] = task_data.pop("deps", [])

    if args.depends_on not in task_data["depends_on"]:
        task_data["depends_on"].append(args.depends_on)
        task_data["updated_at"] = now_iso()
        atomic_write_json(task_path, task_data)

    if args.json:
        json_output(
            {
                "task": args.task,
                "depends_on": task_data["depends_on"],
                "message": f"Dependency {args.depends_on} added to {args.task}",
            }
        )
    else:
        print(f"Dependency {args.depends_on} added to {args.task}")


def cmd_task_set_deps(args: argparse.Namespace) -> None:
    """Set dependencies for a task (convenience wrapper for dep add)."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    if not is_task_id(args.task_id):
        error_exit(
            f"Invalid task ID: {args.task_id}. Expected format: fn-N.M or fn-N-slug.M (e.g., fn-1.2, fn-1-add-auth.2)",
            use_json=args.json,
        )

    if not args.deps:
        error_exit("--deps is required", use_json=args.json)

    # Parse comma-separated deps
    dep_ids = [d.strip() for d in args.deps.split(",") if d.strip()]
    if not dep_ids:
        error_exit("--deps cannot be empty", use_json=args.json)

    task_epic = epic_id_from_task(args.task_id)
    flux_dir = get_flux_dir()
    task_path = flux_dir / TASKS_DIR / f"{args.task_id}.json"

    task_data = load_json_or_exit(
        task_path, f"Task {args.task_id}", use_json=args.json
    )

    # Migrate old 'deps' key if needed
    if "depends_on" not in task_data:
        task_data["depends_on"] = task_data.pop("deps", [])

    added = []
    for dep_id in dep_ids:
        if not is_task_id(dep_id):
            error_exit(
                f"Invalid dependency ID: {dep_id}. Expected format: fn-N.M or fn-N-slug.M (e.g., fn-1.2, fn-1-add-auth.2)",
                use_json=args.json,
            )
        dep_epic = epic_id_from_task(dep_id)
        if dep_epic != task_epic:
            error_exit(
                f"Dependencies must be within same epic. Task {args.task_id} is in {task_epic}, dependency {dep_id} is in {dep_epic}",
                use_json=args.json,
            )
        if dep_id not in task_data["depends_on"]:
            task_data["depends_on"].append(dep_id)
            added.append(dep_id)

    if added:
        task_data["updated_at"] = now_iso()
        atomic_write_json(task_path, task_data)

    if args.json:
        json_output(
            {
                "success": True,
                "task": args.task_id,
                "depends_on": task_data["depends_on"],
                "added": added,
                "message": f"Dependencies set for {args.task_id}",
            }
        )
    else:
        if added:
            print(f"Added dependencies to {args.task_id}: {', '.join(added)}")
        else:
            print(f"No new dependencies added (already set)")


def cmd_tasks(args: argparse.Namespace) -> None:
    """List tasks."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    flux_dir = get_flux_dir()
    tasks_dir = flux_dir / TASKS_DIR

    tasks = []
    if tasks_dir.exists():
        pattern = f"{args.epic}.*.json" if args.epic else "fn-*.json"
        for task_file in sorted(tasks_dir.glob(pattern)):
            task_id = task_file.stem
            if not is_task_id(task_id):
                continue  # Skip non-task files (e.g., fn-1.2-review.json)
            # Load task with merged runtime state
            task_data = load_task_with_state(task_id, use_json=args.json)
            if "id" not in task_data:
                continue  # Skip artifact files (GH-21)
            # Filter by status if requested
            if args.status and task_data["status"] != args.status:
                continue
            tasks.append(
                {
                    "id": task_data["id"],
                    "epic": task_data["epic"],
                    "title": task_data["title"],
                    "status": task_data["status"],
                    "priority": task_data.get("priority"),
                    "depends_on": task_data.get("depends_on", task_data.get("deps", [])),
                }
            )

    # Sort tasks by epic number then task number
    def task_sort_key(t):
        epic_num, task_num = parse_id(t["id"])
        return (
            epic_num if epic_num is not None else 0,
            task_num if task_num is not None else 0,
        )

    tasks.sort(key=task_sort_key)

    if args.json:
        json_output({"success": True, "tasks": tasks, "count": len(tasks)})
    else:
        if not tasks:
            scope = f" for epic {args.epic}" if args.epic else ""
            status_filter = f" with status '{args.status}'" if args.status else ""
            print(f"No tasks found{scope}{status_filter}.")
        else:
            scope = f" for {args.epic}" if args.epic else ""
            print(f"Tasks{scope} ({len(tasks)}):\n")
            for t in tasks:
                deps = (
                    f" (deps: {', '.join(t['depends_on'])})" if t["depends_on"] else ""
                )
                print(f"  [{t['status']}] {t['id']}: {t['title']}{deps}")


def cmd_task_set_backend(args: argparse.Namespace) -> None:
    """Set task backend specs for impl/review/sync."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    task_id = args.id
    if not is_task_id(task_id):
        error_exit(
            f"Invalid task ID: {task_id}. Expected format: fn-N.M or fn-N-slug.M (e.g., fn-1.2, fn-1-add-auth.2)",
            use_json=args.json,
        )

    # At least one of impl/review/sync must be provided
    if args.impl is None and args.review is None and args.sync is None:
        error_exit(
            "At least one of --impl, --review, or --sync must be provided",
            use_json=args.json,
        )

    flux_dir = get_flux_dir()
    task_path = flux_dir / TASKS_DIR / f"{task_id}.json"

    if not task_path.exists():
        error_exit(f"Task {task_id} not found", use_json=args.json)

    task_data = load_json_or_exit(task_path, f"Task {task_id}", use_json=args.json)

    # Update fields (empty string means clear)
    updated = []
    if args.impl is not None:
        task_data["impl"] = args.impl if args.impl else None
        updated.append(f"impl={args.impl or 'null'}")
    if args.review is not None:
        task_data["review"] = args.review if args.review else None
        updated.append(f"review={args.review or 'null'}")
    if args.sync is not None:
        task_data["sync"] = args.sync if args.sync else None
        updated.append(f"sync={args.sync or 'null'}")

    atomic_write_json(task_path, task_data)

    if args.json:
        json_output(
            {
                "id": task_id,
                "impl": task_data.get("impl"),
                "review": task_data.get("review"),
                "sync": task_data.get("sync"),
                "message": f"Task {task_id} backend specs updated: {', '.join(updated)}",
            }
        )
    else:
        print(f"Task {task_id} backend specs updated: {', '.join(updated)}")


def cmd_task_show_backend(args: argparse.Namespace) -> None:
    """Show effective backend specs for a task (task + epic levels only)."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    task_id = args.id
    if not is_task_id(task_id):
        error_exit(
            f"Invalid task ID: {task_id}. Expected format: fn-N.M or fn-N-slug.M (e.g., fn-1.2, fn-1-add-auth.2)",
            use_json=args.json,
        )

    flux_dir = get_flux_dir()
    task_path = flux_dir / TASKS_DIR / f"{task_id}.json"

    if not task_path.exists():
        error_exit(f"Task {task_id} not found", use_json=args.json)

    task_data = normalize_task(
        load_json_or_exit(task_path, f"Task {task_id}", use_json=args.json)
    )

    # Get epic data for defaults
    epic_id = task_data.get("epic")
    epic_data = None
    if epic_id:
        epic_path = flux_dir / EPICS_DIR / f"{epic_id}.json"
        if epic_path.exists():
            epic_data = normalize_epic(
                load_json_or_exit(epic_path, f"Epic {epic_id}", use_json=args.json)
            )

    # Compute effective values with source tracking
    def resolve_spec(task_key: str, epic_key: str) -> tuple:
        """Return (spec, source) tuple."""
        task_val = task_data.get(task_key)
        if task_val:
            return (task_val, "task")
        if epic_data:
            epic_val = epic_data.get(epic_key)
            if epic_val:
                return (epic_val, "epic")
        return (None, None)

    impl_spec, impl_source = resolve_spec("impl", "default_impl")
    review_spec, review_source = resolve_spec("review", "default_review")
    sync_spec, sync_source = resolve_spec("sync", "default_sync")

    if args.json:
        json_output(
            {
                "id": task_id,
                "epic": epic_id,
                "impl": {"spec": impl_spec, "source": impl_source},
                "review": {"spec": review_spec, "source": review_source},
                "sync": {"spec": sync_spec, "source": sync_source},
            }
        )
    else:
        def fmt(spec, source):
            if spec:
                return f"{spec} ({source})"
            return "null"

        print(f"impl: {fmt(impl_spec, impl_source)}")
        print(f"review: {fmt(review_spec, review_source)}")
        print(f"sync: {fmt(sync_spec, sync_source)}")


def cmd_task_set_description(args: argparse.Namespace) -> None:
    """Set task description section."""
    _task_set_section(args.id, "## Description", args.file, args.json)


def cmd_task_set_acceptance(args: argparse.Namespace) -> None:
    """Set task acceptance section."""
    _task_set_section(args.id, "## Acceptance", args.file, args.json)


def cmd_task_set_spec(args: argparse.Namespace) -> None:
    """Set task spec - full replacement (--file) or section patches.

    Full replacement mode: --file replaces entire spec content (like epic set-plan).
    Section patch mode: --description and/or --acceptance update specific sections.
    """
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    task_id = args.id
    if not is_task_id(task_id):
        error_exit(
            f"Invalid task ID: {task_id}. Expected format: fn-N.M or fn-N-slug.M (e.g., fn-1.2, fn-1-add-auth.2)",
            use_json=args.json,
        )

    # Need at least one of file, description, or acceptance
    has_file = hasattr(args, "file") and args.file
    if not has_file and not args.description and not args.acceptance:
        error_exit(
            "Requires --file, --description, or --acceptance",
            use_json=args.json,
        )

    flux_dir = get_flux_dir()
    task_json_path = flux_dir / TASKS_DIR / f"{task_id}.json"
    task_spec_path = flux_dir / TASKS_DIR / f"{task_id}.md"

    # Verify task exists
    if not task_json_path.exists():
        error_exit(f"Task {task_id} not found", use_json=args.json)

    # Load task JSON first (fail early)
    task_data = load_json_or_exit(task_json_path, f"Task {task_id}", use_json=args.json)

    # Full file replacement mode (like epic set-plan)
    if has_file:
        content = read_file_or_stdin(args.file, "Spec file", use_json=args.json)
        atomic_write(task_spec_path, content)
        task_data["updated_at"] = now_iso()
        atomic_write_json(task_json_path, task_data)

        if args.json:
            json_output({"id": task_id, "message": f"Task {task_id} spec replaced"})
        else:
            print(f"Task {task_id} spec replaced")
        return

    # Section patch mode (existing behavior)
    # Read current spec
    current_spec = read_text_or_exit(
        task_spec_path, f"Task {task_id} spec", use_json=args.json
    )

    updated_spec = current_spec
    sections_updated = []

    # Apply description if provided
    if args.description:
        desc_content = read_file_or_stdin(args.description, "Description file", use_json=args.json)
        try:
            updated_spec = patch_task_section(updated_spec, "## Description", desc_content)
            sections_updated.append("## Description")
        except ValueError as e:
            error_exit(str(e), use_json=args.json)

    # Apply acceptance if provided
    if args.acceptance:
        acc_content = read_file_or_stdin(args.acceptance, "Acceptance file", use_json=args.json)
        try:
            updated_spec = patch_task_section(updated_spec, "## Acceptance", acc_content)
            sections_updated.append("## Acceptance")
        except ValueError as e:
            error_exit(str(e), use_json=args.json)

    # Single atomic write for spec, single for JSON
    atomic_write(task_spec_path, updated_spec)
    task_data["updated_at"] = now_iso()
    atomic_write_json(task_json_path, task_data)

    if args.json:
        json_output(
            {
                "id": task_id,
                "sections": sections_updated,
                "message": f"Task {task_id} updated: {', '.join(sections_updated)}",
            }
        )
    else:
        print(f"Task {task_id} updated: {', '.join(sections_updated)}")


def cmd_task_reset(args: argparse.Namespace) -> None:
    """Reset task status to todo."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    task_id = args.task_id
    if not is_task_id(task_id):
        error_exit(
            f"Invalid task ID: {task_id}. Expected format: fn-N.M or fn-N-slug.M (e.g., fn-1.2, fn-1-add-auth.2)",
            use_json=args.json,
        )

    flux_dir = get_flux_dir()
    task_json_path = flux_dir / TASKS_DIR / f"{task_id}.json"

    if not task_json_path.exists():
        error_exit(f"Task {task_id} not found", use_json=args.json)

    # Load task with merged runtime state
    task_data = load_task_with_state(task_id, use_json=args.json)

    # Load epic to check if closed
    epic_id = epic_id_from_task(task_id)
    epic_path = flux_dir / EPICS_DIR / f"{epic_id}.json"
    if epic_path.exists():
        epic_data = load_json_or_exit(epic_path, f"Epic {epic_id}", use_json=args.json)
        if epic_data.get("status") == "done":
            error_exit(
                f"Cannot reset task in closed epic {epic_id}", use_json=args.json
            )

    # Check status validations (use merged state)
    current_status = task_data.get("status", "todo")
    if current_status == "in_progress":
        error_exit(
            f"Cannot reset in_progress task {task_id}. Complete or block it first.",
            use_json=args.json,
        )
    if current_status == "todo":
        # Already todo - no-op success
        if args.json:
            json_output(
                {"success": True, "reset": [], "message": f"{task_id} already todo"}
            )
        else:
            print(f"{task_id} already todo")
        return

    # Reset runtime state to baseline (overwrite, not merge - clears all runtime fields)
    reset_task_runtime(task_id)

    # Also clear legacy runtime fields from definition file (for backward compat cleanup)
    def_data = load_json_or_exit(task_json_path, f"Task {task_id}", use_json=args.json)
    def_data.pop("blocked_reason", None)
    def_data.pop("completed_at", None)
    def_data.pop("assignee", None)
    def_data.pop("claimed_at", None)
    def_data.pop("claim_note", None)
    def_data.pop("evidence", None)
    def_data["status"] = "todo"  # Keep in sync for backward compat
    def_data["updated_at"] = now_iso()
    atomic_write_json(task_json_path, def_data)

    # Clear evidence section from spec markdown
    clear_task_evidence(task_id)

    reset_ids = [task_id]

    # Handle cascade
    if args.cascade:
        dependents = find_dependents(task_id, same_epic=True)
        for dep_id in dependents:
            dep_path = flux_dir / TASKS_DIR / f"{dep_id}.json"
            if not dep_path.exists():
                continue

            # Load merged state for dependent
            dep_data = load_task_with_state(dep_id, use_json=args.json)
            dep_status = dep_data.get("status", "todo")

            # Skip in_progress and already todo
            if dep_status == "in_progress" or dep_status == "todo":
                continue

            # Reset runtime state for dependent (overwrite, not merge)
            reset_task_runtime(dep_id)

            # Also clear legacy fields from definition
            dep_def = load_json(dep_path)
            dep_def.pop("blocked_reason", None)
            dep_def.pop("completed_at", None)
            dep_def.pop("assignee", None)
            dep_def.pop("claimed_at", None)
            dep_def.pop("claim_note", None)
            dep_def.pop("evidence", None)
            dep_def["status"] = "todo"
            dep_def["updated_at"] = now_iso()
            atomic_write_json(dep_path, dep_def)

            clear_task_evidence(dep_id)
            reset_ids.append(dep_id)

    if args.json:
        json_output({"success": True, "reset": reset_ids})
    else:
        print(f"Reset: {', '.join(reset_ids)}")


def _task_set_section(
    task_id: str, section: str, file_path: str, use_json: bool
) -> None:
    """Helper to set a task spec section."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=use_json
        )

    if not is_task_id(task_id):
        error_exit(
            f"Invalid task ID: {task_id}. Expected format: fn-N.M or fn-N-slug.M (e.g., fn-1.2, fn-1-add-auth.2)", use_json=use_json
        )

    flux_dir = get_flux_dir()
    task_json_path = flux_dir / TASKS_DIR / f"{task_id}.json"
    task_spec_path = flux_dir / TASKS_DIR / f"{task_id}.md"

    # Verify task exists
    if not task_json_path.exists():
        error_exit(f"Task {task_id} not found", use_json=use_json)

    # Read new content from file or stdin
    new_content = read_file_or_stdin(file_path, "Input file", use_json=use_json)

    # Load task JSON first (fail early before any writes)
    task_data = load_json_or_exit(task_json_path, f"Task {task_id}", use_json=use_json)

    # Read current spec
    current_spec = read_text_or_exit(
        task_spec_path, f"Task {task_id} spec", use_json=use_json
    )

    # Patch section
    try:
        updated_spec = patch_task_section(current_spec, section, new_content)
    except ValueError as e:
        error_exit(str(e), use_json=use_json)

    # Write spec then JSON (both validated above)
    atomic_write(task_spec_path, updated_spec)
    task_data["updated_at"] = now_iso()
    atomic_write_json(task_json_path, task_data)

    if use_json:
        json_output(
            {
                "id": task_id,
                "section": section,
                "message": f"Task {task_id} {section} updated",
            }
        )
    else:
        print(f"Task {task_id} {section} updated")


def cmd_ready(args: argparse.Namespace) -> None:
    """List ready tasks for an epic."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    if not is_epic_id(args.epic):
        error_exit(
            f"Invalid epic ID: {args.epic}. Expected format: fn-N or fn-N-slug (e.g., fn-1, fn-1-add-auth)", use_json=args.json
        )

    flux_dir = get_flux_dir()
    epic_path = flux_dir / EPICS_DIR / f"{args.epic}.json"

    if not epic_path.exists():
        error_exit(f"Epic {args.epic} not found", use_json=args.json)

    # MU-2: Get current actor for display (marks your tasks)
    current_actor = get_actor()

    # Get all tasks for epic (with merged runtime state)
    tasks_dir = flux_dir / TASKS_DIR
    if not tasks_dir.exists():
        error_exit(
            f"{TASKS_DIR}/ missing. Run 'fluxctl init' or fix repo state.",
            use_json=args.json,
        )
    tasks = {}
    for task_file in tasks_dir.glob(f"{args.epic}.*.json"):
        task_id = task_file.stem
        if not is_task_id(task_id):
            continue  # Skip non-task files (e.g., fn-1.2-review.json)
        task_data = load_task_with_state(task_id, use_json=args.json)
        if "id" not in task_data:
            continue  # Skip artifact files (GH-21)
        tasks[task_data["id"]] = task_data

    # Find ready tasks (status=todo, all deps done)
    ready = []
    in_progress = []
    blocked = []

    for task_id, task in tasks.items():
        # MU-2: Track in_progress tasks separately
        if task["status"] == "in_progress":
            in_progress.append(task)
            continue

        if task["status"] == "done":
            continue

        if task["status"] == "blocked":
            blocked.append({"task": task, "blocked_by": ["status=blocked"]})
            continue

        # Check all deps are done
        deps_done = True
        blocking_deps = []
        for dep in task["depends_on"]:
            if dep not in tasks:
                deps_done = False
                blocking_deps.append(dep)
            elif tasks[dep]["status"] != "done":
                deps_done = False
                blocking_deps.append(dep)

        if deps_done:
            ready.append(task)
        else:
            blocked.append({"task": task, "blocked_by": blocking_deps})

    # Sort by numeric suffix
    def sort_key(t):
        _, task_num = parse_id(t["id"])
        return (
            task_priority(t),
            task_num if task_num is not None else 0,
            t.get("title", ""),
        )

    ready.sort(key=sort_key)
    in_progress.sort(key=sort_key)
    blocked.sort(key=lambda x: sort_key(x["task"]))

    if args.json:
        json_output(
            {
                "epic": args.epic,
                "actor": current_actor,
                "ready": [
                    {"id": t["id"], "title": t["title"], "depends_on": t["depends_on"]}
                    for t in ready
                ],
                "in_progress": [
                    {"id": t["id"], "title": t["title"], "assignee": t.get("assignee")}
                    for t in in_progress
                ],
                "blocked": [
                    {
                        "id": b["task"]["id"],
                        "title": b["task"]["title"],
                        "blocked_by": b["blocked_by"],
                    }
                    for b in blocked
                ],
            }
        )
    else:
        print(f"Ready tasks for {args.epic} (actor: {current_actor}):")
        if ready:
            for t in ready:
                print(f"  {t['id']}: {t['title']}")
        else:
            print("  (none)")
        if in_progress:
            print("\nIn progress:")
            for t in in_progress:
                assignee = t.get("assignee") or "unknown"
                marker = " (you)" if assignee == current_actor else ""
                print(f"  {t['id']}: {t['title']} [{assignee}]{marker}")
        if blocked:
            print("\nBlocked:")
            for b in blocked:
                print(
                    f"  {b['task']['id']}: {b['task']['title']} (by: {', '.join(b['blocked_by'])})"
                )


def cmd_next(args: argparse.Namespace) -> None:
    """Select the next plan/work unit."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    flux_dir = get_flux_dir()

    # Resolve epics list
    epic_ids: list[str] = []
    if args.epics_file:
        data = load_json_or_exit(
            Path(args.epics_file), "Epics file", use_json=args.json
        )
        epics_val = data.get("epics")
        if not isinstance(epics_val, list):
            error_exit(
                "Epics file must be JSON with key 'epics' as a list", use_json=args.json
            )
        for e in epics_val:
            if not isinstance(e, str) or not is_epic_id(e):
                error_exit(f"Invalid epic ID in epics file: {e}", use_json=args.json)
            epic_ids.append(e)
    else:
        epics_dir = flux_dir / EPICS_DIR
        if epics_dir.exists():
            for epic_file in sorted(epics_dir.glob("fn-*.json")):
                # Match: fn-N.json, fn-N-xxx.json (short), fn-N-slug.json (long)
                match = re.match(
                    r"^fn-(\d+)(?:-[a-z0-9][a-z0-9-]*[a-z0-9]|-[a-z0-9]{1,3})?\.json$",
                    epic_file.name,
                )
                if match:
                    epic_ids.append(epic_file.stem)  # Use full ID from filename
        epic_ids.sort(key=lambda e: parse_id(e)[0] or 0)

    current_actor = get_actor()

    def sort_key(t: dict) -> tuple[int, int]:
        _, task_num = parse_id(t["id"])
        return (task_priority(t), task_num if task_num is not None else 0)

    blocked_epics: dict[str, list[str]] = {}

    for epic_id in epic_ids:
        epic_path = flux_dir / EPICS_DIR / f"{epic_id}.json"
        if not epic_path.exists():
            if args.epics_file:
                error_exit(f"Epic {epic_id} not found", use_json=args.json)
            continue

        epic_data = normalize_epic(
            load_json_or_exit(epic_path, f"Epic {epic_id}", use_json=args.json)
        )
        if epic_data.get("status") == "done":
            continue

        # Skip epics blocked by epic-level dependencies
        blocked_by: list[str] = []
        for dep in epic_data.get("depends_on_epics", []) or []:
            if dep == epic_id:
                continue
            dep_path = flux_dir / EPICS_DIR / f"{dep}.json"
            if not dep_path.exists():
                blocked_by.append(dep)
                continue
            dep_data = normalize_epic(
                load_json_or_exit(dep_path, f"Epic {dep}", use_json=args.json)
            )
            if dep_data.get("status") != "done":
                blocked_by.append(dep)
        if blocked_by:
            blocked_epics[epic_id] = blocked_by
            continue

        if args.require_plan_review and epic_data.get("plan_review_status") != "ship":
            if args.json:
                json_output(
                    {
                        "status": "plan",
                        "epic": epic_id,
                        "task": None,
                        "reason": "needs_plan_review",
                    }
                )
            else:
                print(f"plan {epic_id} needs_plan_review")
            return

        tasks_dir = flux_dir / TASKS_DIR
        if not tasks_dir.exists():
            error_exit(
                f"{TASKS_DIR}/ missing. Run 'fluxctl init' or fix repo state.",
                use_json=args.json,
            )

        tasks: dict[str, dict] = {}
        for task_file in tasks_dir.glob(f"{epic_id}.*.json"):
            task_id = task_file.stem
            if not is_task_id(task_id):
                continue  # Skip non-task files (e.g., fn-1.2-review.json)
            # Load task with merged runtime state
            task_data = load_task_with_state(task_id, use_json=args.json)
            if "id" not in task_data:
                continue  # Skip artifact files (GH-21)
            tasks[task_data["id"]] = task_data

        # Resume in_progress tasks owned by current actor
        in_progress = [
            t
            for t in tasks.values()
            if t.get("status") == "in_progress" and t.get("assignee") == current_actor
        ]
        in_progress.sort(key=sort_key)
        if in_progress:
            task_id = in_progress[0]["id"]
            if args.json:
                json_output(
                    {
                        "status": "work",
                        "epic": epic_id,
                        "task": task_id,
                        "reason": "resume_in_progress",
                    }
                )
            else:
                print(f"work {task_id} resume_in_progress")
            return

        # Ready tasks by deps + priority
        ready: list[dict] = []
        for task in tasks.values():
            if task.get("status") != "todo":
                continue
            if task.get("status") == "blocked":
                continue
            deps_done = True
            for dep in task.get("depends_on", []):
                dep_task = tasks.get(dep)
                if not dep_task or dep_task.get("status") != "done":
                    deps_done = False
                    break
            if deps_done:
                ready.append(task)

        ready.sort(key=sort_key)
        if ready:
            task_id = ready[0]["id"]
            if args.json:
                json_output(
                    {
                        "status": "work",
                        "epic": epic_id,
                        "task": task_id,
                        "reason": "ready_task",
                    }
                )
            else:
                print(f"work {task_id} ready_task")
            return

        # Check if all tasks are done and completion review is needed
        if (
            args.require_completion_review
            and tasks
            and all(t.get("status") == "done" for t in tasks.values())
            and epic_data.get("completion_review_status") != "ship"
        ):
            if args.json:
                json_output(
                    {
                        "status": "completion_review",
                        "epic": epic_id,
                        "task": None,
                        "reason": "needs_completion_review",
                    }
                )
            else:
                print(f"completion_review {epic_id} needs_completion_review")
            return

    if args.json:
        payload = {"status": "none", "epic": None, "task": None, "reason": "none"}
        if blocked_epics:
            payload["reason"] = "blocked_by_epic_deps"
            payload["blocked_epics"] = blocked_epics
        json_output(payload)
    else:
        if blocked_epics:
            print("none blocked_by_epic_deps")
            for epic_id, deps in blocked_epics.items():
                print(f"  {epic_id}: {', '.join(deps)}")
        else:
            print("none")


def cmd_start(args: argparse.Namespace) -> None:
    """Start a task (set status to in_progress)."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    if not is_task_id(args.id):
        error_exit(
            f"Invalid task ID: {args.id}. Expected format: fn-N.M or fn-N-slug.M (e.g., fn-1.2, fn-1-add-auth.2)", use_json=args.json
        )

    # Load task definition for dependency info (outside lock)
    # Normalize to handle legacy "deps" field
    task_def = normalize_task(load_task_definition(args.id, use_json=args.json))
    depends_on = task_def.get("depends_on", []) or []

    # Validate all dependencies are done (outside lock - this is read-only check)
    if not args.force:
        for dep in depends_on:
            dep_data = load_task_with_state(dep, use_json=args.json)
            if dep_data["status"] != "done":
                error_exit(
                    f"Cannot start task {args.id}: dependency {dep} is '{dep_data['status']}', not 'done'. "
                    f"Complete dependencies first or use --force to override.",
                    use_json=args.json,
                )

    current_actor = get_actor()
    store = get_state_store()

    # Atomic claim: validation + write inside lock to prevent race conditions
    with store.lock_task(args.id):
        # Re-load runtime state inside lock for accurate check
        runtime = store.load_runtime(args.id)
        if runtime is None:
            # Backward compat: extract from definition
            runtime = {k: task_def[k] for k in RUNTIME_FIELDS if k in task_def}
            if not runtime:
                runtime = {"status": "todo"}

        status = runtime.get("status", "todo")
        existing_assignee = runtime.get("assignee")

        # Cannot start done task
        if status == "done":
            error_exit(
                f"Cannot start task {args.id}: status is 'done'.", use_json=args.json
            )

        # Blocked requires --force
        if status == "blocked" and not args.force:
            error_exit(
                f"Cannot start task {args.id}: status is 'blocked'. Use --force to override.",
                use_json=args.json,
            )

        # Check if claimed by someone else (unless --force)
        if not args.force and existing_assignee and existing_assignee != current_actor:
            error_exit(
                f"Cannot start task {args.id}: claimed by '{existing_assignee}'. "
                f"Use --force to override.",
                use_json=args.json,
            )

        # Validate task is in todo status (unless --force or resuming own task)
        if not args.force and status != "todo":
            # Allow resuming your own in_progress task
            if not (status == "in_progress" and existing_assignee == current_actor):
                error_exit(
                    f"Cannot start task {args.id}: status is '{status}', expected 'todo'. "
                    f"Use --force to override.",
                    use_json=args.json,
                )

        # Build runtime state updates
        runtime_updates = {**runtime, "status": "in_progress", "updated_at": now_iso()}
        if not existing_assignee:
            runtime_updates["assignee"] = current_actor
            runtime_updates["claimed_at"] = now_iso()
        if args.note:
            runtime_updates["claim_note"] = args.note
        elif args.force and existing_assignee and existing_assignee != current_actor:
            # Force override: note the takeover
            runtime_updates["assignee"] = current_actor
            runtime_updates["claimed_at"] = now_iso()
            if not args.note:
                runtime_updates["claim_note"] = f"Taken over from {existing_assignee}"

        # Write inside lock
        store.save_runtime(args.id, runtime_updates)

    # NOTE: We no longer update epic timestamp on task start/done.
    # Epic timestamp only changes on epic-level operations (set-plan, close).
    # This reduces merge conflicts in multi-user scenarios.
    set_active_objective(epic_id_from_task(args.id), use_json=args.json)

    if args.json:
        json_output(
            {
                "id": args.id,
                "status": "in_progress",
                "message": f"Task {args.id} started",
            }
        )
    else:
        print(f"Task {args.id} started")


def cmd_done(args: argparse.Namespace) -> None:
    """Complete a task with summary and evidence."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    if not is_task_id(args.id):
        error_exit(
            f"Invalid task ID: {args.id}. Expected format: fn-N.M or fn-N-slug.M (e.g., fn-1.2, fn-1-add-auth.2)", use_json=args.json
        )

    flux_dir = get_flux_dir()
    task_spec_path = flux_dir / TASKS_DIR / f"{args.id}.md"

    # Load task with merged runtime state (fail early before any writes)
    task_data = load_task_with_state(args.id, use_json=args.json)

    # MU-2: Require in_progress status (unless --force)
    if not args.force and task_data["status"] != "in_progress":
        status = task_data["status"]
        if status == "done":
            error_exit(
                f"Task {args.id} is already done.",
                use_json=args.json,
            )
        else:
            error_exit(
                f"Task {args.id} is '{status}', not 'in_progress'. Use --force to override.",
                use_json=args.json,
            )

    # MU-2: Prevent cross-actor completion (unless --force)
    current_actor = get_actor()
    existing_assignee = task_data.get("assignee")
    if not args.force and existing_assignee and existing_assignee != current_actor:
        error_exit(
            f"Cannot complete task {args.id}: claimed by '{existing_assignee}'. "
            f"Use --force to override.",
            use_json=args.json,
        )

    # Get summary: file > inline > default
    summary: str
    if args.summary_file:
        summary = read_text_or_exit(
            Path(args.summary_file), "Summary file", use_json=args.json
        )
    elif args.summary:
        summary = args.summary
    else:
        summary = "- Task completed"

    # Get evidence: file > inline > default
    evidence: dict
    if args.evidence_json:
        evidence_raw = read_text_or_exit(
            Path(args.evidence_json), "Evidence file", use_json=args.json
        )
        try:
            evidence = json.loads(evidence_raw)
        except json.JSONDecodeError as e:
            error_exit(f"Evidence file invalid JSON: {e}", use_json=args.json)
    elif args.evidence:
        try:
            evidence = json.loads(args.evidence)
        except json.JSONDecodeError as e:
            error_exit(f"Evidence invalid JSON: {e}", use_json=args.json)
    else:
        evidence = {"commits": [], "tests": [], "prs": []}

    if not isinstance(evidence, dict):
        error_exit(
            "Evidence JSON must be an object with keys: commits/tests/prs",
            use_json=args.json,
        )

    # Format evidence as markdown (coerce to strings, handle string-vs-array)
    def to_list(val: Any) -> list:
        if val is None:
            return []
        if isinstance(val, str):
            return [val] if val else []
        return list(val)

    evidence_md = []
    commits = [str(x) for x in to_list(evidence.get("commits"))]
    tests = [str(x) for x in to_list(evidence.get("tests"))]
    prs = [str(x) for x in to_list(evidence.get("prs"))]
    evidence_md.append(f"- Commits: {', '.join(commits)}" if commits else "- Commits:")
    evidence_md.append(f"- Tests: {', '.join(tests)}" if tests else "- Tests:")
    evidence_md.append(f"- PRs: {', '.join(prs)}" if prs else "- PRs:")
    evidence_content = "\n".join(evidence_md)

    # Read current spec
    current_spec = read_text_or_exit(
        task_spec_path, f"Task {args.id} spec", use_json=args.json
    )

    # Patch sections
    try:
        updated_spec = patch_task_section(current_spec, "## Done summary", summary)
        updated_spec = patch_task_section(updated_spec, "## Evidence", evidence_content)
    except ValueError as e:
        error_exit(str(e), use_json=args.json)

    # All validation passed - now write (spec to tracked file, runtime to state-dir)
    atomic_write(task_spec_path, updated_spec)

    # Write runtime state to state-dir (not definition file)
    save_task_runtime(args.id, {"status": "done", "evidence": evidence})
    epic_id = epic_id_from_task(args.id)
    set_active_objective(epic_id, use_json=args.json)
    epic_path = flux_dir / EPICS_DIR / f"{epic_id}.json"
    if epic_path.exists():
        epic_data = normalize_epic(
            load_json_or_exit(epic_path, f"Epic {epic_id}", use_json=args.json)
        )
        tasks = tasks_for_epic(epic_id, use_json=args.json)
        if tasks and all(t.get("status") == "done" for t in tasks):
            epic_data["workflow_status"] = (
                "ready_for_handoff"
                if epic_data.get("implementation_target") == "engineer_handoff"
                else "ready_for_work"
            )
            epic_data["next_action"] = (
                f"/flux:epic-review {epic_id}"
                if epic_data.get("implementation_target") == "self_with_ai"
                else f"Prepare engineer handoff for {epic_id}"
            )
            epic_data["updated_at"] = now_iso()
            atomic_write_json(epic_path, epic_data)

    # NOTE: We no longer update epic timestamp on task done.
    # This reduces merge conflicts in multi-user scenarios.

    if args.json:
        json_output(
            {"id": args.id, "status": "done", "message": f"Task {args.id} completed"}
        )
    else:
        print(f"Task {args.id} completed")


def cmd_block(args: argparse.Namespace) -> None:
    """Block a task with a reason."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    if not is_task_id(args.id):
        error_exit(
            f"Invalid task ID: {args.id}. Expected format: fn-N.M or fn-N-slug.M (e.g., fn-1.2, fn-1-add-auth.2)", use_json=args.json
        )

    flux_dir = get_flux_dir()
    task_spec_path = flux_dir / TASKS_DIR / f"{args.id}.md"

    # Load task with merged runtime state
    task_data = load_task_with_state(args.id, use_json=args.json)

    if task_data["status"] == "done":
        error_exit(
            f"Cannot block task {args.id}: status is 'done'.", use_json=args.json
        )

    reason = read_text_or_exit(
        Path(args.reason_file), "Reason file", use_json=args.json
    ).strip()
    if not reason:
        error_exit("Reason file is empty", use_json=args.json)

    current_spec = read_text_or_exit(
        task_spec_path, f"Task {args.id} spec", use_json=args.json
    )
    summary = get_task_section(current_spec, "## Done summary")
    if summary.strip().lower() in ["tbd", ""]:
        new_summary = f"Blocked:\n{reason}"
    else:
        new_summary = f"{summary}\n\nBlocked:\n{reason}"

    try:
        updated_spec = patch_task_section(current_spec, "## Done summary", new_summary)
    except ValueError as e:
        error_exit(str(e), use_json=args.json)

    atomic_write(task_spec_path, updated_spec)

    # Write runtime state to state-dir (not definition file)
    save_task_runtime(args.id, {"status": "blocked", "blocked_reason": reason})

    if args.json:
        json_output(
            {"id": args.id, "status": "blocked", "message": f"Task {args.id} blocked"}
        )
    else:
        print(f"Task {args.id} blocked")
