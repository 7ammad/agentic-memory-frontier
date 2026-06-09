from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import timedelta
from pathlib import Path

import pytest

from cem_core import CEM, ExperienceCard
from cem_core import operations
from cem_core.local_memory import _active_product_directive_content

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


def test_ams_cli_brief_matches_scoped_directive_by_content_tokens(tmp_path):
    root = tmp_path / "ams"

    directive = (
        "When Hammad brings a high-conviction system build such as unified KB, "
        "massive tool registry, Hermes/Kai agent infrastructure, source capture, "
        "resolver, or organizational AI layer, do not trim it into a cautious "
        "Markdown skeleton."
    )
    _ams(
        root,
        "--json",
        "pin",
        directive,
        "--scope",
        "global",
        "--domain",
        "codex-behavior",
        "--task-family",
        "bold-system-builds",
    )

    brief = _ams(
        root,
        "--json",
        "brief",
        "build a unified KB, massive tools registry, Hermes Kai agent infrastructure, source capture resolver, and organizational AI layer",
    )
    unrelated = _ams(root, "--json", "brief", "continue the small pytest verification task")

    assert directive in brief["recommended_next_actions"]
    assert directive not in unrelated["recommended_next_actions"]


def test_ams_cli_bootstrap_codex_is_idempotent_and_briefable(tmp_path):
    root = tmp_path / "ams"

    first = _ams(root, "--json", "bootstrap-codex", "--workspace", str(ROOT))
    second = _ams(root, "--json", "bootstrap-codex", "--workspace", str(ROOT))
    brief = _ams(root, "--json", "brief", "continue building Agentic Memory System")

    assert first["created_count"] == 7
    assert second["created_count"] == 0
    assert second["existing_count"] == 7
    assert any("Waki" in action for action in brief["recommended_next_actions"])
    assert any("pytest" in action for action in brief["recommended_next_actions"])
    assert any("TODO.md" in action for action in brief["recommended_next_actions"])
    assert any("Capture live user corrections" in action for action in brief["recommended_next_actions"])


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


def test_ams_cli_memory_surfaces_reconcile_legacy_and_codex_memory(tmp_path):
    root = tmp_path / "ams"
    memory_base = _legacy_memory_base(tmp_path)
    config_path = _codex_config(tmp_path, root)

    migration = _ams(root, "--json", "migrate", "apply", "--memory-base", str(memory_base))
    report = _ams(
        root,
        "--json",
        "memory-surfaces",
        "--config-path",
        str(config_path),
        "--memory-base",
        str(memory_base),
    )
    _ams(root, "--json", "migrate", "dry-run", "--memory-base", str(memory_base))
    report_after_dry_run = _ams(
        root,
        "--json",
        "memory-surfaces",
        "--config-path",
        str(config_path),
        "--memory-base",
        str(memory_base),
    )
    surfaces = {surface["name"]: surface for surface in report["surfaces"]}

    assert migration["applied"] is True
    assert report["reconciled"] is True
    assert report_after_dry_run["reconciled"] is True
    assert surfaces["ams-memory"]["role"] == "primary"
    assert surfaces["ams-memory"]["status"] == "pass"
    assert surfaces["codex-memory"]["role"] == "secondary"
    assert surfaces["codex-memory"]["status"] == "pass"
    assert surfaces["native-codex-memory"]["role"] == "secondary_import_source"
    assert surfaces["native-codex-memory"]["status"] == "pass"


def test_ams_cli_memory_surfaces_accept_ams_mcp_root_arg_without_env(tmp_path):
    root = tmp_path / "ams"
    memory_base = _legacy_memory_base(tmp_path)
    config_path = _codex_config_with_ams_root_arg(tmp_path, root)

    _ams(root, "--json", "migrate", "apply", "--memory-base", str(memory_base))
    report = _ams(
        root,
        "--json",
        "memory-surfaces",
        "--config-path",
        str(config_path),
        "--memory-base",
        str(memory_base),
    )
    surfaces = {surface["name"]: surface for surface in report["surfaces"]}

    assert report["reconciled"] is True
    assert surfaces["ams-memory"]["status"] == "pass"
    assert surfaces["ams-memory"]["source_path"] == str(root.resolve())


def test_ams_cli_memory_surfaces_reconcile_ams_only_when_native_memory_disabled(tmp_path):
    root = tmp_path / "ams"
    memory_base = _legacy_memory_base(tmp_path)
    config_path = _codex_config_with_ams_only_and_native_disabled(tmp_path, root)

    report = _ams(
        root,
        "--json",
        "memory-surfaces",
        "--config-path",
        str(config_path),
        "--memory-base",
        str(memory_base),
    )
    surfaces = {surface["name"]: surface for surface in report["surfaces"]}

    assert report["reconciled"] is True
    assert surfaces["ams-memory"]["role"] == "primary"
    assert surfaces["ams-memory"]["status"] == "pass"
    assert surfaces["codex-memory"]["role"] == "unconfigured"
    assert surfaces["codex-memory"]["status"] == "warn"
    assert surfaces["native-codex-memory"]["role"] == "secondary_import_source"
    assert surfaces["native-codex-memory"]["status"] == "pass"
    assert "disabled by Codex config" in surfaces["native-codex-memory"]["detail"]

    _seed_runtime_records(root)
    monitor = _ams(root, "--json", "monitor")
    assert _check_status(monitor, "memory_surfaces_reconciled") == "pass"
    assert "codex-memory optional bridge unconfigured" in _check_detail(monitor, "memory_surfaces_reconciled")
    assert "native Codex memory disabled/import-only" in _check_detail(monitor, "memory_surfaces_reconciled")


def test_ams_cli_memory_surfaces_reject_ams_only_when_native_memory_not_disabled(tmp_path):
    root = tmp_path / "ams"
    memory_base = tmp_path / "empty-memory-base"
    memory_base.mkdir()
    config_path = _codex_config_with_ams_only(tmp_path, root)

    report = _ams(
        root,
        "--json",
        "memory-surfaces",
        "--config-path",
        str(config_path),
        "--memory-base",
        str(memory_base),
    )
    surfaces = {surface["name"]: surface for surface in report["surfaces"]}

    assert report["reconciled"] is False
    assert surfaces["ams-memory"]["role"] == "primary"
    assert surfaces["ams-memory"]["status"] == "pass"
    assert surfaces["codex-memory"]["role"] == "unconfigured"
    assert surfaces["native-codex-memory"]["role"] == "unconfigured"
    assert "disabled by Codex config" not in surfaces["native-codex-memory"]["detail"]


def test_ams_cli_memory_surfaces_warn_until_legacy_migration_applied(tmp_path):
    root = tmp_path / "ams"
    memory_base = _legacy_memory_base(tmp_path)
    config_path = _codex_config(tmp_path, root)

    report = _ams(
        root,
        "--json",
        "memory-surfaces",
        "--config-path",
        str(config_path),
        "--memory-base",
        str(memory_base),
    )
    surfaces = {surface["name"]: surface for surface in report["surfaces"]}

    assert report["reconciled"] is False
    assert surfaces["ams-memory"]["status"] == "pass"
    assert surfaces["codex-memory"]["role"] == "secondary"
    assert surfaces["native-codex-memory"]["status"] == "warn"
    assert "latest applied AMS migration" in surfaces["native-codex-memory"]["detail"]


def test_ams_cli_monitor_and_dashboard_records_status(tmp_path):
    root = tmp_path / "ams"

    _seed_runtime_control_root(root)
    monitor = _ams(root, "--json", "monitor")
    dashboard = _ams(root, "--json", "dashboard")

    assert monitor["status"] == "pass"
    assert monitor["scope"]["ams_directive_count"] == 11
    assert monitor["phase"]["completed_through"].startswith("AMS v1 product lock")
    assert monitor["phase"]["current_phase"] == "AMS v1 Accepted"
    assert (
        monitor["phase"]["next_step"]
        == "none - AMS v1 terminal acceptance contract is complete"
    )
    assert "wire Correction Capture Controller" not in monitor["phase"]["next_step"]
    assert "reconcile legacy Codex memories" not in monitor["phase"]["next_step"]
    assert "real trace intake" not in monitor["phase"]["next_step"]
    assert "aging and maintenance" not in monitor["phase"]["next_step"]
    assert monitor["phase"]["ready_for_next_phase"] is True
    assert monitor["phase"]["open_followups"] == []
    assert _check_status(monitor, "memory_surfaces_reconciled") == "pass"
    assert _check_status(monitor, "brief_has_correction_capture_rule") == "pass"
    assert _check_status(monitor, "maintenance_surface_present") == "pass"
    assert _check_status(monitor, "maintenance_no_blocking_risks") == "pass"
    assert (root / "monitor-runs.jsonl").exists()
    assert (root / "monitor-latest.json").exists()
    assert (root / "monitor-latest.md").exists()
    assert (root / "maintenance-runs.jsonl").exists()
    assert (root / "maintenance-latest.json").exists()
    assert (root / "maintenance-latest.md").exists()
    assert dashboard["latest_monitor"]["run_id"] == monitor["run_id"]
    assert dashboard["latest_maintenance"]["status"] == "pass"
    assert dashboard["card_count"] == 2
    assert dashboard["scope"]["ams_card_count"] == 2
    assert dashboard["directive_count"] == 11
    assert dashboard["scope"]["global_behavior_directive_count"] == 0


def test_ams_cli_startup_brief_degrades_unreconciled_memory_surfaces(tmp_path):
    root = tmp_path / "ams"
    _seed_runtime_records(root)

    monitor = _ams(root, "--json", "monitor")
    result = _ams(
        root,
        "--json",
        "startup-brief",
        "continue building Agentic Memory System",
        "--domain",
        "agentic-memory-system",
    )

    assert monitor["status"] == "fail"
    assert _check_status(monitor, "memory_surfaces_reconciled") == "fail"
    assert "not reconciled" in _check_detail(monitor, "memory_surfaces_reconciled")
    assert result["status"] == "degraded"
    assert result["block_reasons"] == []
    assert any(reason.startswith("monitor_failed:") for reason in result["degraded_reasons"])


def test_ams_cli_runtime_control_does_not_block_unrelated_owner_task_on_monitor_failure(tmp_path):
    root = tmp_path / "ams"
    _seed_runtime_records(root)

    result = _ams(
        root,
        "--json",
        "runtime-control",
        "Review third meeting transcript, Claude analysis, and low-quality voice-note transcription options",
        "--domain",
        "mtm-os",
        "--session-id",
        "incident-monitor-failure",
    )

    assert result["status"] == "degraded"
    assert result["runtime_exit_code"] == 0
    assert result["block_reasons"] == []
    assert any(reason.startswith("startup_degraded:monitor_failed:") for reason in result["degraded_reasons"])

    trace = _ams(
        root,
        "--json",
        "runtime-trace",
        "record",
        "--control-id",
        result["control_id"],
        "--command",
        "codex",
        "--exit-code",
        "0",
    )
    stored_trace = CEM(root).store.get_trace(trace["trace_id"])
    closed = _ams(
        root,
        "--json",
        "governed-run",
        "close",
        "--receipt-id",
        result["governed_run_id"],
        "--outcome",
        "success",
        "--action-taken",
        "reviewed owner-directed transcript materials",
    )

    assert trace["runtime_control_status"] == "degraded"
    assert trace["downstream_invoked"] is True
    assert stored_trace.environment["degraded_reasons"] == result["degraded_reasons"]
    assert closed["status"] == "degraded"
    assert closed["closed"] is True
    assert closed["outcome"] == "success"
    assert closed["influence_ids"] == [closed["influence_id"]]


def test_ams_cli_maintenance_review_detects_aging_risks_and_persists_report(tmp_path):
    root = tmp_path / "ams"
    _seed_runtime_control_root(root)
    cem = CEM(root)
    now = operations.utc_now()

    stale_card = cem.store.list_cards()[0]
    stale_card.valid_from = now - timedelta(days=140)
    stale_card.last_validated_at = now - timedelta(days=120)
    cem.store.save_card(stale_card)
    promoted_atom = cem.store.get_atom(stale_card.evidence_atom_ids[0])
    promoted_atom.observed_at = now - timedelta(days=90)
    cem.store.save_atom(promoted_atom)
    cem.store.save_card(
        ExperienceCard(
            card_id="card_expired",
            title="expired startup runbook",
            use_when="agentic-memory-system",
            do=["open the expired startup runbook"],
            evidence_atom_ids=["atom_expired"],
            confidence_score=0.8,
            valid_from=now - timedelta(days=180),
            valid_until=now - timedelta(days=1),
            last_validated_at=now - timedelta(days=100),
            action_brief_template="open the expired startup runbook",
        )
    )
    cem.store.save_card(
        ExperienceCard(
            card_id="card_inactive",
            title="superseded operator note",
            use_when="agentic-memory-system",
            do=["use the superseded note"],
            evidence_atom_ids=["atom_inactive"],
            confidence_score=0.7,
            promotion_status="superseded",
            deactivated_at=now,
            deactivated_reason="superseded by fresher evidence",
            action_brief_template="use the superseded note",
        )
    )
    cem.store.save_card(
        ExperienceCard(
            card_id="card_contradicted",
            title="contradicted operator note",
            use_when="agentic-memory-system",
            do=["review the contradicted note"],
            evidence_atom_ids=["atom_contradicted"],
            confidence_score=0.7,
            valid_from=now - timedelta(days=10),
            last_validated_at=now - timedelta(days=10),
            action_brief_template="review the contradicted note",
            contradicts_card_ids=["card_other_side"],
        )
    )

    result = _ams(root, "--json", "maintenance", "review", "--stale-after-days", "30")
    dashboard = _ams(root, "--json", "dashboard")
    brief = _ams(
        root,
        "--json",
        "brief",
        "open expired startup runbook",
        "--domain",
        "agentic-memory-system",
    )

    assert result["status"] == "fail"
    assert result["summary"]["expired_active_count"] == 1
    assert result["summary"]["stale_active_count"] == 1
    assert result["summary"]["contradicted_active_count"] == 1
    assert result["summary"]["inactive_card_count"] == 1
    assert result["summary"]["pending_atom_count"] == 0
    assert result["summary"]["stale_pending_atom_count"] == 0
    assert result["summary"]["review_item_count"] == 3
    assert {item["memory_id"] for item in result["items"]} == {
        stale_card.card_id,
        "card_expired",
        "card_contradicted",
    }
    assert (root / "maintenance-runs.jsonl").exists()
    assert (root / "maintenance-latest.json").exists()
    assert (root / "maintenance-latest.md").exists()
    assert dashboard["latest_maintenance"]["run_id"] == result["run_id"]
    assert "open the expired startup runbook" not in brief["recommended_next_actions"]


def test_ams_cli_maintenance_review_flags_active_cards_without_freshness_anchor(tmp_path):
    root = tmp_path / "ams"
    _seed_runtime_control_root(root)
    CEM(root).store.save_card(
        ExperienceCard(
            card_id="card_unknown_freshness",
            title="manual card with unknown freshness",
            use_when="agentic-memory-system",
            do=["review the manually inserted card"],
            evidence_atom_ids=["atom_unknown_freshness"],
            confidence_score=0.7,
            action_brief_template="review the manually inserted card",
        )
    )

    result = _ams(root, "--json", "maintenance", "review")
    item = next(item for item in result["items"] if item["memory_id"] == "card_unknown_freshness")

    assert result["status"] == "warn"
    assert result["summary"]["stale_active_count"] == 1
    assert item["status"] == "warn"
    assert "no validation freshness anchor" in item["reason"]
    assert item["age_days"] is None


def test_ams_cli_monitor_names_maintenance_blocking_risks(tmp_path):
    root = tmp_path / "ams"
    _seed_runtime_control_root(root)
    now = operations.utc_now()
    CEM(root).store.save_card(
        ExperienceCard(
            card_id="card_expired",
            title="expired monitor runbook",
            use_when="agentic-memory-system",
            do=["use expired monitor runbook"],
            evidence_atom_ids=["atom_expired"],
            confidence_score=0.8,
            valid_from=now - timedelta(days=180),
            valid_until=now - timedelta(days=1),
            last_validated_at=now - timedelta(days=120),
            action_brief_template="use expired monitor runbook",
        )
    )

    monitor = _ams(root, "--json", "monitor")

    assert monitor["status"] == "fail"
    assert _check_status(monitor, "maintenance_surface_present") == "pass"
    assert _check_status(monitor, "maintenance_no_blocking_risks") == "fail"
    detail = _check_detail(monitor, "maintenance_no_blocking_risks")
    assert "expired_active=1" in detail


def test_ams_cli_bootstrap_scopes_directives_without_checkout_path_name(tmp_path):
    root = tmp_path / "ams"
    workspace = tmp_path / "repo"
    workspace.mkdir()

    _ams(root, "--json", "bootstrap-codex", "--workspace", str(workspace))
    dashboard = _ams(root, "--json", "dashboard")

    assert "Agentic Memory System" not in str(workspace)
    assert dashboard["directive_count"] == 7
    assert dashboard["scope"]["ams_directive_count"] == 7
    assert dashboard["scope"]["other_directive_count"] == 0


def test_ams_cli_dashboard_does_not_scope_ams_by_substring(tmp_path):
    root = tmp_path / "ams"

    _ams(root, "--json", "bootstrap-codex", "--workspace", str(ROOT))
    _ams(
        root,
        "--json",
        "pin",
        "Keep teams params diagrams in the unrelated planning note.",
        "--scope",
        "workspace",
    )
    dashboard = _ams(root, "--json", "dashboard")

    assert dashboard["directive_count"] == 8
    assert dashboard["scope"]["ams_directive_count"] == 7
    assert dashboard["scope"]["other_directive_count"] == 1


def test_ams_cli_dashboard_separates_ams_and_global_behavior_records(tmp_path):
    root = tmp_path / "ams"

    _seed_runtime_control_root(root)
    _ams(
        root,
        "--json",
        "pin",
        "Use the Hermes writing system before drafting long-form posts.",
        "--scope",
        "global",
        "--domain",
        "codex-behavior",
        "--task-family",
        "writing",
    )

    monitor = _ams(root, "--json", "monitor")
    dashboard = _ams(root, "--json", "dashboard")

    assert monitor["status"] == "pass"
    assert dashboard["directive_count"] == 12
    assert dashboard["scope"]["ams_directive_count"] == 11
    assert dashboard["scope"]["global_behavior_directive_count"] == 1
    assert dashboard["scope"]["other_directive_count"] == 0
    assert dashboard["phase"]["completed_through"].startswith("AMS v1 product lock")
    assert dashboard["phase"]["ready_for_next_phase"] is True
    assert dashboard["phase"]["open_followups"] == []


def test_ams_cli_startup_brief_allows_when_required_memory_is_present(tmp_path):
    root = tmp_path / "ams"

    _seed_runtime_control_root(root)

    result = _ams(
        root,
        "--json",
        "startup-brief",
        "continue building Agentic Memory System",
        "--domain",
        "agentic-memory-system",
        "--max-directives",
        "4",
        "--max-cards",
        "1",
        "--max-tokens",
        "120",
    )
    dashboard = _ams(root, "--json", "dashboard")

    assert result["status"] == "allow"
    assert result["governed_run_id"].startswith("run_")
    assert result["action_brief_id"].startswith("brief_")
    assert result["influence_id"].startswith("influence_")
    assert result["monitor_id"].startswith("monitor_")
    assert result["estimated_tokens"] <= result["limits"]["max_tokens"]
    assert result["required_directives"] == {
        "waki_boundary": True,
        "verification_rule": True,
        "todo_rule": True,
    }
    assert len(result["recommended_next_actions"]) <= 5
    action_text = "\n".join(result["recommended_next_actions"])
    assert "AMS/CEM" not in action_text
    assert "Causal Experience Memory" not in action_text
    assert "CEM-0" not in action_text
    assert (root / "startup-brief-runs.jsonl").exists()
    assert (root / "startup-brief-latest.json").exists()
    assert (root / "startup-brief-latest.md").exists()
    assert (root / "governed-run-runs.jsonl").exists()
    assert (root / "governed-run-latest.json").exists()
    assert (root / "governed-run-latest.md").exists()
    assert dashboard["latest_startup_brief"]["brief_id"] == result["brief_id"]
    assert dashboard["latest_governed_run"]["receipt_id"] == result["governed_run_id"]
    assert dashboard["latest_governed_run"]["startup_brief_id"] == result["brief_id"]
    assert dashboard["latest_governed_run"]["action_brief_id"] == result["action_brief_id"]
    assert dashboard["latest_governed_run"]["influence_id"] == result["influence_id"]
    assert dashboard["latest_governed_run"]["monitor_id"] == result["monitor_id"]
    assert dashboard["latest_governed_run"]["evidence_ids"] == result["evidence_ids"]
    assert dashboard["latest_governed_run"]["closed"] is False
    assert dashboard["latest_governed_run"]["outcome"] is None
    assert dashboard["latest_governed_run"]["finalized_at"] is None
    assert dashboard["latest_governed_run"]["influence_ids"] == []


def test_ams_cli_startup_brief_for_waki_does_not_surface_ams_workspace_boundary(tmp_path):
    root = tmp_path / "ams"
    _seed_runtime_control_root(root)

    result = _ams(
        root,
        "--json",
        "startup-brief",
        "continue Waki PR review work",
        "--domain",
        "Waki",
        "--max-cards",
        "1",
    )

    action_text = "\n".join(result["recommended_next_actions"])
    assert result["status"] == "allow"
    assert "Never read or write files under C:\\Dev\\Builds\\Waki" not in action_text
    assert result["required_directives"] == {
        "waki_boundary": True,
        "verification_rule": True,
        "todo_rule": True,
    }


def test_ams_cli_governed_run_close_records_outcome_and_influence(tmp_path):
    root = tmp_path / "ams"
    _seed_runtime_control_root(root)

    startup = _ams(
        root,
        "--json",
        "startup-brief",
        "continue building Agentic Memory System with verification",
        "--domain",
        "agentic-memory-system",
    )
    closed = _ams(
        root,
        "--json",
        "governed-run",
        "close",
        "--receipt-id",
        startup["governed_run_id"],
        "--outcome",
        "success",
        "--action-taken",
        "ran focused and full pytest",
        "--observed-post-brief-delta",
        "0.25",
    )
    second_close = _ams(
        root,
        "--json",
        "governed-run",
        "close",
        "--receipt-id",
        startup["governed_run_id"],
        "--outcome",
        "failure",
        "--action-taken",
        "try to overwrite",
    )
    dashboard = _ams(root, "--json", "dashboard")
    events = CEM(root).store.list_action_influence_events(startup["influence_id"])

    assert closed["closed"] is True
    assert closed["outcome"] == "success"
    assert closed["finalized_at"] is not None
    assert closed["influence_ids"] == [startup["influence_id"]]
    assert second_close == closed
    assert dashboard["latest_governed_run"]["receipt_id"] == startup["governed_run_id"]
    assert dashboard["latest_governed_run"]["closed"] is True
    assert dashboard["latest_governed_run"]["outcome"] == "success"
    assert len(events) == 1
    assert events[0].brief_id == startup["action_brief_id"]
    assert events[0].outcome == "success"
    assert events[0].counterfactual_method == "observational_no_counterfactual"


def test_ams_cli_governed_run_close_fails_without_action_brief_link(tmp_path):
    root = tmp_path / "ams"
    receipt = operations.GovernedRunReceipt(
        root=str(root),
        cwd=str(ROOT),
        status="allow",
        startup_brief_id="brief_legacy",
        monitor_id="monitor_legacy",
        task_description="legacy governed run without action brief",
        domain_scope="agentic-memory-system",
        task_family=None,
        evidence_ids=[],
        block_reasons=[],
    )
    operations._write_governed_run_records(root, receipt)

    process = _ams_process(
        root,
        "--json",
        "governed-run",
        "close",
        "--outcome",
        "success",
    )

    assert process.returncode == 2
    assert "cannot close influence" in process.stderr
    assert json.loads((root / "governed-run-latest.json").read_text(encoding="utf-8"))["closed"] is False


def test_startup_brief_does_not_persist_dangling_governed_run_id_when_receipt_write_fails(tmp_path, monkeypatch):
    root = tmp_path / "ams"
    _seed_runtime_control_root(root)

    def fail_receipt_write(_root: Path, _receipt: operations.GovernedRunReceipt) -> None:
        raise RuntimeError("receipt write failed")

    monkeypatch.setattr(operations, "_write_governed_run_records", fail_receipt_write)

    with pytest.raises(RuntimeError, match="receipt write failed"):
        operations.startup_brief(
            root,
            description="continue building Agentic Memory System with verification",
            domain_scope="agentic-memory-system",
        )

    assert not (root / "startup-brief-latest.json").exists()
    assert not (root / "startup-brief-runs.jsonl").exists()


def test_ams_cli_runtime_control_allows_and_persists_receipt(tmp_path):
    root = tmp_path / "ams"
    _seed_runtime_control_root(root)

    result = _ams(
        root,
        "--json",
        "runtime-control",
        "continue building Agentic Memory System with verification",
        "--session-id",
        "session_allow",
    )

    assert result["status"] == "allow"
    assert result["runtime_exit_code"] == 0
    assert result["enforcement"] == "external_guard"
    assert result["prompt_decision"]["decision"] == "allow"
    assert result["gate_decision"]["decision"] == "allow"
    assert result["startup_brief_id"].startswith("brief_")
    assert result["governed_run_id"].startswith("run_")
    assert result["monitor_id"].startswith("monitor_")
    latest = json.loads((root / "runtime-control-latest.json").read_text(encoding="utf-8"))
    assert latest["control_id"] == result["control_id"]
    dashboard = _ams(root, "--json", "dashboard")
    assert dashboard["latest_runtime_control"]["control_id"] == result["control_id"]


def test_ams_cli_runtime_control_blocks_correction_prompt(tmp_path):
    root = tmp_path / "ams"
    _seed_runtime_control_root(root)

    process = _ams_process(
        root,
        "--json",
        "runtime-control",
        "we already said no scaffolding; stop and record this correction",
        "--session-id",
        "session_block",
    )

    assert process.returncode == 12
    result = json.loads(process.stdout)
    assert result["status"] == "block"
    assert result["runtime_exit_code"] == 12
    assert result["prompt_decision"]["decision"] == "block"
    assert result["gate_decision"]["decision"] == "block"
    assert any(reason.startswith("correction_prompt_blocked:") for reason in result["block_reasons"])
    assert any(reason.startswith("resume_gate_blocked:") for reason in result["block_reasons"])
    assert (root / "correction-latest.json").exists()
    assert (root / "runtime-control-latest.json").exists()


def test_runtime_control_degrades_when_startup_brief_infrastructure_fails(tmp_path, monkeypatch):
    root = tmp_path / "ams"
    _seed_runtime_control_root(root)

    def fail_startup_brief(*args, **kwargs):
        raise RuntimeError("startup database unavailable")

    monkeypatch.setattr(operations, "startup_brief", fail_startup_brief)

    result = operations.runtime_control(
        root,
        description="Review ordinary owner transcript task",
        domain_scope="mtm-os",
        session_id="startup-infra-failure",
    )

    assert result.status == "degraded"
    assert result.runtime_exit_code == 0
    assert result.block_reasons == []
    assert result.startup_brief_id == "startup_brief_unavailable"
    assert result.governed_run_id is None
    assert result.monitor_id == "monitor_unavailable"
    assert any(
        reason.startswith("startup_brief_failed:RuntimeError")
        for reason in result.degraded_reasons
    )


def test_ams_cli_runtime_trace_records_controlled_work_and_candidates(tmp_path):
    root = tmp_path / "ams"
    _seed_runtime_control_root(root)
    control = _ams(
        root,
        "--json",
        "runtime-control",
        "SKILL: check startup brief before edits",
        "--session-id",
        "trace_session",
    )

    result = _ams(
        root,
        "--json",
        "runtime-trace",
        "record",
        "--control-id",
        control["control_id"],
        "--command",
        "codex",
        "--command-arg=--version",
        "--exit-code",
        "0",
    )

    assert result["control_id"] == control["control_id"]
    assert result["runtime_control_status"] == "allow"
    assert result["final_outcome"] == "success"
    assert result["observed_exit_code"] == 0
    assert result["downstream_invoked"] is True
    assert result["proposed_atom_count"] == 1
    assert (root / "runtime-trace-runs.jsonl").exists()
    assert (root / "runtime-trace-latest.json").exists()
    assert (root / "runtime-trace-latest.md").exists()

    dashboard = _ams(root, "--json", "dashboard")
    assert dashboard["latest_runtime_trace"]["trace_id"] == result["trace_id"]
    trace = CEM(root).store.get_trace(result["trace_id"])
    assert trace.final_outcome == "success"
    assert trace.environment["runtime_control_id"] == control["control_id"]
    atom = CEM(root).store.get_atom(result["proposed_atom_ids"][0])
    assert atom.source_trace_ids == [result["trace_id"]]
    assert atom.source_spans[0].text == "check startup brief before edits"


def test_ams_cli_runtime_trace_rejects_missing_control_receipt(tmp_path):
    root = tmp_path / "ams"
    _seed_runtime_control_root(root)

    process = _ams_process(
        root,
        "--json",
        "runtime-trace",
        "record",
        "--control-id",
        "control_missing",
        "--command",
        "codex",
        "--exit-code",
        "0",
    )

    assert process.returncode == 2
    assert "Runtime control receipt not found" in process.stderr
    assert not (root / "runtime-trace-latest.json").exists()


def test_ams_guarded_command_enforces_block_before_downstream_command(tmp_path):
    powershell = shutil.which("powershell")
    if os.name != "nt" or powershell is None:
        return

    root = tmp_path / "ams"
    _seed_runtime_control_root(root)
    sentinel = tmp_path / "blocked-command-ran.txt"
    env = _ams_env(root)
    env["AMS_ROOT"] = str(root)

    process = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "scripts" / "ams-guarded-command.ps1"),
            "-Workspace",
            str(ROOT),
            "-Prompt",
            "we already said no scaffolding; stop and record this correction",
            "-Command",
            "cmd.exe",
            "/c",
            f"echo ran>\"{sentinel}\"",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )

    assert process.returncode == 12
    assert "AMS_RUNTIME_CONTROL_EXIT: 12" in process.stdout
    latest_trace = json.loads((root / "runtime-trace-latest.json").read_text(encoding="utf-8"))
    assert latest_trace["final_outcome"] == "failure"
    assert latest_trace["downstream_invoked"] is False
    latest_run = _ams(root, "--json", "dashboard")["latest_governed_run"]
    assert latest_run["closed"] is True
    assert latest_run["outcome"] == "failure"
    assert not sentinel.exists()


def test_ams_guarded_command_runs_downstream_command_when_allowed(tmp_path):
    powershell = shutil.which("powershell")
    if os.name != "nt" or powershell is None:
        return

    root = tmp_path / "ams"
    _seed_runtime_control_root(root)
    sentinel = tmp_path / "allowed-command-ran.txt"
    env = _ams_env(root)
    env["AMS_ROOT"] = str(root)

    process = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "scripts" / "ams-guarded-command.ps1"),
            "-Workspace",
            str(ROOT),
            "-Prompt",
            "continue building Agentic Memory System with verification",
            "-Command",
            "cmd.exe",
            "/c",
            f"echo ran>\"{sentinel}\"",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )

    assert process.returncode == 0, process.stderr
    assert "AMS_RUNTIME_CONTROL_EXIT: 0" in process.stdout
    latest_trace = json.loads((root / "runtime-trace-latest.json").read_text(encoding="utf-8"))
    assert latest_trace["final_outcome"] == "success"
    assert latest_trace["downstream_invoked"] is True
    latest_run = _ams(root, "--json", "dashboard")["latest_governed_run"]
    assert latest_run["closed"] is True
    assert latest_run["outcome"] == "success"
    assert latest_run["influence_ids"] == [latest_run["influence_id"]]
    assert sentinel.exists()


def test_ams_guarded_command_runs_downstream_when_runtime_control_infrastructure_fails(tmp_path):
    powershell = shutil.which("powershell")
    if os.name != "nt" or powershell is None:
        return

    workspace = tmp_path / "fake-ams"
    scripts = workspace / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "ams.py").write_text(
        "import sys\n"
        "if 'runtime-control' in sys.argv:\n"
        "    print('runtime-control database unavailable')\n"
        "    raise SystemExit(3)\n"
        "raise SystemExit(2)\n",
        encoding="utf-8",
    )
    sentinel = tmp_path / "infra-failure-command-ran.txt"

    process = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "scripts" / "ams-guarded-command.ps1"),
            "-Workspace",
            str(workspace),
            "-Prompt",
            "Review ordinary owner transcript task",
            "-Command",
            "cmd.exe",
            "/c",
            f"echo ran>\"{sentinel}\"",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert process.returncode == 0
    assert sentinel.exists()
    assert "AMS_RUNTIME_CONTROL_EXIT: 3" in process.stdout
    assert "AMS_RUNTIME_CONTROL_DEGRADED" in process.stdout
    assert "AMS_GUARD_BLOCKED" not in process.stdout


def test_ams_guarded_command_runs_downstream_when_ams_script_is_missing(tmp_path):
    powershell = shutil.which("powershell")
    if os.name != "nt" or powershell is None:
        return

    workspace = tmp_path / "fake-ams"
    (workspace / "scripts").mkdir(parents=True)
    sentinel = tmp_path / "missing-ams-command-ran.txt"

    process = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "scripts" / "ams-guarded-command.ps1"),
            "-Workspace",
            str(workspace),
            "-Prompt",
            "Review ordinary owner transcript task",
            "-Command",
            "cmd.exe",
            "/c",
            f"echo ran>\"{sentinel}\"",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert process.returncode == 0
    assert "AMS_RUNTIME_CONTROL_DEGRADED: missing ams.py" in process.stdout
    assert "AMS_GUARD_BLOCKED" not in process.stdout
    assert sentinel.exists()


def test_ams_guarded_command_records_runtime_trace_when_allowed_launch_fails(tmp_path):
    powershell = shutil.which("powershell")
    if os.name != "nt" or powershell is None:
        return

    root = tmp_path / "ams"
    _seed_runtime_control_root(root)
    env = _ams_env(root)
    env["AMS_ROOT"] = str(root)

    process = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "scripts" / "ams-guarded-command.ps1"),
            "-Workspace",
            str(ROOT),
            "-Prompt",
            "continue building Agentic Memory System with verification",
            "-Command",
            "definitely-not-a-command-xyz",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )

    assert process.returncode == 127
    assert "AMS_RUNTIME_CONTROL_EXIT: 0" in process.stdout
    assert "AMS_GUARD_DOWNSTREAM_LAUNCH_FAIL" in process.stderr
    latest_trace = json.loads((root / "runtime-trace-latest.json").read_text(encoding="utf-8"))
    assert latest_trace["final_outcome"] == "failure"
    assert latest_trace["observed_exit_code"] == 127
    assert latest_trace["downstream_invoked"] is True
    latest_run = _ams(root, "--json", "dashboard")["latest_governed_run"]
    assert latest_run["closed"] is True
    assert latest_run["outcome"] == "failure"


def test_session_start_gate_warns_and_allows_unknown_startup_status(tmp_path):
    powershell = shutil.which("powershell")
    if os.name != "nt" or powershell is None:
        return

    workspace = tmp_path / "fake-ams"
    scripts = workspace / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "ams.py").write_text(
        "print('{\"status\":\"weird\",\"block_reasons\":[],\"degraded_reasons\":[]}')\n",
        encoding="utf-8",
    )

    process = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "scripts" / "session-start-gate.ps1"),
            "-Workspace",
            str(workspace),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    combined_output = process.stdout + process.stderr

    assert process.returncode == 0
    assert "unknown AMS startup brief status weird" in combined_output
    assert "SESSION_GATE_DEGRADED" in combined_output
    assert "SESSION_GATE_PASS" not in combined_output


def test_session_start_gate_warns_and_allows_startup_brief_command_failure(tmp_path):
    powershell = shutil.which("powershell")
    if os.name != "nt" or powershell is None:
        return

    workspace = tmp_path / "fake-ams"
    scripts = workspace / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "ams.py").write_text(
        "print('startup brief database unavailable')\n"
        "raise SystemExit(3)\n",
        encoding="utf-8",
    )

    process = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "scripts" / "session-start-gate.ps1"),
            "-Workspace",
            str(workspace),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    combined_output = process.stdout + process.stderr

    assert process.returncode == 0
    assert "startup brief database unavailable" in combined_output
    assert "unable to build AMS startup brief" in combined_output
    assert "SESSION_GATE_DEGRADED" in combined_output


def test_ams_guarded_command_quietly_records_runtime_trace(tmp_path):
    powershell = shutil.which("powershell")
    if os.name != "nt" or powershell is None:
        return

    root = tmp_path / "ams"
    _seed_runtime_control_root(root)
    env = _ams_env(root)
    env["AMS_ROOT"] = str(root)

    process = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "scripts" / "ams-guarded-command.ps1"),
            "-Workspace",
            str(ROOT),
            "-Prompt",
            "continue building Agentic Memory System with verification",
            "-Quiet",
            "-Command",
            "cmd.exe",
            "/c",
            "echo RAW_OK",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )

    assert process.returncode == 0, process.stderr
    assert process.stdout.strip() == "RAW_OK"
    latest_trace = json.loads((root / "runtime-trace-latest.json").read_text(encoding="utf-8"))
    assert latest_trace["final_outcome"] == "success"
    assert latest_trace["observed_exit_code"] == 0


def test_ams_guarded_command_quiet_mode_surfaces_trace_recording_failure(tmp_path):
    powershell = shutil.which("powershell")
    if os.name != "nt" or powershell is None:
        return

    root = tmp_path / "ams"
    _seed_runtime_control_root(root)
    env = _ams_env(root)
    env["AMS_ROOT"] = str(root)
    control_log = root / "runtime-control-runs.jsonl"

    process = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "scripts" / "ams-guarded-command.ps1"),
            "-Workspace",
            str(ROOT),
            "-Prompt",
            "continue building Agentic Memory System with verification",
            "-Quiet",
            "-Command",
            "cmd.exe",
            "/c",
            f"del /q \"{control_log}\" && echo RAW_OK",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )

    assert process.returncode == 0
    assert process.stdout.strip() == "RAW_OK"
    assert "AMS_TRACE_RECORD_FAIL" in process.stderr
    assert "Runtime control receipt not found" in process.stderr
    assert not (root / "runtime-trace-latest.json").exists()
    latest_run = _ams(root, "--json", "dashboard")["latest_governed_run"]
    assert latest_run["closed"] is True
    assert latest_run["outcome"] == "success"


def test_ams_cli_startup_brief_degrades_when_required_memory_is_missing(tmp_path):
    root = tmp_path / "ams"

    result = _ams(
        root,
        "--json",
        "startup-brief",
        "continue building Agentic Memory System",
        "--domain",
        "agentic-memory-system",
    )

    assert result["status"] == "degraded"
    assert result["governed_run_id"].startswith("run_")
    assert result["block_reasons"] == []
    assert "missing_required_directive:waki_boundary" in result["degraded_reasons"]
    assert any(reason.startswith("monitor_failed:") for reason in result["degraded_reasons"])
    latest = _ams(root, "--json", "dashboard")["latest_governed_run"]
    assert latest["receipt_id"] == result["governed_run_id"]
    assert latest["status"] == "degraded"
    assert latest["block_reasons"] == []
    assert latest["degraded_reasons"] == result["degraded_reasons"]
    assert latest["closed"] is False
    assert latest["outcome"] is None


def test_ams_cli_startup_brief_human_output_uses_controller_printer(tmp_path):
    root = tmp_path / "ams"
    _seed_runtime_control_root(root)

    process = subprocess.run(
        [
            sys.executable,
            str(AMS),
            "--root",
            str(root),
            "startup-brief",
            "continue building Agentic Memory System",
            "--domain",
            "agentic-memory-system",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_ams_env(root),
        check=False,
    )

    assert process.returncode == 0, process.stderr
    assert "startup_brief: allow brief_" in process.stdout
    assert "governed_run: run_" in process.stdout
    assert "confidence:" not in process.stdout


def test_ams_cli_brief_renders_legacy_directives_in_ams_language(tmp_path):
    root = tmp_path / "ams"
    _ams(
        root,
        "--json",
        "pin",
        "Keep the active thesis centered on Causal Experience Memory: memory is verified experience that improves future action.",
        "--scope",
        "global",
    )
    _ams(
        root,
        "--json",
        "pin",
        "Do not claim state-of-the-art for CEM-0 or AMS v1.",
        "--scope",
        "global",
    )

    brief = _ams(
        root,
        "--json",
        "brief",
        "continue building Agentic Memory System",
        "--domain",
        "agentic-memory-system",
    )
    action_text = "\n".join(brief["recommended_next_actions"])

    assert "Keep AMS centered on verified experience" in action_text
    assert "Do not claim state-of-the-art for AMS." in action_text
    assert "Causal Experience Memory" not in action_text
    assert "CEM-0" not in action_text


def test_active_product_directive_rewrite_removes_legacy_identity_tokens():
    legacy_inputs = [
        "Keep the active thesis centered on Causal Experience Memory: memory is verified experience that improves future action.",
        "Capture live user corrections immediately: stop the active lane, name the mistake, record affected files/actions, route the event to AMS/CEM/project ledger as appropriate, and require explicit resume before continuing.",
        "run pytest and synthetic eval before claiming CEM or AMS memory changes are complete",
        "The CEM-1 proof must not reuse CEM-0 fake-green claims.",
    ]
    forbidden = ("AMS/CEM", "CEM or AMS", "Causal Experience Memory", "CEM-0", "CEM-1", "CEM proof")

    for content in legacy_inputs:
        rendered = _active_product_directive_content(content)
        assert all(token not in rendered for token in forbidden)


def test_ams_cli_correction_capture_records_plan_first_violation_and_blocks_resume(tmp_path):
    root = tmp_path / "ams"
    ledger = tmp_path / "PROJECT-LEDGER.md"
    ledger.write_text("# Project Ledger\n\n## Open Follow-Ups\n\n- existing follow-up\n", encoding="utf-8")

    event = _ams(
        root,
        "--json",
        "correction",
        "capture",
        "why are you building before planning; the full plan was approved first",
        "--affected-file",
        "package.json",
        "--affected-file",
        "src/types.ts",
        "--affected-action",
        "created implementation files before plan approval",
        "--project-ledger",
        str(ledger),
    )
    gate = _ams(root, "--json", "correction", "gate")
    brief = _ams(
        root,
        "--json",
        "brief",
        "plan first correction capture resume approval",
        "--domain",
        "agentic-memory-system",
        "--task-family",
        "mistake-capture",
    )
    monitor = _ams(root, "--json", "monitor")
    startup = _ams(
        root,
        "--json",
        "startup-brief",
        "Review third meeting transcript after an unresolved owner correction",
        "--domain",
        "mtm-os",
    )

    assert event["resume_status"] == "blocked"
    assert event["resume_required"] is True
    assert "premature_implementation" in event["categories"]
    assert "workflow_violation" in event["categories"]
    assert "human_approval_gate" in event["route_targets"]
    assert "ams_candidate_experience_atom" in event["route_targets"]
    assert "cem_candidate_experience_atom" not in event["route_targets"]
    assert event["affected_files"] == ["package.json", "src/types.ts"]
    assert (root / "correction-events.jsonl").exists()
    assert (root / "correction-latest.json").exists()
    assert gate["status"] == "blocked"
    assert gate["active_event_id"] == event["event_id"]
    ledger_text = ledger.read_text(encoding="utf-8")
    assert "Correction Capture Controller" in ledger_text
    assert ledger_text.index("LEDGER-CORRECTION") < ledger_text.index("## Open Follow-Ups")
    assert any("avoid continuing after live correction" in action for action in brief["recommended_next_actions"])
    assert monitor["status"] == "fail"
    assert _check_status(monitor, "correction_resume_gate_clear") == "fail"
    assert startup["status"] == "degraded"
    assert startup["block_reasons"] == []
    assert any(
        reason.startswith("monitor_failed:")
        for reason in startup["degraded_reasons"]
    )

    control_process = _ams_process(
        root,
        "--json",
        "runtime-control",
        "Review third meeting transcript after an unresolved owner correction",
        "--domain",
        "mtm-os",
        "--session-id",
        "unresolved-correction-gate",
    )
    assert control_process.returncode == 12
    control = json.loads(control_process.stdout)
    assert control["status"] == "block"
    assert control["prompt_decision"]["decision"] == "allow"
    assert control["gate_decision"]["decision"] == "block"
    assert any(reason.startswith("resume_gate_blocked:") for reason in control["block_reasons"])

    resumed = _ams(
        root,
        "--json",
        "correction",
        "resume",
        event["event_id"],
        "--approved-by",
        "Hammad",
        "--note",
        "plan-first correction recorded",
    )
    cleared = _ams(root, "--json", "correction", "gate")
    listed = _ams(root, "--json", "correction", "list")

    assert resumed["gate"]["status"] == "clear"
    assert cleared["status"] == "clear"
    assert listed["events"][0]["resume_status"] == "resumed"


def test_ams_cli_correction_capture_links_repeated_memory_drift(tmp_path):
    root = tmp_path / "ams"

    event = _ams(
        root,
        "--json",
        "correction",
        "capture",
        "we already said no scaffolding again, save this to memory",
        "--stale-memory-id",
        "directive_old",
    )
    stale_route = next(route for route in event["routes"] if route["target"] == "stale_or_contradicted_memory")

    assert "repeated_drift" in event["categories"]
    assert "memory_miss" in event["categories"]
    assert stale_route["status"] == "written"
    assert stale_route["ids"] == ["directive_old"]


def test_ams_cli_monitor_fails_visibly_when_memory_is_not_seeded(tmp_path):
    root = tmp_path / "ams"

    result = _ams(root, "--json", "monitor")

    assert result["status"] == "fail"
    assert any(check["status"] == "fail" for check in result["checks"])


def _ams(root: Path, *args: str) -> dict:
    process = _ams_process(root, *args)
    assert process.returncode == 0, process.stderr
    return json.loads(process.stdout)


def _ams_process(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    process = subprocess.run(
        [sys.executable, str(AMS), "--root", str(root), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_ams_env(root),
        check=False,
    )
    return process


def _ams_env(root: Path) -> dict[str, str]:
    env = os.environ.copy()
    config_path = root.parent / "config.toml"
    memory_base = root.parent / "legacy-memory"
    if config_path.exists():
        env["AMS_CODEX_CONFIG_PATH"] = str(config_path)
    if memory_base.exists():
        env["AMS_MEMORY_BASE"] = str(memory_base)
    return env


def _check_status(monitor: dict, name: str) -> str:
    return next(check["status"] for check in monitor["checks"] if check["name"] == name)


def _check_detail(monitor: dict, name: str) -> str:
    return next(check["detail"] for check in monitor["checks"] if check["name"] == name)


def _seed_runtime_records(root: Path) -> None:
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
        "--task-family",
        "ams-usage",
    )


def _seed_reconciled_memory_surfaces(root: Path) -> None:
    memory_base = _legacy_memory_base(root.parent)
    _codex_config(root.parent, root)
    _ams(root, "--json", "migrate", "apply", "--memory-base", str(memory_base))


def _seed_runtime_control_root(root: Path) -> None:
    _seed_runtime_records(root)
    _seed_reconciled_memory_surfaces(root)


def _legacy_memory_base(tmp_path: Path) -> Path:
    memory_base = tmp_path / "legacy-memory"
    memory_base.mkdir(exist_ok=True)
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


def _codex_config(tmp_path: Path, root: Path) -> Path:
    config_path = tmp_path / "config.toml"
    codex_db = tmp_path / "codex-memory" / "lancedb"
    config_path.write_text(
        "\n".join(
            [
                "[mcp_servers.ams-memory]",
                'command = "node"',
                "",
                "[mcp_servers.ams-memory.env]",
                f"AMS_ROOT = {json.dumps(str(root))}",
                "",
                "[mcp_servers.codex-memory]",
                'command = "node"',
                "",
                "[mcp_servers.codex-memory.env]",
                f"CODEX_MEMORY_DB_PATH = {json.dumps(str(codex_db))}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return config_path


def _codex_config_with_ams_root_arg(tmp_path: Path, root: Path) -> Path:
    config_path = tmp_path / "config.toml"
    codex_db = tmp_path / "codex-memory" / "lancedb"
    config_path.write_text(
        "\n".join(
            [
                "[mcp_servers.ams-memory]",
                'command = "python"',
                f"args = [{json.dumps(str(ROOT / 'scripts' / 'run_cem_mcp_stdio.py'))}, \"--root\", {json.dumps(str(root))}]",
                "",
                "[mcp_servers.codex-memory]",
                'command = "node"',
                "",
                "[mcp_servers.codex-memory.env]",
                f"CODEX_MEMORY_DB_PATH = {json.dumps(str(codex_db))}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return config_path


def _codex_config_with_ams_only_and_native_disabled(tmp_path: Path, root: Path) -> Path:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "\n".join(
            [
                "[features]",
                "memories = false",
                "",
                "[memories]",
                "generate_memories = false",
                "use_memories = false",
                "disable_on_external_context = true",
                "no_memories_if_mcp_or_web_search = true",
                "",
                "[mcp_servers.ams-memory]",
                'command = "python"',
                f"args = [{json.dumps(str(ROOT / 'scripts' / 'run_cem_mcp_stdio.py'))}, \"--root\", {json.dumps(str(root))}]",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return config_path


def _codex_config_with_ams_only(tmp_path: Path, root: Path) -> Path:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "\n".join(
            [
                "[mcp_servers.ams-memory]",
                'command = "python"',
                f"args = [{json.dumps(str(ROOT / 'scripts' / 'run_cem_mcp_stdio.py'))}, \"--root\", {json.dumps(str(root))}]",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return config_path
