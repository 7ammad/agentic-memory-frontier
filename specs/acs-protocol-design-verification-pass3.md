# Codex Strict-Review Verification PASS 3 - Sub-Project D

_Final pass after applying pass-2 topology fix_
_Agent msgs lengths: [124, 210, 1973]_

---

# Topology consistency

| # | Section | Verdict | Evidence |
|---|---|---|---|
| 1 | §5.1 | PASS | Sample `supportedInterfaces` now uses `http://127.0.0.1:18801/rpc` and `http://127.0.0.1:18801/events`, both with `"via": "acs-service"` and `"routing": "by_recipient_agent_id"` at lines 107-109. |
| 2 | §5.6 | PASS | “Agent Card advertised URLs” states each agent’s card lists the ACS service endpoint, routing is by `recipient_agent_id`, both SC and Codex list the same `:18801` URLs, and distinction is `extensions.acs.agent_id` at line 366. |
| 3 | §5.6 / §5.6.1 | PASS | “Where each Agent Card is served” says SC/Codex serve static cards at their own `:port/.well-known/agent-card.json`, while subsequent A2A messages go through ACS `:18801/rpc` at line 368. §5.6.1 reinforces A2A traffic via `:18801/rpc` and MCP as internal memory access at lines 374-376. |
| 4 | §7 Phase 1 item 2 | PASS | Item 2 still says both SC and Codex publish their own Agent Card on their respective ports, while ACS publishes a separate relay card at `:18801`, line 432. This matches the static-description topology. |
| 5 | §5.6 port table | PASS for `/rpc` placement | Port table lists SC `:18800` paths as `/mcp`, `/notify`; ACS `:18801` as `/rpc`, `/.well-known/agent-card.json`, `/events`; Codex `:18802` as `/mcp`, lines 358-362. No `/rpc` appears on SC or Codex. |

# Any new issues

One minor stale topology/table reference remains:

The new relay topology says each agent’s own MCP HTTP layer serves `:port/.well-known/agent-card.json` for static Agent Cards, but the local topology diagram and port table do not show `/.well-known/agent-card.json` on SC `:18800` or Codex `:18802`. The diagram only shows `:18801/.well-known` at lines 337-343, and the port table only lists `/.well-known/agent-card.json` on ACS at lines 358-362. That is not the old `/rpc` contradiction, but it is a fresh documentation inconsistency with line 368 and §7 item 2.

# Readiness verdict: PATCH-FIRST