from __future__ import annotations

import uuid
from typing import Optional, Tuple, Literal

from fastapi import HTTPException

from app.core.config import settings
from app.core.state import LOCK, NEGOTIATIONS, METRICS, now_ts
from app.models.domain import NegotiationPolicy, NegotiationState, Load

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

    if round_num >= policy.max_rounds:
        return "decline", None

    if round_num == 1:
        counter = policy.target
    elif round_num == 2:
        counter = policy.target + 0.5 * (offer - policy.target)
    else:
        counter = policy.target + 0.75 * (offer - policy.target)

    counter = max(policy.min, min(policy.max, counter))
    return "counter", round(counter, 2)


def start(call_id: Optional[str], load: Load, carrier_mc: Optional[str], carrier_initial_offer: float) -> NegotiationState:
    policy = make_policy(load.rate)
    negotiation_id = f"neg_{uuid.uuid4().hex[:12]}"

    decision, counter = decide(policy, carrier_initial_offer, 1)

    st = NegotiationState(
        negotiation_id=negotiation_id,
        call_id=call_id,
        load=load,
        carrier_mc=carrier_mc,
        status="in_progress",
        round=1,
        policy=policy,
        last_carrier_offer=carrier_initial_offer,
        last_counter_offer=counter,
        final_rate=None,
        created_at=now_ts(),
    )

    with LOCK:
        NEGOTIATIONS[negotiation_id] = st
        METRICS.negotiations_started += 1

        # If decision is an immediate decline, finalize now
        if decision == "decline":
            st.status = "declined"
            METRICS.negotiations_declined += 1
            METRICS.completed_rounds_total += st.round
            METRICS.completed_count += 1

    return st


def get(negotiation_id: str) -> NegotiationState:
    with LOCK:
        st = NEGOTIATIONS.get(negotiation_id)
    if not st:
        raise HTTPException(status_code=404, detail="Negotiation not found")
    return st


def counter(negotiation_id: str, carrier_offer: float) -> Tuple[NegotiationState, Decision, Optional[float]]:
    with LOCK:
        st = NEGOTIATIONS.get(negotiation_id)
        if not st:
            raise HTTPException(status_code=404, detail="Negotiation not found")
        if st.status != "in_progress":
            raise HTTPException(status_code=409, detail=f"Negotiation already {st.status}")

        st.round += 1
        st.last_carrier_offer = carrier_offer

        decision, counter_offer = decide(st.policy, carrier_offer, st.round)

        st.last_counter_offer = counter_offer

        if decision == "decline":
            st.status = "declined"
            METRICS.negotiations_declined += 1
            METRICS.completed_rounds_total += st.round
            METRICS.completed_count += 1

        return st, decision, counter_offer


def accept(negotiation_id: str, final_rate: float) -> NegotiationState:
    with LOCK:
        st = NEGOTIATIONS.get(negotiation_id)
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


def decline(negotiation_id: str, reason: str) -> NegotiationState:
    with LOCK:
        st = NEGOTIATIONS.get(negotiation_id)
        if not st:
            raise HTTPException(status_code=404, detail="Negotiation not found")
        if st.status != "in_progress":
            raise HTTPException(status_code=409, detail=f"Negotiation already {st.status}")

        st.status = "declined"
        METRICS.negotiations_declined += 1
        METRICS.completed_rounds_total += st.round
        METRICS.completed_count += 1

        return st
