# AMS Product Lock Audit

Date: 2026-05-31
Source: `PRODUCT-LOCK.md`
Status: first acceptance audit

## Summary

AMS has a working memory engine and local operator surfaces, but the product is
not accepted yet.

The core gap is primary runtime adoption: Codex can call AMS, and this workspace
can gate startup through AMS, but AMS is not yet proven as the enforced primary
memory path for every serious Codex run.

## Acceptance Matrix

| Criterion | Status | Evidence | Missing Work | Next Step |
|---|---|---|---|---|
| A1. Primary Runtime Lock | partial | `scripts/session-start-gate.ps1` passes; dashboard shows latest startup brief allow; global `ams-memory` MCP is configured in `~/.codex/config.toml`; `startup-brief` now writes governed-run receipts with brief, monitor, evidence, cwd, task, status, and block reasons; live Codex hook smoke proves command hooks are invoked; `ams runtime-control` and `scripts/ams-guarded-command.ps1` enforce allow/block before a downstream command is invoked. | Legacy `codex-memory` and AMS both exist; governed-run receipts exist only when the AMS startup/control path is invoked; the guarded launcher is not yet wired as the default Codex entrypoint; no missing-memory failure drill on a fresh session. | Wire the AMS guarded launcher into the default Codex entrypoint, then define legacy memory as secondary input. |
| A2. Real Trace Intake | fail | Kernel and MCP have trace ingest APIs; tests ingest traces manually. | No ordinary Codex run currently emits a trace into AMS automatically. Source spans are proven for manual/test traces, not live work traces. | Add Codex run trace emission and ingestion. |
| A3. Trust Before Retrieval | pass | Validation, quarantine, reason codes, inactive-card filtering, negative controls, and failure canaries exist in tests and monitor paths. | Extend the same trust proof to live trace-derived candidates once A2 lands. | Keep this as a non-regression gate during trace intake work. |
| A4. Action Briefs Govern Work | partial | `startup-brief` returns bounded directives/cards/evidence/actions; MCP action brief returns applicable ids, evidence ids, score breakdown, and expected action delta source; governed-run receipts attach the startup brief id, monitor id, and evidence ids; `runtime-control` records the startup brief, monitor, governed-run id, gate decision, prompt decision, and evidence ids. | The global Codex runtime is not yet proven to force every serious run through the guarded launcher; normal runs do not yet close outcome/influence records. | Wire the guarded launcher as the default entrypoint, then close the loop with a finalized run/outcome receipt. |
| A5. Outcome Influence Loop | partial | Action influence models, persistence, and vertical-loop tests exist. | Normal Codex runs do not yet close an outcome/influence record. | Add governed-run close/finalize command or hook. |
| A6. Correction Capture | partial | Correction capture core, CLI, resume gate, monitor checks, PowerShell hook wrappers, `ams runtime-control`, and `scripts/ams-guarded-command.ps1` exist; live Codex smoke verified `UserPromptSubmit` payload keys and prompt/session projection; guarded-command tests prove a correction prompt blocks before the downstream command is invoked. | The current default Codex entrypoint is not yet forced through the guarded launcher, so ordinary work can still bypass enforcement. | Wire the guarded launcher into the default Codex entrypoint. |
| A7. Aging And Maintenance | partial | Expired/inactive cards are excluded from retrieval; staleness penalties and stale/supersession tests exist. | Monitor does not yet expose aging/maintenance as a first-class product surface; no operator repair/review command for AMS aging. | Add aging monitor section and review/repair path. |
| A8. Frontier Eval | partial | Baseline ladder, action-advantage metrics, negative-control suppression, latency budget, and full test suite pass. | Eval has not been rerun against the accepted product path after primary runtime adoption and real trace intake. | Re-run eval after A1/A2/A5 are product-wired. |
| A9. Operator Product | partial | README documents local commands; CLI can init, brief, audit, monitor; session gate and dashboard work in this repo. | No isolated fresh-operator proof that setup works without hidden state from this machine/repo. | Run fresh-root setup proof and update docs from the transcript. |

## Product State

Accepted now:

- AMS product lock exists and is the acceptance source.
- AMS startup gate can allow/block.
- AMS dashboard reports the current adoption phase.
- AMS monitor deep checks pass.
- Action-brief and validation engine tests pass.
- AMS runtime control can block before a downstream command is invoked.

Not accepted yet:

- AMS as the primary Codex memory path.
- Default Codex entrypoint through the AMS guarded launcher.
- Automatic trace intake from real Codex work.
- Governed-run receipts exist for `startup-brief`, but are not yet proven mandatory for every serious run.
- Memory aging and maintenance as an operator surface.
- Fresh operator setup proof.

## Commands Run For This Audit

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/session-start-gate.ps1
python scripts/ams.py dashboard
python scripts/ams.py monitor --deep
python scripts/ams.py runtime-control "continue AMS primary runtime adoption" --domain agentic-memory-system
rg -n "class ActionBrief|score_breakdown|ActionInfluenceEvent|VerificationProbe|negative_control|retrieve_action_brief|startup-brief|correction hook|review_stale|stale|superseded|ingest_trace|Trace" packages scripts tests docs README.md PRODUCT-LOCK.md
```

## Review Risk

The highest-risk blind spot is not a missing unit test in the engine. It is a
product acceptance mismatch: tests can pass while Codex can still ignore AMS in
ordinary work.

The PR review should focus on whether `PRODUCT-LOCK.md`, this audit, and the
execution plan truly force the build back to the intended AMS product.

## Next Implementation Target

Continue A1/A4/A6 together:

1. Wire the AMS guarded launcher into the default Codex entrypoint.
2. Define legacy `codex-memory` as secondary input under AMS, not a parallel primary.
3. Add a governed-run close/finalize path so outcomes and influence records attach to the same receipt.
