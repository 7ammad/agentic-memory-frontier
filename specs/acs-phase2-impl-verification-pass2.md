# Codex Strict-Review — D Phase 2 (conversation lifecycle + rate limit + bridge event telemetry)

_Pass 2 reconstructed after the original codex stream errored mid-call producing an 8-byte file._
_Pass-3 and pass-4 transcripts are the authoritative verdicts; this file documents the patch chain._

---

## Pass-1 verdict (PATCH-FIRST)

See `acs-phase2-impl-verification.md`. Three patches required:

1. Add per-conversation rate limiting in addition to per-sender (spec item 16).
2. Add soft timeout per protocol_mode (spec item 14).
3. Add bridge event-log telemetry: delivery_latency_ms, ack_lag_ms, drop_rate (spec item 20).

## Pass-2 (this file — reconstructed)

Pass-2 codex stream errored mid-call: `No such host is known. (os error 11001)` reconnect failure. The raw `.json` capture was truncated to 8 bytes. The retry that completed reported:

- ✅ Two-tier rate limit (sender + conversation) wired into SendMessage. `RateLimitResult` exposes `rejected_by` ∈ `{sender, conversation}`. `rate-limit.ts` keeps two `Map`s of buckets, both must allow before tokens consume.
- ✅ `SOFT_TIMEOUT_BY_MODE` table per protocol_mode: `second_opinion=30min`, `red_team=4h`, `handoff=24h`, `clarification=10min`, `decision_log=0`. `soft_timeout_expired` boolean surfaces in `ConversationSummary`.
- ✅ `bridgeEventTelemetry()` returns total_events, dropped_events, drop_rate, delivery_latency_ms p50/p95/p99, ack_lag_ms p50/p95/p99.
- ✅ `/health` surfaces `rate_limit_buckets`, `conversations_total`, `conversations_active`, `conversations_soft_timed_out`, `bridge_event_telemetry`.

Remaining issues flagged at end of pass-2:

- `RATE_LIMIT_EXCEEDED` error stuffed `rejected_by` in `reason` string instead of as a structured field.
- 2 of 7 `logEvent()` calls in `index.ts` still didn't pass `env.timestamp` (lines 156 + 178 — signature-fail branch and replay-body-hash-mismatch branch).

## Pass-3 verdict (PATCH-FIRST)

Two patches required: structured `rejected_by`+`retry_after_ms` field on the RATE_LIMIT_EXCEEDED error; pass `env.timestamp` to lines 156 + 178 `logEvent` calls.

## Pass-4 verdict (final — READY)

> ```
> | Line | Has env.timestamp? |
> |---:|---|
> | 116 | Yes |
> | 135 | Yes |
> | 156 | Yes |
> | 178 | Yes |
> | 207 | Yes |
> | 235 | Yes |
> | 257 | Yes |
> ```
>
> **Readiness verdict: READY**

All 7 `logEvent` call sites pass `env.timestamp` so `delivery_latency_ms` histogram populates from real send-to-receive deltas. RATE_LIMIT_EXCEEDED error exposes structured `rejected_by` + `retry_after_ms` fields.

D Phase 2 verified READY after 4 codex strict-review passes.

## Live runtime evidence (probed 2026-05-27)

```bash
$ curl -s http://127.0.0.1:18801/health
{
  "status":"ok",
  "uptime":44.4,
  "registered_agents":[
    {"alias":"claude","agent_id":"b7502fd1fe148218c38f216b795fd39335db532ebb674a367c635d4a770fdfb0","has_pub_key":true,"last_error":null},
    {"alias":"codex","agent_id":"5a97dd00baaf8b51aeab46d91f5a16818159328d62cb5ad9382dec0f36568a59","has_pub_key":true,"last_error":null}
  ],
  "rate_limit_buckets":{"senders":{},"conversations":{}},
  "conversations_total":0,
  "conversations_active":0,
  "conversations_soft_timed_out":0,
  "bridge_event_telemetry":{"total_events":0,"dropped_events":0,"drop_rate":0,…}
}
```

Both peer Agent Cards auto-fetched on startup; both ed25519 pub keys loaded into registry. Relay ready to accept signed envelopes.
