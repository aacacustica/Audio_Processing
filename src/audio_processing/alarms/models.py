from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

@dataclass(frozen=True)
class AlarmAggregation:

    start_time: datetime
    end_time: datetime

    aggregation_seconds: float

    measurement_ids: tuple[int, ...]

    la_db: float | None
    lc_db: float | None
    lz_db: float | None

    la_max_db: float | None
    la_min_db: float | None

    percentile_90_db: float | None
    lc_la_mean_db: float | None

    n_peaks: int

    third_octaves_db: dict[float,float]

@dataclass(frozen=True)
class AlarmResult:

    alarm_type: str

    start_time: datetime
    end_time: datetime
    aggregation_seconds: float
    
    measurement_ids: tuple[int, ...]

    value: float | None = None
    threshold: float | None = None

    category: str | None = None

    details: dict[str,Any] | None = None