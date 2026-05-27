from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "cem-core" / "src"))

from cem_core.mcp_stdio import run_stdio_server  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the CEM-0 MCP stdio tool server.")
    parser.add_argument("--root", required=True, help="Directory for persistent CEM-0 storage.")
    args = parser.parse_args()

    run_stdio_server(args.root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
