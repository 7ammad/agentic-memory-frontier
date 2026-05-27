# Codex Counsel - Sub-Project D (ACS Protocol Design)

_Source: codex exec 0.128.0, model_reasoning_effort=medium, read-only_
_Event counts: {'thread.started': 1, 'turn.started': 1, 'item.completed': 32, 'item.started': 28, 'turn.completed': 1}_
_Agent message lengths: [237, 194, 225, 22385]_

---

**Executive Verdict**

Build ACS as a small, explicit A2A v1.0 service, not as “messages hidden inside memory search.” Phase 1 should implement public Agent Cards, JSON-RPC `SendMessage`, optional SSE `SendStreamingMessage`/subscription for push delivery, signed ACS envelopes, an append-only ACS event log, and MCP calls only for durable memory side effects.

The strongest call: choose explicit `protocol_mode` on every message and sign every canonical message body. Do not infer reward mode from message type, and do not rely on TOFU alone for identity. The existing SC HTTP/SSE transport is reusable, but the current `/notify` path is too primitive: it queues in memory, drops identity on save, hardcodes shared visibility, and has no durable delivery semantics [code: notify-handler.ts:118-143].

Q6 recommendation is option **(a)** with one adjustment: a dedicated ACS service plus explicit MCP write-through for durable artifacts. Option (c) is rejected because communication-through-shared-memory is exactly the “GENERAL communication” pattern the locked constraints say to avoid; C’s own bridge spec says shared-row communication maps to general communication, not free communication [spec: 2026-05-26-codex-memory-system-design.md §5.3].

Sources read: A2A latest spec and GitHub mirror [doc: https://a2a-protocol.org/latest/specification/] [doc: https://github.com/a2aproject/A2A/blob/main/docs/specification.md], MCP overview/spec [doc: https://modelcontextprotocol.io/specification/2025-03-26/basic/index] [doc: https://modelcontextprotocol.io/docs/getting-started/intro].

**1. Q1 — A2A v1.0 Wire Format**

**Recommendation.** ACS Phase 1 should expose `GET /.well-known/agent-card.json`, `POST /rpc` for JSON-RPC 2.0, and `POST /rpc` returning SSE only for streaming methods. The canonical Agent Card location in A2A v1.0 is `https://{server_domain}/.well-known/agent-card.json`; the spec registers `agent-card.json` as the well-known URI and says it returns an `AgentCard` describing capabilities, supported protocols, authentication requirements, and available skills [doc: https://a2a-protocol.org/latest/specification/ §8.2, §14.3]. The Agent Card contains `name`, `description`, ordered `supportedInterfaces`, `version`, `capabilities`, `securitySchemes`, `securityRequirements`, input/output modes, `skills`, and optional signatures [doc: https://a2a-protocol.org/latest/specification/ §4.4.1]. A2A v1.0 supports JSON-RPC 2.0 over HTTP(S), with SSE for streaming, and also has REST and gRPC bindings; JSON-RPC has `SendMessage`, `SendStreamingMessage`, `GetTask`, `ListTasks`, `CancelTask`, `SubscribeToTask`, push notification config methods, and `GetExtendedAgentCard` [doc: https://a2a-protocol.org/latest/specification/ §9.1-§9.4]. The existing SC server already uses `StreamableHTTPServerTransport`, tracks session transports, and routes `/mcp` over HTTP, which is the closest local implementation pattern [code: http-server.ts:18-19] [code: http-server.ts:365-405].

**Phase 1 subset.** Implement: Agent Card, JSON-RPC `SendMessage`, `SendStreamingMessage` for direct SSE push, `GetTask` for conversation/task state, minimal `ListTasks` by `contextId`, bearer/auth header support, `A2A-Version`, and signed custom ACS envelope inside the A2A message metadata. Defer: file exchange, push-notification webhook config, gRPC, REST binding, extended Agent Card, registry discovery, multi-tenant routing, and nonlocal HTTPS deployment. Include these Agent Card fields for ACS: `agent_id`, ed25519 public key or JWKS URL as an ACS extension, supported ACS message types, supported protocol modes, endpoint URL, `streaming: true`, `pushNotifications: false` in Phase 1 unless webhooks are actually implemented, `securitySchemes` for bearer plus ACS signature verification, and skills for `second_opinion`, `review`, `handoff`, `clarification`, `decision_log`.

**Rationale.** This gives ACS a true free communication channel: explicit HTTP/SSE messages, not action-coded memory writes. It also aligns with the locked D constraint that A2A is the outer protocol and MCP is the inner tool-access protocol [spec: 2026-05-26-session-handoff.md §ACS constraints]. The A2A spec’s async model returns `Task` or `Message` immediately and lets clients track updates through polling, streaming, or push notifications [doc: https://a2a-protocol.org/latest/specification/ §3.3.3], which maps cleanly to long-running second opinions and handoffs.

**Rejected alternatives.** Do not expose only MCP `/mcp` as ACS. MCP is the right inner tool layer because MCP standardizes access to tools/resources and all messages follow JSON-RPC 2.0 [doc: https://modelcontextprotocol.io/specification/2025-03-26/basic/index], but A2A is the agent-to-agent contract. Do not implement only `/notify`: the current SC notify handler receives `agent_id` but does not persist it into `store.save`, hardcodes `visibility: "shared"`, and stores only an in-memory FIFO queue [code: notify-handler.ts:25] [code: notify-handler.ts:118-143]. That is useful prior art, not an ACS protocol.

**2. Q2 — Five Message Schemas**

Use one canonical ACS envelope for all five message types. It rides inside A2A `Message.parts[].metadata.acs` or JSON-RPC `params.acs_message`.

```json
{
  "acs_version": "0.1.0",
  "message_id": "uuid-v7",
  "conversation_id": "uuid-v7",
  "causality": { "parent_message_id": "uuid-v7|null", "seq": 1 },
  "sender_agent_id": "sha256-ed25519-pubkey-hex",
  "recipient_agent_id": "sha256-ed25519-pubkey-hex",
  "message_type": "second_opinion.request",
  "protocol_mode": "second_opinion",
  "reward_contract": "common_reward_user_welfare_preserve_attribution",
  "timestamp": "2026-05-26T12:00:00.000Z",
  "ttl_ms": 86400000,
  "nonce": "128-bit-base64url",
  "requires_ack": true,
  "payload": {},
  "sig": {
    "alg": "Ed25519",
    "key_id": "sha256-ed25519-pubkey-hex",
    "value": "base64url(signature-over-canonical-envelope-without-sig)"
  }
}
```

**`second_opinion.request` → `second_opinion.response`**

```json
{
  "message_type": "second_opinion.request",
  "protocol_mode": "second_opinion",
  "reward_contract": "common_reward_user_welfare_preserve_attribution",
  "payload": {
    "question": "string",
    "context": [{ "kind": "text|file_ref|memory_ref", "value": "string" }],
    "caller_position": "string|null",
    "requested_depth": "fast|strong|deep",
    "risk": 0.0,
    "deadline_ms": 300000,
    "attribution_required": true
  }
}
```

Response is synchronous if answer fits the request window; otherwise return an A2A `Task` and stream `statusUpdate` until final.

```json
{
  "message_type": "second_opinion.response",
  "payload": {
    "answer": "string",
    "confidence": 0.0,
    "agreements": ["string"],
    "disagreements": ["string"],
    "missing_evidence": ["string"],
    "recommended_action": "accept|revise|escalate",
    "attribution": { "agent_id": "hex", "agent_alias": "codex|claude" }
  }
}
```

**`review.findings`**

One-way plus ack. Findings are a durable artifact, so recipient must acknowledge receipt, not necessarily agreement.

```json
{
  "message_type": "review.findings",
  "protocol_mode": "red_team",
  "reward_contract": "zero_sum_findings_common_sum_user_welfare",
  "payload": {
    "review_target": { "kind": "diff|file|spec|runtime", "ref": "string" },
    "findings": [
      {
        "severity": "critical|high|medium|low",
        "claim": "string",
        "evidence": [{ "kind": "code|doc|spec|runtime", "ref": "string" }],
        "suggested_fix": "string|null"
      }
    ],
    "overall_verdict": "pass|patch_first|block"
  }
}
```

Ack:

```json
{
  "message_type": "ack",
  "payload": {
    "acked_message_id": "uuid-v7",
    "accepted_for_processing": true,
    "durable_ref": "acs:event_id"
  }
}
```

**`handoff.state`**

Asynchronous, requires ack with continuation token.

```json
{
  "message_type": "handoff.state",
  "protocol_mode": "handoff",
  "reward_contract": "sequential_common_reward_state_transfer",
  "payload": {
    "goal": "string",
    "state_summary": "string",
    "decisions": ["string"],
    "files_changed": ["path-or-ref"],
    "verification": [{ "command": "string", "result": "pass|fail|not_run" }],
    "remaining_steps": ["string"],
    "risks": ["string"],
    "start_by": "string",
    "memory_refs": ["mem_id"],
    "continuation_constraints": ["string"]
  }
}
```

Ack:

```json
{
  "message_type": "handoff.accepted",
  "payload": {
    "acked_message_id": "uuid-v7",
    "continuation_token": "uuid-v7",
    "accepted_scope": ["string"],
    "rejected_scope": ["string"],
    "clarifications_needed": ["string"]
  }
}
```

**`clarification.request` → `clarification.response`**

Usually synchronous; may be async if recipient needs tool calls.

```json
{
  "message_type": "clarification.request",
  "protocol_mode": "second_opinion",
  "reward_contract": "common_reward_user_welfare_preserve_attribution",
  "payload": {
    "question": "string",
    "choices": [{ "id": "string", "label": "string" }],
    "freeform_allowed": true,
    "blocking": true,
    "needed_by_message_id": "uuid-v7"
  }
}
```

Response:

```json
{
  "message_type": "clarification.response",
  "payload": {
    "answer": "string",
    "selected_choice_ids": ["string"],
    "confidence": 0.0,
    "unblocks_message_id": "uuid-v7"
  }
}
```

**`decision.recorded`**

One-way, durable, expects ack only for delivery. This can be written to memory after ACS delivery.

```json
{
  "message_type": "decision.recorded",
  "protocol_mode": "handoff",
  "reward_contract": "sequential_common_reward_state_transfer",
  "payload": {
    "decision": "string",
    "rationale": "string",
    "owner": "human|codex|claude",
    "scope": "global|project:<name>",
    "supersedes": ["decision_id"],
    "evidence_refs": ["string"],
    "memory_write": {
      "enabled": true,
      "type": "decision",
      "visibility": "shared"
    }
  }
}
```

**Rationale.** A shared envelope makes verification, replay protection, routing, persistence, and A2A task mapping uniform. It also keeps the five-message vocabulary small without making every message invent its own auth, causality, and ack semantics. The SC row shape today has memory fields but not ACS envelope fields [code: schema.ts:84-123], so keeping the communication envelope separate avoids overloading memory schema.

**Rejected alternatives.** Do not encode these as plain text messages with natural-language conventions. That would make reward mode, signature scope, and ack semantics ambiguous. Do not use JSON-RPC notification semantics for everything: MCP notifications are one-way and require no response [doc: https://modelcontextprotocol.io/specification/2025-03-26/basic/index], but ACS needs durable ack for `review.findings`, `handoff.state`, and `decision.recorded`.

**3. Q3 — Reward Structure Operationalization**

**Recommendation.** Use option **(a)**: an explicit `protocol_mode` and `reward_contract` in every message. Valid `protocol_mode`: `"second_opinion" | "red_team" | "handoff" | "clarification" | "decision_log"`. Conversation initialization may set a default, but every message must repeat it and recipients must reject mismatches unless the message type is an allowed transition.

**Rationale.** MARL dimensions must be explicit: Size = two agents plus human center by default; Knowledge = each agent has private memory and limited model state; Observability = partial, because agents cannot directly inspect each other’s reasoning; Rewards = mode-specific; Objective = user welfare with attribution, findings competition, or state-transfer continuity; Centralization/Communication = decentralized agents with sparse, explicit free communication. The handoff says ACS is decentralized, uses A2A outer/MCP inner, and has Jeffreys/risk escalation [spec: 2026-05-26-session-handoff.md §ACS constraints]. Given partial observability, a reward contract hidden in behavior is brittle.

**Rejected alternatives.** Option (b), conversation-initialization mode-locking, is acceptable as an optimization but not as the source of truth; copied messages, retries, and out-of-band handoff fragments need to remain self-describing. Option (c), behavioral inference from `message_type`, fails immediately for `clarification.request`, which can appear inside second-opinion, red-team, or handoff contexts and has different incentives in each.

**4. Q4 — Escalation Function**

**Recommendation.** Implement this signature:

```ts
type Reversibility = "reversible" | "irreversible" | "security-sensitive";

interface ConversationContext {
  conversation_id: string;
  protocol_mode: "second_opinion" | "red_team" | "handoff" | "clarification" | "decision_log";
  message_type: string;
  user_visible: boolean;
  money_or_legal_impact: boolean;
  touches_secrets_or_credentials: boolean;
  source_confidence: number;
  deadline_ms?: number;
}

function escalate(
  bayes_factor: number,
  risk: number,
  reversibility: Reversibility,
  conversation_context: ConversationContext,
): { decision: "auto_resolve" | "escalate_to_user"; rationale: string } {
  // Normalize BF to evidence strength that agents agree/disagree.
  // BF < 3: barely worth mentioning
  // 3 <= BF < 10: substantial
  // 10 <= BF < 30: strong
  // 30 <= BF < 100: very strong
  // >= 100: decisive

  if (!Number.isFinite(bayes_factor) || bayes_factor <= 0) {
    return { decision: "escalate_to_user", rationale: "Invalid Bayes factor." };
  }
  if (risk < 0 || risk > 1) {
    return { decision: "escalate_to_user", rationale: "Risk outside [0,1]." };
  }
  if (reversibility === "irreversible" || reversibility === "security-sensitive") {
    return { decision: "escalate_to_user", rationale: "Irreversible or security-sensitive action." };
  }
  if (
    conversation_context.money_or_legal_impact ||
    conversation_context.touches_secrets_or_credentials
  ) {
    return { decision: "escalate_to_user", rationale: "High-impact context requires user confirmation." };
  }
  if (risk < 0.3 && bayes_factor >= 10) {
    return { decision: "auto_resolve", rationale: "Low risk and strong-or-better agreement evidence." };
  }
  if (risk >= 0.7 || bayes_factor < 3) {
    return { decision: "escalate_to_user", rationale: "High risk or disagreement evidence is too weak." };
  }
  if (bayes_factor >= 30 && risk < 0.5) {
    return { decision: "auto_resolve", rationale: "Very strong agreement evidence and moderate-low risk." };
  }
  return { decision: "escalate_to_user", rationale: "Middle-zone uncertainty: require human tie-break." };
}
```

**Rationale.** Auto-resolve threshold is `risk < 0.3` plus `BF >= 10`, because “strong” agreement is the first Jeffreys band that should suppress user interruption. Escalate threshold is `risk >= 0.7`, `BF < 3`, irreversible, security-sensitive, secrets, money, legal, or externally visible actions. Middle zone is `0.3 <= risk < 0.7` or `3 <= BF < 10`, and defaults to user escalation unless `BF >= 30` and `risk < 0.5`. Risk wins over Bayes factor because agreement between agents does not reduce blast radius; two agents can confidently agree on a bad irreversible action.

**Rejected alternatives.** Do not use Bayes factor alone; that optimizes agreement, not user welfare. Do not use risk alone; it would escalate too many harmless disagreements and kill the value of second opinions. Do not auto-resolve the entire middle zone; bounded rationality is explicitly in scope, and the locked constraint requires human-in-the-loop escalation paths.

**5. Q5 — Identity Verification On Every Message**

**Recommendation.** Use option **(a)**: sign every canonical message body with the sender’s ed25519 private key, verify with the known public key, and derive `agent_id = sha256(ed25519_pub_key)`. Add TOFU only as a bootstrap convenience for local dev, never as the sole trust model. The v0.3 Phase 1 identity model already establishes `agent_id` as sha256 of an ed25519 public key and couples identity with visibility/auth [spec: 2026-05-26-sc-memory-v0.3-upgrade-spec.md §1, §Phase 1]. A2A says identity is handled at the protocol layer and servers must authenticate every incoming request based on declared requirements [doc: https://a2a-protocol.org/latest/specification/ §7.1-§7.4].

**Rationale.** Signing every message binds sender, recipient, payload, mode, nonce, timestamp, and conversation state. It also fixes the notify-handler class of bug where a payload carries `agent_id` but the persistence path discards or rewrites attribution [code: notify-handler.ts:25] [code: notify-handler.ts:118-127]. A2A Agent Cards may be signed with JWS and canonicalized [doc: https://a2a-protocol.org/latest/specification/ §8.4], so ACS should mirror that discipline for messages even if the signature algorithm is ed25519 rather than Agent Card JWS in Phase 1.

**Rejected alternatives.** TOFU alone is vulnerable to first-contact impersonation and stale key pinning. A centralized registry is overbuilt for two local agents and violates the decentralized premise. A bearer token alone authenticates the HTTP caller but does not give durable, portable message-level attribution once the message is stored, forwarded, or replayed.

**6. Q6 — Persistence + Transport Architecture**

**Recommendation.** Choose option **(a)**: a separate ACS service with its own append-only event log and dedicated operations: `acs_send`, `acs_receive`, `acs_subscribe`, `acs_ack`, `acs_get_conversation`, and `acs_mark_durable`. Transport is A2A JSON-RPC over HTTP for request/response plus SSE for push delivery. Persistence is an ACS event log keyed by `conversation_id`, `message_id`, `recipient_agent_id`, delivery state, ack state, and signature verification state. Memory persistence happens only as an explicit side effect: `decision.recorded`, accepted `handoff.state`, and final review artifacts may be written into each agent’s memory MCP as normal memory rows via MCP tools. The current SC HTTP server already shows the local transport shape, session tracking, `/mcp` routing, and Streamable HTTP usage [code: http-server.ts:18-19] [code: http-server.ts:365-405]. The PMM bridge shows graceful degradation for separate stores with `available=false` and return-empty behavior [code: pmm-bridge.ts:65-76] [code: pmm-bridge.ts:113-150].

**Push delivery.** Use SSE subscription as the Phase 1 “new message arrived” primitive: recipient opens `acs_subscribe`/A2A streaming for its `recipient_agent_id`; ACS streams message events and expects `acs_ack`. If recipient is down, ACS retains pending messages in the event log and delivers on next subscribe. Polling via `acs_receive` exists as fallback and test harness, not primary UX. Do not rely on in-memory queue only; SC’s notify queue is capped FIFO and drains on the next tool call, so it can lose delivery state across process restarts [code: notify-handler.ts:50-65] [code: notify-handler.ts:140-143].

**Rationale.** This preserves the locked “each agent owns its memory” rule and makes ACS communication-only. It also respects C’s bridge: direct LanceDB cross-read is a memory bridge, not an ACS transport [spec: 2026-05-26-codex-memory-system-design.md §5.3]. C’s concurrency section is read-only from Codex into SC memory and explicitly avoids write conflicts [spec: 2026-05-26-codex-memory-system-design.md §6.2]; ACS should not add cross-writes through that path.

**Rejected alternatives.** Option (b), adding `memory_acs_send` to memory MCPs, couples transport lifecycle to memory lifecycle and encourages memory tools to become a mailbox. Option (c) is the wrong abstraction: ACS messages as shared memory rows are communication-via-action through shared state. C’s own spec distinguishes direct cross-read as free communication but says communication-via-shared-rows is general communication and carries the wrong complexity class [spec: 2026-05-26-codex-memory-system-design.md §5.3]. That directly conflicts with the locked constraint to use FREE communication.

**7. Q7 — One Pushback**

**Pushback: “Outer protocol: A2A v1.0 — the Google ADK standard” is too tightly phrased.** The outer protocol should be “A2A v1.0-compatible,” but ACS should not bind its core semantics to ADK-specific assumptions. The current A2A spec is under the A2A project and defines multiple protocol bindings, Agent Cards, JSON-RPC, REST, and gRPC; ADK can be one implementation path, not the normative source [doc: https://a2a-protocol.org/latest/specification/]. This matters because ACS needs ed25519 message signatures, reward contracts, and memory-specific handoff semantics that are ACS extensions on top of A2A, not ADK features.

**Rationale.** Keeping the boundary at “A2A-compatible” lets ACS interoperate while still using its own canonical envelope and identity model. It also avoids making the design fragile if ADK naming, generated schemas, or SDK behavior diverge from the released protocol.

**Rejected alternatives.** I would not push back on decentralization, sparse graph, mode-specific rewards, free communication, A2A outer/MCP inner, or ed25519 fingerprint identity. Those constraints are coherent and mutually reinforcing.

**8. Q8 — One Missing Item**

**Missing item: replay protection and idempotency.** Add `nonce`, `message_id`, `timestamp`, `ttl_ms`, and `body_hash` to every signed envelope. Recipient stores a replay cache keyed by `(sender_agent_id, message_id)` and rejects duplicate `message_id` with mismatched body hash; exact duplicate gets the original ack/result. A2A already notes that send-message operations may use `messageId` to detect duplicates [doc: https://a2a-protocol.org/latest/specification/ §3.3.1], but ACS needs this as a hard requirement because signed messages can be stored, retried, streamed, and written into memory.

**Rationale.** Without replay protection, a valid old `decision.recorded` or `handoff.state` can be resent and re-applied, creating duplicate decisions or stale continuation state. This is especially dangerous because Phase 1 will have SSE reconnects and recipient-down retry behavior.

**Rejected alternatives.** Vector clocks and full causal DAGs are useful later, but they are heavier than needed for Phase 1. Conversation lifecycle is also important, but replay/idempotency must come first because it is a security and correctness primitive for every transport and persistence choice.