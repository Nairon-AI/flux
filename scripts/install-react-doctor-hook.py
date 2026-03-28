#!/usr/bin/env python3
"""Configure a React Doctor pre-commit hook for the current repo.

Preference order:
1. Existing Husky setup
2. Existing Lefthook setup
3. Fresh Lefthook setup
4. Native .git/hooks fallback
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

HOOK_RELATIVE_PATH = ".flux/hooks/react-doctor-pre-commit.sh"
HOOK_RUN = f"./{HOOK_RELATIVE_PATH}"
HOOK_SCRIPT = """#!/bin/sh
set -eu

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  exit 0
fi

if ! git diff --cached --name-only --diff-filter=ACMR | grep -Eq '\\.(jsx?|tsx?)$'; then
  exit 0
fi

if git rev-parse --verify HEAD >/dev/null 2>&1; then
  BASE_REF="HEAD"
else
  BASE_REF=$(git hash-object -t tree /dev/null)
fi

if command -v react-doctor >/dev/null 2>&1; then
  exec react-doctor . --diff "$BASE_REF" --fail-on error
fi

if command -v npx >/dev/null 2>&1; then
  exec npx -y react-doctor@latest . --diff "$BASE_REF" --fail-on error
fi

echo "react-doctor is not installed and npx is unavailable." >&2
exit 1
"""

HUSKY_SNIPPET = f'\n# Flux React Doctor\n"{Path(HOOK_RELATIVE_PATH).as_posix()}"\n'
NATIVE_SNIPPET = '\n# Flux React Doctor\n"./.flux/hooks/react-doctor-pre-commit.sh"\n'


def write_json(payload: dict[str, object], exit_code: int = 0) -> None:
    print(json.dumps(payload))
    raise SystemExit(exit_code)


def ensure_git_repo(root: Path) -> None:
    result = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        write_json(
            {
                "success": False,
                "error": "Not a git repository",
                "manager": "none",
                "hook_status": "failed",
            },
            1,
        )


def ensure_hook_script(root: Path) -> Path:
    hook_path = root / HOOK_RELATIVE_PATH
    hook_path.parent.mkdir(parents=True, exist_ok=True)
    hook_path.write_text(HOOK_SCRIPT)
    hook_path.chmod(hook_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return hook_path


def update_lefthook_config(config_path: Path) -> str:
    block = [
        "pre-commit:",
        "  commands:",
        "    react-doctor:",
        f"      run: {HOOK_RUN}",
        "",
    ]

    if not config_path.exists():
        config_path.write_text("\n".join(block))
        return "configured"

    text = config_path.read_text()
    if HOOK_RUN in text or "\n    react-doctor:\n" in text:
        return "already_configured"

    lines = text.splitlines()

    def root_key(line: str) -> bool:
        stripped = line.strip()
        return bool(stripped) and not line.startswith((" ", "\t", "#"))

    pre_idx = next((i for i, line in enumerate(lines) if line.strip() == "pre-commit:"), None)
    if pre_idx is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines.extend(block[:-1])
        config_path.write_text("\n".join(lines) + "\n")
        return "configured"

    end_idx = len(lines)
    for i in range(pre_idx + 1, len(lines)):
        if root_key(lines[i]):
            end_idx = i
            break

    commands_idx = next(
        (i for i in range(pre_idx + 1, end_idx) if lines[i].strip() == "commands:"),
        None,
    )

    if commands_idx is None:
        insert_at = end_idx
        lines[insert_at:insert_at] = [
            "  commands:",
            "    react-doctor:",
            f"      run: {HOOK_RUN}",
        ]
    else:
        insert_at = commands_idx + 1
        while insert_at < end_idx:
            current = lines[insert_at]
            stripped = current.strip()
            if not stripped or stripped.startswith("#"):
                insert_at += 1
                continue
            indent = len(current) - len(current.lstrip(" "))
            if indent >= 4:
                insert_at += 1
                continue
            break
        lines[insert_at:insert_at] = [
            "    react-doctor:",
            f"      run: {HOOK_RUN}",
        ]

    config_path.write_text("\n".join(lines) + "\n")
    return "configured"


def configure_husky(root: Path) -> str:
    husky_dir = root / ".husky"
    pre_commit = husky_dir / "pre-commit"
    husky_dir.mkdir(parents=True, exist_ok=True)

    if pre_commit.exists():
        text = pre_commit.read_text()
        if HOOK_RELATIVE_PATH in text:
            return "already_configured"
    else:
        text = '#!/bin/sh\nset -eu\n. "$(dirname "$0")/_/husky.sh"\n'

    if HOOK_RELATIVE_PATH not in text:
        if not text.endswith("\n"):
            text += "\n"
        text += HUSKY_SNIPPET

    pre_commit.write_text(text)
    pre_commit.chmod(pre_commit.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return "configured"


def configure_native_hook(root: Path) -> str:
    git_dir = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=True,
    ).stdout.strip()
    hook_path = root / git_dir / "hooks" / "pre-commit"
    hook_path.parent.mkdir(parents=True, exist_ok=True)

    if hook_path.exists():
        text = hook_path.read_text()
        if HOOK_RELATIVE_PATH in text:
            return "already_configured"
        if not text.endswith("\n"):
            text += "\n"
        text += NATIVE_SNIPPET
    else:
        text = "#!/bin/sh\nset -eu\n" + NATIVE_SNIPPET

    hook_path.write_text(text)
    hook_path.chmod(hook_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return "configured"


def maybe_install_lefthook(root: Path) -> str:
    if os.environ.get("FLUX_SKIP_LEFTHOOK_INSTALL") == "1":
        return "skipped"

    if shutil.which("lefthook"):
        command = ["lefthook", "install"]
    elif shutil.which("npx"):
        command = ["npx", "-y", "lefthook", "install"]
    else:
        return "unavailable"

    result = subprocess.run(
        command,
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return "installed" if result.returncode == 0 else "failed"


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    ensure_git_repo(root)
    hook_path = ensure_hook_script(root)

    has_husky = (root / ".husky").exists()
    has_lefthook = (root / "lefthook.yml").exists()

    manager = "none"
    hook_status = "failed"
    install_status = "not_needed"

    if has_husky:
        manager = "husky"
        hook_status = configure_husky(root)
    else:
        manager = "lefthook"
        hook_status = update_lefthook_config(root / "lefthook.yml")
        install_status = maybe_install_lefthook(root)
        if install_status in {"failed", "unavailable"}:
            manager = "git-hooks"
            hook_status = configure_native_hook(root)

    write_json(
        {
            "success": hook_status in {"configured", "already_configured"},
            "manager": manager,
            "hook_status": hook_status,
            "install_status": install_status,
            "hook_script": str(hook_path),
            "config_file": str(root / ("lefthook.yml" if manager == "lefthook" else "")),
            "used_existing_lefthook": has_lefthook,
        }
    )


if __name__ == "__main__":
    main()
