from fastapi import APIRouter, Depends

from app.core.security import require_api_key
from app.models.api import MetricsOverview
from app.services.metrics import overview

router = APIRouter(prefix="/v1/metrics", tags=["metrics"], dependencies=[Depends(require_api_key)])


@router.get("/overview", response_model=MetricsOverview)
def metrics_overview() -> MetricsOverview:
    return overview()
