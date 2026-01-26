from __future__ import annotations

from typing import List, Optional, Tuple

from fastapi import HTTPException

from app.core.state import LOADS
from app.schemas.domain import Load


def _norm(s: Optional[str]) -> str:
    return (s or "").strip().lower()


def score_load(load: Load, origin: Optional[str], destination: Optional[str], equipment: Optional[str]) -> float:
    score = 0.0
    o = _norm(origin)
    d = _norm(destination)
    e = _norm(equipment)

    lo = _norm(load.origin)
    ld = _norm(load.destination)
    le = _norm(load.equipment_type)

    if o:
        if lo == o:
            score += 3
        elif o in lo or lo in o:
            score += 2

    if d:
        if ld == d:
            score += 3
        elif d in ld or ld in d:
            score += 2

    if e:
        if le == e:
            score += 2

    score += min(load.rate / 10000.0, 0.5)
    return score


def search(origin: Optional[str], destination: Optional[str], equipment: Optional[str], limit: int) -> List[Load]:
    scored: List[Tuple[float, Load]] = []

    for load in LOADS:
        if equipment and _norm(load.equipment_type) != _norm(equipment):
            continue

        s = score_load(load, origin, destination, equipment)

        # If user specified lane constraints, avoid ultra-weak matches
        if (origin or destination) and s < 2:
            continue

        scored.append((s, load))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [l for _, l in scored[:limit]]


def get_by_id(load_id: str) -> Load:
    for l in LOADS:
        if l.load_id == load_id:
            return l
    raise HTTPException(status_code=404, detail=f"Load not found: {load_id}")
