from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from typing import Any, Dict, Optional


class Load(BaseModel):
    model_config = ConfigDict(extra="ignore")

    load_id: str
    origin: str
    destination: str
    pickup_datetime: str
    delivery_datetime: str
    equipment_type: str
    loadboard_rate: float

    notes: Optional[str] = None
    weight: Optional[float] = None
    commodity_type: Optional[str] = None
    num_of_pieces: Optional[int] = None
    miles: Optional[float] = None
    dimensions: Optional[str] = None


class CallState(BaseModel):
    model_config = ConfigDict(extra="ignore")

    call_id: str
    started_at: float
    ended_at: Optional[float] = None
    from_number: Optional[str] = None
    metadata: Dict[str, Any] = {}
    outcome: Optional[str] = None
    summary: Dict[str, Any] = {}


class NegotiationPolicy(BaseModel):
    target: float
    min: float
    max: float
    max_rounds: int = 3


class NegotiationState(BaseModel):
    model_config = ConfigDict(extra="ignore")

    call_id: Optional[str] = None
    load: Load
    mc_number: Optional[str] = None

    status: str  # "in_progress" | "accepted" | "declined"
    round: int
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
