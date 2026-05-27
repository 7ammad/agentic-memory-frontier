from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "cem-core" / "src"))

from cem_core import CEM, MultiAgentTrustPolicy, SharedTraceEnvelope, import_shared_trace  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Import a CEM-0 shared trace envelope.")
    parser.add_argument("envelope", help="Path to a shared trace envelope JSON file.")
    parser.add_argument("--root", required=True, help="Directory for persistent CEM-0 storage.")
    parser.add_argument(
        "--trusted-agent-id",
        action="append",
        default=[],
        help="Agent id trusted for automatic memory promotion. Repeatable.",
    )
    args = parser.parse_args()

    envelope = SharedTraceEnvelope.model_validate_json(Path(args.envelope).read_text(encoding="utf-8"))
    receipt = import_shared_trace(
        CEM(args.root),
        envelope,
        trust_policy=MultiAgentTrustPolicy(trusted_agent_ids=args.trusted_agent_id),
    )
    print(json.dumps(receipt.model_dump(mode="json"), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
