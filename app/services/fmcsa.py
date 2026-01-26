import os
from typing import Any, Dict, Optional, Tuple

import httpx

FMCSA_BASE = "https://mobile.fmcsa.dot.gov/qc/services"


class FmcsaError(Exception):
    pass


def _extract_fields(payload: Dict[str, Any], mc_number: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[int]]:
    content = payload.get("content") or []
    if not content:
        return None, None, None, None

    carrier = (content[0] or {}).get("carrier") or {}
    allowed = carrier.get("allowedToOperate")
    city = carrier.get("phyCity")
    state = carrier.get("phyState")
    dot = carrier.get("dotNumber")
    return allowed, city, state, dot


async def fetch_carrier_by_mc(mc_number: str) -> Dict[str, Any]:
    web_key = os.getenv("FMCSA_WEBKEY")
    if not web_key:
        raise FmcsaError("Missing FMCSA_WEBKEY environment variable")

    url = f"{FMCSA_BASE}/carriers/docket-number/{mc_number}"
    params = {"webKey": web_key}

    timeout = httpx.Timeout(10.0, connect=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(url, params=params)
        if resp.status_code == 404:
            return {"content": []}
        if resp.status_code >= 400:
            raise FmcsaError(f"FMCSA request failed: {resp.status_code} {resp.text[:200]}")

        try:
            return resp.json()
        except Exception as e:
            raise FmcsaError(f"FMCSA returned non-JSON: {e}") from e


async def verify_carrier(mc_number: str) -> Dict[str, Any]:
    payload = await fetch_carrier_by_mc(mc_number)
    allowed, city, state, dot = _extract_fields(payload, mc_number)

    # Eligibility logic
    if allowed is None:
        return {
            "eligible": False,
            "mc_number": mc_number,
            "dot_number": dot,
            "allowed_to_operate": allowed,
            "phy_city": city,
            "phy_state": state,
        }

    if allowed != "Y":
        return {
            "eligible": False,
            "mc_number": mc_number,
            "dot_number": dot,
            "allowed_to_operate": allowed,
            "phy_city": city,
            "phy_state": state,
        }

    return {
        "eligible": True,
        "mc_number": mc_number,
        "dot_number": dot,
        "allowed_to_operate": allowed,
        "phy_city": city,
        "phy_state": state, 
    }
