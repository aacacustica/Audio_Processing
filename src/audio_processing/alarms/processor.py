from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Callable

import numpy as np

from audio_processing.alarms.aggregation import leq_safe
from audio_processing.alarms.models import AlarmAggregation,AlarmResult
from audio_processing.alarms.regulation import evaluation_period,get_oca_limit

PeriodResolver = Callable[[datetime], str]
OcaLimitResolver = Callable[[datetime], float]

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

