from __future__ import annotations

import numpy as np
import pandas as pd

from audio_processing.alarms.models import AlarmAggregation
from audio_processing.persistence.models import AcousticMeasurement,AcousticThirdOctaveMeasurements

THIRD_OCTAVE_COLUMNS = {
    12.5: "band_12_5_db",
    16.0: "band_16_db",
    20.0: "band_20_db",
    25.0: "band_25_db",
    31.5: "band_31_5_db",
    40.0: "band_40_db",
    50.0: "band_50_db",
    63.0: "band_63_db",
    80.0: "band_80_db",
    100.0: "band_100_db",
    125.0: "band_125_db",
    160.0: "band_160_db",
    200.0: "band_200_db",
    250.0: "band_250_db",
    315.0: "band_315_db",
    400.0: "band_400_db",
    500.0: "band_500_db",
    630.0: "band_630_db",
    800.0: "band_800_db",
    1000.0: "band_1000_db",
    1250.0: "band_1250_db",
    1600.0: "band_1600_db",
    2000.0: "band_2000_db",
    2500.0: "band_2500_db",
    3150.0: "band_3150_db",
    4000.0: "band_4000_db",
    5000.0: "band_5000_db",
    6300.0: "band_6300_db",
    8000.0: "band_8000_db",
    10000.0: "band_10000_db",
    12500.0: "band_12500_db",
    16000.0: "band_16000_db",
    20000.0: "band_20000_db",
}

def leq_safe(values) -> float | None:

    values = np.asanyarray(values,dtype=float)
    values = values[np.isfinite(values)]

    if values.size == 0: return None

    return float(10.0 * np.log10(np.mean(10.0 ** (values / 10.0))))

def aggregate_measurements(measurements: list[AcousticMeasurement],*,third_octaves: list[AcousticThirdOctaveMeasurements],peak_apex_measurement_ids: set[int],aggregation_seconds: int) -> list[AlarmAggregation]:

    if not measurements: return []

    octave_by_measurement = {row.id_medicion: row for row in third_octaves}

    rows = []
    results = []
    rule = (f"{int(aggregation_seconds)}s")

    for measurement in measurements:

        row = {
            "datetime" :    measurement.datetime,
            "id_medicion" : measurement.id_medicion,
            "LA":           measurement.la_db,
            "LC":           measurement.lc_db,
            "LZ":           measurement.lz_db,
            "LAmax":        measurement.la_max_db,
            "LAmin":        measurement.la_min_db,
            "LC-LA":        measurement.lc_la_db,
            "is_peak":      measurement.id_medicion in peak_apex_measurement_ids
        }

        octave = octave_by_measurement.get(measurement.id_medicion)

        if octave is not None:
            for frequency,column_name in THIRD_OCTAVE_COLUMNS.items(): row[frequency] = getattr(octave,column_name)

        rows.append(row)

    df = pd.DataFrame(rows)
    
    df['datetime'] = pd.to_datetime(df['datetime'],utc=True)
    
    df = df.sort_values("datetime")
    df = df.set_index("datetime")

    for start_time,group in df.resample(rule):

        if group.empty: continue

        measurement_ids = tuple(int(value) for value in group['id_medicion'].dropna())
        la_values = (group['LA'].dropna().to_numpy(dtype=float))

        third_octaves_db = {}

        for frequency in THIRD_OCTAVE_COLUMNS:

            if frequency not in group: continue

            value = leq_safe(group[frequency])

            if value is not None: third_octaves_db[frequency] = value

        results.append(AlarmAggregation(
            start_time              = start_time.to_pydatetime(),
            end_time                = (start_time + pd.Timedelta(seconds = aggregation_seconds)).to_pydatetime(),
            aggregation_seconds     = float(aggregation_seconds),
            measurement_ids         = measurement_ids,
            la_db                   = leq_safe(group['LA']),
            lc_db                   = leq_safe(group['LC']),
            lz_db                   = leq_safe(group['LZ']),
            la_max_db               = leq_safe(group['LAmax']),
            la_min_db               = leq_safe(group['LAmin']),
            percentile_90_db        = float(np.percentile(la_values,90)) if la_values.size else None,
            lc_la_mean_db           = float(group['LC-LA'].dropna().mean()) if group['LC-LA'].notna().any() else None,
            n_peaks                 = int(group['is_peak'].fillna(False).astype(bool).sum()),
            third_octaves_db        = third_octaves_db

        ))

    return results

   

   