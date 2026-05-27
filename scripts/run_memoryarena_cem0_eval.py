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

from cem_eval import run_memoryarena_cem0_eval  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run CEM-0 action-brief scoring on a MemoryArena export.")
    parser.add_argument("dataset", help="Path to a MemoryArena JSON, JSONL, or directory of JSON/JSONL files.")
    parser.add_argument("--domain", default=None, help="Optional MemoryArena domain/config name.")
    parser.add_argument("--root", default=None, help="Directory for temporary CEM-0 eval storage.")
    args = parser.parse_args()

    root = Path(args.root) if args.root else Path(tempfile.mkdtemp(prefix="cem-memoryarena-"))
    result = run_memoryarena_cem0_eval(args.dataset, root, domain=args.domain)
    print(json.dumps({"root": str(root), "result": result.model_dump()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
