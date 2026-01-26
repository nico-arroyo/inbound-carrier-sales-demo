from fastapi import APIRouter, Depends

from app.core.security import require_api_key
from app.core.state import LOCK, CALLS, METRICS, now_ts
from app.schemas.api import WebhookCallStarted, WebhookCallEnded
from app.schemas.domain import CallState

router = APIRouter(prefix="/webhooks/happyrobot", tags=["webhooks"], dependencies=[Depends(require_api_key)])


@router.post("/call-started")
def call_started(payload: WebhookCallStarted):
    with LOCK:
        if payload.call_id in CALLS:
            return {"ok": True, "call_id": payload.call_id, "idempotent": True}

        CALLS[payload.call_id] = CallState(
            call_id=payload.call_id,
            started_at=now_ts(),
            from_number=payload.from_number,
            metadata=payload.metadata or {},
        )
        METRICS.calls_started += 1

    return {"ok": True, "call_id": payload.call_id}


@router.post("/call-ended")
def call_ended(payload: WebhookCallEnded):
    with LOCK:
        st = CALLS.get(payload.call_id)
        if not st:
            st = CallState(call_id=payload.call_id, started_at=now_ts())
            CALLS[payload.call_id] = st
            METRICS.calls_started += 1

        st.ended_at = now_ts()
        st.outcome = payload.outcome
        st.summary = payload.summary or {}
        METRICS.calls_ended += 1

    return {"ok": True, "call_id": payload.call_id}
