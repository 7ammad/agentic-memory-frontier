from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

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


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        payload = args.handler(args)
    except (KeyError, ValueError) as exc:
        parser.exit(2, f"ams: {exc}\n")
    _emit(payload, as_json=args.json)
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


def _emit(payload: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2))
        return
    if "recommended_next_actions" in payload:
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
