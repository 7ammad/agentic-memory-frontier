# AMS Product Lock

Date locked: 2026-05-31
Status: canonical product acceptance lock

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

AMS is not complete because it has a kernel, an MCP tool, a monitor, or an eval
score. AMS is complete only when Codex actually operates through it as the
primary memory path.

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

AMS is not accepted until all criteria below have evidence in the repo.

### A1. Primary Runtime Lock

Codex starts serious work through AMS.

Evidence required:

- session startup runs the AMS gate;
- startup returns a bounded action brief;
- startup records `brief_id`, `monitor_id`, and evidence ids;
- failure to retrieve required memory blocks work in an enforceable runtime path,
  not only as advisory hook output;
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
- correction capture core and hook wrappers.

Not yet accepted:

- AMS as the primary Codex memory path;
- default Codex entrypoint wired through the AMS guarded launcher;
- governed-run receipts for every serious run;
- continuous real trace intake from ordinary Codex work;
- aging and maintenance as a first-class product surface;
- external operator install/run proof.

## Planning Order

Work proceeds in this order. Do not skip ahead to platform features.

1. Lock this document as the product acceptance source.
2. Make Codex start through AMS as primary memory.
3. Add governed-run receipts everywhere: `brief_id`, `monitor_id`, evidence ids.
4. Wire the AMS guarded launcher into the default Codex entrypoint.
5. Add real trace intake from ordinary work.
6. Close the influence loop for governed runs.
7. Add aging and maintenance checks.
8. Package the local operator path.
9. Re-run frontier evals against the accepted product path.

## Completion Rule

AMS is complete only when the acceptance criteria pass against the real product
path, not a detached demo path.

If a test, dashboard, or report says AMS is complete while Codex can still ignore
AMS during normal work, that report is wrong.
