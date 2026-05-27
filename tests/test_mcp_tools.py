from cem_core import AgentTrace, CEM, CEMMCPToolServer, InMemoryStore, TraceTurn
from cem_core import build_shared_trace_envelope


def test_cem_mcp_tool_server_exposes_write_path_and_action_brief():
    server = CEMMCPToolServer(CEM(store=InMemoryStore()))
    tool_names = {tool["name"] for tool in server.list_tools()}
    trace = AgentTrace(
        session_id="mcp-session",
        agent_id="codex",
        task_id="approval-flow",
        turns=[TraceTurn(index=0, role="environment", content="SKILL: open approvals tab")],
        final_outcome="success",
        environment={"domain": "workflow-nav"},
    )

    assert {
        "cem_ingest_trace",
        "cem_propose_memories",
        "cem_validate_memory",
        "cem_promote_memory",
        "cem_retrieve_action_brief",
        "cem_audit_memory",
        "cem_confirm_memory",
        "cem_reject_memory",
        "cem_import_shared_trace",
    } == tool_names

    receipt_result = server.call_tool("cem_ingest_trace", {"trace": trace.model_dump(mode="json")})
    atoms_result = server.call_tool("cem_propose_memories", {"trace_id": trace.trace_id})
    atom_id = atoms_result["structuredContent"]["atoms"][0]["atom_id"]
    decision_result = server.call_tool("cem_validate_memory", {"atom_id": atom_id})
    card_result = server.call_tool("cem_promote_memory", {"atom_id": atom_id})
    card_id = card_result["structuredContent"]["card"]["card_id"]
    brief_result = server.call_tool(
        "cem_retrieve_action_brief",
        {
            "task": {
                "task_id": "held-out",
                "session_id": "mcp-session",
                "description": "Which action should open approvals tab?",
                "domain_scope": "workflow-nav",
                "task_family": "approval-flow",
            }
        },
    )
    audit_result = server.call_tool("cem_audit_memory", {"memory_id": card_id})

    assert receipt_result["structuredContent"]["receipt"]["turn_count"] == 1
    assert decision_result["structuredContent"]["decision"]["decision"] == "candidate"
    assert card_result["structuredContent"]["card"]["do"] == ["open approvals tab"]
    assert brief_result["structuredContent"]["action_brief"]["recommended_next_actions"] == ["open approvals tab"]
    assert audit_result["structuredContent"]["audit"]["memory_id"] == card_id
    assert receipt_result["isError"] is False


def test_cem_mcp_tool_server_can_reject_and_confirm_memory():
    server = CEMMCPToolServer(CEM(store=InMemoryStore()))
    trace = AgentTrace(
        session_id="mcp-session",
        agent_id="codex",
        turns=[TraceTurn(index=0, role="user", content="PREFERENCE: database=postgres")],
    )

    server.call_tool("cem_ingest_trace", {"trace": trace.model_dump(mode="json")})
    atoms_result = server.call_tool("cem_propose_memories", {"trace_id": trace.trace_id})
    atom_id = atoms_result["structuredContent"]["atoms"][0]["atom_id"]
    reject_result = server.call_tool("cem_reject_memory", {"memory_id": atom_id, "reason": "manual test"})
    rejected_audit = server.call_tool("cem_audit_memory", {"memory_id": atom_id})["structuredContent"]["audit"]
    confirm_result = server.call_tool("cem_confirm_memory", {"memory_id": atom_id})
    confirmed_audit = server.call_tool("cem_audit_memory", {"memory_id": atom_id})["structuredContent"]["audit"]

    assert reject_result["structuredContent"] == {"rejected": True, "memory_id": atom_id}
    assert rejected_audit["promotion_status"] == "quarantined"
    assert rejected_audit["quarantine_reason"] == "manual test"
    assert confirm_result["structuredContent"] == {"confirmed": True, "memory_id": atom_id}
    assert confirmed_audit["promotion_status"] == "candidate"
    assert confirmed_audit["quarantine_reason"] is None


def test_cem_mcp_tool_server_imports_shared_trace_with_trust_policy():
    server = CEMMCPToolServer(CEM(store=InMemoryStore()))
    trace = AgentTrace(
        session_id="shared-session",
        agent_id="agent-alpha",
        turns=[TraceTurn(index=0, role="environment", content="SKILL: open approvals tab")],
        final_outcome="success",
        environment={"domain": "workflow-nav"},
    )
    envelope = build_shared_trace_envelope(
        trace,
        sender_agent_id="agent-alpha",
        recipient_agent_id="codex",
    )

    result = server.call_tool(
        "cem_import_shared_trace",
        {
            "envelope": envelope.model_dump(mode="json"),
            "trust_policy": {"trusted_agent_ids": ["agent-alpha"]},
        },
    )

    assert result["structuredContent"]["receipt"]["trusted_sender"] is True
    assert result["structuredContent"]["receipt"]["imported_agent_id"] == "agent-alpha"
