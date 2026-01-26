from fastapi import APIRouter, HTTPException

from app.schemas.carriers import CarrierVerifyRequest, CarrierVerifyResponse
from app.services.fmcsa import FmcsaError, verify_carrier

router = APIRouter(prefix="/carriers", tags=["carriers"])


@router.post("/verify", response_model=CarrierVerifyResponse)
async def verify(req: CarrierVerifyRequest):
    try:
        result = await verify_carrier(req.mc_number)
        return result
    except FmcsaError as e:
        # 502 because this is an upstream dependency failure/misconfig
        raise HTTPException(status_code=502, detail=str(e))
