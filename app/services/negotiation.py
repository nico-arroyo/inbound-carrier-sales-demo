from __future__ import annotations

from typing import Optional, Tuple, Literal

from fastapi import HTTPException

from app.core.state import LOCK, NEGOTIATIONS, METRICS, now_ts
from app.schemas.domain import NegotiationPolicy, NegotiationState, Load

Decision = Literal["accept", "counter", "decline"]
MAX_NEGOTIATION_ROUNDS = 3


def make_policy(load_rate: float) -> NegotiationPolicy:
    target = float(load_rate)
    return NegotiationPolicy(
        target=target,
        min=round(target * 0.90, 2),
        max=round(target * 1.10, 2),
        max_rounds=MAX_NEGOTIATION_ROUNDS,
    )


def decide(policy: NegotiationPolicy, carrier_offer: float, round_num: int) -> Tuple[Decision, Optional[float]]:
    offer = float(carrier_offer)

    if policy.min <= offer <= policy.max:
        return "accept", None

    if round_num > policy.max_rounds:
        return "decline", None

    if round_num == 1:
        counter = policy.target + 0.25 * (offer - policy.target)
    elif round_num == 2:
        counter = policy.target + 0.5 * (offer - policy.target)
    else:
        counter = policy.target + 0.75 * (offer - policy.target)

    counter = max(policy.min, min(policy.max, counter))
    return "counter", round(counter, 2)


def start(
    call_id: Optional[str],
    load: Load,
    mc_number: Optional[str],
    carrier_initial_offer: float,
) -> Tuple[NegotiationState, Decision, Optional[float]]:
    """
    Creates negotiation state for round 1 AND computes the round-1 decision.
    Returns: (state, decision, counter_offer)
    """
    policy = make_policy(load.loadboard_rate)
    if not call_id:
        raise HTTPException(status_code=400, detail="call_id is required for step-based negotiation")

    decision, counter_offer = decide(policy, carrier_initial_offer, 1)

    st = NegotiationState(
        call_id=call_id,
        load=load,
        mc_number=mc_number,
        status="in_progress",
        round=1,
        policy=policy,
        last_carrier_offer=carrier_initial_offer,
        last_counter_offer=counter_offer,
        final_rate=None,
        created_at=now_ts(),
    )

    with LOCK:
        NEGOTIATIONS[call_id] = st
        METRICS.negotiations_started += 1

        if decision == "decline":
            st.status = "declined"
            METRICS.negotiations_declined += 1
            METRICS.completed_rounds_total += st.round
            METRICS.completed_count += 1

    return st, decision, counter_offer


def get(call_id: str) -> NegotiationState:
    with LOCK:
        st = NEGOTIATIONS.get(call_id)
    if not st:
        raise HTTPException(status_code=404, detail="Negotiation not found")
    return st


def counter(call_id: str, carrier_offer: float) -> Tuple[NegotiationState, Decision, Optional[float]]:
    with LOCK:
        st = NEGOTIATIONS.get(call_id)
        if not st:
            raise HTTPException(status_code=404, detail="Negotiation not found")
        if st.status != "in_progress":
            raise HTTPException(status_code=409, detail=f"Negotiation already {st.status}")

        st.round += 1
        st.last_carrier_offer = float(carrier_offer)

        decision, counter_offer = decide(st.policy, carrier_offer, st.round)
        st.last_counter_offer = counter_offer

        if decision == "decline":
            st.status = "declined"
            METRICS.negotiations_declined += 1
            METRICS.completed_rounds_total += st.round
            METRICS.completed_count += 1

        return st, decision, counter_offer


def accept(call_id: str, final_rate: float) -> NegotiationState:
    with LOCK:
        st = NEGOTIATIONS.get(call_id)
        if not st:
            raise HTTPException(status_code=404, detail="Negotiation not found")
        if st.status != "in_progress":
            raise HTTPException(status_code=409, detail=f"Negotiation already {st.status}")

        st.status = "accepted"
        st.final_rate = float(final_rate)

        METRICS.negotiations_accepted += 1
        METRICS.completed_rounds_total += st.round
        METRICS.completed_count += 1

        return st


def decline(call_id: str, reason: str) -> NegotiationState:
    with LOCK:
        st = NEGOTIATIONS.get(call_id)
        if not st:
            raise HTTPException(status_code=404, detail="Negotiation not found")
        if st.status != "in_progress":
            raise HTTPException(status_code=409, detail=f"Negotiation already {st.status}")

        st.status = "declined"
        METRICS.negotiations_declined += 1
        METRICS.completed_rounds_total += st.round
        METRICS.completed_count += 1

        return st


def exists(call_id: str) -> bool:
    with LOCK:
        return call_id in NEGOTIATIONS
