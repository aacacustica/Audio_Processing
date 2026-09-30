from dataclasses import dataclass
from datetime import datetime

THIRD_OCTAVE_NOMINAL_BANDS = ( 12.5, 16.0, 20.0, 25.0, 31.5, 40.0, 50.0, 63.0, 80.0, 100.0, 125.0, 160.0, 200.0, 250.0, 315.0, 400.0, 500.0, 630.0, 800.0, 1000.0, 1250.0, 1600.0, 2000.0, 2500.0, 3150.0, 4000.0, 5000.0, 6300.0, 8000.0, 10000.0, 12500.0, 16000.0, 20000.0 )

@dataclass(frozen=True)
class AcousticLevelResult:

    timestamp:              datetime

    la_db:                  float
    lc_db:                  float
    lz_db:                  float

    lc_la_db:               float

    la_max_db:              float
    la_min_db:              float

    aggregation_seconds:    float

@dataclass(frozen=True)
class ThirdOctaveResult:

    timestamp:              datetime
    aggregation_seconds:    float
    bands_db:               dict[float,float]

@dataclass(frozen=True)
class AcousticFileResult:
    levels: list[AcousticLevelResult]
    third_octaves: list[ThirdOctaveResult]