#!/usr/bin/env python3
"""Tests for profile-manager.py."""

import importlib.util
import json
import subprocess
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


SCRIPT_PATH = Path(__file__).parent / "profile-manager.py"
SPEC = importlib.util.spec_from_file_location("profile_manager", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
profile_manager = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(profile_manager)


def test_redaction_masks_sensitive_values():
    payload = {
        "api_key": "sk-abcdefghijklmnop123456",
        "nested": {"token": "ghp_abcdefghijklmnopqrstuvwxyz0123"},
        "text": "Authorization=Bearer sk-secret-value-1234567890",
    }
    redacted = profile_manager.redact_value(payload)

    assert redacted["api_key"] == "<redacted>"
    assert redacted["nested"]["token"] == "<redacted>"
    assert "<redacted>" in redacted["text"]


def test_skill_detection_dedupes_name_and_hash():
    with tempfile.TemporaryDirectory(prefix="flux-profile-skills-") as tmp:
        root = Path(tmp)
        home = root / "home"
        cwd = root / "repo"

        (home / ".claude" / "skills" / "alpha").mkdir(parents=True)
        (cwd / ".claude" / "skills" / "alpha").mkdir(parents=True)
        (cwd / ".claude" / "skills" / "alpha-variant").mkdir(parents=True)

        (home / ".claude" / "skills" / "alpha" / "SKILL.md").write_text("hello")
        (cwd / ".claude" / "skills" / "alpha" / "SKILL.md").write_text("hello")
        (cwd / ".claude" / "skills" / "alpha-variant" / "SKILL.md").write_text(
            "different"
        )

        old_home = profile_manager.HOME
        try:
            setattr(profile_manager, "HOME", home)
            skills = profile_manager.detect_skills("both", cwd)
        finally:
            setattr(profile_manager, "HOME", old_home)

        names = [s["name"] for s in skills]
        assert "alpha" in names
        alpha = [s for s in skills if s["name"] == "alpha"]
        assert len(alpha) == 1
        assert set(alpha[0]["scopes"]) == {"global", "project"}
        assert "alpha-variant" in names


def test_application_selection_state_buckets():
    state = {
        "saved_applications": {
            "slack": {"priority": "optional"},
            "figma": {"priority": "required"},
        }
    }
    buckets = profile_manager.compute_application_selection(["slack", "granola"], state)
    assert buckets["saved_installed"] == ["slack"]
    assert buckets["new_candidates"] == ["granola"]
    assert buckets["saved_missing"] == ["figma"]


def test_build_profile_snapshot_respects_app_and_required_selection():
    merged = {
        "os": "macos",
        "catalog": {
            "mcps": [
                {
                    "id": "mcp:exa",
                    "name": "exa",
                    "category": "mcp",
                    "install": {"type": "mcp", "config_snippet": {"token": "secret"}},
                }
            ],
            "cli_tools": [
                {
                    "id": "cli-tool:jq",
                    "name": "jq",
                    "category": "cli-tool",
                    "install": {"type": "brew", "command": "brew install jq"},
                }
            ],
            "skills": [],
            "applications": [
                {
                    "id": "application:granola",
                    "name": "granola",
                    "category": "application",
                    "install": {"type": "manual", "instructions": "download"},
                },
                {
                    "id": "application:slack",
                    "name": "slack",
                    "category": "application",
                    "install": {"type": "manual", "instructions": "download"},
                },
            ],
            "plugins": [],
            "workflow_patterns": [],
            "model_preferences": [],
        },
        "application_selection": {
            "saved_installed": ["slack"],
            "saved_missing": ["figma"],
            "new_candidates": ["granola"],
        },
    }

    snapshot, selection_debug, warnings = profile_manager.build_profile_snapshot(
        merged,
        selected_new_apps=["granola"],
        include_saved_apps=True,
        include_saved_missing_apps=[],
        required_items=["mcp:exa", "granola"],
        profile_name="Team Profile",
    )

    assert warnings == []
    names = [item["name"] for item in snapshot["items"]]
    assert "slack" in names
    assert "granola" in names
    assert selection_debug["included_apps"] == ["granola", "slack"]

    exa_item = [item for item in snapshot["items"] if item["name"] == "exa"][0]
    assert exa_item["priority"] == "required"
    assert exa_item["install"]["config_snippet"]["token"] == "<redacted>"


def test_plan_import_filters_incompatible_and_installed_items():
    profile = {
        "items": [
            {
                "id": "cli-tool:jq",
                "name": "jq",
                "category": "cli-tool",
                "priority": "optional",
                "install": {"type": "brew", "command": "brew install jq"},
                "os_support": ["macos", "linux"],
            },
            {
                "id": "cli-tool:fd",
                "name": "fd",
                "category": "cli-tool",
                "priority": "optional",
                "install": {"type": "brew", "command": "brew install fd"},
                "os_support": ["windows"],
            },
            {
                "id": "application:slack",
                "name": "slack",
                "category": "application",
                "priority": "required",
                "install": {"type": "manual", "instructions": "download"},
                "os_support": ["macos"],
                "manual_only": True,
            },
            {
                "id": "mcp:exa",
                "name": "exa",
                "category": "mcp",
                "priority": "required",
                "install": {"type": "mcp", "config_snippet": {"command": "npx"}},
                "os_support": ["macos", "linux", "windows"],
            },
        ]
    }

    local = {
        "installed_index": {
            "cli-tool": ["jq"],
            "mcp": [],
            "application": [],
            "plugin": [],
            "skill": [],
            "workflow-pattern": [],
            "model-preference": [],
        }
    }

    plan = profile_manager.plan_import_actions(profile, local, "macos")
    assert plan["summary"]["already_installed"] == 1
    assert plan["summary"]["unsupported"] == 1
    assert plan["summary"]["manual_required"] == 1
    assert plan["summary"]["prompt_required"] == 1


class _ProfileHandler(BaseHTTPRequestHandler):
    profiles = {}
    tokens = {}
    next_id = 1

    def _json(self, status: int, payload: dict):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode() if length else "{}"
        payload = json.loads(body)

        if self.path == "/v1/profiles":
            profile_id = f"prf-{_ProfileHandler.next_id}"
            _ProfileHandler.next_id += 1
            token = f"token-{profile_id}"
            _ProfileHandler.profiles[profile_id] = {
                "status": "active",
                "profile": payload.get("profile", {}),
                "created_at": "2026-02-22T00:00:00Z",
            }
            _ProfileHandler.tokens[profile_id] = token
            host = str(getattr(self.server, "server_name", "127.0.0.1"))
            port = int(getattr(self.server, "server_port", 80))
            self._json(
                200,
                {
                    "id": profile_id,
                    "url": f"http://{host}:{port}/p/{profile_id}",
                    "manage_token": token,
                    "created_at": "2026-02-22T00:00:00Z",
                },
            )
            return

        if self.path.startswith("/v1/profiles/") and self.path.endswith("/tombstone"):
            parts = [p for p in self.path.split("/") if p]
            profile_id = parts[2]
            auth = self.headers.get("Authorization", "")
            expected = f"Bearer {_ProfileHandler.tokens.get(profile_id, '')}"
            if auth != expected:
                self._json(403, {"error": "forbidden"})
                return
            if profile_id not in _ProfileHandler.profiles:
                self._json(404, {"error": "missing"})
                return
            _ProfileHandler.profiles[profile_id]["status"] = "tombstoned"
            self._json(
                200,
                {
                    "id": profile_id,
                    "status": "tombstoned",
                    "tombstoned_at": "2026-02-22T01:00:00Z",
                },
            )
            return

        self._json(404, {"error": "not_found"})

    def do_GET(self):
        if self.path.startswith("/v1/profiles/"):
            parts = [p for p in self.path.split("/") if p]
            profile_id = parts[2]
            if profile_id not in _ProfileHandler.profiles:
                self._json(404, {"error": "missing"})
                return
            data = _ProfileHandler.profiles[profile_id]
            self._json(
                200,
                {
                    "id": profile_id,
                    "status": data["status"],
                    "profile": data["profile"],
                    "created_at": data["created_at"],
                },
            )
            return
        self._json(404, {"error": "not_found"})

    def log_message(self, format, *args):
        return


def _run_cli(args, stdin_payload=None):
    cmd = ["python3", str(SCRIPT_PATH)] + args
    proc = subprocess.run(
        cmd,
        input=json.dumps(stdin_payload) if stdin_payload is not None else None,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(
            f"Command failed: {' '.join(cmd)}\nSTDOUT:{proc.stdout}\nSTDERR:{proc.stderr}"
        )
    return json.loads(proc.stdout)


def test_publish_fetch_tombstone_roundtrip():
    server = HTTPServer(("127.0.0.1", 0), _ProfileHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    with tempfile.TemporaryDirectory(prefix="flux-profile-service-") as tmp:
        root = Path(tmp)
        state_file = root / "state.json"
        config_file = root / "config.json"
        payload_file = root / "profile.json"

        service_url = f"http://127.0.0.1:{server.server_address[1]}"
        config_file.write_text(json.dumps({"profile_service_url": service_url}))
        payload_file.write_text(
            json.dumps({"profile": {"items": [], "metadata": {"os": "macos"}}})
        )

        published = _run_cli(
            [
                "publish",
                "--input-file",
                str(payload_file),
                "--config-file",
                str(config_file),
                "--state-file",
                str(state_file),
            ]
        )
        profile_id = published["id"]
        assert published["success"] is True

        fetched = _run_cli(
            [
                "fetch",
                profile_id,
                "--config-file",
                str(config_file),
            ]
        )
        assert fetched["status"] == "active"

        tombstoned = _run_cli(
            [
                "tombstone",
                profile_id,
                "--config-file",
                str(config_file),
                "--state-file",
                str(state_file),
            ]
        )
        assert tombstoned["status"] == "tombstoned"

        fetched_again = _run_cli(
            [
                "fetch",
                profile_id,
                "--config-file",
                str(config_file),
            ]
        )
        assert fetched_again["status"] == "tombstoned"

    server.shutdown()
    thread.join(timeout=2)


def test_install_item_dry_run_outputs_commands():
    payload = {
        "item": {
            "name": "jq",
            "category": "cli-tool",
            "install": {"type": "brew", "command": "brew install jq"},
            "verification": {"type": "command_exists", "test_command": "jq --version"},
        }
    }
    result = _run_cli(["install-item", "--dry-run"], stdin_payload=payload)
    assert result["success"] is True
    assert result["dry_run"] is True
    assert "install_command" in result


def test_saved_apps_remove_flow():
    with tempfile.TemporaryDirectory(prefix="flux-profile-saved-apps-") as tmp:
        state_file = Path(tmp) / "state.json"
        state_file.write_text(
            json.dumps(
                {
                    "schema_version": "1",
                    "saved_applications": {
                        "slack": {
                            "last_seen_state": "installed",
                            "priority": "optional",
                        },
                        "granola": {
                            "last_seen_state": "missing",
                            "priority": "required",
                        },
                    },
                    "published_profiles": {},
                    "last_exported_at": "",
                }
            )
        )

        result = _run_cli(
            [
                "saved-apps",
                "--state-file",
                str(state_file),
                "--remove",
                "slack",
            ]
        )

        assert result["removed"] == ["slack"]
        names = [row["name"] for row in result["saved_applications"]]
        assert names == ["granola"]


def run_all_tests():
    test_redaction_masks_sensitive_values()
    test_skill_detection_dedupes_name_and_hash()
    test_application_selection_state_buckets()
    test_build_profile_snapshot_respects_app_and_required_selection()
    test_plan_import_filters_incompatible_and_installed_items()
    test_publish_fetch_tombstone_roundtrip()
    test_install_item_dry_run_outputs_commands()
    test_saved_apps_remove_flow()
    print("All profile-manager tests passed")


if __name__ == "__main__":
    run_all_tests()
