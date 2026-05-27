# Codex Strict-Review Verification - Sub-Project D (ACS Protocol Design)

_Source: codex exec 0.128.0 strict-review, with web_search_cached_
_Agent msgs lengths: [215, 215, 166, 11047]_

---

# Check 1 Coverage — Per Item

Note: the handoff compresses `mem_a4af3f41` into one constraints paragraph rather than enumerating all six principles verbatim. I split the six principles using the handoff plus the deliverable’s own references to principle 1, 3, and 6.

1. Decentralized ownership: each agent owns its memory; ACS is communication-only — **IN DELIVERABLE**  
   Covered in §2.3 and §5.6: ACS has separate event log/state and memory writes only as explicit side effects.

2. ACS messages must not be hidden inside memory rows — **IN DELIVERABLE**  
   Covered strongly in §1, §5.6, and rejected alternatives. This also matches C §5.3.

3. Sparse graph / human-centered topology — **IN DELIVERABLE**  
   Covered in §5.3 table: “2 agents + human at center (sparse star graph per principle 3).” Thin, but present.

4. Free communication, not general communication through shared state — **IN DELIVERABLE**  
   Covered in §2.2, §5.3, §5.6, and C cross-reference. No contradiction with C §5.3 or §6.2.

5. Explicit mode-specific reward structure — **IN DELIVERABLE**  
   Covered in §1, §5.2 envelope, §5.3. Every message carries `protocol_mode` and `reward_contract`.

6. Bounded rationality / human-in-loop escalation — **IN DELIVERABLE**, but see Check 2 drift  
   Covered in §5.4 and §6.1. The concept is present, but the exact escalation thresholds drift.

Starter message types:

1. `second_opinion.request` / `second_opinion.response` — **IN DELIVERABLE**
2. `review.findings` — **IN DELIVERABLE**
3. `handoff.state` / `handoff.accepted` — **IN DELIVERABLE**
4. `clarification.request` / `clarification.response` — **IN DELIVERABLE**
5. `decision.recorded` — **IN DELIVERABLE**

Additional message types:

- `ack` — **IN DELIVERABLE**, not scope creep; required by the ack semantics.
- Phase 3 examples `task_status.update`, `negotiation.propose` — **SCOPE CREEP**, but safely deferred as “beyond the 5 starters.”

Locked tech decisions:

1. A2A outer + MCP inner — **IN DELIVERABLE**  
   A2A outer is strong. MCP inner is partially specified as memory side-effect bridge, but still needs clarification in Check 4.

2. Identity = `sha256(ed25519_pub)` — **IN DELIVERABLE**  
   Covered in §1, §2.2, §5.2, §5.5, §7.

3. Jeffreys scale + Codex risk-weighted escalation — **IN DELIVERABLE**, but threshold drift exists  
   Covered in §1 and §5.4; exactness fails in Check 2.

# Check 2 Internal Consistency — Contradictions

1. §5.6 dedicated ACS service vs §1 executive verdict — **none**  
   They match. §1 says “Dedicated ACS service” with append-only event log; §5.6 repeats option (a).

2. §5.4 escalation function vs locked constraint — **FAIL / drift**  
   Constraint to check: `risk < 0.3` auto-resolve, `risk >= 0.7` escalate, irreversible/security always escalate.  
   §5.4 adds an extra auto-resolve branch: `bayes_factor >= 30 && risk < 0.5`. That allows auto-resolution at `risk >= 0.3`, which contradicts the strict threshold wording. Patch: remove that branch or explicitly get approval that “very strong BF + moderate-low risk” is allowed.

3. §5.2 envelope vs §5.8 replay protection fields — **PASS**  
   §5.2 includes `nonce`, `message_id`, `timestamp`, `ttl_ms`, `body_hash`; §5.8 requires the same five.

4. §7 backlog phase ordering — **mostly PASS**  
   Phase 1 has skeleton, Agent Card, SC key bootstrap, canonical envelope, signing, replay cache, SendMessage/SSE, event log, side-effect bridge, escalation, tests. Phase 2 hygiene/calibration. Phase 3 security/extensions.  
   Minor issue: Phase 1 item 11 says memory write retries with backoff but does not define terminal failure state. That is not ordering failure, but it is implementation underspecification.

# Check 3 Grounding — Spot-Checks

1. `notify-handler.ts:118-126` identity drop / hardcoded visibility — **PASS**  
   Actual source calls `store.save({ content, type, scope, priority, topics, source_type: "bridge", visibility: "shared", task_data: payload.task_data as any })`. It does not pass `payload.agent_id`. This supports the spec’s claim.

2. `notify-handler.ts:50-65, 140-143` in-memory FIFO queue — **PASS**  
   Actual source has `const notificationQueue: PendingNotification[] = []`, `drainNotifications()` clears via `splice(0)`, and when full it calls `notificationQueue.shift()` before `push`. This supports “in-memory capped FIFO, drains on next tool call.”

3. `http-server.ts:18-19` Streamable HTTP claim — **PASS**  
   Actual source imports `McpServer` and `StreamableHTTPServerTransport` from the MCP SDK. This supports the reusable transport-pattern claim.

4. `http-server.ts:365-405` `/mcp` routing/session tracking — **PASS**  
   Actual source routes `url.pathname === "/mcp"`, reuses existing `mcp-session-id`, creates `new StreamableHTTPServerTransport`, connects server, handles request, then stores `transport.sessionId` in `transports`.

5. `pmm-bridge.ts:65-76, 113-150` degradation pattern — **PASS**  
   Actual source has `public available = false`, catches init failure by setting `available = false`, and search/session methods return `[]` when unavailable. Supports the spec’s degradation pattern.

6. `schema.ts:84-123` ACS envelope not MemoryRow — **PASS**  
   Actual `MemoryRow` contains memory fields like `id`, `content`, `vector`, `type`, `scope`, `visibility`, `created_at`, `task_data`; it has no ACS envelope fields like `message_id`, `recipient_agent_id`, `protocol_mode`, `nonce`, or `sig`.

7. A2A Agent Card location — **PASS**  
   A2A spec says servers must make an Agent Card available, and lists the well-known URI `https://{server_domain}/.well-known/agent-card.json`; IANA section says `.well-known/agent-card.json` must return an `AgentCard`. Source: https://a2a-protocol.org/latest/specification/

8. A2A JSON-RPC methods — **PASS with one naming caveat**  
   A2A spec lists JSON-RPC over HTTP(S), SSE for streaming, and core methods: `SendMessage`, `SendStreamingMessage`, `GetTask`, `ListTasks`, `CancelTask`, `SubscribeToTask`, push notification config methods, and `GetExtendedAgentCard`.  
   Caveat: current spec line cites “push notification config” generally; exact method names are `CreateTaskPushNotificationConfig`, `GetTaskPushNotificationConfig`, `ListTaskPushNotificationConfigs`, `DeleteTaskPushNotificationConfig`. Source: https://a2a-protocol.org/latest/specification/

# Check 4 Missing Artifacts

1. Canonicalization rules for message signatures — **MISSING**  
   The spec says “canonical envelope without `sig`” but does not define exact bytes, field order, omitted/null handling, number/string normalization, Unicode normalization, or whether to use RFC 8785/JCS like A2A Agent Card signing.

2. SC ed25519 keypair bootstrap — **MISSING**  
   Phase 1 item 3 says co-generate with Codex memory or fast-path SC v0.3 identity, but not the exact procedure: file path, key format, permissions, env/config wiring, migration from legacy identity, regeneration rules, or failure behavior.

3. MCP side-effect bridge terminal failure — **MISSING**  
   Phase 1 item 11 says ack succeeds and `memory_save` retries with backoff. It does not define what happens after N retries: mark `durable_state=failed`, emit compensating event, notify user, re-open delivery, poison queue, or block future acks.

4. Port/path specificity — **PARTIAL**  
   §5.6 gives ports: SC `:18800/mcp`, ACS `:18801/rpc`, Codex `:18802/mcp`, plus `:18801/events`. This is concrete. Missing: whether these override C defaults, env var names, Windows bind host, collision behavior, and whether Agent Card advertises `/rpc` only or `/events` too.

5. “MCP inner protocol” meaning — **MISSING / ambiguous**  
   The spec rejects exposing only `/mcp` as ACS and says MCP is inner-tool layer. But implementation mostly uses MCP for memory side effects (`memory_save`). It must state whether ACS can invoke arbitrary MCP tools as part of conversations, or only permits MCP-tool calls inside agent workflows and uses MCP directly for durable side effects.

6. ACS version compatibility — **MISSING**  
   A2A has version headers and migration appendix, but ACS-specific compatibility is not specified: what happens when SC supports ACS `0.1.0` and Codex supports `0.2.0`, how Agent Card advertises supported ACS versions, and whether incompatible message types fail closed or degrade.

7. Bayes factor computation — **MISSING but acknowledged as open**  
   §5.4/§6.1 admits the operational definition is open and defers calibration. That is acceptable for Phase 2, but Phase 1 should not rely on BF-based auto-resolution unless the input source is defined.

8. Agent Card custom security scheme shape — **MISSING / likely non-standard**  
   The sample uses `"type": "custom"` under `securitySchemes`. Need verify A2A/OpenAPI-compatible schema accepts that exact shape or move ACS signature declaration into `extensions.acs`.

# Patches Needed Ordered By Importance

1. **Mechanical:** Remove or revise the `bayes_factor >= 30 && risk < 0.5` auto-resolve branch in §5.4 to match the locked threshold exactly.

2. **Mechanical:** Add a “Signature canonicalization” subsection defining exact canonical bytes. Recommended: RFC 8785/JCS over envelope with `sig` omitted, required fields present, no undefined fields, timestamps ISO string, `body_hash = sha256(JCS(payload))`, signature over `JCS(envelope_without_sig)`.

3. **Judgment-call:** Define SC key bootstrap: storage path, key encoding, generation command/API, config/env names, id derivation, permissions, first-run behavior, and legacy fallback.

4. **Judgment-call:** Define MCP side-effect bridge failure semantics after retries: max attempts, backoff schedule, terminal state, user-visible alert, event log fields, and whether ack means “delivered” only or “durably persisted.”

5. **Mechanical:** Add ACS version negotiation and compatibility rules to Agent Card `extensions.acs`: supported versions, min/max accepted, failure code, and backward-compatible decoding policy.

6. **Mechanical:** Clarify MCP inner boundary: “ACS invokes MCP only for durable memory side effects in Phase 1” vs “ACS can broker MCP tool calls.” Pick one and make acceptance tests match.

7. **Mechanical:** Tighten port/path config: env var names, defaults, host binding, collision handling, Agent Card advertised URLs, and how `:18802/mcp` aligns with sub-project C defaults.

8. **Mechanical:** Replace generic “push notification config methods” cite text with exact A2A method names, or explicitly say “push notification configuration methods family.”

9. **Judgment-call:** Either remove Phase 3 extra message type examples or label them as non-normative future examples requiring a separate vocabulary approval.

# Readiness Verdict: PATCH-FIRST

The design is directionally coherent and mostly grounded. It is not ready because the escalation function violates the strict threshold constraint, and Phase 1 still lacks implementable signature canonicalization, SC key bootstrap, durable side-effect failure semantics, and ACS version compatibility.