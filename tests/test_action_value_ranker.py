"""Phase 3 action-value retrieval: the transparent feature ranker (action_value_v1).

These are the RED canaries for the ranker that replaces the bare lexical-overlap
scorer. Each proves one property of "rank by action value, not similarity":
the verified-lift prior dominates similarity, the prior stays genuinely disabled
until a passed probe exists, the per-card breakdown is a faithful audit of the
ranking, penalties never silently drop a relevant card, and the recency term
survives legacy tz-naive anchors.

Fixtures control every feature so the primary canary isolates the lift term:
card A is given a fresh ``valid_from`` so its recency matches the verified card B
(which gets ``last_validated_at`` from verification), leaving the measured lift as
the only thing that can flip the ranking.
"""
from datetime import datetime, timedelta

import pytest

from cem_core import CEM, TaskContext
from cem_core.models import ExperienceCard, VerificationResult, utc_now

# Task whose haystack the cards overlap to varying degrees.
TASK = "deploy the service with rollback enabled safely"


def _make_card(cem, *, title, template, use_when="deploy", check_first=None, confidence=0.5):
    card = ExperienceCard(
        title=title,
        use_when=use_when,
        action_brief_template=template,
        check_first=list(check_first or []),
        evidence_atom_ids=[],
        confidence_score=confidence,
    )
    cem.store.save_card(card)
    return card


def _verify(cem, card, lift):
    # The ONLY real path that sets measured_lift + promotion_status="verified"
    # + last_validated_at. A synthetic passed result stands in for a real probe.
    cem.apply_verification_result(
        VerificationResult(
            probe_id="probe-test", card_id=card.card_id, measured_lift=lift, passed=True
        )
    )
    return cem.store.get_card(card.card_id)


def test_verified_high_lift_outranks_lexically_closer_unverified(tmp_path):
    cem = CEM(tmp_path)
    # Card A: lexically CLOSER (more matching terms) but unverified.
    card_a = _make_card(
        cem,
        title="deploy service rollback enabled safely runbook",
        template="deploy the service with rollback enabled safely",
    )
    # Equalize recency with B (which earns last_validated_at on verification) so the
    # measured-lift term is the only thing that can flip the ranking.
    card_a.valid_from = utc_now()
    cem.store.save_card(card_a)

    # Card B: lexically WEAKER (fewer matching terms) but verified with measured lift.
    card_b = _make_card(cem, title="rollback note", template="rollback")
    _verify(cem, card_b, 0.40)

    brief = cem.retrieve_action_brief(TaskContext(description=TASK), max_cards=5)

    assert brief.applicable_card_ids[0] == card_b.card_id  # action value beats similarity
    assert brief.expected_action_delta_source == "probe_verified"
    assert brief.expected_action_delta == pytest.approx(0.40)
    assert brief.scorer_version == "action_value_v1"
    assert brief.score_breakdown_by_card[card_b.card_id]["verified_lift_prior"] == pytest.approx(0.40)
    assert brief.score_breakdown_by_card[card_a.card_id]["verified_lift_prior"] == 0.0


def test_unverified_only_has_zero_lift_and_observational_source(tmp_path):
    cem = CEM(tmp_path)
    _make_card(cem, title="deploy service safely", template="deploy safely", confidence=0.7)
    _make_card(cem, title="rollback enabled note", template="rollback enabled", confidence=0.4)

    brief = cem.retrieve_action_brief(TaskContext(description=TASK))

    assert brief.applicable_card_ids, "both cards lexically match the task"
    for feats in brief.score_breakdown_by_card.values():
        assert feats["verified_lift_prior"] == 0.0  # prior disabled with no passed probe
    assert brief.expected_action_delta_source == "observational_unverified"
    assert brief.expected_action_delta == pytest.approx(0.7)  # max confidence of selected


def test_breakdown_weighted_terms_sum_to_total(tmp_path):
    cem = CEM(tmp_path)
    verified = _make_card(cem, title="deploy rollback safely", template="deploy rollback safely")
    _verify(cem, verified, 0.5)
    contradicted = _make_card(cem, title="deploy service enabled", template="deploy service enabled")
    contradicted.contradicts_card_ids = [verified.card_id]  # one live conflict in-scope
    cem.store.save_card(contradicted)
    near_expiry = _make_card(cem, title="rollback enabled safely", template="rollback enabled safely")
    near_expiry.valid_until = utc_now() + timedelta(days=3)  # inside the staleness window
    cem.store.save_card(near_expiry)

    brief = cem.retrieve_action_brief(TaskContext(description=TASK))

    assert brief.score_breakdown_by_card, "expected a mixed set to be selected"
    for feats in brief.score_breakdown_by_card.values():
        weighted_sum = (
            feats["weighted_precondition"]
            + feats["weighted_lexical"]
            + feats["weighted_verified_lift"]
            + feats["weighted_recency"]
            + feats["weighted_contradiction"]
            + feats["weighted_staleness"]
        )
        assert weighted_sum == pytest.approx(feats["total"])
        for key in (
            "precondition_match",
            "lexical_overlap",
            "verified_lift_prior",
            "recency_temporal",
            "contradiction_penalty",
            "staleness_penalty",
            "total",
        ):
            assert key in feats


def test_contradicted_verified_card_survives_single_conflict(tmp_path):
    cem = CEM(tmp_path)
    verified = _make_card(cem, title="deploy rollback safely enabled", template="deploy rollback safely enabled")
    verified = _verify(cem, verified, 0.40)
    peer = _make_card(cem, title="deploy service rollback safely", template="deploy service rollback safely")
    # Bidirectional live contradiction between two in-scope candidates.
    verified.contradicts_card_ids = [peer.card_id]
    peer.contradicts_card_ids = [verified.card_id]
    cem.store.save_card(verified)
    cem.store.save_card(peer)

    brief = cem.retrieve_action_brief(TaskContext(description=TASK))

    ids = brief.applicable_card_ids
    assert verified.card_id in ids  # relevance-keyed gate does not drop a penalized card
    feats = brief.score_breakdown_by_card[verified.card_id]
    assert feats["contradiction_penalty"] > 0
    assert feats["weighted_contradiction"] < 0
    assert ids.index(verified.card_id) < ids.index(peer.card_id)  # lift still wins


def test_naive_anchor_does_not_raise(tmp_path):
    cem = CEM(tmp_path)
    card = _make_card(cem, title="deploy rollback safely", template="deploy rollback safely")
    card.last_validated_at = datetime(2026, 1, 1, 0, 0, 0)  # tz-naive legacy value, no validator
    cem.store.save_card(card)

    brief = cem.retrieve_action_brief(TaskContext(description=TASK))  # must not raise TypeError

    feats = brief.score_breakdown_by_card[card.card_id]
    assert 0.0 <= feats["recency_temporal"] <= 1.0
