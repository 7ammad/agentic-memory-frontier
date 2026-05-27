from cem_core import AgentTrace, CEM, CEMMCPToolServer, InMemoryStore, TraceTurn
from cem_core.mcp_stdio import MCP_PROTOCOL_VERSION, handle_jsonrpc_message


def test_mcp_stdio_initialize_and_tool_list():
    server = CEMMCPToolServer(CEM(store=InMemoryStore()))

    initialize = handle_jsonrpc_message(
        server,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "0.1.0"},
            },
        },
    )
    tools = handle_jsonrpc_message(server, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})

    assert initialize is not None
    assert initialize["result"]["protocolVersion"] == MCP_PROTOCOL_VERSION
    assert initialize["result"]["capabilities"] == {"tools": {"listChanged": False}}
    assert tools is not None
    assert "cem_ingest_trace" in {tool["name"] for tool in tools["result"]["tools"]}
    assert "cem_import_shared_trace" in {tool["name"] for tool in tools["result"]["tools"]}


def test_mcp_stdio_tool_call_and_errors():
    server = CEMMCPToolServer(CEM(store=InMemoryStore()))
    trace = AgentTrace(
        session_id="mcp-session",
        agent_id="codex",
        turns=[TraceTurn(index=0, role="environment", content="SKILL: open approvals tab")],
    )

    result = handle_jsonrpc_message(
        server,
        {
            "jsonrpc": "2.0",
            "id": "call-1",
            "method": "tools/call",
            "params": {
                "name": "cem_ingest_trace",
                "arguments": {"trace": trace.model_dump(mode="json")},
            },
        },
    )
    unknown = handle_jsonrpc_message(
        server,
        {
            "jsonrpc": "2.0",
            "id": "call-2",
            "method": "tools/call",
            "params": {"name": "missing_tool", "arguments": {}},
        },
    )
    notification = handle_jsonrpc_message(
        server,
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
    )

    assert result is not None
    assert result["result"]["structuredContent"]["receipt"]["trace_id"] == trace.trace_id
    assert unknown is not None
    assert unknown["error"]["code"] == -32602
    assert "Unknown CEM MCP tool" in unknown["error"]["message"]
    assert notification is None
