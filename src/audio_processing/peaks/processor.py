import numpy as np
import pandas as pd

from scipy.signal import find_peaks

from audio_processing.peaks.models import PeakResult


def calculate_leq(values: np.ndarray) -> float:

    leq = float(10.0 * np.log10(np.mean(10.0 ** (values/ 10.0))))

    return leq


def detect_peaks(measurements,*,window_size: int , adding_threshold: float, width: float, prominence: float) -> list[PeakResult]:

    if not measurements: return []

    measurements        = sorted(measurements, key=lambda m: m.datetime)
    la                  = pd.Series([measurement.la_db for measurement in measurements],dtype='float64')
    dynamic_threshold   = (la.rolling(window=window_size,min_periods=1).median() + adding_threshold)
    results             = []

    peak_indices, properties = find_peaks(la.to_numpy(),prominence=prominence,width=width)

    

    for peak_idx, left_ip, right_ip, peak_prominence in zip(peak_indices, properties["left_ips"],properties["right_ips"],properties["prominences"]):

        if (la.iloc[peak_idx] <= dynamic_threshold.iloc[peak_idx]): continue

        start = max(0,int(np.floor(left_ip)))
        end = min(len(measurements) - 1, int(np.ceil(right_ip)))
        values = (la.iloc[start:end+1].dropna().to_numpy())

        if values.size == 0: continue   

        start_time = measurements[start].datetime
        end_time = measurements[end].datetime

        results.append(PeakResult(
            peak_timestamp      = measurements[int(peak_idx)].datetime,
            start_time          = start_time,
            end_time            = end_time,
            duration_seconds    = (end_time - start_time).total_seconds(),
            sample_count        = int(end - start + 1),
            peak_la_db          = float(la.iloc[peak_idx]),
            leq_db              = round(calculate_leq(values),1,),
            prominence_db       = float(peak_prominence),
            la_values           = [float(value) for value in values]
        ))

    return results