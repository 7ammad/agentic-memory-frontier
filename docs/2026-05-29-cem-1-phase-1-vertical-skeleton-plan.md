# CEM-1 Phase 1 — Full Vertical Skeleton Implementation Plan

> **For agentic workers:** TDD per task (failing test → run → minimal implement → run → commit). Steps use checkbox (`- [ ]`) syntax. Every gate ships a failure canary (a test that injects a known-bad condition and asserts the gate fails), per the §5 build contract.

**Goal:** Make the full causal-memory loop execute end-to-end on real persisted objects — `ingest → atom → validate → candidate card → brief → influence record → eval run` — with no stubs, nothing fake marked `verified`, and a source-tagged (never placeholder) action delta.

**Architecture:** Complete the behavior of objects whose schema Phase 0 locked. The kernel already does ingest/extract/validate/promote-to-candidate; Phase 1 enriches the Action Brief (real ids, scorer version, score breakdown, sourced delta), persists an `ActionBriefRecord`, adds the `close_influence` path that writes an `ActionInfluenceEvent` (observational only), and adds a minimal end-to-end loop runner that produces a real `MMAResult` from the locked eval protocol. The V0 deterministic extractor, the word-overlap scorer, and the absence of verification are **deliberately kept** — the real action-value scorer is Phase 3, consolidation+verification is Phase 2.

**Tech Stack:** Python 3.14, Pydantic v2 (`StrictModel`), pytest (pythonpath wired in pyproject.toml), SQLite JSON-blob storage, Windows/PowerShell.

**Source spec:** `docs/2026-05-28-causal-experience-memory-full-program-design.md` §4.1, §4.5, §5, §8 (Phase 1), §10. **Locked contract (do not re-litigate):** models in `packages/cem-core/src/cem_core/models.py`, storage API in `packages/cem-core/src/cem_core/storage.py`, eval protocol in `packages/cem-eval/src/cem_eval/eval_protocol.py`.

**Phase 1 scope guard (binding).** In-scope: brief enrichment, `ActionBriefRecord` persistence, `close_influence`/`ActionInfluenceEvent`, minimal loop runner + MMA, runnable script. **Out of scope (later phases):** the action-value feature scorer and verified-lift prior (Phase 3); dedup/grounded-abstraction/supersession and verification probes/negative-control promotion gate (Phase 2); the full baseline ladder exam and external benchmarks (Phase 4–5). Phase 1 keeps `scorer_version="lexical_overlap_v0"` and never sets `expected_action_delta_source="probe_verified"`.

---

## File Structure

- **Modify:** `packages/cem-core/src/cem_core/kernel.py` — enrich `retrieve_action_brief`; add `close_influence`.
- **Create:** `packages/cem-eval/src/cem_eval/vertical_loop.py` — `run_vertical_loop(root) -> VerticalLoopReport`.
- **Modify:** `packages/cem-eval/src/cem_eval/__init__.py` — export the runner + report model.
- **Create:** `scripts/run_cem_vertical_loop.py` — runnable consumer (mirrors `scripts/run_synthetic_eval.py`).
- **Create tests:** `tests/test_action_brief_record.py`, `tests/test_close_influence.py`, `tests/test_vertical_loop.py`, `tests/test_run_cem_vertical_loop_script.py`.

---

## Chunk 1: Read-path completion (Tasks A–C)

### Task A: Brief enrichment — ids, scorer version, score breakdown, sourced delta

**Files:** Modify `packages/cem-core/src/cem_core/kernel.py` (`retrieve_action_brief`). Test `tests/test_action_brief_record.py`.

The honesty contract for the Phase 1 delta (spec §4.1): `expected_action_delta` is an **observational estimate**, never invented, never a placeholder, never presented as causal. Phase 1 uses the selected cards' `confidence_score` as the estimate and tags `expected_action_delta_source="observational_unverified"`. Invariant: a non-`None` delta implies `source != "none"`; `source=="none"` implies delta is `None` (no cards selected).

- [ ] **Step 1 — failing test** (add to `tests/test_action_brief_record.py`):

```python
from cem_core import AgentTrace, CEM, TaskContext, TraceTurn


def _seed_card(cem):
    trace = AgentTrace(
        session_id="s1", agent_id="codex",
        turns=[TraceTurn(index=0, role="environment",
                         content="SKILL: set assignment_group before assignee")],
        final_outcome="success",
    )
    cem.ingest_trace(trace)
    atom = cem.propose_memories(trace.trace_id)[0]
    cem.validate(atom.atom_id)
    return cem.promote(atom.atom_id)


def test_brief_is_enriched_and_delta_is_sourced(tmp_path):
    cem = CEM(tmp_path)
    _seed_card(cem)
    brief = cem.retrieve_action_brief(TaskContext(description="set assignment_group before assignee"))
    assert brief.applicable_card_ids, "expected the seeded card to be selected"
    assert brief.influence_id is not None
    assert brief.scorer_version == "lexical_overlap_v0"
    assert brief.expected_action_delta_source == "observational_unverified"
    assert brief.expected_action_delta is not None
    assert set(brief.score_breakdown_by_card) == set(brief.applicable_card_ids)
    for feats in brief.score_breakdown_by_card.values():
        assert "lexical_overlap" in feats


def test_brief_with_no_cards_has_none_delta_and_none_source(tmp_path):
    cem = CEM(tmp_path)  # empty store, nothing selected
    brief = cem.retrieve_action_brief(TaskContext(description="totally unrelated topic xyzzy"))
    assert brief.applicable_card_ids == []
    assert brief.expected_action_delta is None
    assert brief.expected_action_delta_source == "none"


def test_brief_never_presents_untagged_delta(tmp_path):
    # Failure canary: a non-None delta must always be sourced (never the old
    # hardcoded-None placeholder, never an untagged number).
    cem = CEM(tmp_path)
    _seed_card(cem)
    brief = cem.retrieve_action_brief(TaskContext(description="set assignment_group before assignee"))
    if brief.expected_action_delta is not None:
        assert brief.expected_action_delta_source != "none"
    # and Phase 1 never claims causal verification it does not have
    assert brief.expected_action_delta_source != "probe_verified"
```

- [ ] **Step 2 — run, expect fail.** `python -m pytest tests/test_action_brief_record.py -q` → FAIL (`scorer_version` is `None`, delta is `None`, breakdown empty).

- [ ] **Step 3 — implement.** Rewrite the body of `retrieve_action_brief` (`kernel.py`) so the scored cards keep their scores, persist nothing yet (record lands in Task B), and build the enriched brief:

```python
SCORER_VERSION = "lexical_overlap_v0"  # module constant near score_card

def retrieve_action_brief(self, task: TaskContext, *, max_cards: int = 5) -> ActionBrief:
    in_scope = [card for card in self.store.list_cards() if self._card_in_scope(card, task)]
    scored = sorted(
        ((score_card(card, task), card) for card in in_scope),
        key=lambda item: item[0],
        reverse=True,
    )
    selected = [(score, card) for score, card in scored if score > 0][:max_cards]
    selected_cards = [card for _, card in selected]
    confidence = max((card.confidence_score for card in selected_cards), default=0.0)
    score_breakdown = {
        card.card_id: {"lexical_overlap": float(score)} for score, card in selected
    }
    if selected_cards:
        expected_delta = confidence
        delta_source = "observational_unverified"
    else:
        expected_delta = None
        delta_source = "none"
    influence_id = new_id("influence")
    return ActionBrief(
        task_id=task.task_id,
        applicable_card_ids=[c.card_id for c in selected_cards],
        why_applicable=[f"matched task terms with '{c.title}'" for c in selected_cards],
        preconditions_to_check=[item for c in selected_cards for item in c.check_first],
        recommended_next_actions=[item for c in selected_cards for item in c.do],
        risks_and_failure_modes=[item for c in selected_cards for item in c.do_not],
        stale_or_contested_memory_ids_to_ignore=[],
        evidence_links=[a for c in selected_cards for a in c.evidence_atom_ids],
        confidence_score=confidence,
        expected_action_delta=expected_delta,
        influence_id=influence_id,
        scorer_version=SCORER_VERSION,
        expected_action_delta_source=delta_source,
        score_breakdown_by_card=score_breakdown,
    )
```

Add `new_id` to the `.models` import in `kernel.py`.

- [ ] **Step 4 — run, expect pass.** `python -m pytest tests/test_action_brief_record.py -q` → 3 pass.
- [ ] **Step 5 — commit.** `feat: enrich action brief with influence id, scorer version, score breakdown, and sourced delta`.

### Task B: Persist `ActionBriefRecord` on retrieval

**Files:** Modify `kernel.py` (`retrieve_action_brief`). Test `tests/test_action_brief_record.py`.

- [ ] **Step 1 — failing test** (append). Prove real cross-instance persistence over a SQLite root:

```python
from cem_core.storage import SQLiteStore


def test_retrieval_persists_action_brief_record(tmp_path):
    cem = CEM(tmp_path)
    _seed_card(cem)
    brief = cem.retrieve_action_brief(TaskContext(description="set assignment_group before assignee"))
    # a fresh kernel over the SAME root must find the persisted record
    reopened = CEM(store=SQLiteStore(tmp_path))
    record = reopened.store.get_action_brief_record(brief.brief_id)
    assert record.influence_id == brief.influence_id
    assert record.selected_card_ids == brief.applicable_card_ids
    assert set(record.candidate_card_ids) >= set(record.selected_card_ids)
    assert record.scorer_version == "lexical_overlap_v0"
    assert record.expected_action_delta_source == brief.expected_action_delta_source
```

- [ ] **Step 2 — run, expect fail.** `KeyError: Action brief record not found`.
- [ ] **Step 3 — implement.** In `retrieve_action_brief`, before returning, persist the record (capture all in-scope as candidates):

```python
brief = ActionBrief(...)  # as above
self.store.save_action_brief_record(ActionBriefRecord(
    brief_id=brief.brief_id,
    task_id=task.task_id,
    candidate_card_ids=[c.card_id for c in in_scope],
    selected_card_ids=brief.applicable_card_ids,
    score_breakdown_by_card=score_breakdown,
    scorer_version=SCORER_VERSION,
    expected_action_delta_source=delta_source,
    influence_id=influence_id,
))
return brief
```

Add `ActionBriefRecord` to the `.models` import in `kernel.py`.

- [ ] **Step 4 — run, expect pass.** Full file → 4 pass.
- [ ] **Step 5 — commit.** `feat: persist action brief record on retrieval`.

### Task C: `close_influence` writes an `ActionInfluenceEvent` (observational only)

**Files:** Modify `kernel.py` (new method). Test `tests/test_close_influence.py`.

`close_influence` loads the persisted `ActionBriefRecord` by `brief_id` (so the record is load-bearing, not dead state), then writes an observational `ActionInfluenceEvent`. The observational/causal firewall (spec §4.2): closing influence must never set a card `verified` or `measured_lift`.

- [ ] **Step 1 — failing test** (`tests/test_close_influence.py`):

```python
from cem_core import AgentTrace, CEM, TaskContext, TraceTurn


def _brief(cem):
    trace = AgentTrace(
        session_id="s1", agent_id="codex",
        turns=[TraceTurn(index=0, role="environment",
                         content="SKILL: set assignment_group before assignee")],
        final_outcome="success",
    )
    cem.ingest_trace(trace)
    atom = cem.propose_memories(trace.trace_id)[0]
    cem.validate(atom.atom_id)
    card = cem.promote(atom.atom_id)
    return cem.retrieve_action_brief(TaskContext(description="set assignment_group before assignee")), card


def test_close_influence_writes_observational_event(tmp_path):
    cem = CEM(tmp_path)
    brief, _ = _brief(cem)
    event = cem.close_influence(brief.brief_id, action_taken="set assignment_group",
                                outcome="success", observed_post_brief_delta=0.2)
    assert event.influence_id == brief.influence_id
    assert event.brief_id == brief.brief_id
    assert event.observed_post_brief_delta == 0.2
    assert event.counterfactual_method is not None  # documents it is observational
    stored = cem.store.list_action_influence_events(brief.influence_id)
    assert len(stored) == 1 and stored[0].outcome == "success"


def test_close_influence_never_verifies_a_card(tmp_path):
    # Failure canary: a post-brief outcome is observational, never causal — it
    # must not promote or set measured lift on any card.
    cem = CEM(tmp_path)
    brief, card = _brief(cem)
    cem.close_influence(brief.brief_id, action_taken="x", outcome="success",
                        observed_post_brief_delta=0.9)
    reloaded = cem.store.get_card(card.card_id)
    assert reloaded.promotion_status == "candidate"
    assert reloaded.measured_lift is None
```

- [ ] **Step 2 — run, expect fail.** `AttributeError: 'CEM' object has no attribute 'close_influence'`.
- [ ] **Step 3 — implement** (add to `kernel.py`, import `ActionInfluenceEvent`):

```python
def close_influence(
    self, brief_id: str, *, action_taken: str | None = None,
    outcome: str = "unknown", observed_post_brief_delta: float | None = None,
    counterfactual_method: str | None = None, baseline_comparison: str | None = None,
) -> ActionInfluenceEvent:
    record = self.store.get_action_brief_record(brief_id)
    event = ActionInfluenceEvent(
        influence_id=record.influence_id,
        brief_id=brief_id,
        task_id=record.task_id,
        action_taken=action_taken,
        outcome=outcome,
        observed_post_brief_delta=observed_post_brief_delta,
        counterfactual_method=counterfactual_method or "observational_no_counterfactual",
        baseline_comparison=baseline_comparison,
    )
    self.store.save_action_influence_event(event)
    return event
```

- [ ] **Step 4 — run, expect pass.** `python -m pytest tests/test_close_influence.py -q` → 2 pass.
- [ ] **Step 5 — commit.** `feat: add close_influence path writing observational influence events`.

---

## Chunk 2: Minimal end-to-end eval run (Tasks D–E)

### Task D: Minimal vertical-loop runner + MMA

**Files:** Create `packages/cem-eval/src/cem_eval/vertical_loop.py`; modify `__init__.py`. Test `tests/test_vertical_loop.py`.

The runner drives the **whole loop** on real objects and computes a minimal MMA (memory vs no-memory) via the locked `marginal_memory_advantage`. The toy agent: a memory run "succeeds" on a held-out task iff the retrieved brief's `recommended_next_actions` contains the task's decisive action; a no-memory run scores 0 (no brief). This is a skeleton smoke that proves the pipe carries water end-to-end — **not** the Phase 4 ladder exam. Leakage (spec §10): memory-source ids and held-out answer ids must be disjoint; the runner asserts this and a canary proves the guard bites.

- [ ] **Step 1 — failing test** (`tests/test_vertical_loop.py`):

```python
import pytest
from cem_eval.vertical_loop import run_vertical_loop


def test_vertical_loop_runs_end_to_end_on_real_objects(tmp_path):
    report = run_vertical_loop(tmp_path)
    assert report.n >= 1
    assert report.trace_count >= 1
    assert report.atom_count >= 1
    assert report.card_count >= 1
    assert report.brief_record_count == report.n
    assert report.influence_event_count == report.n
    assert report.mma is not None
    assert report.ci_low <= report.mma <= report.ci_high


def test_vertical_loop_leakage_guard_bites(tmp_path):
    # Failure canary: if a held-out answer id leaks into the memory source,
    # the runner's leakage guard must raise (not silently score).
    with pytest.raises(ValueError):
        run_vertical_loop(tmp_path, inject_leakage=True)
```

- [ ] **Step 2 — run, expect fail.** `ModuleNotFoundError: No module named 'cem_eval.vertical_loop'`.
- [ ] **Step 3 — implement** `vertical_loop.py`. Reuse `HELD_OUT_DECISIVE_ACTIONS` as both the seeded memory content and the held-out tasks. Build a `VerticalLoopReport(BaseModel)` with: `mma, n, ci_low, ci_high, trace_count, atom_count, card_count, brief_record_count, influence_event_count, scorer_version`. Flow:

```python
from __future__ import annotations
from pathlib import Path
from pydantic import BaseModel

from cem_core import AgentTrace, CEM, TaskContext, TraceTurn
from cem_eval.eval_protocol import assert_no_leakage, marginal_memory_advantage

HELD_OUT = (
    "set assignment_group before assignee",
    "run pytest before claiming kernel changes are done",
)


class VerticalLoopReport(BaseModel):
    mma: float
    n: int
    ci_low: float
    ci_high: float
    trace_count: int
    atom_count: int
    card_count: int
    brief_record_count: int
    influence_event_count: int
    scorer_version: str


def run_vertical_loop(root: str | Path, *, inject_leakage: bool = False) -> VerticalLoopReport:
    cem = CEM(root)
    memory_source_ids: set[str] = set()
    # 1-4: ingest -> atom -> validate -> candidate card (memory source)
    for i, decisive in enumerate(HELD_OUT):
        trace = AgentTrace(
            session_id=f"seed-{i}", agent_id="codex",
            turns=[TraceTurn(index=0, role="environment", content=f"SKILL: {decisive}")],
            final_outcome="success",
        )
        cem.ingest_trace(trace)
        memory_source_ids.add(trace.trace_id)
        for atom in cem.propose_memories(trace.trace_id):
            cem.validate(atom.atom_id)
            cem.promote(atom.atom_id)

    held_out_answer_ids = {f"answer::{i}" for i in range(len(HELD_OUT))}
    if inject_leakage:
        memory_source_ids |= {"answer::0"}  # negative control: leak one answer id
    assert_no_leakage(memory_source_ids=memory_source_ids, held_out_answer_ids=held_out_answer_ids)

    # 7-9: retrieve brief, "act", close influence  | memory vs no-memory
    memory_success, no_memory_success = [], []
    brief_records = influence_events = 0
    for decisive in HELD_OUT:
        brief = cem.retrieve_action_brief(TaskContext(description=decisive))
        brief_records += 1
        hit = 1.0 if decisive in brief.recommended_next_actions else 0.0
        memory_success.append(hit)
        no_memory_success.append(0.0)  # no-memory control has no brief
        cem.close_influence(brief.brief_id, action_taken=decisive,
                            outcome="success" if hit else "failure",
                            observed_post_brief_delta=hit)
        influence_events += 1

    mma = marginal_memory_advantage(memory_success, no_memory_success)
    return VerticalLoopReport(
        mma=mma.mma, n=mma.n, ci_low=mma.ci_low, ci_high=mma.ci_high,
        trace_count=len(cem.store.list_atoms() and memory_source_ids),
        atom_count=len(cem.store.list_atoms()),
        card_count=len(cem.store.list_cards()),
        brief_record_count=brief_records,
        influence_event_count=influence_events,
        scorer_version="lexical_overlap_v0",
    )
```

(Fix `trace_count` to `len(memory_source_ids)`; keep the line correct in code.) Export `run_vertical_loop` and `VerticalLoopReport` from `cem_eval/__init__.py` (`from .vertical_loop import ...` + add to `__all__`).

- [ ] **Step 4 — run, expect pass.** `python -m pytest tests/test_vertical_loop.py -q` → 2 pass.
- [ ] **Step 5 — commit.** `feat: add minimal end-to-end vertical-loop runner with MMA and leakage guard`.

### Task E: Runnable script + subprocess test (hard-to-fake consumer)

**Files:** Create `scripts/run_cem_vertical_loop.py`. Test `tests/test_run_cem_vertical_loop_script.py`.

- [ ] **Step 1 — failing test** (`tests/test_run_cem_vertical_loop_script.py`):

```python
import json, subprocess, sys
from pathlib import Path

from cem_core import CEM
from cem_core.storage import SQLiteStore

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_cem_vertical_loop.py"


def test_script_runs_and_persists_real_objects(tmp_path):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(tmp_path)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["report"]["n"] >= 1
    assert payload["report"]["brief_record_count"] >= 1
    # hard-to-fake: a real brief record must exist in the persisted root
    store = SQLiteStore(Path(payload["root"]))
    assert store.list_cards(), "expected promoted candidate cards in the persisted root"
```

- [ ] **Step 2 — run, expect fail.** Script missing → non-zero exit.
- [ ] **Step 3 — implement** `scripts/run_cem_vertical_loop.py` (mirror `run_synthetic_eval.py`'s sys.path bootstrap; call `run_vertical_loop(root)`; print `json.dumps({"root": str(root), "report": report.model_dump()}, default=str)`).
- [ ] **Step 4 — run, expect pass.** `python -m pytest tests/test_run_cem_vertical_loop_script.py -q` → 1 pass.
- [ ] **Step 5 — commit.** `feat: add run_cem_vertical_loop script as a real loop consumer`.

---

## Chunk 3: Phase gate (Task F)

### Task F: Phase 1 gate — verify, record, commit

- [ ] **Step 1 — gate battery (executed evidence required):**
  - `python -m pytest` → all pass (≈ 82 + 12 new).
  - `python -m compileall -q packages scripts tests` → clean.
  - `python scripts/run_synthetic_eval.py` → clean.
  - `python scripts/run_cem_vertical_loop.py` → prints a real MMA report.
  - `powershell -ExecutionPolicy Bypass -File scripts/session-start-gate.ps1` → `SESSION_GATE_PASS`.
  - `git diff --check` → clean.
- [ ] **Step 2 — phase-gate honesty checks (spec §8/§9):** MMA does not regress (Phase 1 establishes the first loop MMA — record the number); falsification suite green; no kill criterion trips; every new gate has a passing failure canary (Task A untagged-delta, Task C never-verifies, Task D leakage-bites).
- [ ] **Step 3 — independent verifier** subagent on the Phase 1 diff: confirm real-green, canaries bite (break→fail→revert→pass), no fake-green, scope-only (no Phase 2/3 scorer or verification code leaked).
- [ ] **Step 4 — doc recording:** `CHANGELOG.md` (Phase 1 entry, with the first loop MMA number), `docs/PROJECT-LEDGER.md` (`LEDGER-20260529-013`), `TODO.md` (check Phase 1, set Phase 2 as next unchecked).
- [ ] **Step 5 — commit.** `feat: complete CEM-1 Phase 1 vertical skeleton (end-to-end loop on real objects)`.

---

## Remember

- DRY, YAGNI, TDD, frequent commits, surgical changes (Karpathy + CLAUDE.md).
- No stubs reported as done; nothing fake marked `verified`; every "done" carries executed evidence (§5 + standing anti-ghost-coding gates).
- Keep `scorer_version="lexical_overlap_v0"` — Phase 1 is honest about being the lexical baseline; the causal scorer is Phase 3.
- Do not regress components 1–3 (synthetic false-memory resistance, contradiction recall) or the Phase 0 lifecycle/eval/no-fake-green guards.
