# CEM-0 MCP Integration

Date: 2026-05-27

Status: V0 stdio tool bridge

## Scope

This slice exposes the CEM-0 kernel through a small MCP-compatible stdio JSON-RPC bridge.

It is deliberately narrow:

- no hosted HTTP service;
- no Codex memory twin;
- no ACS or multi-agent relay;
- no external database dependency.

The bridge exists so an agent can call CEM-0's write path and action-brief surface as tools while the kernel remains the center of the project.

## Command

```powershell
python scripts/run_cem_mcp_stdio.py --root tmp\cem-mcp
```

The server persists through the default SQLite + JSONL backend at the supplied root.

## Protocol Surface

The stdio bridge handles:

- `initialize`
- `ping`
- `tools/list`
- `tools/call`
- notifications, including `notifications/initialized`, as no-response messages

It returns tool results with both text content and `structuredContent`.

## Tools

- `cem_ingest_trace`
- `cem_propose_memories`
- `cem_validate_memory`
- `cem_promote_memory`
- `cem_retrieve_action_brief`
- `cem_audit_memory`
- `cem_confirm_memory`
- `cem_reject_memory`
- `cem_import_shared_trace`

These tools map directly to the existing CEM-0 kernel API. They do not bypass validation or promote raw memory as trusted experience.

## Verification

Covered by:

- `tests/test_mcp_tools.py`
- `tests/test_mcp_stdio.py`

The tests verify tool discovery, write-path tool calls, Action Brief retrieval, audit output, manual confirm/reject, JSON-RPC initialization, `tools/list`, `tools/call`, errors, and notification handling.
