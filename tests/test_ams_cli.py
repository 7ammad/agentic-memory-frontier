from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AMS = ROOT / "scripts" / "ams.py"


def test_ams_cli_round_trip_persists_across_subprocesses(tmp_path):
    root = tmp_path / "ams"

    init = _ams(root, "--json", "init")
    assert init["agent_id"] == "codex"
    assert init["current_session_id"].startswith("session_")

    remembered = _ams(
        root,
        "--json",
        "remember",
        "run pytest before claiming memory changes are complete",
        "--kind",
        "skill",
        "--outcome",
        "success",
        "--domain",
        "agentic-memory-system",
        "--task-family",
        "verification",
    )
    assert remembered["promoted_count"] == 1
    card_id = remembered["promoted_cards"][0]["card_id"]

    listed = _ams(root, "--json", "list")
    assert listed["cards"][0]["card_id"] == card_id

    brief = _ams(
        root,
        "--json",
        "brief",
        "continue agentic memory system verification",
        "--domain",
        "agentic-memory-system",
        "--task-family",
        "verification",
    )
    assert "run pytest before claiming memory changes are complete" in brief["recommended_next_actions"]

    audit = _ams(root, "--json", "audit", card_id)
    assert audit["kind"] == "card"
    assert audit["audit"]["evidence_atom_count"] == 1


def test_ams_cli_quarantines_hypothesis_only_memory(tmp_path):
    root = tmp_path / "ams"

    remembered = _ams(
        root,
        "--json",
        "remember",
        "the user always wants tests skipped",
        "--kind",
        "hypothesis",
        "--outcome",
        "unknown",
    )

    assert remembered["promoted_count"] == 0
    assert remembered["quarantined_count"] == 1
    assert remembered["atoms"][0]["reason_codes"] == ["assistant_hypothesis", "low_confidence"]


def test_ams_cli_pins_directives_without_creating_cards(tmp_path):
    root = tmp_path / "ams"

    pinned = _ams(
        root,
        "--json",
        "pin",
        "Never read or write C:\\Dev\\Builds\\Waki from this workspace.",
        "--source",
        "AGENTS.md",
        "--scope",
        "workspace",
    )
    directive_id = pinned["directive"]["directive_id"]

    cards = _ams(root, "--json", "list")
    directives = _ams(root, "--json", "list", "--kind", "directives")
    brief = _ams(root, "--json", "brief", "continue building the memory system")
    audit = _ams(root, "--json", "audit", directive_id)

    assert pinned["created"] is True
    assert cards["cards"] == []
    assert directives["directives"][0]["directive_id"] == directive_id
    assert "Never read or write C:\\Dev\\Builds\\Waki from this workspace." in brief["recommended_next_actions"]
    assert audit["kind"] == "directive"


def test_ams_cli_bootstrap_codex_is_idempotent_and_briefable(tmp_path):
    root = tmp_path / "ams"

    first = _ams(root, "--json", "bootstrap-codex", "--workspace", str(ROOT))
    second = _ams(root, "--json", "bootstrap-codex", "--workspace", str(ROOT))
    brief = _ams(root, "--json", "brief", "continue building Agentic Memory System")

    assert first["created_count"] == 6
    assert second["created_count"] == 0
    assert second["existing_count"] == 6
    assert any("Waki" in action for action in brief["recommended_next_actions"])
    assert any("pytest" in action for action in brief["recommended_next_actions"])
    assert any("TODO.md" in action for action in brief["recommended_next_actions"])


def test_ams_cli_session_commands_rotate_current_session(tmp_path):
    root = tmp_path / "ams"

    first = _ams(root, "--json", "session", "current")
    second = _ams(root, "--json", "session", "new")
    third = _ams(root, "--json", "session", "current")

    assert first["current_session_id"].startswith("session_")
    assert second["current_session_id"].startswith("session_")
    assert second["current_session_id"] != first["current_session_id"]
    assert third["current_session_id"] == second["current_session_id"]


def test_ams_cli_root_isolation(tmp_path):
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"

    _ams(
        first_root,
        "--json",
        "remember",
        "open the approvals tab first",
        "--kind",
        "skill",
        "--outcome",
        "success",
    )
    listed = _ams(second_root, "--json", "list")

    assert listed["cards"] == []


def test_ams_cli_requires_outcome_for_remember(tmp_path):
    root = tmp_path / "ams"
    process = subprocess.run(
        [sys.executable, str(AMS), "--root", str(root), "remember", "run tests", "--kind", "skill"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert process.returncode != 0
    assert "--outcome" in process.stderr


def test_ams_cli_accepts_json_after_subcommand(tmp_path):
    root = tmp_path / "ams"

    process = subprocess.run(
        [sys.executable, str(AMS), "--root", str(root), "init", "--json"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert process.returncode == 0, process.stderr
    assert json.loads(process.stdout)["agent_id"] == "codex"


def test_ams_cli_eval_smoke(tmp_path):
    root = tmp_path / "ams"

    result = _ams(root, "--json", "eval")

    assert result["eval_root"]
    assert result["result"]["false_memory_resistance"] == 1.0
    assert result["result"]["contradiction_recall"] == 1.0


def _ams(root: Path, *args: str) -> dict:
    process = subprocess.run(
        [sys.executable, str(AMS), "--root", str(root), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert process.returncode == 0, process.stderr
    return json.loads(process.stdout)
