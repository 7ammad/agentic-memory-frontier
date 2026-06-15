from __future__ import annotations

from .models import (
    AgentCapabilityContract,
    AgentMemoryContract,
    AgentOnboardingContract,
    AgentOnboardingReceipt,
    AgentOnboardingTrustPolicy,
)
from .storage import CEMStore

STALE_AGENT_IDS = frozenset({"superbrembo"})
AMS_CLI = 'python "C:\\Dev\\Builds\\Agentic Memory System\\scripts\\ams.py"'


def build_hammad_agent_roster() -> list[AgentOnboardingContract]:
    """Build the current owner-approved local agent roster.

    This is intentionally explicit. Roster drift is a memory failure mode: stale
    agent names must not quietly re-enter cross-agent onboarding.
    """

    return [
        _contract(
            agent_id="codex",
            display_name="Codex",
            runtime_surface="codex_desktop",
            operational_status="active",
            trust_level="owner",
            owner_scope="primary coding, refactors, verification, and Codex harness work",
            capabilities=[
                _capability(
                    name="deep_coding",
                    description="Implement, refactor, verify, repair, and hand off code changes through the Codex Execution Contract.",
                    risk_level="high",
                    permissions=["filesystem", "shell", "browser", "mcp"],
                    evidence_id="directive_codex_execution_contract",
                ),
                _capability(
                    name="harness_design",
                    description="Maintain Codex operating harness contracts, skills, hooks, receipts, and AMS memory discipline.",
                    risk_level="high",
                    permissions=["codex_home", "repo_docs", "shell"],
                    evidence_id="directive_codex_harness_design",
                ),
            ],
            evidence_ids=["owner_roster_codex", "directive_codex_execution_contract"],
        ),
        _contract(
            agent_id="hermes",
            display_name="Hermes",
            runtime_surface="hermes_desktop",
            operational_status="active",
            trust_level="trusted",
            owner_scope="desktop/runtime agent lane and local operator infrastructure",
            capabilities=[
                _capability(
                    name="desktop_runtime",
                    description="Operate the local Hermes Desktop runtime without poisoning AMS with ambient Python or stale runtime state.",
                    risk_level="high",
                    permissions=["desktop_runtime", "local_python", "filesystem"],
                    evidence_id="owner_roster_hermes",
                ),
                _capability(
                    name="agent_infrastructure",
                    description="Coordinate local agent infrastructure and runtime environment checks for Hammad's personal stack.",
                    risk_level="medium",
                    permissions=["runtime_config", "local_process"],
                    evidence_id="directive_hermes_env_doctor",
                ),
            ],
            evidence_ids=["owner_roster_hermes", "directive_hermes_env_doctor"],
        ),
        _contract(
            agent_id="hessa",
            display_name="Hessa",
            runtime_surface="hessa",
            operational_status="active",
            trust_level="trusted",
            owner_scope="Hammad's local fast full computer operator and personal voice/computer agent",
            capabilities=[
                _capability(
                    name="computer_operator",
                    description="Use browser, desktop, filesystem, and voice/tool orchestration when Hessa proper acceptance requires it.",
                    risk_level="critical",
                    permissions=["computer_use", "browser", "filesystem", "voice"],
                    evidence_id="directive_hessa_computer_operator",
                ),
                _capability(
                    name="personal_runtime",
                    description="Run Hammad's personal operator workflows with calculated risk and explicit client-production boundaries.",
                    risk_level="high",
                    permissions=["local_runtime", "tool_orchestration"],
                    evidence_id="directive_hessa_personal",
                ),
            ],
            evidence_ids=["owner_roster_hessa", "directive_hessa_computer_operator"],
        ),
        _contract(
            agent_id="claude-code-cursor",
            display_name="Claude Code",
            runtime_surface="claude_code_cursor",
            operational_status="active",
            trust_level="trusted",
            owner_scope="architecture, review, planning, and Claude Code workflow execution in Cursor IDE",
            capabilities=[
                _capability(
                    name="architecture_review",
                    description="Plan architecture, review designs, and challenge implementation decisions before broad code changes.",
                    risk_level="high",
                    permissions=["repo_read", "ide_context", "review"],
                    evidence_id="owner_roster_claude_code",
                ),
                _capability(
                    name="claude_code_execution",
                    description="Run Claude Code workflow slices and choose its own batching, subagent, and command strategy when delegated.",
                    risk_level="high",
                    permissions=["filesystem", "shell", "ide_context"],
                    evidence_id="directive_claude_code_execution",
                ),
            ],
            evidence_ids=["owner_roster_claude_code", "directive_claude_code_execution"],
        ),
        _contract(
            agent_id="cursor-agent",
            display_name="Cursor",
            runtime_surface="cursor_agent",
            operational_status="active",
            trust_level="trusted",
            owner_scope="rapid IDE-native edits and composer workflows when active",
            capabilities=[
                _capability(
                    name="rapid_edits",
                    description="Make fast IDE-native edits while preserving AMS memory lane and verification handoff contracts.",
                    risk_level="high",
                    permissions=["filesystem", "ide_context"],
                    evidence_id="owner_roster_cursor",
                ),
                _capability(
                    name="composer_workflow",
                    description="Use Cursor composer context for targeted code changes and local iteration.",
                    risk_level="medium",
                    permissions=["ide_context", "repo_edit"],
                    evidence_id="owner_roster_cursor",
                ),
            ],
            evidence_ids=["owner_roster_cursor"],
        ),
        _contract(
            agent_id="openclaw",
            display_name="OpenClaw",
            runtime_surface="openclaw",
            operational_status="parked",
            trust_level="team",
            owner_scope="parked coordination lane that still counts for AMS onboarding and A2A context",
            capabilities=[
                _capability(
                    name="coordination_hub",
                    description="Coordinate agent handoffs and A2A queue context when the OpenClaw workspace is active.",
                    risk_level="medium",
                    permissions=["a2a_queue", "handoff_log"],
                    evidence_id="owner_roster_openclaw",
                )
            ],
            evidence_ids=["owner_roster_openclaw"],
        ),
    ]


def onboard_agent(store: CEMStore, contract: AgentOnboardingContract) -> AgentOnboardingReceipt:
    receipt = evaluate_onboarding_contract(contract)
    if receipt.status != "rejected":
        store.save_agent_onboarding_contract(contract)
    store.save_agent_onboarding_receipt(receipt)
    return receipt


def evaluate_onboarding_contract(contract: AgentOnboardingContract) -> AgentOnboardingReceipt:
    missing_requirements = _missing_requirements(contract)
    agent_id = contract.agent_id.lower()
    stale_agent = agent_id in STALE_AGENT_IDS
    retired = contract.operational_status == "retired" or contract.trust_level == "retired"

    if stale_agent:
        status = "rejected"
        reason = "stale retired agent id cannot be onboarded: SuperBrembo is not an active AMS agent"
    elif retired:
        status = "rejected"
        reason = "retired agents cannot be promoted into the active AMS onboarding registry"
    elif missing_requirements:
        status = "needs_review"
        reason = "agent onboarding contract is incomplete and requires owner/operator review"
    else:
        status = "accepted"
        reason = "agent onboarding contract accepted with AMS primary memory lane and capability contracts"

    trust_policy = None
    if status != "rejected" and contract.shared_trace_enabled:
        trusted_agent_ids = []
        if contract.trust_level in {"owner", "trusted", "team"}:
            trusted_agent_ids = [contract.agent_id]
        trust_policy = AgentOnboardingTrustPolicy(
            trusted_agent_ids=trusted_agent_ids,
            require_sender_matches_trace_agent=True,
            default_visibility=contract.default_visibility,
            ownership=contract.ownership,
            allowed_shared_scopes=contract.memory_contract.allowed_scopes,
        )

    return AgentOnboardingReceipt(
        contract_id=contract.contract_id,
        agent_id=contract.agent_id,
        status=status,
        reason=reason,
        runtime_surface=contract.runtime_surface,
        operational_status=contract.operational_status,
        trust_policy=trust_policy,
        capability_ids=[capability.capability_id for capability in contract.capability_contracts],
        memory_lane_ready=not any(item.startswith("memory_contract.") for item in missing_requirements),
        missing_requirements=missing_requirements,
        runtime_checks=contract.runtime_checks,
        evidence_ids=[contract.contract_id, *contract.evidence_ids],
    )


def audit_onboarded_agent(store: CEMStore, agent_id: str) -> dict[str, object]:
    contract = _find_contract(store, agent_id)
    receipt = _latest_receipt(store, agent_id)
    return {
        "contract": contract.model_dump(mode="json"),
        "latest_receipt": receipt.model_dump(mode="json") if receipt is not None else None,
    }


def _contract(
    *,
    agent_id: str,
    display_name: str,
    runtime_surface: str,
    operational_status: str,
    trust_level: str,
    owner_scope: str,
    capabilities: list[AgentCapabilityContract],
    evidence_ids: list[str],
) -> AgentOnboardingContract:
    return AgentOnboardingContract(
        agent_id=agent_id,
        display_name=display_name,
        runtime_surface=runtime_surface,
        operational_status=operational_status,
        trust_level=trust_level,
        owner_scope=owner_scope,
        memory_contract=_memory_contract(agent_id),
        capability_contracts=capabilities,
        harness_contracts=[
            "codex-execution-contract",
            "codex-capability-router",
            "ams-startup-brief",
            "ams-action-brief",
            "ams-correction-capture",
            "delivery-verification-hardgate",
        ],
        runtime_checks=[
            f"{AMS_CLI} startup-brief \"{agent_id} onboarding smoke\" --domain coding --json",
            f"{AMS_CLI} brief \"{agent_id} onboarding smoke\" --domain coding",
        ],
        shared_trace_enabled=True,
        default_visibility="team",
        ownership="owner" if trust_level == "owner" else "source_agent",
        evidence_ids=evidence_ids,
    )


def _capability(
    *,
    name: str,
    description: str,
    risk_level: str,
    permissions: list[str],
    evidence_id: str,
) -> AgentCapabilityContract:
    return AgentCapabilityContract(
        name=name,
        description=description,
        input_contracts=[
            "task intent is explicit or inferred through the Codex Execution Contract",
            "AMS startup/action brief has been pulled before consequential work",
            "owner-only approvals remain explicit for destructive/external/client actions",
        ],
        output_contracts=[
            "produce verified action, receipt, or NOT DONE handoff",
            "write durable AMS lesson only when evidence-backed",
        ],
        permissions=permissions,
        risk_level=risk_level,
        verification_commands=[
            f"{AMS_CLI} startup-brief \"capability smoke\" --domain coding --json",
            f"{AMS_CLI} brief \"capability smoke\" --domain coding",
        ],
        status="declared",
        evidence_ids=[evidence_id],
    )


def _memory_contract(agent_id: str) -> AgentMemoryContract:
    return AgentMemoryContract(
        startup_brief_command=f"{AMS_CLI} startup-brief \"{{task}}\" --domain \"{{domain}}\" --json",
        action_brief_command=f"{AMS_CLI} brief \"{{task}}\" --domain \"{{domain}}\"",
        remember_command=(
            f"{AMS_CLI} remember \"{{verified_lesson}}\" --kind {{kind}} "
            f"--outcome {{outcome}} --domain \"{{domain}}\" --task-family \"{{task_family}}\" "
            f"--agent-id {agent_id}"
        ),
        correction_capture_command=(
            f"{AMS_CLI} correction capture \"{{correction}}\" --domain \"{{domain}}\" "
            f"--task-family \"{{task_family}}\" --source user"
        ),
        default_domain="coding",
        allowed_scopes=["global_agent_behavior", "agent", "project", "task", "multi_agent"],
        legacy_memory_policy="legacy markdown/native memories are evidence-only; AMS is the primary memory lane",
        automation_prompt_prefix=(
            f"First pull AMS startup and action briefs via {AMS_CLI}; "
            "AMS is the only default memory lane for automations. "
            "Do not read or write automation memory.md, legacy markdown memories, "
            "or native Codex memory files as runtime memory unless AMS points to an exact evidence or migration file."
        ),
    )


def _missing_requirements(contract: AgentOnboardingContract) -> list[str]:
    missing: list[str] = []
    commands = {
        "memory_contract.startup_brief_command": contract.memory_contract.startup_brief_command,
        "memory_contract.action_brief_command": contract.memory_contract.action_brief_command,
        "memory_contract.remember_command": contract.memory_contract.remember_command,
        "memory_contract.correction_capture_command": contract.memory_contract.correction_capture_command,
    }
    for field, command in commands.items():
        if not _uses_ams(command):
            missing.append(field)
    if not _automation_prompt_forbids_legacy_memory(contract.memory_contract.automation_prompt_prefix):
        missing.append("memory_contract.automation_prompt_prefix")
    if not contract.capability_contracts:
        missing.append("capability_contracts")
    if "codex-execution-contract" not in contract.harness_contracts:
        missing.append("harness_contracts.codex-execution-contract")
    if not contract.runtime_checks:
        missing.append("runtime_checks")
    return missing


def _uses_ams(command: str) -> bool:
    normalized = command.lower()
    return "ams.py" in normalized or "ams-memory" in normalized


def _automation_prompt_forbids_legacy_memory(prompt: str) -> bool:
    normalized = prompt.lower()
    mentions_ams = "ams" in normalized
    forbids_automation_memory = "automation memory.md" in normalized
    forbids_legacy = "legacy markdown" in normalized
    forbids_native = "native codex memory" in normalized
    disallows_runtime_memory = "default memory lane" in normalized or "runtime memory" in normalized
    return all(
        (
            mentions_ams,
            forbids_automation_memory,
            forbids_legacy,
            forbids_native,
            disallows_runtime_memory,
        )
    )


def _find_contract(store: CEMStore, agent_id: str) -> AgentOnboardingContract:
    for contract in store.list_agent_onboarding_contracts():
        if contract.agent_id == agent_id or contract.contract_id == agent_id:
            return contract
    raise KeyError(f"Agent onboarding contract not found: {agent_id}")


def _latest_receipt(store: CEMStore, agent_id: str) -> AgentOnboardingReceipt | None:
    receipts = [
        receipt
        for receipt in store.list_agent_onboarding_receipts()
        if receipt.agent_id == agent_id or receipt.contract_id == agent_id
    ]
    if not receipts:
        return None
    return receipts[-1]
