#!/usr/bin/env python3
"""Validate built-in Flux skills against repo skill-authoring rules."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from fluxctl_pkg.utils import SESSION_PHASES


FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
FIELD_RE = re.compile(r"^([A-Za-z0-9_-]+):\s*(.*)$")
TRIGGER_HINT_RE = re.compile(
    r"use when|use for|triggers?(?:\s+on)?\s*:?\s*|route here when|run when|invoke when|for /[a-z0-9:_-]+",
    re.IGNORECASE,
)
HEADER_RE = re.compile(r"^##+\s+(.+?)\s*$", re.MULTILINE)
SESSION_PHASE_RE = re.compile(r"session-phase set ([A-Za-z0-9_-]+)")
GOTCHA_EQUIVALENTS = {
    "gotchas",
    "guardrails",
    "critical rules",
    "hard rules",
    "rules",
    "error messages",
    "safety notes",
    "guidelines",
    "product constraints",
}

HARD_LINE_LIMIT = 500
SOFT_LINE_LIMIT = 350


@dataclass
class SkillReport:
    path: Path
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text

    raw = match.group(1)
    body = text[match.end() :]
    data: dict[str, str] = {}
    current_key: str | None = None
    current_lines: list[str] = []

    for line in raw.splitlines():
        field = FIELD_RE.match(line)
        if field and not line.startswith((" ", "\t")):
            if current_key is not None:
                data[current_key] = "\n".join(current_lines).strip().strip('"').strip("'")
            current_key = field.group(1)
            value = field.group(2).strip()
            current_lines = [] if value in {"|", ">", ">-"} else [value]
            continue

        if current_key is not None:
            current_lines.append(line.strip())

    if current_key is not None:
        data[current_key] = "\n".join(current_lines).strip().strip('"').strip("'")

    return data, body


def has_supporting_files(skill_dir: Path) -> bool:
    for name in ("references", "scripts", "assets", "agents"):
        if (skill_dir / name).exists():
            return True
    for pattern in ("*.md",):
        for child in skill_dir.glob(pattern):
            if child.name != "SKILL.md":
                return True
    return False


def body_mentions_supporting_files(body: str) -> bool:
    supporting_hints = (
        "references/",
        "scripts/",
        "assets/",
        "workflow.md",
        "examples.md",
        "questions.md",
        "phases.md",
        "steps.md",
        "linear.md",
        "agents/",
    )
    return any(hint in body for hint in supporting_hints)


def validate_skill(skill_dir: Path) -> SkillReport:
    report = SkillReport(path=skill_dir / "SKILL.md")
    skill_file = report.path
    text = skill_file.read_text()
    lines = text.splitlines()
    frontmatter, body = parse_frontmatter(text)

    if not frontmatter:
        report.errors.append("missing YAML frontmatter")
        return report

    name = frontmatter.get("name", "").strip()
    description = frontmatter.get("description", "").strip()

    if not name:
        report.errors.append("missing frontmatter.name")
    elif name != skill_dir.name:
        report.errors.append(
            f"frontmatter.name '{name}' does not match folder '{skill_dir.name}'"
        )

    if not description:
        report.errors.append("missing frontmatter.description")
    elif not TRIGGER_HINT_RE.search(description):
        report.warnings.append(
            "description is not clearly trigger-oriented; add 'Use when', 'Triggers:', or similar language"
        )

    command_path = None
    if skill_dir.name.startswith("flux-"):
        command_name = skill_dir.name.removeprefix("flux-")
        command_path = ROOT / "commands" / "flux" / f"{command_name}.md"
        if frontmatter.get("user-invocable", "").strip().lower() == "true" and not command_path.exists():
            report.errors.append(
                f"user-invocable skill is missing command file commands/flux/{command_name}.md"
            )

    phases_used = sorted(set(SESSION_PHASE_RE.findall(text)))
    for phase in phases_used:
        if phase not in SESSION_PHASES:
            report.errors.append(
                f"uses unsupported session phase '{phase}' (add it to scripts/fluxctl_pkg/utils.py::SESSION_PHASES)"
            )
    if command_path and command_path.exists() and not phases_used:
        report.errors.append(
            f"command-backed skill is missing session-phase tracking for commands/flux/{command_path.name}"
        )

    if len(lines) > HARD_LINE_LIMIT:
        report.errors.append(
            f"SKILL.md is {len(lines)} lines; keep it at or below {HARD_LINE_LIMIT} and move detail into supporting files"
        )
    headers = {header.strip().lower() for header in HEADER_RE.findall(body)}
    has_files = has_supporting_files(skill_dir)
    has_linked_support = has_files and body_mentions_supporting_files(body)

    if len(lines) > SOFT_LINE_LIMIT and not has_linked_support:
        report.warnings.append(
            f"SKILL.md is {len(lines)} lines without clear progressive disclosure; move detail into references or workflow files and link them from SKILL.md"
        )

    if not headers.intersection(GOTCHA_EQUIVALENTS):
        report.warnings.append("missing `## Gotchas` section")
    if len(lines) > SOFT_LINE_LIMIT and not has_files:
        report.warnings.append(
            "long skill has no supporting files; consider references/, scripts/, assets/, or sibling markdown files"
        )
    elif has_files and not body_mentions_supporting_files(body):
        report.warnings.append(
            "supporting files exist but SKILL.md does not clearly point to them"
        )

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional skill directories to validate. Defaults to skills/*/",
    )
    parser.add_argument(
        "--strict-warnings",
        action="store_true",
        help="Treat warnings as failures.",
    )
    args = parser.parse_args()

    root = ROOT
    skill_dirs = [Path(p).resolve() for p in args.paths] if args.paths else sorted(
        path for path in (root / "skills").iterdir() if path.is_dir()
    )

    reports = [validate_skill(skill_dir) for skill_dir in skill_dirs]

    error_count = sum(len(report.errors) for report in reports)
    warning_count = sum(len(report.warnings) for report in reports)

    for report in reports:
        rel = report.path.relative_to(root)
        if not report.errors and not report.warnings:
            continue
        print(f"{rel}")
        for message in report.errors:
            print(f"  ERROR: {message}")
        for message in report.warnings:
            print(f"  WARN: {message}")

    checked = len(reports)
    print(
        f"Validated {checked} skill(s): {error_count} error(s), {warning_count} warning(s)"
    )

    if error_count:
        return 1
    if args.strict_warnings and warning_count:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
