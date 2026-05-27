# CEM-0 Multi-Agent Protocol

Date: 2026-05-27

Status: V0 shared-experience envelope

## Scope

This is the smallest CEM-0 multi-agent protocol that protects the write path.

It does not implement ACS, agent messaging, relay routing, SSE, signatures, or cross-agent tool brokerage. Those remain later infrastructure. This slice only answers:

> If another agent sends experience, how does CEM-0 ingest it without laundering it into trusted memory?

## Primitive

`SharedTraceEnvelope` wraps an `AgentTrace` with:

- `sender_agent_id`
- `recipient_agent_id`
- `payload_kind`
- `protocol_version`
- `body_hash`
- `created_at`

The `body_hash` is a SHA-256 hash over the canonical JSON trace payload. CEM rejects envelopes whose hash does not match the trace.

## Trust Policy

`MultiAgentTrustPolicy` controls whether a sender is trusted for automatic memory promotion.

Default behavior is conservative:

- no sender is trusted by default;
- untrusted shared traces are imported with an `untrusted-` agent prefix;
- the existing validator then quarantines extracted atoms with `untrusted_source`;
- if `require_sender_matches_trace_agent` is true, a sender cannot claim trust for a trace authored by another agent id.

Trusted sender import:

```python
from cem_core import CEM, MultiAgentTrustPolicy, import_shared_trace

receipt = import_shared_trace(
    cem,
    envelope,
    trust_policy=MultiAgentTrustPolicy(trusted_agent_ids=["agent-alpha"]),
)
```

Untrusted sender import still preserves the trace as evidence, but candidate memories do not become trusted experience without validation or manual confirmation.

## CLI

```powershell
python scripts/run_cem_import_shared_trace.py envelope.json --root tmp\cem-shared --trusted-agent-id agent-alpha
```

## MCP Tool

The MCP bridge exposes the same import path as:

- `cem_import_shared_trace`

## Verification

Covered by:

- `tests/test_multi_agent.py`
- `tests/test_mcp_tools.py`
- `tests/test_mcp_stdio.py`

The tests verify trusted import, untrusted-source quarantine, tamper rejection, sender/trace mismatch handling, and MCP tool exposure.

