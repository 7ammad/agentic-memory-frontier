from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .correction_capture import (
    capture_correction,
    correction_gate_status,
    list_corrections,
    resume_correction,
)
from .correction_hooks import hook_on_pre_tool_use_gate, hook_on_user_prompt_submit
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
from .operations import (
    apply_codex_memory_migration,
    build_codex_memory_migration_run,
    dashboard_status,
    run_monitor,
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

    monitor_parser = subparsers.add_parser("monitor", parents=[json_parent], help="Run AMS Monitor-0 checks.")
    monitor_parser.add_argument("--deep", action="store_true", help="Also run the synthetic corruption eval.")
    monitor_parser.set_defaults(handler=_cmd_monitor)

    startup_parser = subparsers.add_parser(
        "startup-brief",
        parents=[json_parent],
        help="Build a bounded startup brief and allow/block decision before agent work.",
    )
    startup_parser.add_argument("description", help="Task description.")
    startup_parser.add_argument("--domain", default="agentic-memory-system", help="Domain scope.")
    startup_parser.add_argument("--task-family", help="Task family.")
    startup_parser.add_argument("--max-directives", type=int, default=8, help="Maximum directives in startup context.")
    startup_parser.add_argument("--max-cards", type=int, default=5, help="Maximum CEM cards in startup context.")
    startup_parser.add_argument("--max-evidence", type=int, default=20, help="Maximum evidence ids in startup context.")
    startup_parser.add_argument("--max-tokens", type=int, default=900, help="Approximate token budget for actions.")
    startup_parser.set_defaults(handler=_cmd_startup_brief)

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


def _cmd_monitor(args: argparse.Namespace) -> dict[str, Any]:
    return run_monitor(args.root, deep=args.deep).model_dump(mode="json")


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


def _read_hook_stdin() -> str:
    """Read a hook payload from stdin, tolerating a leading UTF-8 BOM.

    Windows PowerShell 5.1 prepends a UTF-8 BOM when piping a string to a native
    command. Reading the raw bytes and decoding ``utf-8-sig`` strips it regardless of
    the console code page (decoding as text first would turn the BOM into cp1252
    mojibake ``ï»¿`` that a ``\\ufeff`` strip would miss). Falls back to text mode for
    test stubs (``io.StringIO``) that expose no ``.buffer``.
    """
    import sys

    stream = sys.stdin
    if hasattr(stream, "buffer"):
        return stream.buffer.read().decode("utf-8-sig", errors="replace").strip()
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
    decision = hook_on_user_prompt_submit(
        args.root,
        payload.get("prompt_text", ""),
        session_id=payload.get("session_id"),
        affected_files=payload.get("affected_files") or [],
    )
    return decision.model_dump(mode="json")


def _cmd_correction_hook_gate(args: argparse.Namespace) -> dict[str, Any]:
    return hook_on_pre_tool_use_gate(args.root).model_dump(mode="json")


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


def _emit_startup_brief(payload: dict[str, Any]) -> None:
    print(f"startup_brief: {payload['status']} {payload['brief_id']}")
    print(f"monitor: {payload['monitor_id']}")
    print(f"phase: {payload['phase']['current_phase']} ({payload['phase']['status']})")
    print(f"tokens: {payload['estimated_tokens']} / {payload['limits']['max_tokens']}")
    if payload["block_reasons"]:
        print("block_reasons:")
        for reason in payload["block_reasons"]:
            print(f"- {reason}")
    print("required:")
    for name, present in payload["required_directives"].items():
        print(f"- {name}: {present}")
    if payload["recommended_next_actions"]:
        print("actions:")
        for action in payload["recommended_next_actions"]:
            print(f"- {action}")


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
