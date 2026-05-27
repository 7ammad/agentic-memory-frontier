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
    load_memoryarena_dataset,
    score_memoryarena_reference_upper_bound,
    summarize_memoryarena_dataset,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a local MemoryArena dataset export.")
    parser.add_argument("dataset", help="Path to a MemoryArena JSON, JSONL, or directory of JSON/JSONL files.")
    parser.add_argument("--domain", default=None, help="Optional MemoryArena domain/config name.")
    args = parser.parse_args()

    dataset = load_memoryarena_dataset(args.dataset, domain=args.domain)
    summary = summarize_memoryarena_dataset(args.dataset, domain=args.domain)
    reference_score = score_memoryarena_reference_upper_bound(dataset)
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
