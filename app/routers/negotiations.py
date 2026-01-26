from fastapi import APIRouter, Depends, HTTPException

from app.core.security import require_api_key
from app.schemas.negotiation import NegotiationStepRequest, NegotiationStepResponse
from app.services.loads import get_by_id
from app.services.negotiation import (
    start,
    counter as do_counter,
    accept as do_accept,
    exists as negotiation_exists,
)

router = APIRouter(
    prefix="/v1/negotiations",
    tags=["negotiations"],
    dependencies=[Depends(require_api_key)],
)


@router.post("/step", response_model=NegotiationStepResponse)
def step(req: NegotiationStepRequest) -> NegotiationStepResponse:
    if not req.call_id:
        raise HTTPException(status_code=400, detail="call_id is required")

    load = get_by_id(req.load_id)

    # Round 1: initialize + decide in one place (service layer)
    if not negotiation_exists(req.call_id):
        st, decision, counter_offer = start(
            call_id=req.call_id,
            load=load,
            mc_number=req.mc_number,
            carrier_initial_offer=req.carrier_offer,
        )
    else:
        # Round >=2: counter/accept/decline decision happens in service
        st, decision, counter_offer = do_counter(req.call_id, req.carrier_offer)

    # If accepted at this step, finalize so workflow can transfer
    transfer = False
    final_rate = st.final_rate

    if decision == "accept":
        st = do_accept(req.call_id, req.carrier_offer)
        transfer = True
        final_rate = st.final_rate
        counter_offer = None  # accepted means no counter

    return NegotiationStepResponse(
        call_id=req.call_id,
        status=st.status,
        round=st.round,
        decision=decision,
        counter_offer=counter_offer,
        final_rate=final_rate,
        policy=st.policy.model_dump() if getattr(st, "policy", None) else None,
        transfer_to_rep=transfer,
    )
