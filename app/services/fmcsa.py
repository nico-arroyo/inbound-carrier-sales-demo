from __future__ import annotations

from typing import Any, Dict, Optional

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.models.api import CarrierVerifyResponse, CarrierInfo

FMCSA_BASE = "https://mobile.fmcsa.dot.gov/qc/services"


def _pick_first_carrier_obj(data: Any) -> Optional[Dict[str, Any]]:
    """
    FMCSA responses sometimes wrap the actual record in arrays/containers.
    This keeps parsing defensive for demo reliability.
    """
    if isinstance(data, dict):
        for key in ("content", "carriers", "carrier", "results", "result"):
            v = data.get(key)
            if isinstance(v, list) and v:
                if isinstance(v[0], dict):
                    return v[0]
            if isinstance(v, dict):
                return v
        return data
    if isinstance(data, list) and data:
        if isinstance(data[0], dict):
            return data[0]
    return None


async def verify_mc(mc_number: str) -> CarrierVerifyResponse:
    """
    Verify a carrier by MC number using FMCSA QCMobile API.

    Auth: `webKey` query param required.
    Endpoint family: QCMobile supports queries by docket number (MC). :contentReference[oaicite:5]{index=5}
    """
    if not settings.fmcsa_webkey:
        raise HTTPException(
            status_code=500,
            detail="FMCSA_WEBKEY is not set. Add it to .env to enable real MC verification.",
        )

    mc = mc_number.strip()
    url = f"{FMCSA_BASE}/carriers/docket-number/{mc}"
    params = {"webKey": settings.fmcsa_webkey}

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url, params=params)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"FMCSA request error: {type(e).__name__}")

    if resp.status_code == 401:
        raise HTTPException(status_code=502, detail="FMCSA auth failed (invalid FMCSA_WEBKEY).")
    if resp.status_code == 404:
        return CarrierVerifyResponse(
            verified=False,
            eligible=False,
            reason="not_found",
            carrier=CarrierInfo(mc_number=mc, legal_name=None, status=None),
        )

    try:
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        raise HTTPException(status_code=502, detail="FMCSA returned invalid response.")

    carrier = _pick_first_carrier_obj(data)
    if not carrier:
        return CarrierVerifyResponse(
            verified=False,
            eligible=False,
            reason="unexpected_response",
            carrier=CarrierInfo(mc_number=mc, legal_name=None, status=None),
        )

    allow_to_operate = carrier.get("allowToOperate")  # "Y" or "N"
    out_of_service = carrier.get("outOfService")      # "Y" or "N"

    eligible = (allow_to_operate == "Y") and (out_of_service != "Y")
    reason = "eligible" if eligible else "not_eligible"

    legal_name = carrier.get("legalName") or carrier.get("dbaName")

    return CarrierVerifyResponse(
        verified=True,
        eligible=eligible,
        reason=reason,
        carrier=CarrierInfo(
            mc_number=str(carrier.get("mcNumber") or mc),
            legal_name=legal_name,
            status="ACTIVE" if eligible else "RESTRICTED",
        ),
    )
