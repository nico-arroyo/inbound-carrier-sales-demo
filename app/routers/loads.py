from fastapi import APIRouter, Depends

from app.core.security import require_api_key
from app.core.state import LOCK, CALLS
from app.models.api import LoadSearchRequest, LoadSearchResponse
from app.services.loads import search

router = APIRouter(prefix="/v1/loads", tags=["loads"], dependencies=[Depends(require_api_key)])


@router.post("/search", response_model=LoadSearchResponse)
def load_search(req: LoadSearchRequest) -> LoadSearchResponse:
    matches = search(req.origin, req.destination, req.equipment_type, req.limit)

    if req.call_id:
        with LOCK:
            st = CALLS.get(req.call_id)
            if st:
                st.summary["last_search"] = {
                    "origin": req.origin,
                    "destination": req.destination,
                    "equipment_type": req.equipment_type,
                    "returned": [m.load_id for m in matches],
                }

    return LoadSearchResponse(matches=matches)
