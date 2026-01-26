from __future__ import annotations

from typing import List, Optional
from fastapi import HTTPException

from app.core.state import LOADS
from app.schemas.domain import Load


def _norm(s: Optional[str]) -> str:
    if not s:
        return ""
    return " ".join(s.strip().lower().split())


def _match_field(actual: str, wanted: Optional[str]) -> bool:
    if wanted is None or wanted == "":
        return True
    return _norm(actual) == _norm(wanted)


def search(origin: Optional[str], destination: Optional[str], equipment: Optional[str], limit: int) -> List[Load]:
    origin = origin or None
    destination = destination or None
    equipment = (equipment or "").strip().lower() or None

    results: List[Load] = []
    for load in LOADS:
        if not _match_field(load.origin, origin):
            continue
        if not _match_field(load.destination, destination):
            continue
        if equipment and _norm(load.equipment_type) != _norm(equipment):
            continue
        results.append(load)

    results.sort(key=lambda l: float(l.loadboard_rate), reverse=True)

    return results[: max(1, int(limit or 1))]


def get_by_id(load_id: str) -> Load:
    for l in LOADS:
        if l.load_id == load_id:
            return l
    raise HTTPException(status_code=404, detail=f"Load not found: {load_id}")
