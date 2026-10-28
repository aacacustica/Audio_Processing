from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path
from zoneinfo import ZoneInfo

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from audio_processing.alarms.models import AlarmAggregation

DB_LOWER_LIMIT = 30
DB_UPPER_LIMIT = 105

def _local_timestamp(value,timezone:ZoneInfo) -> pd.Timestamp | None:
    
    timestamp = pd.Timestamp(value)
    
    
    if value is None or pd.isna(value): return None
    if timestamp.tzinfo is None: return timestamp.tz_localize(timezone)

    return timestamp.tz_convert(timezone)


def _energy_average(values: pd.Series) -> float:

    values_array = values.to_numpy(dtype=float)

    return float(10.0 * np.log10(np.mean(np.power(10.0,values_array/10.0))))

def render_l90_alarm_visualization(aggregations: Iterable[AlarmAggregation],output_dir: Path, * ,plot_name: str, threshold_db: float, timezone_name: str = "Europe/Madrid") -> dict[str,Path] | None:

    timezone = ZoneInfo(timezone_name)
    rows: list[dict[str,object]] = []

    for aggregation in aggregations: 
        value = aggregation.percentile_90_db

        if value is None or pd.isna(value): continue

        timestamp = _local_timestamp(aggregation.start_time, timezone)
        
        if timestamp is None: continue

        rows.append({"timestamp":timestamp,'l90_db':float(value)})

    if not rows: return None

    frame = pd.DataFrame(rows).sort_values("timestamp")
    frame = frame.drop_duplicates(subset=["timestamp"], keep="last")
    frame["local_date"] = frame["timestamp"].map(lambda value: value.date().isoformat())

    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", plot_name).strip("_") or "source"
    output_dir = Path(output_dir)
    outputs: dict[str, Path] = {}

    for local_date, day_frame in frame.groupby('local_date',sort=True):

        day_frame = day_frame.sort_values("timestamp")
        l90_values = day_frame["l90_db"]
        daily_mean = round(_energy_average(l90_values), 2)
        alarm_threshold = daily_mean + float(threshold_db)
        alarm_rows = day_frame[day_frame["l90_db"] > alarm_threshold]

        timestamps = [value.to_pydatetime() for value in day_frame["timestamp"]]
        fig, ax = plt.subplots(figsize=(15, 8))

        try:
            ax.plot(timestamps,l90_values.to_numpy(),label='90th Percentile')
            ax.plot([value.to_pydatetime() for value in alarm_rows['timestamp']],alarm_rows['l90_db'].to_numpy(),'ro',label='Alarm')
            ax.axhline(daily_mean,color='r',linestyle='--',label='avg',linewidth=2)
            ax.axhline(alarm_threshold,color='g',linestyle='--',label=f"avg + {threshold_db:g} dB",linewidth=2)

            ax.set_title(f"{plot_name} | 90th Percentile | Alarm | {local_date}")
            ax.set_ylabel("dB(A)")
            ax.grid(True)
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d %H:%M",tz=timezone))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=4,tz=timezone))
            ax.tick_params(axis='x',labelrotation=90)
            
            if len(timestamps) == 1: 
                point = pd.Timestamp(timestamps[0])
                ax.set_xlim((point - pd.Timedelta(hours=2)).to_pydatetime(),(point + pd.Timedelta(hours=2).to_pydatetime()))
            else:
                ax.set_xlim(timestamps[0],timestamps[-1])

            ax.set_ylim(DB_LOWER_LIMIT,DB_UPPER_LIMIT)
            ax.legend(loc='upper left',bbox_to_anchor=(1.02,1))
            fig.tight_layout()

            day_dir = output_dir / f"day_{local_date}"
            day_dir.mkdir(parents=True,exist_ok=True)
            output_path = day_dir / f"{safe_name}_L90_Alarm.png"
            fig.savefig(output_path,dpi=150,bbox_inches='tight')
            outputs[local_date] = output_path
        finally:
            plt.close(fig)

    return outputs or None

