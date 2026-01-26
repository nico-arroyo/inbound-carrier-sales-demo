from fastapi import APIRouter, Depends, Path

from app.core.security import require_api_key
from app.core.state import LOCK, CALLS
from app.models.api import (
    NegotiationStartRequest,
    NegotiationCounterRequest,
    NegotiationAcceptRequest,
    NegotiationDeclineRequest,
    NegotiationResponse,
)
from app.services.loads import get_by_id
from app.services.negotiation import start, counter as do_counter, accept as do_accept, decline as do_decline

router = APIRouter(prefix="/v1/negotiations", tags=["negotiations"], dependencies=[Depends(require_api_key)])


@router.post("/start", response_model=NegotiationResponse)
def start_neg(req: NegotiationStartRequest) -> NegotiationResponse:
    load = get_by_id(req.load_id)
    st = start(req.call_id, load, req.carrier_mc, req.carrier_initial_offer)

    if req.call_id:
        with LOCK:
            cs = CALLS.get(req.call_id)
            if cs:
                cs.summary["negotiation_id"] = st.negotiation_id
                cs.summary["load_id"] = st.load.load_id

    if st.policy.min <= st.last_carrier_offer <= st.policy.max:
        decision = "accept"
        counter_offer = None
    elif st.status == "declined":
        decision = "decline"
        counter_offer = None
    else:
        decision = "counter"
        counter_offer = st.last_counter_offer

    return NegotiationResponse(
        negotiation_id=st.negotiation_id,
        status=st.status,
        round=st.round,
        decision=decision,
        counter_offer=counter_offer,
        final_rate=st.final_rate,
        policy=st.policy,
    )


@router.post("/{negotiation_id}/counter", response_model=NegotiationResponse)
def counter_neg(
    negotiation_id: str = Path(...),
    req: NegotiationCounterRequest = None,
) -> NegotiationResponse:
    st, decision, counter_offer = do_counter(negotiation_id, req.carrier_offer)

    return NegotiationResponse(
        negotiation_id=st.negotiation_id,
        status=st.status,
        round=st.round,
        decision=decision,
        counter_offer=counter_offer,
        final_rate=st.final_rate,
        policy=st.policy,
    )


@router.post("/{negotiation_id}/accept", response_model=NegotiationResponse)
def accept_neg(negotiation_id: str, req: NegotiationAcceptRequest) -> NegotiationResponse:
    st = do_accept(negotiation_id, req.final_rate)
    return NegotiationResponse(
        negotiation_id=st.negotiation_id,
        status=st.status,
        round=st.round,
        decision="accept",
        counter_offer=None,
        final_rate=st.final_rate,
        policy=st.policy,
    )


@router.post("/{negotiation_id}/decline", response_model=NegotiationResponse)
def decline_neg(negotiation_id: str, req: NegotiationDeclineRequest) -> NegotiationResponse:
    st = do_decline(negotiation_id, req.reason or "declined")
    return NegotiationResponse(
        negotiation_id=st.negotiation_id,
        status=st.status,
        round=st.round,
        decision="decline",
        counter_offer=None,
        final_rate=st.final_rate,
        policy=st.policy,
    )
