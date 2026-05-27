from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for package_src in (
    ROOT / "packages" / "cem-core" / "src",
    ROOT / "packages" / "cem-eval" / "src",
):
    sys.path.insert(0, str(package_src))

from cem_eval import (  # noqa: E402
    build_external_benchmark_report_from_json_files,
    render_external_benchmark_report_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a unified CEM-0 external benchmark report from runner JSON outputs."
    )
    parser.add_argument("--halumem-result", default=None, help="JSON output from run_halumem_cem0_eval.py.")
    parser.add_argument("--memoryarena-result", default=None, help="JSON output from run_memoryarena_cem0_eval.py.")
    parser.add_argument(
        "--longmemeval-v2-result",
        default=None,
        help="JSON output from run_longmemeval_v2_cem0_eval.py.",
    )
    parser.add_argument("--markdown", action="store_true", help="Render markdown instead of JSON.")
    args = parser.parse_args()

    report = build_external_benchmark_report_from_json_files(
        halumem_result_path=args.halumem_result,
        memoryarena_result_path=args.memoryarena_result,
        longmemeval_v2_result_path=args.longmemeval_v2_result,
    )
    if args.markdown:
        print(render_external_benchmark_report_markdown(report), end="")
    else:
        print(json.dumps(report.model_dump(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
