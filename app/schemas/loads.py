from pydantic import BaseModel
from typing import Optional, List

from app.schemas.domain import Load


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
