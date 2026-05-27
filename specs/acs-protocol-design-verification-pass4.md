# Codex Strict-Review Verification PASS 4 - Sub-Project D

_Final pass after topology table+diagram patch_
_Agent msgs lengths: [98, 116, 750]_

---

# Final check
| # | Item | Verdict | Evidence |
|---|---|---|---|
| 1 | Port table lists Agent Card on SC `:18800` and Codex `:18802` | READY | SC row: `/mcp`, `/notify`, `/.well-known/agent-card.json`; Codex row: `/mcp`, `/.well-known/agent-card.json`; ACS row also includes it. |
| 2 | Topology diagram shows Agent Card on all three services | READY | Diagram shows `:18800/.well-known/ agent-card.json`, `:18801/.well-known/ agent-card.json`, and `:18802/.well-known/ agent-card.json`. |
| 3 | No new contradiction introduced | READY | Prose now aligns with table and diagram: peer Agent Cards are served on each agent’s MCP HTTP layer, while A2A traffic still routes through ACS `:18801/rpc` by `recipient_agent_id`. |

# Readiness verdict: READY