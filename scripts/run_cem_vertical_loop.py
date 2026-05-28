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

from cem_eval import run_vertical_loop  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the CEM-1 Phase 1 vertical loop.")
    parser.add_argument("--root", default=None, help="Directory for vertical-loop storage.")
    args = parser.parse_args()

    root = Path(args.root) if args.root else Path(tempfile.mkdtemp(prefix="cem-vertical-loop-"))
    report = run_vertical_loop(root)
    print(json.dumps({"root": str(root), "report": report.model_dump()}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
