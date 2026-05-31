from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPERATOR_PROOF = ROOT / "scripts" / "run_ams_operator_proof.py"


def test_operator_proof_runs_from_fresh_root_without_global_state(tmp_path):
    root = tmp_path / "fresh-ams-root"
    process = subprocess.run(
        [
            sys.executable,
            str(OPERATOR_PROOF),
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
    assert summary["memory_surfaces_reconciled"] is True
    assert summary["startup_status"] == "allow"
    assert summary["monitor_status"] == "pass"
    assert summary["maintenance_status"] == "pass"
    assert summary["maintenance_item_count"] == 0
    assert summary["audited_memory_id"].startswith("card_")
    assert summary["closed_governed_run_id"].startswith("run_")
    assert summary["closed_governed_run_outcome"] == "success"
    assert (root / "monitor-latest.json").exists()
    assert (root / "maintenance-latest.json").exists()
    assert (root / "startup-brief-latest.json").exists()
