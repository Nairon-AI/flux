"""
fluxctl_pkg.utils - Constants, imports, file locking, I/O helpers, ID parsing, actor resolution.
"""

import fnmatch
import json
import os
import re
import secrets
import shlex
import shutil
import string
import subprocess
import sys
import tempfile
import unicodedata
from abc import ABC, abstractmethod
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, ContextManager, Optional

# Platform-specific file locking (fcntl on Unix, no-op on Windows)
try:
    import fcntl

    def _flock(f, lock_type):
        fcntl.flock(f, lock_type)

    LOCK_EX = fcntl.LOCK_EX
    LOCK_UN = fcntl.LOCK_UN
except ImportError:
    # Windows: fcntl not available, use no-op (acceptable for single-machine use)
    def _flock(f, lock_type):
        pass

    LOCK_EX = 0
    LOCK_UN = 0


# --- Constants ---

SCHEMA_VERSION = 2
SUPPORTED_SCHEMA_VERSIONS = [1, 2]
FLUX_DIR = ".flux"
META_FILE = "meta.json"
EPICS_DIR = "epics"
SPECS_DIR = "specs"
TASKS_DIR = "tasks"
ARTIFACTS_DIR = "artifacts"
CONFIG_FILE = "config.json"

EPIC_STATUS = ["open", "done"]
TASK_STATUS = ["todo", "in_progress", "blocked", "done"]
OBJECTIVE_KINDS = ["feature", "bug", "refactor"]
SCOPE_MODES = ["shallow", "deep"]
TECHNICAL_LEVELS = ["non_technical", "semi_technical", "technical"]
IMPLEMENTATION_TARGETS = ["self_with_ai", "engineer_handoff"]
WORKFLOW_PHASES_DEEP = ["start", "discover", "define", "develop", "deliver", "handoff"]
WORKFLOW_PHASES_SHALLOW = ["start", "discover", "define", "deliver", "handoff"]
WORKFLOW_STATUSES = [
    "not_started",
    "in_progress",
    "needs_confirmation",
    "ready_for_work",
    "ready_for_handoff",
    "done",
]
PRIME_STATUSES = ["not_started", "in_progress", "done"]

# Session-level phases — tracks where the user/agent is in the full workflow lifecycle.
# These cover the entire state machine, not just scoping phases.
SESSION_PHASES = [
    "idle",              # No active workflow
    "prime",             # Running /flux:prime
    "ruminate",          # Mining past conversations
    "scope",             # Running /flux:scope (problem space)
    "stress_test",       # Dialectic subagents running
    "plan",              # Creating epic + tasks
    "plan_review",       # Reviewing plan quality
    "work",              # Task loop — implementing
    "impl_review",       # Per-task lightweight review
    "epic_review",       # Per-epic thorough review
    "quality",           # Tests + lint + desloppify
    "submit",            # Push + PR
    "reflect",           # Capturing session learnings
    "meditate",          # Pruning brain vault
    "gate",              # Staging validation
    "propose",           # Stakeholder feature proposal
    "rca",               # Root cause analysis
    "improve",           # Workflow optimization
    "remember",          # Storing knowledge (CLAUDE.md or brain/)
]

TASK_SPEC_HEADINGS = [
    "## Description",
    "## Acceptance",
    "## Done summary",
    "## Evidence",
]

# Runtime fields stored in state-dir (not tracked in git)
RUNTIME_FIELDS = {
    "status",
    "updated_at",
    "claimed_at",
    "assignee",
    "claim_note",
    "evidence",
    "blocked_reason",
}


# --- Helpers ---


def get_repo_root() -> Path:
    """Find git repo root."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        # Fallback to current directory
        return Path.cwd()


def get_flux_dir() -> Path:
    """Get .flux/ directory path."""
    return get_repo_root() / FLUX_DIR


def ensure_flux_exists() -> bool:
    """Check if .flux/ exists."""
    return get_flux_dir().exists()


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


def json_output(data: dict, success: bool = True) -> None:
    """Output JSON response."""
    result = {"success": success, **data}
    print(json.dumps(result, indent=2, default=str))


def error_exit(message: str, code: int = 1, use_json: bool = True) -> None:
    """Output error and exit."""
    if use_json:
        json_output({"error": message}, success=False)
    else:
        print(f"Error: {message}", file=sys.stderr)
    sys.exit(code)


def now_iso() -> str:
    """Current timestamp in ISO format."""
    return datetime.utcnow().isoformat() + "Z"


def is_supported_schema(version: Any) -> bool:
    """Check schema version compatibility."""
    try:
        return int(version) in SUPPORTED_SCHEMA_VERSIONS
    except Exception:
        return False


def atomic_write(path: Path, content: str) -> None:
    """Write file atomically via temp + rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def atomic_write_json(path: Path, data: dict) -> None:
    """Write JSON file atomically with sorted keys."""
    content = json.dumps(data, indent=2, sort_keys=True) + "\n"
    atomic_write(path, content)


def load_json(path: Path) -> dict:
    """Load JSON file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_json_or_exit(path: Path, what: str, use_json: bool = True) -> dict:
    """Load JSON file with safe error handling."""
    if not path.exists():
        error_exit(f"{what} missing: {path}", use_json=use_json)
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        error_exit(f"{what} invalid JSON: {path} ({e})", use_json=use_json)
    except Exception as e:
        error_exit(f"{what} unreadable: {path} ({e})", use_json=use_json)


def read_text_or_exit(path: Path, what: str, use_json: bool = True) -> str:
    """Read text file with safe error handling."""
    if not path.exists():
        error_exit(f"{what} missing: {path}", use_json=use_json)
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        error_exit(f"{what} unreadable: {path} ({e})", use_json=use_json)


def read_file_or_stdin(file_arg: str, what: str, use_json: bool = True) -> str:
    """Read from file path or stdin if file_arg is '-'.

    Supports heredoc usage: fluxctl ... --file - <<'EOF'
    """
    if file_arg == "-":
        try:
            return sys.stdin.read()
        except Exception as e:
            error_exit(f"Failed to read {what} from stdin: {e}", use_json=use_json)
    return read_text_or_exit(Path(file_arg), what, use_json=use_json)


def generate_epic_suffix(length: int = 3) -> str:
    """Generate random alphanumeric suffix for epic IDs (a-z0-9)."""
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def slugify(text: str, max_length: int = 40) -> Optional[str]:
    """Convert text to URL-safe slug for epic IDs.

    Uses Django pattern (stdlib only): normalize unicode, strip non-alphanumeric,
    collapse whitespace/hyphens. Returns None if result is empty (for fallback).

    Output contains only [a-z0-9-] to match parse_id() regex.

    Args:
        text: Input text to slugify
        max_length: Maximum length (40 default, leaves room for fn-XXX- prefix)

    Returns:
        Slugified string or None if empty
    """
    text = str(text)
    # Normalize unicode and convert to ASCII
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    # Remove non-word chars (except spaces and hyphens), lowercase
    text = re.sub(r"[^\w\s-]", "", text.lower())
    # Convert underscores to spaces (will be collapsed to hyphens)
    text = text.replace("_", " ")
    # Collapse whitespace and hyphens to single hyphen, strip leading/trailing
    text = re.sub(r"[-\s]+", "-", text).strip("-")
    # Truncate at word boundary if too long
    if max_length and len(text) > max_length:
        truncated = text[:max_length]
        if "-" in truncated:
            truncated = truncated.rsplit("-", 1)[0]
        text = truncated.strip("-")
    return text if text else None


def parse_id(id_str: str) -> tuple[Optional[int], Optional[int]]:
    """Parse ID into (epic_num, task_num). Returns (epic, None) for epic IDs.

    Supports formats:
    - Legacy: fn-N, fn-N.M
    - Short suffix: fn-N-xxx, fn-N-xxx.M (3-char random)
    - Slug suffix: fn-N-longer-slug, fn-N-longer-slug.M (slugified title)
    """
    # Pattern supports: fn-N, fn-N-x (1-3 char), fn-N-xx-yy (multi-segment slug)
    match = re.match(
        r"^fn-(\d+)(?:-[a-z0-9][a-z0-9-]*[a-z0-9]|-[a-z0-9]{1,3})?(?:\.(\d+))?$",
        id_str,
    )
    if not match:
        return None, None
    epic = int(match.group(1))
    task = int(match.group(2)) if match.group(2) else None
    return epic, task


def is_epic_id(id_str: str) -> bool:
    """Check if ID is an epic ID (fn-N)."""
    epic, task = parse_id(id_str)
    return epic is not None and task is None


def is_task_id(id_str: str) -> bool:
    """Check if ID is a task ID (fn-N.M)."""
    epic, task = parse_id(id_str)
    return epic is not None and task is not None


def epic_id_from_task(task_id: str) -> str:
    """Extract epic ID from task ID. Raises ValueError if invalid.

    Preserves suffix: fn-5-x7k.3 -> fn-5-x7k
    """
    epic, task = parse_id(task_id)
    if epic is None or task is None:
        raise ValueError(f"Invalid task ID: {task_id}")
    # Split on '.' and take epic part (preserves suffix if present)
    return task_id.rsplit(".", 1)[0]


def workflow_phases_for_mode(scope_mode: str) -> list[str]:
    """Return the ordered workflow phases for a scope mode."""
    return WORKFLOW_PHASES_DEEP if scope_mode == "deep" else WORKFLOW_PHASES_SHALLOW


def get_actor() -> str:
    """Determine current actor for soft-claim semantics.

    Priority:
    1. FLUX_ACTOR env var
    2. git config user.email
    3. git config user.name
    4. $USER env var
    5. "unknown"
    """
    # 1. FLUX_ACTOR env var
    if actor := os.environ.get("FLUX_ACTOR"):
        return actor.strip()

    # 2. git config user.email (preferred)
    try:
        result = subprocess.run(
            ["git", "config", "user.email"], capture_output=True, text=True, check=True
        )
        if email := result.stdout.strip():
            return email
    except subprocess.CalledProcessError:
        pass

    # 3. git config user.name
    try:
        result = subprocess.run(
            ["git", "config", "user.name"], capture_output=True, text=True, check=True
        )
        if name := result.stdout.strip():
            return name
    except subprocess.CalledProcessError:
        pass

    # 4. $USER env var
    if user := os.environ.get("USER"):
        return user

    # 5. fallback
    return "unknown"


def require_keys(obj: dict, keys: list[str], what: str, use_json: bool = True) -> None:
    """Validate dict has required keys. Exits on missing keys."""
    missing = [k for k in keys if k not in obj]
    if missing:
        error_exit(
            f"{what} missing required keys: {', '.join(missing)}", use_json=use_json
        )


def scan_max_epic_id(flux_dir: Path) -> int:
    """Scan .flux/epics/ and .flux/specs/ to find max epic number. Returns 0 if none exist.

    Handles legacy (fn-N.json), short suffix (fn-N-xxx.json), and slug (fn-N-slug.json) formats.
    Also scans specs/*.md as safety net for orphaned specs created without fluxctl.
    """
    max_n = 0
    pattern = r"^fn-(\d+)(?:-[a-z0-9][a-z0-9-]*[a-z0-9]|-[a-z0-9]{1,3})?\.(json|md)$"

    # Scan epics/*.json
    epics_dir = flux_dir / EPICS_DIR
    if epics_dir.exists():
        for epic_file in epics_dir.glob("fn-*.json"):
            match = re.match(pattern, epic_file.name)
            if match:
                n = int(match.group(1))
                max_n = max(max_n, n)

    # Scan specs/*.md as safety net (catches orphaned specs)
    specs_dir = flux_dir / SPECS_DIR
    if specs_dir.exists():
        for spec_file in specs_dir.glob("fn-*.md"):
            match = re.match(pattern, spec_file.name)
            if match:
                n = int(match.group(1))
                max_n = max(max_n, n)

    return max_n


def scan_max_task_id(flux_dir: Path, epic_id: str) -> int:
    """Scan .flux/tasks/ to find max task number for an epic. Returns 0 if none exist."""
    tasks_dir = flux_dir / TASKS_DIR
    if not tasks_dir.exists():
        return 0

    max_m = 0
    for task_file in tasks_dir.glob(f"{epic_id}.*.json"):
        match = re.match(rf"^{re.escape(epic_id)}\.(\d+)\.json$", task_file.name)
        if match:
            m = int(match.group(1))
            max_m = max(max_m, m)
    return max_m


def task_priority(task_data: dict) -> int:
    """Priority for sorting (None -> 999)."""
    try:
        if task_data.get("priority") is None:
            return 999
        return int(task_data.get("priority"))
    except Exception:
        return 999


def require_rp_cli() -> str:
    """Ensure rp-cli is available."""
    rp = shutil.which("rp-cli")
    if not rp:
        error_exit("rp-cli not found in PATH", use_json=False, code=2)
    return rp


def run_rp_cli(
    args: list[str], timeout: Optional[int] = None
) -> subprocess.CompletedProcess:
    """Run rp-cli with safe error handling and timeout.

    Args:
        args: Command arguments to pass to rp-cli
        timeout: Max seconds to wait. Default from FLUX_RP_TIMEOUT env or 1200s (20min).
    """
    if timeout is None:
        timeout = int(os.environ.get("FLUX_RP_TIMEOUT", "1200"))
    rp = require_rp_cli()
    cmd = [rp] + args
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, check=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        error_exit(f"rp-cli timed out after {timeout}s", use_json=False, code=3)
    except subprocess.CalledProcessError as e:
        msg = (e.stderr or e.stdout or str(e)).strip()
        error_exit(f"rp-cli failed: {msg}", use_json=False, code=2)


def normalize_repo_root(path: str) -> list[str]:
    """Normalize repo root for window matching."""
    root = os.path.realpath(path)
    roots = [root]
    if root.startswith("/private/tmp/"):
        roots.append("/tmp/" + root[len("/private/tmp/") :])
    elif root.startswith("/tmp/"):
        roots.append("/private/tmp/" + root[len("/tmp/") :])
    return list(dict.fromkeys(roots))


def parse_windows(raw: str) -> list[dict[str, Any]]:
    """Parse rp-cli windows JSON."""
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
        if (
            isinstance(data, dict)
            and "windows" in data
            and isinstance(data["windows"], list)
        ):
            return data["windows"]
    except json.JSONDecodeError as e:
        if "single-window mode" in raw:
            return [{"windowID": 1, "rootFolderPaths": []}]
        error_exit(f"windows JSON parse failed: {e}", use_json=False, code=2)
    error_exit("windows JSON has unexpected shape", use_json=False, code=2)


def extract_window_id(win: dict[str, Any]) -> Optional[int]:
    for key in ("windowID", "windowId", "id"):
        if key in win:
            try:
                return int(win[key])
            except Exception:
                return None
    return None


def extract_root_paths(win: dict[str, Any]) -> list[str]:
    for key in ("rootFolderPaths", "rootFolders", "rootFolderPath"):
        if key in win:
            val = win[key]
            if isinstance(val, list):
                return [str(v) for v in val]
            if isinstance(val, str):
                return [val]
    return []


def parse_builder_tab(output: str) -> str:
    match = re.search(r"Tab:\s*([A-Za-z0-9-]+)", output)
    if not match:
        error_exit("builder output missing Tab id", use_json=False, code=2)
    return match.group(1)


def parse_chat_id(output: str) -> Optional[str]:
    match = re.search(r"Chat\s*:\s*`([^`]+)`", output)
    if match:
        return match.group(1)
    match = re.search(r"\"chat_id\"\s*:\s*\"([^\"]+)\"", output)
    if match:
        return match.group(1)
    return None


def build_chat_payload(
    message: str,
    mode: str,
    new_chat: bool = False,
    chat_name: Optional[str] = None,
    chat_id: Optional[str] = None,
    selected_paths: Optional[list[str]] = None,
) -> str:
    payload: dict[str, Any] = {
        "message": message,
        "mode": mode,
    }
    if new_chat:
        payload["new_chat"] = True
    if chat_name:
        payload["chat_name"] = chat_name
    if chat_id:
        payload["chat_id"] = chat_id
    if selected_paths:
        payload["selected_paths"] = selected_paths
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


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
