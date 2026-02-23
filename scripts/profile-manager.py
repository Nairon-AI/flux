#!/usr/bin/env python3
"""N-bench profile manager for export/import/view workflows."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - optional dependency fallback
    yaml = None


SCRIPT_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = Path(
    os.environ.get("CLAUDE_PLUGIN_ROOT")
    or os.environ.get("DROID_PLUGIN_ROOT")
    or SCRIPT_DIR.parent
)
HOME = Path.home()
DEFAULT_STATE_PATH = HOME / ".nbench" / "profile-state.json"
DEFAULT_CONFIG_PATH = HOME / ".nbench" / "config.json"
DEFAULT_RECS_DIR = Path(
    os.environ.get("NBENCH_RECS_DIR") or HOME / ".nbench" / "recommendations"
)

ALL_OSES = ["macos", "linux", "windows"]
SENSITIVE_KEY_RE = re.compile(
    r"(token|secret|password|api[_-]?key|pat|authorization)", re.IGNORECASE
)
SENSITIVE_VALUE_PATTERNS = [
    re.compile(r"\b(sk-[A-Za-z0-9]{12,})\b"),
    re.compile(r"\b(ghp_[A-Za-z0-9]{20,})\b"),
    re.compile(r"\b(xox[baprs]-[A-Za-z0-9-]{10,})\b"),
    re.compile(r"\b[A-Za-z0-9_\-]{30,}\b"),
]


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_os(raw: str | None) -> str:
    value = (raw or "").strip().lower()
    if value in {"darwin", "mac", "macos", "osx"}:
        return "macos"
    if value in {"linux"}:
        return "linux"
    if value in {"windows", "win32", "cygwin", "msys"}:
        return "windows"
    system_name = platform.system().lower()
    if system_name == "darwin":
        return "macos"
    if system_name == "windows":
        return "windows"
    return "linux"


def default_state() -> dict[str, Any]:
    return {
        "schema_version": "1",
        "saved_applications": {},
        "published_profiles": {},
        "last_exported_at": "",
    }


def parse_json_file(path: Path) -> Any:
    with open(path) as f:
        return json.load(f)


def load_json_file(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return copy.deepcopy(fallback)
    try:
        data = parse_json_file(path)
    except (OSError, json.JSONDecodeError):
        return copy.deepcopy(fallback)
    return data


def write_json_file(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)


def load_state(path: Path) -> dict[str, Any]:
    data = load_json_file(path, default_state())
    if not isinstance(data, dict):
        return default_state()

    state = default_state()
    state.update({k: v for k, v in data.items() if k in state})

    if not isinstance(state.get("saved_applications"), dict):
        state["saved_applications"] = {}
    if not isinstance(state.get("published_profiles"), dict):
        state["published_profiles"] = {}
    if not isinstance(state.get("last_exported_at"), str):
        state["last_exported_at"] = ""
    return state


def load_config(path: Path) -> dict[str, Any]:
    data = load_json_file(path, {})
    return data if isinstance(data, dict) else {}


def parse_csv(value: str) -> list[str]:
    if not value:
        return []
    out = []
    seen = set()
    for part in value.split(","):
        token = part.strip()
        if not token:
            continue
        lowered = token.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        out.append(token)
    return out


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9._-]+", "-", value.lower()).strip("-")


def item_id(category: str, name: str, fingerprint: str = "") -> str:
    base = f"{category}:{slugify(name)}"
    if category == "skill" and fingerprint:
        return f"{base}:{fingerprint[:8]}"
    return base


def redact_text(value: str) -> str:
    output = value
    output = re.sub(
        r'(?i)("?(?:token|secret|password|api[_-]?key|pat|authorization)"?\s*[:=]\s*")([^"]+)(")',
        r"\1<redacted>\3",
        output,
    )
    output = re.sub(
        r"(?i)(token|secret|password|api[_-]?key|pat|authorization)\s*[:=]\s*([^\s,;]+)",
        r"\1=<redacted>",
        output,
    )

    for pattern in SENSITIVE_VALUE_PATTERNS:
        output = pattern.sub("<redacted>", output)
    return output


def redact_value(value: Any, parent_key: str = "") -> Any:
    if isinstance(value, dict):
        redacted = {}
        for key, inner in value.items():
            if SENSITIVE_KEY_RE.search(str(key)):
                redacted[key] = "<redacted>"
            else:
                redacted[key] = redact_value(inner, str(key))
        return redacted

    if isinstance(value, list):
        return [redact_value(item, parent_key) for item in value]

    if isinstance(value, str):
        if SENSITIVE_KEY_RE.search(parent_key):
            return "<redacted>"
        return redact_text(value)

    return value


def simple_yaml_parse(content: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    current_list: list[Any] | None = None
    multiline_key: str | None = None
    multiline_value: list[str] = []
    indent_stack = [0]
    nested_key: str | None = None
    nested_dict: dict[str, Any] = {}

    lines = content.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            if multiline_key:
                multiline_value.append("")
            i += 1
            continue

        if multiline_key:
            indent = len(line) - len(line.lstrip())
            if indent > indent_stack[-1] or stripped == "":
                multiline_value.append(stripped)
                i += 1
                continue
            result[multiline_key] = "\n".join(multiline_value).strip()
            multiline_key = None
            multiline_value = []

        if nested_key:
            indent = len(line) - len(line.lstrip())
            if indent > 0 and ":" in stripped:
                parts = stripped.split(":", 1)
                key = parts[0].strip()
                value = parts[1].strip().strip("\"'") if len(parts) > 1 else ""
                nested_dict[key] = value
                i += 1
                continue
            result[nested_key] = nested_dict
            nested_key = None
            nested_dict = {}

        if ":" in stripped:
            if stripped.startswith("- "):
                if current_list is not None:
                    item_content = stripped[2:]
                    if ":" not in item_content:
                        current_list.append(item_content.strip())
                i += 1
                continue

            parts = stripped.split(":", 1)
            key = parts[0].strip()
            value = parts[1].strip() if len(parts) > 1 else ""

            if value == "|":
                multiline_key = key
                multiline_value = []
                indent_stack.append(len(line) - len(line.lstrip()))
                i += 1
                continue

            if value == "":
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line.startswith("- "):
                        result[key] = []
                        current_list = result[key]
                    else:
                        nested_key = key
                        nested_dict = {}
            elif value.startswith("[") and value.endswith("]"):
                items = value[1:-1].split(",")
                result[key] = [
                    item.strip().strip("\"'") for item in items if item.strip()
                ]
            elif value.startswith("{"):
                result[key] = {}
            else:
                parsed_value: Any = value.strip("\"'")
                if value.lower() == "true":
                    parsed_value = True
                elif value.lower() == "false":
                    parsed_value = False
                elif value.isdigit():
                    parsed_value = int(value)
                result[key] = parsed_value
        elif stripped.startswith("- "):
            item = stripped[2:].strip().strip("\"'")
            if current_list is not None:
                current_list.append(item)

        i += 1

    if multiline_key:
        result[multiline_key] = "\n".join(multiline_value).strip()
    if nested_key:
        result[nested_key] = nested_dict
    return result


def load_recommendations(recs_dir: Path) -> dict[str, dict[str, Any]]:
    catalog: dict[str, dict[str, Any]] = {}
    if not recs_dir.exists():
        return catalog

    for yaml_path in recs_dir.rglob("*.yaml"):
        if yaml_path.name in {"schema.yaml", "accounts.yaml"}:
            continue
        if "pending" in yaml_path.parts:
            continue
        try:
            content = yaml_path.read_text()
        except OSError:
            continue

        try:
            if yaml is not None:
                loaded = yaml.safe_load(content)
                rec = loaded if isinstance(loaded, dict) else {}
            else:
                rec = simple_yaml_parse(content)
        except Exception:
            rec = simple_yaml_parse(content)

        if not isinstance(rec, dict):
            continue
        name = str(rec.get("name", "")).strip().lower()
        if not name:
            continue
        rec["_file"] = str(yaml_path)
        catalog[name] = rec
    return catalog


def run_json_script(script_name: str, cwd: Path) -> dict[str, Any]:
    script_path = PLUGIN_ROOT / "scripts" / script_name
    proc = subprocess.run(
        [str(script_path)],
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )
    output = proc.stdout.strip() or proc.stderr.strip()
    if proc.returncode != 0:
        raise RuntimeError(f"{script_name} failed: {output}")

    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{script_name} returned invalid JSON: {output}") from exc


def read_detect_payload(cwd: Path, detect_json_file: str = "") -> dict[str, Any]:
    if detect_json_file:
        data = parse_json_file(Path(detect_json_file))
        return data if isinstance(data, dict) else {}
    return run_json_script("detect-installed.sh", cwd)


def read_repo_payload(cwd: Path, repo_json_file: str = "") -> dict[str, Any]:
    if repo_json_file:
        data = parse_json_file(Path(repo_json_file))
        return data if isinstance(data, dict) else {}
    return run_json_script("analyze-context.sh", cwd)


def infer_os_support(rec: dict[str, Any], category: str, source_os: str) -> list[str]:
    prereqs = rec.get("prerequisites", [])
    if not isinstance(prereqs, list):
        prereqs = []
    blob = " ".join([str(item).lower() for item in prereqs])

    supported: list[str] = []
    if "mac" in blob:
        supported.append("macos")
    if "linux" in blob:
        supported.append("linux")
    if "windows" in blob:
        supported.append("windows")

    if supported:
        return sorted(set(supported))
    if category == "application":
        return [source_os]
    return list(ALL_OSES)


def normalize_install_data(rec: dict[str, Any]) -> dict[str, Any]:
    install = rec.get("install", {})
    if not isinstance(install, dict):
        install = {}

    install_type = str(install.get("type", "manual"))
    command = str(install.get("command", "")).strip()
    config_snippet = install.get("config_snippet")

    if isinstance(config_snippet, str):
        snippet = config_snippet.strip()
        if snippet:
            try:
                config_snippet = json.loads(snippet)
            except json.JSONDecodeError:
                config_snippet = snippet

    out: dict[str, Any] = {"type": install_type, "command": command}
    if config_snippet:
        out["config_snippet"] = config_snippet

    if "source" in install:
        out["source"] = str(install.get("source", ""))
    if "scope" in install:
        out["scope"] = str(install.get("scope", "user"))
    if "repo" in install:
        out["repo"] = str(install.get("repo", ""))
    return out


def normalize_verification(rec: dict[str, Any]) -> dict[str, Any]:
    verification = rec.get("verification", {})
    if not isinstance(verification, dict):
        verification = {}

    verify_type = str(verification.get("type", "manual"))
    test_command = str(verification.get("test_command", "")).strip()
    success_indicator = str(verification.get("success_indicator", "")).strip()

    out: dict[str, Any] = {"type": verify_type}
    if test_command:
        out["test_command"] = test_command
    if success_indicator:
        out["success_indicator"] = success_indicator
    return out


def manual_item(
    name: str, category: str, source_os: str, note: str = ""
) -> dict[str, Any]:
    item = {
        "id": item_id(category, name),
        "name": name,
        "category": category,
        "sdlc_phase": "implementation",
        "install": {
            "type": "manual",
            "command": "",
            "instructions": note or "Manual setup required",
        },
        "verification": {"type": "manual", "test_command": "Verify manually"},
        "tags": [],
        "source": "detected",
        "source_url": "",
        "pricing": {},
        "os_support": [source_os] if category == "application" else list(ALL_OSES),
        "manual_only": True,
        "priority": "optional",
    }
    return item


def build_item_from_recommendation(
    name: str,
    category: str,
    source_os: str,
    rec: dict[str, Any] | None,
    mcp_config: dict[str, Any] | None = None,
    skill_hash: str = "",
) -> dict[str, Any]:
    if rec is None:
        return manual_item(name, category, source_os)

    install = normalize_install_data(rec)
    verification = normalize_verification(rec)

    if category == "mcp" and mcp_config is not None:
        install = {"type": "mcp", "command": "", "config_snippet": mcp_config}
        verification = {"type": "mcp_connect", "test_command": f"Use MCP: {name}"}

    if (
        category == "skill"
        and not install.get("command")
        and install.get("type") == "manual"
    ):
        install["instructions"] = (
            "Share this skill package separately or install manually"
        )

    raw_tags = rec.get("tags", [])
    tags = raw_tags if isinstance(raw_tags, list) else []
    pricing = rec.get("pricing", {}) if isinstance(rec.get("pricing"), dict) else {}

    item = {
        "id": item_id(category, name, skill_hash),
        "name": name,
        "category": category,
        "sdlc_phase": str(rec.get("sdlc_phase", "implementation")),
        "install": redact_value(install),
        "verification": verification,
        "tags": [str(tag) for tag in tags],
        "source": str(rec.get("source", "manual")),
        "source_url": str(rec.get("source_url", "")),
        "pricing": pricing,
        "os_support": infer_os_support(rec, category, source_os),
        "manual_only": bool(
            category == "application" or install.get("type") == "manual"
        ),
        "priority": "optional",
    }
    return item


def extract_mcp_servers(json_path: Path) -> dict[str, Any]:
    payload = load_json_file(json_path, {})
    if not isinstance(payload, dict):
        return {}
    servers = payload.get("mcpServers", {})
    if not isinstance(servers, dict):
        return {}
    out = {}
    for name, config in servers.items():
        out[str(name).lower()] = config
    return out


def detect_mcp_configs(cwd: Path, warnings: list[str]) -> dict[str, dict[str, Any]]:
    files: list[tuple[str, Path]] = [
        ("project", cwd / ".mcp.json"),
        ("global", HOME / ".mcp.json"),
        ("claude-settings", HOME / ".claude" / "settings.json"),
    ]

    merged: dict[str, dict[str, Any]] = {}
    for source, path in files:
        if not path.exists():
            continue
        try:
            servers = extract_mcp_servers(path)
        except Exception:
            warnings.append(f"Malformed MCP config ignored: {source} ({path})")
            continue

        for name, config in servers.items():
            if name in merged:
                continue
            if isinstance(config, dict):
                merged[name] = config
    return merged


def hash_skill_folder(path: Path) -> str:
    digest = hashlib.sha256()
    files = [p for p in sorted(path.rglob("*")) if p.is_file()]
    if not files:
        digest.update(path.name.encode())
    for file_path in files:
        digest.update(file_path.name.encode())
        try:
            digest.update(file_path.read_bytes())
        except OSError:
            continue
    return digest.hexdigest()


def detect_skills(scope: str, cwd: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    roots: list[tuple[str, Path]] = []

    if scope in {"global", "both"}:
        roots.append(("global", HOME / ".claude" / "skills"))
    if scope in {"project", "both"}:
        roots.append(("project", cwd / ".claude" / "skills"))

    for skill_scope, root in roots:
        if not root.exists():
            continue
        for child in sorted(root.iterdir()):
            if not child.is_dir():
                continue
            skill_name = child.name
            fingerprint = hash_skill_folder(child)
            entries.append(
                {
                    "name": skill_name,
                    "hash": fingerprint,
                    "scopes": [skill_scope],
                }
            )

    deduped: dict[str, dict[str, Any]] = {}
    for entry in entries:
        key = f"{entry['name'].lower()}::{entry['hash']}"
        if key not in deduped:
            deduped[key] = entry
            continue
        existing_scopes = set(deduped[key].get("scopes", []))
        for scope_name in entry.get("scopes", []):
            existing_scopes.add(scope_name)
        deduped[key]["scopes"] = sorted(existing_scopes)

    return sorted(deduped.values(), key=lambda x: (x["name"].lower(), x["hash"]))


def detect_workflow_patterns(
    repo_payload: dict[str, Any], detected_payload: dict[str, Any]
) -> list[str]:
    repo = repo_payload.get("repo", {})
    if not isinstance(repo, dict):
        repo = {}

    detected = detected_payload.get("installed", {})
    if not isinstance(detected, dict):
        detected = {}

    cli_tools = [str(item).lower() for item in (detected.get("cli_tools") or [])]
    patterns: list[str] = []

    if bool(repo.get("has_hooks")):
        patterns.append("pre-commit-hooks")
    if bool(repo.get("has_tests")):
        patterns.append("test-first-debugging")
    if bool(repo.get("has_agent_docs")):
        patterns.append("agents-md-structure")
    if "beads" in cli_tools:
        patterns.append("context-management")

    unique = []
    seen = set()
    for pattern_name in patterns:
        lowered = pattern_name.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique.append(pattern_name)
    return unique


def detect_model_preferences() -> list[dict[str, Any]]:
    settings_path = HOME / ".claude" / "settings.json"
    if not settings_path.exists():
        return []

    payload = load_json_file(settings_path, {})
    if not isinstance(payload, dict):
        return []

    preferences: list[dict[str, Any]] = []

    default_model = payload.get("defaultModel") or payload.get("model")
    if isinstance(default_model, str) and default_model.strip():
        preferences.append(
            {
                "name": f"default-model:{default_model.strip()}",
                "value": default_model.strip(),
            }
        )

    models = payload.get("models")
    if isinstance(models, list):
        for model in models:
            if not isinstance(model, str):
                continue
            cleaned = model.strip()
            if not cleaned:
                continue
            preferences.append({"name": f"model:{cleaned}", "value": cleaned})

    unique: dict[str, dict[str, Any]] = {}
    for pref in preferences:
        unique[pref["name"].lower()] = pref
    return sorted(unique.values(), key=lambda x: x["name"])


def compute_application_selection(
    detected_apps: list[str], state: dict[str, Any]
) -> dict[str, list[str]]:
    saved_map = state.get("saved_applications", {})
    saved_names = sorted([name for name in saved_map.keys() if isinstance(name, str)])

    detected_set = {name.lower(): name for name in detected_apps}
    saved_set = {name.lower(): name for name in saved_names}

    saved_installed = sorted(
        [name for key, name in detected_set.items() if key in saved_set]
    )
    new_candidates = sorted(
        [name for key, name in detected_set.items() if key not in saved_set]
    )
    saved_missing = sorted(
        [name for key, name in saved_set.items() if key not in detected_set]
    )

    return {
        "saved_installed": saved_installed,
        "saved_missing": saved_missing,
        "new_candidates": new_candidates,
    }


def update_saved_app_state(
    state: dict[str, Any],
    detected_apps: list[str],
    selected_apps: list[str],
    required_apps: set[str],
) -> None:
    saved = state.setdefault("saved_applications", {})
    now = now_iso()

    detected_lookup = {name.lower(): name for name in detected_apps}
    selected_lookup = {name.lower(): name for name in selected_apps}

    for lower_name, original in detected_lookup.items():
        entry = (
            saved.get(original)
            or saved.get(lower_name)
            or {
                "first_saved_at": now,
                "last_selected_at": "",
                "last_seen_state": "installed",
                "priority": "optional",
            }
        )

        entry["last_seen_state"] = "installed"
        if lower_name in selected_lookup:
            entry["last_selected_at"] = now
            if not entry.get("first_saved_at"):
                entry["first_saved_at"] = now
        if lower_name in required_apps:
            entry["priority"] = "required"
        elif entry.get("priority") not in {"required", "optional"}:
            entry["priority"] = "optional"

        saved[original] = entry

    current_detected = set(detected_lookup.keys())
    for app_name, entry in list(saved.items()):
        if not isinstance(entry, dict):
            saved[app_name] = {
                "first_saved_at": now,
                "last_selected_at": "",
                "last_seen_state": "missing",
                "priority": "optional",
            }
            continue

        if app_name.lower() not in current_detected:
            entry["last_seen_state"] = "missing"
            if entry.get("priority") not in {"required", "optional"}:
                entry["priority"] = "optional"


def merge_detected_context(
    cwd: Path,
    skills_scope: str,
    recs_dir: Path,
    state_path: Path,
    detect_json_file: str = "",
    repo_json_file: str = "",
) -> dict[str, Any]:
    warnings: list[str] = []
    detected_payload = read_detect_payload(cwd, detect_json_file)
    repo_payload = read_repo_payload(cwd, repo_json_file)
    state = load_state(state_path)
    recommendations = load_recommendations(recs_dir)

    detected = detected_payload.get("installed", {})
    if not isinstance(detected, dict):
        detected = {}

    source_os = normalize_os(str(detected_payload.get("os") or ""))
    mcp_configs = detect_mcp_configs(cwd, warnings)
    skills = detect_skills(skills_scope, cwd)
    workflow_patterns = detect_workflow_patterns(repo_payload, detected_payload)
    model_preferences = detect_model_preferences()

    def rec_for(name: str) -> dict[str, Any] | None:
        return recommendations.get(name.lower())

    catalog: dict[str, list[dict[str, Any]]] = {
        "mcps": [],
        "cli_tools": [],
        "skills": [],
        "applications": [],
        "plugins": [],
        "workflow_patterns": [],
        "model_preferences": [],
    }

    for name in sorted([str(item) for item in (detected.get("mcps") or [])]):
        mcp_conf = mcp_configs.get(name.lower())
        item = build_item_from_recommendation(
            name, "mcp", source_os, rec_for(name), mcp_conf
        )
        catalog["mcps"].append(item)

    for name in sorted([str(item) for item in (detected.get("cli_tools") or [])]):
        item = build_item_from_recommendation(
            name, "cli-tool", source_os, rec_for(name)
        )
        catalog["cli_tools"].append(item)

    for name in sorted([str(item) for item in (detected.get("applications") or [])]):
        item = build_item_from_recommendation(
            name, "application", source_os, rec_for(name)
        )
        catalog["applications"].append(item)

    for name in sorted([str(item) for item in (detected.get("plugins") or [])]):
        item = build_item_from_recommendation(name, "plugin", source_os, rec_for(name))
        catalog["plugins"].append(item)

    for skill in skills:
        skill_name = str(skill.get("name", ""))
        skill_hash = str(skill.get("hash", ""))
        rec = rec_for(skill_name)
        item = build_item_from_recommendation(
            skill_name,
            "skill",
            source_os,
            rec,
            None,
            skill_hash,
        )
        item["skill_hash"] = skill_hash
        item["skill_scopes"] = skill.get("scopes", [])
        if rec is None:
            item["manual_only"] = True
            item["install"] = {
                "type": "manual",
                "command": "",
                "instructions": "Custom skill detected. Share/install the skill directory manually.",
            }
        catalog["skills"].append(item)

    for pattern_name in workflow_patterns:
        rec = rec_for(pattern_name)
        if rec is None:
            item = manual_item(
                pattern_name,
                "workflow-pattern",
                source_os,
                "Document and apply manually",
            )
        else:
            item = build_item_from_recommendation(
                pattern_name, "workflow-pattern", source_os, rec
            )
            item["manual_only"] = True
        catalog["workflow_patterns"].append(item)

    for model_pref in model_preferences:
        model_name = model_pref["name"]
        item = manual_item(
            model_name, "model-preference", source_os, "Set model preference manually"
        )
        item["value"] = model_pref["value"]
        catalog["model_preferences"].append(item)

    app_selection = compute_application_selection(
        [str(item) for item in (detected.get("applications") or [])],
        state,
    )

    installed_index = {
        "mcp": [item["name"].lower() for item in catalog["mcps"]],
        "cli-tool": [item["name"].lower() for item in catalog["cli_tools"]],
        "application": [item["name"].lower() for item in catalog["applications"]],
        "plugin": [item["name"].lower() for item in catalog["plugins"]],
        "skill": [item["name"].lower() for item in catalog["skills"]],
        "workflow-pattern": [
            item["name"].lower() for item in catalog["workflow_patterns"]
        ],
        "model-preference": [
            item["name"].lower() for item in catalog["model_preferences"]
        ],
    }

    return {
        "os": source_os,
        "skills_scope": skills_scope,
        "catalog": catalog,
        "application_selection": app_selection,
        "installed_index": installed_index,
        "warnings": warnings,
    }


def build_profile_snapshot(
    merged: dict[str, Any],
    selected_new_apps: list[str],
    include_saved_apps: bool,
    include_saved_missing_apps: list[str],
    required_items: list[str],
    profile_name: str,
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    warnings: list[str] = []
    app_selection = merged.get("application_selection", {})

    saved_installed = [str(v) for v in app_selection.get("saved_installed", [])]
    saved_missing = [str(v) for v in app_selection.get("saved_missing", [])]
    new_candidates = [str(v) for v in app_selection.get("new_candidates", [])]

    normalized_new = {name.lower(): name for name in new_candidates}
    normalized_saved_missing = {name.lower(): name for name in saved_missing}

    include_apps: dict[str, str] = {}
    if include_saved_apps:
        for app in saved_installed:
            include_apps[app.lower()] = app

    for app in selected_new_apps:
        lower = app.lower()
        if lower not in normalized_new:
            warnings.append(f"Ignored unknown new app selection: {app}")
            continue
        include_apps[lower] = normalized_new[lower]

    for app in include_saved_missing_apps:
        lower = app.lower()
        if lower not in normalized_saved_missing:
            warnings.append(f"Ignored unknown saved-missing app selection: {app}")
            continue
        include_apps[lower] = normalized_saved_missing[lower]

    required_tokens = {token.lower() for token in required_items}

    categories_in_order = [
        ("mcps", "mcp"),
        ("cli_tools", "cli-tool"),
        ("skills", "skill"),
        ("applications", "application"),
        ("plugins", "plugin"),
        ("workflow_patterns", "workflow-pattern"),
        ("model_preferences", "model-preference"),
    ]

    selected_items: list[dict[str, Any]] = []
    catalog = merged.get("catalog", {})
    for key, category in categories_in_order:
        items = catalog.get(key, []) if isinstance(catalog, dict) else []
        if not isinstance(items, list):
            continue

        for item in items:
            if not isinstance(item, dict):
                continue
            if (
                category == "application"
                and item.get("name", "").lower() not in include_apps
            ):
                continue

            copy_item = copy.deepcopy(item)
            token_name = str(copy_item.get("name", "")).lower()
            token_id = str(copy_item.get("id", "")).lower()
            copy_item["priority"] = (
                "required"
                if token_name in required_tokens or token_id in required_tokens
                else "optional"
            )
            copy_item["install"] = redact_value(copy_item.get("install", {}))
            selected_items.append(copy_item)

    counts: dict[str, Any] = {
        "total": len(selected_items),
        "required": len(
            [item for item in selected_items if item.get("priority") == "required"]
        ),
        "optional": len(
            [item for item in selected_items if item.get("priority") != "required"]
        ),
    }

    by_category: dict[str, int] = {}
    for item in selected_items:
        cat = str(item.get("category", "unknown"))
        by_category[cat] = by_category.get(cat, 0) + 1
    counts["by_category"] = by_category

    snapshot = {
        "schema_version": "1.0",
        "profile_kind": "nbench-sdlc-profile",
        "profile_name": profile_name or "N-bench SDLC Profile",
        "created_at": now_iso(),
        "visibility": "public-anonymous",
        "link_policy": {
            "immutable": True,
            "non_expiring": True,
            "tombstone_supported": True,
        },
        "metadata": {
            "os": normalize_os(str(merged.get("os") or "")),
        },
        "policies": {
            "secret_redaction": "auto",
            "import_confirmation": "per-item",
            "already_installed_default": "skip",
            "cross_os": "compatible-only",
            "manual_items": "allowed",
        },
        "items": selected_items,
        "counts": counts,
    }

    selection_debug = {
        "saved_installed": saved_installed,
        "saved_missing": saved_missing,
        "new_candidates": new_candidates,
        "selected_new_apps": sorted(
            [v for v in include_apps.values() if v.lower() in normalized_new]
        ),
        "included_apps": sorted(include_apps.values()),
    }
    return snapshot, selection_debug, warnings


def resolve_service_url(config: dict[str, Any], explicit: str = "") -> str:
    if explicit:
        return explicit.rstrip("/")
    env_url = os.environ.get("NBENCH_PROFILE_SERVICE_URL", "").strip()
    if env_url:
        return env_url.rstrip("/")
    conf_url = str(config.get("profile_service_url", "")).strip()
    if conf_url:
        return conf_url.rstrip("/")
    raise RuntimeError(
        "Profile service URL not configured. Set NBENCH_PROFILE_SERVICE_URL or ~/.nbench/config.json profile_service_url"
    )


def http_json(
    method: str,
    url: str,
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    payload = None
    if body is not None:
        payload = json.dumps(body).encode()

    req = urllib.request.Request(url, data=payload, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "N-benchProfile/1.0")
    if headers:
        for key, value in headers.items():
            req.add_header(key, value)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read().decode()
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode() if hasattr(exc, "read") else str(exc)
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("Service returned invalid JSON") from exc


def resolve_profile_id(target: str) -> str:
    candidate = target.strip()
    if not candidate:
        raise RuntimeError("Profile identifier is required")

    parsed = urllib.parse.urlparse(candidate)
    if parsed.scheme and parsed.netloc:
        parts = [part for part in parsed.path.split("/") if part]
        if not parts:
            raise RuntimeError("Could not resolve profile ID from URL")
        return parts[-1]
    return candidate


def load_profile_payload(input_file: str = "") -> dict[str, Any]:
    if input_file:
        payload = parse_json_file(Path(input_file))
    else:
        payload = json.load(sys.stdin)
    if not isinstance(payload, dict):
        raise RuntimeError("Profile payload must be a JSON object")
    if "profile" in payload and isinstance(payload["profile"], dict):
        return payload["profile"]
    return payload


def plan_import_actions(
    profile: dict[str, Any], local: dict[str, Any], current_os: str
) -> dict[str, Any]:
    items = profile.get("items", [])
    if not isinstance(items, list):
        items = []

    installed_index = local.get("installed_index", {})
    if not isinstance(installed_index, dict):
        installed_index = {}

    def installed_names(category: str) -> set[str]:
        raw = installed_index.get(category, [])
        if not isinstance(raw, list):
            return set()
        return {str(name).lower() for name in raw}

    installed_by_category = {
        "mcp": installed_names("mcp"),
        "cli-tool": installed_names("cli-tool"),
        "application": installed_names("application"),
        "plugin": installed_names("plugin"),
        "skill": installed_names("skill"),
        "workflow-pattern": installed_names("workflow-pattern"),
        "model-preference": installed_names("model-preference"),
    }

    prompt_required: list[dict[str, Any]] = []
    prompt_optional: list[dict[str, Any]] = []
    manual_required: list[dict[str, Any]] = []
    manual_optional: list[dict[str, Any]] = []
    already_installed: list[dict[str, Any]] = []
    unsupported: list[dict[str, Any]] = []

    for raw_item in items:
        if not isinstance(raw_item, dict):
            continue

        item = copy.deepcopy(raw_item)
        category = str(item.get("category", "")).strip().lower()
        name = str(item.get("name", "")).strip()
        priority = str(item.get("priority", "optional")).strip().lower()
        is_required = priority == "required"

        os_support = item.get("os_support", ALL_OSES)
        if not isinstance(os_support, list):
            os_support = list(ALL_OSES)
        os_support_norm = {normalize_os(str(value)) for value in os_support}

        if current_os not in os_support_norm:
            item["action"] = "unsupported_os"
            item["reason"] = f"Not supported on {current_os}"
            unsupported.append(item)
            continue

        if name.lower() in installed_by_category.get(category, set()):
            item["action"] = "skip_already_installed"
            item["reason"] = "Already installed"
            already_installed.append(item)
            continue

        install = (
            item.get("install", {}) if isinstance(item.get("install"), dict) else {}
        )
        install_type = str(install.get("type", "manual")).lower()
        manual_only = (
            bool(item.get("manual_only"))
            or install_type == "manual"
            or category
            in {
                "application",
                "workflow-pattern",
                "model-preference",
            }
        )

        if manual_only:
            item["action"] = "manual_setup"
            item["reason"] = "Manual setup required"
            if is_required:
                manual_required.append(item)
            else:
                manual_optional.append(item)
            continue

        item["action"] = "prompt_install"
        item["reason"] = "Ready to install"
        if is_required:
            prompt_required.append(item)
        else:
            prompt_optional.append(item)

    ordered = prompt_required + prompt_optional + manual_required + manual_optional
    summary = {
        "total_items": len(items),
        "prompt_required": len(prompt_required),
        "prompt_optional": len(prompt_optional),
        "manual_required": len(manual_required),
        "manual_optional": len(manual_optional),
        "already_installed": len(already_installed),
        "unsupported": len(unsupported),
    }

    return {
        "current_os": current_os,
        "summary": summary,
        "prompt_required": prompt_required,
        "prompt_optional": prompt_optional,
        "manual_required": manual_required,
        "manual_optional": manual_optional,
        "already_installed": already_installed,
        "unsupported": unsupported,
        "ordered_candidates": ordered,
    }


def parse_verify_arg(item: dict[str, Any]) -> tuple[str, str]:
    verification = item.get("verification", {})
    if not isinstance(verification, dict):
        return "manual", "Verify manually"

    verify_type = str(verification.get("type", "manual"))
    test_command = str(verification.get("test_command", "")).strip()

    if verify_type == "command_exists":
        command_name = (
            test_command.split(" ")[0] if test_command else str(item.get("name", ""))
        )
        return verify_type, command_name
    if verify_type == "config_exists":
        return verify_type, test_command
    if verify_type == "mcp_connect":
        return verify_type, ""
    return "manual", test_command or "Verify manually"


def run_cmd(args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(args, text=True, capture_output=True, check=False)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def install_item(
    item: dict[str, Any], plugin_root: Path, dry_run: bool = False
) -> dict[str, Any]:
    name = str(item.get("name", "")).strip()
    category = str(item.get("category", "")).strip().lower()
    install = item.get("install", {})
    if not isinstance(install, dict):
        install = {}

    install_type = str(install.get("type", "manual")).strip().lower()
    manual_only = (
        bool(item.get("manual_only"))
        or install_type == "manual"
        or category
        in {
            "application",
            "workflow-pattern",
            "model-preference",
        }
    )

    scripts = plugin_root / "scripts"
    install_cli = str(scripts / "install-cli.sh")
    install_mcp = str(scripts / "install-mcp.sh")
    install_skill = str(scripts / "install-skill.sh")
    install_plugin = str(scripts / "install-plugin.sh")
    verify_script = str(scripts / "verify-install.sh")

    if manual_only:
        return {
            "success": True,
            "name": name,
            "category": category,
            "manual": True,
            "installed": False,
            "verification": "manual",
            "message": str(install.get("instructions") or "Manual setup required"),
        }

    command: list[str] = []
    if category == "mcp" or install_type == "mcp":
        config = install.get("config_snippet")
        if isinstance(config, str):
            try:
                config = json.loads(config)
            except json.JSONDecodeError:
                config = None
        if not isinstance(config, dict):
            return {
                "success": False,
                "name": name,
                "category": category,
                "manual": True,
                "installed": False,
                "verification": "manual",
                "message": "Missing valid MCP config_snippet",
            }
        command = [install_mcp, name, json.dumps(redact_value(config))]
    elif category == "cli-tool":
        cli_command = str(install.get("command", "")).strip()
        if not cli_command:
            return {
                "success": False,
                "name": name,
                "category": category,
                "manual": True,
                "installed": False,
                "verification": "manual",
                "message": "No CLI install command provided",
            }
        command = [install_cli, name, cli_command, install_type or "manual"]
    elif category == "skill":
        source = str(install.get("source", "")).strip()
        scope = str(install.get("scope", "user")).strip() or "user"
        if source:
            command = [install_skill, name, source, scope]
        else:
            command = [install_skill, name]
    elif category == "plugin":
        repo = str(install.get("repo", "")).strip()
        if repo:
            command = [install_plugin, name, repo]
        else:
            command = [install_plugin, name]
    else:
        return {
            "success": True,
            "name": name,
            "category": category,
            "manual": True,
            "installed": False,
            "verification": "manual",
            "message": "Manual setup required for this category",
        }

    verify_type, verify_arg = parse_verify_arg(item)
    verify_command = [verify_script, name, verify_type]
    if verify_arg:
        verify_command.append(verify_arg)

    if dry_run:
        return {
            "success": True,
            "name": name,
            "category": category,
            "manual": False,
            "installed": False,
            "verification": verify_type,
            "dry_run": True,
            "install_command": command,
            "verify_command": verify_command,
        }

    code, stdout, stderr = run_cmd(command)
    if code != 0:
        return {
            "success": False,
            "name": name,
            "category": category,
            "manual": False,
            "installed": False,
            "verification": "not_run",
            "install_command": command,
            "stdout": stdout,
            "stderr": stderr,
        }

    verify_code, verify_stdout, verify_stderr = run_cmd(verify_command)
    success = verify_code == 0 or verify_type == "manual"

    return {
        "success": success,
        "name": name,
        "category": category,
        "manual": False,
        "installed": True,
        "verification": verify_type,
        "install_command": command,
        "verify_command": verify_command,
        "stdout": stdout,
        "stderr": stderr,
        "verify_stdout": verify_stdout,
        "verify_stderr": verify_stderr,
    }


def cmd_detect(args: argparse.Namespace) -> None:
    cwd = Path(args.cwd or os.getcwd())
    merged = merge_detected_context(
        cwd,
        args.skills_scope,
        Path(args.recs_dir),
        Path(args.state_file),
        args.detect_json_file,
        args.repo_json_file,
    )
    print(json.dumps(merged, indent=2))


def cmd_export(args: argparse.Namespace) -> None:
    cwd = Path(args.cwd or os.getcwd())
    state_path = Path(args.state_file)
    state = load_state(state_path)

    merged = merge_detected_context(
        cwd,
        args.skills_scope,
        Path(args.recs_dir),
        state_path,
        args.detect_json_file,
        args.repo_json_file,
    )

    selected_new_apps = parse_csv(args.selected_new_apps)
    include_missing_saved_apps = parse_csv(args.include_saved_missing_apps)
    required_items = parse_csv(args.required_items)

    snapshot, selection_debug, warnings = build_profile_snapshot(
        merged,
        selected_new_apps,
        not bool(args.exclude_saved_apps),
        include_missing_saved_apps,
        required_items,
        args.profile_name,
    )

    if not args.dry_run:
        detected_apps = [
            item.get("name", "")
            for item in merged.get("catalog", {}).get("applications", [])
            if isinstance(item, dict)
        ]
        included_apps = selection_debug.get("included_apps", [])
        required_apps = {
            token.lower()
            for token in required_items
            if token.lower().startswith("application:")
            or token.lower() in {name.lower() for name in included_apps}
        }
        update_saved_app_state(
            state,
            [str(v) for v in detected_apps],
            [str(v) for v in included_apps],
            required_apps,
        )
        state["last_exported_at"] = now_iso()
        write_json_file(state_path, state)

    output = {
        "profile": snapshot,
        "application_selection": selection_debug,
        "state_file": str(state_path),
        "warnings": warnings + merged.get("warnings", []),
        "state_updated": not args.dry_run,
    }

    if args.output_file:
        write_json_file(Path(args.output_file), output)
    print(json.dumps(output, indent=2))


def cmd_publish(args: argparse.Namespace) -> None:
    state_path = Path(args.state_file)
    state = load_state(state_path)
    config = load_config(Path(args.config_file))
    profile = load_profile_payload(args.input_file)

    service_url = resolve_service_url(config, args.service_url)
    response = http_json("POST", f"{service_url}/v1/profiles", {"profile": profile})

    profile_id = str(response.get("id") or response.get("profile_id") or "")
    if not profile_id:
        raw = json.dumps(profile, sort_keys=True)
        profile_id = hashlib.sha256(raw.encode()).hexdigest()[:12]

    share_url = str(response.get("url") or f"{service_url}/p/{profile_id}")
    manage_token = str(response.get("manage_token") or response.get("token") or "")

    state.setdefault("published_profiles", {})[profile_id] = {
        "url": share_url,
        "manage_token": manage_token,
        "status": "active",
        "created_at": str(response.get("created_at") or now_iso()),
    }
    write_json_file(state_path, state)

    print(
        json.dumps(
            {
                "success": True,
                "id": profile_id,
                "url": share_url,
                "immutable": True,
                "non_expiring": True,
                "tombstone_supported": True,
            },
            indent=2,
        )
    )


def cmd_fetch(args: argparse.Namespace) -> None:
    config = load_config(Path(args.config_file))
    service_url = resolve_service_url(config, args.service_url)
    profile_id = resolve_profile_id(args.target)

    response = http_json("GET", f"{service_url}/v1/profiles/{profile_id}")
    status = str(response.get("status") or "active")

    output = {
        "id": str(response.get("id") or profile_id),
        "status": status,
        "tombstoned": status == "tombstoned",
        "profile": response.get("profile"),
        "created_at": response.get("created_at", ""),
    }
    print(json.dumps(output, indent=2))


def cmd_plan_import(args: argparse.Namespace) -> None:
    cwd = Path(args.cwd or os.getcwd())
    current_os = normalize_os(args.current_os)

    profile = load_profile_payload(args.profile_file)
    local = merge_detected_context(
        cwd,
        args.skills_scope,
        Path(args.recs_dir),
        Path(args.state_file),
        args.detect_json_file,
        args.repo_json_file,
    )

    planned = plan_import_actions(profile, local, current_os)
    print(json.dumps(planned, indent=2))


def cmd_install_item(args: argparse.Namespace) -> None:
    if args.item_file:
        payload = parse_json_file(Path(args.item_file))
    else:
        payload = json.load(sys.stdin)
    if not isinstance(payload, dict):
        raise RuntimeError("Item payload must be an object")

    if "item" in payload and isinstance(payload["item"], dict):
        payload = payload["item"]

    root = Path(args.plugin_root or PLUGIN_ROOT)
    result = install_item(payload, root, args.dry_run)
    print(json.dumps(result, indent=2))


def cmd_tombstone(args: argparse.Namespace) -> None:
    state_path = Path(args.state_file)
    state = load_state(state_path)
    config = load_config(Path(args.config_file))
    service_url = resolve_service_url(config, args.service_url)

    profile_id = resolve_profile_id(args.target)
    token = args.manage_token
    if not token:
        profile_entry = state.get("published_profiles", {}).get(profile_id, {})
        if isinstance(profile_entry, dict):
            token = str(profile_entry.get("manage_token", ""))

    if not token:
        raise RuntimeError(
            "Missing manage token. Pass --manage-token or publish from this machine first."
        )

    response = http_json(
        "POST",
        f"{service_url}/v1/profiles/{profile_id}/tombstone",
        body={},
        headers={"Authorization": f"Bearer {token}"},
    )

    entry = state.setdefault("published_profiles", {}).get(profile_id)
    if isinstance(entry, dict):
        entry["status"] = "tombstoned"
        entry["tombstoned_at"] = str(response.get("tombstoned_at") or now_iso())
    write_json_file(state_path, state)

    print(
        json.dumps(
            {
                "success": True,
                "id": profile_id,
                "status": "tombstoned",
                "url": str(response.get("url") or f"{service_url}/p/{profile_id}"),
            },
            indent=2,
        )
    )


def cmd_saved_apps(args: argparse.Namespace) -> None:
    state_path = Path(args.state_file)
    state = load_state(state_path)
    saved = state.setdefault("saved_applications", {})

    removed: list[str] = []
    if args.remove:
        requested = parse_csv(args.remove)
        for token in requested:
            for key in list(saved.keys()):
                if key.lower() == token.lower():
                    del saved[key]
                    removed.append(key)
        if removed:
            write_json_file(state_path, state)

    rows = []
    for name in sorted(saved.keys(), key=lambda x: x.lower()):
        entry = saved.get(name, {})
        if not isinstance(entry, dict):
            entry = {}
        rows.append(
            {
                "name": name,
                "last_seen_state": entry.get("last_seen_state", "unknown"),
                "priority": entry.get("priority", "optional"),
                "last_selected_at": entry.get("last_selected_at", ""),
            }
        )

    print(
        json.dumps(
            {
                "saved_applications": rows,
                "removed": sorted(removed),
                "state_file": str(state_path),
            },
            indent=2,
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="N-bench profile export/import manager")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common_detection_options(cmd: argparse.ArgumentParser) -> None:
        cmd.add_argument("--cwd", default="", help="Working directory for detection")
        cmd.add_argument(
            "--skills-scope", choices=["global", "project", "both"], default="both"
        )
        cmd.add_argument("--recs-dir", default=str(DEFAULT_RECS_DIR))
        cmd.add_argument("--state-file", default=str(DEFAULT_STATE_PATH))
        cmd.add_argument("--detect-json-file", default="")
        cmd.add_argument("--repo-json-file", default="")

    detect_cmd = sub.add_parser(
        "detect", help="Detect environment and build profile catalog"
    )
    add_common_detection_options(detect_cmd)
    detect_cmd.set_defaults(func=cmd_detect)

    export_cmd = sub.add_parser(
        "export", help="Build profile snapshot from current setup"
    )
    add_common_detection_options(export_cmd)
    export_cmd.add_argument(
        "--selected-new-apps",
        default="",
        help="CSV list of newly detected apps to include",
    )
    export_cmd.add_argument(
        "--include-saved-missing-apps",
        default="",
        help="CSV list of previously saved missing apps to include",
    )
    export_cmd.add_argument(
        "--exclude-saved-apps",
        action="store_true",
        help="Do not include previously saved installed apps",
    )
    export_cmd.add_argument(
        "--required-items", default="", help="CSV of required item IDs or names"
    )
    export_cmd.add_argument("--profile-name", default="")
    export_cmd.add_argument("--output-file", default="")
    export_cmd.add_argument("--dry-run", action="store_true")
    export_cmd.set_defaults(func=cmd_export)

    publish_cmd = sub.add_parser(
        "publish", help="Publish profile snapshot to link service"
    )
    publish_cmd.add_argument(
        "--input-file", default="", help="Input JSON file (reads stdin if omitted)"
    )
    publish_cmd.add_argument("--service-url", default="")
    publish_cmd.add_argument("--state-file", default=str(DEFAULT_STATE_PATH))
    publish_cmd.add_argument("--config-file", default=str(DEFAULT_CONFIG_PATH))
    publish_cmd.set_defaults(func=cmd_publish)

    fetch_cmd = sub.add_parser("fetch", help="Fetch profile snapshot from link service")
    fetch_cmd.add_argument("target", help="Profile URL or ID")
    fetch_cmd.add_argument("--service-url", default="")
    fetch_cmd.add_argument("--config-file", default=str(DEFAULT_CONFIG_PATH))
    fetch_cmd.set_defaults(func=cmd_fetch)

    import_plan_cmd = sub.add_parser(
        "plan-import", help="Plan import actions against local machine"
    )
    import_plan_cmd.add_argument(
        "--profile-file", default="", help="Profile JSON file (reads stdin if omitted)"
    )
    import_plan_cmd.add_argument("--current-os", default="", help="Override current OS")
    add_common_detection_options(import_plan_cmd)
    import_plan_cmd.set_defaults(func=cmd_plan_import)

    install_cmd = sub.add_parser(
        "install-item", help="Install one item from import plan"
    )
    install_cmd.add_argument(
        "--item-file", default="", help="Item JSON file (reads stdin if omitted)"
    )
    install_cmd.add_argument("--plugin-root", default="")
    install_cmd.add_argument("--dry-run", action="store_true")
    install_cmd.set_defaults(func=cmd_install_item)

    tombstone_cmd = sub.add_parser(
        "tombstone", help="Tombstone an immutable profile link"
    )
    tombstone_cmd.add_argument("target", help="Profile URL or ID")
    tombstone_cmd.add_argument("--manage-token", default="")
    tombstone_cmd.add_argument("--service-url", default="")
    tombstone_cmd.add_argument("--state-file", default=str(DEFAULT_STATE_PATH))
    tombstone_cmd.add_argument("--config-file", default=str(DEFAULT_CONFIG_PATH))
    tombstone_cmd.set_defaults(func=cmd_tombstone)

    saved_apps_cmd = sub.add_parser(
        "saved-apps", help="List or remove saved application selections"
    )
    saved_apps_cmd.add_argument("--state-file", default=str(DEFAULT_STATE_PATH))
    saved_apps_cmd.add_argument(
        "--remove", default="", help="CSV list of saved app names to remove"
    )
    saved_apps_cmd.set_defaults(func=cmd_saved_apps)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except RuntimeError as exc:
        print(json.dumps({"success": False, "error": str(exc)}))
        sys.exit(1)
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"success": False, "error": f"Invalid JSON input: {exc}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
