"""
fluxctl_pkg.epics - Epic normalization, CRUD, workflow progress, artifacts, objectives, validation, load_all_epics.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Optional

from .utils import (
    ARTIFACTS_DIR,
    EPICS_DIR,
    FLUX_DIR,
    IMPLEMENTATION_TARGETS,
    META_FILE,
    OBJECTIVE_KINDS,
    SCOPE_MODES,
    SPECS_DIR,
    SUPPORTED_SCHEMA_VERSIONS,
    TASK_STATUS,
    TASKS_DIR,
    TECHNICAL_LEVELS,
    WORKFLOW_STATUSES,
    atomic_write,
    atomic_write_json,
    ensure_flux_exists,
    error_exit,
    generate_epic_suffix,
    get_actor,
    get_flux_dir,
    get_repo_root,
    is_epic_id,
    is_supported_schema,
    is_task_id,
    json_output,
    load_json,
    load_json_or_exit,
    now_iso,
    parse_id,
    read_file_or_stdin,
    read_text_or_exit,
    scan_max_epic_id,
    slugify,
    workflow_phases_for_mode,
)
from .config import get_config, get_default_config, deep_merge
from . import tracker
from .state import (
    default_prime_state,
    delete_task_runtime,
    get_active_objective,
    get_prime_state,
    get_state_store,
    load_meta,
    load_task_with_state,
    normalize_task,
    save_meta,
    set_active_objective,
    set_prime_state,
)


def normalize_epic(epic_data: dict) -> dict:
    """Apply defaults for optional epic fields."""
    if "plan_review_status" not in epic_data:
        epic_data["plan_review_status"] = "unknown"
    if "plan_reviewed_at" not in epic_data:
        epic_data["plan_reviewed_at"] = None
    if "completion_review_status" not in epic_data:
        epic_data["completion_review_status"] = "unknown"
    if "completion_reviewed_at" not in epic_data:
        epic_data["completion_reviewed_at"] = None
    if "branch_name" not in epic_data:
        epic_data["branch_name"] = None
    if "depends_on_epics" not in epic_data:
        epic_data["depends_on_epics"] = []
    # Backend spec defaults (for orchestration products like flux-swarm)
    if "default_impl" not in epic_data:
        epic_data["default_impl"] = None
    if "default_review" not in epic_data:
        epic_data["default_review"] = None
    if "default_sync" not in epic_data:
        epic_data["default_sync"] = None
    if "objective_kind" not in epic_data:
        epic_data["objective_kind"] = "feature"
    if epic_data["objective_kind"] not in OBJECTIVE_KINDS:
        epic_data["objective_kind"] = "feature"
    if "scope_mode" not in epic_data:
        epic_data["scope_mode"] = "shallow"
    if epic_data["scope_mode"] not in SCOPE_MODES:
        epic_data["scope_mode"] = "shallow"
    if "technical_level" not in epic_data:
        epic_data["technical_level"] = None
    if epic_data["technical_level"] not in TECHNICAL_LEVELS:
        epic_data["technical_level"] = None
    if "implementation_target" not in epic_data:
        epic_data["implementation_target"] = "self_with_ai"
    if epic_data["implementation_target"] not in IMPLEMENTATION_TARGETS:
        epic_data["implementation_target"] = "self_with_ai"
    allowed_phases = workflow_phases_for_mode(epic_data["scope_mode"])
    if "workflow_phase" not in epic_data:
        epic_data["workflow_phase"] = allowed_phases[0]
    if epic_data["workflow_phase"] not in allowed_phases:
        epic_data["workflow_phase"] = allowed_phases[0]
    if "workflow_step" not in epic_data:
        epic_data["workflow_step"] = "intake"
    if "workflow_status" not in epic_data:
        epic_data["workflow_status"] = "not_started"
    if epic_data["workflow_status"] not in WORKFLOW_STATUSES:
        epic_data["workflow_status"] = "not_started"
    if "workflow_summary" not in epic_data:
        epic_data["workflow_summary"] = ""
    if "open_questions" not in epic_data or not isinstance(epic_data["open_questions"], list):
        epic_data["open_questions"] = []
    if "resolved_decisions" not in epic_data or not isinstance(epic_data["resolved_decisions"], list):
        epic_data["resolved_decisions"] = []
    if "next_action" not in epic_data:
        epic_data["next_action"] = None
    if "scope_artifacts" not in epic_data or not isinstance(epic_data["scope_artifacts"], dict):
        epic_data["scope_artifacts"] = {}
    return epic_data


def workflow_progress(epic_data: dict) -> dict:
    """Compute workflow progress metrics for an epic."""
    phases = workflow_phases_for_mode(epic_data.get("scope_mode", "shallow"))
    current_phase = epic_data.get("workflow_phase", phases[0])
    try:
        phase_index = phases.index(current_phase)
    except ValueError:
        phase_index = 0
        current_phase = phases[0]
    completed = phase_index
    total = len(phases)
    percent = int((completed / total) * 100) if total else 0
    if epic_data.get("workflow_status") == "done":
        completed = total
        percent = 100
    elif epic_data.get("workflow_status") in {"ready_for_work", "ready_for_handoff"}:
        percent = int(((phase_index + 1) / total) * 100)
    return {
        "phases": phases,
        "current_phase": current_phase,
        "phase_index": phase_index,
        "completed_phases": completed,
        "total_phases": total,
        "percent": percent,
    }


def artifact_dir_for_epic(epic_id: str) -> Path:
    """Get artifact directory for an epic."""
    return get_flux_dir() / ARTIFACTS_DIR / epic_id


def artifact_path_for_phase(epic_id: str, phase: str) -> Path:
    """Get artifact path for an epic phase."""
    return artifact_dir_for_epic(epic_id) / f"{phase}.md"


def load_all_epics(use_json: bool = True) -> list[dict]:
    """Load all epics with defaults applied."""
    flux_dir = get_flux_dir()
    epics_dir = flux_dir / EPICS_DIR
    if not epics_dir.exists():
        return []
    epics = []
    for epic_file in sorted(epics_dir.glob("fn-*.json")):
        try:
            epics.append(
                normalize_epic(
                    load_json_or_exit(epic_file, f"Epic {epic_file.stem}", use_json=use_json)
                )
            )
        except SystemExit:
            raise
        except Exception:
            continue
    epics.sort(key=lambda e: parse_id(e.get("id", ""))[0] or 0)
    return epics


def choose_current_objective(current_actor: str, use_json: bool = True) -> Optional[dict]:
    """Choose the current objective based on active meta pointer and live state."""
    open_epics = [e for e in load_all_epics(use_json=use_json) if e.get("status") != "done"]
    if not open_epics:
        return None

    active_id = get_active_objective(use_json=use_json)
    if active_id:
        for epic in open_epics:
            if epic.get("id") == active_id:
                return epic

    # Prefer epic with in-progress task assigned to current actor.
    for epic in open_epics:
        tasks_dir = get_flux_dir() / TASKS_DIR
        if not tasks_dir.exists():
            break
        for task_file in sorted(tasks_dir.glob(f"{epic['id']}.*.json")):
            task_id = task_file.stem
            if not is_task_id(task_id):
                continue
            task_data = load_task_with_state(task_id, use_json=use_json)
            if (
                task_data.get("status") == "in_progress"
                and task_data.get("assignee") == current_actor
            ):
                return epic

    # Otherwise use most recently updated open epic.
    return sorted(
        open_epics,
        key=lambda e: (e.get("updated_at") or e.get("created_at") or "", e.get("id", "")),
        reverse=True,
    )[0]


def tasks_for_epic(epic_id: str, use_json: bool = True) -> list[dict]:
    """Load all tasks for an epic."""
    tasks_dir = get_flux_dir() / TASKS_DIR
    if not tasks_dir.exists():
        return []
    tasks = []
    for task_file in sorted(tasks_dir.glob(f"{epic_id}.*.json")):
        task_id = task_file.stem
        if not is_task_id(task_id):
            continue
        task = load_task_with_state(task_id, use_json=use_json)
        if "id" in task:
            tasks.append(task)
    tasks.sort(key=lambda t: parse_id(t.get("id", ""))[1] or 0)
    return tasks


def ready_state_for_epic(epic_id: str, use_json: bool = True) -> dict:
    """Compute ready/in-progress/blocked state for an epic."""
    from .utils import task_priority
    current_actor = get_actor()
    tasks = {task["id"]: task for task in tasks_for_epic(epic_id, use_json=use_json)}
    ready = []
    in_progress = []
    blocked = []
    for task in tasks.values():
        if task.get("status") == "in_progress":
            in_progress.append(task)
            continue
        if task.get("status") == "done":
            continue
        if task.get("status") == "blocked":
            blocked.append({"task": task, "blocked_by": ["status=blocked"]})
            continue
        deps_done = True
        blocking_deps = []
        for dep in task.get("depends_on", []):
            dep_task = tasks.get(dep)
            if not dep_task or dep_task.get("status") != "done":
                deps_done = False
                blocking_deps.append(dep)
        if deps_done:
            ready.append(task)
        else:
            blocked.append({"task": task, "blocked_by": blocking_deps})
    ready.sort(key=lambda t: ((task_priority(t)), parse_id(t["id"])[1] or 0, t.get("title", "")))
    in_progress.sort(
        key=lambda t: (
            0 if t.get("assignee") == current_actor else 1,
            task_priority(t),
            parse_id(t["id"])[1] or 0,
        )
    )
    blocked.sort(key=lambda b: (task_priority(b["task"]), parse_id(b["task"]["id"])[1] or 0))
    return {"ready": ready, "in_progress": in_progress, "blocked": blocked}


def validate_flux_root(flux_dir: Path) -> list[str]:
    """Validate .flux/ root invariants. Returns list of errors."""
    from .utils import META_FILE
    errors = []

    # Check meta.json exists and is valid
    meta_path = flux_dir / META_FILE
    if not meta_path.exists():
        errors.append(f"meta.json missing: {meta_path}")
    else:
        try:
            meta = load_json(meta_path)
            if not is_supported_schema(meta.get("schema_version")):
                errors.append(
                    "schema_version unsupported in meta.json "
                    f"(expected {', '.join(map(str, SUPPORTED_SCHEMA_VERSIONS))}, got {meta.get('schema_version')})"
                )
        except json.JSONDecodeError as e:
            errors.append(f"meta.json invalid JSON: {e}")
        except Exception as e:
            errors.append(f"meta.json unreadable: {e}")

    # Check required subdirectories exist
    from .utils import ARTIFACTS_DIR
    for subdir in [EPICS_DIR, SPECS_DIR, TASKS_DIR, ARTIFACTS_DIR]:
        if not (flux_dir / subdir).exists():
            errors.append(f"Required directory missing: {subdir}/")

    return errors


def validate_epic(
    flux_dir: Path, epic_id: str, use_json: bool = True
) -> tuple[list[str], list[str], int]:
    """Validate a single epic. Returns (errors, warnings, task_count)."""
    from .tasks import validate_task_spec_headings

    errors = []
    warnings = []

    epic_path = flux_dir / EPICS_DIR / f"{epic_id}.json"

    if not epic_path.exists():
        errors.append(f"Epic {epic_id} not found")
        return errors, warnings, 0

    epic_data = normalize_epic(
        load_json_or_exit(epic_path, f"Epic {epic_id}", use_json=use_json)
    )

    # Check epic spec exists
    epic_spec = flux_dir / SPECS_DIR / f"{epic_id}.md"
    if not epic_spec.exists():
        errors.append(f"Epic spec missing: {epic_spec}")

    # Validate epic dependencies
    deps = epic_data.get("depends_on_epics", [])
    if deps is None:
        deps = []
    if not isinstance(deps, list):
        errors.append(f"Epic {epic_id}: depends_on_epics must be a list")
    else:
        for dep in deps:
            if not isinstance(dep, str) or not is_epic_id(dep):
                errors.append(f"Epic {epic_id}: invalid depends_on_epics entry '{dep}'")
                continue
            if dep == epic_id:
                errors.append(f"Epic {epic_id}: depends_on_epics cannot include itself")
                continue
            dep_path = flux_dir / EPICS_DIR / f"{dep}.json"
            if not dep_path.exists():
                errors.append(f"Epic {epic_id}: depends_on_epics missing epic {dep}")

    # Get all tasks (with merged runtime state for accurate status)
    tasks_dir = flux_dir / TASKS_DIR
    tasks = {}
    if tasks_dir.exists():
        for task_file in tasks_dir.glob(f"{epic_id}.*.json"):
            task_id = task_file.stem
            if not is_task_id(task_id):
                continue  # Skip non-task files (e.g., fn-1.2-review.json)
            # Use merged state to get accurate status
            task_data = load_task_with_state(task_id, use_json=use_json)
            if "id" not in task_data:
                continue  # Skip artifact files (GH-21)
            tasks[task_data["id"]] = task_data

    # Validate each task
    for task_id, task in tasks.items():
        # Validate status (use merged state which defaults to "todo" if missing)
        status = task.get("status", "todo")
        if status not in TASK_STATUS:
            errors.append(f"Task {task_id}: invalid status '{status}'")

        # Check task spec exists
        task_spec_path = flux_dir / TASKS_DIR / f"{task_id}.md"
        if not task_spec_path.exists():
            errors.append(f"Task spec missing: {task_spec_path}")
        else:
            # Validate task spec headings
            try:
                spec_content = task_spec_path.read_text(encoding="utf-8")
            except Exception as e:
                errors.append(f"Task {task_id}: spec unreadable ({e})")
                continue
            heading_errors = validate_task_spec_headings(spec_content)
            for he in heading_errors:
                errors.append(f"Task {task_id}: {he}")

        # Check dependencies exist and are within epic
        for dep in task["depends_on"]:
            if dep not in tasks:
                errors.append(f"Task {task_id}: dependency {dep} not found")
            if not dep.startswith(epic_id + "."):
                errors.append(
                    f"Task {task_id}: dependency {dep} is outside epic {epic_id}"
                )

    # Cycle detection using DFS
    def has_cycle(task_id: str, visited: set, rec_stack: set) -> list[str]:
        visited.add(task_id)
        rec_stack.add(task_id)

        for dep in tasks.get(task_id, {}).get("depends_on", []):
            if dep not in visited:
                cycle = has_cycle(dep, visited, rec_stack)
                if cycle:
                    return [task_id] + cycle
            elif dep in rec_stack:
                return [task_id, dep]

        rec_stack.remove(task_id)
        return []

    visited = set()
    for task_id in tasks:
        if task_id not in visited:
            cycle = has_cycle(task_id, visited, set())
            if cycle:
                errors.append(f"Dependency cycle detected: {' -> '.join(cycle)}")
                break

    # Check epic done status consistency
    if epic_data["status"] == "done":
        for task_id, task in tasks.items():
            if task["status"] != "done":
                errors.append(
                    f"Epic marked done but task {task_id} is {task['status']}"
                )

    return errors, warnings, len(tasks)


# We need create_epic_spec in utils but it references SPECS_DIR which is already there.
# Actually create_epic_spec and create_task_spec are spec creation helpers - let's keep them accessible.

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


# ---------------------------------------------------------------------------
# cmd_ functions for epic-related CLI commands
# ---------------------------------------------------------------------------


def cmd_epic_create(args: argparse.Namespace) -> None:
    """Create a new epic."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    flux_dir = get_flux_dir()
    meta_path = flux_dir / META_FILE
    load_json_or_exit(meta_path, "meta.json", use_json=args.json)

    # MU-1: Scan-based allocation for merge safety
    # Scan existing epics to determine next ID (don't rely on counter)
    max_epic = scan_max_epic_id(flux_dir)
    epic_num = max_epic + 1
    # Use slugified title as suffix, fallback to random if empty/invalid
    slug = slugify(args.title)
    suffix = slug if slug else generate_epic_suffix()
    epic_id = f"fn-{epic_num}-{suffix}"

    # Double-check no collision (shouldn't happen with scan-based allocation)
    epic_json_path = flux_dir / EPICS_DIR / f"{epic_id}.json"
    epic_spec_path = flux_dir / SPECS_DIR / f"{epic_id}.md"
    if epic_json_path.exists() or epic_spec_path.exists():
        error_exit(
            f"Refusing to overwrite existing epic {epic_id}. "
            f"This shouldn't happen - check for orphaned files.",
            use_json=args.json,
        )

    # Create epic JSON
    technical_level = args.technical_level or get_config("workflow.technicalLevel", "semi_technical")
    scope_mode = args.scope_mode or get_config("workflow.defaultScopeMode", "shallow")
    implementation_target = args.implementation_target or get_config(
        "workflow.defaultImplementationTarget", "self_with_ai"
    )
    epic_data = {
        "id": epic_id,
        "title": args.title,
        "status": "open",
        "objective_kind": args.kind,
        "scope_mode": scope_mode if scope_mode in SCOPE_MODES else "shallow",
        "technical_level": technical_level if technical_level in TECHNICAL_LEVELS else None,
        "implementation_target": implementation_target
        if implementation_target in IMPLEMENTATION_TARGETS
        else "self_with_ai",
        "workflow_phase": "start",
        "workflow_step": "intake",
        "workflow_status": "not_started",
        "workflow_summary": "",
        "open_questions": [],
        "resolved_decisions": [],
        "next_action": "Continue scoping in /flux:scope",
        "scope_artifacts": {},
        "plan_review_status": "unknown",
        "plan_reviewed_at": None,
        "branch_name": args.branch if args.branch else epic_id,
        "depends_on_epics": [],
        "spec_path": f"{FLUX_DIR}/{SPECS_DIR}/{epic_id}.md",
        "next_task": 1,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    atomic_write_json(flux_dir / EPICS_DIR / f"{epic_id}.json", epic_data)
    set_active_objective(epic_id, use_json=args.json)

    # Create epic spec
    spec_content = create_epic_spec(epic_id, args.title)
    atomic_write(flux_dir / SPECS_DIR / f"{epic_id}.md", spec_content)

    # NOTE: We no longer update meta["next_epic"] since scan-based allocation
    # is the source of truth. This reduces merge conflicts.

    # Tracker hook: create Linear project if configured
    linear_project_id = tracker.on_epic_created(epic_data)
    if linear_project_id:
        epic_data["linear_project_id"] = linear_project_id
        atomic_write_json(flux_dir / EPICS_DIR / f"{epic_id}.json", epic_data)

    if args.json:
        json_output(
            {
                "id": epic_id,
                "title": args.title,
                "objective_kind": epic_data["objective_kind"],
                "scope_mode": epic_data["scope_mode"],
                "spec_path": epic_data["spec_path"],
                "message": f"Epic {epic_id} created",
            }
        )
    else:
        print(f"Epic {epic_id} created: {args.title}")


def cmd_show(args: argparse.Namespace) -> None:
    """Show epic or task details."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    flux_dir = get_flux_dir()

    if is_epic_id(args.id):
        epic_path = flux_dir / EPICS_DIR / f"{args.id}.json"
        epic_data = normalize_epic(
            load_json_or_exit(epic_path, f"Epic {args.id}", use_json=args.json)
        )

        # Get tasks for this epic (with merged runtime state)
        tasks = []
        tasks_dir = flux_dir / TASKS_DIR
        if tasks_dir.exists():
            for task_file in sorted(tasks_dir.glob(f"{args.id}.*.json")):
                task_id = task_file.stem
                if not is_task_id(task_id):
                    continue  # Skip non-task files (e.g., fn-1.2-review.json)
                task_data = load_task_with_state(task_id, use_json=args.json)
                if "id" not in task_data:
                    continue  # Skip artifact files (GH-21)
                tasks.append(
                    {
                        "id": task_data["id"],
                        "title": task_data["title"],
                        "status": task_data["status"],
                        "priority": task_data.get("priority"),
                        "depends_on": task_data.get("depends_on", task_data.get("deps", [])),
                    }
                )

        # Sort tasks by numeric suffix (safe via parse_id)
        def task_sort_key(t):
            _, task_num = parse_id(t["id"])
            return task_num if task_num is not None else 0

        tasks.sort(key=task_sort_key)

        result = {**epic_data, "tasks": tasks, "progress": workflow_progress(epic_data)}

        if args.json:
            json_output(result)
        else:
            print(f"Epic: {epic_data['id']}")
            print(f"Title: {epic_data['title']}")
            print(f"Status: {epic_data['status']}")
            print(
                "Workflow: "
                f"{epic_data['workflow_phase']} / {epic_data['workflow_step']} "
                f"[{epic_data['workflow_status']}]"
            )
            print(f"Spec: {epic_data['spec_path']}")
            print(f"\nTasks ({len(tasks)}):")
            for t in tasks:
                deps = (
                    f" (deps: {', '.join(t['depends_on'])})" if t["depends_on"] else ""
                )
                print(f"  [{t['status']}] {t['id']}: {t['title']}{deps}")

    elif is_task_id(args.id):
        # Load task with merged runtime state
        task_data = load_task_with_state(args.id, use_json=args.json)

        if args.json:
            json_output(task_data)
        else:
            print(f"Task: {task_data['id']}")
            print(f"Epic: {task_data['epic']}")
            print(f"Title: {task_data['title']}")
            print(f"Status: {task_data['status']}")
            print(f"Depends on: {', '.join(task_data['depends_on']) or 'none'}")
            print(f"Spec: {task_data['spec_path']}")

    else:
        error_exit(
            f"Invalid ID: {args.id}. Expected format: fn-N or fn-N-slug (epic), fn-N.M or fn-N-slug.M (task)",
            use_json=args.json,
        )


def cmd_epics(args: argparse.Namespace) -> None:
    """List all epics."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    flux_dir = get_flux_dir()
    epics_dir = flux_dir / EPICS_DIR

    epics = []
    if epics_dir.exists():
        for epic_file in sorted(epics_dir.glob("fn-*.json")):
            epic_data = normalize_epic(
                load_json_or_exit(
                    epic_file, f"Epic {epic_file.stem}", use_json=args.json
                )
            )
            # Count tasks (with merged runtime state)
            tasks_dir = flux_dir / TASKS_DIR
            task_count = 0
            done_count = 0
            if tasks_dir.exists():
                for task_file in tasks_dir.glob(f"{epic_data['id']}.*.json"):
                    task_id = task_file.stem
                    if not is_task_id(task_id):
                        continue  # Skip non-task files (e.g., fn-1.2-review.json)
                    task_data = load_task_with_state(task_id, use_json=args.json)
                    task_count += 1
                    if task_data.get("status") == "done":
                        done_count += 1

            epics.append(
                {
                    "id": epic_data["id"],
                    "title": epic_data["title"],
                    "status": epic_data["status"],
                    "tasks": task_count,
                    "done": done_count,
                }
            )

    # Sort by epic number
    def epic_sort_key(e):
        epic_num, _ = parse_id(e["id"])
        return epic_num if epic_num is not None else 0

    epics.sort(key=epic_sort_key)

    if args.json:
        json_output({"success": True, "epics": epics, "count": len(epics)})
    else:
        if not epics:
            print("No epics found.")
        else:
            print(f"Epics ({len(epics)}):\n")
            for e in epics:
                progress = f"{e['done']}/{e['tasks']}" if e["tasks"] > 0 else "0/0"
                print(
                    f"  [{e['status']}] {e['id']}: {e['title']} ({progress} tasks done)"
                )


def cmd_list(args: argparse.Namespace) -> None:
    """List all epics and their tasks."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    flux_dir = get_flux_dir()
    epics_dir = flux_dir / EPICS_DIR
    tasks_dir = flux_dir / TASKS_DIR

    # Load all epics
    epics = []
    if epics_dir.exists():
        for epic_file in sorted(epics_dir.glob("fn-*.json")):
            epic_data = normalize_epic(
                load_json_or_exit(
                    epic_file, f"Epic {epic_file.stem}", use_json=args.json
                )
            )
            epics.append(epic_data)

    # Sort epics by number
    def epic_sort_key(e):
        epic_num, _ = parse_id(e["id"])
        return epic_num if epic_num is not None else 0

    epics.sort(key=epic_sort_key)

    # Load all tasks grouped by epic (with merged runtime state)
    tasks_by_epic = {}
    all_tasks = []
    if tasks_dir.exists():
        for task_file in sorted(tasks_dir.glob("fn-*.json")):
            task_id = task_file.stem
            if not is_task_id(task_id):
                continue  # Skip non-task files (e.g., fn-1.2-review.json)
            task_data = load_task_with_state(task_id, use_json=args.json)
            if "id" not in task_data or "epic" not in task_data:
                continue  # Skip artifact files (GH-21)
            epic_id = task_data["epic"]
            if epic_id not in tasks_by_epic:
                tasks_by_epic[epic_id] = []
            tasks_by_epic[epic_id].append(task_data)
            all_tasks.append(
                {
                    "id": task_data["id"],
                    "epic": task_data["epic"],
                    "title": task_data["title"],
                    "status": task_data["status"],
                    "priority": task_data.get("priority"),
                    "depends_on": task_data.get("depends_on", task_data.get("deps", [])),
                }
            )

    # Sort tasks within each epic
    for epic_id in tasks_by_epic:
        tasks_by_epic[epic_id].sort(key=lambda t: parse_id(t["id"])[1] or 0)

    if args.json:
        epics_out = []
        for e in epics:
            task_list = tasks_by_epic.get(e["id"], [])
            done_count = sum(1 for t in task_list if t["status"] == "done")
            epics_out.append(
                {
                    "id": e["id"],
                    "title": e["title"],
                    "status": e["status"],
                    "tasks": len(task_list),
                    "done": done_count,
                }
            )
        json_output(
            {
                "success": True,
                "epics": epics_out,
                "tasks": all_tasks,
                "epic_count": len(epics),
                "task_count": len(all_tasks),
            }
        )
    else:
        if not epics:
            print("No epics or tasks found.")
            return

        total_tasks = len(all_tasks)
        total_done = sum(1 for t in all_tasks if t["status"] == "done")
        print(
            f"Flow Status: {len(epics)} epics, {total_tasks} tasks ({total_done} done)\n"
        )

        for e in epics:
            task_list = tasks_by_epic.get(e["id"], [])
            done_count = sum(1 for t in task_list if t["status"] == "done")
            progress = f"{done_count}/{len(task_list)}" if task_list else "0/0"
            print(f"[{e['status']}] {e['id']}: {e['title']} ({progress} done)")

            for t in task_list:
                deps = (
                    f" (deps: {', '.join(t['depends_on'])})" if t["depends_on"] else ""
                )
                print(f"    [{t['status']}] {t['id']}: {t['title']}{deps}")
            print()


def cmd_cat(args: argparse.Namespace) -> None:
    """Print markdown spec for epic or task."""
    if not ensure_flux_exists():
        error_exit(".flux/ does not exist. Run 'fluxctl init' first.", use_json=False)

    flux_dir = get_flux_dir()

    if is_epic_id(args.id):
        spec_path = flux_dir / SPECS_DIR / f"{args.id}.md"
    elif is_task_id(args.id):
        spec_path = flux_dir / TASKS_DIR / f"{args.id}.md"
    else:
        error_exit(
            f"Invalid ID: {args.id}. Expected format: fn-N or fn-N-slug (epic), fn-N.M or fn-N-slug.M (task)",
            use_json=False,
        )
        return

    content = read_text_or_exit(spec_path, f"Spec {args.id}", use_json=False)
    print(content)


def cmd_epic_set_plan(args: argparse.Namespace) -> None:
    """Set/overwrite entire epic spec from file."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    if not is_epic_id(args.id):
        error_exit(
            f"Invalid epic ID: {args.id}. Expected format: fn-N or fn-N-slug (e.g., fn-1, fn-1-add-auth)", use_json=args.json
        )

    flux_dir = get_flux_dir()
    epic_path = flux_dir / EPICS_DIR / f"{args.id}.json"

    # Verify epic exists (will be loaded later for timestamp update)
    if not epic_path.exists():
        error_exit(f"Epic {args.id} not found", use_json=args.json)

    # Read content from file or stdin
    content = read_file_or_stdin(args.file, "Input file", use_json=args.json)

    # Write spec
    spec_path = flux_dir / SPECS_DIR / f"{args.id}.md"
    atomic_write(spec_path, content)

    # Update epic timestamp
    epic_data = load_json_or_exit(epic_path, f"Epic {args.id}", use_json=args.json)
    epic_data["updated_at"] = now_iso()
    atomic_write_json(epic_path, epic_data)

    if args.json:
        json_output(
            {
                "id": args.id,
                "spec_path": str(spec_path),
                "message": f"Epic {args.id} spec updated",
            }
        )
    else:
        print(f"Epic {args.id} spec updated")


def cmd_epic_set_plan_review_status(args: argparse.Namespace) -> None:
    """Set plan review status for an epic."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    if not is_epic_id(args.id):
        error_exit(
            f"Invalid epic ID: {args.id}. Expected format: fn-N or fn-N-slug (e.g., fn-1, fn-1-add-auth)", use_json=args.json
        )

    flux_dir = get_flux_dir()
    epic_path = flux_dir / EPICS_DIR / f"{args.id}.json"

    if not epic_path.exists():
        error_exit(f"Epic {args.id} not found", use_json=args.json)

    epic_data = normalize_epic(
        load_json_or_exit(epic_path, f"Epic {args.id}", use_json=args.json)
    )
    epic_data["plan_review_status"] = args.status
    epic_data["plan_reviewed_at"] = now_iso()
    epic_data["updated_at"] = now_iso()
    atomic_write_json(epic_path, epic_data)

    if args.json:
        json_output(
            {
                "id": args.id,
                "plan_review_status": epic_data["plan_review_status"],
                "plan_reviewed_at": epic_data["plan_reviewed_at"],
                "message": f"Epic {args.id} plan review status set to {args.status}",
            }
        )
    else:
        print(f"Epic {args.id} plan review status set to {args.status}")


def cmd_epic_set_completion_review_status(args: argparse.Namespace) -> None:
    """Set completion review status for an epic."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    if not is_epic_id(args.id):
        error_exit(
            f"Invalid epic ID: {args.id}. Expected format: fn-N or fn-N-slug (e.g., fn-1, fn-1-add-auth)", use_json=args.json
        )

    flux_dir = get_flux_dir()
    epic_path = flux_dir / EPICS_DIR / f"{args.id}.json"

    if not epic_path.exists():
        error_exit(f"Epic {args.id} not found", use_json=args.json)

    epic_data = normalize_epic(
        load_json_or_exit(epic_path, f"Epic {args.id}", use_json=args.json)
    )
    epic_data["completion_review_status"] = args.status
    epic_data["completion_reviewed_at"] = now_iso()
    epic_data["updated_at"] = now_iso()
    atomic_write_json(epic_path, epic_data)

    if args.json:
        json_output(
            {
                "id": args.id,
                "completion_review_status": epic_data["completion_review_status"],
                "completion_reviewed_at": epic_data["completion_reviewed_at"],
                "message": f"Epic {args.id} completion review status set to {args.status}",
            }
        )
    else:
        print(f"Epic {args.id} completion review status set to {args.status}")


def cmd_epic_set_branch(args: argparse.Namespace) -> None:
    """Set epic branch name."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    if not is_epic_id(args.id):
        error_exit(
            f"Invalid epic ID: {args.id}. Expected format: fn-N or fn-N-slug (e.g., fn-1, fn-1-add-auth)", use_json=args.json
        )

    flux_dir = get_flux_dir()
    epic_path = flux_dir / EPICS_DIR / f"{args.id}.json"

    if not epic_path.exists():
        error_exit(f"Epic {args.id} not found", use_json=args.json)

    epic_data = normalize_epic(
        load_json_or_exit(epic_path, f"Epic {args.id}", use_json=args.json)
    )
    epic_data["branch_name"] = args.branch
    epic_data["updated_at"] = now_iso()
    atomic_write_json(epic_path, epic_data)

    if args.json:
        json_output(
            {
                "id": args.id,
                "branch_name": epic_data["branch_name"],
                "message": f"Epic {args.id} branch_name set to {args.branch}",
            }
        )
    else:
        print(f"Epic {args.id} branch_name set to {args.branch}")


def cmd_epic_set_title(args: argparse.Namespace) -> None:
    """Rename epic by setting a new title (updates slug in ID, renames all files)."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    old_id = args.id
    if not is_epic_id(old_id):
        error_exit(
            f"Invalid epic ID: {old_id}. Expected format: fn-N or fn-N-slug (e.g., fn-1, fn-1-add-auth)",
            use_json=args.json,
        )

    flux_dir = get_flux_dir()
    old_epic_path = flux_dir / EPICS_DIR / f"{old_id}.json"

    if not old_epic_path.exists():
        error_exit(f"Epic {old_id} not found", use_json=args.json)

    epic_data = normalize_epic(
        load_json_or_exit(old_epic_path, f"Epic {old_id}", use_json=args.json)
    )

    # Extract epic number from old ID
    epic_num, _ = parse_id(old_id)
    if epic_num is None:
        error_exit(f"Could not parse epic number from {old_id}", use_json=args.json)

    # Generate new ID with slugified title
    new_slug = slugify(args.title)
    new_suffix = new_slug if new_slug else generate_epic_suffix()
    new_id = f"fn-{epic_num}-{new_suffix}"

    # Check if new ID already exists (and isn't same as old)
    if new_id != old_id:
        new_epic_path = flux_dir / EPICS_DIR / f"{new_id}.json"
        if new_epic_path.exists():
            error_exit(
                f"Epic {new_id} already exists. Choose a different title.",
                use_json=args.json,
            )

    # Collect files to rename
    renames: list[tuple[Path, Path]] = []
    specs_dir = flux_dir / SPECS_DIR
    tasks_dir = flux_dir / TASKS_DIR
    epics_dir = flux_dir / EPICS_DIR

    # Epic JSON
    renames.append((old_epic_path, epics_dir / f"{new_id}.json"))

    # Epic spec
    old_spec = specs_dir / f"{old_id}.md"
    if old_spec.exists():
        renames.append((old_spec, specs_dir / f"{new_id}.md"))

    # Task files (JSON and MD)
    task_files: list[tuple[str, str]] = []  # (old_task_id, new_task_id)
    if tasks_dir.exists():
        for task_file in tasks_dir.glob(f"{old_id}.*.json"):
            task_id = task_file.stem
            if not is_task_id(task_id):
                continue
            # Extract task number
            _, task_num = parse_id(task_id)
            if task_num is not None:
                new_task_id = f"{new_id}.{task_num}"
                task_files.append((task_id, new_task_id))
                # JSON file
                renames.append((task_file, tasks_dir / f"{new_task_id}.json"))
                # MD file
                old_task_md = tasks_dir / f"{task_id}.md"
                if old_task_md.exists():
                    renames.append((old_task_md, tasks_dir / f"{new_task_id}.md"))

    # Checkpoint file
    old_checkpoint = flux_dir / f".checkpoint-{old_id}.json"
    if old_checkpoint.exists():
        renames.append((old_checkpoint, flux_dir / f".checkpoint-{new_id}.json"))

    # Perform renames (collect errors but continue)
    rename_errors: list[str] = []
    for old_path, new_path in renames:
        try:
            old_path.rename(new_path)
        except OSError as e:
            rename_errors.append(f"{old_path.name} -> {new_path.name}: {e}")

    if rename_errors:
        error_exit(
            f"Failed to rename some files: {'; '.join(rename_errors)}",
            use_json=args.json,
        )

    old_artifact_dir = artifact_dir_for_epic(old_id)
    new_artifact_dir = artifact_dir_for_epic(new_id)
    if old_artifact_dir.exists():
        new_artifact_dir.parent.mkdir(parents=True, exist_ok=True)
        try:
            old_artifact_dir.rename(new_artifact_dir)
        except OSError as e:
            error_exit(
                f"Failed to rename artifact directory {old_artifact_dir.name} -> {new_artifact_dir.name}: {e}",
                use_json=args.json,
            )

    # Update epic JSON content
    epic_data["id"] = new_id
    epic_data["title"] = args.title
    epic_data["spec_path"] = f"{FLUX_DIR}/{SPECS_DIR}/{new_id}.md"
    if epic_data.get("scope_artifacts"):
        updated_artifacts = {}
        for phase in epic_data["scope_artifacts"]:
            updated_artifacts[phase] = str(
                artifact_path_for_phase(new_id, phase).relative_to(get_repo_root())
            )
        epic_data["scope_artifacts"] = updated_artifacts
    epic_data["updated_at"] = now_iso()
    atomic_write_json(epics_dir / f"{new_id}.json", epic_data)

    if get_active_objective(use_json=args.json) == old_id:
        set_active_objective(new_id, use_json=args.json)

    # Update task JSON content
    task_id_map = dict(task_files)  # old_task_id -> new_task_id
    for old_task_id, new_task_id in task_files:
        task_path = tasks_dir / f"{new_task_id}.json"
        if task_path.exists():
            task_data = normalize_task(load_json(task_path))
            task_data["id"] = new_task_id
            task_data["epic"] = new_id
            task_data["spec_path"] = f"{FLUX_DIR}/{TASKS_DIR}/{new_task_id}.md"
            # Update depends_on references within same epic
            if task_data.get("depends_on"):
                task_data["depends_on"] = [
                    task_id_map.get(dep, dep) for dep in task_data["depends_on"]
                ]
            task_data["updated_at"] = now_iso()
            atomic_write_json(task_path, task_data)

    # Update depends_on_epics in other epics that reference this one
    updated_deps_in: list[str] = []
    if epics_dir.exists():
        for other_epic_file in epics_dir.glob("fn-*.json"):
            if other_epic_file.name == f"{new_id}.json":
                continue  # Skip self
            try:
                other_data = load_json(other_epic_file)
                deps = other_data.get("depends_on_epics", [])
                if old_id in deps:
                    other_data["depends_on_epics"] = [
                        new_id if d == old_id else d for d in deps
                    ]
                    other_data["updated_at"] = now_iso()
                    atomic_write_json(other_epic_file, other_data)
                    updated_deps_in.append(other_data.get("id", other_epic_file.stem))
            except (json.JSONDecodeError, OSError):
                pass  # Skip files that can't be parsed

    # Update state files if they exist
    state_store = get_state_store()
    state_tasks_dir = state_store.tasks_dir
    if state_tasks_dir.exists():
        for old_task_id, new_task_id in task_files:
            old_state = state_tasks_dir / f"{old_task_id}.state.json"
            new_state = state_tasks_dir / f"{new_task_id}.state.json"
            if old_state.exists():
                try:
                    old_state.rename(new_state)
                except OSError:
                    pass  # Non-critical

    result = {
        "old_id": old_id,
        "new_id": new_id,
        "title": args.title,
        "files_renamed": len(renames),
        "tasks_updated": len(task_files),
        "message": f"Epic renamed: {old_id} -> {new_id}",
    }
    if updated_deps_in:
        result["updated_deps_in"] = updated_deps_in

    if args.json:
        json_output(result)
    else:
        print(f"Epic renamed: {old_id} -> {new_id}")
        print(f"  Title: {args.title}")
        print(f"  Files renamed: {len(renames)}")
        print(f"  Tasks updated: {len(task_files)}")
        if updated_deps_in:
            print(f"  Updated deps in: {', '.join(updated_deps_in)}")


def cmd_epic_add_dep(args: argparse.Namespace) -> None:
    """Add epic-level dependency."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    epic_id = args.epic
    dep_id = args.depends_on

    if not is_epic_id(epic_id):
        error_exit(
            f"Invalid epic ID: {epic_id}. Expected format: fn-N or fn-N-slug (e.g., fn-1, fn-1-add-auth)",
            use_json=args.json,
        )
    if not is_epic_id(dep_id):
        error_exit(
            f"Invalid epic ID: {dep_id}. Expected format: fn-N or fn-N-slug (e.g., fn-1, fn-1-add-auth)",
            use_json=args.json,
        )
    if epic_id == dep_id:
        error_exit("Epic cannot depend on itself", use_json=args.json)

    flux_dir = get_flux_dir()
    epic_path = flux_dir / EPICS_DIR / f"{epic_id}.json"
    dep_path = flux_dir / EPICS_DIR / f"{dep_id}.json"

    if not epic_path.exists():
        error_exit(f"Epic {epic_id} not found", use_json=args.json)
    if not dep_path.exists():
        error_exit(f"Epic {dep_id} not found", use_json=args.json)

    epic_data = load_json_or_exit(epic_path, f"Epic {epic_id}", use_json=args.json)
    deps = epic_data.get("depends_on_epics", [])

    if dep_id in deps:
        # Already exists, no-op success
        if args.json:
            json_output(
                {
                    "success": True,
                    "id": epic_id,
                    "depends_on_epics": deps,
                    "message": f"{dep_id} already in dependencies",
                }
            )
        else:
            print(f"{dep_id} already in {epic_id} dependencies")
        return

    deps.append(dep_id)
    epic_data["depends_on_epics"] = deps
    epic_data["updated_at"] = now_iso()
    atomic_write_json(epic_path, epic_data)

    if args.json:
        json_output(
            {
                "success": True,
                "id": epic_id,
                "depends_on_epics": deps,
                "message": f"Added {dep_id} to {epic_id} dependencies",
            }
        )
    else:
        print(f"Added {dep_id} to {epic_id} dependencies")


def cmd_epic_rm_dep(args: argparse.Namespace) -> None:
    """Remove epic-level dependency."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    epic_id = args.epic
    dep_id = args.depends_on

    if not is_epic_id(epic_id):
        error_exit(
            f"Invalid epic ID: {epic_id}. Expected format: fn-N or fn-N-slug (e.g., fn-1, fn-1-add-auth)",
            use_json=args.json,
        )

    flux_dir = get_flux_dir()
    epic_path = flux_dir / EPICS_DIR / f"{epic_id}.json"

    if not epic_path.exists():
        error_exit(f"Epic {epic_id} not found", use_json=args.json)

    epic_data = load_json_or_exit(epic_path, f"Epic {epic_id}", use_json=args.json)
    deps = epic_data.get("depends_on_epics", [])

    if dep_id not in deps:
        # Not in deps, no-op success
        if args.json:
            json_output(
                {
                    "success": True,
                    "id": epic_id,
                    "depends_on_epics": deps,
                    "message": f"{dep_id} not in dependencies",
                }
            )
        else:
            print(f"{dep_id} not in {epic_id} dependencies")
        return

    deps.remove(dep_id)
    epic_data["depends_on_epics"] = deps
    epic_data["updated_at"] = now_iso()
    atomic_write_json(epic_path, epic_data)

    if args.json:
        json_output(
            {
                "success": True,
                "id": epic_id,
                "depends_on_epics": deps,
                "message": f"Removed {dep_id} from {epic_id} dependencies",
            }
        )
    else:
        print(f"Removed {dep_id} from {epic_id} dependencies")


def cmd_epic_set_backend(args: argparse.Namespace) -> None:
    """Set epic default backend specs for impl/review/sync."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    if not is_epic_id(args.id):
        error_exit(
            f"Invalid epic ID: {args.id}. Expected format: fn-N or fn-N-slug (e.g., fn-1, fn-1-add-auth)",
            use_json=args.json,
        )

    # At least one of impl/review/sync must be provided
    if args.impl is None and args.review is None and args.sync is None:
        error_exit(
            "At least one of --impl, --review, or --sync must be provided",
            use_json=args.json,
        )

    flux_dir = get_flux_dir()
    epic_path = flux_dir / EPICS_DIR / f"{args.id}.json"

    if not epic_path.exists():
        error_exit(f"Epic {args.id} not found", use_json=args.json)

    epic_data = normalize_epic(
        load_json_or_exit(epic_path, f"Epic {args.id}", use_json=args.json)
    )

    # Update fields (empty string means clear)
    updated = []
    if args.impl is not None:
        epic_data["default_impl"] = args.impl if args.impl else None
        updated.append(f"default_impl={args.impl or 'null'}")
    if args.review is not None:
        epic_data["default_review"] = args.review if args.review else None
        updated.append(f"default_review={args.review or 'null'}")
    if args.sync is not None:
        epic_data["default_sync"] = args.sync if args.sync else None
        updated.append(f"default_sync={args.sync or 'null'}")

    epic_data["updated_at"] = now_iso()
    atomic_write_json(epic_path, epic_data)

    if args.json:
        json_output(
            {
                "id": args.id,
                "default_impl": epic_data["default_impl"],
                "default_review": epic_data["default_review"],
                "default_sync": epic_data["default_sync"],
                "message": f"Epic {args.id} backend specs updated: {', '.join(updated)}",
            }
        )
    else:
        print(f"Epic {args.id} backend specs updated: {', '.join(updated)}")


def cmd_epic_set_context(args: argparse.Namespace) -> None:
    """Set epic workflow context fields."""
    if not ensure_flux_exists():
        error_exit(".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json)

    if not is_epic_id(args.id):
        error_exit(
            f"Invalid epic ID: {args.id}. Expected format: fn-N or fn-N-slug (e.g., fn-1, fn-1-add-auth)",
            use_json=args.json,
        )

    if (
        args.kind is None
        and args.scope_mode is None
        and args.technical_level is None
        and args.implementation_target is None
        and not args.activate
    ):
        error_exit(
            "At least one context field or --activate must be provided",
            use_json=args.json,
        )

    epic_path = get_flux_dir() / EPICS_DIR / f"{args.id}.json"
    if not epic_path.exists():
        error_exit(f"Epic {args.id} not found", use_json=args.json)

    epic_data = normalize_epic(load_json_or_exit(epic_path, f"Epic {args.id}", use_json=args.json))
    if args.kind is not None:
        epic_data["objective_kind"] = args.kind
    if args.scope_mode is not None:
        epic_data["scope_mode"] = args.scope_mode
        allowed_phases = workflow_phases_for_mode(args.scope_mode)
        if epic_data.get("workflow_phase") not in allowed_phases:
            epic_data["workflow_phase"] = allowed_phases[0]
    if args.technical_level is not None:
        epic_data["technical_level"] = args.technical_level
    if args.implementation_target is not None:
        epic_data["implementation_target"] = args.implementation_target
    epic_data["updated_at"] = now_iso()
    atomic_write_json(epic_path, epic_data)
    if args.activate:
        set_active_objective(args.id, use_json=args.json)

    if args.json:
        json_output(
            {
                "id": args.id,
                "objective_kind": epic_data["objective_kind"],
                "scope_mode": epic_data["scope_mode"],
                "technical_level": epic_data["technical_level"],
                "implementation_target": epic_data["implementation_target"],
                "active_objective": get_active_objective(use_json=args.json),
                "message": f"Epic {args.id} context updated",
            }
        )
    else:
        print(f"Epic {args.id} context updated")


def cmd_epic_set_workflow(args: argparse.Namespace) -> None:
    """Set epic workflow phase/progress fields."""
    if not ensure_flux_exists():
        error_exit(".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json)

    if not is_epic_id(args.id):
        error_exit(
            f"Invalid epic ID: {args.id}. Expected format: fn-N or fn-N-slug (e.g., fn-1, fn-1-add-auth)",
            use_json=args.json,
        )

    if (
        args.phase is None
        and args.step is None
        and args.status is None
        and args.summary is None
        and args.next_action is None
        and not args.clear_open_questions
        and not args.clear_decisions
        and not args.open_question
        and not args.decision
        and not args.activate
    ):
        error_exit(
            "At least one workflow field or --activate must be provided",
            use_json=args.json,
        )

    epic_path = get_flux_dir() / EPICS_DIR / f"{args.id}.json"
    if not epic_path.exists():
        error_exit(f"Epic {args.id} not found", use_json=args.json)

    epic_data = normalize_epic(load_json_or_exit(epic_path, f"Epic {args.id}", use_json=args.json))
    if args.phase is not None:
        allowed_phases = workflow_phases_for_mode(epic_data["scope_mode"])
        if args.phase not in allowed_phases:
            error_exit(
                f"Phase '{args.phase}' is not valid for scope mode '{epic_data['scope_mode']}'. "
                f"Allowed: {', '.join(allowed_phases)}",
                use_json=args.json,
            )
        epic_data["workflow_phase"] = args.phase
        if args.status is None and epic_data.get("workflow_status") != "done":
            epic_data["workflow_status"] = "in_progress"
    if args.step is not None:
        epic_data["workflow_step"] = args.step
    if args.status is not None:
        epic_data["workflow_status"] = args.status
    if args.summary is not None:
        epic_data["workflow_summary"] = args.summary
    if args.next_action is not None:
        epic_data["next_action"] = args.next_action
    if args.clear_open_questions:
        epic_data["open_questions"] = []
    if args.open_question:
        epic_data["open_questions"].extend(args.open_question)
    if args.clear_decisions:
        epic_data["resolved_decisions"] = []
    if args.decision:
        epic_data["resolved_decisions"].extend(args.decision)
    epic_data["updated_at"] = now_iso()
    atomic_write_json(epic_path, epic_data)
    if args.activate:
        set_active_objective(args.id, use_json=args.json)

    progress = workflow_progress(epic_data)
    if args.json:
        json_output(
            {
                "id": args.id,
                "workflow_phase": epic_data["workflow_phase"],
                "workflow_step": epic_data["workflow_step"],
                "workflow_status": epic_data["workflow_status"],
                "workflow_summary": epic_data["workflow_summary"],
                "open_questions": epic_data["open_questions"],
                "resolved_decisions": epic_data["resolved_decisions"],
                "next_action": epic_data["next_action"],
                "progress": progress,
                "active_objective": get_active_objective(use_json=args.json),
                "message": f"Epic {args.id} workflow updated",
            }
        )
    else:
        print(
            f"Epic {args.id} workflow updated: {epic_data['workflow_phase']} / "
            f"{epic_data['workflow_step']} [{epic_data['workflow_status']}]"
        )


def cmd_objective_current(args: argparse.Namespace) -> None:
    """Show the active objective."""
    if not ensure_flux_exists():
        error_exit(".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json)

    current_actor = get_actor()
    epic_data = choose_current_objective(current_actor, use_json=args.json)
    if not epic_data:
        if args.json:
            json_output({"objective": None, "message": "No active or open objective"})
        else:
            print("No active or open objective")
        return

    tasks = tasks_for_epic(epic_data["id"], use_json=args.json)
    progress = workflow_progress(epic_data)
    if args.json:
        json_output({"objective": epic_data, "tasks": tasks, "progress": progress})
    else:
        print(f"Current objective: {epic_data['id']} - {epic_data['title']}")
        print(
            f"{epic_data['objective_kind']} | {epic_data['scope_mode']} | "
            f"{epic_data['workflow_phase']} / {epic_data['workflow_step']}"
        )


def cmd_objective_switch(args: argparse.Namespace) -> None:
    """Set the active objective explicitly."""
    if not ensure_flux_exists():
        error_exit(".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json)

    if not is_epic_id(args.id):
        error_exit(
            f"Invalid epic ID: {args.id}. Expected format: fn-N or fn-N-slug (e.g., fn-1, fn-1-add-auth)",
            use_json=args.json,
        )

    epic_path = get_flux_dir() / EPICS_DIR / f"{args.id}.json"
    if not epic_path.exists():
        error_exit(f"Epic {args.id} not found", use_json=args.json)

    epic_data = normalize_epic(load_json_or_exit(epic_path, f"Epic {args.id}", use_json=args.json))
    if epic_data.get("status") == "done":
        error_exit(f"Epic {args.id} is already done", use_json=args.json)

    set_active_objective(args.id, use_json=args.json)
    if args.json:
        json_output({"active_objective": args.id, "message": f"Active objective set to {args.id}"})
    else:
        print(f"Active objective set to {args.id}")


def cmd_scope_status(args: argparse.Namespace) -> None:
    """Show scoped workflow status for an objective."""
    if not ensure_flux_exists():
        error_exit(".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json)

    current_actor = get_actor()
    epic_data = None
    if args.objective:
        if not is_epic_id(args.objective):
            error_exit(
                f"Invalid epic ID: {args.objective}. Expected format: fn-N or fn-N-slug",
                use_json=args.json,
            )
        epic_path = get_flux_dir() / EPICS_DIR / f"{args.objective}.json"
        if not epic_path.exists():
            error_exit(f"Epic {args.objective} not found", use_json=args.json)
        epic_data = normalize_epic(load_json_or_exit(epic_path, f"Epic {args.objective}", use_json=args.json))
    else:
        epic_data = choose_current_objective(current_actor, use_json=args.json)

    if not epic_data:
        if args.json:
            json_output({"objective": None, "message": "No active or open objective"})
        else:
            print("No active or open objective")
        return

    progress = workflow_progress(epic_data)
    readiness = ready_state_for_epic(epic_data["id"], use_json=args.json)
    artifacts = []
    for phase in progress["phases"]:
        path = artifact_path_for_phase(epic_data["id"], phase)
        if path.exists():
            artifacts.append({"phase": phase, "path": str(path.relative_to(get_repo_root()))})

    prime_state = get_prime_state(use_json=args.json)
    result = {
        "objective": {
            "id": epic_data["id"],
            "title": epic_data["title"],
            "objective_kind": epic_data["objective_kind"],
            "scope_mode": epic_data["scope_mode"],
            "technical_level": epic_data["technical_level"],
            "implementation_target": epic_data["implementation_target"],
        },
        "workflow": {
            "phase": epic_data["workflow_phase"],
            "step": epic_data["workflow_step"],
            "status": epic_data["workflow_status"],
            "summary": epic_data["workflow_summary"],
            "next_action": epic_data["next_action"],
            "open_questions": epic_data["open_questions"],
            "resolved_decisions": epic_data["resolved_decisions"],
        },
        "progress": progress,
        "prime": prime_state,
        "tasks": {
            "ready": [{"id": t["id"], "title": t["title"]} for t in readiness["ready"]],
            "in_progress": [
                {"id": t["id"], "title": t["title"], "assignee": t.get("assignee")}
                for t in readiness["in_progress"]
            ],
            "blocked": [
                {"id": b["task"]["id"], "title": b["task"]["title"], "blocked_by": b["blocked_by"]}
                for b in readiness["blocked"]
            ],
        },
        "artifacts": artifacts,
    }
    if args.json:
        json_output(result)
    else:
        phases = progress["phases"]
        phase_parts = []
        for idx, phase in enumerate(phases):
            if phase == epic_data["workflow_phase"]:
                phase_parts.append(f"[>{phase}<]")
            elif idx < progress["phase_index"]:
                phase_parts.append(f"[x {phase}]")
            else:
                phase_parts.append(f"[  {phase}]")
        print(f"Objective: {epic_data['id']} — {epic_data['title']}")
        print(
            f"Type: {epic_data['objective_kind']} | Mode: {epic_data['scope_mode']} | "
            f"Technical: {epic_data['technical_level'] or 'unset'} | "
            f"Target: {epic_data['implementation_target']}"
        )
        print(f"Prime: {prime_state['status']}")
        print("Progress: " + " -> ".join(phase_parts))
        print(
            f"Current: {epic_data['workflow_phase']} / {epic_data['workflow_step']} "
            f"[{epic_data['workflow_status']}]"
        )
        if epic_data.get("next_action"):
            print(f"Next: {epic_data['next_action']}")
        if epic_data.get("workflow_summary"):
            print(f"Summary: {epic_data['workflow_summary']}")


def cmd_session_state(args: argparse.Namespace) -> None:
    """Summarize the current workflow routing state."""
    if not ensure_flux_exists():
        result = {
            "state": "fresh_session_no_objective",
            "flux_exists": False,
            "objective": None,
            "task": None,
            "prime": default_prime_state(),
            "message": "Flux is not initialized yet.",
            "next_action": "/flux:setup",
        }
        if args.json:
            json_output(result)
        else:
            print(result["message"])
        return

    prime_state = get_prime_state(use_json=args.json)
    if prime_state.get("status") != "done":
        current_actor = get_actor()
        epic_data = choose_current_objective(current_actor, use_json=args.json)
        result = {
            "state": "needs_prime",
            "flux_exists": True,
            "objective": None
            if not epic_data
            else {
                "id": epic_data["id"],
                "title": epic_data["title"],
                "objective_kind": epic_data["objective_kind"],
                "scope_mode": epic_data["scope_mode"],
                "workflow_phase": epic_data["workflow_phase"],
                "workflow_step": epic_data["workflow_step"],
                "workflow_status": epic_data["workflow_status"],
            },
            "task": None,
            "prime": prime_state,
            "message": "Flux is installed, but this repository has not been primed yet. Run /flux:prime before scoping or implementation.",
            "next_action": "/flux:prime",
        }
        if args.json:
            json_output(result)
        else:
            print(result["message"])
        return

    current_actor = get_actor()
    epic_data = choose_current_objective(current_actor, use_json=args.json)
    if not epic_data:
        result = {
            "state": "fresh_session_no_objective",
            "flux_exists": True,
            "objective": None,
            "task": None,
            "prime": prime_state,
            "message": "No open objective. Start a new feature, bug, or refactor scope.",
            "next_action": "/flux:scope",
        }
        if args.json:
            json_output(result)
        else:
            print(result["message"])
        return

    readiness = ready_state_for_epic(epic_data["id"], use_json=args.json)
    current_task = None
    for task in readiness["in_progress"]:
        if task.get("assignee") == current_actor:
            current_task = task
            break

    all_tasks = tasks_for_epic(epic_data["id"], use_json=args.json)
    if current_task:
        state = "resume_work"
        message = f"Resume task {current_task['id']} for {epic_data['title']}."
        next_action = f"/flux:work {current_task['id']}"
    elif all_tasks and all(t.get("status") == "done" for t in all_tasks) and epic_data.get("completion_review_status") != "ship":
        state = "needs_completion_review"
        message = f"Implementation is done for {epic_data['title']}, but completion review is pending."
        next_action = f"/flux:epic-review {epic_data['id']}"
    elif epic_data.get("workflow_status") in {"not_started", "in_progress", "needs_confirmation"}:
        state = "resume_scope"
        message = f"Resume scoping for {epic_data['title']} at {epic_data['workflow_phase']}."
        next_action = f"/flux:scope {epic_data['title']}"
    elif epic_data.get("workflow_status") == "ready_for_handoff":
        state = "needs_review"
        message = f"{epic_data['title']} is ready for handoff."
        next_action = f"/flux:scope {epic_data['title']}"
    elif readiness["ready"]:
        state = "resume_work"
        current_task = readiness["ready"][0]
        message = f"Continue implementation with ready task {current_task['id']}."
        next_action = f"/flux:work {current_task['id']}"
    else:
        state = "idle_with_open_epics"
        message = f"{epic_data['title']} is open but waiting for the next decision."
        next_action = epic_data.get("next_action") or f"/flux:scope {epic_data['title']}"

    result = {
        "state": state,
        "flux_exists": True,
        "prime": prime_state,
        "objective": {
            "id": epic_data["id"],
            "title": epic_data["title"],
            "objective_kind": epic_data["objective_kind"],
            "scope_mode": epic_data["scope_mode"],
            "workflow_phase": epic_data["workflow_phase"],
            "workflow_step": epic_data["workflow_step"],
            "workflow_status": epic_data["workflow_status"],
        },
        "task": None if not current_task else {"id": current_task["id"], "title": current_task["title"]},
        "message": message,
        "next_action": next_action,
    }
    if args.json:
        json_output(result)
    else:
        print(message)


def cmd_artifact_write(args: argparse.Namespace) -> None:
    """Write a workflow artifact for an objective phase."""
    if not ensure_flux_exists():
        error_exit(".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json)

    if not is_epic_id(args.id):
        error_exit(
            f"Invalid epic ID: {args.id}. Expected format: fn-N or fn-N-slug",
            use_json=args.json,
        )

    epic_path = get_flux_dir() / EPICS_DIR / f"{args.id}.json"
    if not epic_path.exists():
        error_exit(f"Epic {args.id} not found", use_json=args.json)

    epic_data = normalize_epic(load_json_or_exit(epic_path, f"Epic {args.id}", use_json=args.json))
    allowed_phases = workflow_phases_for_mode(epic_data["scope_mode"])
    if args.phase not in allowed_phases:
        error_exit(
            f"Phase '{args.phase}' is not valid for scope mode '{epic_data['scope_mode']}'. "
            f"Allowed: {', '.join(allowed_phases)}",
            use_json=args.json,
        )

    content = read_file_or_stdin(args.file, "Artifact file", use_json=args.json)
    artifact_path = artifact_path_for_phase(args.id, args.phase)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(artifact_path, content)

    epic_data["scope_artifacts"][args.phase] = str(artifact_path.relative_to(get_repo_root()))
    epic_data["updated_at"] = now_iso()
    atomic_write_json(epic_path, epic_data)
    if args.activate:
        set_active_objective(args.id, use_json=args.json)

    if args.json:
        json_output(
            {
                "id": args.id,
                "phase": args.phase,
                "path": str(artifact_path.relative_to(get_repo_root())),
                "message": f"Artifact written for {args.id} phase {args.phase}",
            }
        )
    else:
        print(f"Artifact written: {artifact_path.relative_to(get_repo_root())}")


def cmd_artifact_read(args: argparse.Namespace) -> None:
    """Read a workflow artifact for an objective phase."""
    if not ensure_flux_exists():
        error_exit(".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json)

    if not is_epic_id(args.id):
        error_exit(
            f"Invalid epic ID: {args.id}. Expected format: fn-N or fn-N-slug",
            use_json=args.json,
        )

    artifact_path = artifact_path_for_phase(args.id, args.phase)
    if not artifact_path.exists():
        error_exit(
            f"No artifact found for {args.id} phase {args.phase}",
            use_json=args.json,
        )

    content = artifact_path.read_text(encoding="utf-8")
    if args.json:
        json_output(
            {
                "id": args.id,
                "phase": args.phase,
                "path": str(artifact_path.relative_to(get_repo_root())),
                "content": content,
            }
        )
    else:
        print(content)


def cmd_prime_status(args: argparse.Namespace) -> None:
    """Show whether this repo has been primed yet."""
    if not ensure_flux_exists():
        result = {
            "flux_exists": False,
            "prime": default_prime_state(),
            "prime_required": True,
            "message": "Flux is not initialized yet.",
            "next_action": "/flux:setup",
        }
        if args.json:
            json_output(result)
        else:
            print(result["message"])
        return

    prime = get_prime_state(use_json=args.json)
    prime_required = prime.get("status") != "done"
    message = (
        "Prime has not completed for this repository yet."
        if prime_required
        else "Prime has completed for this repository."
    )
    result = {
        "flux_exists": True,
        "prime": prime,
        "prime_required": prime_required,
        "message": message,
        "next_action": "/flux:prime" if prime_required else None,
    }
    if args.json:
        json_output(result)
    else:
        print(message)


def cmd_prime_mark(args: argparse.Namespace) -> None:
    """Internal helper to persist prime-state metadata."""
    if not ensure_flux_exists():
        error_exit(".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json)
    prime = set_prime_state(
        args.status,
        use_json=args.json,
        last_run_version=args.version,
    )
    if args.json:
        json_output({"prime": prime, "message": f"Prime marked {prime['status']}"})
    else:
        print(f"Prime marked {prime['status']}")


def cmd_epic_close(args: argparse.Namespace) -> None:
    """Close an epic (all tasks must be done)."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    if not is_epic_id(args.id):
        error_exit(
            f"Invalid epic ID: {args.id}. Expected format: fn-N or fn-N-slug (e.g., fn-1, fn-1-add-auth)", use_json=args.json
        )

    flux_dir = get_flux_dir()
    epic_path = flux_dir / EPICS_DIR / f"{args.id}.json"

    if not epic_path.exists():
        error_exit(f"Epic {args.id} not found", use_json=args.json)

    # Check all tasks are done (with merged runtime state)
    tasks_dir = flux_dir / TASKS_DIR
    if not tasks_dir.exists():
        error_exit(
            f"{TASKS_DIR}/ missing. Run 'fluxctl init' or fix repo state.",
            use_json=args.json,
        )
    incomplete = []
    for task_file in tasks_dir.glob(f"{args.id}.*.json"):
        task_id = task_file.stem
        if not is_task_id(task_id):
            continue  # Skip non-task files (e.g., fn-1.2-review.json)
        task_data = load_task_with_state(task_id, use_json=args.json)
        if task_data["status"] != "done":
            incomplete.append(f"{task_data['id']} ({task_data['status']})")

    if incomplete:
        error_exit(
            f"Cannot close epic: incomplete tasks - {', '.join(incomplete)}",
            use_json=args.json,
        )

    epic_data = load_json_or_exit(epic_path, f"Epic {args.id}", use_json=args.json)
    epic_data["status"] = "done"
    epic_data["workflow_status"] = "done"
    epic_data["updated_at"] = now_iso()
    atomic_write_json(epic_path, epic_data)
    if get_active_objective(use_json=args.json) == args.id:
        set_active_objective(None, use_json=args.json)

    if args.json:
        json_output(
            {"id": args.id, "status": "done", "message": f"Epic {args.id} closed"}
        )
    else:
        print(f"Epic {args.id} closed")


def cmd_checkpoint_save(args: argparse.Namespace) -> None:
    """Save full epic + tasks state to checkpoint file.

    Creates .flux/.checkpoint-fn-N.json with complete state snapshot.
    Use before plan-review or other long operations to enable recovery
    if context compaction occurs.
    """
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    epic_id = args.epic
    if not is_epic_id(epic_id):
        error_exit(
            f"Invalid epic ID: {epic_id}. Expected format: fn-N or fn-N-slug (e.g., fn-1, fn-1-add-auth)",
            use_json=args.json,
        )

    flux_dir = get_flux_dir()
    epic_path = flux_dir / EPICS_DIR / f"{epic_id}.json"
    spec_path = flux_dir / SPECS_DIR / f"{epic_id}.md"

    if not epic_path.exists():
        error_exit(f"Epic {epic_id} not found", use_json=args.json)

    # Load epic data
    epic_data = load_json_or_exit(epic_path, f"Epic {epic_id}", use_json=args.json)

    # Load epic spec
    epic_spec = ""
    if spec_path.exists():
        epic_spec = spec_path.read_text(encoding="utf-8")

    # Load all tasks for this epic (including runtime state)
    tasks_dir = flux_dir / TASKS_DIR
    store = get_state_store()
    tasks = []
    if tasks_dir.exists():
        for task_file in sorted(tasks_dir.glob(f"{epic_id}.*.json")):
            task_id = task_file.stem
            if not is_task_id(task_id):
                continue  # Skip non-task files (e.g., fn-1.2-review.json)
            task_data = load_json(task_file)
            task_spec_path = tasks_dir / f"{task_id}.md"
            task_spec = ""
            if task_spec_path.exists():
                task_spec = task_spec_path.read_text(encoding="utf-8")
            # Include runtime state in checkpoint
            runtime_state = store.load_runtime(task_id)
            tasks.append({
                "id": task_id,
                "data": task_data,
                "spec": task_spec,
                "runtime": runtime_state,  # May be None if no state file
            })

    # Build checkpoint
    checkpoint = {
        "schema_version": 2,  # Bumped for runtime state support
        "created_at": now_iso(),
        "epic_id": epic_id,
        "epic": {
            "data": epic_data,
            "spec": epic_spec,
        },
        "tasks": tasks,
    }

    # Write checkpoint
    checkpoint_path = flux_dir / f".checkpoint-{epic_id}.json"
    atomic_write_json(checkpoint_path, checkpoint)

    if args.json:
        json_output({
            "epic_id": epic_id,
            "checkpoint_path": str(checkpoint_path),
            "task_count": len(tasks),
            "message": f"Checkpoint saved: {checkpoint_path}",
        })
    else:
        print(f"Checkpoint saved: {checkpoint_path} ({len(tasks)} tasks)")


def cmd_checkpoint_restore(args: argparse.Namespace) -> None:
    """Restore epic + tasks state from checkpoint file.

    Reads .flux/.checkpoint-fn-N.json and overwrites current state.
    Use to recover after context compaction or to rollback changes.
    """
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    epic_id = args.epic
    if not is_epic_id(epic_id):
        error_exit(
            f"Invalid epic ID: {epic_id}. Expected format: fn-N or fn-N-slug (e.g., fn-1, fn-1-add-auth)",
            use_json=args.json,
        )

    flux_dir = get_flux_dir()
    checkpoint_path = flux_dir / f".checkpoint-{epic_id}.json"

    if not checkpoint_path.exists():
        error_exit(f"No checkpoint found for {epic_id}", use_json=args.json)

    # Load checkpoint
    checkpoint = load_json_or_exit(
        checkpoint_path, f"Checkpoint {epic_id}", use_json=args.json
    )

    # Validate checkpoint structure
    if "epic" not in checkpoint or "tasks" not in checkpoint:
        error_exit("Invalid checkpoint format", use_json=args.json)

    # Restore epic
    epic_path = flux_dir / EPICS_DIR / f"{epic_id}.json"
    spec_path = flux_dir / SPECS_DIR / f"{epic_id}.md"

    epic_data = checkpoint["epic"]["data"]
    epic_data["updated_at"] = now_iso()
    atomic_write_json(epic_path, epic_data)

    if checkpoint["epic"]["spec"]:
        atomic_write(spec_path, checkpoint["epic"]["spec"])

    # Restore tasks (including runtime state)
    tasks_dir = flux_dir / TASKS_DIR
    store = get_state_store()
    restored_tasks = []
    for task in checkpoint["tasks"]:
        task_id = task["id"]
        task_json_path = tasks_dir / f"{task_id}.json"
        task_spec_path = tasks_dir / f"{task_id}.md"

        task_data = task["data"]
        task_data["updated_at"] = now_iso()
        atomic_write_json(task_json_path, task_data)

        if task["spec"]:
            atomic_write(task_spec_path, task["spec"])

        # Restore runtime state from checkpoint (schema_version >= 2)
        runtime = task.get("runtime")
        if runtime is not None:
            # Restore saved runtime state
            with store.lock_task(task_id):
                store.save_runtime(task_id, runtime)
        else:
            # No runtime in checkpoint - delete any existing runtime state
            delete_task_runtime(task_id)

        restored_tasks.append(task_id)

    if args.json:
        json_output({
            "epic_id": epic_id,
            "checkpoint_created_at": checkpoint.get("created_at"),
            "tasks_restored": restored_tasks,
            "message": f"Restored {epic_id} from checkpoint ({len(restored_tasks)} tasks)",
        })
    else:
        print(f"Restored {epic_id} from checkpoint ({len(restored_tasks)} tasks)")
        print(f"Checkpoint was created at: {checkpoint.get('created_at', 'unknown')}")


def cmd_checkpoint_delete(args: argparse.Namespace) -> None:
    """Delete checkpoint file for an epic."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    epic_id = args.epic
    if not is_epic_id(epic_id):
        error_exit(
            f"Invalid epic ID: {epic_id}. Expected format: fn-N or fn-N-slug (e.g., fn-1, fn-1-add-auth)",
            use_json=args.json,
        )

    flux_dir = get_flux_dir()
    checkpoint_path = flux_dir / f".checkpoint-{epic_id}.json"

    if not checkpoint_path.exists():
        if args.json:
            json_output({
                "epic_id": epic_id,
                "deleted": False,
                "message": f"No checkpoint found for {epic_id}",
            })
        else:
            print(f"No checkpoint found for {epic_id}")
        return

    checkpoint_path.unlink()

    if args.json:
        json_output({
            "epic_id": epic_id,
            "deleted": True,
            "message": f"Deleted checkpoint for {epic_id}",
        })
    else:
        print(f"Deleted checkpoint for {epic_id}")


def cmd_validate(args: argparse.Namespace) -> None:
    """Validate epic structure or all epics."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    # Require either --epic or --all
    if not args.epic and not getattr(args, "all", False):
        error_exit("Must specify --epic or --all", use_json=args.json)

    flux_dir = get_flux_dir()

    # MU-3: Validate all mode
    if getattr(args, "all", False):
        # First validate .flux/ root invariants
        root_errors = validate_flux_root(flux_dir)

        epics_dir = flux_dir / EPICS_DIR

        # Find all epics (if epics dir exists)
        epic_ids = []
        epic_nums: dict[int, list[str]] = {}  # Track numeric IDs for collision detection
        if epics_dir.exists():
            for epic_file in sorted(epics_dir.glob("fn-*.json")):
                # Match: fn-N.json, fn-N-xxx.json (short), fn-N-slug.json (long)
                match = re.match(
                    r"^fn-(\d+)(?:-[a-z0-9][a-z0-9-]*[a-z0-9]|-[a-z0-9]{1,3})?\.json$",
                    epic_file.name,
                )
                if match:
                    epic_id = epic_file.stem
                    epic_ids.append(epic_id)
                    num = int(match.group(1))
                    if num not in epic_nums:
                        epic_nums[num] = []
                    epic_nums[num].append(epic_id)

        # Start with root errors
        all_errors = list(root_errors)

        # Detect epic ID collisions (multiple epics with same fn-N prefix)
        for num, ids in epic_nums.items():
            if len(ids) > 1:
                all_errors.append(
                    f"Epic ID collision: fn-{num} used by multiple epics: {', '.join(sorted(ids))}"
                )

        all_warnings = []

        # Detect orphaned specs (spec exists but no epic JSON)
        specs_dir = flux_dir / SPECS_DIR
        if specs_dir.exists():
            pattern = r"^fn-(\d+)(?:-[a-z0-9][a-z0-9-]*[a-z0-9]|-[a-z0-9]{1,3})?\.md$"
            for spec_file in specs_dir.glob("fn-*.md"):
                match = re.match(pattern, spec_file.name)
                if match:
                    spec_id = spec_file.stem
                    if spec_id not in epic_ids:
                        all_warnings.append(
                            f"Orphaned spec: {spec_file.name} has no matching epic JSON"
                        )
        total_tasks = 0
        epic_results = []

        for epic_id in epic_ids:
            errors, warnings, task_count = validate_epic(
                flux_dir, epic_id, use_json=args.json
            )
            all_errors.extend(errors)
            all_warnings.extend(warnings)
            total_tasks += task_count
            epic_results.append(
                {
                    "epic": epic_id,
                    "valid": len(errors) == 0,
                    "errors": errors,
                    "warnings": warnings,
                    "task_count": task_count,
                }
            )

        valid = len(all_errors) == 0

        if args.json:
            json_output(
                {
                    "valid": valid,
                    "root_errors": root_errors,
                    "epics": epic_results,
                    "total_epics": len(epic_ids),
                    "total_tasks": total_tasks,
                    "total_errors": len(all_errors),
                    "total_warnings": len(all_warnings),
                },
                success=valid,
            )
        else:
            print("Validation for all epics:")
            print(f"  Epics: {len(epic_ids)}")
            print(f"  Tasks: {total_tasks}")
            print(f"  Valid: {valid}")
            if all_errors:
                print("  Errors:")
                for e in all_errors:
                    print(f"    - {e}")
            if all_warnings:
                print("  Warnings:")
                for w in all_warnings:
                    print(f"    - {w}")

        # Exit with non-zero if validation failed
        if not valid:
            sys.exit(1)
        return

    # Single epic validation
    if not is_epic_id(args.epic):
        error_exit(
            f"Invalid epic ID: {args.epic}. Expected format: fn-N or fn-N-slug (e.g., fn-1, fn-1-add-auth)", use_json=args.json
        )

    errors, warnings, task_count = validate_epic(
        flux_dir, args.epic, use_json=args.json
    )
    valid = len(errors) == 0

    if args.json:
        json_output(
            {
                "epic": args.epic,
                "valid": valid,
                "errors": errors,
                "warnings": warnings,
                "task_count": task_count,
            },
            success=valid,
        )
    else:
        print(f"Validation for {args.epic}:")
        print(f"  Tasks: {task_count}")
        print(f"  Valid: {valid}")
        if errors:
            print("  Errors:")
            for e in errors:
                print(f"    - {e}")
        if warnings:
            print("  Warnings:")
            for w in warnings:
                print(f"    - {w}")

    # Exit with non-zero if validation failed
    if not valid:
        sys.exit(1)
