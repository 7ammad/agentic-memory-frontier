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
    load_longmemeval_v2_dataset,
    score_longmemeval_v2_reference_upper_bound,
    summarize_longmemeval_v2_dataset,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a local LongMemEval-V2 dataset root.")
    parser.add_argument("dataset_root", help="Directory containing questions.jsonl and trajectories.jsonl.")
    args = parser.parse_args()

    dataset = load_longmemeval_v2_dataset(args.dataset_root)
    summary = summarize_longmemeval_v2_dataset(args.dataset_root)
    reference_score = score_longmemeval_v2_reference_upper_bound(dataset)
    print(
        json.dumps(
            {
                "summary": summary.model_dump(),
                "reference_upper_bound": reference_score.model_dump(),
                "haystacks": sorted(dataset.haystacks),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
