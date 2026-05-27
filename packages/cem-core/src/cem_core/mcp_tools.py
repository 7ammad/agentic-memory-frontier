from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from .kernel import CEM
from .models import AgentTrace, TaskContext


class MCPToolDefinition(BaseModel):
    name: str
    description: str
    inputSchema: dict[str, Any] = Field(default_factory=dict)


class CEMMCPToolServer:
    """Transport-neutral MCP tool adapter for the CEM-0 kernel."""

    def __init__(self, cem: CEM) -> None:
        self.cem = cem

    def list_tools(self) -> list[dict[str, Any]]:
        return [tool.model_dump(mode="json") for tool in _tool_definitions()]

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        arguments = arguments or {}
        if name == "cem_ingest_trace":
            trace = AgentTrace.model_validate(arguments["trace"])
            payload = {"receipt": self.cem.ingest_trace(trace).model_dump(mode="json")}
            return _tool_result(payload)
        if name == "cem_propose_memories":
            atoms = self.cem.propose_memories(
                str(arguments["trace_id"]),
                strategy=str(arguments.get("strategy", "all")),
            )
            payload = {"atoms": [atom.model_dump(mode="json") for atom in atoms]}
            return _tool_result(payload)
        if name == "cem_validate_memory":
            decision = self.cem.validate(str(arguments["atom_id"]))
            payload = {"decision": decision.model_dump(mode="json")}
            return _tool_result(payload)
        if name == "cem_promote_memory":
            card = self.cem.promote(str(arguments["atom_id"]))
            payload = {"card": card.model_dump(mode="json") if card is not None else None}
            return _tool_result(payload)
        if name == "cem_retrieve_action_brief":
            task = TaskContext.model_validate(arguments["task"])
            brief = self.cem.retrieve_action_brief(
                task,
                max_cards=int(arguments.get("max_cards", 5)),
            )
            payload = {"action_brief": brief.model_dump(mode="json")}
            return _tool_result(payload)
        if name == "cem_audit_memory":
            audit = self.cem.audit(str(arguments["memory_id"]))
            payload = {"audit": audit.model_dump(mode="json")}
            return _tool_result(payload)
        if name == "cem_confirm_memory":
            self.cem.confirm(str(arguments["memory_id"]))
            return _tool_result({"confirmed": True, "memory_id": str(arguments["memory_id"])})
        if name == "cem_reject_memory":
            self.cem.reject(str(arguments["memory_id"]), str(arguments["reason"]))
            return _tool_result({"rejected": True, "memory_id": str(arguments["memory_id"])})
        raise KeyError(f"Unknown CEM MCP tool: {name}")


def _tool_definitions() -> list[MCPToolDefinition]:
    return [
        MCPToolDefinition(
            name="cem_ingest_trace",
            description="Ingest an AgentTrace into the raw CEM-0 evidence ledger.",
            inputSchema={
                "type": "object",
                "properties": {"trace": AgentTrace.model_json_schema()},
                "required": ["trace"],
                "additionalProperties": False,
            },
        ),
        MCPToolDefinition(
            name="cem_propose_memories",
            description="Extract candidate Experience Atoms from an ingested trace.",
            inputSchema={
                "type": "object",
                "properties": {
                    "trace_id": {"type": "string"},
                    "strategy": {"type": "string", "default": "all"},
                },
                "required": ["trace_id"],
                "additionalProperties": False,
            },
        ),
        MCPToolDefinition(
            name="cem_validate_memory",
            description="Run write-path validation for a proposed Experience Atom.",
            inputSchema={
                "type": "object",
                "properties": {"atom_id": {"type": "string"}},
                "required": ["atom_id"],
                "additionalProperties": False,
            },
        ),
        MCPToolDefinition(
            name="cem_promote_memory",
            description="Promote a candidate Experience Atom into an Experience Card when validation permits it.",
            inputSchema={
                "type": "object",
                "properties": {"atom_id": {"type": "string"}},
                "required": ["atom_id"],
                "additionalProperties": False,
            },
        ),
        MCPToolDefinition(
            name="cem_retrieve_action_brief",
            description="Retrieve an Action Brief for a task context.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task": TaskContext.model_json_schema(),
                    "max_cards": {"type": "integer", "default": 5, "minimum": 1},
                },
                "required": ["task"],
                "additionalProperties": False,
            },
        ),
        MCPToolDefinition(
            name="cem_audit_memory",
            description="Return provenance, validation, confidence, and status for an atom or card.",
            inputSchema={
                "type": "object",
                "properties": {"memory_id": {"type": "string"}},
                "required": ["memory_id"],
                "additionalProperties": False,
            },
        ),
        MCPToolDefinition(
            name="cem_confirm_memory",
            description="Manually confirm a memory candidate and clear its quarantine reason.",
            inputSchema={
                "type": "object",
                "properties": {"memory_id": {"type": "string"}},
                "required": ["memory_id"],
                "additionalProperties": False,
            },
        ),
        MCPToolDefinition(
            name="cem_reject_memory",
            description="Manually reject a memory candidate with a reason.",
            inputSchema={
                "type": "object",
                "properties": {
                    "memory_id": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["memory_id", "reason"],
                "additionalProperties": False,
            },
        ),
    ]


def _tool_result(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(payload, ensure_ascii=False, sort_keys=True),
            }
        ],
        "structuredContent": payload,
        "isError": False,
    }
