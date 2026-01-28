from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy import select

import app.db as db
from app.models import CallRecord

from app.core.security import require_api_key
from app.core.state import LOCK, CALLS
from app.schemas.api import MetricsOverview
from app.services.metrics import overview

router = APIRouter(prefix="/v1/metrics", tags=["metrics"], dependencies=[Depends(require_api_key)])


@router.get("/overview", response_model=MetricsOverview)
def metrics_overview() -> MetricsOverview:
    return overview()


def _dashboard_rows() -> list[dict]:
    db.require_db()

    with db.SessionLocal() as session:
        rows = (
            session.execute(
                select(CallRecord).order_by(CallRecord.ended_at.desc().nullslast())
            )
            .scalars()
            .all()
        )

    out: list[dict] = []
    for r in rows:
        out.append({
            "call_id": r.call_id,
            "ended_at": r.ended_at,
            "verified": r.verified,
            "load_id": r.load_id,
            "loadboard_rate": r.loadboard_rate,
            "rounds": r.rounds,
            "carrier_first_offer": r.carrier_first_offer,
            "carrier_last_offer": r.carrier_last_offer,
            "final_offer": r.final_offer,
            "agreed": r.agreed,
            "transfer_to_rep": r.transfer_to_rep,
            "outcome": r.outcome,
            "sentiment": r.sentiment,
        })
    return out


@router.get("/dashboard/overview")
def dashboard_overview():
    rows = _dashboard_rows()
    total = len(rows)

    if total == 0:
        return {
            "total_calls": 0,
            "verified_rate": 0.0,
            "acceptance_rate": 0.0,
            "transfer_rate": 0.0,
            "avg_rounds": 0.0,
            "avg_final_vs_loadboard": 0.0,
        }

    verified_known = [r for r in rows if r.get("verified") is not None]
    verified_rate = (
        sum(1 for r in verified_known if r.get("verified") is True) / len(verified_known)
        if verified_known
        else 0.0
    )

    accepted = [r for r in rows if r.get("outcome") == "ACCEPTED" or r.get("agreed") is True]
    acceptance_rate = len(accepted) / total

    transferred = [r for r in rows if r.get("transfer_to_rep") is True]
    transfer_rate = len(transferred) / total

    rounds_vals = [float(r["rounds"]) for r in rows if r.get("rounds") is not None]
    avg_rounds = (sum(rounds_vals) / len(rounds_vals)) if rounds_vals else 0.0

    deltas = []
    for r in rows:
        if r.get("final_offer") is not None and r.get("loadboard_rate") is not None:
            deltas.append(float(r["final_offer"]) - float(r["loadboard_rate"]))
    avg_final_vs_loadboard = (sum(deltas) / len(deltas)) if deltas else 0.0

    return {
        "total_calls": total,
        "verified_rate": round(verified_rate, 3),
        "acceptance_rate": round(acceptance_rate, 3),
        "transfer_rate": round(transfer_rate, 3),
        "avg_rounds": round(avg_rounds, 3),
        "avg_final_vs_loadboard": round(avg_final_vs_loadboard, 2),
    }


@router.get("/dashboard/outcomes")
def dashboard_outcomes():
    rows = _dashboard_rows()
    counts: dict[str, int] = {}
    for r in rows:
        key = r.get("outcome") or "UNKNOWN"
        counts[key] = counts.get(key, 0) + 1
    return counts


@router.get("/dashboard/sentiment")
def dashboard_sentiment():
    rows = _dashboard_rows()
    counts: dict[str, int] = {}
    for r in rows:
        key = r.get("sentiment") or "Unknown"
        counts[key] = counts.get(key, 0) + 1
    return counts


@router.get("/dashboard/calls")
def dashboard_calls(limit: int = 50):
    rows = _dashboard_rows()
    limit = max(1, min(limit, 500))
    return rows[:limit]


def _row_to_dashboard_dict(r: CallRecord) -> dict:
    return {
        "call_id": r.call_id,
        "ended_at": r.ended_at,
        "verified": r.verified,
        "load_id": r.load_id,
        "loadboard_rate": r.loadboard_rate,
        "rounds": r.rounds,
        "carrier_first_offer": r.carrier_first_offer,
        "carrier_last_offer": r.carrier_last_offer,
        "final_offer": r.final_offer,
        "agreed": r.agreed,
        "transfer_to_rep": r.transfer_to_rep,
        "outcome": r.outcome,
        "sentiment": r.sentiment,
        "summary": r.summary,
    }

@router.get("/dashboard/calls/{call_id}")
def dashboard_call(call_id: str):
    with db.SessionLocal() as session:
        row = session.execute(
            select(CallRecord).where(CallRecord.call_id == call_id)
        ).scalar_one_or_none()

    if not row:
        raise HTTPException(status_code=404, detail="Call not found")

    return _row_to_dashboard_dict(row)