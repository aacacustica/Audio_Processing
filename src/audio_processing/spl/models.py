from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class AcousticLevelResult:

    timestamp: datetime

    la_db: float
    lc_db: float
    lz_db: float

    lc_la_db: float

    la_max_db: float
    la_min_db: float

    aggregation_seconds: float