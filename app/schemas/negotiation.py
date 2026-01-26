from typing import Optional
from pydantic import BaseModel

from app.schemas.api import NegotiationResponse


class NegotiationStepRequest(BaseModel):
    call_id: Optional[str] = None
    load_id: str
    mc_number: Optional[str] = None
    carrier_offer: float


class NegotiationStepResponse(NegotiationResponse):
    transfer_to_rep: bool = False
