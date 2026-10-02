from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PeakResult:

    peak_timestamp: datetime

    start_time: datetime
    end_time: datetime

    duration_seconds: float
    sample_count: int

    peak_la_db: float
    leq_db: float
    prominence_db: float

    la_values: list[float]

