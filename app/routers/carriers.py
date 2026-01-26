from fastapi import APIRouter, Depends

from app.core.security import require_api_key
from app.core.state import LOCK, CALLS
from app.models.api import CarrierVerifyRequest, CarrierVerifyResponse
from app.services.fmcsa import verify_mc

router = APIRouter(prefix="/v1/carriers", tags=["carriers"], dependencies=[Depends(require_api_key)])


@router.post("/verify-mc", response_model=CarrierVerifyResponse)
async def verify(req: CarrierVerifyRequest) -> CarrierVerifyResponse:
    resp = await verify_mc(req.mc_number)

    if req.call_id:
        with LOCK:
            st = CALLS.get(req.call_id)
            if st:
                st.summary["mc_number"] = req.mc_number
                st.summary["carrier_verified"] = resp.verified
                st.summary["carrier_eligible"] = resp.eligible
                st.summary["carrier_reason"] = resp.reason

    return resp
