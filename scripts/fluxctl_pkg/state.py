"""
fluxctl_pkg.state - StateStore, runtime state, meta.json, prime state, task loading with state merge,
epic normalization, workflow progress, objectives, and epic/task queries.
"""

import json
import os
import subprocess
from abc import ABC, abstractmethod
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from .utils import (
    ARTIFACTS_DIR,
    EPICS_DIR,
    FLUX_DIR,
    IMPLEMENTATION_TARGETS,
    LOCK_EX,
    LOCK_UN,
    META_FILE,
    OBJECTIVE_KINDS,
    PRIME_STATUSES,
    RUNTIME_FIELDS,
    SCHEMA_VERSION,
    SCOPE_MODES,
    SPECS_DIR,
    SUPPORTED_SCHEMA_VERSIONS,
    TASKS_DIR,
    TECHNICAL_LEVELS,
    WORKFLOW_PHASES_DEEP,
    WORKFLOW_PHASES_SHALLOW,
    WORKFLOW_STATUSES,
    _flock,
    atomic_write,
    atomic_write_json,
    error_exit,
    get_actor,
    get_flux_dir,
    get_repo_root,
    is_epic_id,
    is_supported_schema,
    is_task_id,
    load_json,
    load_json_or_exit,
    now_iso,
    parse_id,
    task_priority,
    workflow_phases_for_mode,
)
from .config import load_flux_config, get_default_config, deep_merge


# --- State Directory ---


def get_state_dir() -> Path:
    """Get state directory for runtime task state.

    Resolution order:
    1. FLUX_STATE_DIR env var (explicit override for orchestrators)
    2. git common-dir (shared across all worktrees automatically)
    3. Fallback to .flux/state for non-git repos
    """
    # 1. Explicit override
    if state_dir := os.environ.get("FLUX_STATE_DIR"):
        return Path(state_dir).resolve()

    # 2. Git common-dir (shared across worktrees)
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-common-dir", "--path-format=absolute"],
            capture_output=True,
            text=True,
            check=True,
        )
        common = result.stdout.strip()
        return Path(common) / "flux-state"
    except subprocess.CalledProcessError:
        pass

    # 3. Fallback for non-git repos
    return get_flux_dir() / "state"


# --- StateStore (runtime task state) ---


class StateStore(ABC):
    """Abstract interface for runtime task state storage."""

    @abstractmethod
    def load_runtime(self, task_id: str) -> Optional[dict]:
        """Load runtime state for a task. Returns None if no state file."""
        ...

    @abstractmethod
    def save_runtime(self, task_id: str, data: dict) -> None:
        """Save runtime state for a task."""
        ...

    @abstractmethod
    def lock_task(self, task_id: str):
        """Context manager for exclusive task lock."""
        ...

    @abstractmethod
    def list_runtime_files(self) -> list[str]:
        """List all task IDs that have runtime state files."""
        ...


class LocalFileStateStore(StateStore):
    """File-based state store with fcntl locking."""

    def __init__(self, state_dir: Path):
        self.state_dir = state_dir
        self.tasks_dir = state_dir / "tasks"
        self.locks_dir = state_dir / "locks"

    def _state_path(self, task_id: str) -> Path:
        return self.tasks_dir / f"{task_id}.state.json"

    def _lock_path(self, task_id: str) -> Path:
        return self.locks_dir / f"{task_id}.lock"

    def load_runtime(self, task_id: str) -> Optional[dict]:
        state_path = self._state_path(task_id)
        if not state_path.exists():
            return None
        try:
            with open(state_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def save_runtime(self, task_id: str, data: dict) -> None:
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        state_path = self._state_path(task_id)
        content = json.dumps(data, indent=2, sort_keys=True) + "\n"
        atomic_write(state_path, content)

    @contextmanager
    def lock_task(self, task_id: str):
        """Acquire exclusive lock for task operations."""
        self.locks_dir.mkdir(parents=True, exist_ok=True)
        lock_path = self._lock_path(task_id)
        with open(lock_path, "w") as f:
            try:
                _flock(f, LOCK_EX)
                yield
            finally:
                _flock(f, LOCK_UN)

    def list_runtime_files(self) -> list[str]:
        if not self.tasks_dir.exists():
            return []
        return [
            f.stem.replace(".state", "")
            for f in self.tasks_dir.glob("*.state.json")
        ]


def get_state_store() -> LocalFileStateStore:
    """Get the state store instance."""
    return LocalFileStateStore(get_state_dir())


# --- Task Loading with State Merge ---


def load_task_definition(task_id: str, use_json: bool = True) -> dict:
    """Load task definition from tracked file (no runtime state)."""
    flux_dir = get_flux_dir()
    def_path = flux_dir / TASKS_DIR / f"{task_id}.json"
    return load_json_or_exit(def_path, f"Task {task_id}", use_json=use_json)


def load_task_with_state(task_id: str, use_json: bool = True) -> dict:
    """Load task definition merged with runtime state.

    Backward compatible: if no state file exists, reads legacy runtime
    fields from definition file.
    """
    definition = load_task_definition(task_id, use_json=use_json)

    # Load runtime state
    store = get_state_store()
    runtime = store.load_runtime(task_id)

    if runtime is None:
        # Backward compat: extract runtime fields from definition
        runtime = {k: definition[k] for k in RUNTIME_FIELDS if k in definition}
        if not runtime:
            runtime = {"status": "todo"}

    # Merge: runtime overwrites definition for runtime fields
    merged = {**definition, **runtime}
    return normalize_task(merged)


def save_task_runtime(task_id: str, updates: dict) -> None:
    """Write runtime state only (merge with existing). Never touch definition file."""
    store = get_state_store()
    with store.lock_task(task_id):
        current = store.load_runtime(task_id) or {"status": "todo"}
        merged = {**current, **updates, "updated_at": now_iso()}
        store.save_runtime(task_id, merged)


def reset_task_runtime(task_id: str) -> None:
    """Reset runtime state to baseline (overwrite, not merge). Used by task reset."""
    store = get_state_store()
    with store.lock_task(task_id):
        # Overwrite with clean baseline state
        store.save_runtime(task_id, {"status": "todo", "updated_at": now_iso()})


def delete_task_runtime(task_id: str) -> None:
    """Delete runtime state file entirely. Used by checkpoint restore when no runtime."""
    store = get_state_store()
    with store.lock_task(task_id):
        state_path = store._state_path(task_id)
        if state_path.exists():
            state_path.unlink()


def save_task_definition(task_id: str, definition: dict) -> None:
    """Write definition to tracked file (filters out runtime fields)."""
    flux_dir = get_flux_dir()
    def_path = flux_dir / TASKS_DIR / f"{task_id}.json"
    # Filter out runtime fields
    clean_def = {k: v for k, v in definition.items() if k not in RUNTIME_FIELDS}
    atomic_write_json(def_path, clean_def)


# --- Normalization ---


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


# --- Meta / Prime State ---


def default_prime_state() -> dict:
    """Default prime-state metadata stored in meta.json."""
    return {
        "status": "not_started",
        "last_run_at": None,
        "last_run_version": None,
    }


def current_flux_version() -> Optional[str]:
    """Best-effort local Flux version lookup."""
    candidates = [
        get_repo_root() / "package.json",
        get_repo_root() / ".claude-plugin" / "plugin.json",
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        version = data.get("version")
        if isinstance(version, str) and version.strip():
            return version.strip()
    return None


def load_meta(use_json: bool = True) -> dict:
    """Load meta.json."""
    meta_path = get_flux_dir() / META_FILE
    meta = load_json_or_exit(meta_path, "meta.json", use_json=use_json)
    if not isinstance(meta, dict):
        return {
            "schema_version": SCHEMA_VERSION,
            "next_epic": 1,
            "active_objective": None,
            "prime": default_prime_state(),
        }
    if "prime" not in meta or not isinstance(meta.get("prime"), dict):
        meta["prime"] = default_prime_state()
    else:
        prime = meta["prime"]
        merged_prime = default_prime_state()
        for key in ("status", "last_run_at", "last_run_version"):
            if key in prime:
                merged_prime[key] = prime[key]
        if merged_prime.get("status") not in PRIME_STATUSES:
            merged_prime["status"] = "not_started"
        meta["prime"] = merged_prime
    return meta


def save_meta(meta: dict) -> None:
    """Write meta.json."""
    atomic_write_json(get_flux_dir() / META_FILE, meta)


def get_active_objective(use_json: bool = True) -> Optional[str]:
    """Get active objective ID from meta.json."""
    meta = load_meta(use_json=use_json)
    active = meta.get("active_objective")
    return active if isinstance(active, str) and is_epic_id(active) else None


def set_active_objective(epic_id: Optional[str], use_json: bool = True) -> None:
    """Set or clear the active objective in meta.json."""
    meta = load_meta(use_json=use_json)
    if epic_id is None:
        meta.pop("active_objective", None)
    else:
        meta["active_objective"] = epic_id
    save_meta(meta)


def get_prime_state(use_json: bool = True) -> dict:
    """Get repo prime-state metadata."""
    meta = load_meta(use_json=use_json)
    prime = meta.get("prime")
    if not isinstance(prime, dict):
        return default_prime_state()
    merged = default_prime_state()
    for key in merged:
        if key in prime:
            merged[key] = prime[key]
    if merged["status"] not in PRIME_STATUSES:
        merged["status"] = "not_started"
    return merged


def set_prime_state(
    status: str,
    *,
    use_json: bool = True,
    last_run_at: Optional[str] = None,
    last_run_version: Optional[str] = None,
) -> dict:
    """Update repo prime-state metadata and return the normalized state."""
    if status not in PRIME_STATUSES:
        status = "not_started"
    meta = load_meta(use_json=use_json)
    prime = get_prime_state(use_json=use_json)
    prime["status"] = status
    if status == "done":
        prime["last_run_at"] = last_run_at or now_iso()
        prime["last_run_version"] = last_run_version or current_flux_version()
    elif status == "in_progress":
        prime["last_run_at"] = last_run_at or prime.get("last_run_at")
        if last_run_version is not None:
            prime["last_run_version"] = last_run_version
    else:
        prime["last_run_at"] = None
        prime["last_run_version"] = None
    meta["prime"] = prime
    save_meta(meta)
    return prime


# --- Session Phase ---


SESSION_PHASE_FILE = "session_phase.json"


def get_session_phase(use_json: bool = True) -> dict:
    """Get current session phase from state directory."""
    state_dir = get_state_dir()
    phase_path = state_dir / SESSION_PHASE_FILE
    if not phase_path.exists():
        return {"phase": "idle", "detail": None, "epic_id": None, "task_id": None, "updated_at": None}
    try:
        data = json.loads(phase_path.read_text(encoding="utf-8"))
    except Exception:
        return {"phase": "idle", "detail": None, "epic_id": None, "task_id": None, "updated_at": None}
    from .utils import SESSION_PHASES
    if data.get("phase") not in SESSION_PHASES:
        data["phase"] = "idle"
    return data


def set_session_phase(
    phase: str,
    *,
    detail: Optional[str] = None,
    epic_id: Optional[str] = None,
    task_id: Optional[str] = None,
    use_json: bool = True,
) -> dict:
    """Set current session phase in state directory."""
    from .utils import SESSION_PHASES
    if phase not in SESSION_PHASES:
        error_exit(f"Invalid session phase: {phase}. Valid: {', '.join(SESSION_PHASES)}", use_json=use_json)
    state_dir = get_state_dir()
    state_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "phase": phase,
        "detail": detail,
        "epic_id": epic_id,
        "task_id": task_id,
        "updated_at": now_iso(),
    }
    atomic_write_json(state_dir / SESSION_PHASE_FILE, data)
    return data


# --- Workflow Progress & Artifacts ---


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


# --- Epic & Task Queries ---


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
