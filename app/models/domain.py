from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field, ConfigDict


class Load(BaseModel):
    model_config = ConfigDict(extra="ignore")
    load_id: str
    origin: str
    destination: str
    equipment_type: str
    rate: float
    pickup_date: Optional[str] = None
    notes: Optional[str] = None


class CallState(BaseModel):
    call_id: str
    started_at: float
    ended_at: Optional[float] = None
    from_number: Optional[str] = None
    outcome: Optional[str] = None
    summary: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NegotiationPolicy(BaseModel):
    target: float
    min: float
    max: float
    max_rounds: int


NegStatus = Literal["in_progress", "accepted", "declined"]


class NegotiationState(BaseModel):
    negotiation_id: str
    call_id: Optional[str]
    load: Load
    carrier_mc: Optional[str] = None
    status: NegStatus = "in_progress"
    round: int = 1
    policy: NegotiationPolicy
    last_carrier_offer: float
    last_counter_offer: Optional[float] = None
    final_rate: Optional[float] = None
    created_at: float


class MetricsState(BaseModel):
    calls_started: int = 0
    calls_ended: int = 0
    negotiations_started: int = 0
    negotiations_accepted: int = 0
    negotiations_declined: int = 0
    completed_rounds_total: int = 0
    completed_count: int = 0

    def avg_rounds(self) -> float:
        if self.completed_count == 0:
            return 0.0
        return self.completed_rounds_total / self.completed_count
