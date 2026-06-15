# AMS Product Lock

Date locked: 2026-05-31
Status: canonical product acceptance lock; AMS v1 accepted on 2026-06-01; AMS
V2 accepted on 2026-06-10

## Product Line

The product is **AMS**.

AMS is AMS. Older internal research and kernel labels remain implementation
history in older specs, but they are not the product name and they are not how
scope is accepted.

## Product Thesis

Memory is not storage. Memory is verified experience that improves future
action.

AMS exists to make that thesis operational for real agents.

## Product Definition

AMS is a local, auditable memory operating layer for agents.

It turns real agent work into verified experience, filters out unsafe or stale
memory before trust, retrieves bounded action guidance before work, records
whether the guidance changed the outcome, and uses that evidence to improve the
next run.

AMS is not complete merely because it has a kernel, an MCP tool, a monitor, or
an eval score. AMS v1 is accepted only when Codex operates through it as the
primary memory path and the fresh local operator path passes.

## Frontier Bottlenecks AMS Attacks

1. Bad memory writes become trusted too easily.
2. Similarity retrieval does not reliably improve future action.
3. Agent memories get stale, contradicted, or poisoned.
4. Useful procedural lessons are not captured as reusable skills.
5. Multi-agent memory lacks provenance, conflict handling, and ownership.
6. Memory products overclaim because their evals do not measure action lift.

## Scope Lock

AMS v1 includes:

1. Real trace intake from agent work.
2. Typed memory candidates with source spans and provenance.
3. Validation before trust.
4. Quarantine for false, stale, unsupported, contradictory, poisoned, or
   non-causal memories.
5. Consolidation of repeated evidence into durable experience.
6. Evidence-gated verification before a memory can be trusted.
7. Retrieval by expected action value, not just similarity.
8. Bounded action briefs before serious work.
9. Influence records that connect memory use to task outcome.
10. Live correction capture and resume gates.
11. Memory health checks for staleness, contradiction, and aging.
12. Honest evals against no-memory, summary, and similarity baselines.
13. A local install/run path another operator can use.

AMS v1 does not require:

1. Hosted SaaS.
2. Dashboard-first UI.
3. Enterprise multi-tenant auth.
4. Broad framework integration matrix.
5. Public cloud deployment.
6. A learned black-box scorer.

Those can come later only after the local primary-memory product is real.

## Product Acceptance Criteria

AMS v1 is accepted because all criteria below have evidence in the repo.

### A1. Primary Runtime Lock

Codex starts serious work through AMS.

Evidence required:

- session startup runs the AMS gate;
- startup returns a bounded action brief;
- startup records `brief_id`, `monitor_id`, and evidence ids;
- missing, stale, contradicted, or failed memory retrieval degrades startup
  status with auditable warnings and does not block fresh explicit owner work;
- monitor, dashboard, MCP, and memory-surface failures degrade startup/runtime
  memory-readiness status with auditable warnings and do not become command
  authority;
- enforcement lives in a separate runtime-control/action-safety lane for
  destructive actions, secrets, legal/security risk, external sends, or an
  explicit current owner pause/stop/correction gate;
- legacy memory surfaces are secondary inputs, not the primary source.

### A2. Real Trace Intake

AMS ingests real agent work, not only hand-written examples.

Evidence required:

- a normal Codex run emits a trace;
- the trace is stored in the AMS root;
- memory candidates can be proposed from that trace;
- source spans point back to the trace evidence.

### A3. Trust Before Retrieval

Untrusted memory cannot silently enter action briefs.

Evidence required:

- every candidate has validation status and reason codes;
- bad candidates are quarantined before retrieval;
- trusted records have provenance, confidence, and temporal validity;
- failure canaries prove the validation gates can go red.

### A4. Action Briefs Govern Work

AMS returns actionable, bounded guidance before work.

Evidence required:

- retrieval returns action briefs, not raw dumps;
- action briefs include selected memory ids and why they apply;
- action briefs include score breakdowns or equivalent audit detail;
- action brief size is bounded by count and approximate token budget.

### A5. Outcome Influence Loop

AMS records whether memory changed the result.

Evidence required:

- each governed run can close an influence record;
- outcomes are linked to the brief that influenced them;
- reports distinguish observed outcome from verified lift.

### A6. Correction Capture

When Hammad corrects the agent, AMS captures it live.

Evidence required:

- the live hook payload mapping is smoke-tested;
- correction events open a resume gate;
- agent continuation is blocked until explicit approval by an enforceable
  runtime path, not only by a command-hook failure message;
- the correction is routed into directives, memory candidates, and the ledger.

### A7. Aging And Maintenance

AMS does not treat memory as permanently fresh.

Evidence required:

- stale or superseded memories are detected;
- active retrieval excludes expired or inactive records;
- monitor output names aging/maintenance risks;
- there is a repair or review path.

### A8. Frontier Eval

AMS proves action advantage honestly.

Evidence required:

- no-memory, summary, and similarity baselines run on the same tasks;
- AMS reports marginal action advantage with confidence intervals;
- negative controls are suppressed;
- failures are reported without moving the goalposts.

### A9. Operator Product

AMS can be used by someone other than the original builder.

Evidence required:

- fresh local setup instructions work;
- one command runs the health check;
- one command retrieves a startup/action brief;
- one command audits a memory;
- docs explain what is complete and what is not.

## Current Status

Built and verified:

- memory write-path validation and quarantine;
- typed evidence and durable memory records;
- action-brief retrieval with auditable scoring;
- verification probes, negative controls, and baseline evals;
- local CLI, monitor, dashboard, startup gate, and MCP bridge;
- correction capture core and hook wrappers;
- default Codex entrypoint wrapping through AMS runtime control;
- legacy `codex-memory` and native Codex memory reconciled under AMS as secondary inputs;
- governed-run close/finalize records with observational influence events;
- automatic runtime trace intake from ordinary guarded Codex work;
- automatic governed-run closure for guarded work outcomes;
- aging and maintenance review for expired, stale, inactive, contradicted, and pending records.
- fresh operator proof from an isolated local AMS root;
- Phase 4 frontier eval rerun after operator packaging.

Remaining AMS v1 gaps:

- Nothing for AMS v1. Post-v1 work must be opened as a new named phase, not as a
  surprise continuation of this acceptance lock.

Post-v1 phase opened:

- AMS V2: Experience Enforcement Architecture.
- Canonical plan: `docs/2026-06-10-ams-v2-experience-enforcement-plan.md`.
- Acceptance contract: `docs/2026-06-10-ams-v2-acceptance-contract.md`.
- Scope lock: V2 is the full experience enforcement build. The non-repeat
  enforcement kernel is included inside V2; it is not a V1.5 downgrade or
  smaller substitute.
- Status: accepted after the V2 terminal operator proof.

Post-V2 phase opened:

- External Benchmark Final Build.
- Status: active as of 2026-06-15.
- Scope: repair the real public benchmark zero-output finding by adding a
  natural-language extraction lane, answer synthesis, zero-output gates, local
  proxy metric labeling, and official evaluator provenance.
- Boundary: AMS V2 governance remains accepted. Internal synthetic/V2 greens
  prove governance-layer behavior, not official natural-language benchmark
  performance. Official HaluMem, MemoryArena, and LongMemEval-V2 scores require
  the released evaluator runtimes plus any required model/service credentials.

## AMS V2 Acceptance Lock

AMS V2 is accepted because the complete local experience-enforcement path has
repo evidence:

1. Consequential actions are captured as decision intents with authority,
   approval/experiment state, runtime surface, expected outcome, and evidence.
2. Outcomes are attributed as mistake, approved experiment failure, acceptable
   tradeoff, success, or unresolved.
3. Confirmed mistakes compile into behavior invariants; confirmed successes
   compile into procedural skill candidates.
4. Situation matching catches exact and paraphrased repeats while suppressing
   valid neighbors and owner-approved changed contexts.
5. Policy binding decides allow, steer, block, override, or degraded allow
   before downstream action selection.
6. Reasoning control keeps silent steering under the hood, makes blocks
   visible, and requires explicit authority for downgrades.
7. Supersession retires or restores stale/wrong invariants with audit events.
8. Multi-agent governance preserves writer identity, authority, visibility,
   ownership, provenance, and scope; low-authority or project-specific
   experience cannot silently become global action control.
9. The V2 eval harness passes all seed cases with zero false blocks.
10. The fresh-root V2 operator proof composes the accepted v1 operator path with
    the V2 eval harness and verifies final monitor/dashboard status.

V2 terminal proof command:

```powershell
python scripts/run_ams_v2_operator_proof.py --root tmp\ams-v2-operator-proof-final
```

Terminal proof result must include:

```text
AMS_V2_OPERATOR_PROOF_PASS
v2_eval=PASS 13/13 false_blocks=0/0
phase=AMS V2 Accepted ready=True
```

## AMS Agent Onboarding V2 Lock

AMS Agent Onboarding V2 is the named post-V2 product layer for registering
other agents as governed AMS participants.

Acceptance contract:
`docs/2026-06-11-ams-agent-onboarding-v2-contract.md`.

Accepted local roster:

- `codex`
- `hermes`
- `hessa`
- `claude-code-cursor`
- `cursor-agent`
- `openclaw` as parked but counted

Rejected stale topology:

- `superbrembo` is not an active agent and must not be revived by default.

AMS Agent Onboarding V2 is accepted only when agent identity, runtime surface,
operational status, owner scope, capability contracts, AMS memory-lane
commands, harness contracts, runtime checks, visibility/ownership, trust policy,
persistence, CLI, MCP, and stale-roster rejection are implemented and tested.

## Planning Order

Work proceeds in this order. Do not skip ahead to platform features.

1. Lock this document as the product acceptance source.
2. Make Codex start through AMS as primary memory.
3. Add governed-run receipts everywhere: `brief_id`, `monitor_id`, evidence ids.
4. Reconcile legacy Codex memory surfaces under AMS as secondary inputs.
5. Close the influence loop for governed runs.
6. Add real trace intake from ordinary work.
7. Add aging and maintenance checks.
8. Package the local operator path.
9. Re-run frontier evals against the accepted product path.

All nine planning-order items are complete for AMS v1.

## Completion Rule

AMS v1 is complete because the acceptance criteria pass against the real product
path, not a detached demo path.

If a test, dashboard, or report says AMS is complete while Codex can still ignore
AMS during normal work, that report is wrong.

Terminal proof command:

```powershell
python scripts/run_ams_operator_proof.py --root tmp\ams-operator-proof-final
```

Terminal proof result: fresh root setup passed, `ams-memory` reconciled as
primary, startup brief allowed, Monitor-0 deep passed, maintenance had zero
items, a real card audit passed, the governed run closed with outcome success,
and the Phase 4 frontier eval returned `PASS` with a 75.0pp lexical margin.
