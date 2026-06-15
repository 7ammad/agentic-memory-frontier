from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from .agent_onboarding import build_hammad_agent_roster
from .correction_capture import (
    capture_correction,
    correction_gate_status,
    list_corrections,
    resume_correction,
)
from .correction_hooks import hook_on_pre_tool_use_gate, hook_on_user_prompt_submit
from .kernel import CEM
from .local_memory import (
    audit_memory,
    bootstrap_codex,
    current_session,
    init_memory,
    list_memory,
    new_session,
    pin_directive,
    remember_experience,
    retrieve_brief,
    run_eval,
)
from .models import AgentOnboardingContract
from .operations import (
    apply_codex_memory_migration,
    build_codex_memory_migration_run,
    close_governed_run,
    dashboard_status,
    maintenance_review,
    memory_surface_report,
    record_runtime_trace,
    run_monitor,
    runtime_control,
    startup_brief,
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        payload = args.handler(args)
    except (KeyError, ValueError) as exc:
        # json.JSONDecodeError (malformed hook stdin) is a ValueError -> exit 2 before
        # any capture, so a parse error never writes an event or prints to stdout.
        parser.exit(2, f"ams: {exc}\n")
    _emit(payload, as_json=args.json)
    # §12 hook decisions carry the process exit code (0 allow / 10 block / 11 gate);
    # every other command returns 0 (no hook_exit_code key).
    if isinstance(payload, dict) and "hook_exit_code" in payload:
        return int(payload["hook_exit_code"])
    if isinstance(payload, dict) and "runtime_exit_code" in payload:
        return int(payload["runtime_exit_code"])
    return 0


def build_parser() -> argparse.ArgumentParser:
    json_parent = argparse.ArgumentParser(add_help=False)
    json_parent.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    parser = argparse.ArgumentParser(
        prog="ams",
        description="Local Agentic Memory System for Codex.",
    )
    parser.add_argument("--root", type=Path, default=None, help="Memory root. Defaults to AMS_ROOT or ~/.codex/memory/cem.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", parents=[json_parent], help="Initialize local memory.")
    init_parser.add_argument("--agent-id", default="codex", help="Default source agent id.")
    init_parser.set_defaults(handler=_cmd_init)

    session_parser = subparsers.add_parser("session", parents=[json_parent], help="Inspect or rotate the current session.")
    session_subparsers = session_parser.add_subparsers(dest="session_command", required=True)
    session_current = session_subparsers.add_parser("current", parents=[json_parent], help="Print the current session id.")
    session_current.set_defaults(handler=_cmd_session_current)
    session_new = session_subparsers.add_parser("new", parents=[json_parent], help="Rotate to a new session id.")
    session_new.set_defaults(handler=_cmd_session_new)

    remember_parser = subparsers.add_parser(
        "remember",
        parents=[json_parent],
        help="Remember learned experience through CEM validation.",
    )
    remember_parser.add_argument("content", help="Operational experience to remember.")
    remember_parser.add_argument(
        "--kind",
        required=True,
        choices=["fact", "preference", "instruction", "skill", "failure", "hypothesis"],
        help="Experience kind.",
    )
    remember_parser.add_argument(
        "--outcome",
        required=True,
        choices=["success", "failure", "partial", "unknown"],
        help="Observed outcome. Required to avoid silently over-promoting memories.",
    )
    remember_parser.add_argument("--domain", help="Domain scope.")
    remember_parser.add_argument("--task-family", help="Task family.")
    remember_parser.add_argument("--session-id", help="Override the current session id.")
    remember_parser.add_argument("--agent-id", help="Override the configured agent id.")
    remember_parser.set_defaults(handler=_cmd_remember)

    pin_parser = subparsers.add_parser(
        "pin",
        parents=[json_parent],
        help="Pin an explicit directive without treating it as learned experience.",
    )
    pin_parser.add_argument("content", help="Directive content.")
    pin_parser.add_argument("--source", default="manual", help="Directive source.")
    pin_parser.add_argument("--scope", default="global", help="Directive scope.")
    pin_parser.add_argument("--domain", help="Domain scope.")
    pin_parser.add_argument("--task-family", help="Task family.")
    pin_parser.set_defaults(handler=_cmd_pin)

    bootstrap_parser = subparsers.add_parser(
        "bootstrap-codex",
        parents=[json_parent],
        help="Pin this repo's first Codex directives.",
    )
    bootstrap_parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root.")
    bootstrap_parser.set_defaults(handler=_cmd_bootstrap)

    brief_parser = subparsers.add_parser("brief", parents=[json_parent], help="Retrieve a task-scoped action brief.")
    brief_parser.add_argument("description", help="Task description.")
    brief_parser.add_argument("--domain", help="Domain scope.")
    brief_parser.add_argument("--task-family", help="Task family.")
    brief_parser.add_argument("--session-id", help="Session id.")
    brief_parser.add_argument("--task-id", help="Task id.")
    brief_parser.add_argument("--max-cards", type=int, default=5, help="Maximum CEM cards.")
    brief_parser.set_defaults(handler=_cmd_brief)

    list_parser = subparsers.add_parser("list", parents=[json_parent], help="List memory objects.")
    list_parser.add_argument("--kind", choices=["cards", "atoms", "directives"], default="cards")
    list_parser.set_defaults(handler=_cmd_list)

    audit_parser = subparsers.add_parser("audit", parents=[json_parent], help="Audit one card, atom, or directive.")
    audit_parser.add_argument("memory_id")
    audit_parser.set_defaults(handler=_cmd_audit)

    eval_parser = subparsers.add_parser("eval", parents=[json_parent], help="Run the synthetic corruption eval.")
    eval_parser.set_defaults(handler=_cmd_eval)

    migrate_parser = subparsers.add_parser("migrate", parents=[json_parent], help="Curate legacy Codex memory into AMS.")
    migrate_subparsers = migrate_parser.add_subparsers(dest="migrate_command", required=True)
    migrate_dry_run = migrate_subparsers.add_parser(
        "dry-run",
        parents=[json_parent],
        help="Build and log a migration plan without applying it.",
    )
    migrate_dry_run.add_argument("--memory-base", type=Path, help="Legacy Codex memory base. Defaults to ~/.codex/memories.")
    migrate_dry_run.set_defaults(handler=_cmd_migrate_dry_run)
    migrate_apply = migrate_subparsers.add_parser(
        "apply",
        parents=[json_parent],
        help="Apply the curated migration plan.",
    )
    migrate_apply.add_argument("--memory-base", type=Path, help="Legacy Codex memory base. Defaults to ~/.codex/memories.")
    migrate_apply.set_defaults(handler=_cmd_migrate_apply)

    surfaces_parser = subparsers.add_parser(
        "memory-surfaces",
        parents=[json_parent],
        help="Report which memory surfaces are primary versus secondary under AMS.",
    )
    surfaces_parser.add_argument("--config-path", type=Path, help="Codex config.toml path. Defaults to ~/.codex/config.toml.")
    surfaces_parser.add_argument("--memory-base", type=Path, help="Legacy Codex memory base. Defaults to ~/.codex/memories.")
    surfaces_parser.set_defaults(handler=_cmd_memory_surfaces)

    monitor_parser = subparsers.add_parser("monitor", parents=[json_parent], help="Run AMS Monitor-0 checks.")
    monitor_parser.add_argument("--deep", action="store_true", help="Also run the synthetic corruption eval.")
    monitor_parser.set_defaults(handler=_cmd_monitor)

    maintenance_parser = subparsers.add_parser(
        "maintenance",
        parents=[json_parent],
        help="Review AMS memory freshness and maintenance risk.",
    )
    maintenance_subparsers = maintenance_parser.add_subparsers(dest="maintenance_command", required=True)
    maintenance_review_parser = maintenance_subparsers.add_parser(
        "review",
        parents=[json_parent],
        help="List stale, expired, contradicted, and pending records requiring operator action.",
    )
    maintenance_review_parser.add_argument(
        "--stale-after-days",
        type=int,
        default=90,
        help="Warn on active cards not validated for this many days.",
    )
    maintenance_review_parser.add_argument(
        "--pending-atom-after-days",
        type=int,
        default=14,
        help="Warn on proposed/candidate atoms waiting this many days.",
    )
    maintenance_review_parser.set_defaults(handler=_cmd_maintenance_review)

    startup_parser = subparsers.add_parser(
        "startup-brief",
        parents=[json_parent],
        help="Build a bounded startup brief and non-blocking memory-readiness status before agent work.",
    )
    startup_parser.add_argument("description", help="Task description.")
    startup_parser.add_argument("--domain", default="agentic-memory-system", help="Domain scope.")
    startup_parser.add_argument("--task-family", help="Task family.")
    startup_parser.add_argument("--max-directives", type=int, default=8, help="Maximum directives in startup context.")
    startup_parser.add_argument("--max-cards", type=int, default=5, help="Maximum CEM cards in startup context.")
    startup_parser.add_argument("--max-evidence", type=int, default=20, help="Maximum evidence ids in startup context.")
    startup_parser.add_argument("--max-tokens", type=int, default=900, help="Approximate token budget for actions.")
    startup_parser.set_defaults(handler=_cmd_startup_brief)

    runtime_control_parser = subparsers.add_parser(
        "runtime-control",
        parents=[json_parent],
        help="Build an enforceable AMS allow/degraded/block decision before a guarded runtime action.",
    )
    runtime_control_parser.add_argument("description", help="Prompt or task description to guard.")
    runtime_control_parser.add_argument("--domain", default="agentic-memory-system", help="Domain scope.")
    runtime_control_parser.add_argument("--task-family", help="Task family.")
    runtime_control_parser.add_argument("--session-id", help="Runtime session id.")
    runtime_control_parser.add_argument("--affected-file", action="append", default=[], help="Affected file path.")
    runtime_control_parser.set_defaults(handler=_cmd_runtime_control)

    runtime_trace_parser = subparsers.add_parser(
        "runtime-trace",
        parents=[json_parent],
        help="Record a real AMS runtime trace after a guarded command.",
    )
    runtime_trace_subparsers = runtime_trace_parser.add_subparsers(dest="runtime_trace_command", required=True)
    runtime_trace_record_parser = runtime_trace_subparsers.add_parser(
        "record",
        parents=[json_parent],
        help="Ingest a guarded runtime command into the CEM trace ledger.",
    )
    runtime_trace_record_parser.add_argument("--control-id", required=True, help="Runtime control receipt id.")
    runtime_trace_record_parser.add_argument("--command", required=True, help="Downstream command path or name.")
    runtime_trace_record_parser.add_argument("--command-arg", action="append", default=[], help="Downstream command arg.")
    runtime_trace_record_parser.add_argument("--exit-code", required=True, type=int, help="Observed downstream/guard exit code.")
    runtime_trace_record_parser.add_argument("--started-at", type=_parse_datetime, help="Command start time as ISO-8601.")
    runtime_trace_record_parser.add_argument("--ended-at", type=_parse_datetime, help="Command end time as ISO-8601.")
    runtime_trace_record_parser.set_defaults(handler=_cmd_runtime_trace_record)

    governed_parser = subparsers.add_parser(
        "governed-run",
        parents=[json_parent],
        help="Close governed AMS run receipts.",
    )
    governed_subparsers = governed_parser.add_subparsers(dest="governed_command", required=True)
    governed_close_parser = governed_subparsers.add_parser(
        "close",
        parents=[json_parent],
        help="Finalize a governed run with observed outcome and influence evidence.",
    )
    governed_close_parser.add_argument("--receipt-id", help="Receipt id. Defaults to the latest governed run.")
    governed_close_parser.add_argument(
        "--outcome",
        required=True,
        choices=["success", "failure", "partial", "unknown"],
        help="Observed outcome.",
    )
    governed_close_parser.add_argument("--action-taken", help="Action performed after reading the brief.")
    governed_close_parser.add_argument(
        "--observed-post-brief-delta",
        type=float,
        help="Observed post-brief delta. Observational only, not verified lift.",
    )
    governed_close_parser.add_argument("--baseline-comparison", help="Optional baseline comparison note.")
    governed_close_parser.set_defaults(handler=_cmd_governed_run_close)

    correction_parser = subparsers.add_parser(
        "correction",
        parents=[json_parent],
        help="Capture live corrections and manage the resume gate.",
    )
    correction_subparsers = correction_parser.add_subparsers(dest="correction_command", required=True)
    correction_capture_parser = correction_subparsers.add_parser(
        "capture",
        parents=[json_parent],
        help="Record a live user correction and block continuation until resume.",
    )
    correction_capture_parser.add_argument("user_text", help="Correction text from the user.")
    correction_capture_parser.add_argument("--affected-file", action="append", default=[], help="Affected file path.")
    correction_capture_parser.add_argument("--affected-action", action="append", default=[], help="Affected action.")
    correction_capture_parser.add_argument("--stale-memory-id", action="append", default=[], help="Stale or contradicted memory id.")
    correction_capture_parser.add_argument("--source", default="manual", help="Correction source.")
    correction_capture_parser.add_argument("--domain", default="agentic-memory-system", help="Domain scope.")
    correction_capture_parser.add_argument("--task-family", default="mistake-capture", help="Task family.")
    correction_capture_parser.add_argument("--session-id", help="Session id.")
    correction_capture_parser.add_argument("--project-ledger", type=Path, help="Optional project ledger file to append.")
    correction_capture_parser.set_defaults(handler=_cmd_correction_capture)

    correction_gate_parser = correction_subparsers.add_parser("gate", parents=[json_parent], help="Inspect resume gate.")
    correction_gate_parser.set_defaults(handler=_cmd_correction_gate)

    correction_list_parser = correction_subparsers.add_parser("list", parents=[json_parent], help="List correction events.")
    correction_list_parser.add_argument("--limit", type=int, default=20, help="Maximum events to return.")
    correction_list_parser.set_defaults(handler=_cmd_correction_list)

    correction_resume_parser = correction_subparsers.add_parser(
        "resume",
        parents=[json_parent],
        help="Clear the resume gate after explicit approval.",
    )
    correction_resume_parser.add_argument("event_id", help="Correction event id.")
    correction_resume_parser.add_argument("--approved-by", required=True, help="Approver name.")
    correction_resume_parser.add_argument("--note", help="Resume note.")
    correction_resume_parser.set_defaults(handler=_cmd_correction_resume)

    # §12 live runtime hooks (UserPromptSubmit / PreToolUse). Read a hook payload from
    # stdin (hook-prompt) or no input (hook-gate); the exit code carries the decision
    # (0 allow, 10 prompt-block, 11 gate-blocked, 2 parse/Waki error). No hook-resume
    # subcommand exists: the gate clears ONLY via `correction resume` (human-approved).
    correction_hook_prompt_parser = correction_subparsers.add_parser(
        "hook-prompt",
        parents=[json_parent],
        help="UserPromptSubmit hook: classify a prompt (read from stdin), capture + block on a correction.",
    )
    correction_hook_prompt_parser.set_defaults(handler=_cmd_correction_hook_prompt)

    correction_hook_gate_parser = correction_subparsers.add_parser(
        "hook-gate",
        parents=[json_parent],
        help="PreToolUse hook: deny continuation while the resume gate is armed.",
    )
    correction_hook_gate_parser.set_defaults(handler=_cmd_correction_hook_gate)

    agent_parser = subparsers.add_parser(
        "agent",
        parents=[json_parent],
        help="Onboard and audit agents against AMS capability and memory-lane contracts.",
    )
    agent_subparsers = agent_parser.add_subparsers(dest="agent_command", required=True)
    agent_seed_parser = agent_subparsers.add_parser(
        "seed-roster",
        parents=[json_parent],
        help="Seed Hammad's current agent roster: Codex, Hermes, Hessa, Claude Code, Cursor, and parked OpenClaw.",
    )
    agent_seed_parser.set_defaults(handler=_cmd_agent_seed_roster)
    agent_list_parser = agent_subparsers.add_parser(
        "list",
        parents=[json_parent],
        help="List persisted agent onboarding contracts.",
    )
    agent_list_parser.set_defaults(handler=_cmd_agent_list)
    agent_audit_parser = agent_subparsers.add_parser(
        "audit",
        parents=[json_parent],
        help="Audit one onboarded agent by agent id or contract id.",
    )
    agent_audit_parser.add_argument("agent_id")
    agent_audit_parser.set_defaults(handler=_cmd_agent_audit)
    agent_onboard_parser = agent_subparsers.add_parser(
        "onboard",
        parents=[json_parent],
        help="Onboard an agent from an AgentOnboardingContract JSON file.",
    )
    agent_onboard_parser.add_argument("contract", type=Path)
    agent_onboard_parser.set_defaults(handler=_cmd_agent_onboard)

    dashboard_parser = subparsers.add_parser("dashboard", parents=[json_parent], help="Show latest AMS operator status.")
    dashboard_parser.set_defaults(handler=_cmd_dashboard)

    return parser


def _cmd_init(args: argparse.Namespace) -> dict[str, Any]:
    return init_memory(args.root, agent_id=args.agent_id)


def _cmd_session_current(args: argparse.Namespace) -> dict[str, Any]:
    return current_session(args.root)


def _cmd_session_new(args: argparse.Namespace) -> dict[str, Any]:
    return new_session(args.root)


def _cmd_remember(args: argparse.Namespace) -> dict[str, Any]:
    return remember_experience(
        args.root,
        args.content,
        kind=args.kind,
        outcome=args.outcome,
        domain_scope=args.domain,
        task_family=args.task_family,
        session_id=args.session_id,
        agent_id=args.agent_id,
    )


def _cmd_pin(args: argparse.Namespace) -> dict[str, Any]:
    return pin_directive(
        args.root,
        args.content,
        source=args.source,
        scope=args.scope,
        domain_scope=args.domain,
        task_family=args.task_family,
    )


def _cmd_bootstrap(args: argparse.Namespace) -> dict[str, Any]:
    return bootstrap_codex(args.root, workspace=args.workspace)


def _cmd_brief(args: argparse.Namespace) -> dict[str, Any]:
    return retrieve_brief(
        args.root,
        args.description,
        domain_scope=args.domain,
        task_family=args.task_family,
        session_id=args.session_id,
        task_id=args.task_id,
        max_cards=args.max_cards,
    )


def _cmd_list(args: argparse.Namespace) -> dict[str, Any]:
    return list_memory(args.root, kind=args.kind)


def _cmd_audit(args: argparse.Namespace) -> dict[str, Any]:
    return audit_memory(args.root, args.memory_id)


def _cmd_eval(args: argparse.Namespace) -> dict[str, Any]:
    return run_eval(args.root)


def _cmd_migrate_dry_run(args: argparse.Namespace) -> dict[str, Any]:
    return build_codex_memory_migration_run(args.root, memory_base=args.memory_base).model_dump(mode="json")


def _cmd_migrate_apply(args: argparse.Namespace) -> dict[str, Any]:
    return apply_codex_memory_migration(args.root, memory_base=args.memory_base).model_dump(mode="json")


def _cmd_memory_surfaces(args: argparse.Namespace) -> dict[str, Any]:
    return memory_surface_report(
        args.root,
        config_path=args.config_path,
        memory_base=args.memory_base,
    ).model_dump(mode="json")


def _cmd_monitor(args: argparse.Namespace) -> dict[str, Any]:
    return run_monitor(args.root, deep=args.deep).model_dump(mode="json")


def _cmd_maintenance_review(args: argparse.Namespace) -> dict[str, Any]:
    return maintenance_review(
        args.root,
        stale_after_days=args.stale_after_days,
        pending_atom_after_days=args.pending_atom_after_days,
    ).model_dump(mode="json")


def _cmd_startup_brief(args: argparse.Namespace) -> dict[str, Any]:
    return startup_brief(
        args.root,
        description=args.description,
        domain_scope=args.domain,
        task_family=args.task_family,
        max_directives=args.max_directives,
        max_cards=args.max_cards,
        max_evidence=args.max_evidence,
        max_tokens=args.max_tokens,
    ).model_dump(mode="json")


def _cmd_runtime_control(args: argparse.Namespace) -> dict[str, Any]:
    return runtime_control(
        args.root,
        description=args.description,
        domain_scope=args.domain,
        task_family=args.task_family,
        session_id=args.session_id,
        affected_files=args.affected_file,
    ).model_dump(mode="json")


def _cmd_runtime_trace_record(args: argparse.Namespace) -> dict[str, Any]:
    return record_runtime_trace(
        args.root,
        control_id=args.control_id,
        command=args.command,
        command_args=args.command_arg,
        observed_exit_code=args.exit_code,
        started_at=args.started_at,
        ended_at=args.ended_at,
    ).model_dump(mode="json")


def _cmd_governed_run_close(args: argparse.Namespace) -> dict[str, Any]:
    return close_governed_run(
        args.root,
        receipt_id=args.receipt_id,
        outcome=args.outcome,
        action_taken=args.action_taken,
        observed_post_brief_delta=args.observed_post_brief_delta,
        baseline_comparison=args.baseline_comparison,
    ).model_dump(mode="json")


def _cmd_correction_capture(args: argparse.Namespace) -> dict[str, Any]:
    return capture_correction(
        args.root,
        args.user_text,
        affected_files=args.affected_file,
        affected_actions=args.affected_action,
        stale_memory_ids=args.stale_memory_id,
        source=args.source,
        domain_scope=args.domain,
        task_family=args.task_family,
        session_id=args.session_id,
        project_ledger=args.project_ledger,
    ).model_dump(mode="json")


def _cmd_correction_gate(args: argparse.Namespace) -> dict[str, Any]:
    return correction_gate_status(args.root).model_dump(mode="json")


def _cmd_correction_list(args: argparse.Namespace) -> dict[str, Any]:
    return list_corrections(args.root, limit=args.limit)


def _cmd_correction_resume(args: argparse.Namespace) -> dict[str, Any]:
    return resume_correction(
        args.root,
        args.event_id,
        approved_by=args.approved_by,
        note=args.note,
    ).model_dump(mode="json")


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _read_hook_stdin() -> str:
    """Read a hook payload from stdin, tolerating a leading UTF-8 BOM.

    Windows PowerShell 5.1 prepends a UTF-8 BOM when piping a string to a native
    command. Reading the raw bytes and decoding ``utf-8-sig`` strips it regardless of
    the console code page (decoding as text first would turn the BOM into cp1252
    mojibake ``ï»¿`` that a ``\\ufeff`` strip would miss). Falls back to text mode for
    test stubs (``io.StringIO``) that expose no ``.buffer``.

    Decodes STRICTLY (no ``errors="replace"``): genuinely-malformed input raises
    ``UnicodeDecodeError`` (a ``ValueError`` subclass) which ``main()`` maps to a clean
    exit 2, rather than silently substituting U+FFFD and accepting mangled data.
    """
    import sys

    stream = sys.stdin
    if hasattr(stream, "buffer"):
        return stream.buffer.read().decode("utf-8-sig").strip()
    text = stream.read()
    for bom in ("﻿", "\xef\xbb\xbf"):  # decoded-as-utf-8 vs decoded-as-cp1252
        if text.startswith(bom):
            text = text[len(bom):]
    return text.strip()


def _cmd_correction_hook_prompt(args: argparse.Namespace) -> dict[str, Any]:
    # Parse stdin as an UNTYPED dict (never a StrictModel), so unknown runtime keys
    # (transcript_path, cwd, hook_event_name, ...) are tolerated. A malformed payload
    # raises json.JSONDecodeError (a ValueError subclass) -> main() maps it to exit 2,
    # before any capture, so no event is written.
    payload = json.loads(_read_hook_stdin() or "{}")
    prompt_text = payload.get("prompt_text")
    if prompt_text is None:
        prompt_text = payload.get("prompt", "")
    decision = hook_on_user_prompt_submit(
        args.root,
        prompt_text,
        session_id=payload.get("session_id"),
        affected_files=payload.get("affected_files") or [],
    )
    return decision.model_dump(mode="json")


def _cmd_correction_hook_gate(args: argparse.Namespace) -> dict[str, Any]:
    return hook_on_pre_tool_use_gate(args.root).model_dump(mode="json")


def _cmd_agent_seed_roster(args: argparse.Namespace) -> dict[str, Any]:
    cem = CEM(args.root)
    receipts = [cem.onboard_agent(contract) for contract in build_hammad_agent_roster()]
    return {
        "accepted_count": sum(receipt.status == "accepted" for receipt in receipts),
        "rejected_count": sum(receipt.status == "rejected" for receipt in receipts),
        "needs_review_count": sum(receipt.status == "needs_review" for receipt in receipts),
        "agent_ids": [receipt.agent_id for receipt in receipts if receipt.status == "accepted"],
        "receipts": [receipt.model_dump(mode="json") for receipt in receipts],
    }


def _cmd_agent_list(args: argparse.Namespace) -> dict[str, Any]:
    cem = CEM(args.root)
    return {"agents": [contract.model_dump(mode="json") for contract in cem.list_onboarded_agents()]}


def _cmd_agent_audit(args: argparse.Namespace) -> dict[str, Any]:
    cem = CEM(args.root)
    return cem.audit_onboarded_agent(args.agent_id)


def _cmd_agent_onboard(args: argparse.Namespace) -> dict[str, Any]:
    contract = AgentOnboardingContract.model_validate_json(args.contract.read_text(encoding="utf-8"))
    receipt = CEM(args.root).onboard_agent(contract)
    return {"receipt": receipt.model_dump(mode="json")}


def _cmd_dashboard(args: argparse.Namespace) -> dict[str, Any]:
    return dashboard_status(args.root)


def _emit(payload: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2))
        return
    # Hook decisions FIRST: the unique 'hook'+'hook_exit_code' discriminator keeps a
    # HookDecision (which carries event_id/active_event_id) from misrouting through the
    # correction-event or gate emitters below.
    if "hook" in payload and "hook_exit_code" in payload:
        _emit_correction_hook(payload)
    elif "control_id" in payload and "runtime_exit_code" in payload:
        _emit_runtime_control(payload)
    elif "trace_id" in payload and "control_id" in payload and "observed_exit_code" in payload:
        _emit_runtime_trace(payload)
    elif "receipt_id" in payload and "startup_brief_id" in payload and "closed" in payload:
        _emit_governed_run(payload)
    elif "brief_id" in payload and "monitor_id" in payload:
        _emit_startup_brief(payload)
    elif "event_id" in payload and "route_targets" in payload:
        _emit_correction_event(payload)
    elif "event_id" in payload and "approved_by" in payload:
        _emit_correction_resume(payload)
    elif "active_event_id" in payload and "resume_token" in payload:
        _emit_correction_gate(payload)
    elif "events" in payload and "gate" in payload:
        _emit_correction_list(payload)
    elif "recommended_next_actions" in payload:
        _emit_brief(payload)
    elif "promoted_cards" in payload:
        _emit_remember(payload)
    elif "directive" in payload:
        directive = payload["directive"]
        status = "created" if payload["created"] else "existing"
        print(f"{status}: {directive['directive_id']} :: {directive['content']}")
    elif "directives" in payload and "created_count" in payload:
        print(f"bootstrap: {payload['created_count']} created, {payload['existing_count']} existing")
        for directive in payload["directives"]:
            print(f"{directive['directive_id']} :: {directive['content']}")
    elif "pin_count" in payload and "remember_count" in payload:
        _emit_migration(payload)
    elif "memory_base" in payload and "surfaces" in payload:
        _emit_memory_surfaces(payload)
    elif "summary" in payload and "stale_after_days" in payload:
        _emit_maintenance(payload)
    elif "checks" in payload and "status" in payload:
        _emit_monitor(payload)
    elif "latest_monitor" in payload:
        _emit_dashboard(payload)
    elif "cards" in payload:
        _emit_cards(payload)
    elif "atoms" in payload:
        _emit_atoms(payload)
    elif "directives" in payload:
        for directive in payload["directives"]:
            print(f"{directive['directive_id']} :: {directive['content']}")
    else:
        print(json.dumps(payload, indent=2))


def _emit_remember(payload: dict[str, Any]) -> None:
    print(f"trace: {payload['trace_id']}")
    print(f"session: {payload['session_id']}")
    print(
        "result: "
        f"{payload['promoted_count']} promoted, "
        f"{payload['quarantined_count']} quarantined, "
        f"{payload['proposed_count']} proposed"
    )
    for card in payload["promoted_cards"]:
        print(f"card: {card['card_id']} :: {card['title']}")
    for atom in payload["atoms"]:
        if atom["status"] == "quarantined":
            print(f"quarantined: {atom['atom_id']} :: {', '.join(atom['reason_codes'])}")


def _emit_brief(payload: dict[str, Any]) -> None:
    print(f"task: {payload.get('task_id') or '(ad hoc)'}")
    print(f"confidence: {payload['confidence_score']}")
    if not payload["recommended_next_actions"]:
        print("actions: none")
        return
    print("actions:")
    for action in payload["recommended_next_actions"]:
        print(f"- {action}")
    if payload["preconditions_to_check"]:
        print("check first:")
        for item in payload["preconditions_to_check"]:
            print(f"- {item}")
    if payload["evidence_links"]:
        print("evidence:")
        for item in payload["evidence_links"]:
            print(f"- {item}")


def _emit_cards(payload: dict[str, Any]) -> None:
    if not payload["cards"]:
        print("cards: none")
        return
    for card in payload["cards"]:
        print(f"{card['card_id']} :: {card['title']} :: evidence={card['evidence_count']}")


def _emit_atoms(payload: dict[str, Any]) -> None:
    if not payload["atoms"]:
        print("atoms: none")
        return
    for atom in payload["atoms"]:
        print(f"{atom['atom_id']} :: {atom['status']} :: {atom['content']}")


def _emit_migration(payload: dict[str, Any]) -> None:
    mode = "applied" if payload["applied"] else "dry-run"
    print(f"migration: {mode} {payload['run_id']}")
    print(
        "items: "
        f"{payload['pin_count']} pin, "
        f"{payload['remember_count']} remember, "
        f"{payload['skip_count']} skip"
    )
    if payload["applied"]:
        print(
            "applied: "
            f"{payload['applied_pin_count']} pins, "
            f"{payload['applied_remember_count']} memories, "
            f"{payload['existing_count']} existing"
        )
    for item in payload["items"]:
        print(f"- {item['action']}: {item['content']}")


def _emit_memory_surfaces(payload: dict[str, Any]) -> None:
    status = "reconciled" if payload["reconciled"] else "not-reconciled"
    print(f"memory_surfaces: {status}")
    print(f"config: {payload['config_path']}")
    print(f"memory_base: {payload['memory_base']}")
    for surface in payload["surfaces"]:
        print(
            f"- {surface['status']}: {surface['name']} "
            f"role={surface['role']} configured={surface['configured']} :: {surface['detail']}"
        )


def _emit_monitor(payload: dict[str, Any]) -> None:
    print(f"monitor: {payload['status']} {payload['run_id']}")
    scope = payload.get("scope")
    phase = payload.get("phase")
    if phase:
        print(f"phase: {phase['current_phase']} ({phase['status']})")
        print(f"next: {phase['next_step']}")
    if scope:
        print(
            "scope: "
            f"{scope['ams_card_count']} AMS cards, "
            f"{scope['ams_atom_count']} AMS atoms, "
            f"{scope['ams_directive_count']} AMS directives, "
            f"{scope['global_behavior_directive_count']} global behavior directives, "
            f"{scope['other_directive_count']} other directives"
        )
    for check in payload["checks"]:
        print(f"- {check['status']}: {check['name']} :: {check['detail']}")


def _emit_maintenance(payload: dict[str, Any]) -> None:
    print(f"maintenance: {payload['status']} {payload['run_id']}")
    summary = payload["summary"]
    print(
        "summary: "
        f"{summary['active_card_count']} active cards, "
        f"{summary['inactive_card_count']} inactive cards, "
        f"{summary['expired_active_count']} expired active, "
        f"{summary['stale_active_count']} stale active, "
        f"{summary['contradicted_active_count']} contradicted active, "
        f"{summary['stale_pending_atom_count']} stale pending atoms"
    )
    if not payload["items"]:
        print("items: none")
        return
    print("items:")
    for item in payload["items"]:
        related = ""
        if item["related_memory_ids"]:
            related = f" related={','.join(item['related_memory_ids'])}"
        print(
            f"- {item['status']}: {item['memory_kind']} {item['memory_id']} :: "
            f"{item['reason']} -> {item['action']}{related}"
        )


def _emit_startup_brief(payload: dict[str, Any]) -> None:
    print(f"startup_brief: {payload['status']} {payload['brief_id']}")
    if payload.get("governed_run_id"):
        print(f"governed_run: {payload['governed_run_id']}")
    if payload.get("action_brief_id"):
        print(f"action_brief: {payload['action_brief_id']}")
    if payload.get("influence_id"):
        print(f"influence: {payload['influence_id']}")
    print(f"monitor: {payload['monitor_id']}")
    print(f"phase: {payload['phase']['current_phase']} ({payload['phase']['status']})")
    print(f"tokens: {payload['estimated_tokens']} / {payload['limits']['max_tokens']}")
    if payload["block_reasons"]:
        print("block_reasons:")
        for reason in payload["block_reasons"]:
            print(f"- {reason}")
    if payload.get("degraded_reasons"):
        print("degraded_reasons:")
        for reason in payload["degraded_reasons"]:
            print(f"- {reason}")
    print("required:")
    for name, present in payload["required_directives"].items():
        print(f"- {name}: {present}")
    if payload["recommended_next_actions"]:
        print("actions:")
        for action in payload["recommended_next_actions"]:
            print(f"- {action}")


def _emit_runtime_control(payload: dict[str, Any]) -> None:
    print(f"runtime_control: {payload['status']} {payload['control_id']} (exit {payload['runtime_exit_code']})")
    print(f"enforcement: {payload['enforcement']}")
    print(f"startup_brief: {payload['startup_brief_id']}")
    if payload.get("governed_run_id"):
        print(f"governed_run: {payload['governed_run_id']}")
    print(f"monitor: {payload['monitor_id']}")
    print(f"prompt_decision: {payload['prompt_decision']['decision']}")
    print(f"gate_decision: {payload['gate_decision']['decision']}")
    if payload["block_reasons"]:
        print("block_reasons:")
        for reason in payload["block_reasons"]:
            print(f"- {reason}")
    if payload.get("degraded_reasons"):
        print("degraded_reasons:")
        for reason in payload["degraded_reasons"]:
            print(f"- {reason}")


def _emit_runtime_trace(payload: dict[str, Any]) -> None:
    print(f"runtime_trace: {payload['final_outcome']} {payload['trace_id']}")
    print(f"control: {payload['control_id']} ({payload['runtime_control_status']})")
    if payload.get("governed_run_id"):
        print(f"governed_run: {payload['governed_run_id']}")
    print(f"monitor: {payload['monitor_id']}")
    print(f"command: {payload['command']}")
    print(f"exit_code: {payload['observed_exit_code']}")
    print(f"downstream_invoked: {payload['downstream_invoked']}")
    print(f"proposed_atoms: {payload['proposed_atom_count']}")


def _emit_governed_run(payload: dict[str, Any]) -> None:
    status = "closed" if payload["closed"] else "open"
    print(f"governed_run: {status} {payload['receipt_id']}")
    print(f"outcome: {payload['outcome']}")
    print(f"startup_brief: {payload['startup_brief_id']}")
    if payload.get("action_brief_id"):
        print(f"action_brief: {payload['action_brief_id']}")
    if payload.get("influence_id"):
        print(f"influence: {payload['influence_id']}")
    print(f"influence_records: {len(payload['influence_ids'])}")


def _emit_correction_hook(payload: dict[str, Any]) -> None:
    print(f"hook: {payload['hook']} {payload['decision']} (exit {payload['hook_exit_code']})")
    if payload.get("event_id"):
        print(f"event: {payload['event_id']}")
    print(f"gate: {payload['gate_status']}")


def _emit_correction_event(payload: dict[str, Any]) -> None:
    print(f"correction: {payload['event_id']} {payload['resume_status']}")
    print(f"mistake: {payload['mistake']}")
    print(f"resume_token: {payload['resume_token']}")
    print("categories:")
    for category in payload["categories"]:
        print(f"- {category}")
    print("routes:")
    for route in payload["routes"]:
        print(f"- {route['status']}: {route['target']} :: {route['detail']}")


def _emit_correction_gate(payload: dict[str, Any]) -> None:
    print(f"correction_gate: {payload['status']}")
    if payload.get("active_event_id"):
        print(f"event: {payload['active_event_id']}")
    if payload.get("resume_token"):
        print(f"resume_token: {payload['resume_token']}")


def _emit_correction_list(payload: dict[str, Any]) -> None:
    print(f"corrections: {len(payload['events'])}")
    for event in payload["events"]:
        print(f"- {event['event_id']}: {event['resume_status']} :: {event['mistake']}")
    _emit_correction_gate(payload["gate"])


def _emit_correction_resume(payload: dict[str, Any]) -> None:
    print(f"correction_resume: {payload['event_id']}")
    print(f"approved_by: {payload['approved_by']}")
    print(f"gate: {payload['gate']['status']}")


def _emit_dashboard(payload: dict[str, Any]) -> None:
    print(f"root: {payload['root']}")
    phase = payload.get("phase")
    if phase:
        print(f"completed: {phase['completed_through']}")
        print(f"phase: {phase['current_phase']} ({phase['status']})")
        print(f"next: {phase['next_step']}")
    print(
        "counts: "
        f"{payload['card_count']} cards, "
        f"{payload['atom_count']} atoms, "
        f"{payload['directive_count']} directives"
    )
    scope = payload.get("scope")
    if scope:
        print(
            "ams_scope: "
            f"{scope['ams_card_count']} cards, "
            f"{scope['ams_atom_count']} atoms, "
            f"{scope['ams_directive_count']} directives"
        )
        print(f"global_behavior: {scope['global_behavior_directive_count']} directives")
        print(f"other_scope: {scope['other_directive_count']} directives")
    memory_surfaces = payload.get("memory_surfaces")
    if memory_surfaces:
        status = "reconciled" if memory_surfaces["reconciled"] else "not-reconciled"
        print(f"memory_surfaces: {status}")
    latest_monitor = payload.get("latest_monitor")
    latest_migration = payload.get("latest_migration")
    if latest_monitor:
        print(f"latest_monitor: {latest_monitor['status']} {latest_monitor['run_id']}")
    else:
        print("latest_monitor: none")
    if latest_migration:
        mode = "applied" if latest_migration["applied"] else "dry-run"
        print(f"latest_migration: {mode} {latest_migration['run_id']}")
    else:
        print("latest_migration: none")
    latest_startup_brief = payload.get("latest_startup_brief")
    if latest_startup_brief:
        print(f"latest_startup_brief: {latest_startup_brief['status']} {latest_startup_brief['brief_id']}")
    else:
        print("latest_startup_brief: none")
    latest_governed_run = payload.get("latest_governed_run")
    if latest_governed_run:
        print(
            f"latest_governed_run: {latest_governed_run['status']} {latest_governed_run['receipt_id']} "
            f"closed={latest_governed_run['closed']} outcome={latest_governed_run['outcome']}"
        )
    else:
        print("latest_governed_run: none")
    latest_runtime_control = payload.get("latest_runtime_control")
    if latest_runtime_control:
        print(f"latest_runtime_control: {latest_runtime_control['status']} {latest_runtime_control['control_id']}")
    else:
        print("latest_runtime_control: none")
    latest_runtime_trace = payload.get("latest_runtime_trace")
    if latest_runtime_trace:
        print(
            f"latest_runtime_trace: {latest_runtime_trace['final_outcome']} "
            f"{latest_runtime_trace['trace_id']} atoms={latest_runtime_trace['proposed_atom_count']}"
        )
    else:
        print("latest_runtime_trace: none")
    latest_maintenance = payload.get("latest_maintenance")
    if latest_maintenance:
        print(
            f"latest_maintenance: {latest_maintenance['status']} "
            f"{latest_maintenance['run_id']} items={latest_maintenance['summary']['review_item_count']}"
        )
    else:
        print("latest_maintenance: none")
