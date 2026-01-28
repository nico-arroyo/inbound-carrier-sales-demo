from sqlalchemy.dialects.postgresql import insert

import app.db as db
from app.models import CallRecord


def upsert_call_record(record: dict, summary_text: str | None,):
    db.require_db()

    values = {
        "call_id": record.get("call_id"),
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
        "summary": summary_text,
    }

    update_values = dict(values)
    if summary_text is None:
        update_values.pop("summary", None)

    stmt = insert(CallRecord).values(**values).on_conflict_do_update(
        index_elements=[CallRecord.call_id],
        set_=values,
    )

    with db.SessionLocal() as session:
        session.execute(stmt)
        session.commit()