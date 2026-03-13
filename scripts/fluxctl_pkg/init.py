"""Init, detect, status, state-path, agentmap, and migrate-state commands."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Optional

from .utils import (
    get_flux_dir,
    get_repo_root,
    SCHEMA_VERSION,
    SUPPORTED_SCHEMA_VERSIONS,
    FLUX_DIR,
    META_FILE,
    EPICS_DIR,
    SPECS_DIR,
    TASKS_DIR,
    MEMORY_DIR,
    ARTIFACTS_DIR,
    CONFIG_FILE,
    RUNTIME_FIELDS,
    json_output,
    error_exit,
    atomic_write,
    atomic_write_json,
    load_json,
    is_supported_schema,
    is_task_id,
    is_epic_id,
    parse_id,
    get_actor,
    ensure_flux_exists,
    current_flux_version,
)
from .state import (
    get_state_dir,
    get_state_store,
    load_task_with_state,
    normalize_epic,
    load_meta,
    save_meta,
    default_prime_state,
    get_prime_state,
    choose_current_objective,
    load_all_epics,
)
from .config import get_default_config, deep_merge, load_flux_config
from .ralph import find_active_runs


# ---------------------------------------------------------------------------
# cmd_init
# ---------------------------------------------------------------------------

def cmd_init(args: argparse.Namespace) -> None:
    """Initialize or upgrade .flux/ directory structure (idempotent)."""
    flux_dir = get_flux_dir()
    actions = []

    # Create directories if missing (idempotent, never destroys existing)
    for subdir in [EPICS_DIR, SPECS_DIR, TASKS_DIR, MEMORY_DIR, ARTIFACTS_DIR]:
        dir_path = flux_dir / subdir
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
            actions.append(f"created {subdir}/")

    # Create meta.json if missing (never overwrite existing)
    meta_path = flux_dir / META_FILE
    if not meta_path.exists():
        meta = {
            "schema_version": SCHEMA_VERSION,
            "next_epic": 1,
            "active_objective": None,
            "prime": default_prime_state(),
        }
        atomic_write_json(meta_path, meta)
        actions.append("created meta.json")
    else:
        try:
            raw_meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if not isinstance(raw_meta, dict):
                raw_meta = {"schema_version": SCHEMA_VERSION, "next_epic": 1}
        except (json.JSONDecodeError, Exception):
            raw_meta = {"schema_version": SCHEMA_VERSION, "next_epic": 1}
        merged_meta = {
            "schema_version": raw_meta.get("schema_version", SCHEMA_VERSION),
            "next_epic": raw_meta.get("next_epic", 1),
            "active_objective": raw_meta.get("active_objective"),
            "prime": raw_meta.get("prime", default_prime_state()),
        }
        if merged_meta != raw_meta:
            atomic_write_json(meta_path, merged_meta)
            actions.append("upgraded meta.json (added missing keys)")

    # Config: create or upgrade (merge missing defaults)
    config_path = flux_dir / CONFIG_FILE
    if not config_path.exists():
        atomic_write_json(config_path, get_default_config())
        actions.append("created config.json")
    else:
        # Load raw config, compare with merged (which includes new defaults)
        try:
            raw = json.loads(config_path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raw = {}
        except (json.JSONDecodeError, Exception):
            raw = {}
        merged = deep_merge(get_default_config(), raw)
        if merged != raw:
            atomic_write_json(config_path, merged)
            actions.append("upgraded config.json (added missing keys)")

    # Output
    if actions:
        message = f".flux/ updated: {', '.join(actions)}"
    else:
        message = ".flux/ already up to date"

    if args.json:
        json_output(
            {"success": True, "message": message, "path": str(flux_dir), "actions": actions}
        )
    else:
        print(message)


# ---------------------------------------------------------------------------
# cmd_detect
# ---------------------------------------------------------------------------

def cmd_detect(args: argparse.Namespace) -> None:
    """Check if .flux/ exists and is valid."""
    flux_dir = get_flux_dir()
    exists = flux_dir.exists()
    valid = False
    issues = []

    if exists:
        meta_path = flux_dir / META_FILE
        if not meta_path.exists():
            issues.append("meta.json missing")
        else:
            try:
                meta = load_json(meta_path)
                if not is_supported_schema(meta.get("schema_version")):
                    issues.append(
                        f"schema_version unsupported (expected {', '.join(map(str, SUPPORTED_SCHEMA_VERSIONS))})"
                    )
            except Exception as e:
                issues.append(f"meta.json parse error: {e}")

        # Check required subdirectories
        for subdir in [EPICS_DIR, SPECS_DIR, TASKS_DIR, MEMORY_DIR, ARTIFACTS_DIR]:
            if not (flux_dir / subdir).exists():
                issues.append(f"{subdir}/ missing")

        valid = len(issues) == 0

    if args.json:
        result = {
            "exists": exists,
            "valid": valid,
            "path": str(flux_dir) if exists else None,
        }
        if issues:
            result["issues"] = issues
        json_output(result)
    else:
        if exists and valid:
            print(f".flux/ exists and is valid at {flux_dir}")
        elif exists:
            print(f".flux/ exists but has issues at {flux_dir}:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(".flux/ does not exist")


# ---------------------------------------------------------------------------
# cmd_status
# ---------------------------------------------------------------------------

def cmd_status(args: argparse.Namespace) -> None:
    """Show .flux state and active Ralph runs."""
    flux_dir = get_flux_dir()
    flux_exists = flux_dir.exists()
    current_actor = get_actor()
    current_objective = (
        choose_current_objective(current_actor, use_json=args.json) if flux_exists else None
    )
    prime_state = get_prime_state(use_json=args.json) if flux_exists else default_prime_state()

    # Count epics and tasks by status
    epic_counts = {"open": 0, "done": 0}
    task_counts = {"todo": 0, "in_progress": 0, "blocked": 0, "done": 0}

    if flux_exists:
        epics_dir = flux_dir / EPICS_DIR
        tasks_dir = flux_dir / TASKS_DIR

        if epics_dir.exists():
            for epic_file in epics_dir.glob("fn-*.json"):
                try:
                    epic_data = load_json(epic_file)
                    status = epic_data.get("status", "open")
                    if status in epic_counts:
                        epic_counts[status] += 1
                except Exception:
                    pass

        if tasks_dir.exists():
            for task_file in tasks_dir.glob("fn-*.json"):
                task_id = task_file.stem
                if not is_task_id(task_id):
                    continue  # Skip non-task files (e.g., fn-1.2-review.json)
                try:
                    # Use merged state for accurate status counts
                    task_data = load_task_with_state(task_id, use_json=True)
                    status = task_data.get("status", "todo")
                    if status in task_counts:
                        task_counts[status] += 1
                except Exception:
                    pass

    # Get active runs
    active_runs = find_active_runs()

    if args.json:
        json_output(
            {
                "success": True,
                "flux_exists": flux_exists,
                "epics": epic_counts,
                "tasks": task_counts,
                "runs": [
                    {
                        "id": r["id"],
                        "iteration": r["iteration"],
                        "current_epic": r["current_epic"],
                        "current_task": r["current_task"],
                        "paused": r["paused"],
                        "stopped": r["stopped"],
                    }
                    for r in active_runs
                ],
                "current_objective": None
                if not current_objective
                else {
                    "id": current_objective["id"],
                    "title": current_objective["title"],
                    "objective_kind": current_objective["objective_kind"],
                    "scope_mode": current_objective["scope_mode"],
                    "workflow_phase": current_objective["workflow_phase"],
                    "workflow_step": current_objective["workflow_step"],
                    "workflow_status": current_objective["workflow_status"],
                    "next_action": current_objective.get("next_action"),
                },
                "prime": prime_state,
            }
        )
    else:
        if not flux_exists:
            print(".flux/ not initialized")
        else:
            total_epics = sum(epic_counts.values())
            total_tasks = sum(task_counts.values())
            print(f"Epics: {epic_counts['open']} open, {epic_counts['done']} done")
            print(
                f"Tasks: {task_counts['todo']} todo, {task_counts['in_progress']} in_progress, "
                f"{task_counts['done']} done, {task_counts['blocked']} blocked"
            )

        print()
        if active_runs:
            print("Active runs:")
            for r in active_runs:
                state = []
                if r["paused"]:
                    state.append("PAUSED")
                if r["stopped"]:
                    state.append("STOPPED")
                state_str = f" [{', '.join(state)}]" if state else ""
                task_info = ""
                if r["current_task"]:
                    task_info = f", working on {r['current_task']}"
                elif r["current_epic"]:
                    task_info = f", epic {r['current_epic']}"
                iter_info = f"iteration {r['iteration']}" if r["iteration"] else "starting"
                print(f"  {r['id']} ({iter_info}{task_info}){state_str}")
        else:
            print("No active runs")
        if current_objective:
            print()
            print(
                f"Current objective: {current_objective['id']} "
                f"({current_objective['objective_kind']}, {current_objective['scope_mode']})"
            )
            print(
                f"Phase: {current_objective['workflow_phase']} / "
                f"{current_objective['workflow_step']} [{current_objective['workflow_status']}]"
            )
            if current_objective.get("next_action"):
                print(f"Next: {current_objective['next_action']}")
        if flux_exists:
            print()
            prime_line = f"Prime: {prime_state['status']}"
            if prime_state.get("last_run_at"):
                prime_line += f" at {prime_state['last_run_at']}"
            if prime_state.get("last_run_version"):
                prime_line += f" (v{prime_state['last_run_version']})"
            print(prime_line)


# ---------------------------------------------------------------------------
# cmd_state_path
# ---------------------------------------------------------------------------

def cmd_state_path(args: argparse.Namespace) -> None:
    """Show resolved state directory path."""
    state_dir = get_state_dir()

    if args.task:
        if not is_task_id(args.task):
            error_exit(
                f"Invalid task ID: {args.task}. Expected format: fn-N.M or fn-N-slug.M (e.g., fn-1.2, fn-1-add-auth.2)",
                use_json=args.json,
            )
        state_path = state_dir / "tasks" / f"{args.task}.state.json"
        if args.json:
            json_output({"state_dir": str(state_dir), "task_state_path": str(state_path)})
        else:
            print(state_path)
    else:
        if args.json:
            json_output({"state_dir": str(state_dir)})
        else:
            print(state_dir)


# ---------------------------------------------------------------------------
# Agentmap section
# ---------------------------------------------------------------------------

AGENTMAP_SUPPORTED_EXTENSIONS = {
    ".ts",
    ".tsx",
    ".mts",
    ".cts",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".py",
    ".pyi",
    ".rs",
    ".go",
    ".zig",
    ".c",
    ".h",
    ".cpp",
    ".hpp",
    ".cc",
    ".cxx",
}
AGENTMAP_MAX_HEADER_LINES = 50
AGENTMAP_MAX_DESCRIPTION_LINES = 25
AGENTMAP_LICENSE_PATTERNS = [
    r"\bcopyright\s*(?:\(c\)|©|\d{4})",
    r"\bspdx-license-identifier\s*:",
    r"\ball rights reserved\b",
    r"\blicensed under\b",
    r"\bpermission is hereby granted\b",
    r"\bredistribution and use\b",
    r"\bthis source code is licensed\b",
    r"\bwithout warranty\b",
    r'\bthe software is provided "as is"\b',
]


def _agentmap_supported(path: Path) -> bool:
    return path.suffix.lower() in AGENTMAP_SUPPORTED_EXTENSIONS


def _agentmap_is_readme(path: Path) -> bool:
    name = path.name.lower()
    return name == "readme" or name == "readme.md"


def _agentmap_matches(rel_path: str, filters: list[str], ignores: list[str]) -> bool:
    if filters and not any(fnmatch.fnmatch(rel_path, pattern) for pattern in filters):
        return False
    if any(fnmatch.fnmatch(rel_path, pattern) for pattern in ignores):
        return False
    return True


def _agentmap_normalize_comment_lines(lines: list[str]) -> Optional[str]:
    cleaned = []
    for raw in lines[:AGENTMAP_MAX_DESCRIPTION_LINES]:
        line = raw.strip()
        line = re.sub(r"^(///|//!|//|#)\s?", "", line)
        line = re.sub(r"^/\*\*?\s?", "", line)
        line = re.sub(r"\*/$", "", line).strip()
        line = re.sub(r"^\*\s?", "", line)
        line = line.strip()
        if line:
            cleaned.append(line)
    if not cleaned:
        return None
    return " ".join(cleaned)


def _agentmap_is_license_comment(text: str) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in AGENTMAP_LICENSE_PATTERNS)


def _agentmap_is_reference_directive(text: str) -> bool:
    return bool(re.match(r"^///\s*<reference\s", text.strip()))


def _agentmap_truncate_lines(lines: list[str]) -> list[str]:
    if len(lines) <= AGENTMAP_MAX_DESCRIPTION_LINES:
        return lines
    remaining = len(lines) - AGENTMAP_MAX_DESCRIPTION_LINES
    return lines[:AGENTMAP_MAX_DESCRIPTION_LINES] + [f"... and {remaining} more lines"]


def _agentmap_extract_block_comment(
    lines: list[str], start: int, opener: str, closer: str
) -> tuple[Optional[str], int]:
    first = lines[start].strip()
    payload = [first[len(opener) :]]
    idx = start
    while idx < len(lines):
        current = lines[idx].strip()
        if idx != start:
            payload.append(current)
        if closer in current:
            joined = "\n".join(payload).split(closer, 1)[0]
            return _agentmap_normalize_comment_lines(joined.splitlines()), idx + 1
        idx += 1
    return _agentmap_normalize_comment_lines(payload), idx


def _agentmap_is_js_directive(line: str) -> bool:
    stripped = line.strip().rstrip(";")
    return stripped in {'"use strict"', "'use strict'", '"use client"', "'use client'", '"use server"', "'use server'"}


def _agentmap_collect_line_comment_description(
    lines: list[str], start: int, prefixes: tuple[str, ...]
) -> tuple[Optional[str], int]:
    comment_lines = []
    idx = start
    while idx < len(lines):
        current = lines[idx].strip()
        if not current.startswith(prefixes):
            break
        comment_lines.append(lines[idx])
        idx += 1

    normalized_lines = []
    for raw in comment_lines:
        stripped = raw.strip()
        if _agentmap_is_reference_directive(stripped):
            continue
        normalized = _agentmap_normalize_comment_lines([raw])
        if not normalized:
            continue
        normalized_lines.append(normalized)

    while normalized_lines and _agentmap_is_license_comment(normalized_lines[0]):
        normalized_lines.pop(0)

    if not normalized_lines:
        return None, idx
    return " ".join(normalized_lines[:AGENTMAP_MAX_DESCRIPTION_LINES]), idx


def _agentmap_extract_header_description(path: Path, text: str) -> Optional[str]:
    lines = text.splitlines()[:AGENTMAP_MAX_HEADER_LINES]
    idx = 0
    shebang: Optional[str] = None
    if lines and lines[0].startswith("#!"):
        shebang = lines[0].strip()
        idx += 1
    suffix = path.suffix.lower()

    def with_shebang(description: Optional[str]) -> Optional[str]:
        if shebang and description:
            return f"{shebang}\n{description}"
        if shebang:
            return shebang
        return description

    if suffix in {".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs"}:
        while idx < len(lines) and _agentmap_is_js_directive(lines[idx]):
            idx += 1
    while idx < len(lines):
        while idx < len(lines) and not lines[idx].strip():
            idx += 1
        if idx >= len(lines):
            return with_shebang(None)

        line = lines[idx].strip()
        description: Optional[str] = None
        next_idx = idx + 1

        if suffix in {".py", ".pyi"}:
            if line.startswith('"""') or line.startswith("'''"):
                quote = line[:3]
                description, next_idx = _agentmap_extract_block_comment(lines, idx, quote, quote)
            elif line.startswith("#"):
                description, next_idx = _agentmap_collect_line_comment_description(lines, idx, ("#",))
        elif line.startswith("/**") or line.startswith("/*"):
            opener = "/**" if line.startswith("/**") else "/*"
            description, next_idx = _agentmap_extract_block_comment(lines, idx, opener, "*/")
        elif suffix == ".rs" and (line.startswith("//!") or line.startswith("///") or line.startswith("//")):
            description, next_idx = _agentmap_collect_line_comment_description(
                lines, idx, ("//!", "///", "//")
            )
        elif line.startswith("//"):
            description, next_idx = _agentmap_collect_line_comment_description(lines, idx, ("///", "//"))

        if not description:
            idx = next_idx
            continue
        if not _agentmap_is_license_comment(description):
            return with_shebang(description)
        idx = next_idx

    return with_shebang(None)


def _agentmap_extract_markdown_description(text: str) -> Optional[str]:
    lines = text.splitlines()[:AGENTMAP_MAX_HEADER_LINES]
    filtered = []
    in_comment = False
    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith("<!--"):
            in_comment = True
        if in_comment:
            if "-->" in stripped:
                in_comment = False
            continue
        if stripped.startswith("!["):
            continue
        stripped = re.sub(r"^#{1,6}\s*", "", stripped)
        stripped = re.sub(r"^[-*+]\s+", "- ", stripped)
        filtered.append(stripped)
    if not filtered:
        return None
    return "\n".join(_agentmap_truncate_lines(filtered))


def _agentmap_format_def(line_no: int, kind: str, exported: bool = False) -> str:
    parts = [f"line {line_no}", kind]
    if exported:
        parts.append("exported")
    return ", ".join(parts)


def _agentmap_extract_defs(path: Path, text: str) -> dict[str, str]:
    suffix = path.suffix.lower()
    defs: dict[str, str] = {}
    lines = text.splitlines()

    if suffix in {".py", ".pyi"}:
        patterns = [
            (re.compile(r"^class\s+([A-Za-z_]\w*)\b"), "class"),
            (re.compile(r"^(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\("), "function"),
        ]
        for idx, line in enumerate(lines, start=1):
            if line.startswith((" ", "\t")):
                continue
            stripped = line.strip()
            for pattern, kind in patterns:
                match = pattern.match(stripped)
                if match:
                    defs[match.group(1)] = _agentmap_format_def(idx, kind)
                    break
        return defs

    if suffix in {".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs"}:
        patterns = [
            (re.compile(r"^(export\s+)?(?:default\s+)?class\s+([A-Za-z_$][\w$]*)\b"), "class"),
            (re.compile(r"^(export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\("), "function"),
            (re.compile(r"^(export\s+)?interface\s+([A-Za-z_$][\w$]*)\b"), "interface"),
            (re.compile(r"^(export\s+)?type\s+([A-Za-z_$][\w$]*)\b"), "type"),
            (re.compile(r"^(export\s+)?enum\s+([A-Za-z_$][\w$]*)\b"), "enum"),
            (re.compile(r"^(export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>"), "function"),
        ]
        depth = 0
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if depth == 0:
                for pattern, kind in patterns:
                    match = pattern.match(stripped)
                    if match:
                        exported = bool(match.group(1))
                        defs[match.group(2)] = _agentmap_format_def(idx, kind, exported)
                        break
            depth += line.count("{") - line.count("}")
            if depth < 0:
                depth = 0
        return defs

    if suffix == ".rs":
        patterns = [
            (re.compile(r"^(pub\s+)?(?:async\s+)?fn\s+([A-Za-z_]\w*)\s*\("), "function"),
            (re.compile(r"^(pub\s+)?struct\s+([A-Za-z_]\w*)\b"), "struct"),
            (re.compile(r"^(pub\s+)?enum\s+([A-Za-z_]\w*)\b"), "enum"),
            (re.compile(r"^(pub\s+)?trait\s+([A-Za-z_]\w*)\b"), "trait"),
            (re.compile(r"^(pub\s+)?type\s+([A-Za-z_]\w*)\b"), "type"),
        ]
        depth = 0
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if depth == 0:
                for pattern, kind in patterns:
                    match = pattern.match(stripped)
                    if match:
                        defs[match.group(2)] = _agentmap_format_def(idx, kind, bool(match.group(1)))
                        break
            depth += line.count("{") - line.count("}")
            if depth < 0:
                depth = 0
        return defs

    if suffix == ".go":
        patterns = [
            (re.compile(r"^func\s+(?:\([^)]+\)\s*)?([A-Za-z_]\w*)\s*\("), "function"),
            (re.compile(r"^type\s+([A-Za-z_]\w*)\s+struct\b"), "struct"),
            (re.compile(r"^type\s+([A-Za-z_]\w*)\s+interface\b"), "interface"),
        ]
        depth = 0
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if depth == 0:
                for pattern, kind in patterns:
                    match = pattern.match(stripped)
                    if match:
                        name = match.group(1)
                        defs[name] = _agentmap_format_def(idx, kind, name[:1].isupper())
                        break
            depth += line.count("{") - line.count("}")
            if depth < 0:
                depth = 0
        return defs

    return defs


def _agentmap_insert(tree: dict[str, Any], parts: list[str], payload: dict[str, Any]) -> None:
    node = tree
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    node[parts[-1]] = payload


def _agentmap_render_yaml(node: Any, indent: int = 0) -> list[str]:
    if not isinstance(node, dict):
        return [" " * indent + json.dumps(node, ensure_ascii=False)]

    lines = []
    for key in sorted(node.keys()):
        value = node[key]
        prefix = " " * indent + f"{json.dumps(str(key), ensure_ascii=False)}:"
        if isinstance(value, dict):
            if value:
                lines.append(prefix)
                lines.extend(_agentmap_render_yaml(value, indent + 2))
            else:
                lines.append(prefix + " {}")
        else:
            lines.append(prefix + f" {json.dumps(value, ensure_ascii=False)}")
    return lines


def _generate_agentmap_yaml(target_dir: Path, filters: list[str], ignores: list[str]) -> tuple[str, int]:
    tree: dict[str, Any] = {target_dir.name: {}}
    count = 0
    if target_dir.resolve() == Path.home().resolve():
        return "\n".join(_agentmap_render_yaml(tree)) + "\n", 0

    try:
        subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=target_dir,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return "\n".join(_agentmap_render_yaml(tree)) + "\n", 0

    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=target_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        tracked_files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except subprocess.CalledProcessError:
        tracked_files = []

    for rel_path in sorted(tracked_files):
        path = (target_dir / rel_path).resolve()
        if not path.is_file():
            continue
        if not _agentmap_supported(path) and not _agentmap_is_readme(path):
            continue
        if not _agentmap_matches(rel_path, filters, ignores):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
        except OSError:
            continue

        description = (
            _agentmap_extract_markdown_description(text)
            if _agentmap_is_readme(path)
            else _agentmap_extract_header_description(path, text)
        )
        if not description:
            continue

        payload: dict[str, Any] = {"description": description}
        defs = _agentmap_extract_defs(path, text)
        if defs:
            payload["defs"] = defs
        _agentmap_insert(tree[target_dir.name], rel_path.split("/"), payload)
        count += 1

    return "\n".join(_agentmap_render_yaml(tree)) + "\n", count


def cmd_agentmap(args: argparse.Namespace) -> None:
    """Generate or inspect a built-in agentmap artifact."""

    if args.check:
        payload = {
            "available": True,
            "engine": "built-in",
            "path": None,
            "version": current_flux_version(),
        }
        if args.json:
            json_output(payload)
        else:
            version = payload["version"] or "unknown version"
            print(f"agentmap built into fluxctl ({version})")
        return

    if args.write and args.out:
        error_exit("--write and --out cannot be used together", use_json=args.json)

    target_dir = Path(args.dir).resolve()
    if not target_dir.exists():
        error_exit(f"Directory not found: {target_dir}", use_json=args.json)
    if not target_dir.is_dir():
        error_exit(f"Not a directory: {target_dir}", use_json=args.json)

    output_path: Optional[Path] = None
    if args.write:
        output_path = get_flux_dir() / "context" / "agentmap.yaml"
    elif args.out:
        output_path = Path(args.out).expanduser()
        if not output_path.is_absolute():
            output_path = (Path.cwd() / output_path).resolve()

    yaml_text, file_count = _generate_agentmap_yaml(target_dir, args.filter, args.ignore)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(output_path, yaml_text)

    if args.json:
        payload = {
            "available": True,
            "engine": "built-in",
            "path": None,
            "dir": str(target_dir),
            "output_file": str(output_path) if output_path else None,
            "filters": args.filter,
            "ignores": args.ignore,
            "file_count": file_count,
        }
        if output_path is None:
            payload["yaml"] = yaml_text.rstrip()
        json_output(payload)
    else:
        if output_path is not None:
            print(output_path)
        else:
            print(yaml_text.rstrip())


# ---------------------------------------------------------------------------
# cmd_migrate_state
# ---------------------------------------------------------------------------

def cmd_migrate_state(args: argparse.Namespace) -> None:
    """Migrate runtime state from definition files to state-dir."""
    if not ensure_flux_exists():
        error_exit(
            ".flux/ does not exist. Run 'fluxctl init' first.", use_json=args.json
        )

    flux_dir = get_flux_dir()
    tasks_dir = flux_dir / TASKS_DIR
    store = get_state_store()

    migrated = []
    skipped = []

    if not tasks_dir.exists():
        if args.json:
            json_output({"migrated": [], "skipped": [], "message": "No tasks directory"})
        else:
            print("No tasks directory found.")
        return

    for task_file in tasks_dir.glob("fn-*.json"):
        task_id = task_file.stem
        if not is_task_id(task_id):
            continue  # Skip non-task files (e.g., fn-1.2-review.json)

        # Check if state file already exists
        if store.load_runtime(task_id) is not None:
            skipped.append(task_id)
            continue

        # Load definition and extract runtime fields
        try:
            definition = load_json(task_file)
        except Exception:
            skipped.append(task_id)
            continue

        runtime = {k: definition[k] for k in RUNTIME_FIELDS if k in definition}
        if not runtime or runtime.get("status") == "todo":
            # No runtime state to migrate
            skipped.append(task_id)
            continue

        # Write runtime state
        store.save_runtime(task_id, runtime)
        migrated.append(task_id)

        # Optionally clean definition file (only with --clean flag)
        if args.clean:
            clean_def = {k: v for k, v in definition.items() if k not in RUNTIME_FIELDS}
            atomic_write_json(task_file, clean_def)

    if args.json:
        json_output({
            "migrated": migrated,
            "skipped": skipped,
            "cleaned": args.clean,
        })
    else:
        print(f"Migrated: {len(migrated)} tasks")
        if migrated:
            for t in migrated:
                print(f"  {t}")
        print(f"Skipped: {len(skipped)} tasks (already migrated or no state)")
        if args.clean:
            print("Definition files cleaned (runtime fields removed)")
