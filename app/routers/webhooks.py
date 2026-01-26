from fastapi import APIRouter, Depends

from app.core.security import require_api_key
from app.core.state import LOCK, CALLS, METRICS, NEGOTIATIONS, now_ts
from app.schemas.api import WebhookCallEnded
from app.schemas.domain import CallState, NegotiationState

router = APIRouter(
    prefix="/webhooks/happyrobot",
    tags=["webhooks"],
    dependencies=[Depends(require_api_key)],
)


def _classify_outcome(
    webhook_outcome: str | None,
    negotiation: NegotiationState | None,
    verified: bool | None,
) -> str:
    """
    Minimal deterministic outcome labels for dashboard.
    Matches the challenge funnel (verify -> load -> negotiate -> transfer). 
    """
    if verified is False or webhook_outcome == "failed_verification":
        return "FAILED_VERIFICATION"

    if webhook_outcome == "no_match":
        return "NO_MATCHING_LOAD"

    if webhook_outcome == "dropped":
        return "CALL_DROPPED"

    # Prefer negotiation truth if it exists
    if negotiation:
        if negotiation.status == "accepted":
            return "ACCEPTED_TRANSFERRED"
        if negotiation.status == "declined":
            return "DECLINED"

    # Fall back to platform outcome
    if webhook_outcome == "accepted":
        return "ACCEPTED_TRANSFERRED"
    if webhook_outcome == "declined":
        return "DECLINED"

    return "OTHER"


def _build_dashboard_record(call_id: str, payload: WebhookCallEnded) -> dict:
    negotiation = NEGOTIATIONS.get(call_id)

    summary = payload.summary if isinstance(payload.summary, dict) else {}

    # Optional: workflow/platform can provide this
    verified = None
    if "verified" in summary:
        try:
            verified = bool(summary.get("verified"))
        except Exception:
            verified = None

    # Keep exact platform value like:
    # "Really negative", "Negative", "Neutral", "Positive", "Really positive"
    sentiment = summary.get("sentiment") if isinstance(summary.get("sentiment"), str) else None

    # Determine business outcome
    outcome = _classify_outcome(payload.outcome, negotiation, verified)

    # Offer extraction (minimal, accurate naming)
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

        # Best available: unless you persist a first_offer in negotiation state,
        # we only know it reliably if round == 1.
        carrier_last_offer = negotiation.last_carrier_offer
        carrier_first_offer = negotiation.last_carrier_offer if negotiation.round == 1 else None

        # Only set when negotiation.status == "accepted" (in your code)
        final_offer = negotiation.final_rate

        agreed = negotiation.status == "accepted"
        transfer_to_rep = agreed  # spec: agreed -> transfer

    # If platform says accepted, keep record consistent even if negotiation didn't finalize
    if outcome == "ACCEPTED_TRANSFERRED":
        agreed = True
        transfer_to_rep = True

        # Fill final_offer from best available number if missing
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
    """
    Single webhook endpoint.

    Stores:
      - raw webhook summary in CALLS[call_id].summary
      - minimal per-call dashboard record in CALLS[call_id].summary["dashboard"]
    """
    with LOCK:
        st = CALLS.get(payload.call_id)

        # Create if missing (we removed call-started webhook)
        if not st:
            st = CallState(call_id=payload.call_id, started_at=now_ts())
            CALLS[payload.call_id] = st
            METRICS.calls_started += 1

        # Idempotency: if already ended, don't double count
        if st.ended_at is not None:
            return {"ok": True, "call_id": payload.call_id, "idempotent": True}

        st.ended_at = now_ts()
        st.outcome = payload.outcome

        # Keep raw platform payload summary
        st.summary = payload.summary or {}

        # Attach minimal dashboard record used by /v1/metrics/dashboard/*
        st.summary["dashboard"] = _build_dashboard_record(payload.call_id, payload)

        METRICS.calls_ended += 1

    return {"ok": True, "call_id": payload.call_id}
