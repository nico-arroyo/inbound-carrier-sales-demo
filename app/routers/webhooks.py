from fastapi import APIRouter, Depends

from app.core.security import require_api_key
from app.core.state import LOCK, CALLS, METRICS, NEGOTIATIONS, now_ts
from app.schemas.api import WebhookCallEnded
from app.schemas.domain import CallState, NegotiationState
from app.services.call_store import upsert_call_record

router = APIRouter(prefix="/webhooks/happyrobot", tags=["webhooks"], dependencies=[Depends(require_api_key)],)


def _classify_outcome(webhook_outcome: str | None, negotiation: NegotiationState | None, verified: bool | None,) -> str:
    if verified is False or webhook_outcome == "failed_verification":
        return "FAILED_VERIFICATION"

    if webhook_outcome == "no_match":
        return "NO_MATCHING_LOAD"

    if webhook_outcome == "dropped":
        return "CALL_DROPPED"

    if negotiation:
        if negotiation.status == "accepted":
            return "ACCEPTED"
        if negotiation.status == "declined":
            return "DECLINED"

    if webhook_outcome == "accepted":
        return "ACCEPTED"
    if webhook_outcome == "declined":
        return "DECLINED"

    return "OTHER"


def _build_dashboard_record(call_id: str, payload: WebhookCallEnded) -> dict:
    negotiation = NEGOTIATIONS.get(call_id)

    summary = payload.summary if isinstance(payload.summary, dict) else {}

    verified = None
    if "verified" in summary:
        try:
            verified = bool(summary.get("verified"))
        except Exception:
            verified = None

    sentiment = summary.get("sentiment") if isinstance(summary.get("sentiment"), str) else None

    outcome = _classify_outcome(payload.outcome, negotiation, verified)

    rounds = None
    carrier_first_offer = None
    carrier_last_offer = None
    final_offer = None
    load_id = None
    loadboard_rate = None
    agreed = False
    transfer_to_rep = False

    if negotiation:
        rounds = negotiation.round
        load_id = negotiation.load.load_id
        loadboard_rate = negotiation.load.loadboard_rate

        carrier_last_offer = negotiation.last_carrier_offer
        carrier_first_offer = negotiation.last_carrier_offer if negotiation.round == 1 else None

        final_offer = negotiation.final_rate

        agreed = negotiation.status == "accepted"
        transfer_to_rep = agreed

    if outcome == "ACCEPTED":
        agreed = True
        transfer_to_rep = True

        if final_offer is None:
            if negotiation and negotiation.last_counter_offer is not None:
                final_offer = negotiation.last_counter_offer
            elif negotiation and negotiation.last_carrier_offer is not None:
                final_offer = negotiation.last_carrier_offer

    return {
        "call_id": call_id,
        "ended_at": now_ts(),
        "verified": verified,
        "load_id": load_id,
        "loadboard_rate": loadboard_rate,
        "rounds": rounds,
        "carrier_first_offer": carrier_first_offer,
        "carrier_last_offer": carrier_last_offer,
        "final_offer": final_offer,
        "agreed": agreed,
        "transfer_to_rep": transfer_to_rep,
        "outcome": outcome,
        "sentiment": sentiment,
    }



@router.post("/call-ended")
def call_ended(payload: WebhookCallEnded):
    with LOCK:
        st = CALLS.get(payload.call_id)

        if not st:
            st = CallState(call_id=payload.call_id)
            CALLS[payload.call_id] = st
            METRICS.calls_started += 1

        if st.ended_at is not None:
            return {"ok": True, "call_id": payload.call_id, "idempotent": True}

        st.ended_at = now_ts()
        st.outcome = payload.outcome

        st.summary = payload.summary or {}

        dash = _build_dashboard_record(payload.call_id, payload)
        st.summary["dashboard"] = dash

        summary_text = None
        if isinstance(payload.summary, dict):
            if "summary" in payload.summary:
                summary_field = payload.summary["summary"]
                if isinstance(summary_field, dict) and "summary" in summary_field:
                    summary_text = summary_field["summary"]
                elif isinstance(summary_field, str):
                    summary_text = summary_field
        elif isinstance(payload.summary, str):
            summary_text = payload.summary

        upsert_call_record(record=dash, summary_text=summary_text,)

        METRICS.calls_ended += 1

    return {"ok": True, "call_id": payload.call_id}