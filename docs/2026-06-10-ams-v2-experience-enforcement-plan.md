# AMS V2 Experience Enforcement Plan

Date: 2026-06-10
Status: active execution plan
Scope: full AMS V2, not V1.5, not a smaller proof kernel
Acceptance contract: `docs/2026-06-10-ams-v2-acceptance-contract.md`

## Non-Trimming Lock

AMS V2 is the full experience enforcement architecture. The non-repeat
enforcement kernel is a core subsystem inside V2, not a downgrade, substitute,
or smaller plan.

The execution order below is dependency order, not scope reduction. Every phase
exists to ship the complete V2 objective:

> AMS uses attributed experience under the hood to improve agent action before
> the user has to notice, while exposing concise inference receipts, asks,
> blocks, and override evidence only when needed.

## V2 Thesis

Memory is not storage and not advice. Memory is attributed, authority-ranked,
temporally scoped experience that binds to future action control.

AMS V2 is accepted only when confirmed mistakes are not repeated on equivalent
future decisions, valid neighbor work is not falsely blocked, successful
procedures become reusable skill memory, superseded lessons stop firing, and the
whole loop is auditable through receipts rather than raw hidden reasoning.

## Product Objective

Build an under-the-hood experience layer for agents that can:

1. Capture what the agent intended, what it did, what authority applied, and what
   happened.
2. Classify outcomes as mistake, approved experiment failure, acceptable
   tradeoff, success, or unresolved.
3. Convert confirmed mistakes into scoped behavior invariants.
4. Convert successful repeated procedures into reusable skills.
5. Match future situations against prior experience without over-generalizing.
6. Intercept consequential decisions before action.
7. Decide block, ask, warn, allow, or silently steer to the corrected action.
8. Let the agent reason with rules without silently rationalizing past them.
9. Supersede stale or wrong lessons through authority-ranked updates.
10. Share governed experience across agents without scope pollution.
11. Prove behavior changed through non-repeat, false-block, skill-transfer, and
    drift evals.

## Core Architecture

```text
Runtime Trace + Decision Intent
        -> Experience Graph
        -> ErrorAttributor
        -> Success/Skill Attributor
        -> Authority + Scope Resolver
        -> BehaviorInvariantCompiler
        -> SkillCompiler
        -> SituationMatcher
        -> PolicyBindingLayer
        -> ActionDecisionPoint
        -> ReasoningController
        -> Under-the-Hood Steering / Block / Ask / Warn / Allow
        -> Inference Receipt
        -> Outcome + NonRepeat/Skill/Drift Eval
        -> Supersession + Active Forgetting
        -> Multi-Agent Governance
```

## V2 Subsystems

### 1. Experience Graph

Stores more than memory text. Each consequential action records:

- task and domain;
- expected outcome;
- actual outcome;
- action attempted;
- owner instruction or approval state;
- experiment flag;
- applicable authority;
- scope candidate;
- evidence ids and source spans;
- agent id and runtime surface;
- confidence, freshness, and supersession state.

Acceptance:

- A consequential action without expected outcome, authority, or approval state
  is flagged as unattributable.
- A user correction can be traced back to the decision that created it.

### 2. ErrorAttributor

Classifies outcomes as:

- `mistake`;
- `approved_experiment_failure`;
- `acceptable_tradeoff`;
- `success`;
- `unresolved`.

A mistake is an action, decision, statement, or judgment that is wrong relative
to applicable authority: owner input, docs, logic, system/developer instruction,
verified experience, best practice, or current evidence.

Acceptance:

- The June 9 general Codex/AMS correction classifies as a general agent behavior
  mistake, not a project-specific task issue.
- A failed but owner-approved experiment does not create a mistake invariant.
- A repeated owner-corrected behavior creates a non-repeat candidate.

### 3. Authority And Scope Resolver

Ranks authority and resolves scope:

```text
current explicit owner instruction
  > system/developer instruction
  > authoritative project docs
  > confirmed behavior invariant
  > verified experience card
  > best-practice evidence
  > learned card
  > current task context
```

Scope starts as narrow unless owner authority or cross-context recurrence proves
it is general.

Acceptance:

- A general behavior correction is retrievable outside the project where it was
  captured.
- A stale learned card cannot override a current owner directive.
- Scope promotion requires owner authority or recurrence evidence.

### 4. BehaviorInvariantCompiler

Converts confirmed mistakes into enforceable invariants:

```json
{
  "invariant_id": "...",
  "authority": "owner_instruction",
  "scope": "global_agent_behavior",
  "trigger": "equivalent situation match",
  "forbidden_repeat": "scope a general behavior failure as project-specific",
  "corrected_action": "route to codex-harness / AMS control-plane",
  "enforcement": "steer_or_block",
  "evidence_ids": ["..."],
  "supersession_status": "active"
}
```

Acceptance:

- Confirmed mistakes compile into explicit invariants with authority, scope,
  trigger, corrected action, enforcement mode, and evidence ids.
- Invariants can be audited and superseded.

### 5. SkillCompiler

V2 is not only "do not repeat mistakes." It also captures "do this again" when
success is attributable and reusable.

Skill memory records:

- preconditions;
- procedure;
- tools used;
- expected result;
- failure boundaries;
- evidence;
- transfer scope;
- when not to apply.

Acceptance:

- A repeated successful workflow becomes a skill candidate.
- A skill candidate must pass replay or transfer evidence before promotion.
- Skill retrieval includes "do not apply when" constraints.

### 6. SituationMatcher

Matches future decisions to prior mistakes, skills, and supersession evidence.
It must catch paraphrased repeats without blocking valid neighbors.

Acceptance:

- Exact repeat fires.
- Paraphrased repeat fires.
- Valid neighbor does not fire.
- Owner-approved changed context does not block.
- Match results include confidence and reasons suitable for receipt output.

### 7. PolicyBindingLayer

Binds invariants and skills to enforcement modes:

- silent steer;
- warn;
- ask;
- block;
- allow with receipt;
- override with receipt.

Default behavior is under the hood. The user should not have to catch the repeat.

Acceptance:

- Known repeats are silently steered or blocked before execution.
- The user sees a concise receipt only when intervention, audit, or override is
  needed.

### 8. ActionDecisionPoint

Every consequential action passes through a decision point before execution.

Verdicts:

- `allow`;
- `steer`;
- `warn`;
- `ask`;
- `block`;
- `override_allowed`;
- `degraded_allow`.

Acceptance:

- A blocked action does not execute.
- A steered action changes the next move without requiring user intervention.
- If the host runtime cannot intercept an action class, AMS records the boundary
  honestly and does not claim full blocking for that class.

### 9. ReasoningController

The agent must reason, not blindly follow regex rules. But it cannot silently
rationalize past confirmed mistakes.

Rules:

- Escalation is easy: allow -> warn -> ask -> block.
- Downgrade is constrained: block -> allow requires explicit reason, receipt,
  authority, and rate limit.
- Raw hidden reasoning is not the UX. The UX is an inference receipt.

Acceptance:

- The same model cannot silently override an active invariant.
- Downgrades create visible receipts.
- Receipts say what changed and why without exposing raw hidden chain-of-thought.

### 10. Inference Receipts

Receipts are compact evidence artifacts, not long explanations.

Example:

```json
{
  "ams_effect": "changed_action",
  "matched_experience": "invariant_...",
  "decision": "steer",
  "authority": "owner_instruction",
  "scope": "global_agent_behavior",
  "user_visible": false,
  "receipt_available": true
}
```

Acceptance:

- Receipts are persisted for audit.
- User-facing output stays quiet unless ask, block, override, or audit requires
  visibility.

### 11. Supersession And Active Forgetting

Experience must not become permanent stale law.

Supersession sources:

- current explicit owner instruction;
- updated authoritative docs;
- higher-priority verified evidence;
- failed replay evidence;
- owner-approved override.

Acceptance:

- A superseded invariant stops firing on the next equivalent decision.
- Supersession is auditable and reversible.

### 12. Multi-Agent Governance

V2 includes shared experience without scope pollution.

Governance tracks:

- agent identity;
- writer authority;
- visibility;
- ownership;
- conflict;
- provenance;
- recipient applicability;
- cross-agent promotion rules.

Acceptance:

- One agent's project-specific lesson cannot silently become another agent's
  global behavior rule.
- A global owner directive can apply across agents.
- Conflicts surface through authority-ranked receipts.

### 13. Evaluation Layer

V2 eval is not storage hygiene only. It measures behavior change.

Required eval families:

- non-repeat eval;
- false-block eval;
- approved-experiment exclusion;
- skill-transfer eval;
- supersession eval;
- cross-context generalization eval;
- multi-agent conflict eval;
- context-pollution / memory-laundering eval;
- identity / behavior drift eval.

Acceptance:

- A release cannot pass if it prevents repeats only by blocking valid work.
- A release cannot pass if it stores corrections but the next equivalent action
  repeats the mistake.

## Execution Phases

### Phase 0 - V2 Contract Lock

Deliverables:

- this plan accepted as AMS V2 scope;
- V2 acceptance contract;
- V2 acceptance criteria added to TODO;
- V2 ledger entry;
- baseline test corpus outline;
- explicit false-block budget placeholder.

Acceptance:

- Repo has a named AMS V2 phase.
- No document frames V2 as V1.5 or a smaller substitute.
- Dashboard/monitor status reports AMS V2 as the active rail.

### Phase 1 - Experience Graph And Decision Intent

Deliverables:

- v2 trace/decision schema;
- expected outcome capture;
- authority capture;
- approval and experiment-state capture;
- runtime-surface capture;
- audit view.

Acceptance:

- Consequential action traces include enough evidence for later attribution.
- Missing attribution fields fail a canary.

### Phase 2 - Error And Success Attribution

Deliverables:

- ErrorAttributor;
- SuccessAttributor;
- owner-labeled seed corpus;
- approved experiment exclusion;
- scope candidate classification.

Acceptance:

- Mistake vs approved experiment failure is classified correctly.
- General behavior corrections are not trapped in project-specific scope.

### Phase 3 - Invariants, Skills, And Authority Scope

Deliverables:

- BehaviorInvariantCompiler;
- SkillCompiler;
- authority-ranked retrieval lanes;
- scope promotion rules.

Acceptance:

- A confirmed mistake creates a scoped invariant.
- A confirmed success creates a skill candidate.
- Owner authority beats stale learned memory.

### Phase 4 - Situation Matching

Deliverables:

- exact repeat matching;
- paraphrase repeat matching;
- valid-neighbor suppression;
- confidence and reason output.

Acceptance:

- True repeats fire.
- Valid neighbors do not fire.
- Thresholds are measured against the false-block budget.

### Phase 5 - Action Decision Point And Policy Binding

Deliverables:

- pre-action decision point;
- policy verdicts;
- enforcement receipts;
- runtime interception boundary map.

Acceptance:

- A known repeat is stopped or steered before execution.
- Non-interceptable action classes are documented honestly.

### Phase 6 - Reasoning Controller And Under-The-Hood UX

Deliverables:

- asymmetric reasoning rules;
- downgrade receipts;
- silent steering behavior;
- ask/block/override UX.

Acceptance:

- Agent can reason with experience.
- Agent cannot silently override confirmed mistakes.
- User does not need to notice a repeat for AMS to work.

### Phase 7 - Supersession And Active Forgetting

Deliverables:

- SupersessionLedger;
- active forgetting path;
- stale invariant demotion;
- owner override handling.

Acceptance:

- Superseded experience stops firing.
- Override and supersession are auditable.

### Phase 8 - Multi-Agent Experience Governance

Deliverables:

- writer identity;
- cross-agent authority model;
- visibility and ownership constraints;
- conflict receipts.

Acceptance:

- Cross-agent sharing works only within declared authority and scope.
- Scope pollution is caught by canaries.

### Phase 9 - V2 Eval Harness

Deliverables:

- NonRepeatEval;
- FalseBlockEval;
- ApprovedExperimentEval;
- SkillTransferEval;
- SupersessionEval;
- MultiAgentConflictEval;
- ContextPollutionEval.

Acceptance:

- Known mistakes do not repeat.
- Valid work is not blocked beyond budget.
- Skills transfer only when preconditions match.
- Superseded rules stop firing.

### Phase 10 - Operator Proof And Release Lock

Deliverables:

- one-command V2 operator proof;
- dashboard/monitor V2 status;
- audit docs;
- review prompts;
- final product lock update.

Acceptance:

- Fresh-root V2 operator proof passes.
- Full test suite passes.
- Independent review finds no blocking issues.
- V2 acceptance claims cite receipts, not impressions.

## Blocking Acceptance Battery

AMS V2 is not accepted unless all of these pass:

1. Confirmed mistake replay: the same mistake is not repeated.
2. Paraphrased repeat replay: the same mistake in different wording is not
   repeated.
3. Valid neighbor: similar but valid work is not blocked.
4. Approved experiment: failed approved experiment does not become a mistake.
5. Scope correction: general behavior correction applies outside the original
   project.
6. Authority precedence: current owner directive beats stale learned memory.
7. Silent steering: AMS changes action under the hood without requiring the user
   to catch the repeat.
8. Block receipt: a blocked action does not execute and leaves an audit receipt.
9. Downgrade receipt: allow-despite-invariant requires visible evidence.
10. Supersession: retired invariant stops firing.
11. Skill transfer: successful procedure is reused when preconditions match.
12. Skill boundary: successful procedure is not reused when preconditions fail.
13. Multi-agent scope: one agent's project-specific lesson does not become
    global for another agent.
14. Context pollution: untrusted or low-authority memory cannot launder into
    action control.
15. Operator proof: fresh-root local V2 path passes from setup to eval.

## Kill Criteria

Stop or redesign the relevant subsystem if:

- the host runtime cannot provide any enforceable decision point for the action
  class being claimed;
- repeat prevention only works by blocking too much valid work;
- attribution cannot distinguish mistake from approved experiment failure better
  than a trivial baseline;
- situation matching only works on exact text replay;
- receipts cannot explain action changes without leaking raw hidden reasoning;
- cross-agent sharing creates uncontrolled scope pollution.

## First Implementation Slice

The first slice is not a smaller product. It is the first executable dependency
inside full V2:

1. Add V2 TODO rail.
2. Add V2 schemas for decision intent and experience graph records.
3. Add seed fixtures for the June 9 general Codex/AMS correction, an approved
   failed experiment, a valid neighbor, and a paraphrased repeat.
4. Add red tests proving current AMS cannot prevent the repeated mistake under
   the V2 acceptance contract.
5. Implement attribution and invariant compilation only after the red tests bite.
