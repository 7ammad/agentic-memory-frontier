import json
import subprocess
import sys
from pathlib import Path

from cem_core import CEM, CEMMCPToolServer, InMemoryStore
from cem_core.agent_onboarding import build_hammad_agent_roster
from cem_core.models import AgentOnboardingContract


ROOT = Path(__file__).resolve().parents[1]


def test_default_hammad_roster_is_current_and_contract_backed():
    roster = build_hammad_agent_roster()
    by_id = {contract.agent_id: contract for contract in roster}

    assert {
        "codex",
        "hermes",
        "hessa",
        "claude-code-cursor",
        "cursor-agent",
        "openclaw",
    } <= set(by_id)
    assert "superbrembo" not in by_id
    assert by_id["claude-code-cursor"].display_name == "Claude Code"
    assert by_id["claude-code-cursor"].runtime_surface == "claude_code_cursor"
    assert by_id["cursor-agent"].display_name == "Cursor"
    assert by_id["cursor-agent"].runtime_surface == "cursor_agent"
    assert by_id["openclaw"].operational_status == "parked"

    for contract in roster:
        assert contract.capability_contracts
        assert contract.memory_contract.startup_brief_command
        assert contract.memory_contract.action_brief_command
        assert contract.memory_contract.remember_command
        assert contract.memory_contract.correction_capture_command
        assert "automation memory.md" in contract.memory_contract.automation_prompt_prefix.lower()
        assert "only default memory lane" in contract.memory_contract.automation_prompt_prefix.lower()
        assert "codex-execution-contract" in contract.harness_contracts


def test_cem_onboards_agent_contract_and_builds_trust_receipt():
    cem = CEM(store=InMemoryStore())
    hermes = next(contract for contract in build_hammad_agent_roster() if contract.agent_id == "hermes")

    receipt = cem.onboard_agent(hermes)

    assert receipt.status == "accepted"
    assert receipt.agent_id == "hermes"
    assert receipt.trust_policy is not None
    assert receipt.trust_policy.trusted_agent_ids == ["hermes"]
    assert receipt.runtime_surface == "hermes_desktop"
    assert cem.store.get_agent_onboarding_contract(hermes.contract_id) == hermes
    assert cem.store.list_agent_onboarding_receipts() == [receipt]


def test_stale_superbrembo_onboarding_is_rejected_without_contract_promotion():
    cem = CEM(store=InMemoryStore())
    codex = next(contract for contract in build_hammad_agent_roster() if contract.agent_id == "codex")
    stale_contract = codex.model_copy(
        update={
            "agent_id": "superbrembo",
            "display_name": "SuperBrembo",
            "runtime_surface": "custom",
            "operational_status": "retired",
        }
    )

    receipt = cem.onboard_agent(stale_contract)

    assert receipt.status == "rejected"
    assert receipt.agent_id == "superbrembo"
    assert "stale" in receipt.reason.lower()
    assert cem.store.list_agent_onboarding_contracts() == []
    assert cem.store.list_agent_onboarding_receipts() == [receipt]


def test_agent_onboarding_contract_requires_real_memory_lane():
    codex = next(contract for contract in build_hammad_agent_roster() if contract.agent_id == "codex")

    bad_payload = codex.model_dump(mode="json")
    bad_payload["memory_contract"]["startup_brief_command"] = ""

    try:
        AgentOnboardingContract.model_validate(bad_payload)
    except ValueError as exc:
        assert "startup_brief_command" in str(exc)
    else:
        raise AssertionError("contract without startup brief command must fail validation")


def test_agent_onboarding_contract_requires_automation_prompt_to_forbid_memory_md():
    codex = next(contract for contract in build_hammad_agent_roster() if contract.agent_id == "codex")
    bad_contract = codex.model_copy(
        update={
            "memory_contract": codex.memory_contract.model_copy(
                update={
                    "automation_prompt_prefix": (
                        'First pull AMS startup and action briefs via '
                        'python "C:\\Dev\\Builds\\Agentic Memory System\\scripts\\ams.py"; '
                        "do not use legacy memory as primary context."
                    )
                }
            )
        }
    )

    receipt = CEM(store=InMemoryStore()).onboard_agent(bad_contract)

    assert receipt.status == "needs_review"
    assert receipt.memory_lane_ready is False
    assert "memory_contract.automation_prompt_prefix" in receipt.missing_requirements


def test_cli_seeds_and_lists_current_roster(tmp_path):
    root = tmp_path / "ams-root"

    seed = _ams(root, "--json", "agent", "seed-roster")
    listed = _ams(root, "--json", "agent", "list")
    audit = _ams(root, "--json", "agent", "audit", "hessa")

    assert seed["accepted_count"] == 6
    assert seed["rejected_count"] == 0
    assert {
        "codex",
        "hermes",
        "hessa",
        "claude-code-cursor",
        "cursor-agent",
        "openclaw",
    } <= set(seed["agent_ids"])
    assert "superbrembo" not in seed["agent_ids"]
    assert {agent["agent_id"] for agent in listed["agents"]} == set(seed["agent_ids"])
    assert audit["contract"]["agent_id"] == "hessa"
    assert audit["latest_receipt"]["status"] == "accepted"


def test_mcp_exposes_agent_onboarding_tools():
    server = CEMMCPToolServer(CEM(store=InMemoryStore()))
    tool_names = {tool["name"] for tool in server.list_tools()}
    codex = next(contract for contract in build_hammad_agent_roster() if contract.agent_id == "codex")

    result = server.call_tool("cem_onboard_agent", {"contract": codex.model_dump(mode="json")})
    listed = server.call_tool("cem_list_onboarded_agents")

    assert "cem_onboard_agent" in tool_names
    assert "cem_list_onboarded_agents" in tool_names
    assert result["structuredContent"]["receipt"]["status"] == "accepted"
    assert listed["structuredContent"]["agents"][0]["agent_id"] == "codex"


def _ams(root: Path, *args: str) -> dict:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "ams.py"), "--root", str(root), *args],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(result.stdout)
