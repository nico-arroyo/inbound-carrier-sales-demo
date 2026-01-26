from fastapi import APIRouter, Depends, HTTPException

from app.core.security import require_api_key
from app.core.state import LOCK, CALLS
from app.schemas.api import MetricsOverview
from app.services.metrics import overview

router = APIRouter(prefix="/v1/metrics", tags=["metrics"], dependencies=[Depends(require_api_key)])


@router.get("/overview", response_model=MetricsOverview)
def metrics_overview() -> MetricsOverview:
    return overview()


def _dashboard_rows() -> list[dict]:
    """
    Returns per-call dashboard records stored at:
      CALLS[call_id].summary["dashboard"]
    """
    rows: list[dict] = []
    with LOCK:
        for st in CALLS.values():
            if isinstance(st.summary, dict):
                dash = st.summary.get("dashboard")
                if isinstance(dash, dict):
                    rows.append(dash)

    rows.sort(key=lambda r: float(r.get("ended_at") or 0.0), reverse=True)
    return rows


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

    accepted = [r for r in rows if r.get("outcome") == "ACCEPTED_TRANSFERRED" or r.get("agreed") is True]
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
        # Keep exact platform values; bucket missing as "Unknown"
        key = r.get("sentiment") or "Unknown"
        counts[key] = counts.get(key, 0) + 1
    return counts


@router.get("/dashboard/calls")
def dashboard_calls(limit: int = 50):
    rows = _dashboard_rows()
    limit = max(1, min(limit, 500))
    return rows[:limit]


@router.get("/dashboard/calls/{call_id}")
def dashboard_call_detail(call_id: str):
    with LOCK:
        st = CALLS.get(call_id)
        if not st:
            raise HTTPException(status_code=404, detail="Call not found")
        dash = None
        if isinstance(st.summary, dict):
            dash = st.summary.get("dashboard")
        if not isinstance(dash, dict):
            raise HTTPException(status_code=404, detail="No dashboard data for call (call may not be ended yet)")

        return {
            "dashboard": dash,
            "call_state": {
                "call_id": st.call_id,
                "started_at": st.started_at,
                "ended_at": st.ended_at,
                "from_number": st.from_number,
                "metadata": st.metadata,
                "raw_outcome": st.outcome,
            },
            "raw_summary": st.summary,
        }
