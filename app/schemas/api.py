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


# ---- Metrics
class MetricsOverview(BaseModel):
    calls_started: int
    calls_ended: int
    negotiations_started: int
    negotiations_accepted: int
    negotiations_declined: int
    average_rounds_completed: float


class NegotiationResponse(BaseModel):
    call_id: str
    status: str
    round: int
    decision: str
    counter_offer: float | None = None
    final_rate: float | None = None
    policy: dict | None = None
