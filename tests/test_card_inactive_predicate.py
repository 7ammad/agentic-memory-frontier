"""Phase 5 hardening: the shared ``card_is_inactive`` predicate.

Promotes the lifecycle-state test from a private CEM staticmethod to a single
module-level predicate so ``_supersede_stale_cards`` and the eval vertical loop
classify inactivity on the SAME axis (LEDGER Open Follow-Up "two latent
defensive consistency nits"). The behavioural canary proves nit (a) actually
bites without the shared predicate.
"""
from __future__ import annotations

from cem_core import CEM
from cem_core.kernel import card_is_inactive
from cem_core.models import ExperienceAtom, ExperienceCard, utc_now


def _card(promotion_status: str = "candidate", *, deactivated_at=None) -> ExperienceCard:
    return ExperienceCard(
        title="db host order",
        use_when="db config",
        evidence_atom_ids=["atom-x"],
        confidence_score=0.9,
        action_brief_template="use db host",
        promotion_status=promotion_status,
        deactivated_at=deactivated_at,
    )


def _atom(
    content: str,
    *,
    epistemic_type: str = "observation",
    atom_id: str | None = None,
    superseded_by: list[str] | None = None,
    promotion_status: str = "candidate",
) -> ExperienceAtom:
    kwargs: dict[str, object] = dict(
        source_trace_ids=["trace-1"],
        source_turn_ids=["turn-1"],
        source_spans=[],
        source_agent_id="codex",
        source_session_id="sess-1",
        extracted_by_model="deterministic-v0",
        extraction_prompt_version="v0",
        epistemic_type=epistemic_type,
        content=content,
        promotion_status=promotion_status,
    )
    if atom_id is not None:
        kwargs["atom_id"] = atom_id
    if superseded_by is not None:
        kwargs["superseded_by"] = superseded_by
    return ExperienceAtom(**kwargs)


def test_card_is_inactive_true_for_every_inactive_state():
    for status in ("deprecated", "superseded", "quarantined"):
        assert card_is_inactive(_card(status)) is True, status
    # A deactivated card is inactive even with an otherwise-live status.
    assert card_is_inactive(_card("candidate", deactivated_at=utc_now())) is True


def test_card_is_inactive_false_for_active_states():
    assert card_is_inactive(_card("candidate")) is False
    assert card_is_inactive(_card("verified")) is False


def test_staticmethod_delegates_to_module_predicate():
    # The CEM staticmethod must agree with the module-level predicate across states
    # (retrieval/_matching_card/negative_control_suppression_rate all key off it).
    for status in ("candidate", "verified", "deprecated", "superseded", "quarantined"):
        card = _card(status)
        assert CEM._card_is_inactive(card) is card_is_inactive(card)


def test_supersede_stale_cards_skips_already_inactive_card(tmp_path):
    """Canary for nit (a): a card that is ALREADY inactive (deprecated) and still
    carries evidence must not be re-flipped to ``superseded`` by a later
    invalidation event. With the old ``promotion_status == "superseded"`` skip the
    deprecated card is not skipped and gets clobbered; the shared predicate fixes it.
    """
    cem = CEM(tmp_path)
    old_evidence = _atom("db host is legacy", atom_id="atom-old", promotion_status="deprecated")
    inv = _atom("UPDATE: db host is new", epistemic_type="invalidation_event", atom_id="atom-inv")
    old_evidence.superseded_by = ["atom-inv"]
    cem.store.save_atom(old_evidence)
    cem.store.save_atom(inv)

    deprecated_card = ExperienceCard(
        title="db host",
        use_when="db config",
        evidence_atom_ids=["atom-old"],
        confidence_score=0.9,
        action_brief_template="use db host",
        promotion_status="deprecated",
    )
    new_card = ExperienceCard(
        title="db host new",
        use_when="db config",
        evidence_atom_ids=["atom-inv"],
        confidence_score=0.9,
        action_brief_template="use new db host",
    )
    cem.store.save_card(deprecated_card)
    cem.store.save_card(new_card)

    cem._supersede_stale_cards(inv, new_card)

    refreshed = cem.store.get_card(deprecated_card.card_id)
    assert refreshed.promotion_status == "deprecated"
    assert new_card.card_id not in refreshed.superseded_by_card_ids
