from __future__ import annotations

from app.core.state import LOCK, METRICS
from app.models.api import MetricsOverview


def overview() -> MetricsOverview:
    with LOCK:
        return MetricsOverview(
            calls_started=METRICS.calls_started,
            calls_ended=METRICS.calls_ended,
            negotiations_started=METRICS.negotiations_started,
            negotiations_accepted=METRICS.negotiations_accepted,
            negotiations_declined=METRICS.negotiations_declined,
            average_rounds_completed=round(METRICS.avg_rounds(), 2),
        )
