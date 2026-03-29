"""Host detection and environment diagnostics for Flux."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Optional

from .utils import current_flux_version, get_repo_root, json_output

KNOWN_DRIVERS = {"codex", "claude", "opencode", "cursor", "windsurf", "unknown"}


def _read_json(path: Path) -> Optional[dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _normalize_driver(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    normalized = value.strip().lower().replace(" ", "").replace("-", "")
    aliases = {
        "codex": "codex",
        "codexcli": "codex",
        "claude": "claude",
        "claudecode": "claude",
        "opencode": "opencode",
        "droid": "opencode",
        "cursor": "cursor",
        "windsurf": "windsurf",
        "unknown": "unknown",
        "auto": None,
    }
    return aliases.get(normalized)


def _command_version(command: str) -> Optional[str]:
    if not shutil.which(command):
        return None
    try:
        result = subprocess.run(
            [command, "--version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except Exception:
        return None
    output = (result.stdout or result.stderr or "").strip().splitlines()
    return output[0].strip() if output else None


def _runtime_details(repo_root: Path) -> dict[str, Any]:
    candidates = [
        ("package.json", repo_root / "package.json", "repo_local_runtime"),
        (".claude-plugin/plugin.json", repo_root / ".claude-plugin" / "plugin.json", "claude_adapter_manifest"),
    ]
    for label, path, kind in candidates:
        data = _read_json(path)
        if not data:
            continue
        version = data.get("version")
        if isinstance(version, str) and version.strip():
            return {
                "version": version.strip(),
                "source": label,
                "source_kind": kind,
                "path": str(path),
                "authoritative": kind == "repo_local_runtime",
            }
    return {
        "version": None,
        "source": None,
        "source_kind": None,
        "path": None,
        "authoritative": False,
    }


def _repo_setup_details(repo_root: Path) -> dict[str, Any]:
    meta_path = repo_root / ".flux" / "meta.json"
    meta = _read_json(meta_path) or {}
    setup_version = meta.get("setup_version")
    if not isinstance(setup_version, str) or not setup_version.strip():
        setup_version = None

    fluxctl_path = repo_root / ".flux" / "bin" / "fluxctl"
    usage_path = repo_root / ".flux" / "usage.md"
    agents_path = repo_root / "AGENTS.md"
    claude_md_path = repo_root / "CLAUDE.md"

    installed = any(
        path.exists()
        for path in (fluxctl_path, usage_path, agents_path, claude_md_path)
    ) or setup_version is not None

    return {
        "installed": installed,
        "version": setup_version,
        "source": str(meta_path) if meta_path.exists() else None,
        "source_kind": "repo_setup",
        "paths": {
            "fluxctl": str(fluxctl_path),
            "usage": str(usage_path),
            "agents": str(agents_path),
            "claude_md": str(claude_md_path),
        },
        "files": {
            "fluxctl": fluxctl_path.exists(),
            "usage": usage_path.exists(),
            "agents": agents_path.exists(),
            "claude_md": claude_md_path.exists(),
        },
    }


def _claude_adapter_details(home: Path) -> dict[str, Any]:
    env_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "").strip()
    if env_root:
        manifest = Path(env_root) / ".claude-plugin" / "plugin.json"
        data = _read_json(manifest)
        if data and isinstance(data.get("version"), str):
            return {
                "installed": True,
                "version": data["version"].strip(),
                "source": "env:CLAUDE_PLUGIN_ROOT",
                "source_kind": "active_claude_plugin_root",
                "path": str(manifest),
            }

    installed_path = home / ".claude" / "plugins" / "installed_plugins.json"
    data = _read_json(installed_path)
    plugins = (data or {}).get("plugins")
    if isinstance(plugins, dict):
        entries = plugins.get("flux@nairon-flux")
        if isinstance(entries, list) and entries:
            first = entries[0] if isinstance(entries[0], dict) else {}
            version = first.get("version")
            if isinstance(version, str) and version.strip():
                return {
                    "installed": True,
                    "version": version.strip(),
                    "source": "installed_plugins.json",
                    "source_kind": "claude_installed_plugin",
                    "path": str(installed_path),
                    "install_path": first.get("installPath"),
                }

    cache_root = home / ".claude" / "plugins" / "cache" / "nairon-flux" / "flux"
    if cache_root.exists():
        candidates = sorted(
            [p for p in cache_root.iterdir() if p.is_dir()],
            key=lambda p: p.name,
            reverse=True,
        )
        for candidate in candidates:
            manifest = candidate / ".claude-plugin" / "plugin.json"
            data = _read_json(manifest)
            if data and isinstance(data.get("version"), str):
                return {
                    "installed": True,
                    "version": data["version"].strip(),
                    "source": "claude cache",
                    "source_kind": "claude_cache",
                    "path": str(manifest),
                }

    return {
        "installed": False,
        "version": None,
        "source": None,
        "source_kind": "claude_installed_plugin",
        "path": None,
    }


def _host_cli_details() -> dict[str, Any]:
    return {
        "codex": {
            "available": shutil.which("codex") is not None,
            "version": _command_version("codex"),
        },
        "claude": {
            "available": shutil.which("claude") is not None,
            "version": _command_version("claude"),
        },
    }


def _primary_driver(repo_root: Path) -> dict[str, Any]:
    override = _normalize_driver(os.environ.get("FLUX_PRIMARY_DRIVER"))
    if override:
        return {
            "name": override,
            "source": "env:FLUX_PRIMARY_DRIVER",
            "confidence": "high",
            "reason": "Explicit override",
        }

    if os.environ.get("CODEX_HOME"):
        return {
            "name": "codex",
            "source": "env:CODEX_HOME",
            "confidence": "high",
            "reason": "Active Codex session detected",
        }

    droid_root = os.environ.get("DROID_PLUGIN_ROOT", "").strip()
    claude_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "").strip()
    if droid_root and not claude_root:
        return {
            "name": "opencode",
            "source": "env:DROID_PLUGIN_ROOT",
            "confidence": "high",
            "reason": "Active OpenCode session detected",
        }
    if claude_root and not droid_root:
        return {
            "name": "claude",
            "source": "env:CLAUDE_PLUGIN_ROOT",
            "confidence": "high",
            "reason": "Active Claude Code session detected",
        }

    has_agents = (repo_root / "AGENTS.md").exists() or (repo_root / ".claude" / "AGENTS.md").exists()
    has_claude_md = (repo_root / "CLAUDE.md").exists() or (repo_root / ".claude" / "CLAUDE.md").exists()
    if has_agents and not has_claude_md:
        return {
            "name": "codex",
            "source": "repo:AGENTS.md",
            "confidence": "medium",
            "reason": "Repo uses AGENTS.md without a primary CLAUDE.md signal",
        }
    if has_claude_md and not has_agents:
        return {
            "name": "claude",
            "source": "repo:CLAUDE.md",
            "confidence": "medium",
            "reason": "Repo uses CLAUDE.md without AGENTS.md",
        }
    if has_agents and has_claude_md:
        return {
            "name": "codex",
            "source": "repo:AGENTS.md+CLAUDE.md",
            "confidence": "low",
            "reason": "Both instruction files exist; defaulting to Codex-first repo setup",
        }

    has_codex = shutil.which("codex") is not None
    has_claude = shutil.which("claude") is not None
    if has_codex and not has_claude:
        return {
            "name": "codex",
            "source": "path:codex",
            "confidence": "low",
            "reason": "Only Codex CLI is available on PATH",
        }
    if has_claude and not has_codex:
        return {
            "name": "claude",
            "source": "path:claude",
            "confidence": "low",
            "reason": "Only Claude CLI is available on PATH",
        }

    return {
        "name": "unknown",
        "source": "none",
        "confidence": "low",
        "reason": "No active host signal detected",
    }


def _sync_status(authoritative: Optional[str], adapter: dict[str, Any]) -> dict[str, Any]:
    if not authoritative:
        return {"status": "unknown", "in_sync": None, "reason": "Runtime version unavailable"}
    if not adapter.get("installed"):
        return {"status": "missing", "in_sync": None, "reason": "Host adapter not installed"}
    adapter_version = adapter.get("version")
    if not adapter_version:
        return {"status": "unknown", "in_sync": None, "reason": "Host adapter version unavailable"}
    in_sync = adapter_version == authoritative
    return {
        "status": "in_sync" if in_sync else "out_of_sync",
        "in_sync": in_sync,
        "reason": "Host adapter matches runtime" if in_sync else "Host adapter differs from runtime",
    }


def _guidance(
    repo_root: Path,
    primary: dict[str, Any],
    runtime: dict[str, Any],
    repo_setup: dict[str, Any],
    primary_sync: dict[str, Any],
) -> dict[str, str]:
    repo_fluxctl = repo_root / ".flux" / "bin" / "fluxctl"
    verify_cmd = ".flux/bin/fluxctl doctor --json" if repo_fluxctl.exists() else "scripts/fluxctl doctor --json"
    driver = primary["name"]

    if driver == "codex":
        install = "Run /flux:setup in this repo to install repo-local Flux helpers and AGENTS.md instructions."
        if primary_sync["status"] in {"missing", "out_of_sync"}:
            update = "Update the repo-local Flux source you installed from, then re-run /flux:setup so .flux/bin and AGENTS.md match the runtime. Restart Codex afterward."
        else:
            update = "Update the repo-local Flux source you installed from. Re-run /flux:setup only if doctor reports setup drift, then restart Codex."
        restart = "Restart Codex after Flux updates, AGENTS.md changes, or .mcp.json changes."
        troubleshoot = f"Use `{verify_cmd}` to confirm Codex is the primary driver and that repo-local setup matches the authoritative runtime."
    elif driver == "claude":
        install = "Install Flux through Claude's plugin workflow, then initialize the repo with /flux:setup if you want project-local helpers."
        update = "Run `claude plugin update flux@nairon-flux -s user`, then restart Claude Code. If this repo's runtime is newer, refresh the repo checkout too."
        restart = "Restart Claude Code after plugin updates or settings changes."
        troubleshoot = f"Use `{verify_cmd}` to compare the repo-local runtime with the installed Claude plugin version."
    elif driver == "opencode":
        install = "Initialize the repo with /flux:setup so Flux can install project-local helpers for OpenCode-compatible workflows."
        update = "Update the repo-local Flux source you installed from, then re-run /flux:setup if doctor reports repo setup drift."
        restart = "Restart OpenCode after Flux updates or instruction-file changes."
        troubleshoot = f"Use `{verify_cmd}` to confirm the repo-local runtime is authoritative for this host."
    else:
        install = "Initialize the repo with /flux:setup so Flux can install project-local helpers for the active host."
        update = "Update Flux from the same source you installed it from, then restart your agent session."
        restart = "Restart your agent session after Flux updates or MCP/instruction-file changes."
        troubleshoot = f"Use `{verify_cmd}` to detect the active host and compare adapter/runtime versions."

    return {
        "install": install,
        "verify": f"Run `{verify_cmd}`.",
        "update": update,
        "restart": restart,
        "troubleshoot": troubleshoot,
    }


def collect_host_diagnostics() -> dict[str, Any]:
    repo_root = get_repo_root()
    home = Path(os.environ.get("HOME", str(Path.home())))

    runtime = _runtime_details(repo_root)
    repo_setup = _repo_setup_details(repo_root)
    claude_adapter = _claude_adapter_details(home)
    primary = _primary_driver(repo_root)
    host_clis = _host_cli_details()

    if primary["name"] in {"codex", "opencode"}:
        primary_adapter = {
            "name": primary["name"],
            **repo_setup,
        }
    elif primary["name"] == "claude":
        primary_adapter = {
            "name": "claude",
            **claude_adapter,
        }
    else:
        primary_adapter = {"name": "unknown", "installed": False, "version": None}

    primary_sync = _sync_status(runtime.get("version"), primary_adapter)
    repo_setup_sync = _sync_status(runtime.get("version"), repo_setup)
    claude_sync = _sync_status(runtime.get("version"), claude_adapter)

    payload = {
        "repo_root": str(repo_root),
        "primary_driver": primary,
        "authoritative_version": {
            "version": runtime.get("version"),
            "source": runtime.get("source"),
            "source_kind": runtime.get("source_kind"),
            "path": runtime.get("path"),
        },
        "runtime": runtime,
        "repo_setup": {
            **repo_setup,
            "sync": repo_setup_sync,
        },
        "host_adapters": {
            "claude": {
                **claude_adapter,
                "sync": claude_sync,
            },
        },
        "host_clis": host_clis,
        "primary_adapter": {
            **primary_adapter,
            "sync": primary_sync,
        },
    }
    payload["guidance"] = _guidance(repo_root, primary, runtime, repo_setup, primary_sync)
    return payload


def _print_summary(payload: dict[str, Any], include_guidance: bool = False) -> None:
    primary = payload["primary_driver"]
    authoritative = payload["authoritative_version"]
    primary_adapter = payload["primary_adapter"]

    print(f"Primary driver: {primary['name']} ({primary['reason']})")
    if authoritative["version"]:
        print(
            f"Authoritative version: {authoritative['version']} "
            f"({authoritative['source']})"
        )
    else:
        print("Authoritative version: unknown")

    adapter_version = primary_adapter.get("version") or "unknown"
    adapter_status = primary_adapter.get("sync", {}).get("status", "unknown")
    adapter_name = primary_adapter.get("name", "unknown")
    print(f"Primary adapter ({adapter_name}): {adapter_version} [{adapter_status}]")

    claude = payload["host_adapters"]["claude"]
    if claude.get("installed"):
        claude_version = claude.get("version") or "unknown"
        claude_status = claude.get("sync", {}).get("status", "unknown")
        print(f"Claude adapter: {claude_version} [{claude_status}]")

    if include_guidance:
        guidance = payload["guidance"]
        print("")
        print(f"Verify: {guidance['verify']}")
        print(f"Update: {guidance['update']}")
        print(f"Restart: {guidance['restart']}")


def cmd_env(args: argparse.Namespace) -> None:
    payload = collect_host_diagnostics()
    if args.json:
        json_output(payload)
    else:
        _print_summary(payload, include_guidance=False)


def cmd_doctor(args: argparse.Namespace) -> None:
    payload = collect_host_diagnostics()
    if args.json:
        json_output(payload)
    else:
        _print_summary(payload, include_guidance=True)


def cmd_version(args: argparse.Namespace) -> None:
    payload = collect_host_diagnostics()
    version = payload["authoritative_version"]["version"] or current_flux_version()
    if args.json or args.verbose:
        result = {
            "version": version,
            "authoritative_version": payload["authoritative_version"],
            "primary_driver": payload["primary_driver"],
            "primary_adapter": payload["primary_adapter"],
            "guidance": payload["guidance"] if args.verbose else None,
        }
        json_output(result)
        return
    print(version or "unknown")
