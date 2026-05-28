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
