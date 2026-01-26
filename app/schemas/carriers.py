from pydantic import BaseModel
from typing import Optional, Literal


class CarrierVerifyRequest(BaseModel):
    mc_number: str


class CarrierVerifyResponse(BaseModel):
    eligible: bool
    mc_number: str
    dot_number: Optional[int] = None
    allowed_to_operate: Optional[Literal["Y", "N"]] = None
    phy_city: Optional[str] = None
    phy_state: Optional[str] = None
