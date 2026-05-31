import json
import subprocess
import sys
from pathlib import Path

from cem_core.storage import SQLiteStore

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_cem_vertical_loop.py"


def test_script_runs_and_persists_real_objects(tmp_path):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["report"]["n"] >= 1
    assert payload["report"]["brief_record_count"] >= 1
    # hard-to-fake: a real brief record must exist in the persisted root
    store = SQLiteStore(Path(payload["root"]))
    assert store.list_cards(), "expected promoted candidate cards in the persisted root"
