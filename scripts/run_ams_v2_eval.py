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

from cem_eval.v2_eval_harness import run_v2_eval_harness  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the AMS V2 acceptance eval harness.")
    parser.add_argument("--root", default=None, help="Directory for temporary V2 eval storage.")
    args = parser.parse_args()

    root = Path(args.root) if args.root else Path(tempfile.mkdtemp(prefix="ams-v2-eval-"))
    report = run_v2_eval_harness(root)

    print(json.dumps({"root": str(root), "report": report.model_dump()}, indent=2, default=str))
    print()
    print(
        f"AMS_V2_EVAL_{report.verdict}: "
        f"{report.pass_count}/{report.case_count} cases passed; "
        f"false_blocks={report.false_block_count}/{report.false_block_budget}"
    )
    for row in report.rows:
        print(
            f"  {row.suite_name}: {row.pass_count}/{row.case_count} "
            f"{row.primary_metric_name}={row.primary_metric_value:.3f}"
        )
    return 0 if report.verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
