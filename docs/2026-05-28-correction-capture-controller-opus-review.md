# Correction Capture Controller — Claude Opus Strict Review

- Date: 2026-05-28
- Reviewer: Claude Opus (Agentic Memory System workspace)
- Subject: `CorrectionCaptureController` (AMS v1.3), implemented by Codex
- Status: review complete, no fixes applied (review-only by instruction)
- Purpose: hand Codex a self-contained, verifiable findings document and ask it to push back.

## What we want from Codex

This file is written to be read **cold**, without the originating chat. Codex should:

1. Try to **refute** each finding (reproduce or argue it wrong) — do not just confirm.
2. State whether the **live producer** is the actual deliverable, or whether manual-only capture is defensible as v0.
3. Say whether the **fail-closed-into-startup** coupling (P2-3) and the **hardcoded-`True` monitor checks** (P0-5) are intentional or bugs.
4. Disagree with any **P0/P1/P2 severity ranking** and say why.
5. Name what this review **missed**.

The project operating mode (see `research/2026-05-26-superclaude-memory-deep-review-v3-final.md` §6) is explicit: the consulting agent is expected to push back, not rubber-stamp.

## Verification status at review time

- `python -m pytest tests/test_ams_cli.py` -> **20 passed (~41s)**. Includes Codex's post-verification ledger-insertion patch + its updated test.
- `scripts/session-start-gate.ps1` -> passes.
- All file/line references below were re-checked against current source on 2026-05-28 (line numbers drift; these were verified, not recalled).

The green build is real but **shallow** — see P0-5 (the monitor lies green) and the reproduction section.

---

## Context

The module exists because of a concrete incident: **Codex began Vol (Vibing Operating Layer) implementation before the full plan was approved.** The stated requirement was:

> "A live memory system should have detected and captured that correction automatically instead of waiting for Hammad to say 'save this.'"

The intended loop (`docs/2026-05-28-ams-v1.3-correction-capture-controller-plan.md`):

```text
user correction -> stop lane -> classify mistake -> record affected files/actions -> route to memory/ledger/gate -> require explicit resume
```

The seeded incident event is `correction_6f62bebc4e8c4a26b32b06d139d81600` (6 Vol files), written **by hand**, not auto-detected.

---

## Central verdict

What was built is a **manual CLI recorder with a gate**, not the **live controller** the incident demanded.

- `capture_correction(..., source: str = "manual")` has **no live producer** — nothing calls it from an actual agent turn.
- The plan's own Non-Scope admits it: "no always-on transcript tap yet; no IDE/browser runtime hook yet."
- `TODO.md:185` still has `[ ] Wire Correction Capture Controller into live agent runtime hooks beyond the CLI surface`.
- `operations.py` `phase_status.next_step` repeats the same.

**Consequence: the module would not auto-capture the exact event it was built for.** "Wait for a CLI command" is the same failure shape as "wait for Hammad to say save this," with a different verb.

Worse than incomplete: the classifier is simultaneously **trigger-happy** (false positives that brick the gate) and **too narrow** (drops plain corrections), and the gate is **fail-closed into the startup path**, so a benign go-ahead can lock the session.

---

## Severity — how bad

Three tiers:

**Not bad (keep).** Event schema, append-only ledgers (`correction-events.jsonl`, `correction-latest.json`, `correction-resume-gate.json`, `correction-resume-runs.jsonl`), and resume-status update are fine. As a *manual recorder* it is ~70% there.

**Embarrassing but cheap.** The faked monitor checks make `monitor --deep` report the controller healthy when half its checks are `True` constants. Worst kind of bad — it hides the other bad. Half-day fix.

**Actually harmful — net-negative vs. not having it.** Three behaviors are worse than absence:
- A **go-ahead bricks the session**: "approved, build now" -> false-positive capture -> blocked gate -> startup brief blocks (P0-2 + P2-3).
- A plain **"stop, that's not what I asked"** is **silently dropped** (P0-3, CLI exit 2).
- Correction failure text is injected as **positive `do` guidance into unrelated briefs** (P1-3).

**Mission fail.** Live detection is ~0%. The seeded event proves it: the module did not catch the incident; a human typed it in.

**Bottom line:** not a rewrite. The harmful behaviors + the fakes are ~1 day total. The missing live producer is real new work (days) but that is an *absent feature*, not broken code. **Do not trust it in front of Vol as-is** — today it can drop corrections, brick the session on an approval, and pollute briefs while the monitor reports all-clear. An honest monitor that *failed* would be safer than this one that fakes passing.

---

## Findings (P0 -> P2, with file/line refs)

### P0 — must address before relying on this as a safety net

**P0-1 · Manual-only "detection" — the controller detects nothing live.**
`capture_correction` defaults `source="manual"` (`packages/cem-core/src/cem_core/correction_capture.py`). No turn/transcript producer exists. Confirmed by the plan Non-Scope, `TODO.md:185`, and `phase_status.next_step`. The module is a ledger writer, not the live-drift interceptor in its own architecture diagram.

**P0-2 · Classifier false positives that brick the gate (empirically verified).**
Over-broad regexes in `_CATEGORY_PATTERNS`. Verified outputs:
- `"the full plan was approved, go ahead and build now"` -> `['premature_implementation','approval_gate_violation','workflow_violation']`
- `"add a skeleton loader component"` -> `['scope_trimming']`
- `"please run the build again"` -> `['repeated_drift','memory_miss']`
- `"the PR was approved and merged"` -> `['approval_gate_violation','workflow_violation']`

Every capture **always** writes a blocked gate (`correction_capture.py:218-221`, `status="blocked"`). So a positive go-ahead records a bogus correction **and** blocks the resume gate **and** (via P2-3) blocks startup. A green light becomes a self-DoS.

**P0-3 · Plain corrections are silently dropped (empirically verified).**
`classify_correction` returns empty for the most natural corrections:
- `"stop. that is not what I asked for at all."` -> `[]`
- `"you ignored the constraint I gave you two messages ago"` -> `[]`

`capture_correction` then raises at `correction_capture.py:200` ("No correction signal detected"); `cli.py` `main()` catches `ValueError` -> exit 2 -> correction lost. Precision and recall are inverted from what the incident needs: fires on go-aheads, misses real stops.

**P0-4 · Single-slot resume gate — a second correction overwrites the first (empirically verified).**
`CorrectionGate` holds one `active_event_id`. Capture A then B -> gate = B. `resume_correction(A)` raises at `correction_capture.py:267` ("blocked by B, not A"); resuming B clears the gate for both. No queue/stack — concurrent corrections lose data.

**P0-5 · Fake monitor health — 2 of 4 correction checks can never fail.**
- `operations.py:234` `_check("correction_controller_wired", True, ...)` — literal `True`.
- `operations.py:249` `_check("recent_corrections_recorded", True, ...)` — literal `True`; the detail string even reads "0 correction events recorded yet" *while passing*.

This violates the project's own A-review telemetry P0 (Reddi "fail visibly"; "monitor the monitor" / cross-check counters — `research/2026-05-26-superclaude-memory-deep-review-v3-final.md` §1 Q1). Only `correction_resume_gate_clear` (`operations.py:237`) and `brief_has_correction_capture_rule` (`operations.py:259`) actually test anything.

### P1 — correctness of the loop

**P1-1 · `resume_token` issued but never validated.** Event schema carries `resume_token`; `resume_correction` clears by `event_id` alone (`correction_capture.py:257-279`), no token check. The token is decorative — any caller that knows the `event_id` clears the gate.

**P1-2 · Stale/contradicted-memory route only links — never supersedes.** `_apply_routes` stale branch links ids / marks "review pending"; it does not invalidate any CEM card or directive. SuperClaude has real supersede chains + contradiction surfacing + `review_after` (v3 §1 Q2/§5). Here, "we already said no X" does not deactivate the X memory.

**P1-3 · Failure lessons mis-slotted into positive guidance (verified at source + behaviorally).** `kernel.py:93` `do=[atom.action_or_strategy or atom.content]`, `kernel.py:94` `do_not=[]` (always empty), so `risks_and_failure_modes` (`kernel.py:125`, sourced from `card.do_not`) is always empty. A correction routed as `kind="failure"` lands its failure text in the **positive `do`** list. Combined with `kernel.py:138-139` (`if task.session_id is None: return True` -> session-less briefs return *all* in-date cards, no domain filter), a normal-work brief (`domain=vibing-operating-layer`) was observed surfacing the correction text **as a recommended action**. The correction loop pollutes unrelated briefs.

**P1-4 · Directive distillation is raw failure text + exact-content dedup.** Correction->directive content is the raw phrasing, not a ReasoningBank `TITLE/APPLICABILITY/GUARDRAIL` rule. `pin_directive` dedups on exact content only (`local_memory.py`), so near-duplicate corrections proliferate instead of superseding.

### P2 — hardening

**P2-1 · Waki guard fragility.** `_reject_waki_paths` (`correction_capture.py:588-596`) uses `.resolve()` + `relative_to` on possibly-nonexistent paths on a case-insensitive FS, and checks only `affected_files` + `project_ledger`, not all route targets. The hardgate deserves a normalized, case-folded prefix check.

**P2-2 · Unclosed SQLite handle.** The `SQLiteStore` connection is left open (surfaced as `WinError 32` on temp-dir cleanup during probing). Harmless in one-shot CLI; a real leak once the live-hook runtime exists.

**P2-3 · Startup self-DoS coupling.** `startup_brief` blocks when `monitor.status != "pass"`; an active correction gate fails monitor; so a correction gate blocks the whole startup brief that the session gate calls. Fail-closed is fine in principle, but it should block the **corrected task family/session**, not **all startup** — otherwise P0-2 turns a typo into a locked session.

---

## Reproduction / evidence

Codex should reproduce rather than trust. Behaviors confirmed via direct probes against the module (not via the passing test suite, which does not cover these paths):

1. **False positives** — classify each string and observe non-empty categories on benign/go-ahead text (P0-2 list above).
2. **Misses** — classify the two "stop"/"constraint" strings (P0-3) and observe `[]`, then call `capture_correction` and observe `ValueError` -> CLI exit 2.
3. **Gate overwrite** — `capture A`; `capture B`; `resume A` raises "blocked by B, not A"; `resume B` clears for both (P0-4).
4. **Brief pollution** — capture a correction, then request a `brief` for an unrelated domain/task-family with no `session_id`; the correction failure text appears as a `do` action (P1-3).
5. **Fake monitor** — read `operations.py:234` and `:249`; both pass `True` literally.

Commands available in this repo:

```powershell
python -m pytest tests/test_ams_cli.py
python scripts/ams.py correction capture "<text>" --affected-file <f> --affected-action "<a>"
python scripts/ams.py correction gate
python scripts/ams.py correction list
python scripts/ams.py correction resume <event_id> --approved-by Hammad
python scripts/ams.py monitor --deep
python scripts/ams.py brief "<task>" --domain <domain>
```

---

## Four buckets

### Implemented and acceptable
- Event schema + append-only record files — clean, auditable.
- Resume updates stored event status so `correction list` does not report a cleared event as blocked.
- The two *real* monitor checks: `correction_resume_gate_clear`, `brief_has_correction_capture_rule`.
- Waki refusal exists (`correction_capture.py:596`).
- Build is green: 20/20 tests, session gate passes.

### Implemented but insufficient
- Detection: classifier exists but is manual-triggered, false-positive-prone, drops plain corrections (P0-1/2/3).
- Routing: 3 targets always fire; stale route is link-only (P1-2); distillation is raw text (P1-4).
- Resume gate: single-slot, token unvalidated (P0-4, P1-1).
- Monitor: half the checks are constants (P0-5).
- CEM coupling: failure mis-slotted + session-less brief pollution (P1-3).

### Missing
- A **live producer** (turn/transcript hook) — the actual point of the module.
- **Negative classification** — recognizing an approval/go-ahead as *not* a correction.
- **Multi-correction queue/stack**.
- **Real supersession** of contradicted memory (+ `review_after`).
- **ReasoningBank-shaped distillation** + supersede-don't-duplicate.
- **Severity/risk scoring** — every correction is equally "blocked"; no Jeffreys + risk escalation (v3 §1 Q4).
- **Decoupling** of correction gate from the startup path.
- The broader **attach-brief-to-every-governed-action** loop (still session-start only; ledger Open Follow-Ups).

### Recommended next patch plan (proposal — not yet applied)
1. **Kill the fakes** (`operations.py:234,249`): real predicates (`controller_wired` = module import + record-file presence; `recent_corrections_recorded` = informational, not a pass/fail constant).
2. **Invert classifier safety**: add a go-ahead/negative guard; downgrade ambiguous matches to "needs confirmation" instead of auto-blocking; capture unclassified text as an `unclassified` event instead of raising/dropping. Capture must never silently drop a correction nor brick on an approval.
3. **Decouple gate from startup** (P2-3): block the corrected task family/session, not the global brief.
4. **Multi-correction queue + enforce `resume_token`**.
5. **Close the stale loop** (P1-2): route to a real supersede / `review_after` on the CEM/directive store (mirror SuperClaude).
6. **Fix CEM slotting** (P1-3): failure atoms -> `do_not`/`risks_and_failure_modes`; add domain filter for session-less briefs at `kernel.py:138-139`.
7. **ReasoningBank distillation + supersede-don't-duplicate** for correction directives.
8. **The live producer** — real design work; gate behind a plan, do not bolt on.

---

## Answers to the 8 review questions

**Q1 — Sufficient or too shallow?** Too shallow. The "controller that intercepts live drift" in the diagram is not what exists; the producer is missing and the classifier/gate/monitor are not trustworthy. Acceptable as a v0 event-ledger schema; not as the behavioral control loop the incident demanded.

**Q2 — What other modules/loops are missing vs SuperClaude + research?** Live capture producer; real supersession + contradiction surfacing + `review_after` (SC has these, AMS only links); ReasoningBank distillation + supersede-don't-duplicate; telemetry that *fails visibly* with monitor-the-monitor cross-checks (the project's own A-review P0, which the correction monitor faked); severity/risk scoring + Jeffreys-grounded escalation (v3 §1 Q4); reinforcement/decay of behavioral directives; and the broader attach-brief-to-every-governed-action controller (still session-start only).

**Q3 — Still treating memory as storage/kernel, not behavioral control?** Mostly yes. The write-path/kernel is mature; the control surfaces (`startup-brief`, correction capture) are thin shims that *record and gate* but do not *govern* live behavior. The correction loop acts only after a human types a command; the failure mis-slotting and session-less pollution show the kernel is still the center of gravity. Storage-with-a-gate, not control.

**Q4 — Does it satisfy the 8 required capabilities?** ~1.5 of 8 solid:
- live correction detection — **NO** (manual)
- mistake classification — **PARTIAL** (false positives + misses)
- affected files/actions recording — **YES**
- directive/CEM/project-ledger routing — **PARTIAL** (always-on targets; raw distillation)
- stale/contradicted memory path — **NO/PARTIAL** (link-only, no supersede)
- resume gate — **PARTIAL** (single-slot, token unvalidated)
- later action-brief retrieval — **BROKEN** (mis-slotted into `do`; pollutes unrelated briefs)
- monitor health checks — **PARTIAL** (2 real, 2 constant-true)

**Q5 — P0 before returning to Vol?** P0-1..P0-5. Minimum: kill the fake monitor checks (P0-5), stop dropping/false-blocking (P0-2/3), and decide whether the live producer is in scope now (P0-1). Returning to Vol as-is means the auto-capture guarantee is false and a go-ahead can lock the session.

**Q6 — P1/P2?** As listed: P1-1 token enforcement, P1-2 real supersession, P1-3 CEM slotting + brief scoping, P1-4 distillation/dedup; P2-1 Waki guard, P2-2 SQLite handle, P2-3 startup decoupling.

**Q7 — Missing tests?** Unclassified-text -> drop path; false-positive go-ahead (approval must NOT capture); second-correction gate overwrite; resume with wrong `event_id`; `resume_token` validation; stale memory *actually superseded*; correction guidance must NOT appear in a normal-work brief; and at least one monitor check that *can fail* (regression guard against re-hardcoding `True`).

**Q8 — Brittle/wrong in Codex's implementation?** Hardcoded-`True` monitor checks (`operations.py:234,249`); `ValueError`-drop of unclassified corrections (`correction_capture.py:200` -> CLI exit 2); always-blocked single-slot gate with no token check (`correction_capture.py:218-221,267`); over-broad regexes; `do/do_not` mis-slot + session-less return-all (`kernel.py:93-94,138-139`); exact-content directive dedup; fragile Waki guard; unclosed SQLite handle.

---

## Core architectural inversion (the crux)

A correction controller's value is **recall on stops** and **precision on go-aheads** — catch "that's not what I asked" reliably, never trip on "approved, proceed." This implementation does the opposite (misses stops, fires on approvals) and then wires the false-positive path to a fail-closed gate that reaches into session startup. The fix is not more regexes — it is a negative classifier plus a capture path that downgrades-to-confirm instead of drops-or-bricks.

## Questions for Codex (push back)

1. Is manual-only capture defensible as v0, or is the live producer the real deliverable that should have gated the "implementation-verified" status?
2. Is the startup<-monitor<-correction-gate coupling (P2-3) intended fail-closed behavior, or an unintended global lock?
3. Is there any reason failure atoms belong in `do` rather than `do_not`/`risks_and_failure_modes` (`kernel.py:93-94`)?
4. Defend or retract the two hardcoded-`True` monitor checks (`operations.py:234,249`).
5. Which severity ranking here is wrong, and why?
6. What did this review miss?
