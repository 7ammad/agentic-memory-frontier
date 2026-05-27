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


def test_ams_cli_migration_dry_run_writes_ledger_without_mutating_memory(tmp_path):
    root = tmp_path / "ams"
    memory_base = _legacy_memory_base(tmp_path)

    result = _ams(root, "--json", "migrate", "dry-run", "--memory-base", str(memory_base))
    directives = _ams(root, "--json", "list", "--kind", "directives")
    cards = _ams(root, "--json", "list")

    assert result["applied"] is False
    assert result["pin_count"] == 4
    assert result["remember_count"] == 1
    assert result["skip_count"] == 1
    assert directives["directives"] == []
    assert cards["cards"] == []
    assert (root / "migration-runs.jsonl").exists()
    assert (root / "migration-latest.json").exists()
    assert (root / "migration-latest.md").exists()


def test_ams_cli_migration_apply_is_idempotent(tmp_path):
    root = tmp_path / "ams"
    memory_base = _legacy_memory_base(tmp_path)

    first = _ams(root, "--json", "migrate", "apply", "--memory-base", str(memory_base))
    second = _ams(root, "--json", "migrate", "apply", "--memory-base", str(memory_base))
    directives = _ams(root, "--json", "list", "--kind", "directives")
    cards = _ams(root, "--json", "list")

    assert first["applied"] is True
    assert first["applied_pin_count"] == 4
    assert first["applied_remember_count"] == 1
    assert second["applied_pin_count"] == 0
    assert second["applied_remember_count"] == 0
    assert second["existing_count"] == 5
    assert len(directives["directives"]) == 4
    assert len(cards["cards"]) == 1


def test_ams_cli_monitor_and_dashboard_records_status(tmp_path):
    root = tmp_path / "ams"

    _ams(root, "--json", "bootstrap-codex", "--workspace", str(ROOT))
    _ams(
        root,
        "--json",
        "remember",
        "run python scripts/ams.py brief before continuing Agentic Memory System work",
        "--kind",
        "skill",
        "--outcome",
        "success",
        "--domain",
        "agentic-memory-system",
    )
    monitor = _ams(root, "--json", "monitor")
    dashboard = _ams(root, "--json", "dashboard")

    assert monitor["status"] == "pass"
    assert (root / "monitor-runs.jsonl").exists()
    assert (root / "monitor-latest.json").exists()
    assert (root / "monitor-latest.md").exists()
    assert dashboard["latest_monitor"]["run_id"] == monitor["run_id"]
    assert dashboard["card_count"] == 1
    assert dashboard["directive_count"] == 6


def test_ams_cli_monitor_fails_visibly_when_memory_is_not_seeded(tmp_path):
    root = tmp_path / "ams"

    result = _ams(root, "--json", "monitor")

    assert result["status"] == "fail"
    assert any(check["status"] == "fail" for check in result["checks"])


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


def _legacy_memory_base(tmp_path: Path) -> Path:
    memory_base = tmp_path / "legacy-memory"
    memory_base.mkdir()
    (memory_base / "MEMORY.md").write_text(
        "\n".join(
            [
                "# Task Group: C:\\Dev\\Builds\\Agentic Memory System / CEM-0 foundation pivot",
                "scope: Agentic Memory System after the pivot away from universal onboarding.",
                "",
                "## Reusable knowledge",
                "- The project pivot is explicit: Causal Experience Memory.",
                "- The first implementation wedge is CEM-0 / MemGuard Kernel.",
                "- The immediate next-work queue is verification.",
                "",
                "## Failures and how to do differently",
                "- Symptom: drift back into platform-first framing.",
                "- Symptom: overstate current extractor.",
                "",
                "# Task Group: Other Project",
                "scope: unrelated",
            ]
        ),
        encoding="utf-8",
    )
    return memory_base
