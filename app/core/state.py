import json
import time
from pathlib import Path
from threading import RLock
from typing import Dict, List

from app.core.config import settings
from app.models.domain import CallState, Load, MetricsState, NegotiationState

LOCK = RLock()

LOADS: List[Load] = []
CALLS: Dict[str, CallState] = {}
NEGOTIATIONS: Dict[str, NegotiationState] = {}
METRICS = MetricsState()


def now_ts() -> float:
    return time.time()


def init_state() -> None:
    global LOADS

    file_name = settings.loads_file

    candidate_paths = [
        Path(file_name),
        Path("/app") / file_name,
        Path(__file__).resolve().parents[2] / file_name,
    ]

    seed_path = next((p for p in candidate_paths if p.exists()), None)
    if seed_path is None:
        raise RuntimeError(f"loads seed file not found. Tried: {[str(p) for p in candidate_paths]}")

    with open(seed_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    LOADS = [Load(**item) for item in raw]
    print(f"[startup] loaded {len(LOADS)} loads from {seed_path}")

init_state()
