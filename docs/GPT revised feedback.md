You’re right to challenge it.

My previous framing was **directionally correct but operationally risky**. The phrase **“smallest kernel + ruthless eval”** can easily be interpreted by Codex as:

> “Build a narrow proof harness, leave the rest as placeholders, and call that progress.”

That is exactly how you get a half-baked repo.

The correct framing should be:

> **Build the full CEM-1 kernel now, end-to-end, with proof built into the architecture from day one. Not a mini proof project. Not a platform. Not a stubbed research scaffold. A full vertical system.**

So yes: **you should build the full project** — but with a very specific boundary.

---

# The distinction that matters

There are three possible strategies:

## 1. Bad: “Full platform build”

This means building everything around the idea:

```text
API service
UI
framework integrations
enterprise governance
multi-agent orchestration
graph browser
advanced learned scorer
cloud deployment
```

That would be premature. The current plan explicitly excludes these as non-goals: no hosted API, no integration matrix, no graph DB UI, no consumer app, no multi-agent orchestration platform, and no enterprise compliance layer. ([GitHub][1])

I agree with excluding those.

## 2. Bad: “Small proof-only slice”

This means:

```text
build eval harness
run synthetic MMA
leave consolidation shallow
leave verification partial
leave read-path partial
claim proof later
```

That is the Codex trap. It creates motion, not a system.

This is the version you are rejecting, and I agree with you.

## 3. Correct: “Full CEM-1 vertical kernel”

This means build the complete core loop:

```text
trace
→ atoms
→ validation
→ grounded consolidation
→ probe-gated verification
→ action-value retrieval
→ action brief
→ influence logging
→ MMA evaluation
→ feedback into verification/eval
```

That is already the architecture described in the plan: components 4–7 complete the missing system around the existing write path, especially consolidation, verification/promotion, causal read-path, and evaluation harness. ([GitHub][1])

This is the right build.

---

# Why I recommended proof-first

I recommended the “CEM-1 Proof Program” framing because the central claim of the project is not:

> “We store memories.”

It is:

> “Verified experience improves future action.”

The plan itself says the locked thesis is two clauses: prevent bad memories from becoming trusted experience, then prove verified experience changes what agents do. It also says clause 2 — causal read-path plus proof through MMA — is not built. ([GitHub][1])

So proof cannot be a later report. It has to be part of the system architecture.

But here is the important correction:

> **Proof-first should not mean proof-only.**

It should mean every major component is built against an evidence contract.

---

# What I would revise from my earlier recommendation

I would stop calling the immediate deliverable:

```text
CEM-1 Proof Program
```

because that phrase over-indexes on evaluation and invites underbuilding.

I would rename it:

```text
CEM-1 Full Kernel Build
```

With this definition:

> **A complete, local, end-to-end Causal Experience Memory kernel where every memory lifecycle transition, retrieval decision, and action-improvement claim is auditable, testable, and measurable.**

That is not a smaller project. It is a sharper full project.

---

# What should be built now

The full project should include all of this in the immediate CEM-1 build.

## 1. Full memory lifecycle

Current issue: promotion exists, but the plan says it is asserted rather than probe-verified. The current design doc identifies that cards can become `verified` without a real verification probe. ([GitHub][1])

Build the real lifecycle:

```text
proposed atom
→ candidate atom
→ candidate card
→ verification probe scheduled
→ verification result stored
→ verified card
→ retrieval eligible
→ deprecated / superseded / quarantined if invalidated
```

Hard rule:

```text
promote() must never mean verified.
```

It should mean:

```text
create_or_update_candidate_card()
```

Only a verification result should make a card verified.

## 2. Full consolidation, not shallow merging

The current plan says consolidation is partial: merges exist, but abstraction is not verified against source spans, and supersession is link-only. ([GitHub][1])

Build real consolidation now:

```text
deduplication
near-duplicate merge
source-span preservation
grounded abstraction
exception boundaries
supersession
deactivation of stale cards
contradiction links
```

Do not postpone this too far. Verification depends on what object is being verified. If consolidation changes the card after verification, the verification result becomes semantically unstable.

So the right order is not:

```text
read-path → verification → consolidation later
```

It should be:

```text
minimum grounded consolidation
→ verification
→ read-path
→ deeper abstraction
```

## 3. Full verification and negative controls

The project needs a CI/CD system for memory.

Build:

```text
VerificationProbe
VerificationResult
probe runner
negative-control injector
held-out replay probe
staleness probe
contradiction probe
promotion gate
```

No memory should be called verified unless there is stored evidence.

## 4. Full action-time adapter

The current plan says the action-time adapter is not built: retrieval is word-overlap and `expected_action_delta` is hardcoded `None`. ([GitHub][1])

Build the actual read-path:

```text
candidate generation
scope filtering
temporal filtering
precondition matching
contradiction penalty
staleness penalty
verified-lift prior
action-value score breakdown
bounded Action Brief
influence ID
```

This is not a later optimization. This is the core product.

## 5. Full influence ledger

Every action brief should create a traceable record:

```text
brief_id
task_id
candidate_card_ids
selected_card_ids
score_breakdown
scorer_version
expected_delta_source
influence_id
```

Then later:

```text
action_taken
outcome
observed_delta
counterfactual method
baseline comparison
```

Without this, the system cannot learn from its own memory use.

## 6. Full eval harness

The eval harness should not be the whole project, but it must be part of the full build.

The plan already says Phase 0 builds the proving-ground spine first, with baseline ladder, MMA harness, held-out tasks, and falsification suite. ([GitHub][1])

That is correct, but the implementation should not stop there.

The harness should evaluate the full kernel, not replace it.

## 7. Full CLI/operator surface

Because this is a local kernel, not a hosted platform, the operator surface matters.

Build commands like:

```bash
cem ingest
cem propose
cem validate
cem consolidate
cem verify
cem brief
cem close-influence
cem eval
cem audit
cem inspect-card
cem inject-negative-control
```

This makes the system usable, inspectable, and hard to fake.

---

# What should still wait

I would still sequence these after the core kernel:

```text
hosted API
multi-tenant auth
dashboard UI
graph browser
LangChain/LlamaIndex adapters
enterprise compliance layer
learned scorer
large-scale distributed storage
multi-agent orchestration
production SaaS packaging
```

Those are “full platform” features, not the CEM invention.

But I would **not** postpone:

```text
verification
consolidation
causal retrieval
influence logging
eval harness
auditability
negative controls
staleness handling
supersession
```

Those are the invention.

---

# The mistake Codex likely made

Codex probably took “eval-first” as:

> “Build the measurement slice first, then incrementally add pieces.”

That is not inherently wrong, but it becomes wrong when the agent starts marking scaffolds as done.

The plan itself warns against this: a component is only done with real consumers wired end-to-end, no fake-green checks, no asserted promotions, and executed evidence for every done claim. ([GitHub][1])

So the fix is not to abandon proof-first.

The fix is to change the build contract:

```text
No phase is allowed to land as isolated scaffolding.
Every phase must move the full vertical loop closer to completion.
Every component must have a real caller, real persisted state, real tests, and a failure canary.
```

---

# The corrected recommendation

I would now recommend this:

## Build the full CEM-1 kernel, not a proof MVP.

CEM-1 should be considered complete only when this whole loop works:

```text
1. Ingest real traces.
2. Extract typed atoms.
3. Validate atoms against grounding and contradiction checks.
4. Consolidate atoms into grounded candidate cards.
5. Run verification probes and negative controls.
6. Promote only probe-passing cards to verified.
7. Retrieve cards by action value, not similarity.
8. Return bounded Action Briefs with influence IDs.
9. Close the action-influence loop after outcomes.
10. Evaluate MMA against honest baselines on held-out tasks.
11. Report failure honestly if memory does not help.
```

That is the full project at kernel level.

---

# Revised sequencing I would use

Not:

```text
Phase 0: eval only
Phase 1: read-path
Phase 2: verification
Phase 3: consolidation
```

Better:

```text
Phase 0: Contract lock
- schemas
- lifecycle rules
- eval protocol
- no-fake-green gates
- storage migration plan

Phase 1: Full vertical skeleton, no stubs allowed
- ingest → atom → validate → candidate card → brief → influence record → eval run
- every step persists real objects
- nothing fake marked verified

Phase 2: Grounded consolidation + verification
- dedup
- source-span support
- probes
- negative controls
- verified lifecycle

Phase 3: Action-value retrieval
- feature scorer
- score breakdown
- temporal/staleness/contradiction penalties
- expected delta only from verified evidence

Phase 4: MMA and baseline ladder
- no-memory
- lexical overlap
- summary
- vector RAG
- time-aware RAG
- unverified reflection
- CEM

Phase 5: Hardening
- external benchmark runners
- better probes
- deeper abstraction
- cost/latency budgets
- stronger audit tools
```

This builds the full system, but avoids pretending that late-stage platform features are necessary for the core research/product claim.

---

# My direct answer

You are right that **“smallest kernel + eval” is dangerous wording**. It can produce exactly the half-built outcome you are trying to avoid.

The correct way is:

> **Build the full CEM project at kernel depth now. Do not build a small proof artifact. Do not build a broad platform. Build the complete causal-memory loop end-to-end with proof gates embedded into every transition.**

So I would change the plan language from:

```text
CEM-1 Proof Program
```

to:

```text
CEM-1 Full Kernel Build
```

And I would define the immediate deliverable as:

```text
A complete local CEM kernel with grounded consolidation, probe-gated verification, causal read-path, influence logging, and MMA evaluation against honest baselines.
```

That is the right version of “full project.”

[1]: https://raw.githubusercontent.com/7ammad/agentic-memory-frontier/main/docs/2026-05-28-causal-experience-memory-full-program-design.md "raw.githubusercontent.com"
