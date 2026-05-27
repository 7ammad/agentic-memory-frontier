from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for package_src in (
    ROOT / "packages" / "cem-core" / "src",
    ROOT / "packages" / "cem-eval" / "src",
):
    sys.path.insert(0, str(package_src))

from cem_core.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
