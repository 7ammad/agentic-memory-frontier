# Codex D Impl Verification

_Msg lengths: [250, 155, 207, 206, 195, 9117]_

---

# Check 1 Coverage

| Item | Verdict | Evidence |
|---|---:|---|
| ACS service skeleton + HTTP/SSE at `:18801` | PARTIAL | [index.ts](C:/Users/7amma/.acs/server/src/index.ts) uses `node:http`, default `ACS_SERVICE_PORT || 18801`, `/rpc`, `/events`, `/health`. It is not using an actual `StreamableHTTPServerTransport`, but does implement HTTP + SSE shape. |
| Agent Card generation + serving at `/.well-known/agent-card.json` | PARTIAL | [index.ts](C:/Users/7amma/.acs/server/src/index.ts) serves the relay card. It does not include relay `extensions.acs.agent_id` / `ed25519_pub_key`, and listed code does not implement SC/Codex peer Agent Card serving required by spec §7 item 2. |
| Canonical envelope Zod schema | YES | [envelope.ts](C:/Users/7amma/.acs/server/src/envelope.ts) defines `EnvelopeSchema`, message types, protocol modes, `sig`, `body_hash`, `nonce`, `ttl_ms`, etc. |
| Ed25519 sign + verify with RFC 8785 JCS | PARTIAL | [signing.ts](C:/Users/7amma/.acs/server/src/signing.ts) uses `canonicalize` and Ed25519. But [index.ts](C:/Users/7amma/.acs/server/src/index.ts) treats relay verification as advisory and does not fail closed on invalid or unknown sender signatures. |
| Replay cache in-memory Map with TTL | YES | [replay-cache.ts](C:/Users/7amma/.acs/server/src/replay-cache.ts) has Map cache, expiry, `checkReplay`, `recordOutcome`, eviction timer. |
| JSON-RPC `SendMessage` handler | YES | [index.ts](C:/Users/7amma/.acs/server/src/index.ts) handles `/rpc` method `SendMessage`. |
| `SendStreamingMessage` over SSE | NO | [index.ts](C:/Users/7amma/.acs/server/src/index.ts) maps `SendStreamingMessage` to the same JSON response path as `SendMessage`; it does not stream the RPC response over SSE. |
| `/events` SSE subscription endpoint | YES | [index.ts](C:/Users/7amma/.acs/server/src/index.ts) implements `GET /events?agent_id=...` with SSE headers, hello event, queue drain, subscription registration, ping. |
| Append-only event log | YES | [event-log.ts](C:/Users/7amma/.acs/server/src/event-log.ts) appends JSONL entries under `~/.acs/data/event-log/events.jsonl`. |
| MCP side-effect bridge for `decision.recorded` + `handoff.state`, 5 retries exp backoff | PARTIAL | [mcp-side-effect.ts](C:/Users/7amma/.acs/server/src/mcp-side-effect.ts) targets those two types and has `RETRY_DELAYS_MS = [1000,2000,4000,8000,16000]`, but the loop performs 5 attempts with only 4 waits: `1s,2s,4s,8s`. It never waits `16s`, and it does not create the required sender-side critical blocker memory entry on terminal failure. |
| 5 message type handlers | PARTIAL | Message types are enumerated, but there are no per-type payload schemas or handlers. [index.ts](C:/Users/7amma/.acs/server/src/index.ts) mostly generic-passthroughs envelopes, with special side effects only for `decision.recorded` and `handoff.state`. |
| Escalation function with Jeffreys x risk thresholds | YES | [escalation.ts](C:/Users/7amma/.acs/server/src/escalation.ts) matches: auto-resolve only `risk < 0.3 && BF >= 10`; escalate on irreversible/security-sensitive, money/legal, credentials, `risk >= 0.7`, `BF < 3`; middle zone escalates. |
| 10-test acceptance battery | NO | [d-phase1-acceptance.test.ts](C:/Users/7amma/.acs/server/src/tests/d-phase1-acceptance.test.ts) covers unit subset. [d-phase1-integration.test.ts](C:/Users/7amma/.acs/server/src/tests/d-phase1-integration.test.ts) explicitly does not exercise real T2 roundtrip, real T7 queued delivery, or T10 memory write. |

# Check 2 Internal Consistency

- `signing.ts` says ACS relay performs only advisory verification and recipient-side verification is authoritative. The spec says Phase 1 fails closed on any verification error. `index.ts` follows advisory behavior, so implementation contradicts spec security posture.
- `mcp-side-effect.ts` comment says “5 retries with exponential backoff: 1s, 2s, 4s, 8s, 16s,” but the loop does 5 total attempts and waits only before attempts 2-5, so observed waits are `1s,2s,4s,8s`.
- `client/src/index.ts` header says it supports “subscribe to /events SSE,” but the exported client only has `sendEnvelopeToAcs`, `pollInbox`, `verifyIncoming`, and `getAcsBaseUrl`; no SSE subscription helper exists.
- Integration test comments claim T2/T7 constraints cannot be exercised without live SC/Codex, then tests weaker substitutes. Passing integration tests therefore do not prove the spec acceptance items they are mapped to.
- `mcp-side-effect.ts` uses `any` in payload parsing and JSON parsing paths, conflicting with the provided AGENTS rule “No `any` in TypeScript.”

# Check 3 Grounding

1. Signature canonicalization: implementation signs `JCS(envelope_without_sig)`, not payload-omitted. `signing.ts` calls `canonicalEnvelopeBytes(envelopeWithoutSig)` and `verifyEnvelopeSignature` reconstructs unsigned envelope by removing `sig`. Payload remains included in the signed envelope; `body_hash` is separately `sha256(JCS(payload))`.

2. Replay cache behavior: `replay-cache.ts` rejects duplicate `message_id` with different `body_hash` as `body_hash_mismatch`, returns `cached_outcome` for exact duplicates, and deletes expired entries before treating them fresh.

3. Escalation thresholds: `escalation.ts` matches §5.4 thresholds exactly for the core decision rule: hard escalation first, then auto-resolve only at `risk < 0.3 && bayes_factor >= 10`, then `risk >= 0.7 || bayes_factor < 3`, then middle-zone escalation.

4. MCP retry backoff: `mcp-side-effect.ts` declares `[1000, 2000, 4000, 8000, 16000]`, but loop condition `i < RETRY_DELAYS_MS.length` plus `setTimeout(RETRY_DELAYS_MS[i - 1])` means the 16s delay is never used. This fails the requested spot-check claim.

5. `/events` SSE drains queue on connect: `index.ts` writes SSE headers, emits `event: subscribed`, calls `drain(agent_id, 100)`, writes each pending envelope to the stream, then registers the subscription.

6. Relay verification fail-closed: `index.ts` computes `sigState = advisory_pass/advisory_fail/skipped`, logs that state, but does not reject `advisory_fail` or `skipped`. That is a security gap against the spec’s “fails closed” language.

7. Tests do not prove T10: `d-phase1-integration.test.ts` contains no live SC memory MCP assertion and no `decision.recorded` memory-save verification. The only side-effect code path evidence is implementation-level, not acceptance-level.

# Check 4 Missing Artifacts

- Real `SendStreamingMessage` SSE response implementation.
- Fail-closed relay verification for invalid sender signature, invalid body hash, and unknown/unloaded sender public key, if relay is intended to enforce Phase 1.
- SC/Codex peer Agent Card serving artifacts, or evidence files for them. Listed code only serves the ACS relay card.
- Full Agent Card security fields on relay card: `securitySchemes`, `securityRequirements`, `extensions.acs.agent_id`, `extensions.acs.ed25519_pub_key`.
- Per-message payload schemas/validators for the starter message families.
- Real acceptance coverage for T2, T7, and T10.
- Sender-side blocker notification after terminal MCP side-effect failure.
- `acs_get_conversation` / conversation query surface with `durable_state`, required by §7 item 11.
- Durable replay/idempotency across restart, if the event log is expected to replay decisions safely. Current replay cache is process memory only.
- Shared client SSE receive helper, despite comments claiming it.

# Patches Needed

1. Make relay verification fail closed: if sender cannot be loaded, body hash fails, signature fails, or envelope unsupported, return a JSON-RPC error before delivery/queue/side-effect.
2. Fix `performSideEffect` retry semantics to match the spec exactly: either 5 retries after initial attempt with waits `1,2,4,8,16`, or change the spec/comment/tests. Current implementation does neither.
3. Add sender-side critical blocker write on terminal durable failure, or explicitly defer it and mark §7 item 11 incomplete.
4. Implement true `SendStreamingMessage` over SSE, separate from normal `SendMessage` JSON result.
5. Add peer Agent Card serving for SC/Codex or include the actual artifacts in the review set; relay card alone is not enough for §7 item 2.
6. Add per-message payload schemas or document Phase 1 as envelope-only passthrough and mark starter payload validation deferred.
7. Strengthen tests: real T2 signed roundtrip, T7 offline queue then SSE drain, T10 `decision.recorded` memory-save or durable failure path, invalid signature rejected by `/rpc`, and `SendStreamingMessage` SSE behavior.
8. Remove `any` usages from implementation files; use `unknown` plus type guards.
9. Add client SSE subscribe helper or remove the claim from client comments.
10. Add query/conversation API exposing event-log `durable_state`, or mark that spec item missing.

# Readiness Verdict: PATCH-FIRST

The skeleton is credible and several primitives are in place, but it is not READY. The biggest blockers are security fail-open relay verification, non-streaming `SendStreamingMessage`, incomplete side-effect failure semantics, and acceptance tests that pass without proving key spec requirements.