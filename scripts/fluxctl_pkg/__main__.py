import argparse

from .utils import (
    EPIC_STATUS, TASK_STATUS, OBJECTIVE_KINDS, SCOPE_MODES,
    TECHNICAL_LEVELS, IMPLEMENTATION_TARGETS, WORKFLOW_STATUSES, PRIME_STATUSES,
    SESSION_PHASES,
)
from .init import cmd_init, cmd_detect, cmd_status, cmd_state_path, cmd_agentmap, cmd_migrate_state
from .config import (
    cmd_config_edit,
    cmd_config_get,
    cmd_config_list,
    cmd_config_set,
    cmd_config_toggle,
    cmd_review_backend,
)
from .architecture import cmd_architecture_status, cmd_architecture_path, cmd_architecture_write
from .epics import (
    cmd_epic_create, cmd_show, cmd_epics, cmd_list, cmd_cat,
    cmd_epic_set_plan, cmd_epic_set_plan_review_status, cmd_epic_set_completion_review_status,
    cmd_epic_set_branch, cmd_epic_set_title, cmd_epic_add_dep, cmd_epic_rm_dep,
    cmd_epic_set_backend, cmd_epic_set_context, cmd_epic_set_workflow,
    cmd_objective_current, cmd_objective_switch, cmd_scope_status, cmd_session_state,
    cmd_artifact_write, cmd_artifact_read, cmd_prime_status, cmd_prime_mark,
    cmd_epic_close, cmd_checkpoint_save, cmd_checkpoint_restore, cmd_checkpoint_delete,
    cmd_validate, cmd_session_phase_get, cmd_session_phase_set,
)
from .tasks import (
    cmd_task_create, cmd_dep_add, cmd_task_set_deps, cmd_tasks,
    cmd_task_set_backend, cmd_task_show_backend,
    cmd_task_set_description, cmd_task_set_acceptance, cmd_task_set_spec,
    cmd_task_reset, cmd_ready, cmd_next, cmd_start, cmd_done, cmd_block,
)
from .ralph import (
    cmd_ralph_pause, cmd_ralph_resume, cmd_ralph_stop, cmd_ralph_status,
    cmd_prep_chat, cmd_rp_windows, cmd_rp_pick_window, cmd_rp_ensure_workspace,
    cmd_rp_builder, cmd_rp_prompt_get, cmd_rp_prompt_set, cmd_rp_select_get,
    cmd_rp_select_add, cmd_rp_chat_send, cmd_rp_prompt_export, cmd_rp_setup_review,
)
from .codex import cmd_codex_check
from .host import cmd_doctor, cmd_env, cmd_version
from .review import cmd_codex_impl_review, cmd_codex_plan_review, cmd_codex_completion_review


def main() -> None:
    parser = argparse.ArgumentParser(
        description="fluxctl - CLI for .flux/ task tracking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = subparsers.add_parser("init", help="Initialize .flux/ directory")
    p_init.add_argument("--json", action="store_true", help="JSON output")
    p_init.set_defaults(func=cmd_init)

    # detect
    p_detect = subparsers.add_parser("detect", help="Check if .flux/ exists")
    p_detect.add_argument("--json", action="store_true", help="JSON output")
    p_detect.set_defaults(func=cmd_detect)

    # status
    p_status = subparsers.add_parser("status", help="Show .flux state and active runs")
    p_status.add_argument("--json", action="store_true", help="JSON output")
    p_status.set_defaults(func=cmd_status)

    # env
    p_env = subparsers.add_parser(
        "env", help="Detect the active host and report Flux runtime/adapter versions"
    )
    p_env.add_argument("--json", action="store_true", help="JSON output")
    p_env.set_defaults(func=cmd_env)

    # doctor
    p_doctor = subparsers.add_parser(
        "doctor", help="Host-aware Flux diagnostics and update guidance"
    )
    p_doctor.add_argument("--json", action="store_true", help="JSON output")
    p_doctor.set_defaults(func=cmd_doctor)

    # version
    p_version = subparsers.add_parser("version", help="Show Flux runtime version")
    p_version.add_argument("--json", action="store_true", help="JSON output")
    p_version.add_argument(
        "--verbose",
        action="store_true",
        help="Include host/runtime diagnostics in JSON output",
    )
    p_version.set_defaults(func=cmd_version)

    # session-state
    p_session_state = subparsers.add_parser(
        "session-state", help="Summarize current workflow routing state"
    )
    p_session_state.add_argument("--json", action="store_true", help="JSON output")
    p_session_state.set_defaults(func=cmd_session_state)

    # session-phase
    p_session_phase = subparsers.add_parser(
        "session-phase", help="Get or set the current session lifecycle phase"
    )
    session_phase_sub = p_session_phase.add_subparsers(
        dest="session_phase_cmd", required=True
    )

    p_sp_get = session_phase_sub.add_parser("get", help="Get current session phase")
    p_sp_get.add_argument("--json", action="store_true", help="JSON output")
    p_sp_get.set_defaults(func=cmd_session_phase_get)

    p_sp_set = session_phase_sub.add_parser("set", help="Set current session phase")
    p_sp_set.add_argument("phase", choices=SESSION_PHASES, help="Phase to set")
    p_sp_set.add_argument("--detail", help="Optional detail string")
    p_sp_set.add_argument("--epic-id", help="Associated epic ID")
    p_sp_set.add_argument("--task-id", help="Associated task ID")
    p_sp_set.add_argument("--json", action="store_true", help="JSON output")
    p_sp_set.set_defaults(func=cmd_session_phase_set)

    # prime-status
    p_prime_status = subparsers.add_parser(
        "prime-status", help="Show whether this repository has been primed"
    )
    p_prime_status.add_argument("--json", action="store_true", help="JSON output")
    p_prime_status.set_defaults(func=cmd_prime_status)

    # prime-mark
    p_prime_mark = subparsers.add_parser(
        "prime-mark", help="Internal helper to persist prime-state metadata"
    )
    p_prime_mark.add_argument(
        "--status", required=True, choices=PRIME_STATUSES, help="Prime status"
    )
    p_prime_mark.add_argument("--version", help="Flux version associated with this prime run")
    p_prime_mark.add_argument("--json", action="store_true", help="JSON output")
    p_prime_mark.set_defaults(func=cmd_prime_mark)

    # scope-status
    p_scope_status = subparsers.add_parser(
        "scope-status", help="Show current scoped workflow progress"
    )
    p_scope_status.add_argument("--objective", help="Epic ID (defaults to active objective)")
    p_scope_status.add_argument("--json", action="store_true", help="JSON output")
    p_scope_status.set_defaults(func=cmd_scope_status)

    # config
    p_config = subparsers.add_parser("config", help="Config commands")
    config_sub = p_config.add_subparsers(dest="config_cmd", required=True)

    p_config_get = config_sub.add_parser("get", help="Get config value")
    p_config_get.add_argument("key", help="Config key (e.g., review.backend)")
    p_config_get.add_argument("--json", action="store_true", help="JSON output")
    p_config_get.set_defaults(func=cmd_config_get)

    p_config_set = config_sub.add_parser("set", help="Set config value")
    p_config_set.add_argument("key", help="Config key (e.g., review.backend)")
    p_config_set.add_argument("value", help="Config value")
    p_config_set.add_argument("--json", action="store_true", help="JSON output")
    p_config_set.set_defaults(func=cmd_config_set)

    p_config_list = config_sub.add_parser("list", help="List current config")
    p_config_list.add_argument("--json", action="store_true", help="JSON output")
    p_config_list.set_defaults(func=cmd_config_list)

    p_config_toggle = config_sub.add_parser("toggle", help="Toggle boolean config value")
    p_config_toggle.add_argument("key", help="Boolean config key (e.g., planSync.enabled)")
    p_config_toggle.add_argument("--json", action="store_true", help="JSON output")
    p_config_toggle.set_defaults(func=cmd_config_toggle)

    p_config_edit = config_sub.add_parser("edit", help="Open config file in an editor")
    p_config_edit.add_argument(
        "--editor",
        help="Editor command override (defaults to $VISUAL/$EDITOR)",
    )
    p_config_edit.add_argument("--json", action="store_true", help="JSON output")
    p_config_edit.set_defaults(func=cmd_config_edit)

    # review-backend (helper for skills)
    p_review_backend = subparsers.add_parser(
        "review-backend", help="Get review backend (ASK if not configured)"
    )
    p_review_backend.add_argument("--json", action="store_true", help="JSON output")
    p_review_backend.set_defaults(func=cmd_review_backend)

    # architecture
    p_architecture = subparsers.add_parser(
        "architecture", help="Canonical architecture diagram commands"
    )
    architecture_sub = p_architecture.add_subparsers(dest="architecture_cmd", required=True)

    p_architecture_status = architecture_sub.add_parser("status", help="Show architecture status")
    p_architecture_status.add_argument("--json", action="store_true", help="JSON output")
    p_architecture_status.set_defaults(func=cmd_architecture_status)

    p_architecture_path = architecture_sub.add_parser("path", help="Show architecture file path")
    p_architecture_path.add_argument("--json", action="store_true", help="JSON output")
    p_architecture_path.set_defaults(func=cmd_architecture_path)

    p_architecture_write = architecture_sub.add_parser("write", help="Write architecture diagram")
    p_architecture_write.add_argument(
        "--file", required=True, help="Markdown file with diagram content (use '-' for stdin)"
    )
    p_architecture_write.add_argument(
        "--status",
        choices=["missing", "seeded", "current", "needs_update"],
        help="Architecture freshness state",
    )
    p_architecture_write.add_argument("--summary", help="Short summary of the architecture change")
    p_architecture_write.add_argument("--source", help="Command or workflow that updated it")
    p_architecture_write.add_argument("--json", action="store_true", help="JSON output")
    p_architecture_write.set_defaults(func=cmd_architecture_write)

    # epic create
    p_epic = subparsers.add_parser("epic", help="Epic commands")
    epic_sub = p_epic.add_subparsers(dest="epic_cmd", required=True)

    p_epic_create = epic_sub.add_parser("create", help="Create new epic")
    p_epic_create.add_argument("--title", required=True, help="Epic title")
    p_epic_create.add_argument("--branch", help="Branch name to store on epic")
    p_epic_create.add_argument(
        "--kind",
        choices=OBJECTIVE_KINDS,
        default="feature",
        help="Objective kind",
    )
    p_epic_create.add_argument(
        "--scope-mode",
        choices=SCOPE_MODES,
        help="Scope mode (defaults to workflow.defaultScopeMode config)",
    )
    p_epic_create.add_argument(
        "--technical-level",
        choices=TECHNICAL_LEVELS,
        help="Technical level (defaults to workflow.technicalLevel config)",
    )
    p_epic_create.add_argument(
        "--implementation-target",
        choices=IMPLEMENTATION_TARGETS,
        help="Implementation target (defaults to workflow.defaultImplementationTarget config)",
    )
    p_epic_create.add_argument("--json", action="store_true", help="JSON output")
    p_epic_create.set_defaults(func=cmd_epic_create)

    p_epic_set_context = epic_sub.add_parser("set-context", help="Set epic workflow context")
    p_epic_set_context.add_argument("id", help="Epic ID (e.g., fn-1, fn-1-add-auth)")
    p_epic_set_context.add_argument("--kind", choices=OBJECTIVE_KINDS, help="Objective kind")
    p_epic_set_context.add_argument("--scope-mode", choices=SCOPE_MODES, help="Scope mode")
    p_epic_set_context.add_argument(
        "--technical-level", choices=TECHNICAL_LEVELS, help="Technical level"
    )
    p_epic_set_context.add_argument(
        "--implementation-target",
        choices=IMPLEMENTATION_TARGETS,
        help="Implementation target",
    )
    p_epic_set_context.add_argument(
        "--activate", action="store_true", help="Make this the active objective"
    )
    p_epic_set_context.add_argument("--json", action="store_true", help="JSON output")
    p_epic_set_context.set_defaults(func=cmd_epic_set_context)

    p_epic_set_workflow = epic_sub.add_parser("set-workflow", help="Set epic workflow state")
    p_epic_set_workflow.add_argument("id", help="Epic ID (e.g., fn-1, fn-1-add-auth)")
    p_epic_set_workflow.add_argument("--phase", help="Workflow phase")
    p_epic_set_workflow.add_argument("--step", help="Workflow step")
    p_epic_set_workflow.add_argument(
        "--status", choices=WORKFLOW_STATUSES, help="Workflow status"
    )
    p_epic_set_workflow.add_argument("--summary", help="Workflow summary")
    p_epic_set_workflow.add_argument("--next-action", help="Suggested next action")
    p_epic_set_workflow.add_argument(
        "--open-question",
        action="append",
        help="Open question to append (repeatable)",
    )
    p_epic_set_workflow.add_argument(
        "--decision",
        action="append",
        help="Resolved decision to append (repeatable)",
    )
    p_epic_set_workflow.add_argument(
        "--clear-open-questions", action="store_true", help="Clear open questions first"
    )
    p_epic_set_workflow.add_argument(
        "--clear-decisions", action="store_true", help="Clear resolved decisions first"
    )
    p_epic_set_workflow.add_argument(
        "--activate", action="store_true", help="Make this the active objective"
    )
    p_epic_set_workflow.add_argument("--json", action="store_true", help="JSON output")
    p_epic_set_workflow.set_defaults(func=cmd_epic_set_workflow)

    p_epic_set_plan = epic_sub.add_parser("set-plan", help="Set epic spec from file")
    p_epic_set_plan.add_argument("id", help="Epic ID (e.g., fn-1, fn-1-add-auth)")
    p_epic_set_plan.add_argument("--file", required=True, help="Markdown file (use '-' for stdin)")
    p_epic_set_plan.add_argument("--json", action="store_true", help="JSON output")
    p_epic_set_plan.set_defaults(func=cmd_epic_set_plan)

    p_epic_set_review = epic_sub.add_parser(
        "set-plan-review-status", help="Set plan review status"
    )
    p_epic_set_review.add_argument("id", help="Epic ID (e.g., fn-1, fn-1-add-auth)")
    p_epic_set_review.add_argument(
        "--status",
        required=True,
        choices=["ship", "needs_work", "unknown"],
        help="Plan review status",
    )
    p_epic_set_review.add_argument("--json", action="store_true", help="JSON output")
    p_epic_set_review.set_defaults(func=cmd_epic_set_plan_review_status)

    p_epic_set_completion_review = epic_sub.add_parser(
        "set-completion-review-status", help="Set completion review status"
    )
    p_epic_set_completion_review.add_argument("id", help="Epic ID (e.g., fn-1, fn-1-add-auth)")
    p_epic_set_completion_review.add_argument(
        "--status",
        required=True,
        choices=["ship", "needs_work", "unknown"],
        help="Completion review status",
    )
    p_epic_set_completion_review.add_argument("--json", action="store_true", help="JSON output")
    p_epic_set_completion_review.set_defaults(func=cmd_epic_set_completion_review_status)

    p_epic_set_branch = epic_sub.add_parser("set-branch", help="Set epic branch name")
    p_epic_set_branch.add_argument("id", help="Epic ID (e.g., fn-1, fn-1-add-auth)")
    p_epic_set_branch.add_argument("--branch", required=True, help="Branch name")
    p_epic_set_branch.add_argument("--json", action="store_true", help="JSON output")
    p_epic_set_branch.set_defaults(func=cmd_epic_set_branch)

    p_epic_set_title = epic_sub.add_parser(
        "set-title", help="Rename epic by setting a new title (updates slug)"
    )
    p_epic_set_title.add_argument("id", help="Epic ID (e.g., fn-1, fn-1-add-auth)")
    p_epic_set_title.add_argument("--title", required=True, help="New title for the epic")
    p_epic_set_title.add_argument("--json", action="store_true", help="JSON output")
    p_epic_set_title.set_defaults(func=cmd_epic_set_title)

    p_epic_close = epic_sub.add_parser("close", help="Close epic")
    p_epic_close.add_argument("id", help="Epic ID (e.g., fn-1, fn-1-add-auth)")
    p_epic_close.add_argument("--json", action="store_true", help="JSON output")
    p_epic_close.set_defaults(func=cmd_epic_close)

    p_epic_add_dep = epic_sub.add_parser("add-dep", help="Add epic-level dependency")
    p_epic_add_dep.add_argument("epic", help="Epic ID")
    p_epic_add_dep.add_argument("depends_on", help="Epic ID to depend on")
    p_epic_add_dep.add_argument("--json", action="store_true", help="JSON output")
    p_epic_add_dep.set_defaults(func=cmd_epic_add_dep)

    p_epic_rm_dep = epic_sub.add_parser("rm-dep", help="Remove epic-level dependency")
    p_epic_rm_dep.add_argument("epic", help="Epic ID")
    p_epic_rm_dep.add_argument("depends_on", help="Epic ID to remove from deps")
    p_epic_rm_dep.add_argument("--json", action="store_true", help="JSON output")
    p_epic_rm_dep.set_defaults(func=cmd_epic_rm_dep)

    p_epic_set_backend = epic_sub.add_parser(
        "set-backend", help="Set default backend specs for impl/review/sync"
    )
    p_epic_set_backend.add_argument("id", help="Epic ID (e.g., fn-1, fn-1-add-auth)")
    p_epic_set_backend.add_argument(
        "--impl", help="Default impl backend spec (e.g., 'codex:gpt-5.3-codex')"
    )
    p_epic_set_backend.add_argument(
        "--review", help="Default review backend spec (e.g., 'claude:opus')"
    )
    p_epic_set_backend.add_argument(
        "--sync", help="Default sync backend spec (e.g., 'claude:haiku')"
    )
    p_epic_set_backend.add_argument("--json", action="store_true", help="JSON output")
    p_epic_set_backend.set_defaults(func=cmd_epic_set_backend)

    # task create
    p_task = subparsers.add_parser("task", help="Task commands")
    task_sub = p_task.add_subparsers(dest="task_cmd", required=True)

    p_task_create = task_sub.add_parser("create", help="Create new task")
    p_task_create.add_argument("--epic", required=True, help="Epic ID (e.g., fn-1, fn-1-add-auth)")
    p_task_create.add_argument("--title", required=True, help="Task title")
    p_task_create.add_argument("--deps", help="Comma-separated dependency IDs")
    p_task_create.add_argument(
        "--acceptance-file", help="Markdown file with acceptance criteria"
    )
    p_task_create.add_argument(
        "--priority", type=int, help="Priority (lower = earlier)"
    )
    p_task_create.add_argument("--json", action="store_true", help="JSON output")
    p_task_create.set_defaults(func=cmd_task_create)

    p_task_desc = task_sub.add_parser("set-description", help="Set task description")
    p_task_desc.add_argument("id", help="Task ID (e.g., fn-1.2, fn-1-add-auth.2)")
    p_task_desc.add_argument("--file", required=True, help="Markdown file (use '-' for stdin)")
    p_task_desc.add_argument("--json", action="store_true", help="JSON output")
    p_task_desc.set_defaults(func=cmd_task_set_description)

    p_task_acc = task_sub.add_parser("set-acceptance", help="Set task acceptance")
    p_task_acc.add_argument("id", help="Task ID (e.g., fn-1.2, fn-1-add-auth.2)")
    p_task_acc.add_argument("--file", required=True, help="Markdown file (use '-' for stdin)")
    p_task_acc.add_argument("--json", action="store_true", help="JSON output")
    p_task_acc.set_defaults(func=cmd_task_set_acceptance)

    p_task_set_spec = task_sub.add_parser(
        "set-spec", help="Set task spec (full file or sections)"
    )
    p_task_set_spec.add_argument("id", help="Task ID (e.g., fn-1.2, fn-1-add-auth.2)")
    p_task_set_spec.add_argument(
        "--file", help="Full spec file (use '-' for stdin) - replaces entire spec"
    )
    p_task_set_spec.add_argument(
        "--description", help="Description section file (use '-' for stdin)"
    )
    p_task_set_spec.add_argument(
        "--acceptance", help="Acceptance section file (use '-' for stdin)"
    )
    p_task_set_spec.add_argument("--json", action="store_true", help="JSON output")
    p_task_set_spec.set_defaults(func=cmd_task_set_spec)

    p_task_reset = task_sub.add_parser("reset", help="Reset task to todo")
    p_task_reset.add_argument("task_id", help="Task ID (e.g., fn-1.2, fn-1-add-auth.2)")
    p_task_reset.add_argument(
        "--cascade", action="store_true", help="Also reset dependent tasks (same epic)"
    )
    p_task_reset.add_argument("--json", action="store_true", help="JSON output")
    p_task_reset.set_defaults(func=cmd_task_reset)

    p_task_set_backend = task_sub.add_parser(
        "set-backend", help="Set backend specs for impl/review/sync"
    )
    p_task_set_backend.add_argument("id", help="Task ID (e.g., fn-1.2, fn-1-add-auth.2)")
    p_task_set_backend.add_argument(
        "--impl", help="Impl backend spec (e.g., 'codex:gpt-5.3-codex')"
    )
    p_task_set_backend.add_argument(
        "--review", help="Review backend spec (e.g., 'claude:opus')"
    )
    p_task_set_backend.add_argument(
        "--sync", help="Sync backend spec (e.g., 'claude:haiku')"
    )
    p_task_set_backend.add_argument("--json", action="store_true", help="JSON output")
    p_task_set_backend.set_defaults(func=cmd_task_set_backend)

    p_task_show_backend = task_sub.add_parser(
        "show-backend", help="Show effective backend specs (task + epic levels)"
    )
    p_task_show_backend.add_argument("id", help="Task ID (e.g., fn-1.2, fn-1-add-auth.2)")
    p_task_show_backend.add_argument("--json", action="store_true", help="JSON output")
    p_task_show_backend.set_defaults(func=cmd_task_show_backend)

    p_task_set_deps = task_sub.add_parser(
        "set-deps", help="Set task dependencies (comma-separated)"
    )
    p_task_set_deps.add_argument("task_id", help="Task ID (e.g., fn-1.2, fn-1-add-auth.2)")
    p_task_set_deps.add_argument(
        "--deps", required=True, help="Comma-separated dependency IDs (e.g., fn-1-add-auth.1,fn-1-add-auth.2)"
    )
    p_task_set_deps.add_argument("--json", action="store_true", help="JSON output")
    p_task_set_deps.set_defaults(func=cmd_task_set_deps)

    # dep add
    p_dep = subparsers.add_parser("dep", help="Dependency commands")
    dep_sub = p_dep.add_subparsers(dest="dep_cmd", required=True)

    p_dep_add = dep_sub.add_parser("add", help="Add dependency")
    p_dep_add.add_argument("task", help="Task ID (e.g., fn-1.2, fn-1-add-auth.2)")
    p_dep_add.add_argument("depends_on", help="Dependency task ID (e.g., fn-1.1, fn-1-add-auth.1)")
    p_dep_add.add_argument("--json", action="store_true", help="JSON output")
    p_dep_add.set_defaults(func=cmd_dep_add)

    # show
    p_show = subparsers.add_parser("show", help="Show epic or task")
    p_show.add_argument("id", help="Epic or task ID (e.g., fn-1-add-auth, fn-1-add-auth.2)")
    p_show.add_argument("--json", action="store_true", help="JSON output")
    p_show.set_defaults(func=cmd_show)

    # objective
    p_objective = subparsers.add_parser("objective", help="Objective commands")
    objective_sub = p_objective.add_subparsers(dest="objective_cmd", required=True)

    p_objective_current = objective_sub.add_parser("current", help="Show active objective")
    p_objective_current.add_argument("--json", action="store_true", help="JSON output")
    p_objective_current.set_defaults(func=cmd_objective_current)

    p_objective_switch = objective_sub.add_parser("switch", help="Switch active objective")
    p_objective_switch.add_argument("id", help="Epic ID (e.g., fn-1-add-auth)")
    p_objective_switch.add_argument("--json", action="store_true", help="JSON output")
    p_objective_switch.set_defaults(func=cmd_objective_switch)

    # artifact
    p_artifact = subparsers.add_parser("artifact", help="Workflow artifact commands")
    artifact_sub = p_artifact.add_subparsers(dest="artifact_cmd", required=True)

    p_artifact_write = artifact_sub.add_parser("write", help="Write phase artifact")
    p_artifact_write.add_argument("id", help="Epic ID (e.g., fn-1-add-auth)")
    p_artifact_write.add_argument("--phase", required=True, help="Workflow phase")
    p_artifact_write.add_argument("--file", required=True, help="Markdown file (use '-' for stdin)")
    p_artifact_write.add_argument(
        "--activate", action="store_true", help="Make this the active objective"
    )
    p_artifact_write.add_argument("--json", action="store_true", help="JSON output")
    p_artifact_write.set_defaults(func=cmd_artifact_write)

    p_artifact_read = artifact_sub.add_parser("read", help="Read phase artifact")
    p_artifact_read.add_argument("id", help="Epic ID (e.g., fn-1-add-auth)")
    p_artifact_read.add_argument("--phase", required=True, help="Workflow phase")
    p_artifact_read.add_argument("--json", action="store_true", help="JSON output")
    p_artifact_read.set_defaults(func=cmd_artifact_read)

    # epics
    p_epics = subparsers.add_parser("epics", help="List all epics")
    p_epics.add_argument("--json", action="store_true", help="JSON output")
    p_epics.set_defaults(func=cmd_epics)

    # tasks
    p_tasks = subparsers.add_parser("tasks", help="List tasks")
    p_tasks.add_argument("--epic", help="Filter by epic ID (e.g., fn-1, fn-1-add-auth)")
    p_tasks.add_argument(
        "--status",
        choices=["todo", "in_progress", "blocked", "done"],
        help="Filter by status",
    )
    p_tasks.add_argument("--json", action="store_true", help="JSON output")
    p_tasks.set_defaults(func=cmd_tasks)

    # list
    p_list = subparsers.add_parser("list", help="List all epics and tasks")
    p_list.add_argument("--json", action="store_true", help="JSON output")
    p_list.set_defaults(func=cmd_list)

    # cat
    p_cat = subparsers.add_parser("cat", help="Print spec markdown")
    p_cat.add_argument("id", help="Epic or task ID (e.g., fn-1-add-auth, fn-1-add-auth.2)")
    p_cat.set_defaults(func=cmd_cat)

    # ready
    p_ready = subparsers.add_parser("ready", help="List ready tasks")
    p_ready.add_argument("--epic", required=True, help="Epic ID (e.g., fn-1, fn-1-add-auth)")
    p_ready.add_argument("--json", action="store_true", help="JSON output")
    p_ready.set_defaults(func=cmd_ready)

    # next
    p_next = subparsers.add_parser("next", help="Select next plan/work unit")
    p_next.add_argument("--epics-file", help="JSON file with ordered epic list")
    p_next.add_argument(
        "--require-plan-review",
        action="store_true",
        help="Require plan review before work",
    )
    p_next.add_argument(
        "--require-completion-review",
        action="store_true",
        help="Require completion review when all tasks done",
    )
    p_next.add_argument("--json", action="store_true", help="JSON output")
    p_next.set_defaults(func=cmd_next)

    # start
    p_start = subparsers.add_parser("start", help="Start task")
    p_start.add_argument("id", help="Task ID (e.g., fn-1.2, fn-1-add-auth.2)")
    p_start.add_argument(
        "--force", action="store_true", help="Skip status/dependency/claim checks"
    )
    p_start.add_argument("--note", help="Claim note (e.g., reason for taking over)")
    p_start.add_argument("--json", action="store_true", help="JSON output")
    p_start.set_defaults(func=cmd_start)

    # done
    p_done = subparsers.add_parser("done", help="Complete task")
    p_done.add_argument("id", help="Task ID (e.g., fn-1.2, fn-1-add-auth.2)")
    p_done.add_argument("--summary-file", help="Done summary markdown file")
    p_done.add_argument("--summary", help="Done summary (inline text)")
    p_done.add_argument("--evidence-json", help="Evidence JSON file")
    p_done.add_argument("--evidence", help="Evidence JSON (inline string)")
    p_done.add_argument("--force", action="store_true", help="Skip status checks")
    p_done.add_argument("--json", action="store_true", help="JSON output")
    p_done.set_defaults(func=cmd_done)

    # block
    p_block = subparsers.add_parser("block", help="Block task with reason")
    p_block.add_argument("id", help="Task ID (e.g., fn-1.2, fn-1-add-auth.2)")
    p_block.add_argument(
        "--reason-file", required=True, help="Markdown file with block reason"
    )
    p_block.add_argument("--json", action="store_true", help="JSON output")
    p_block.set_defaults(func=cmd_block)

    # state-path
    p_state_path = subparsers.add_parser(
        "state-path", help="Show resolved state directory path"
    )
    p_state_path.add_argument("--task", help="Task ID to show state file path for")
    p_state_path.add_argument("--json", action="store_true", help="JSON output")
    p_state_path.set_defaults(func=cmd_state_path)

    # agentmap
    p_agentmap = subparsers.add_parser(
        "agentmap", help="Generate or inspect an agentmap artifact"
    )
    p_agentmap.add_argument(
        "dir",
        nargs="?",
        default=".",
        help="Directory to map (defaults to current directory)",
    )
    p_agentmap.add_argument(
        "--out",
        help="Write YAML to a specific file path",
    )
    p_agentmap.add_argument(
        "--write",
        action="store_true",
        help="Write to .flux/context/agentmap.yaml",
    )
    p_agentmap.add_argument(
        "--check",
        action="store_true",
        help="Check built-in agentmap availability",
    )
    p_agentmap.add_argument(
        "--filter",
        action="append",
        default=[],
        help="Filter pattern to include (repeatable)",
    )
    p_agentmap.add_argument(
        "--ignore",
        action="append",
        default=[],
        help="Ignore pattern to exclude (repeatable)",
    )
    p_agentmap.add_argument("--json", action="store_true", help="JSON output")
    p_agentmap.set_defaults(func=cmd_agentmap)

    # migrate-state
    p_migrate = subparsers.add_parser(
        "migrate-state", help="Migrate runtime state from definition files to state-dir"
    )
    p_migrate.add_argument(
        "--clean",
        action="store_true",
        help="Remove runtime fields from definition files after migration",
    )
    p_migrate.add_argument("--json", action="store_true", help="JSON output")
    p_migrate.set_defaults(func=cmd_migrate_state)

    # validate
    p_validate = subparsers.add_parser("validate", help="Validate epic or all")
    p_validate.add_argument("--epic", help="Epic ID (e.g., fn-1, fn-1-add-auth)")
    p_validate.add_argument(
        "--all", action="store_true", help="Validate all epics and tasks"
    )
    p_validate.add_argument("--json", action="store_true", help="JSON output")
    p_validate.set_defaults(func=cmd_validate)

    # checkpoint
    p_checkpoint = subparsers.add_parser("checkpoint", help="Checkpoint commands")
    checkpoint_sub = p_checkpoint.add_subparsers(dest="checkpoint_cmd", required=True)

    p_checkpoint_save = checkpoint_sub.add_parser(
        "save", help="Save epic state to checkpoint"
    )
    p_checkpoint_save.add_argument("--epic", required=True, help="Epic ID (e.g., fn-1, fn-1-add-auth)")
    p_checkpoint_save.add_argument("--json", action="store_true", help="JSON output")
    p_checkpoint_save.set_defaults(func=cmd_checkpoint_save)

    p_checkpoint_restore = checkpoint_sub.add_parser(
        "restore", help="Restore epic state from checkpoint"
    )
    p_checkpoint_restore.add_argument("--epic", required=True, help="Epic ID (e.g., fn-1, fn-1-add-auth)")
    p_checkpoint_restore.add_argument("--json", action="store_true", help="JSON output")
    p_checkpoint_restore.set_defaults(func=cmd_checkpoint_restore)

    p_checkpoint_delete = checkpoint_sub.add_parser(
        "delete", help="Delete checkpoint for epic"
    )
    p_checkpoint_delete.add_argument("--epic", required=True, help="Epic ID (e.g., fn-1, fn-1-add-auth)")
    p_checkpoint_delete.add_argument("--json", action="store_true", help="JSON output")
    p_checkpoint_delete.set_defaults(func=cmd_checkpoint_delete)

    # prep-chat (for rp-cli chat_send JSON escaping)
    p_prep = subparsers.add_parser(
        "prep-chat", help="Prepare JSON for rp-cli chat_send"
    )
    p_prep.add_argument(
        "id", nargs="?", help="(ignored) Epic/task ID for compatibility"
    )
    p_prep.add_argument(
        "--message-file", required=True, help="File containing message text"
    )
    p_prep.add_argument(
        "--mode", default="chat", choices=["chat", "ask"], help="Chat mode"
    )
    p_prep.add_argument("--new-chat", action="store_true", help="Start new chat")
    p_prep.add_argument("--chat-name", help="Name for new chat")
    p_prep.add_argument(
        "--selected-paths", nargs="*", help="Files to include in context"
    )
    p_prep.add_argument("--output", "-o", help="Output file (default: stdout)")
    p_prep.set_defaults(func=cmd_prep_chat)

    # ralph (Ralph run control)
    p_ralph = subparsers.add_parser("ralph", help="Ralph run control commands")
    ralph_sub = p_ralph.add_subparsers(dest="ralph_cmd", required=True)

    p_ralph_pause = ralph_sub.add_parser("pause", help="Pause a Ralph run")
    p_ralph_pause.add_argument("--run", help="Run ID (auto-detect if single)")
    p_ralph_pause.add_argument("--json", action="store_true", help="JSON output")
    p_ralph_pause.set_defaults(func=cmd_ralph_pause)

    p_ralph_resume = ralph_sub.add_parser("resume", help="Resume a paused Ralph run")
    p_ralph_resume.add_argument("--run", help="Run ID (auto-detect if single)")
    p_ralph_resume.add_argument("--json", action="store_true", help="JSON output")
    p_ralph_resume.set_defaults(func=cmd_ralph_resume)

    p_ralph_stop = ralph_sub.add_parser("stop", help="Request a Ralph run to stop")
    p_ralph_stop.add_argument("--run", help="Run ID (auto-detect if single)")
    p_ralph_stop.add_argument("--json", action="store_true", help="JSON output")
    p_ralph_stop.set_defaults(func=cmd_ralph_stop)

    p_ralph_status = ralph_sub.add_parser("status", help="Show Ralph run status")
    p_ralph_status.add_argument("--run", help="Run ID (auto-detect if single)")
    p_ralph_status.add_argument("--json", action="store_true", help="JSON output")
    p_ralph_status.set_defaults(func=cmd_ralph_status)

    # rp (RepoPrompt wrappers)
    p_rp = subparsers.add_parser("rp", help="RepoPrompt helpers")
    rp_sub = p_rp.add_subparsers(dest="rp_cmd", required=True)

    p_rp_windows = rp_sub.add_parser(
        "windows", help="List RepoPrompt windows (raw JSON)"
    )
    p_rp_windows.add_argument("--json", action="store_true", help="JSON output (raw)")
    p_rp_windows.set_defaults(func=cmd_rp_windows)

    p_rp_pick = rp_sub.add_parser("pick-window", help="Pick window by repo root")
    p_rp_pick.add_argument("--repo-root", required=True, help="Repo root path")
    p_rp_pick.add_argument("--json", action="store_true", help="JSON output")
    p_rp_pick.set_defaults(func=cmd_rp_pick_window)

    p_rp_ws = rp_sub.add_parser(
        "ensure-workspace", help="Ensure workspace and switch window"
    )
    p_rp_ws.add_argument("--window", type=int, required=True, help="Window id")
    p_rp_ws.add_argument("--repo-root", required=True, help="Repo root path")
    p_rp_ws.set_defaults(func=cmd_rp_ensure_workspace)

    p_rp_builder = rp_sub.add_parser("builder", help="Run builder and return tab")
    p_rp_builder.add_argument("--window", type=int, required=True, help="Window id")
    p_rp_builder.add_argument("--summary", required=True, help="Builder summary")
    p_rp_builder.add_argument(
        "--response-type",
        dest="response_type",
        choices=["review", "plan", "question", "clarify"],
        help="Builder response type (requires RP 1.6.0+)",
    )
    p_rp_builder.add_argument("--json", action="store_true", help="JSON output")
    p_rp_builder.set_defaults(func=cmd_rp_builder)

    p_rp_prompt_get = rp_sub.add_parser("prompt-get", help="Get current prompt")
    p_rp_prompt_get.add_argument("--window", type=int, required=True, help="Window id")
    p_rp_prompt_get.add_argument("--tab", required=True, help="Tab id or name")
    p_rp_prompt_get.set_defaults(func=cmd_rp_prompt_get)

    p_rp_prompt_set = rp_sub.add_parser("prompt-set", help="Set current prompt")
    p_rp_prompt_set.add_argument("--window", type=int, required=True, help="Window id")
    p_rp_prompt_set.add_argument("--tab", required=True, help="Tab id or name")
    p_rp_prompt_set.add_argument("--message-file", required=True, help="Message file")
    p_rp_prompt_set.set_defaults(func=cmd_rp_prompt_set)

    p_rp_select_get = rp_sub.add_parser("select-get", help="Get selection")
    p_rp_select_get.add_argument("--window", type=int, required=True, help="Window id")
    p_rp_select_get.add_argument("--tab", required=True, help="Tab id or name")
    p_rp_select_get.set_defaults(func=cmd_rp_select_get)

    p_rp_select_add = rp_sub.add_parser("select-add", help="Add files to selection")
    p_rp_select_add.add_argument("--window", type=int, required=True, help="Window id")
    p_rp_select_add.add_argument("--tab", required=True, help="Tab id or name")
    p_rp_select_add.add_argument("paths", nargs="+", help="Paths to add")
    p_rp_select_add.set_defaults(func=cmd_rp_select_add)

    p_rp_chat = rp_sub.add_parser("chat-send", help="Send chat via rp-cli")
    p_rp_chat.add_argument("--window", type=int, required=True, help="Window id")
    p_rp_chat.add_argument("--tab", required=True, help="Tab id or name")
    p_rp_chat.add_argument("--message-file", required=True, help="Message file")
    p_rp_chat.add_argument("--new-chat", action="store_true", help="Start new chat")
    p_rp_chat.add_argument("--chat-name", help="Chat name (with --new-chat)")
    p_rp_chat.add_argument(
        "--chat-id",
        dest="chat_id",
        help="Continue specific chat by ID (RP 1.6.0+)",
    )
    p_rp_chat.add_argument(
        "--mode",
        choices=["chat", "review", "plan", "edit"],
        default="chat",
        help="Chat mode (default: chat)",
    )
    p_rp_chat.add_argument(
        "--selected-paths", nargs="*", help="Override selected paths"
    )
    p_rp_chat.add_argument(
        "--json", action="store_true", help="JSON output (no review text)"
    )
    p_rp_chat.set_defaults(func=cmd_rp_chat_send)

    p_rp_export = rp_sub.add_parser("prompt-export", help="Export prompt to file")
    p_rp_export.add_argument("--window", type=int, required=True, help="Window id")
    p_rp_export.add_argument("--tab", required=True, help="Tab id or name")
    p_rp_export.add_argument("--out", required=True, help="Output file")
    p_rp_export.set_defaults(func=cmd_rp_prompt_export)

    p_rp_setup = rp_sub.add_parser(
        "setup-review", help="Atomic: pick-window + workspace + builder"
    )
    p_rp_setup.add_argument("--repo-root", required=True, help="Repo root path")
    p_rp_setup.add_argument("--summary", required=True, help="Builder summary/instructions")
    p_rp_setup.add_argument(
        "--response-type",
        dest="response_type",
        choices=["review"],
        help="Use builder review mode (requires RP 1.6.0+)",
    )
    p_rp_setup.add_argument(
        "--create",
        action="store_true",
        help="Create new RP window if none matches (requires RP 1.5.68+)",
    )
    p_rp_setup.add_argument("--json", action="store_true", help="JSON output")
    p_rp_setup.set_defaults(func=cmd_rp_setup_review)

    # codex (Codex CLI wrappers)
    p_codex = subparsers.add_parser("codex", help="Codex CLI helpers")
    codex_sub = p_codex.add_subparsers(dest="codex_cmd", required=True)

    p_codex_check = codex_sub.add_parser("check", help="Check codex availability")
    p_codex_check.add_argument("--json", action="store_true", help="JSON output")
    p_codex_check.set_defaults(func=cmd_codex_check)

    p_codex_impl = codex_sub.add_parser("impl-review", help="Implementation review")
    p_codex_impl.add_argument(
        "task",
        nargs="?",
        default=None,
        help="Task ID (e.g., fn-1.2, fn-1-add-auth.2), optional for standalone",
    )
    p_codex_impl.add_argument("--base", required=True, help="Base branch for diff")
    p_codex_impl.add_argument(
        "--focus", help="Focus areas for standalone review (comma-separated)"
    )
    p_codex_impl.add_argument(
        "--receipt", help="Receipt file path for session continuity"
    )
    p_codex_impl.add_argument("--json", action="store_true", help="JSON output")
    p_codex_impl.add_argument(
        "--sandbox",
        choices=["read-only", "workspace-write", "danger-full-access", "auto"],
        default="auto",
        help="Sandbox mode (auto: danger-full-access on Windows, read-only on Unix)",
    )
    p_codex_impl.set_defaults(func=cmd_codex_impl_review)

    p_codex_plan = codex_sub.add_parser("plan-review", help="Plan review")
    p_codex_plan.add_argument("epic", help="Epic ID (e.g., fn-1, fn-1-add-auth)")
    p_codex_plan.add_argument(
        "--files",
        required=True,
        help="Comma-separated file paths to embed for context (required)",
    )
    p_codex_plan.add_argument("--base", default="main", help="Base branch for context")
    p_codex_plan.add_argument(
        "--receipt", help="Receipt file path for session continuity"
    )
    p_codex_plan.add_argument("--json", action="store_true", help="JSON output")
    p_codex_plan.add_argument(
        "--sandbox",
        choices=["read-only", "workspace-write", "danger-full-access", "auto"],
        default="auto",
        help="Sandbox mode (auto: danger-full-access on Windows, read-only on Unix)",
    )
    p_codex_plan.set_defaults(func=cmd_codex_plan_review)

    p_codex_completion = codex_sub.add_parser(
        "completion-review", help="Epic completion review"
    )
    p_codex_completion.add_argument("epic", help="Epic ID (e.g., fn-1, fn-1-add-auth)")
    p_codex_completion.add_argument(
        "--base", default="main", help="Base branch for diff"
    )
    p_codex_completion.add_argument(
        "--receipt", help="Receipt file path for session continuity"
    )
    p_codex_completion.add_argument("--json", action="store_true", help="JSON output")
    p_codex_completion.add_argument(
        "--sandbox",
        choices=["read-only", "workspace-write", "danger-full-access", "auto"],
        default="auto",
        help="Sandbox mode (auto: danger-full-access on Windows, read-only on Unix)",
    )
    p_codex_completion.set_defaults(func=cmd_codex_completion_review)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
