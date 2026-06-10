from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from uuid import uuid4
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
V1_PROOF = REPO_ROOT / "scripts" / "run_ams_operator_proof.py"
V2_EVAL = REPO_ROOT / "scripts" / "run_ams_v2_eval.py"
V2_ACCEPTANCE_IDS = {f"V2-SEED-{index:03d}" for index in range(1, 14)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the terminal fresh-root AMS V2 operator proof.")
    parser.add_argument("--root", type=Path, help="Fresh proof root. Defaults to a temp root.")
    parser.add_argument(
        "--workspace",
        type=Path,
        default=REPO_ROOT,
        help="Workspace whose Codex directives should be bootstrapped by the v1 operator path.",
    )
    parser.add_argument(
        "--keep-root",
        action="store_true",
        help="Do not remove the generated temp proof root.",
    )
    parser.add_argument(
        "--skip-frontier-eval",
        action="store_true",
        help="Skip the Phase 4 frontier eval inside the v1 operator proof. Intended for focused tests.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable proof JSON.")
    args = parser.parse_args(argv)

    temp_dir: Path | None = None
    if args.root is None:
        temp_dir = Path(tempfile.mkdtemp(prefix="ams-v2-operator-proof-"))
        requested_root = temp_dir
    else:
        requested_root = args.root.expanduser().resolve()
    root = requested_root / f"proof-{uuid4().hex}"

    try:
        root.mkdir(parents=True, exist_ok=False)
        commands: list[dict[str, Any]] = []
        v1_root = root / "v1-operator"
        v2_root = root / "v2-eval"
        frontier_root = root / "phase4-frontier"

        v1 = _run_v1_operator_proof(
            v1_root,
            workspace=args.workspace.expanduser().resolve(),
            skip_frontier_eval=args.skip_frontier_eval,
            frontier_root=frontier_root,
            commands=commands,
        )
        v2 = _run_v2_eval(v2_root, commands)
        monitor = _load_json(v1_root / "monitor-latest.json")

        v1_summary = v1["summary"]
        v2_report = v2["report"]
        executed_case_ids = _executed_case_ids(v2_report)
        summary = {
            "v1_operator_status": v1["status"],
            "v1_memory_surfaces_reconciled": v1_summary["memory_surfaces_reconciled"],
            "v1_monitor_status": v1_summary["monitor_status"],
            "v1_maintenance_status": v1_summary["maintenance_status"],
            "v1_closed_governed_run_outcome": v1_summary["closed_governed_run_outcome"],
            "v1_frontier_eval_verdict": v1_summary["frontier_eval_verdict"],
            "v2_eval_verdict": v2_report["verdict"],
            "v2_eval_case_count": v2_report["case_count"],
            "v2_eval_pass_count": v2_report["pass_count"],
            "v2_eval_fail_count": v2_report["fail_count"],
            "v2_eval_false_block_count": v2_report["false_block_count"],
            "v2_eval_false_block_budget": v2_report["false_block_budget"],
            "v2_executed_case_ids": executed_case_ids,
            "v2_acceptance_battery_complete": set(executed_case_ids) == V2_ACCEPTANCE_IDS
            and len(executed_case_ids) == len(V2_ACCEPTANCE_IDS),
            "v2_phase_status": monitor["phase"]["current_phase"],
            "v2_ready_for_next_phase": monitor["phase"]["ready_for_next_phase"],
            "v2_open_followups": monitor["phase"]["open_followups"],
        }
        proof = {
            "status": "pass",
            "root": str(root),
            "requested_root": str(requested_root),
            "workspace": str(args.workspace.expanduser().resolve()),
            "commands": commands,
            "artifacts": {
                "v2_operator_proof": str(root / "v2-operator-proof-latest.json"),
                "v1_operator_root": str(v1_root),
                "v2_eval_root": str(v2_root),
                "v2_eval_receipt": str(v2_root / "v2-eval-latest.json"),
                "phase4_frontier_root": str(frontier_root),
                "v1_monitor": str(v1_root / "monitor-latest.json"),
            },
            "summary": summary,
        }
        _assert_pass(proof)
        _write_json_file(proof, root / "v2-operator-proof-latest.json")

        if args.json:
            print(json.dumps(proof, indent=2, default=str))
        else:
            print(f"AMS_V2_OPERATOR_PROOF_PASS root={root}")
            print(
                "v1_operator="
                f"{summary['v1_operator_status']} monitor={summary['v1_monitor_status']} "
                f"maintenance={summary['v1_maintenance_status']}"
            )
            print(
                "v2_eval="
                f"{summary['v2_eval_verdict']} {summary['v2_eval_pass_count']}/{summary['v2_eval_case_count']} "
                f"false_blocks={summary['v2_eval_false_block_count']}/{summary['v2_eval_false_block_budget']}"
            )
            print(
                "phase="
                f"{summary['v2_phase_status']} ready={summary['v2_ready_for_next_phase']}"
            )
        return 0
    except Exception as exc:
        failure = {"status": "fail", "root": str(root), "error": str(exc)}
        if args.json:
            print(json.dumps(failure, indent=2), file=sys.stdout)
        else:
            print(f"AMS_V2_OPERATOR_PROOF_FAIL root={root}", file=sys.stderr)
            print(str(exc), file=sys.stderr)
        return 1
    finally:
        if temp_dir is not None and not args.keep_root:
            shutil.rmtree(temp_dir, ignore_errors=True)


def _run_v1_operator_proof(
    root: Path,
    *,
    workspace: Path,
    skip_frontier_eval: bool,
    frontier_root: Path,
    commands: list[dict[str, Any]],
) -> dict[str, Any]:
    command = [
        sys.executable,
        str(V1_PROOF),
        "--root",
        str(root),
        "--workspace",
        str(workspace),
        "--json",
    ]
    if skip_frontier_eval:
        command.append("--skip-frontier-eval")
    else:
        command.extend(["--frontier-root", str(frontier_root)])
    return _run_json_command("v1 operator proof", command, commands)


def _run_v2_eval(root: Path, commands: list[dict[str, Any]]) -> dict[str, Any]:
    command = [sys.executable, str(V2_EVAL), "--root", str(root)]
    payload = _run_json_prefix_command("v2 eval harness", command, commands)
    root.mkdir(parents=True, exist_ok=True)
    (root / "v2-eval-latest.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    return payload


def _run_json_command(name: str, command: list[str], commands: list[dict[str, Any]]) -> dict[str, Any]:
    process = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    commands.append(_record(name, command, process))
    if process.returncode != 0:
        raise RuntimeError(f"{name} failed: {process.stderr.strip() or process.stdout.strip()}")
    try:
        return json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{name} did not emit JSON: {process.stdout}") from exc


def _run_json_prefix_command(name: str, command: list[str], commands: list[dict[str, Any]]) -> dict[str, Any]:
    process = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    commands.append(_record(name, command, process))
    if process.returncode != 0:
        raise RuntimeError(f"{name} failed: {process.stderr.strip() or process.stdout.strip()}")
    first_json = process.stdout.split("\n\n", 1)[0]
    try:
        return json.loads(first_json)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{name} did not start with JSON: {process.stdout}") from exc


def _record(name: str, command: list[str], process: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    return {
        "name": name,
        "command": command,
        "returncode": process.returncode,
        "stdout": process.stdout,
        "stderr": process.stderr,
    }


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json_file(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def _executed_case_ids(v2_report: dict[str, Any]) -> list[str]:
    case_ids: list[str] = []
    for row in v2_report.get("rows", []):
        if not isinstance(row, dict):
            continue
        for case in row.get("cases", []):
            if isinstance(case, dict) and isinstance(case.get("case_id"), str):
                case_ids.append(case["case_id"])
    return case_ids


def _assert_pass(proof: dict[str, Any]) -> None:
    summary = proof["summary"]
    failures: list[str] = []
    if summary["v1_operator_status"] != "pass":
        failures.append(f"v1 operator status was {summary['v1_operator_status']}")
    if summary["v1_memory_surfaces_reconciled"] is not True:
        failures.append("v1 memory surfaces did not reconcile")
    if summary["v1_monitor_status"] != "pass":
        failures.append(f"v1 monitor status was {summary['v1_monitor_status']}")
    if summary["v1_maintenance_status"] != "pass":
        failures.append(f"v1 maintenance status was {summary['v1_maintenance_status']}")
    if summary["v1_closed_governed_run_outcome"] != "success":
        failures.append("v1 governed run did not close with success")
    if summary["v1_frontier_eval_verdict"] is not None and summary["v1_frontier_eval_verdict"] != "PASS":
        failures.append(f"frontier eval verdict was {summary['v1_frontier_eval_verdict']}")
    if summary["v2_eval_verdict"] != "PASS":
        failures.append(f"v2 eval verdict was {summary['v2_eval_verdict']}")
    if summary["v2_eval_case_count"] != 13:
        failures.append(f"v2 eval case count was {summary['v2_eval_case_count']}")
    if summary["v2_eval_fail_count"] != 0:
        failures.append(f"v2 eval fail count was {summary['v2_eval_fail_count']}")
    if summary["v2_eval_false_block_count"] > summary["v2_eval_false_block_budget"]:
        failures.append("v2 false-block budget exceeded")
    if summary["v2_acceptance_battery_complete"] is not True:
        failures.append(f"v2 executed acceptance battery ids incomplete: {summary['v2_executed_case_ids']}")
    if summary["v2_phase_status"] != "AMS V2 Accepted":
        failures.append(f"v2 phase status was {summary['v2_phase_status']}")
    if summary["v2_ready_for_next_phase"] is not True:
        failures.append("v2 phase is not marked ready")
    if summary["v2_open_followups"] != []:
        failures.append(f"v2 open followups were {summary['v2_open_followups']}")
    if failures:
        raise RuntimeError("; ".join(failures))


if __name__ == "__main__":
    raise SystemExit(main())
