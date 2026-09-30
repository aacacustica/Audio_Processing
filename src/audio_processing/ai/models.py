from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PredictionResult:

    timestamp: datetime
    window_seconds: float
    class_name: str
    probability: float
    