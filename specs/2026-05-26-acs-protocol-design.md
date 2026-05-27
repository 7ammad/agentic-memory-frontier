# ACS Protocol Design Spec (Sub-Project D)

**Project:** Agentic Memory System
**Date:** 2026-05-26
**Status:** DRAFT — awaiting Step 6 codex strict-review verification
**Deliverable target:** this file
**Inputs:** [mem_a4af3f41] (6 ACS constraints), [spec: 2026-05-26-codex-memory-system-design.md] (sub-project C — bridge transport layer), [spec: 2026-05-26-sc-memory-v0.3-upgrade-spec.md] (v0.3 identity + visibility), [research/codex-counsel-D-output.md] (codex consult, 22,385 chars, with A2A spec citations).
**Sequencing:** A → B → C → D, all verification-gated. D unlocks once codex strict-review returns READY.

---

## 1. Executive Verdict

Build ACS as an explicit, signed **A2A v1.0-compatible service**, not as messages hidden inside memory rows. Phase 1 implements:

1. A public Agent Card at `GET /.well-known/agent-card.json` advertising capabilities, ed25519 public key, supported message types, and protocol modes.
2. `POST /rpc` for JSON-RPC 2.0 — `SendMessage` for request/response and `SendStreamingMessage` for SSE-streamed long-running tasks.
3. **Ed25519 signatures on every canonical message body** — no TOFU as sole trust model. `agent_id = sha256(ed25519_pub_key)` is shared with SC v0.3 and Codex memory C.
4. **Explicit `protocol_mode` + `reward_contract` on every message** — not conversation-initialization-only, not behavioral inference. Each of the 5 starter message types declares its reward structure inline.
5. **Dedicated ACS service** with its own append-only event log keyed by `(conversation_id, message_id, recipient_agent_id, delivery_state, ack_state, sig_verify_state)`. **NOT** "messages as memory rows" — that's exactly the general-communication anti-pattern the locked constraints (and C's own §5.3 reasoning) rule out. Memory writes happen only as explicit side effects (`decision.recorded`, accepted `handoff.state`, final review artifacts).
6. **Escalation function** with Jeffreys scale × Codex risk-weighted thresholds: auto-resolve at `risk < 0.3 AND bayes_factor >= 10`, escalate at `risk >= 0.7 OR bayes_factor < 3 OR irreversible OR security-sensitive OR money/legal/credential-touching`. Risk wins ties with Bayes factor (two agents can confidently agree on a bad action).

Phase 1 missing artifact (codex's accepted "missing item"): **replay protection + idempotency**. Every signed envelope carries `nonce`, `message_id`, `timestamp`, `ttl_ms`, `body_hash`. Recipient maintains a replay cache keyed by `(sender_agent_id, message_id)`; exact duplicate gets the original ack; mismatched body hash with duplicate ID is rejected.

Codex's pushback was accepted: the outer protocol is "A2A v1.0-**compatible**," not "the Google ADK standard." ADK is one implementation path; A2A is its own project [doc: https://a2a-protocol.org/latest/specification/].

---

## 2. Architecture and current-state assessment

### 2.1 What we are NOT reusing — and why

The existing SC `/notify` HTTP handler is **not** ACS. It receives a payload, parses an `agent_id` [code: notify-handler.ts:22, 25], but the persistence path **discards identity** and **hardcodes `visibility: "shared"`** [code: notify-handler.ts:118-126]. The in-memory FIFO queue [code: notify-handler.ts:50-65, 140-143] drains on next tool call without durable delivery semantics, so process restarts lose state.

This is the prior art's failure mode catalog. ACS must fix all three: preserve `agent_id` in attribution, treat visibility as the receiver-side filter (not a hardcoded sender claim), and use an append-only event log instead of in-memory FIFO.

### 2.2 What we ARE reusing

- **Streamable HTTP transport pattern** [code: http-server.ts:18-19, 365-405] — SC's `StreamableHTTPServerTransport` with per-session tracking is the closest local implementation pattern for A2A's HTTP+SSE.
- **`PmmBridge` degradation discipline** [code: pmm-bridge.ts:65-76, 113-150] — `available=false` with empty-result fallback. ACS adopts this for "recipient agent is down" handling.
- **Ed25519 identity model from v0.3 Phase 1** [spec: 2026-05-26-sc-memory-v0.3-upgrade-spec.md §Phase 1] — `agent_id = sha256(ed25519_pub_key)`. ACS reuses the exact same identity bytes; no new identity registry.
- **C's bridge as a memory channel, NOT an ACS channel** [spec: 2026-05-26-codex-memory-system-design.md §5.3] — C's direct LanceDB cross-read is free communication for memory state. ACS is a separate free-communication channel for messages.

### 2.3 The decentralization invariant

Per [mem_a4af3f41] principle 1: each agent owns its memory; ACS is communication-only. The architectural translation: ACS state (event log, delivery state, ack state) lives in a separate persistence layer from either agent's memory. ACS reads/writes to memory only as an explicit side effect of accepting a `decision.recorded` or `handoff.state`. This preserves the "each agent owns its memory" invariant — neither SC nor Codex can mutate the other through ACS message delivery.

---

## 3. Gap analysis (ranked by blast radius)

| # | Gap | Blast radius | Phase |
|---|-----|--------------|-------|
| G1 | No replay protection — old `decision.recorded` or `handoff.state` could re-apply | Duplicate decisions, stale continuation tokens, audit corruption | 1 (mandatory) |
| G2 | No message-level signature — bearer-token auth alone breaks once messages are stored/forwarded | Forged provenance survives across storage; the notify-handler bug class extends to ACS | 1 (mandatory) |
| G3 | No explicit `protocol_mode` per message — agents could mis-interpret reward structure under partial observability | Wrong incentive applied (e.g., red-team logic in a handoff context) | 1 (mandatory) |
| G4 | No ed25519 keypair for SC — Codex C generates one; SC v0.3 Phase 1 plans one but it's not shipped | ACS can't bootstrap signatures from SC side until SC Phase 1 lands | Blocks ACS Phase 1 |
| G5 | No bridge between ACS event log and memory `decision.recorded` writes — risk of dropped writes if MCP call fails | Decision recorded over ACS but never persisted in memory | 1 |
| G6 | No SSE reconnection / message retry semantics | Recipient-down messages lost or duplicated on reconnect | 1 |
| G7 | No conversation lifecycle (start/close/timeout) | Conversations leak open forever, memory-pressure unbounded | 2 |
| G8 | No rate-limit between agents | One-agent runaway can flood the other | 2 |

G1-G6 must be addressed in Phase 1. G7-G8 can defer.

---

## 4. Codex counsel — verbatim reference

See [research/codex-counsel-D-output.md](../research/codex-counsel-D-output.md) for the full 22,385-character output. Headline:

- **Q1 wire format**: Agent Card at `/.well-known/agent-card.json`, JSON-RPC over HTTP+SSE for streaming. Phase 1 subset of A2A v1.0.
- **Q2 message schemas**: One canonical envelope with `acs_version`, `message_id`, `conversation_id`, causality, sender/recipient ids, mode, contract, timestamp, ttl, nonce, payload, sig. Concrete payload shapes per message type (see §5.2).
- **Q3 reward mode**: Option (a) — explicit `protocol_mode` + `reward_contract` in EVERY message. Conversation default acceptable; messages must repeat.
- **Q4 escalation function**: Concrete TypeScript signature with risk-wins-over-BF logic. Auto-resolve at `risk<0.3 AND BF>=10`; escalate at `risk>=0.7 OR BF<3 OR irreversible OR security-sensitive`.
- **Q5 identity**: Option (a) — sign every message with ed25519. TOFU as bootstrap convenience only.
- **Q6 persistence + transport**: Option (a) — dedicated ACS service with append-only event log + A2A JSON-RPC over HTTP+SSE. Option (c) rejected because shared-memory-row communication = general communication, which the locked constraints rule out and C's §5.3 confirms.
- **Q7 pushback**: "A2A v1.0 - the Google ADK standard" is too tight. Use "A2A v1.0-compatible" instead.
- **Q8 missing**: Replay protection + idempotency — nonces, message_id-keyed replay cache, body_hash.

This synthesis adopts all of codex's recommendations. The Q7 pushback is accepted (constraint wording rewritten in §1). The Q8 missing item is elevated to Phase 1 mandatory.

---

## 5. Final answers — SOURCE FACT / INFERENCE / JUDGMENT / OPEN QUESTION

### 5.1 Wire format (Q1) — JUDGMENT: Phase 1 A2A subset

This is vendor-fact territory (A2A v1.0 spec exists, codex read it via web_search). MIT-12 doesn't cover the wire format. Citing codex's read of the spec:

[doc: https://a2a-protocol.org/latest/specification/]:
- §8.2, §14.3 — Agent Card at `/.well-known/agent-card.json`
- §4.4.1 — Agent Card fields: name, description, supportedInterfaces (ordered), version, capabilities, securitySchemes, securityRequirements, input/output modes, skills, optional signatures
- §9.1-§9.4 — JSON-RPC methods: `SendMessage`, `SendStreamingMessage`, `GetTask`, `ListTasks`, `CancelTask`, `SubscribeToTask`, the push notification configuration methods family (`CreateTaskPushNotificationConfig`, `GetTaskPushNotificationConfig`, `ListTaskPushNotificationConfigs`, `DeleteTaskPushNotificationConfig`), and `GetExtendedAgentCard`
- §3.3.3 — Async model: server returns Task or Message immediately; client tracks updates via polling, streaming, or push
- §7.1-§7.4 — Identity/auth required on every incoming request per declared scheme
- §8.4 — Agent Cards may be signed with JWS and canonicalized

**JUDGMENT for ACS Phase 1**: implement Agent Card + `SendMessage` + `SendStreamingMessage` + `GetTask` + minimal `ListTasks(by contextId)` + bearer/auth headers + `A2A-Version` header + **signed custom ACS envelope inside `Message.parts[].metadata.acs` OR `params.acs_message`**. Defer: file exchange, push-notification webhook config, gRPC binding, REST binding, extended Agent Card, registry discovery, multi-tenant routing, non-local HTTPS deployment.

**JUDGMENT for ACS Agent Card content (Phase 1)**:

```json
{
  "name": "claude-superclaude-memory" /* or "codex-memory" */,
  "description": "string",
  "version": "0.1.0",
  "supportedInterfaces": [
    {"transport": "JSONRPC", "url": "http://127.0.0.1:18801/rpc", "via": "acs-service", "routing": "by_recipient_agent_id"},
    {"transport": "SSE",     "url": "http://127.0.0.1:18801/events", "via": "acs-service", "routing": "by_recipient_agent_id"}
  ],
  "capabilities": {
    "streaming": true,
    "pushNotifications": false
  },
  "securitySchemes": {
    "acs_ed25519": {"type": "custom", "scheme": "Ed25519-Envelope-Signature"}
  },
  "securityRequirements": [{"acs_ed25519": []}],
  "skills": [
    {"id": "second_opinion", "description": "Request a second opinion on a question"},
    {"id": "review", "description": "Submit or receive findings against a target"},
    {"id": "handoff", "description": "Transfer task state to another agent"},
    {"id": "clarification", "description": "Ask or answer a blocking clarification"},
    {"id": "decision_log", "description": "Record a durable decision"}
  ],
  "extensions": {
    "acs": {
      "version": "0.1.0",
      "supported_versions": ["0.1.0"],
      "min_compatible_version": "0.1.0",
      "agent_id": "{sha256-ed25519-pubkey-hex}",
      "ed25519_pub_key": "{base64url-encoded-pubkey}",
      "supported_message_types": [
        "second_opinion.request", "second_opinion.response",
        "review.findings", "handoff.state", "handoff.accepted",
        "clarification.request", "clarification.response",
        "decision.recorded", "ack"
      ],
      "supported_protocol_modes": ["second_opinion", "red_team", "handoff", "clarification", "decision_log"]
    }
  }
}
```

**ACS version negotiation rules**:
- Every incoming message envelope's `acs_version` field is checked against the recipient's `supported_versions` list in its Agent Card.
- If `acs_version` is in `supported_versions`: process normally.
- If `acs_version` is below `min_compatible_version`: reject with error `ACS_VERSION_UNSUPPORTED` and include the recipient's `supported_versions` in the error response.
- If `acs_version` is ABOVE the recipient's highest `supported_versions`: reject with `ACS_VERSION_TOO_NEW`, include recipient's range. Sender should downgrade or escalate.
- Forward-incompatibility: if the message contains a `message_type` not in `supported_message_types`, reject with `MESSAGE_TYPE_UNSUPPORTED`.
- This is fail-closed, not graceful-degradation, in Phase 1 to keep semantics deterministic. Graceful-degradation deferred to Phase 2 (item 19 in §7).

**Rejected alternatives**: do NOT expose only MCP `/mcp` as ACS — MCP is the right inner-tool layer (JSON-RPC tool calls) but the agent-to-agent contract belongs at the A2A layer. Do NOT implement only `/notify` — the existing notify queue is in-memory FIFO with no durable delivery [code: notify-handler.ts:50-65].

### 5.2 Five message schemas (Q2) — JUDGMENT: canonical envelope + 5 payloads

**JUDGMENT for ACS envelope (Phase 1)** — one canonical shape carries every message type:

```json
{
  "acs_version": "0.1.0",
  "message_id": "uuid-v7",
  "conversation_id": "uuid-v7",
  "causality": {"parent_message_id": "uuid-v7|null", "seq": 1},
  "sender_agent_id": "sha256-ed25519-pubkey-hex",
  "recipient_agent_id": "sha256-ed25519-pubkey-hex",
  "message_type": "second_opinion.request",
  "protocol_mode": "second_opinion",
  "reward_contract": "common_reward_user_welfare_preserve_attribution",
  "timestamp": "2026-05-26T12:00:00.000Z",
  "ttl_ms": 86400000,
  "nonce": "128-bit-base64url",
  "body_hash": "sha256(canonical-payload)",
  "requires_ack": true,
  "payload": { /* type-specific */ },
  "sig": {
    "alg": "Ed25519",
    "key_id": "sha256-ed25519-pubkey-hex",
    "value": "base64url(signature-over-canonical-envelope-without-sig)"
  }
}
```

### 5.2.1 Signature canonicalization (mandatory)

The envelope's `sig.value` is `Ed25519_sign(privkey, JCS(envelope_without_sig))`, where:

- **JCS** = RFC 8785 JSON Canonicalization Scheme. Same canonical form A2A Agent Cards use [doc: https://a2a-protocol.org/latest/specification/ §8.4].
- **`envelope_without_sig`** = the envelope JSON object with the `sig` field omitted entirely (not set to null — fully removed before JCS).
- **Field ordering**: JCS sorts object keys lexicographically; no manual ordering needed.
- **Required fields**: `acs_version`, `message_id`, `conversation_id`, `causality.parent_message_id`, `causality.seq`, `sender_agent_id`, `recipient_agent_id`, `message_type`, `protocol_mode`, `reward_contract`, `timestamp`, `ttl_ms`, `nonce`, `body_hash`, `requires_ack`, `payload`. If any are missing, signing fails closed.
- **Null/undefined handling**: explicit `null` is preserved; undefined fields are omitted entirely. (JCS handles both consistently.)
- **`body_hash`** = `sha256_hex(JCS(payload))`. Computed before signing the envelope. Recipient re-computes and compares before signature verification.
- **`timestamp`** = ISO 8601 string (e.g., `"2026-05-26T12:00:00.000Z"`) — JCS preserves as-is.
- **Verification**: recipient runs `Ed25519_verify(sender_pubkey, sig.value, JCS(envelope_without_sig))`. Then independently recomputes `body_hash` from `JCS(payload)` and compares. Any mismatch → reject with `SIGNATURE_INVALID` or `BODY_HASH_MISMATCH`.

Concrete payloads for each starter message type are documented in full in [research/codex-counsel-D-output.md] §Q2. Summary:

| Message type | Direction | Ack required? | Notes |
|--------------|-----------|---------------|-------|
| `second_opinion.request` → `second_opinion.response` | request/response | sync if fast; async via Task otherwise | payload: question, context refs, caller_position, requested_depth (fast/strong/deep), risk, deadline_ms, attribution_required |
| `review.findings` | one-way + ack | ack required (delivery only, not agreement) | payload: review_target, findings[] with severity/claim/evidence/fix, overall_verdict (pass/patch_first/block) |
| `handoff.state` | one-way + ack | ack required, returns continuation_token | payload: goal, state_summary, decisions, files_changed, verification, remaining_steps, risks, memory_refs |
| `clarification.request` → `clarification.response` | request/response | sync usually | payload: question, choices, freeform_allowed, blocking, needed_by_message_id |
| `decision.recorded` | one-way | ack required (delivery only) | payload: decision, rationale, owner, scope, supersedes, evidence_refs, memory_write spec |

Ack envelope:
```json
{
  "message_type": "ack",
  "payload": {"acked_message_id": "uuid-v7", "accepted_for_processing": true, "durable_ref": "acs:event_id"}
}
```

**Rejected alternatives**: do NOT encode as plain text — reward mode, signature scope, ack semantics would be ambiguous. Do NOT use JSON-RPC notification semantics (one-way, no response) for `review.findings`, `handoff.state`, `decision.recorded` — they need durable ack.

### 5.3 Reward structure operationalization (Q3) — JUDGMENT: explicit per-message

**SOURCE FACT** [`mit12: book-08-chunk-0080 pp.274-278`]: "the multi-agent credit assignment problem" requires "individual agent utility functions" that can "discriminate between joint histories with different action values." For common-reward agents, the IGM property + linear value decomposition gives `r_t = sum_i(r_i_t)` — the sum of individual utilities equals the common reward.

**SOURCE FACT** [`mit12: book-09-chunk-0050 pp.205-208`] (already cited in C spec): communication × observability table — partial observability + free communication = MPOMDP (PSPACE), partial observability + general communication = Dec-POMDP (NEXP). ACS is partial observability (each agent has private memory + private model state) + free communication (explicit message channel).

**INFERENCE**: under partial observability, an agent cannot reliably infer the other agent's reward structure from observed behavior. The reward contract must be explicit in the message, not behavioral. Conversation-initialization mode-locking (option b) breaks when messages are retried, forwarded, copied across conversations, or partially delivered.

**JUDGMENT for ACS reward operationalization**: Option (a) — explicit `protocol_mode` ∈ `{"second_opinion", "red_team", "handoff", "clarification", "decision_log"}` AND `reward_contract` in every message. Conversation initialization may set a default; receivers must reject mismatched mode-changes unless the message type is an allowed transition (e.g., `clarification.request` can ride inside any conversation).

The MARL design dimensions (Size, Knowledge, Observability, Rewards, Objective, Centralization & Communication) fill in for ACS as:

| Dimension | ACS Phase 1 |
|-----------|-------------|
| Size | 2 agents + human at center (sparse star graph per principle 3) |
| Knowledge | Each agent has private memory; partial knowledge of the other |
| Observability | Partial — no direct introspection of other agent's reasoning |
| Rewards | Mode-specific: common-reward (second_opinion, clarification), zero-sum-findings + common-sum user welfare (red_team), sequential-common state-transfer (handoff, decision_log) |
| Objective | Mode-specific (see Rewards) |
| Centralization & Communication | Decentralized agents, sparse free-communication channel via A2A |

**Rejected alternatives**: option (b) acceptable as optimization (default mode for a conversation) but not as source of truth — retries and forwards need self-describing messages. Option (c) (behavioral inference) breaks on `clarification.request`, which appears in second_opinion, red_team, AND handoff contexts with different incentives in each.

### 5.4 Escalation function (Q4) — JUDGMENT: Jeffreys × Codex risk

**SOURCE FACT** [`mit12: book-11-chunk-0053 pp.209-213`]: Jeffreys scale of evidence for interpreting Bayes factors (Murphy *Probabilistic Machine Learning: An Introduction*, Table 5.6):

| Bayes factor BF(1,0) | Interpretation |
|----------------------|----------------|
| BF < 1/100 | Decisive evidence for M0 |
| BF < 1/10 | Strong evidence for M0 |
| 1/10 < BF < 1/3 | Moderate evidence for M0 |
| 1/3 < BF < 1 | Weak evidence for M0 |
| 1 < BF < 3 | Weak evidence for M1 |
| 3 < BF < 10 | Moderate evidence for M1 |
| BF > 10 | Strong evidence for M1 |
| BF > 100 | Decisive evidence for M1 |

In ACS terms: M1 = "agents disagree," M0 = "agents agree" (or any framing — what matters is the BF magnitude maps to evidence strength).

**INFERENCE**: Jeffreys' bands give a natural set of action thresholds. "Strong" (BF ≥ 10) is the first band where evidence becomes worth acting on without human review IF risk is low. Below "weak" (BF < 3), there isn't enough evidence to act either way without human input. Risk modulates: even strong agreement on a high-risk action should escalate (two agents can confidently agree on a bad irreversible decision).

**JUDGMENT for ACS escalation function** — concrete TypeScript:

```typescript
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
  risk: number,                       // [0, 1] from Codex's risk model
  reversibility: Reversibility,
  conversation_context: ConversationContext,
): { decision: "auto_resolve" | "escalate_to_user"; rationale: string } {
  // Input validation
  if (!Number.isFinite(bayes_factor) || bayes_factor <= 0) {
    return { decision: "escalate_to_user", rationale: "Invalid Bayes factor." };
  }
  if (risk < 0 || risk > 1) {
    return { decision: "escalate_to_user", rationale: "Risk outside [0,1]." };
  }
  // Hard escalations (risk-side wins over BF)
  if (reversibility === "irreversible" || reversibility === "security-sensitive") {
    return { decision: "escalate_to_user", rationale: "Irreversible or security-sensitive action." };
  }
  if (conversation_context.money_or_legal_impact ||
      conversation_context.touches_secrets_or_credentials) {
    return { decision: "escalate_to_user", rationale: "High-impact context requires user confirmation." };
  }
  // Auto-resolve case — single condition, strictly within locked threshold
  if (risk < 0.3 && bayes_factor >= 10) {
    return { decision: "auto_resolve", rationale: "Low risk (risk<0.3) and strong-or-better agreement (Jeffreys: strong, BF≥10)." };
  }
  // Hard escalations on weak evidence or high risk
  if (risk >= 0.7 || bayes_factor < 3) {
    return { decision: "escalate_to_user", rationale: "High risk (risk≥0.7) or evidence below Jeffreys 'weak' threshold (BF<3)." };
  }
  // Middle zone: default to escalation (bounded rationality + human-in-loop principle)
  return { decision: "escalate_to_user", rationale: "Middle-zone uncertainty: require human tie-break." };
}
```

**Rationale**: risk wins over BF because agreement does not reduce blast radius — two agents can confidently agree on a bad irreversible action. The only auto-resolve case is `risk<0.3 AND BF≥10`, matching the locked threshold exactly (codex verification pass 1 flagged a `BF≥30 && risk<0.5` branch in an earlier draft as constraint drift; removed). Everything else escalates by default. This implements principle 6 from [mem_a4af3f41] (human-in-the-loop escalation paths).

**Rejected alternatives**: BF alone optimizes agreement, not user welfare. Risk alone kills the value of second opinions by escalating harmless disagreements. Auto-resolving the entire middle zone violates principle 6 (bounded rationality).

**OPEN QUESTION**: how does each agent compute the Bayes factor in practice? Two posteriors over (agree, disagree) given the available evidence — but what's the operational definition of "evidence" for an agent's claim about another agent's reasoning? Probable answer: codex's risk model already gives a `source_confidence`; combine that with self-reported confidence on both sides to derive a synthetic BF. This needs a Phase 2 calibration experiment, not a paper answer.

### 5.5 Identity verification (Q5) — JUDGMENT: sign every message

**JUDGMENT for ACS identity (Phase 1)**: Option (a) — sign every canonical message body (envelope minus `sig` field) with the sender's ed25519 private key. Verify on receipt against the sender's `ed25519_pub_key` from their Agent Card. Derive `agent_id = lowercase hex sha256(ed25519_pub_key)` per [spec: 2026-05-26-sc-memory-v0.3-upgrade-spec.md §Phase 1]. Use TOFU **only** as a local-dev bootstrap convenience (first message from an unknown `agent_id`: fetch Agent Card, pin key, log); never as the sole trust model in any persistent or shared deployment.

**Why every message and not just session-start handshake**: per [code: notify-handler.ts:22-25, 118-126], the notify-handler bug class is exactly this — payload carries `agent_id` but persistence discards/rewrites attribution. Session-only auth means the same bug class can extend to ACS: anyone with session access can forge subsequent messages. Per-message signature binds sender, recipient, payload, mode, nonce, timestamp, conversation state.

A2A v1.0 [doc: https://a2a-protocol.org/latest/specification/ §7.1-§7.4] requires authentication on every incoming request per declared scheme. Agent Cards may be JWS-signed [doc: §8.4]. ACS extends this discipline to messages.

**Rejected alternatives**: TOFU alone is vulnerable to first-contact impersonation and stale key pinning. Centralized key registry is overbuilt for two local agents and violates the decentralization principle. Bearer token alone authenticates the HTTP caller but doesn't give durable, portable message-level attribution once the message is stored, forwarded, or replayed (the exact failure mode the notify-handler exhibits).

**OPEN QUESTION**: should ACS support key rotation in Phase 1 or defer to Phase 3 (matches C spec §7 Phase 3 item 22)? Recommend defer — Phase 1 ships with `key_id` field in the signature, which is forward-compatible with rotation.

### 5.6 Persistence + transport architecture (Q6) — JUDGMENT: dedicated ACS service

**SOURCE FACT** [`mit12: book-09-chunk-0050 pp.205-208`] (already cited): free communication outside the model is in MPOMDP/MMDP complexity class (P/PSPACE); communication via shared state is general communication in Dec-MDP/Dec-POMDP (NEXP).

**INFERENCE**: Option (c) — ACS messages as memory rows with `type="acs.*"` and `visibility="shared"`, retrieved via memory_search — is precisely communication-via-shared-state. C's spec §5.3 already articulates this: shared-memory communication is general communication. Picking option (c) for ACS contradicts both the locked constraint (use FREE communication, not GENERAL) and C's own internal logic. **Option (c) is rejected on theoretical grounds, not just operational ones.**

**JUDGMENT for ACS architecture (Phase 1)**: Option (a) — a dedicated ACS service with its own append-only event log. Operations: `acs_send`, `acs_receive`, `acs_subscribe`, `acs_ack`, `acs_get_conversation`, `acs_mark_durable`. Transport: A2A JSON-RPC over HTTP for request/response; SSE for push delivery. Persistence: append-only event log keyed by `(conversation_id, message_id, recipient_agent_id, delivery_state, ack_state, sig_verify_state)`. Memory persistence is an explicit side effect — `decision.recorded`, accepted `handoff.state`, and final review artifacts may be written into each agent's memory MCP as normal rows via MCP tools (the ACS service calls `memory_save` on the receiving agent's MCP).

**Push delivery (Phase 1)**: recipient subscribes via `acs_subscribe` or A2A `SubscribeToTask` over SSE. ACS streams new message events and expects `acs_ack`. If recipient is down, ACS retains pending messages in the event log and delivers on next subscribe. Polling via `acs_receive` is a fallback and test harness, not primary UX.

**Local deployment topology (Phase 1)**:

```
SC memory MCP            ACS service              Codex memory MCP
:18800/mcp               :18801/rpc               :18802/mcp
:18800/notify*           :18801/events (SSE)      :18802/.well-known/
:18800/.well-known/      :18801/.well-known/         agent-card.json
   agent-card.json          agent-card.json
       \                    /  \                    /
        \                  /    \                  /
         \                /      \                /
          \ MCP tool     /        \ MCP tool     /
           v calls only v          v calls only v
              Agent A                              Agent B
            (Claude/SC)                          (Codex)

  All A2A traffic flows agent <-> ACS :18801/rpc, routed by
  recipient_agent_id. Agents' :port/.well-known/agent-card.json
  endpoints are static descriptions only — no RPC there.

  * /notify is the existing SC primitive, kept for backward compat
    during Phase 1 migration; deprecated for new ACS messages.
```

**Port and host configuration (Phase 1)**:

| Service | Default port | Default path | Env override (port) | Env override (host) | Notes |
|---------|--------------|--------------|---------------------|---------------------|-------|
| SC memory MCP | `:18800` | `/mcp`, `/notify`, `/.well-known/agent-card.json` | `SC_MEMORY_PORT` | `SC_MEMORY_HOST` (default `127.0.0.1`) | existing MCP layer — D adds the static Agent Card endpoint |
| ACS service | `:18801` | `/rpc`, `/events`, `/.well-known/agent-card.json` | `ACS_SERVICE_PORT` | `ACS_BIND_HOST` (default `127.0.0.1`) | new in D — the routing/relay |
| Codex memory MCP | `:18802` | `/mcp`, `/.well-known/agent-card.json` | `CODEX_MEMORY_PORT` | `CODEX_MEMORY_HOST` (default `127.0.0.1`) | from C spec; D adds the static Agent Card endpoint. Must differ from `:18800` to avoid collision with SC. |

**Collision behavior**: if any service finds its default port already bound at startup, it logs `PORT_IN_USE` with the conflicting PID (where discoverable on Windows via `netstat -ano`), refuses to start, and exits non-zero. Phase 1 ships no auto-port-bumping — failures are explicit. Phase 2+ may add auto-bump with a registry file.

**Agent Card advertised URLs (relay topology)**: each agent's Agent Card lists the **ACS service** endpoint (`http://127.0.0.1:18801/rpc` and `:18801/events`) as the way to reach that agent. Routing happens via the `recipient_agent_id` field in the message envelope, NOT by the URL itself. So both SC's Agent Card and Codex's Agent Card list the same `:18801` ACS URLs — what distinguishes them is the `extensions.acs.agent_id` field in each card, which the sender uses to populate `recipient_agent_id` when sending. Memory MCP endpoints (`:port/mcp`) are NOT in Agent Cards — those are inner MCP tool layers consumed by the agent itself, not by other agents (see §5.6.1).

**Where each Agent Card is served**: the Agent Card JSON is served by each agent's own MCP HTTP layer at `:port/.well-known/agent-card.json` (SC `:18800`, Codex `:18802`) — that's just a static description endpoint, NOT an A2A RPC endpoint. The ACS service ALSO serves its own Agent Card at `:18801/.well-known/agent-card.json` describing the relay's own capabilities. **Discovery flow**: a new agent connecting first GETs each known peer's Agent Card from the peer's MCP `/.well-known/` path to learn their `agent_id` + public key + supported features; subsequent A2A messages route through ACS `:18801/rpc` using `recipient_agent_id`.

### 5.6.1 MCP inner boundary — what "MCP inner" means

The locked constraint says "outer protocol: A2A v1.0; inner protocol: MCP for tool access." Concretely:

- **MCP is used by each AGENT internally** for memory operations (memory_save, memory_search, etc.) on its own memory MCP. SC's agent uses `:18800/mcp`; Codex's agent uses `:18802/mcp`. This is the AGENT-to-its-own-memory channel.
- **A2A is used between agents** for ACS messages via `:18801/rpc`. This is the AGENT-to-AGENT channel.
- **ACS service invokes MCP only as a durable side effect** of accepting specific message types — namely `decision.recorded` and accepted `handoff.state` (see §7 Phase 1 item 11). The ACS service calls the RECIPIENT agent's memory MCP (`:18802/mcp` for Codex; `:18800/mcp` for SC) via its standard `memory_save` tool.
- **ACS does NOT broker arbitrary MCP tool calls** in Phase 1. An agent that wants to invoke a tool on its own memory uses its own direct MCP connection; it does not route MCP calls through ACS. Phase 1 acceptance test T10 specifically tests this side-effect-only pattern.
- **Phase 2+ may extend** ACS to broker arbitrary MCP tool calls for cross-agent tool access (e.g., "agent A asks ACS to call agent B's tool X with arguments Y") — currently NOT planned but the architecture allows it.

**Rationale**: this preserves "each agent owns its memory" (principle 1) and makes ACS purely communication. It respects C's bridge (which is for memory cross-read, NOT ACS transport — C §5.3, §6.2). C's concurrency analysis is read-only from Codex into SC memory and explicitly avoids write conflicts; ACS adds no cross-writes through that path.

**Rejected alternatives**: Option (b), adding `memory_acs_send` to memory MCPs, couples transport lifecycle to memory lifecycle and turns memory tools into a mailbox. Option (c) is wrong on theoretical grounds (see above) and operational ones (no SSE push, no append-only event log, no replay protection separate from memory dedup).

### 5.7 Pushback (Q7) — accepted: A2A v1.0-compatible, not ADK-bound

Codex's pushback was on the constraint phrasing "Outer protocol: A2A v1.0 - the Google ADK standard." The A2A spec is its own project at [doc: https://a2a-protocol.org/latest/specification/]; ADK is one implementation. ACS needs ed25519 message signatures, reward contracts, and memory-specific handoff semantics that are ACS extensions on top of A2A, not ADK features. **Accepted.** Throughout this spec, "A2A v1.0-compatible" is used; ADK is mentioned only as one possible client implementation, not as the normative source.

### 5.8 Missing item (Q8) — accepted: replay protection + idempotency

Codex flagged replay protection as the missing item. **Accepted as Phase 1 mandatory.**

**JUDGMENT for ACS replay protection (Phase 1)**:

- Every signed envelope carries `nonce` (128-bit random), `message_id` (uuid-v7), `timestamp`, `ttl_ms`, `body_hash` (sha256 of canonical payload).
- Recipient maintains a replay cache keyed by `(sender_agent_id, message_id)` with TTL = `ttl_ms` from envelope (default 24h).
- Exact duplicate (same `message_id` + matching `body_hash`): return the original ack/response. Idempotent retry.
- Mismatched body hash with duplicate `message_id`: reject with error `MESSAGE_ID_BODY_MISMATCH`. Log to ACS event log as a tamper-attempt signal.
- Expired `ttl_ms` on receipt: reject with `MESSAGE_EXPIRED`. Do not process even if signature is valid.
- A2A's note that `messageId` may be used for duplicate detection [doc: https://a2a-protocol.org/latest/specification/ §3.3.1] becomes a hard requirement in ACS.

**Why this is mandatory in Phase 1, not Phase 2**: SSE reconnects + recipient-down retry behavior + event-log replay all create replay surfaces. Adding replay protection after Phase 1 ships means every `decision.recorded` and `handoff.state` written in Phase 1 is potentially re-appliable, polluting the audit trail and corrupting continuation tokens.

**Rejected alternatives**: vector clocks and full causal DAGs are useful later (Phase 2+) but heavier than needed for Phase 1. Conversation lifecycle (close/timeout) is also important but replay/idempotency must come first because it is a security and correctness primitive for every transport and persistence choice.

---

## 6. Cross-cutting concerns

### 6.1 Construct validity of Bayes factor as a disagreement metric (Lens 5)

The Lens 5 query asked: is "Bayes factor between agents" actually measuring inter-agent disagreement, or is it a proxy that drifts?

**SOURCE FACT** [`mit12: book-10-chunk-0066 pp.199-202`] (cited in C spec, same principle applies): "it is meaningless to ascribe fairness as an attribute of models as opposed to actions, outputs, or decision processes."

**INFERENCE**: applied to ACS — it is meaningless to ascribe "agreement" as an attribute of agent outputs without reference to a downstream task. Two agents producing identical strings doesn't necessarily mean they "agree" — they may agree on the literal answer but disagree on confidence, evidence weight, or recommended action. The Bayes factor between agents is a proxy for the construct (inter-agent disagreement that warrants user attention). The proxy can drift in the same way cross-store embeddings drift (C spec §6.1).

**JUDGMENT for Phase 2 calibration**: just as C defers cross-store cosine ranking until empirical calibration (C spec §6.1, Phase 2 item 19), ACS should defer "auto-resolve based purely on inter-agent BF" until a calibration experiment measures: for a fixed set of (question, agent_A_answer, agent_B_answer, human_judgment) tuples, how well does the computed BF correlate with the human judgment of "these answers agree well enough that I wouldn't have wanted to be asked"? Phase 2 deliverable.

**OPEN QUESTION**: what's the minimum sample size for this calibration to be meaningful? Probably ≥30 hand-labeled disagreement cases. Hammad needs to confirm whether this is a real Phase 2 priority or whether the escalation function as specified is acceptable without empirical calibration (relying on the conservative middle-zone-escalates default).

### 6.2 Workflow state machines (Lens 4)

Each of the 5 starter messages has its own state machine. Phase 1 implements them as documented in §5.2 (sync vs async + ack requirements). Out of scope for Phase 1 but planned for Phase 2: deadlock detection (e.g., `clarification.request` blocking `handoff.state` blocking `clarification.request` between the same two agents). For Phase 1, the `ttl_ms` field provides a coarse deadlock breaker (timeout = abandon).

---

## 7. Priority backlog

### Phase 1 — MVP A2A service (P0, blocks D verification)

1. **ACS service skeleton** — Node/TypeScript, HTTP on `:18801` by default (env: `ACS_SERVICE_PORT`), bind host `127.0.0.1` (env: `ACS_BIND_HOST`). Streamable HTTP transport pattern from [code: http-server.ts:18-19].
2. **Agent Card generation + serving** — `GET /.well-known/agent-card.json` per §5.1. Both SC and Codex publish their own Agent Card on their respective ports (SC `:18800`, Codex per C §5.5). The ACS service `:18801` publishes a separate Agent Card describing its routing/relay role.
3. **Ed25519 keypair bootstrap for SC** — SC currently lacks one; this is a fast-path Phase 1 identity step (originally planned in v0.3 spec Phase 1 but not yet shipped). Procedure:
   - On SC server first start after this Phase 1 lands, generate ed25519 keypair via `@noble/ed25519` or NaCl bindings.
   - Store private key at `C:\Users\7amma\.claude\memory\identity\sc.ed25519.key` (mirror of Codex's `~/.codex/memory/identity/codex.ed25519.key` per C §5.5 step 1). Permissions: NTFS ACL restricting to user.
   - Store public key alongside as `sc.ed25519.pub` (base64url-encoded).
   - Derive `agent_id = lowercase hex sha256(ed25519_pub_key)` (64 chars).
   - Write `~/.claude/memory/identity/manifest.json` mirroring Codex's manifest: `{"agent_id": "...", "agent_alias": "claude", "created_at": <unix_ms>, "key_format": "ed25519-base64url"}`.
   - First-run behavior: generate if missing; reuse if present; refuse to start if either file exists but doesn't parse.
   - Legacy fallback: if v0.3 Phase 1 lands first and creates these files via its own bootstrap, this step becomes a no-op. The two bootstraps share the same paths and format intentionally.
   - Env override: `SC_IDENTITY_PATH` (default `~/.claude/memory/identity/`), `SC_AGENT_ALIAS` (default `"claude"`).
4. **Canonical envelope** — schema + canonicalization function for sig.
5. **Ed25519 sign + verify** — per §5.5. Phase 1 fails closed on any verification error.
6. **Replay cache** — per §5.8. SQLite or in-process LRU with TTL.
7. **JSON-RPC `SendMessage`** — request/response handling for 5 message types.
8. **`SendStreamingMessage` over SSE** — for long-running tasks (second_opinion deep mode, handoff with multiple sub-acks).
9. **`acs_subscribe` SSE endpoint** — recipient subscribes by `agent_id`; ACS pushes pending messages.
10. **Append-only event log** — SQLite or LanceDB table (separate from memory). Indexed by `(conversation_id, message_id, recipient_agent_id, state)`.
11. **MCP side-effect bridge with explicit failure semantics** — `decision.recorded` + accepted `handoff.state` write to recipient's memory MCP via existing `memory_save` tool. Delivery semantics:
    - Ack means "delivered to ACS event log + signature verified," NOT "durably persisted in memory yet."
    - Memory write retry policy: 5 attempts with exponential backoff (1s, 2s, 4s, 8s, 16s).
    - After 5 failed retries: mark `durable_state="failed"` in the event log entry, emit a compensating `acs.durable_write_failed` audit-log event (separate from ACS event log — written to `~/.acs/audit.jsonl`).
    - User notification: ACS writes a critical-priority memory entry of `type="blocker"` into the SENDING agent's memory MCP (NOT the failing recipient's), with content `"ACS durable write failed: {message_id} after 5 retries. Audit log: {audit_log_id}"`. This surfaces the failure in the sender's next memory_load_session.
    - `acs_get_conversation` includes `durable_state` per message — callers see failed-durable-state messages explicitly.
    - Future `acs_ack` responses for the same `message_id` continue to return the original ack (idempotent — replay protection per §5.8). Subsequent send attempts of the same content require a NEW `message_id` and start the retry counter fresh.
12. **Escalation function** — implement per §5.4. Integration: called from agent-side code when receiving any second_opinion.response, review.findings, or handoff.state.
13. **Phase 1 acceptance test battery** — 10 tests minimum (see §8 below).

### Phase 2 — Hygiene + calibration (P1)

14. **Conversation lifecycle** — open/close/timeout. Hard timeout = 7 days. Soft timeout per protocol mode.
15. **BF calibration experiment** — §6.1.
16. **Rate limiting** — per-sender, per-conversation.
17. **Deadlock detection** — workflow state machine analysis (Lens 4).
18. **Vector clocks** — for causality beyond simple `parent_message_id`.
19. **Agent Card JWS signing** — sign Agent Card itself per [doc: A2A §8.4].
20. **Bridge → ACS event log telemetry** — measure delivery latency, ack lag, drop rate.

### Phase 3 — Security + extensions (P2)

21. **Key rotation** — `key_id` field already in Phase 1 envelope; rotation procedure documented.
22. **Push notification webhooks** — A2A `pushNotifications: true`.
23. **gRPC binding** — for high-throughput agent pairs.
24. **Cross-machine deployment** — HTTPS, mTLS, real Agent Card discovery.
25. **Additional message types** (NON-NORMATIVE FUTURE EXAMPLES — these are illustrative, not committed; new message types require a separate vocabulary approval via the same dual-counsel workflow that produced the 5 starters). Examples: `task_status.update`, `negotiation.propose`.

---

## 8. Phase 1 acceptance test battery (10 tests, all must pass)

| # | Test | Setup | Expected |
|---|------|-------|----------|
| T1 | Agent Card fetch | SC + ACS running | `GET /.well-known/agent-card.json` returns valid Agent Card with `extensions.acs.agent_id` matching SC's identity |
| T2 | SendMessage roundtrip | Both agents up, both Agent Cards advertised | `second_opinion.request` from Codex → SC → `second_opinion.response` returned within deadline; both signed; sig verified on receipt |
| T3 | Ed25519 sig fail-closed | Tamper with one byte of payload after signing | Recipient returns `SIGNATURE_INVALID`, message NOT processed, no memory write |
| T4 | Replay rejection (duplicate body) | Send same `message_id` with mismatched body | Recipient returns `MESSAGE_ID_BODY_MISMATCH`, logged in event log |
| T5 | Replay idempotency (exact duplicate) | Send identical message twice | Second send returns the same ack as the first; no double-processing; memory write count = 1 |
| T6 | TTL expiry | Send message with `ttl_ms=1000`, wait 2s, deliver | Recipient returns `MESSAGE_EXPIRED`, no processing |
| T7 | Recipient-down delivery | Send to a recipient that is offline; recipient comes online and subscribes | Pending message delivered on subscribe; ack returned; event log shows delivery state transitions |
| T8 | Escalation function — clear auto-resolve | `bayes_factor=15, risk=0.2, reversibility=reversible` | Returns `{decision: "auto_resolve", rationale: "..."}` |
| T9 | Escalation function — irreversible escalates regardless | `bayes_factor=100, risk=0.1, reversibility=irreversible` | Returns `{decision: "escalate_to_user", rationale: "Irreversible..."}` |
| T10 | `decision.recorded` writes to memory | Send `decision.recorded` from Codex to SC | Ack returned; SC's memory MCP receives a `memory_save` with the decision content; memory row shows `agent_id=codex`, `visibility=shared`, `type="decision"` |

**All 10 must pass** before Phase 1 is declaration-complete.

---

## 9. Source manifest

### 9.1 SC source citations

| File | Lines | What it shows |
|------|-------|---------------|
| `~/.claude/mcp-servers/superclaude-memory/src/http-server.ts` | 18-19 | Streamable HTTP transport import — reusable for ACS HTTP layer |
| | 365-405 | `/mcp` routing pattern — adaptable to `/rpc` for ACS JSON-RPC |
| `~/.claude/mcp-servers/superclaude-memory/src/notify-handler.ts` | 22, 25 | Inbound payload carries `agent_id` — but next lines discard it |
| | 50-65 | In-memory FIFO queue — Phase 1 ACS event log replaces this with append-only persistence |
| | 118-126 | Save drops `agent_id`, hardcodes `visibility="shared"` — the bug class ACS must NOT extend |
| | 140-143 | Queue drains on next tool call — no durable delivery semantics |
| `~/.claude/mcp-servers/superclaude-memory/src/pmm-bridge.ts` | 65-76 | `available=false` degradation pattern — adopted for ACS recipient-down handling |
| | 113-150 | Empty-array fallback when unavailable |
| `~/.claude/mcp-servers/superclaude-memory/src/schema.ts` | 84-123 | Current MemoryRow shape — ACS envelope is intentionally NOT a MemoryRow |

### 9.2 Project cross-references

- [spec: 2026-05-26-codex-memory-system-design.md §5.3] — direct LanceDB cross-read as free communication for memory (the transport layer ACS is independent of)
- [spec: 2026-05-26-codex-memory-system-design.md §6.2] — concurrency analysis (Codex read-only from SC, no cross-writes); ACS preserves this
- [spec: 2026-05-26-sc-memory-v0.3-upgrade-spec.md §Phase 1] — ed25519 identity model (ACS reuses the same `agent_id` bytes)
- [research/codex-counsel-D-output.md] — verbatim counsel output (22,385 chars)

### 9.3 A2A v1.0 spec citations

- [doc: https://a2a-protocol.org/latest/specification/]
- [doc: https://github.com/a2aproject/A2A/blob/main/docs/specification.md]
- §3.3.1 — Send-message operations use `messageId` for duplicate detection (basis for §5.8 replay protection)
- §3.3.3 — Async model: server returns Task or Message immediately, client tracks via polling/streaming/push
- §4.4.1 — Agent Card fields (name, description, supportedInterfaces, capabilities, securitySchemes, etc.)
- §7.1-§7.4 — Authentication required on every incoming request
- §8.2, §14.3 — Well-known Agent Card URI: `/.well-known/agent-card.json`
- §8.4 — Agent Cards may be signed with JWS and canonicalized
- §9.1-§9.4 — JSON-RPC methods: SendMessage, SendStreamingMessage, GetTask, ListTasks, CancelTask, SubscribeToTask, etc.

### 9.4 MCP spec citation

- [doc: https://modelcontextprotocol.io/specification/2025-03-26/basic/index] — JSON-RPC 2.0 conformance; one-way notification semantics

### 9.5 MIT-12 chunk citations

- `mit12: book-08-chunk-0080 pp.274-278` — IGM property + linear value decomposition of common rewards (grounds Q3 reward structure)
- `mit12: book-09-chunk-0050 pp.205-208` — Free vs General communication complexity table (grounds Q6 architecture rejection of option c)
- `mit12: book-11-chunk-0053 pp.209-213` — Jeffreys scale of evidence (grounds Q4 escalation thresholds, Table 5.6)
- `mit12: book-10-chunk-0066 pp.199-202` — Embeddings/models have no ground truth without downstream task (grounds §6.1 BF construct validity)

Out-of-corpus flags: A2A v1.0 wire format details (vendor-fact, codex web_search), TypeScript-level escalation function implementation (engineering, not theory), Phase 1 deployment topology (operational).

### 9.6 Memory MCP entries

- `mem_a4af3f41` — 6 ACS principles + tech decisions (input to this spec)
- `mem_343df0ac` — Project state (updated after C; about to be updated after D)
- `mem_63263e0e` — v0.3 schema additions (identity bytes ACS reuses)
- `mem_0928b27c` — Construct-validity for cross-store cosine (lesson from C session, generalized to BF in §6.1)
- `mem_13ab8d10` — Codex CLI Windows gotchas (applied in this session)

---

_End of spec. Awaiting Step 6 codex strict-review verification._
