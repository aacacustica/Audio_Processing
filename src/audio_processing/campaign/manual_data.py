from dataclasses import dataclass
import pandas as pd
from audio_processing.campaign.models import MeasurementSource

@dataclass(frozen=True,slots=True)
class ManualSourceData:
    source: MeasurementSource
    acoustic: pd.DataFrame
    predictions: pd.DataFrame | None = None
    third_octave: pd.DataFrame | None = None
    