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
