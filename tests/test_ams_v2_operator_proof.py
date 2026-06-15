from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
V2_OPERATOR_PROOF = ROOT / "scripts" / "run_ams_v2_operator_proof.py"


def test_v2_operator_proof_runs_from_fresh_root_without_global_state(tmp_path):
    root = tmp_path / "fresh-ams-v2-root"
    process = subprocess.run(
        [
            sys.executable,
            str(V2_OPERATOR_PROOF),
            "--root",
            str(root),
            "--skip-frontier-eval",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert process.returncode == 0, process.stderr
    payload = json.loads(process.stdout)
    assert payload["status"] == "pass"
    summary = payload["summary"]
    assert summary["v1_operator_status"] == "pass"
    assert summary["v1_memory_surfaces_reconciled"] is True
    assert summary["v1_monitor_status"] == "pass"
    assert summary["v1_maintenance_status"] == "pass"
    assert summary["v2_eval_verdict"] == "PASS"
    assert summary["v2_eval_case_count"] == 13
    assert summary["v2_eval_false_block_count"] == 0
    assert summary["v2_eval_false_block_budget"] == 0
    assert summary["v2_acceptance_battery_complete"] is True
    assert len(summary["v2_executed_case_ids"]) == len(set(summary["v2_executed_case_ids"])) == 13
    assert summary["v2_phase_status"] == "AMS V2 Accepted"
    assert summary["v2_ready_for_next_phase"] is True
    proof_root = Path(payload["root"])
    assert proof_root.parent == root
    artifacts = payload["artifacts"]
    assert Path(artifacts["v2_operator_proof"]) == proof_root / "v2-operator-proof-latest.json"
    assert Path(artifacts["v2_operator_proof"]).exists()
    assert Path(artifacts["v2_eval_receipt"]) == proof_root / "v2-eval" / "v2-eval-latest.json"
    assert Path(artifacts["v2_eval_receipt"]).exists()
    assert Path(artifacts["phase4_frontier_root"]) == proof_root / "phase4-frontier"
    assert (proof_root / "v1-operator" / "monitor-latest.json").exists()
    assert (proof_root / "v2-eval").exists()


def test_v2_operator_proof_reuses_documented_parent_without_reusing_state(tmp_path):
    root = tmp_path / "repeatable-proof-root"
    first = subprocess.run(
        [
            sys.executable,
            str(V2_OPERATOR_PROOF),
            "--root",
            str(root),
            "--skip-frontier-eval",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    second = subprocess.run(
        [
            sys.executable,
            str(V2_OPERATOR_PROOF),
            "--root",
            str(root),
            "--skip-frontier-eval",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    first_payload = json.loads(first.stdout)
    second_payload = json.loads(second.stdout)
    assert first_payload["root"] != second_payload["root"]
    assert Path(first_payload["root"]).parent == root
    assert Path(second_payload["root"]).parent == root
