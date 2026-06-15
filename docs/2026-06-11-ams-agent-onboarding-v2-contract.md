# AMS Agent Onboarding V2 Contract

Date: 2026-06-11
Last updated: 2026-06-12 - Claude Code and Cursor promoted from implied coding
agents to explicit onboarding roster entries.
Status: implemented and under verification
Parent product: AMS, after accepted AMS V2 Experience Enforcement Architecture

## Contract

AMS Agent Onboarding V2 is the post-V2 product layer that turns another agent
from an informal name into a governed AMS participant.

It is not the old parked "universal one-command memory API" idea and not the
deferred ACS relay. It is the full local onboarding path AMS needs now:
identity, capability contracts, AMS memory lane, runtime checks, trust policy,
shared-experience governance, persistence, CLI, MCP, docs, and tests.

## Current Roster

Current owner-approved onboarding targets:

- `codex` - primary coding, refactors, verification, and Codex harness work.
- `hermes` - desktop/runtime agent lane and local operator infrastructure.
- `hessa` - Hammad's local fast full computer operator and personal voice/computer agent.
- `claude-code-cursor` - Claude Code in Cursor IDE for architecture, review,
  planning, and Claude workflow execution.
- `cursor-agent` - Cursor composer for rapid IDE-native edits.
- `openclaw` - parked coordination/A2A lane; not used recently, but still counts.

`superbrembo` is not an active agent. It never became a working agent lane and
must be rejected by onboarding unless Hammad explicitly asks for historical
context.

## Acceptance Axes

| Axis | Required proof |
| --- | --- |
| Identity | Every onboarded agent has `agent_id`, display name, runtime surface, operational status, owner scope, and evidence ids. |
| Capability contracts | Every agent has at least one typed capability with inputs, outputs, permissions, risk level, verification commands, and evidence. |
| AMS memory lane | Every agent has startup brief, action brief, remember, and correction-capture commands that route through AMS. |
| Harness contracts | Every agent contract carries Codex Execution Contract, capability router, AMS startup/action brief, correction capture, and delivery verification gates. |
| Trust policy | Accepted agents get a trust policy that preserves sender identity and allowed shared scopes. |
| Stale roster defense | SuperBrembo and other retired/stale ids cannot be promoted into the active registry. |
| Persistence | Contracts and receipts round-trip in SQLite and in-memory stores. |
| Operator CLI | `python scripts/ams.py agent seed-roster|list|audit|onboard` works from a fresh root. |
| MCP | `cem_onboard_agent`, `cem_seed_hammad_agent_roster`, and `cem_list_onboarded_agents` expose the same path. |
| Verification | Focused tests prove roster, stale rejection, persistence, CLI, and MCP behavior. |

## CLI Surface

```powershell
python scripts/ams.py --json agent seed-roster
python scripts/ams.py --json agent list
python scripts/ams.py --json agent audit hessa
python scripts/ams.py --json agent onboard contract.json
```

## MCP Surface

- `cem_onboard_agent`
- `cem_seed_hammad_agent_roster`
- `cem_list_onboarded_agents`

## Non-Goals

- ACS live relay, SSE, or cross-machine messaging.
- Hosted SaaS onboarding.
- Claiming external runtime activation for Hermes, Hessa, or OpenClaw without
  their own product-path smoke proofs.

Those can be later phases. This phase accepts the full local AMS onboarding
contract and registry path.
