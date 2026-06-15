from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
AMS = REPO_ROOT / "scripts" / "ams.py"
PHASE4 = REPO_ROOT / "scripts" / "run_phase4_exam.py"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the terminal fresh-operator AMS acceptance proof."
    )
    parser.add_argument("--root", type=Path, help="Fresh AMS root to prove. Defaults to a temp root.")
    parser.add_argument(
        "--workspace",
        type=Path,
        default=REPO_ROOT,
        help="Workspace whose Codex directives should be bootstrapped.",
    )
    parser.add_argument(
        "--keep-root",
        action="store_true",
        help="Do not remove the generated temp proof root.",
    )
    parser.add_argument(
        "--skip-frontier-eval",
        action="store_true",
        help="Skip the Phase 4 frontier eval rerun. Intended only for focused script tests.",
    )
    parser.add_argument(
        "--frontier-root",
        type=Path,
        default=None,
        help="Directory for the Phase 4 frontier eval storage. Defaults to the eval script temp root.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable proof JSON.")
    args = parser.parse_args(argv)

    temp_dir: Path | None = None
    if args.root is None:
        temp_dir = Path(tempfile.mkdtemp(prefix="ams-operator-proof-"))
        root = temp_dir / "ams-root"
    else:
        root = args.root.expanduser().resolve()
    workspace = args.workspace.expanduser().resolve()
    proof_home = root.parent
    memory_base = proof_home / "legacy-memory"
    config_path = proof_home / "codex-config.toml"
    codex_db = proof_home / "codex-memory" / "lancedb"

    try:
        proof_home.mkdir(parents=True, exist_ok=True)
        _write_legacy_memory(memory_base)
        _write_codex_config(config_path, root, codex_db)
        env = os.environ.copy()
        env["AMS_ROOT"] = str(root)
        env["CEM_ROOT"] = str(root)
        env["AMS_MEMORY_BASE"] = str(memory_base)
        env["AMS_CODEX_CONFIG_PATH"] = str(config_path)

        commands: list[dict[str, Any]] = []
        init = _ams(env, root, commands, "init")
        bootstrap = _ams(env, root, commands, "bootstrap-codex", "--workspace", str(workspace))
        remembered = _ams(
            env,
            root,
            commands,
            "remember",
            "run AMS monitor before claiming the operator proof is healthy",
            "--kind",
            "skill",
            "--outcome",
            "success",
            "--domain",
            "agentic-memory-system",
            "--task-family",
            "operator-proof",
            "--session-id",
            "operator-proof-session",
        )
        migration = _ams(env, root, commands, "migrate", "apply", "--memory-base", str(memory_base))
        surfaces = _ams(env, root, commands, "memory-surfaces")
        startup = _ams(
            env,
            root,
            commands,
            "startup-brief",
            "continue AMS operator proof",
            "--domain",
            "agentic-memory-system",
            "--task-family",
            "operator-proof",
        )
        maintenance = _ams(env, root, commands, "maintenance", "review")
        monitor = _ams(env, root, commands, "monitor", "--deep")
        cards = _ams(env, root, commands, "list", "--kind", "cards")
        audit_target = _first_card_id(cards) or _first_atom_id(remembered)
        if audit_target is None:
            raise RuntimeError("Operator proof could not find a memory id to audit.")
        audit = _ams(env, root, commands, "audit", audit_target)
        closed_run = _ams(
            env,
            root,
            commands,
            "governed-run",
            "close",
            "--receipt-id",
            startup["governed_run_id"],
            "--outcome",
            "success",
            "--action-taken",
            "completed AMS fresh operator proof",
        )
        dashboard = _ams(env, root, commands, "dashboard")

        frontier_eval: dict[str, Any] | None = None
        if not args.skip_frontier_eval:
            frontier_eval = _phase4(env, commands, root=args.frontier_root)

        proof = {
            "status": "pass",
            "root": str(root),
            "workspace": str(workspace),
            "config_path": str(config_path),
            "memory_base": str(memory_base),
            "commands": commands,
            "artifacts": {
                "startup_brief": root / "startup-brief-latest.json",
                "monitor": root / "monitor-latest.json",
                "maintenance": root / "maintenance-latest.json",
            },
            "summary": {
                "init_card_count": init["card_count"],
                "bootstrap_directive_count": bootstrap["created_count"] + bootstrap["existing_count"],
                "remembered_trace_id": remembered["trace_id"],
                "migration_id": migration["run_id"],
                "memory_surfaces_reconciled": surfaces["reconciled"],
                "startup_status": startup["status"],
                "startup_brief_id": startup["brief_id"],
                "startup_monitor_id": startup["monitor_id"],
                "monitor_id": monitor["run_id"],
                "maintenance_status": maintenance["status"],
                "maintenance_item_count": maintenance["summary"]["review_item_count"],
                "monitor_status": monitor["status"],
                "dashboard_next_step": dashboard["phase"]["next_step"],
                "audited_memory_id": audit["audit"]["memory_id"],
                "closed_governed_run_id": closed_run["receipt_id"],
                "closed_governed_run_outcome": closed_run["outcome"],
                "frontier_eval_verdict": _frontier_verdict(frontier_eval),
                "frontier_eval_margin_pp": _frontier_margin(frontier_eval),
            },
        }
        _assert_pass(proof)

        if args.json:
            _write_json(proof)
        else:
            print(f"AMS_OPERATOR_PROOF_PASS root={root}")
            summary = proof["summary"]
            print(f"memory_surfaces_reconciled={summary['memory_surfaces_reconciled']}")
            print(f"startup={summary['startup_status']} {summary['startup_brief_id']}")
            print(f"monitor={summary['monitor_status']} {summary['monitor_id']}")
            print(
                "maintenance="
                f"{summary['maintenance_status']} items={summary['maintenance_item_count']}"
            )
            print(f"audit={summary['audited_memory_id']}")
            print(
                "governed_run="
                f"{summary['closed_governed_run_id']} outcome={summary['closed_governed_run_outcome']}"
            )
            if frontier_eval is not None:
                print(
                    "frontier_eval="
                    f"{summary['frontier_eval_verdict']} margin={summary['frontier_eval_margin_pp']}pp"
                )
        return 0
    except Exception as exc:
        failure = {"status": "fail", "root": str(root), "error": str(exc)}
        if args.json:
            _write_json(failure)
        else:
            print(f"AMS_OPERATOR_PROOF_FAIL root={root}", file=sys.stderr)
            print(str(exc), file=sys.stderr)
        return 1
    finally:
        if temp_dir is not None and not args.keep_root:
            shutil.rmtree(temp_dir, ignore_errors=True)


def _ams(env: dict[str, str], root: Path, commands: list[dict[str, Any]], *args: str) -> dict[str, Any]:
    command = [sys.executable, str(AMS), "--root", str(root), "--json", *args]
    process = subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    record = {
        "name": "ams " + " ".join(args),
        "returncode": process.returncode,
        "stdout": process.stdout,
        "stderr": process.stderr,
    }
    commands.append(record)
    if process.returncode != 0:
        raise RuntimeError(f"{record['name']} failed: {process.stderr.strip()}")
    try:
        return json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{record['name']} did not emit JSON: {process.stdout}") from exc


def _phase4(env: dict[str, str], commands: list[dict[str, Any]], *, root: Path | None = None) -> dict[str, Any]:
    command = [sys.executable, str(PHASE4)]
    if root is not None:
        command.extend(["--root", str(root)])
    process = subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    commands.append(
        {
            "name": "phase4 frontier eval",
            "returncode": process.returncode,
            "stdout": process.stdout,
            "stderr": process.stderr,
        }
    )
    if process.returncode != 0:
        raise RuntimeError(f"Phase 4 frontier eval failed: {process.stderr.strip()}")
    first_json = process.stdout.split("\n\n", 1)[0]
    try:
        return json.loads(first_json)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Phase 4 frontier eval did not start with JSON.") from exc


def _write_legacy_memory(memory_base: Path) -> None:
    memory_base.mkdir(parents=True, exist_ok=True)
    registry = memory_base / "MEMORY.md"
    registry.write_text(
        "\n".join(
            [
                "# Task Group: C:\\Dev\\Builds\\Agentic Memory System / fresh operator proof",
                "",
                "scope: Agentic Memory System operator proof.",
                "",
                "## Reusable knowledge",
                "- Run the AMS startup brief before serious AMS work.",
                "- Run monitor --deep before claiming AMS operator setup is healthy.",
                "- Keep AMS as the primary memory surface; legacy Codex memory is secondary input.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_codex_config(config_path: Path, root: Path, codex_db: Path) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        "\n".join(
            [
                "[mcp_servers.ams-memory]",
                'command = "node"',
                f'args = ["ignored-runner.js", "--root", {json.dumps(str(root))}]',
                "",
                "[mcp_servers.codex-memory]",
                'command = "node"',
                "",
                "[mcp_servers.codex-memory.env]",
                f"CODEX_MEMORY_DB_PATH = {json.dumps(str(codex_db))}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _first_card_id(payload: dict[str, Any]) -> str | None:
    cards = payload.get("cards")
    if isinstance(cards, list) and cards:
        first = cards[0]
        if isinstance(first, dict) and isinstance(first.get("card_id"), str):
            return first["card_id"]
    return None


def _first_atom_id(payload: dict[str, Any]) -> str | None:
    atoms = payload.get("atoms")
    if isinstance(atoms, list) and atoms:
        first = atoms[0]
        if isinstance(first, dict) and isinstance(first.get("atom_id"), str):
            return first["atom_id"]
    return None


def _frontier_verdict(frontier_eval: dict[str, Any] | None) -> str | None:
    if frontier_eval is None:
        return None
    report = frontier_eval.get("report")
    if isinstance(report, dict) and isinstance(report.get("verdict"), str):
        return report["verdict"]
    return None


def _frontier_margin(frontier_eval: dict[str, Any] | None) -> float | None:
    if frontier_eval is None:
        return None
    report = frontier_eval.get("report")
    if isinstance(report, dict):
        value = report.get("measured_lexical_margin_pp")
        if isinstance(value, int | float):
            return float(value)
    return None


def _assert_pass(proof: dict[str, Any]) -> None:
    summary = proof["summary"]
    failures = []
    if summary["memory_surfaces_reconciled"] is not True:
        failures.append("memory surfaces did not reconcile")
    if summary["startup_status"] != "allow":
        failures.append(f"startup did not allow: {summary['startup_status']}")
    if summary["monitor_status"] != "pass":
        failures.append(f"monitor did not pass: {summary['monitor_status']}")
    if summary["maintenance_status"] != "pass":
        failures.append(f"maintenance did not pass: {summary['maintenance_status']}")
    if summary["maintenance_item_count"] != 0:
        failures.append(f"maintenance produced {summary['maintenance_item_count']} review items")
    if summary["closed_governed_run_outcome"] != "success":
        failures.append("governed run was not closed with success")
    verdict = summary["frontier_eval_verdict"]
    if verdict is not None and verdict != "PASS":
        failures.append(f"frontier eval verdict was {verdict}")
    if failures:
        raise RuntimeError("; ".join(failures))


def _write_json(payload: dict[str, Any]) -> None:
    serializable = json.loads(json.dumps(payload, default=str))
    print(json.dumps(serializable, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
