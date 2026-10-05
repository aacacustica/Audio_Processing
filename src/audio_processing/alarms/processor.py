from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class AggregatedMeasurement:

    start_time: datetime
    end_time: datetime

    aggregation_seconds: float

    la_db: float | None
    lc_db: float | None
    lz_db: float | None
    la_max_db: float | None

    lc_la_mean_db: float | None
    l90_db: float | None

    has_peak: bool
    third_octaves: dict[str,float]