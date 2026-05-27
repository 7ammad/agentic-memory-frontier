# Per-spec-item

| # | Item | IMPLEMENTED / DEFERRED / MISSING | Evidence |
|---|---|---|---|
| 14 | Conversation lifecycle | IMPLEMENTED, with one spec gap | `conversations.ts` uses `conversations = new Map` and tracks `opened_at`, `last_activity_at`, `participants`, `protocol_mode`, `closed_at`, `close_reason` at lines 22-31 and 49-63. Hard idle timeout is `7 * 86_400_000` at line 18, applied in `expireIdle` lines 79-82, started from `index.ts` line 473. Endpoints exist in `index.ts`: `GET /conversations` lines 322-324, `GET /conversations/{id}` lines 326-331, `POST /conversations/{id}/close` lines 333-344. Gap: spec says “soft timeout per protocol mode”; I did not see mode-specific soft timeout logic. |
| 15 | BF calibration experiment | DEFERRED | Spec item 15 says experiment artifact, not server code. No BF calibration implementation in the three implementation files, which matches the requested deferral. |
| 16 | Rate limiting | MISSING for full spec, partially implemented | Per-sender token bucket is implemented: defaults `ACS_RATE_LIMIT_BURST || 60` and `ACS_RATE_LIMIT_PER_SEC || 1` in `rate-limit.ts` lines 11-12; bucket key is only `sender_agent_id` in `checkRateLimit(sender_agent_id)` line 36. `SendMessage` rejects with `RATE_LIMIT_EXCEEDED` in `index.ts` lines 98-106. Gap: spec item 16 requires per-sender, per-conversation; no conversation-keyed bucket is present. |
| 17 | Deadlock detection | DEFERRED | No workflow state-machine/deadlock detector in implementation files. Matches requested deferral. |
| 18 | Vector clocks | DEFERRED | No vector clock implementation in implementation files. Matches requested deferral. |
| 19 | Agent Card JWS signing | DEFERRED | `/.well-known/agent-card.json` returns an unsigned relay card in `index.ts` lines 349-386. No JWS signing visible. Matches requested deferral. |
| 20 | Bridge → ACS event log telemetry | MISSING | Event-log entries exist for delivery/ack/durable state in `index.ts` lines 120-124, 239-243, and 254-265. But spec item 20 asks to measure delivery latency, ack lag, and drop rate. I did not see those telemetry metrics or `/health` exposure for them. |

# Confirmed

- Per-sender token bucket defaults: yes, `ACS_RATE_LIMIT_BURST=60`, `ACS_RATE_LIMIT_PER_SEC=1` defaults in `rate-limit.ts` lines 11-12.
- Conversation Map fields: yes, `opened_at`, `last_activity_at`, `participants`, `protocol_mode` in `conversations.ts` lines 22-31 and populated at lines 49-63.
- Conversation idle timeout 7d via `startExpireTimer`: yes, `IDLE_TIMEOUT_MS` line 18, `startExpireTimer` lines 118-122, called from `index.ts` line 473.
- Conversation endpoints: yes, `GET /conversations`, `GET /conversations/{id}`, `POST /conversations/{id}/close` in `index.ts` lines 322-344.
- SendMessage rate-limit rejection: yes, `RATE_LIMIT_EXCEEDED` in `index.ts` lines 98-106.
- `mode_mismatch` advisory, not rejected: yes, `recordMessage` returns mismatch in `conversations.ts` lines 63-64; `index.ts` logs advisory and continues at lines 111-124.
- `/health` reports `rate_limit_buckets`, `conversations_total`, `conversations_active`: yes, `index.ts` lines 314-316.

# Patches needed

1. Add per-conversation rate limiting or a combined sender+conversation bucket path to satisfy item 16 exactly.
2. Add soft timeout per `protocol_mode` or explicitly document the Phase 2 implementation as hard-timeout-only.
3. Add telemetry metrics for item 20: delivery latency, ack lag, drop rate, and expose them through health or a telemetry endpoint.

# Readiness verdict: PATCH-FIRST