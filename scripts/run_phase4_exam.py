from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for package_src in (
    ROOT / "packages" / "cem-core" / "src",
    ROOT / "packages" / "cem-eval" / "src",
):
    sys.path.insert(0, str(package_src))

from cem_eval.phase4_exam import run_phase4_exam  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the CEM-1 Phase 4 MMA + 10-baseline held-out exam."
    )
    parser.add_argument("--root", default=None, help="Directory for temporary exam storage.")
    args = parser.parse_args()

    root = Path(args.root) if args.root else Path(tempfile.mkdtemp(prefix="cem-phase4-"))
    report = run_phase4_exam(root)

    print(json.dumps({"root": str(root), "report": report.model_dump()}, indent=2, default=str))
    print()
    print("BASELINE LADDER (MMA vs no_memory, 95% CI):")
    for rung in report.rungs:
        flag = " [ceiling]" if rung.is_ceiling else ""
        print(f"  {rung.name:22} {rung.mma:6.3f}  [{rung.ci_low:6.3f}, {rung.ci_high:6.3f}]{flag}")
    print()
    print(report.headline)
    # Exit code reflects the single-shot verdict (PASS=0, honest miss=1).
    return 0 if report.verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
