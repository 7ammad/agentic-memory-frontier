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
    load_halumem_dataset,
    score_halumem_reference_upper_bound,
    summarize_halumem_dataset,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a local HaluMem dataset export.")
    parser.add_argument("dataset", help="Path to a HaluMem JSON, JSONL, or directory of JSON/JSONL files.")
    args = parser.parse_args()

    dataset = load_halumem_dataset(args.dataset)
    summary = summarize_halumem_dataset(args.dataset)
    reference_score = score_halumem_reference_upper_bound(dataset)
    print(
        json.dumps(
            {
                "summary": summary.model_dump(),
                "reference_upper_bound": reference_score.model_dump(),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
