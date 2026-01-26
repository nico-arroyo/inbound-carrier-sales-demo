from fastapi import APIRouter, Depends

from app.core.security import require_api_key
from app.core.state import LOCK, CALLS
from app.schemas.loads import LoadSearchRequest, LoadSearchResponse
from app.services.loads import search

router = APIRouter(prefix="/v1/loads", tags=["loads"], dependencies=[Depends(require_api_key)])


def _fmt_city_state(city: str | None, state: str | None) -> str | None:
    if not city or not state:
        return None
    return f"{city.strip()}, {state.strip().upper()}"


@router.post("/search", response_model=LoadSearchResponse)
def load_search(req: LoadSearchRequest) -> LoadSearchResponse:
    origin = req.origin or _fmt_city_state(req.origin_city, req.origin_state)
    destination = req.destination or _fmt_city_state(req.destination_city, req.destination_state)

    matches = search(origin, destination, req.equipment_type, req.limit)

    return LoadSearchResponse(matches=matches)
