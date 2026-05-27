from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Literal

from pydantic import Field

from .kernel import CEM
from .models import AgentTrace, StrictModel, TraceReceipt, new_id, utc_now

PROTOCOL_VERSION = "cem-shared-experience-v0"


class SharedTraceEnvelope(StrictModel):
    envelope_id: str = Field(default_factory=lambda: new_id("shared_trace"))
    protocol_version: str = PROTOCOL_VERSION
    sender_agent_id: str
    recipient_agent_id: str
    payload_kind: Literal["agent_trace"] = "agent_trace"
    trace: AgentTrace
    body_hash: str
    created_at: datetime = Field(default_factory=utc_now)


class MultiAgentTrustPolicy(StrictModel):
    trusted_agent_ids: list[str] = Field(default_factory=list)
    require_sender_matches_trace_agent: bool = True
    untrusted_agent_prefix: str = "untrusted"


class SharedTraceImportReceipt(StrictModel):
    envelope_id: str
    trace_receipt: TraceReceipt
    trusted_sender: bool
    imported_agent_id: str
    reason: str


def build_shared_trace_envelope(
    trace: AgentTrace,
    *,
    sender_agent_id: str,
    recipient_agent_id: str,
) -> SharedTraceEnvelope:
    return SharedTraceEnvelope(
        sender_agent_id=sender_agent_id,
        recipient_agent_id=recipient_agent_id,
        trace=trace,
        body_hash=trace_body_hash(trace),
    )


def import_shared_trace(
    cem: CEM,
    envelope: SharedTraceEnvelope,
    *,
    trust_policy: MultiAgentTrustPolicy | None = None,
) -> SharedTraceImportReceipt:
    verify_shared_trace_envelope(envelope)
    policy = trust_policy or MultiAgentTrustPolicy()
    trusted_sender = _trusted_sender(envelope, policy)
    trace = envelope.trace
    reason = "trusted sender"
    if not trusted_sender:
        trace = trace.model_copy(update={"agent_id": _untrusted_agent_id(envelope.sender_agent_id, policy)})
        reason = "sender not trusted for automatic memory promotion"
    receipt = cem.ingest_trace(trace)
    return SharedTraceImportReceipt(
        envelope_id=envelope.envelope_id,
        trace_receipt=receipt,
        trusted_sender=trusted_sender,
        imported_agent_id=trace.agent_id,
        reason=reason,
    )


def verify_shared_trace_envelope(envelope: SharedTraceEnvelope) -> None:
    expected = trace_body_hash(envelope.trace)
    if envelope.body_hash != expected:
        raise ValueError("Shared trace envelope body_hash does not match trace payload.")


def trace_body_hash(trace: AgentTrace) -> str:
    payload = json.dumps(trace.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _trusted_sender(envelope: SharedTraceEnvelope, policy: MultiAgentTrustPolicy) -> bool:
    if envelope.sender_agent_id not in set(policy.trusted_agent_ids):
        return False
    if policy.require_sender_matches_trace_agent and envelope.trace.agent_id != envelope.sender_agent_id:
        return False
    return True


def _untrusted_agent_id(sender_agent_id: str, policy: MultiAgentTrustPolicy) -> str:
    if sender_agent_id.startswith(f"{policy.untrusted_agent_prefix}-"):
        return sender_agent_id
    return f"{policy.untrusted_agent_prefix}-{sender_agent_id}"
