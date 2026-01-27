from sqlalchemy.dialects.postgresql import insert

import app.db as db
from app.models import CallRecord


def upsert_call_record(
    record: dict,
    started_at: float | None,
    raw_outcome: str | None,
    raw_summary: dict | None,
):
    db.require_db()

    values = {
        "call_id": record.get("call_id"),
        "started_at": int(started_at) if started_at is not None else None,
        "ended_at": int(record.get("ended_at")) if record.get("ended_at") is not None else None,
        "outcome": record.get("outcome"),
        "sentiment": record.get("sentiment"),
        "verified": record.get("verified"),
        "load_id": record.get("load_id"),
        "loadboard_rate": record.get("loadboard_rate"),
        "rounds": record.get("rounds"),
        "carrier_first_offer": record.get("carrier_first_offer"),
        "carrier_last_offer": record.get("carrier_last_offer"),
        "final_offer": record.get("final_offer"),
        "agreed": record.get("agreed"),
        "transfer_to_rep": record.get("transfer_to_rep"),
        "raw_outcome": raw_outcome,
        "raw_summary": raw_summary,
    }

    stmt = insert(CallRecord).values(**values).on_conflict_do_update(
        index_elements=[CallRecord.call_id],
        set_=values,
    )

    with db.SessionLocal() as session:
        session.execute(stmt)
        session.commit()
