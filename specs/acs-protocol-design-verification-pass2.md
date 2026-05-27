# Codex Strict-Review Verification PASS 2 - Sub-Project D

_Re-verification after applying 9 pass-1 patches_
_Agent msgs lengths: [135, 249, 155, 4042]_

---

# Per-patch re-check

| # | Patch | Verdict | Evidence |
|---|---|---|---|
| 1 | Remove `BF>=30 && risk<0.5` auto-resolve branch | RESOLVED | §5.4 now has only `risk < 0.3 && bayes_factor >= 10` auto-resolve at lines 296-299. It escalates on `risk >= 0.7 || bayes_factor < 3` at lines 300-303. The rationale explicitly says “The only auto-resolve case is `risk<0.3 AND BF≥10`” and notes the prior `BF≥30 && risk<0.5` branch was removed at line 309. No stale “two cases” wording found. |
| 2 | Add signature canonicalization subsection with RFC 8785/JCS exact bytes | RESOLVED | §5.2.1 exists at line 184. It defines `Ed25519_sign(privkey, JCS(envelope_without_sig))`, RFC 8785/JCS, omission of `sig`, lexicographic key ordering, required fields, null/undefined behavior, timestamp format, and verification at lines 186-195. |
| 3 | SC ed25519 keypair bootstrap procedure | RESOLVED | §7 Phase 1 item 3 defines first-run generation, library options, private/public key paths, NTFS ACL, `agent_id` derivation, manifest format, parse-failure behavior, legacy fallback, and env overrides at lines 431-439. |
| 4 | MCP side-effect bridge terminal failure semantics | RESOLVED | §7 Phase 1 item 11 defines ack meaning, 5 retry attempts, exponential backoff, terminal `durable_state="failed"`, audit event, sender-side critical blocker notification, conversation visibility, and idempotent ack behavior at lines 447-453. |
| 5 | ACS version negotiation in Agent Card `extensions.acs` | RESOLVED | Agent Card now includes `supported_versions` and `min_compatible_version` at lines 127-130. Negotiation rules reject unsupported, too-old, too-new, and unsupported message types with explicit error codes at lines 145-151. |
| 6 | MCP inner boundary clarification | RESOLVED | §5.6.1 explicitly defines MCP as agent-to-own-memory, A2A as agent-to-agent, ACS MCP usage as durable side effects only, and says ACS does not broker arbitrary MCP tool calls in Phase 1 at lines 368-376. |
| 7 | Port/path config tighter | PARTIALLY RESOLVED | §5.6 now gives env names, defaults, bind hosts, collision behavior, and advertised URL rules at lines 358-366. §7 Phase 1 item 1 matches ACS default `:18801` and env `ACS_SERVICE_PORT` / `ACS_BIND_HOST` at line 429. However, this patch introduced a topology contradiction listed below. |
| 8 | Replace generic push notification config methods with exact A2A method names | RESOLVED | §5.1 now names `CreateTaskPushNotificationConfig`, `GetTaskPushNotificationConfig`, `ListTaskPushNotificationConfigs`, and `DeleteTaskPushNotificationConfig` at line 93. |
| 9 | Label Phase 3 extra message types as non-normative | RESOLVED | §7 Phase 3 item 25 labels the examples as “NON-NORMATIVE FUTURE EXAMPLES,” illustrative, not committed, and requiring separate vocabulary approval at line 473. |

# New contradictions introduced

1. **Agent Card / RPC port topology is now inconsistent.**  
   §5.1 sample Agent Card advertises `http://127.0.0.1:18800/rpc` for JSON-RPC/SSE at lines 107-109. §5.6 says SC memory MCP `:18800` only serves `/mcp` and `/notify`, while ACS service `:18801` serves `/rpc`, `/.well-known/agent-card.json`, and `/events` at lines 358-362. §5.6 then says each agent’s Agent Card lists its own `:port/rpc` and `:port/events` at line 366, and §7 item 2 says SC publishes its own Agent Card on `:18800` at line 430.  
   This leaves unclear whether SC is supposed to add `/rpc` and `/.well-known/agent-card.json` to the existing `:18800` service, or whether A2A RPC is only on ACS `:18801`.

# Remaining gaps

- **Patch #7 needs one clarifying edit**: choose one topology and make §5.1 sample Agent Card, §5.6 port table, §5.6 Agent Card URL paragraph, and §7 Phase 1 item 2 agree.
- The ACS port default itself is consistent: §5.6 uses `:18801` / `ACS_SERVICE_PORT` at line 361, and §7 Phase 1 item 1 repeats `:18801` / `ACS_SERVICE_PORT` at line 429.
- §5.2.1 properly states `body_hash = sha256_hex(JCS(payload))` and that it is computed before signing at line 193.

# Readiness verdict: PATCH-FIRST