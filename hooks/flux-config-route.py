#!/usr/bin/env python3
"""
Deterministic route guard for Flux config requests.

Uses UserPromptSubmit to classify config prompts and PreToolUse to enforce
the first meaningful action:
- inspect prompts -> `.flux/bin/fluxctl config list --json`
- edit prompts -> `.flux/bin/fluxctl config edit`
"""

import json
import re
import sys
from pathlib import Path
from typing import Optional


def state_path(session_id: str) -> Path:
    return Path(f"/tmp/flux-config-route-{session_id}.json")


def load_state(session_id: str) -> Optional[dict]:
    path = state_path(session_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def save_state(session_id: str, mode: str) -> None:
    state_path(session_id).write_text(json.dumps({"mode": mode}), encoding="utf-8")


def clear_state(session_id: str) -> None:
    path = state_path(session_id)
    if path.exists():
        path.unlink()


def output_json(data: dict) -> None:
    print(json.dumps(data))
    sys.exit(0)


def output_block(reason: str) -> None:
    print(reason, file=sys.stderr)
    sys.exit(2)


def classify_prompt(prompt: str) -> Optional[str]:
    text = prompt.lower().strip()

    edit_patterns = [
        r"\bedit\s+flux\s+(?:config|settings)\b",
        r"\bopen\s+flux\s+(?:config|settings)\b",
        r"\bchange\s+flux\s+(?:config|settings)\b",
        r"\bupdate\s+flux\s+(?:config|settings)\b",
    ]
    inspect_patterns = [
        r"\bshow\s+my\s+flux\s+config\b",
        r"\bshow\s+flux\s+(?:config|settings)\b",
        r"\bwhat\s+did\s+setup\s+configure\b",
        r"\bshow\s+me\s+(?:the\s+)?flux\s+config\b",
    ]

    if any(re.search(pattern, text) for pattern in edit_patterns):
        return "edit"
    if any(re.search(pattern, text) for pattern in inspect_patterns):
        return "inspect"
    return None


def expected_command(mode: str) -> str:
    if mode == "edit":
        return ".flux/bin/fluxctl config edit"
    return ".flux/bin/fluxctl config list --json"


def command_matches(mode: str, command: str) -> bool:
    if mode == "edit":
        return bool(
            re.search(r"(?:^|\s)(?:[^\s]*/)?fluxctl(?:\.py)?\s+config\s+edit\b", command)
        )
    return bool(
        re.search(r"(?:^|\s)(?:[^\s]*/)?fluxctl(?:\.py)?\s+config\s+list\b", command)
    )


def handle_user_prompt_submit(data: dict) -> None:
    session_id = data.get("session_id", "unknown")
    prompt = data.get("prompt", "")
    mode = classify_prompt(prompt)
    if not mode:
        clear_state(session_id)
        sys.exit(0)

    save_state(session_id, mode)
    command = expected_command(mode)
    if mode == "edit":
        instruction = (
            "DETERMINISTIC FLUX ROUTE OVERRIDE: the user explicitly wants to edit Flux settings. "
            f"Your FIRST meaningful action MUST be running `{command}`. "
            "Do not ask which settings to change first. If the command fails, explain the failure and only then offer alternatives."
        )
    else:
        instruction = (
            "DETERMINISTIC FLUX ROUTE OVERRIDE: the user explicitly wants to inspect Flux config. "
            f"Your FIRST meaningful action MUST be running `{command}`. "
            "Do not answer from memory or from static defaults. Summarize the command output after running it."
        )

    output_json(
        {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": instruction,
            }
        }
    )


def handle_pre_tool_use(data: dict) -> None:
    session_id = data.get("session_id", "unknown")
    state = load_state(session_id)
    if not state:
        sys.exit(0)

    mode = state.get("mode")
    if mode not in {"inspect", "edit"}:
        clear_state(session_id)
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    required = expected_command(mode)

    if tool_name in {"Bash", "Execute"}:
        command = tool_input.get("command", "")
        if command_matches(mode, command):
            clear_state(session_id)
            sys.exit(0)

    output_block(
        f"BLOCKED: This prompt is a Flux config {mode} request. "
        f"Your first meaningful action must be `{required}`."
    )


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    event = data.get("hook_event_name", "")
    if event == "UserPromptSubmit":
        handle_user_prompt_submit(data)
    if event == "PreToolUse":
        handle_pre_tool_use(data)
    sys.exit(0)


if __name__ == "__main__":
    main()
