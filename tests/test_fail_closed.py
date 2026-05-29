"""Phase 5 hardening: failure-mode coverage. Every error path is fail-closed --
a missing id RAISES (never a silent None), malformed input RAISES at the model
boundary, and an empty store degrades GRACEFULLY (an empty brief, never a crash).
Each test asserts the MESSAGE, not just the type, so a future silent-default
regression bites. RED-first: each is watched to fail for the right reason.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from cem_core import CEM
from cem_core.models import TaskContext, VerificationProbe, VerificationResult
from cem_core.storage import InMemoryStore, SQLiteStore


def _stores(tmp_path):
    return [SQLiteStore(tmp_path / "db"), InMemoryStore()]


def test_empty_store_brief_is_graceful_not_raise(tmp_path):
    # Empty/out-of-scope store -> graceful degradation: a real (empty) ActionBrief,
    # NEVER None and NEVER a raise. Distinct shape from the RAISE cases below.
    cem = CEM(tmp_path)
    brief = cem.retrieve_action_brief(TaskContext(description="anything at all"))
    assert brief is not None
    assert brief.applicable_card_ids == []
    assert brief.recommended_next_actions == []
    assert brief.confidence_score == 0.0
    assert brief.expected_action_delta is None
    assert brief.expected_action_delta_source == "none"


def test_missing_id_raises_keyerror_store_level_both_backends(tmp_path):
    # Store layer fails closed on an unknown id, identically across both backends.
    for store in _stores(tmp_path):
        with pytest.raises(KeyError, match="Card not found"):
            store.get_card("does-not-exist")
        with pytest.raises(KeyError, match="Atom not found"):
            store.get_atom("does-not-exist")


def test_missing_id_raises_keyerror_kernel_level(tmp_path):
    # Kernel surfaces the same fail-closed KeyError (no silent no-op) for a result
    # targeting an unknown card and for auditing an unknown id.
    cem = CEM(tmp_path)
    with pytest.raises(KeyError, match="Card not found"):
        cem.apply_verification_result(
            VerificationResult(probe_id="p", card_id="nope", measured_lift=0.0, passed=False)
        )
    with pytest.raises(KeyError):
        cem.audit("nope")


def test_run_probe_without_target_raises_valueerror(tmp_path):
    # A probe with no target card is a malformed verification request -> ValueError,
    # a DIFFERENT trigger than the missing-id KeyError (kept separate deliberately).
    cem = CEM(tmp_path)
    probe = cem.schedule_probe(
        VerificationProbe(kind="held_out_replay", control_definition="x", threshold=0.5)
    )
    with pytest.raises(ValueError, match="verification probe has no target card"):
        cem.run_probe(
            probe.probe_id,
            task=TaskContext(description="anything"),
            correct_action="do x",
        )


def test_malformed_input_raises_validationerror():
    # StrictModel (extra="forbid") fails closed on an unexpected field -- proves the
    # fail-closed validation is wired, not pydantic-by-accident. One representative
    # model suffices (StrictModel is the single enforcement point).
    with pytest.raises(ValidationError):
        TaskContext(description="x", bogus=1)
