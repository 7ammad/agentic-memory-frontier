# CEM-1 Phase 0 (Contract Lock) Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Lock the CEM-1 schema, lifecycle rules, eval protocol, no-fake-green gates, and storage migration so every later phase builds against a fixed contract — with no capability change shipped beyond the asserted-promotion fix.

**Architecture:** Add four new Pydantic evidence primitives + defaulted field extensions (storage is SQLite JSON-blob `payload TEXT`, so adding defaulted fields is migration-free); separate `promote()` (creates a *candidate* card) from a new `apply_verification_result()` (the only path that may set `promotion_status="verified"`); add dedicated SQLite tables for the query-heavy primitives; encode the MMA/baseline/leakage contract as a `cem_eval.eval_protocol` module; and ship a static no-fake-green guard plus failure canaries for every new gate.

**Tech Stack:** Python 3.14, Pydantic v2 (`StrictModel` = `extra="forbid"`), SQLite (`sqlite3`, WAL, `payload TEXT` + `model_dump_json()`), pytest (pythonpath wired in `pyproject.toml`).

**Source spec:** `docs/2026-05-28-causal-experience-memory-full-program-design.md` §6 (schema), §8 (Phase 0 definition), §4.2 (lifecycle rules), §4.5 (influence ledger), §7 (baseline ladder), §9 (kill thresholds), §10 (leakage + canaries), §5 (anti-scaffolding contract).

**Verified current state (2026-05-28, read this session):**
- `promotion_status` lives on `ExperienceAtom` (`models.py:100-106`); `ExperienceCard` (`models.py:110`) has **no** status field. `audit()` hardcodes a card's status to `"verified"` (`kernel.py:200`).
- `promote()` flips the atom to `"verified"` unconditionally at `kernel.py:84` (merge branch) and `kernel.py:105` (new-card branch) — the asserted-promotion bug.
- **No test asserts `promotion_status == "verified"`** anywhere (grep over `tests/`); the validator — not `promote()` — sets `candidate`/`quarantined`/`deprecated`. So the lifecycle fix does not fight the current suite.
- `ActionBrief` (`models.py:136`) carries only `expected_action_delta: float | None = None` (`models.py:146`).
- Storage has two backends implementing the `CEMStore` Protocol (`storage.py:10-23`): `SQLiteStore` (tables: traces, atoms, cards, validations, validation_decisions) and `InMemoryStore`. Both must gain the new primitives.
- `cem_eval` is importable (`tests/test_cem_kernel.py:417` does `from cem_eval.synthetic_corruption import ...`).

**Non-goals for Phase 0 (deferred to later phases, do NOT build here):** the probe *runner*, negative-control *injector*, the action-value *scorer*, consolidation, and the MMA *exam run*. Phase 0 locks contracts and fixes the asserted-promotion bug only. `apply_verification_result()` is the contract entry point; nothing auto-generates a `VerificationResult` yet, so after Phase 0 **no card is ever auto-verified** — which is the correct honest state.

---

## Chunk 1: Schema + storage contract

### Task 1: `ConfidenceInterval` + four evidence primitives

**Files:**
- Modify: `packages/cem-core/src/cem_core/models.py` (add `ConfidenceInterval` after `SourceSpan` line 29; append the four new models after `MemoryAudit` line 191)
- Modify: `packages/cem-core/src/cem_core/__init__.py` (export new models)
- Test: `tests/test_evidence_models.py` (new)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_evidence_models.py
from cem_core.models import (
    ActionBriefRecord,
    ActionInfluenceEvent,
    ConfidenceInterval,
    VerificationProbe,
    VerificationResult,
)


def test_verification_probe_roundtrips_and_defaults_status():
    probe = VerificationProbe(
        kind="held_out_replay",
        target_card_id="card_x",
        control_definition="no-memory control on held-out task T",
        threshold=0.05,
    )
    assert probe.probe_id.startswith("probe_")
    assert probe.status == "scheduled"
    assert VerificationProbe.model_validate_json(probe.model_dump_json()) == probe


def test_verification_result_carries_ci_and_pass_flag():
    result = VerificationResult(
        probe_id="probe_x",
        card_id="card_x",
        measured_lift=0.12,
        measured_lift_ci=ConfidenceInterval(low=0.02, high=0.22),
        passed=True,
        evidence_pointer="influence_123",
    )
    assert result.result_id.startswith("vresult_")
    assert result.measured_lift_ci.low == 0.02
    assert VerificationResult.model_validate_json(result.model_dump_json()) == result


def test_action_brief_record_and_influence_event_link_by_influence_id():
    record = ActionBriefRecord(
        task_id="t1",
        candidate_card_ids=["card_a", "card_b"],
        selected_card_ids=["card_a"],
        score_breakdown_by_card={"card_a": {"precondition_match": 1.0}},
        scorer_version="phase0-contract",
        expected_action_delta_source="none",
        influence_id="influence_123",
    )
    event = ActionInfluenceEvent(
        influence_id="influence_123",
        brief_id=record.brief_id,
        task_id="t1",
        action_taken="selected assignment_group first",
        outcome="success",
        observed_post_brief_delta=0.3,
    )
    assert record.brief_id.startswith("brief_")
    assert event.influence_id == record.influence_id
    assert ActionBriefRecord.model_validate_json(record.model_dump_json()) == record
    assert ActionInfluenceEvent.model_validate_json(event.model_dump_json()) == event


def test_confidence_interval_rejects_extra_fields():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ConfidenceInterval(low=0.0, high=1.0, mean=0.5)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_evidence_models.py -v`
Expected: FAIL — `ImportError` (models not defined).

- [ ] **Step 3: Write minimal implementation**

In `models.py`, after `SourceSpan` (line 29):

```python
class ConfidenceInterval(StrictModel):
    low: float
    high: float
```

In `models.py`, after `MemoryAudit` (end of file):

```python
ExpectedActionDeltaSource = Literal[
    "none",
    "observational_unverified",
    "probe_verified",
    "heldout_eval",
]


class VerificationProbe(StrictModel):
    probe_id: str = Field(default_factory=lambda: new_id("probe"))
    kind: Literal["held_out_replay", "staleness", "contradiction", "negative_control"]
    target_card_id: str | None = None
    target_atom_id: str | None = None
    control_definition: str
    threshold: float
    status: Literal["scheduled", "run", "skipped"] = "scheduled"
    created_at: datetime = Field(default_factory=utc_now)


class VerificationResult(StrictModel):
    result_id: str = Field(default_factory=lambda: new_id("vresult"))
    probe_id: str
    card_id: str
    measured_lift: float
    measured_lift_ci: ConfidenceInterval | None = None
    passed: bool
    evidence_pointer: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class ActionBriefRecord(StrictModel):
    brief_id: str = Field(default_factory=lambda: new_id("brief"))
    task_id: str | None = None
    candidate_card_ids: list[str] = Field(default_factory=list)
    selected_card_ids: list[str] = Field(default_factory=list)
    score_breakdown_by_card: dict[str, dict[str, float]] = Field(default_factory=dict)
    scorer_version: str
    expected_action_delta_source: ExpectedActionDeltaSource = "none"
    influence_id: str
    created_at: datetime = Field(default_factory=utc_now)


class ActionInfluenceEvent(StrictModel):
    influence_id: str
    brief_id: str
    task_id: str | None = None
    action_taken: str | None = None
    outcome: Literal["success", "failure", "partial", "unknown"] = "unknown"
    observed_post_brief_delta: float | None = None
    counterfactual_method: str | None = None
    baseline_comparison: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
```

In `__init__.py`, add the five names to the imports from `.models` and to `__all__` (open the file; mirror the existing export pattern).

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_evidence_models.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add packages/cem-core/src/cem_core/models.py packages/cem-core/src/cem_core/__init__.py tests/test_evidence_models.py
git commit -m "feat: add cem-1 evidence primitives (probe, result, brief record, influence event)"
```

---

### Task 2: Field extensions on `ActionBrief` and `ExperienceCard`

**Files:**
- Modify: `packages/cem-core/src/cem_core/models.py` (`ActionBrief` line 136-146; `ExperienceCard` line 110-124)
- Test: `tests/test_evidence_models.py` (extend)

- [ ] **Step 1: Write the failing test** (append to `tests/test_evidence_models.py`)

```python
def test_action_brief_new_fields_default_safely():
    from cem_core.models import ActionBrief

    brief = ActionBrief(
        applicable_card_ids=[],
        why_applicable=[],
        preconditions_to_check=[],
        recommended_next_actions=[],
        risks_and_failure_modes=[],
        stale_or_contested_memory_ids_to_ignore=[],
        evidence_links=[],
        confidence_score=0.0,
    )
    assert brief.brief_id.startswith("brief_")
    assert brief.influence_id is None
    assert brief.scorer_version is None
    assert brief.expected_action_delta_source == "none"
    assert brief.score_breakdown_by_card == {}


def test_experience_card_lifecycle_fields_default_to_candidate():
    from cem_core.models import ExperienceCard

    card = ExperienceCard(
        title="t",
        use_when="w",
        evidence_atom_ids=["atom_1"],
        confidence_score=0.5,
        action_brief_template="do x",
    )
    assert card.promotion_status == "candidate"
    assert card.measured_lift is None
    assert card.measured_lift_ci is None
    assert card.verification_result_ids == []
    assert card.deactivated_at is None
    assert card.deactivated_reason is None
    assert card.superseded_by_card_ids == []


def test_old_shape_card_json_loads_with_defaults():
    # Backward-compat canary: a card persisted before Phase 0 (no new fields)
    # must still load, defaulting to candidate.
    from cem_core.models import ExperienceCard

    legacy = (
        '{"card_id":"card_legacy","title":"t","use_when":"w","do":[],"do_not":[],'
        '"check_first":[],"evidence_atom_ids":["atom_1"],"confidence_score":0.5,'
        '"known_exceptions":[],"valid_from":null,"valid_until":null,'
        '"tested_by_probe_ids":[],"last_validated_at":null,"action_brief_template":"do x"}'
    )
    card = ExperienceCard.model_validate_json(legacy)
    assert card.promotion_status == "candidate"
    assert card.measured_lift is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_evidence_models.py -k "default_safely or lifecycle_fields or old_shape" -v`
Expected: FAIL — new attributes missing.

- [ ] **Step 3: Write minimal implementation**

In `ExperienceCard` (after `action_brief_template`, line 124), add:

```python
    promotion_status: Literal[
        "candidate",
        "verified",
        "deprecated",
        "superseded",
        "quarantined",
    ] = "candidate"
    measured_lift: float | None = None
    measured_lift_ci: ConfidenceInterval | None = None
    verification_result_ids: list[str] = Field(default_factory=list)
    deactivated_at: datetime | None = None
    deactivated_reason: str | None = None
    superseded_by_card_ids: list[str] = Field(default_factory=list)
```

In `ActionBrief` (after `expected_action_delta`, line 146), add:

```python
    brief_id: str = Field(default_factory=lambda: new_id("brief"))
    influence_id: str | None = None
    scorer_version: str | None = None
    expected_action_delta_source: ExpectedActionDeltaSource = "none"
    score_breakdown_by_card: dict[str, dict[str, float]] = Field(default_factory=dict)
```

(`ConfidenceInterval` and `ExpectedActionDeltaSource` are defined in Task 1; ensure `ExpectedActionDeltaSource` is declared above `ActionBrief` or move its definition up near the top with `ConfidenceInterval`.)

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_evidence_models.py -v`
Expected: PASS (all tests, including Task 1's).

- [ ] **Step 5: Run the full suite to confirm no regressions from defaulted fields**

Run: `python -m pytest -q`
Expected: PASS (defaulted fields are additive; existing constructors unaffected).

- [ ] **Step 6: Commit**

```bash
git add packages/cem-core/src/cem_core/models.py tests/test_evidence_models.py
git commit -m "feat: extend ActionBrief and ExperienceCard with cem-1 evidence + lifecycle fields"
```

---

### Task 3: Storage tables + CRUD for the four primitives

**Files:**
- Modify: `packages/cem-core/src/cem_core/storage.py` (Protocol line 10-23; `SQLiteStore._init_db` line 39-66 + new methods; `InMemoryStore` new methods)
- Test: `tests/test_storage_evidence.py` (new)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_storage_evidence.py
import pytest

from cem_core.models import (
    ActionBriefRecord,
    ActionInfluenceEvent,
    VerificationProbe,
    VerificationResult,
)
from cem_core.storage import InMemoryStore, SQLiteStore


def _stores(tmp_path):
    return [SQLiteStore(tmp_path / "db"), InMemoryStore()]


def test_probe_and_result_roundtrip_in_both_backends(tmp_path):
    for store in _stores(tmp_path):
        probe = VerificationProbe(
            kind="negative_control",
            target_card_id="card_x",
            control_definition="injected false memory must not promote",
            threshold=0.0,
        )
        store.save_probe(probe)
        assert store.get_probe(probe.probe_id) == probe

        result = VerificationResult(
            probe_id=probe.probe_id, card_id="card_x", measured_lift=0.1, passed=True
        )
        store.save_verification_result(result)
        assert store.list_verification_results("card_x") == [result]


def test_brief_record_and_influence_event_roundtrip(tmp_path):
    for store in _stores(tmp_path):
        record = ActionBriefRecord(
            scorer_version="phase0", influence_id="influence_1", task_id="t1"
        )
        store.save_action_brief_record(record)
        assert store.get_action_brief_record(record.brief_id) == record

        event = ActionInfluenceEvent(influence_id="influence_1", brief_id=record.brief_id)
        store.save_action_influence_event(event)
        assert store.list_action_influence_events("influence_1") == [event]


def test_missing_probe_raises_keyerror(tmp_path):
    for store in _stores(tmp_path):
        with pytest.raises(KeyError):
            store.get_probe("nope")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_storage_evidence.py -v`
Expected: FAIL — `AttributeError` (methods not defined).

- [ ] **Step 3: Write minimal implementation**

In `storage.py`, extend the `CEMStore` Protocol (after line 23) with:

```python
    def save_probe(self, probe: VerificationProbe) -> None: ...
    def get_probe(self, probe_id: str) -> VerificationProbe: ...
    def list_probes(self) -> list[VerificationProbe]: ...
    def save_verification_result(self, result: VerificationResult) -> None: ...
    def list_verification_results(self, card_id: str) -> list[VerificationResult]: ...
    def save_action_brief_record(self, record: ActionBriefRecord) -> None: ...
    def get_action_brief_record(self, brief_id: str) -> ActionBriefRecord: ...
    def save_action_influence_event(self, event: ActionInfluenceEvent) -> None: ...
    def list_action_influence_events(self, influence_id: str) -> list[ActionInfluenceEvent]: ...
```

Add the imports at the top of `storage.py`:

```python
from .models import (
    ActionBriefRecord,
    ActionInfluenceEvent,
    AgentTrace,
    ExperienceAtom,
    ExperienceCard,
    ValidationDecision,
    ValidationResult,
    VerificationProbe,
    VerificationResult,
)
```

In `SQLiteStore._init_db`, append to the `executescript` block:

```sql
                CREATE TABLE IF NOT EXISTS verification_probes (
                    probe_id TEXT PRIMARY KEY,
                    target_card_id TEXT,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS verification_results (
                    result_id TEXT PRIMARY KEY,
                    card_id TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS action_brief_records (
                    brief_id TEXT PRIMARY KEY,
                    influence_id TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS action_influence_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    influence_id TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
```

Add `SQLiteStore` methods (follow the existing `save_card`/`get_card`/`list_validations` patterns — `INSERT OR REPLACE` for keyed rows, ordered `SELECT` for lists, `KeyError` on missing):

```python
    def save_probe(self, probe: VerificationProbe) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO verification_probes(probe_id, target_card_id, payload) VALUES(?, ?, ?)",
                (probe.probe_id, probe.target_card_id, probe.model_dump_json()),
            )

    def get_probe(self, probe_id: str) -> VerificationProbe:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM verification_probes WHERE probe_id = ?", (probe_id,)
            ).fetchone()
        if row is None:
            raise KeyError(f"Probe not found: {probe_id}")
        return VerificationProbe.model_validate_json(row[0])

    def list_probes(self) -> list[VerificationProbe]:
        with self._connect() as conn:
            rows = conn.execute("SELECT payload FROM verification_probes").fetchall()
        return [VerificationProbe.model_validate_json(row[0]) for row in rows]

    def save_verification_result(self, result: VerificationResult) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO verification_results(result_id, card_id, payload) VALUES(?, ?, ?)",
                (result.result_id, result.card_id, result.model_dump_json()),
            )

    def list_verification_results(self, card_id: str) -> list[VerificationResult]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM verification_results WHERE card_id = ? ORDER BY rowid",
                (card_id,),
            ).fetchall()
        return [VerificationResult.model_validate_json(row[0]) for row in rows]

    def save_action_brief_record(self, record: ActionBriefRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO action_brief_records(brief_id, influence_id, payload) VALUES(?, ?, ?)",
                (record.brief_id, record.influence_id, record.model_dump_json()),
            )

    def get_action_brief_record(self, brief_id: str) -> ActionBriefRecord:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM action_brief_records WHERE brief_id = ?", (brief_id,)
            ).fetchone()
        if row is None:
            raise KeyError(f"Action brief record not found: {brief_id}")
        return ActionBriefRecord.model_validate_json(row[0])

    def save_action_influence_event(self, event: ActionInfluenceEvent) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO action_influence_events(influence_id, payload) VALUES(?, ?)",
                (event.influence_id, event.model_dump_json()),
            )

    def list_action_influence_events(self, influence_id: str) -> list[ActionInfluenceEvent]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM action_influence_events WHERE influence_id = ? ORDER BY id",
                (influence_id,),
            ).fetchall()
        return [ActionInfluenceEvent.model_validate_json(row[0]) for row in rows]
```

Add the mirror methods to `InMemoryStore` (dicts keyed by id; lists for the append-only events), following the existing in-memory patterns. Initialize the new containers in `__init__`:

```python
        self._probes: dict[str, str] = {}
        self._verification_results: list[tuple[str, str]] = []
        self._action_brief_records: dict[str, str] = {}
        self._action_influence_events: list[tuple[str, str]] = []
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_storage_evidence.py -v`
Expected: PASS (3 tests, both backends).

- [ ] **Step 5: Commit**

```bash
git add packages/cem-core/src/cem_core/storage.py tests/test_storage_evidence.py
git commit -m "feat: persist cem-1 verification + influence primitives in both store backends"
```

---

## Chunk 2: Lifecycle rules, eval protocol, no-fake-green gates

### Task 4: Lifecycle rules — `promote()` candidate semantics, `apply_verification_result()`, honest `audit()`

**Files:**
- Modify: `packages/cem-core/src/cem_core/kernel.py` (`promote()` lines 84 & 105; `audit()` line 200; add `apply_verification_result()`; import `VerificationResult`)
- Test: `tests/test_lifecycle_rules.py` (new)

**Contract being locked (spec §4.2):** `promote()` means *create_or_update_candidate_card()* — it may **never** set `verified`. Only `apply_verification_result()` with a `passed=True` result may set a card `promotion_status="verified"`. This is the structural fix for the asserted-promotion bug.

- [ ] **Step 1: Write the failing tests (incl. failure canaries)**

```python
# tests/test_lifecycle_rules.py
from cem_core import AgentTrace, CEM, TraceTurn
from cem_core.models import VerificationResult, ConfidenceInterval


def _promote_one(cem):
    trace = AgentTrace(
        session_id="s1",
        agent_id="codex",
        turns=[TraceTurn(index=0, role="environment", content="SKILL: set assignment_group before assignee")],
        final_outcome="success",
    )
    cem.ingest_trace(trace)
    atom = cem.propose_memories(trace.trace_id)[0]
    cem.validate(atom.atom_id)
    return cem.promote(atom.atom_id), atom


def test_promote_never_yields_verified(tmp_path):
    # Failure canary for the asserted-promotion bug (kernel.py:84/:105).
    cem = CEM(tmp_path)
    card, atom = _promote_one(cem)
    assert card is not None
    assert card.promotion_status == "candidate"
    assert cem.store.get_atom(atom.atom_id).promotion_status != "verified"


def test_apply_verification_result_verifies_only_on_pass(tmp_path):
    cem = CEM(tmp_path)
    card, _ = _promote_one(cem)
    result = VerificationResult(
        probe_id="probe_1",
        card_id=card.card_id,
        measured_lift=0.2,
        measured_lift_ci=ConfidenceInterval(low=0.05, high=0.35),
        passed=True,
    )
    verified = cem.apply_verification_result(result)
    assert verified.promotion_status == "verified"
    assert verified.measured_lift == 0.2
    assert result.result_id in verified.verification_result_ids
    assert cem.store.list_verification_results(card.card_id) == [result]


def test_apply_verification_result_rejects_failed_probe(tmp_path):
    # Failure canary: a non-passing probe must NOT verify (the gate must bite).
    cem = CEM(tmp_path)
    card, _ = _promote_one(cem)
    failed = VerificationResult(
        probe_id="probe_1", card_id=card.card_id, measured_lift=-0.1, passed=False
    )
    out = cem.apply_verification_result(failed)
    assert out.promotion_status != "verified"
    assert failed.result_id in out.verification_result_ids  # evidence still recorded


def test_audit_reports_card_real_status_not_hardcoded(tmp_path):
    # Failure canary for the hardcoded audit status (kernel.py:200).
    cem = CEM(tmp_path)
    card, _ = _promote_one(cem)
    assert cem.audit(card.card_id).promotion_status == "candidate"
    result = VerificationResult(probe_id="p", card_id=card.card_id, measured_lift=0.2, passed=True)
    cem.apply_verification_result(result)
    assert cem.audit(card.card_id).promotion_status == "verified"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_lifecycle_rules.py -v`
Expected: FAIL — `apply_verification_result` missing; `audit` returns hardcoded `"verified"` so the candidate assertion fails.

- [ ] **Step 3: Write minimal implementation**

In `kernel.py`, add `VerificationResult` to the `.models` import. Remove both `atom.promotion_status = "verified"` lines (84, 105). The atom stays `candidate` (it already is, per the guard at lines 70-76). The new card is created with the model default `promotion_status="candidate"`.

Replace the hardcoded `promotion_status="verified"` in the `audit()` card branch (line 200) with the card's real status:

```python
                promotion_status=card.promotion_status,
```

Add the verified-setter method (the only path to `verified`):

```python
    def apply_verification_result(self, result: VerificationResult) -> ExperienceCard:
        card = self.store.get_card(result.card_id)
        self.store.save_verification_result(result)
        if result.result_id not in card.verification_result_ids:
            card.verification_result_ids.append(result.result_id)
        if result.passed:
            card.promotion_status = "verified"
            card.measured_lift = result.measured_lift
            card.measured_lift_ci = result.measured_lift_ci
            card.last_validated_at = utc_now()
        self.store.save_card(card)
        return card
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_lifecycle_rules.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Run the full kernel suite for regressions**

Run: `python -m pytest tests/test_cem_kernel.py tests/test_mcp_tools.py tests/test_multi_agent.py -v`
Expected: PASS. (No existing test asserts a `verified` status, so removing the flips is safe. If `tests/test_mcp_tools.py` asserts a post-promote status, reconcile it to `candidate` — verify first, do not assume. Verified during planning + plan review: no such assertion exists today, so this reconcile is expected to be a no-op.)

- [ ] **Step 6: Commit**

```bash
git add packages/cem-core/src/cem_core/kernel.py tests/test_lifecycle_rules.py
git commit -m "fix: separate promote() from verification; only applied probe results set verified"
```

---

### Task 5: Eval protocol module (MMA + baseline ladder + leakage controls)

**Files:**
- Create: `packages/cem-eval/src/cem_eval/eval_protocol.py`
- Test: `tests/test_eval_protocol.py` (new)

**Contract being locked (spec §7, §9, §10):** the MMA metric, the success bar, the honest baseline ladder (with `human_runbook` flagged as ceiling), the ≥5pp margin, and the leakage rules — all locked *before any scorer tuning* (§11).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_eval_protocol.py
import pytest

from cem_eval.eval_protocol import (
    BASELINE_LADDER,
    LEXICAL_MARGIN_PP,
    MMAResult,
    assert_no_leakage,
    marginal_memory_advantage,
    mma_passes,
)


def test_mma_is_paired_delta_with_ci_and_n():
    memory = [1.0, 1.0, 0.0, 1.0]
    no_memory = [0.0, 1.0, 0.0, 0.0]
    result = marginal_memory_advantage(memory, no_memory)
    assert isinstance(result, MMAResult)
    assert result.n == 4
    assert result.mma == pytest.approx(0.5)
    assert result.ci_low <= result.mma <= result.ci_high


def test_mma_rejects_unpaired_inputs():
    with pytest.raises(ValueError):
        marginal_memory_advantage([1.0, 0.0], [1.0])


def test_baseline_ladder_has_all_ten_and_human_runbook_is_ceiling():
    names = {b.name for b in BASELINE_LADDER}
    assert names == {
        "no_memory",
        "full_context",
        "lexical_overlap",
        "summary",
        "vector_rag",
        "time_aware_rag",
        "temporal_graph",
        "unverified_reflection",
        "cem",
        "human_runbook",
    }
    ceiling = {b.name for b in BASELINE_LADDER if b.is_ceiling}
    must_beat_lexical = {b.name for b in BASELINE_LADDER if b.name == "lexical_overlap"}
    assert ceiling == {"human_runbook"}
    assert LEXICAL_MARGIN_PP == 5.0
    assert must_beat_lexical == {"lexical_overlap"}


def test_leakage_guard_fails_on_overlap():
    # Failure canary: overlapping memory-source and held-out answer ids must raise.
    with pytest.raises(ValueError):
        assert_no_leakage(memory_source_ids={"a", "b"}, held_out_answer_ids={"b", "c"})
    # disjoint sets pass
    assert_no_leakage(memory_source_ids={"a"}, held_out_answer_ids={"c"}) is None


def test_mma_passes_requires_positive_lower_ci():
    # Failure canary for the success-bar gate (spec section 9): a positive mean
    # whose 95% CI straddles zero must NOT pass.
    clean = MMAResult(mma=0.3, n=10, ci_low=0.1, ci_high=0.5)
    straddles_zero = MMAResult(mma=0.3, n=10, ci_low=-0.05, ci_high=0.65)
    assert mma_passes(clean) is True
    assert mma_passes(straddles_zero) is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_eval_protocol.py -v`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Write minimal implementation**

```python
# packages/cem-eval/src/cem_eval/eval_protocol.py
"""Locked CEM-1 evaluation contract (spec sections 7, 9, 10, 11).

This module fixes the proof contract BEFORE any scorer tuning. Phase 4 runs the
exam against this contract; it does not get to move these definitions.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# Pre-registered margin: CEM must beat lexical-overlap retrieval by >= this many
# percentage points of held-out task success (spec section 9), or the
# causal-retrieval thesis is unproven.
LEXICAL_MARGIN_PP: float = 5.0


@dataclass(frozen=True)
class Baseline:
    name: str
    description: str
    is_ceiling: bool = False  # ceiling = upper-bound reference, NOT a must-beat gate


# Spec section 7 — all baselines run honestly on the same held-out tasks.
BASELINE_LADDER: tuple[Baseline, ...] = (
    Baseline("no_memory", "No memory access; the MMA control/denominator."),
    Baseline("full_context", "All allowed prior trace material within the budget; no selectivity."),
    Baseline("lexical_overlap", "Current word-overlap retrieval; CEM must beat it by LEXICAL_MARGIN_PP."),
    Baseline("summary", "Rolling summary of prior traces injected as context."),
    Baseline("vector_rag", "Embedding-similarity retrieval over the trace/card corpus."),
    Baseline("time_aware_rag", "Vector RAG with recency weighting / temporal filtering."),
    Baseline("temporal_graph", "Graph retrieval over entity/event/time links; no causal scorer."),
    Baseline("unverified_reflection", "Self-generated lessons with no verification gate."),
    Baseline("cem", "The full CEM kernel."),
    Baseline("human_runbook", "Hand-written ideal playbook.", is_ceiling=True),
)


@dataclass(frozen=True)
class MMAResult:
    mma: float
    n: int
    ci_low: float
    ci_high: float


def marginal_memory_advantage(
    memory_success: list[float],
    no_memory_success: list[float],
    *,
    z: float = 1.96,
) -> MMAResult:
    """Paired task-level MMA with a 95% CI (spec section 11 forbids a bare mean)."""
    if len(memory_success) != len(no_memory_success):
        raise ValueError("MMA requires paired per-task results of equal length.")
    if not memory_success:
        raise ValueError("MMA requires at least one task.")
    deltas = [m - b for m, b in zip(memory_success, no_memory_success)]
    n = len(deltas)
    mma = sum(deltas) / n
    if n == 1:
        return MMAResult(mma=mma, n=n, ci_low=mma, ci_high=mma)
    var = sum((d - mma) ** 2 for d in deltas) / (n - 1)
    se = math.sqrt(var / n)
    return MMAResult(mma=mma, n=n, ci_low=mma - z * se, ci_high=mma + z * se)


def mma_passes(result: MMAResult) -> bool:
    """Success bar (spec section 9): MMA > 0 AND lower 95% CI > 0."""
    return result.mma > 0.0 and result.ci_low > 0.0


def assert_no_leakage(*, memory_source_ids: set[str], held_out_answer_ids: set[str]) -> None:
    """Spec section 10: memory-source traces and held-out answers must be disjoint."""
    overlap = memory_source_ids & held_out_answer_ids
    if overlap:
        raise ValueError(f"Leakage: memory source overlaps held-out answers: {sorted(overlap)}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_eval_protocol.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add packages/cem-eval/src/cem_eval/eval_protocol.py tests/test_eval_protocol.py
git commit -m "feat: lock cem-1 eval protocol (MMA paired-delta + CI, baseline ladder, leakage guard)"
```

---

### Task 6: No-fake-green guard + failure-canary convention

**Files:**
- Create: `tests/test_no_fake_green_guard.py`
- Reference: `packages/cem-core/src/cem_core/operations.py:234`, `:249` (known offenders — the Correction Capture track, spec §12)

**Contract being locked (spec §10):** a static guard that fails if any monitor/health `_check(...)` call passes a hardcoded literal `True`/`False` as its evaluated value — so the `operations.py:234`/`:249` anti-pattern cannot reappear in *new* code. The two existing offenders are pinned to a frozen allowlist (tracked debt on the separate Correction Capture track); any *new* literal-bool `_check` outside the allowlist fails the test.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_no_fake_green_guard.py
import ast
from pathlib import Path

OPERATIONS = Path("packages/cem-core/src/cem_core/operations.py")

# Frozen tracked-debt allowlist: the known fake-green checks on the Correction
# Capture track (spec section 12). Removing these from operations.py should also
# shrink this set. Any NEW literal-bool _check outside this set fails the test.
ALLOWLISTED_FAKE_GREEN = {"correction_controller_wired", "recent_corrections_recorded"}


def _literal_bool_check_names(source: str) -> set[str]:
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_check"
            and len(node.args) >= 2
            and isinstance(node.args[1], ast.Constant)
            and isinstance(node.args[1].value, bool)
            and isinstance(node.args[0], ast.Constant)
        ):
            names.add(node.args[0].value)
    return names


def test_no_new_fake_green_checks():
    found = _literal_bool_check_names(OPERATIONS.read_text(encoding="utf-8"))
    new_offenders = found - ALLOWLISTED_FAKE_GREEN
    assert not new_offenders, f"New fake-green _check(...) with literal bool: {sorted(new_offenders)}"


def test_guard_detects_a_literal_bool_check():
    # Failure canary: prove the guard actually bites on a fake-green pattern.
    sample = "def f():\n    _check('always_ok', True, 'x')\n"
    assert _literal_bool_check_names(sample) == {"always_ok"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_no_fake_green_guard.py -v`
Expected: First run may FAIL if the allowlist does not match the actual literal arg names. Inspect `operations.py:234`/`:249` and set `ALLOWLISTED_FAKE_GREEN` to the exact check names found. (Verify against source — do not assume the names.)

- [ ] **Step 3: Reconcile the allowlist to the real offender names**

Open `packages/cem-core/src/cem_core/operations.py` around lines 234 and 249, read the literal `_check("<name>", True, ...)` names, and set `ALLOWLISTED_FAKE_GREEN` to exactly those.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_no_fake_green_guard.py -v`
Expected: PASS (2 tests) — guard green on current code, canary proves it bites.

- [ ] **Step 5: Commit**

```bash
git add tests/test_no_fake_green_guard.py
git commit -m "test: add no-fake-green guard blocking new literal-bool health checks"
```

---

### Task 7: Phase 0 gate — verify, record, advance

**Files:**
- Modify: `CHANGELOG.md`, `docs/PROJECT-LEDGER.md`, `TODO.md`

- [ ] **Step 1: Run the full phase gate (spec §8)**

```bash
powershell -ExecutionPolicy Bypass -File scripts/session-start-gate.ps1
python -m pytest -q
python -m compileall -q packages scripts tests
python scripts/run_synthetic_eval.py
git diff --check
```
Expected: session gate `allow`; full pytest PASS; compile clean; synthetic eval clean; no whitespace errors.

- [ ] **Step 2: Record evidence**

Add a `CHANGELOG.md` entry and a `docs/PROJECT-LEDGER.md` ledger entry (`LEDGER-20260528-011`, type `plan-update` + `verification`) noting: contract locked (schema, lifecycle rules, eval protocol, no-fake-green guard, storage migration), the asserted-promotion bug fixed (`promote()` no longer sets `verified`; only `apply_verification_result()` does), and the executed verification commands above with their results.

- [ ] **Step 3: Update `TODO.md`** — check off Phase 0 (Contract lock); set the next unchecked item to Phase 1 (Full vertical skeleton).

- [ ] **Step 4: Commit**

```bash
git add CHANGELOG.md docs/PROJECT-LEDGER.md TODO.md
git commit -m "docs: record cem-1 phase 0 contract lock with executed verification"
```

---

## Phase 0 acceptance (gate must be met with executed evidence)

- [ ] All four evidence primitives + field extensions exist, round-trip through `model_dump_json()`, and are exported from `cem_core`.
- [ ] Both store backends persist/return probes, results, brief records, and influence events; missing keys raise `KeyError`.
- [ ] `promote()` yields a `candidate` card and never `verified` (canary `test_promote_never_yields_verified`).
- [ ] Only `apply_verification_result()` with `passed=True` sets `verified`; a failed probe does not (canary `test_apply_verification_result_rejects_failed_probe`).
- [ ] `audit()` reports a card's real `promotion_status`, not a hardcoded literal.
- [ ] Eval protocol locks MMA (paired delta + CI), the 10-baseline ladder (`human_runbook`=ceiling), the ≥5pp lexical margin, and a leakage guard (canary `test_leakage_guard_fails_on_overlap`).
- [ ] No-fake-green guard passes on current code and provably bites on a literal-bool `_check` (canary `test_guard_detects_a_literal_bool_check`).
- [ ] Full `pytest` + `run_synthetic_eval.py` + session-start gate pass; evidence recorded in `CHANGELOG.md` + `docs/PROJECT-LEDGER.md`.
- [ ] No capability beyond the asserted-promotion fix shipped (no probe runner, no scorer, no consolidation) — Phase 0 is contract-only.
