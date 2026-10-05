from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Callable

import numpy as np

from audio_processing.alarms.aggregation import leq_safe
from audio_processing.alarms.models import AlarmAggregation,AlarmResult
from audio_processing.alarms.regulation import evaluation_period,get_oca_limit

PeriodResolver = Callable[[datetime], str]
OcaLimitResolver = Callable[[datetime], float]

LOW_FREQUENCIES = (
    50.0,
    63.0,
    80.0,
    100.0,
    125.0,
    160.0,
)

MEDIUM_FREQUENCIES = (
    200.0,
    250.0,
    315.0,
    400.0,
    500.0,
    630.0,
    800.0,
    1000.0,
    1250.0,
)

HIGH_FREQUENCIES = (
    1600.0,
    2000.0,
    2500.0,
    3150.0,
    4000.0,
    5000.0,
    6300.0,
    8000.0,
)

TONAL_LOW_FREQUENCIES = (
    25.0,
    31.5,
    40.0,
    50.0,
    63.0,
    80.0,
    100.0,
    125.0,
)

TONAL_MEDIUM_FREQUENCIES = (
    160.0,
    200.0,
    250.0,
    315.0,
    400.0,
)

TONAL_HIGH_FREQUENCIES = (
    500.0,
    630.0,
    800.0,
    1000.0,
    1250.0,
    1600.0,
    2000.0,
    2500.0,
    3150.0,
    4000.0,
    5000.0,
    6300.0,
)


TONAL_FREQUENCIES = (
    TONAL_LOW_FREQUENCIES
    + TONAL_MEDIUM_FREQUENCIES
    + TONAL_HIGH_FREQUENCIES
)


TONAL_THRESHOLDS = {
    "LOW": 15.0,
    "MEDIUM": 8.0,
    "HIGH": 5.0,
}

def _tonal_group(frequency:float) -> str:

    if frequency in TONAL_LOW_FREQUENCIES: return "LOW"
    if frequency in TONAL_MEDIUM_FREQUENCIES: return "MEDIUM"
    if frequency in TONAL_HIGH_FREQUENCIES: return "HIGH"

    raise ValueError(f"Frecuencia tonal desconocida: {frequency}")

def _detect_tonal_components(aggregation: AlarmAggregation) -> list[dict]:

    values = aggregation.third_octaves_db
    detections = []

    for index, frequency in enumerate(TONAL_FREQUENCIES):

        current_value = values.get(frequency)

        if (current_value is None or not np.isfinite(current_value)): continue

        previous_frequency = (TONAL_FREQUENCIES[index - 1] if index > 0 else None)
        next_frequency = (TONAL_FREQUENCIES[index + 1] if index < len(TONAL_FREQUENCIES) - 1 else None)
        previous_value = (values.get(previous_frequency) if previous_frequency is not None else None)
        next_value = (values.get(next_frequency) if next_frequency is not None else None)

        if previous_value is None: previous_value = next_value
        if next_value is None: next_value = previous_value

        if (previous_value is None or next_value is None): continue
        if (not np.isfinite(previous_value) or not np.isfinite(next_value)): continue

        previous_diff = round(current_value - previous_value,2)
        next_diff = round(current_value - next_value,2)
        band = _tonal_group(frequency)
        threshold = TONAL_THRESHOLDS[band]

        if (previous_diff <= threshold or next_diff <= threshold): continue

        detections.append({
            "band": band,
            "frequency_hz": frequency,
            "value_db": float(current_value),
            "previous_frequency_hz":previous_frequency,
            "previous_value_hz":previous_value,
            "previous_diff_db":previous_diff,
            "next_frequency_hz":next_frequency,
            "next_value_hz":next_value,
            "next_diff_db": next_diff,
            "threshold_db":threshold
        })


    return detections


def detect_tonal_alarm(aggregations: list[AlarmAggregation]) -> list[AlarmResult]:

    if not aggregations: return []

    ordered = sorted(aggregations,key=lambda item: item.start_time)

    detections_by_hour = defaultdict(list)
    aggregations_by_hour = defaultdict(list)

    for aggregation in ordered:

        hour = aggregation.start_time.replace(
            minute=0,
            second=0,
            microsecond=0
        )

        aggregations_by_hour[hour].append(aggregation)
        detections_by_hour[hour].extend(_detect_tonal_components(aggregation))

    results = []

    for hour in sorted(aggregations_by_hour):

        hour_aggregations = aggregations_by_hour[hour]
        detections = detections_by_hour[hour]

        if not detections: continue

        counts = Counter(detection['band'] for detection in detections)

        maximum_count = max(counts.values())

        predominant = [band for band,count in counts.items() if count == maximum_count]

        if len(predominant) != 1: continue

        predominant_band = predominant[0]

        measurement_ids = tuple(dict.fromkeys(measurement_id for aggregation in hour_aggregations for measurement_id in aggregation.measurement_ids))

        results.append(
            AlarmResult(
                alarm_type="tonal_frequency",
                start_time=hour,
                end_time=(hour + timedelta(hours=1)),
                aggregation_seconds=3600.0,
                measurement_ids=(measurement_ids),
                category=(predominant_band),
                details={
                    "band_counts":dict(counts),    
                    "detections":detections,                  
                    "n_peaks":sum(aggregation.n_peaks for aggregation in hour_aggregations),
                },
            )
        )

    return results

def sum_db_safe(values) -> float | None:

    values = np.array(values,dtype=float)
    values = values[np.isfinite(values)]

    if values.size == 0: return None

    return float(10.0 * np.log10(np.sum(10.0 ** (values / 10.0))))

def _sum_frequency_group(aggregation: AlarmAggregation,frequencies: tuple[float, ...]) -> float | None:

    values = [aggregation.third_octaves_db[frequency] for frequency in frequencies if frequency in aggregation.third_octaves_db]

    return sum_db_safe(values)

def detect_frequency_composition_alarms(aggregations: list[AlarmAggregation],*,jump_threshold_db: float) -> list[AlarmResult]:

    ordered = sorted(aggregations,key=lambda item: item.start_time)

    results = []

    previous_low = None
    previous_high = None

    for aggregation in ordered:

        low = _sum_frequency_group(aggregation,LOW_FREQUENCIES)
        medium = _sum_frequency_group(aggregation,MEDIUM_FREQUENCIES)
        high = _sum_frequency_group(aggregation,HIGH_FREQUENCIES)

        available = {"low": low, "medium":medium, "high":high}
        valid = {key:value for key,value in available.items() if value is not None}

        if not valid: continue

        maximum = max(valid.values())
        predominant = [key for key,value in valid.items() if value == maximum]

        predominant_frequency = (predominant[0] if len(predominant) == 1 else 'none')

        low_jump = (low is not None and previous_low is not None and low > previous_low + jump_threshold_db)
        high_jump = (high is not None and previous_high is not None and high > previous_high + jump_threshold_db)

        triggered_bands = []

        if low_jump: triggered_bands.append('low')
        if high_jump: triggered_bands.append('high')

        if triggered_bands: 
            jumps = []

            if low_jump: jumps.append(low - previous_low)
            if high_jump: jumps.append(high - previous_high)

            results.append(
            AlarmResult(
                alarm_type=("frequency_composition"),
                start_time=(aggregation.start_time),
                end_time=(aggregation.end_time),
                aggregation_seconds=(aggregation.aggregation_seconds),
                measurement_ids=(aggregation.measurement_ids),
                value=float(max(jumps)),
                threshold=float(jump_threshold_db),
                category="+".join(triggered_bands),
                details={
                    "low_db": low,
                    "medium_db": medium,
                    "high_db": high,
                    "previous_low_db":previous_low,                      
                    "previous_high_db":previous_high,                     
                    "low_jump_db": ( low - previous_low if low_jump else None),
                    "high_jump_db": ( high - previous_high if high_jump else None),
                    "predominant_frequency": predominant_frequency,                     
                    "n_peaks": aggregation.n_peaks,
                        
                },
            )
        )


        if low is not None: previous_low = low
        if high is not None: previous_high = high

    return results

def detect_oca_alarms(aggregations: list[AlarmAggregation],*,oca_type: str) -> list[AlarmResult]:

    result = []

    for aggregation in aggregations:

        if aggregation.la_db is None: continue

        threshold = get_oca_limit(aggregation.start_time,oca_type=oca_type)

        if aggregation.la_db <= threshold: continue

        result.append(
            AlarmResult(
                alarm_type =            "oca",
                start_time =            aggregation.start_time,
                end_time =              aggregation.end_time,
                aggregation_seconds =   aggregation.aggregation_seconds,
                measurement_ids =       aggregation.measurement_ids,
                value =                 aggregation.la_db,
                threshold =             threshold,
                category =              evaluation_period(aggregation.start_time),
                details =               {'n_peaks': aggregation.n_peaks,
                                         'oca_type': oca_type}
            )
        )

    return result

def detect_lc_la_alarms(aggregations: list[AlarmAggregation],*,normative_threshold_db: float, dynamic_threshold_db: float) -> list[AlarmResult]:

    values_by_period = defaultdict(list)

    for aggregation in aggregations:

        value = aggregation.lc_la_mean_db

        if value is None: continue

        period = evaluation_period(aggregation.start_time)

        values_by_period[period].append(value)

    references = {period: leq_safe(values) for period, values in values_by_period.items()}

    results = []

    for aggregation in aggregations:

        value = aggregation.lc_la_mean_db

        if value is None: continue

        period = evaluation_period(aggregation.start_time)

        reference = references.get(period)

        dynamic_limit = reference + dynamic_threshold_db if reference is not None else None
        normative_trigger = value > normative_threshold_db
        dynamic_trigger = dynamic_limit is not None and value > dynamic_limit

        if not (normative_trigger or dynamic_trigger): continue

        triggered_by = []

        if normative_trigger: triggered_by.append('normative')
        if dynamic_trigger: triggered_by.append('dynamic')

        results.append(
            AlarmResult(
                alarm_type="lc_la",
                start_time=aggregation.start_time,
                end_time=aggregation.end_time,
                aggregation_seconds=( aggregation.aggregation_seconds),              
                measurement_ids=( aggregation.measurement_ids),         
                value=value,
                threshold=( normative_threshold_db if normative_trigger else dynamic_limit),
                category=period,
                details={
                    "period":                   period,
                    "dynamic_reference_db":     reference,    
                    "dynamic_limit_db":         dynamic_limit,      
                    "normative_threshold_db":   normative_threshold_db,         
                    "dynamic_threshold_db":     dynamic_threshold_db,             
                    "triggered_by":             triggered_by,             
                    "n_peaks":                  aggregation.n_peaks,                     
                },
            )
        )

    return results

def detect_lmax_alarms(aggregations: list[AlarmAggregation],*,threshold_db: float) -> list[AlarmResult]:

    results = []

    for aggregation in aggregations:

        if aggregation.la_max_db is None: continue

        if aggregation.la_max_db <= threshold_db: continue

        results.append(
            AlarmResult(
                alarm_type =            "lmax",
                start_time =            aggregation.start_time,
                end_time =              aggregation.end_time,
                aggregation_seconds =   aggregation.aggregation_seconds,
                measurement_ids =       aggregation.measurement_ids,
                value =                 aggregation.la_max_db,
                threshold =             threshold_db,
                details =               {'n_peaks': aggregation.n_peaks}
            )
        ) 

    return results

def detect_l90_dynamic_alarms(aggregations: list[AlarmAggregation],*,threshold_db: float, rolling_window: int = 3) -> list[AlarmResult]:

    if rolling_window <= 0: raise ValueError(f"El valor de rolling_window debe de ser > 0.")

    ordered = sorted(aggregations,key=lambda item: item.start_time)
    results = []

    for index, aggregation in enumerate(ordered):

        value = aggregation.percentile_90_db

        if value is None: continue

        start_index = max(0, index - rolling_window + 1)

        window_values = [ item.percentile_90_db for item in ordered[start_index:index + 1] if item.percentile_90_db is not None]

        if not window_values: continue

        rolling_median = float(np.median(window_values))

        threshold = rolling_median + threshold_db

        if value <= threshold: continue

        results.append(
            AlarmResult(
                alarm_type                      = "l90_dynamic",
                start_time                      = aggregation.start_time,
                end_time                        = aggregation.end_time,
                aggregation_seconds             = (aggregation.aggregation_seconds),  
                measurement_ids                 = (aggregation.measurement_ids),
                value                           = value,
                threshold                       = float(threshold),          
                details                         = {"rolling_median_db": (rolling_median),
                                                 "threshold_offset_db": (threshold_db),
                                                 "rolling_window": (rolling_window),
                                                 "n_peaks": aggregation.n_peaks,       },  
            )
        )

    return results

