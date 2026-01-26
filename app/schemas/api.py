from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.domain import Load, NegotiationPolicy


# ---- Webhooks
class WebhookCallStarted(BaseModel):
    call_id: str
    from_number: Optional[str] = None
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WebhookCallEnded(BaseModel):
    call_id: str
    timestamp: Optional[str] = None
    outcome: Literal[
        "accepted",
        "declined",
        "no_match",
        "failed_verification",
        "dropped",
        "other",
    ] = "other"
    summary: Dict[str, Any] = Field(default_factory=dict)



# ---- Loads
class LoadSearchRequest(BaseModel):
    call_id: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    origin_city: Optional[str] = None
    origin_state: Optional[str] = None
    destination_city: Optional[str] = None
    destination_state: Optional[str] = None

    equipment_type: Optional[str] = None
    limit: int = 3


class LoadSearchResponse(BaseModel):
    matches: List[Load]


# ---- Negotiations
class NegotiationStartRequest(BaseModel):
    call_id: Optional[str] = None
    load_id: str
    carrier_mc: Optional[str] = None
    carrier_initial_offer: float


class NegotiationCounterRequest(BaseModel):
    carrier_offer: float


class NegotiationAcceptRequest(BaseModel):
    final_rate: float


class NegotiationDeclineRequest(BaseModel):
    reason: Optional[str] = "declined"


Decision = Literal["accept", "counter", "decline"]
NegStatus = Literal["in_progress", "accepted", "declined"]


class NegotiationResponse(BaseModel):
    negotiation_id: str
    status: NegStatus
    round: int
    decision: Decision
    counter_offer: Optional[float] = None
    final_rate: Optional[float] = None
    policy: Optional[NegotiationPolicy] = None


# ---- Metrics
class MetricsOverview(BaseModel):
    calls_started: int
    calls_ended: int
    negotiations_started: int
    negotiations_accepted: int
    negotiations_declined: int
    average_rounds_completed: float
