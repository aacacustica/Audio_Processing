from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path
from zoneinfo import ZoneInfo

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from audio_processing.alarms.models import AlarmAggregation
from audio_processing.alarms.regulation import get_oca_limit


DB_LOWER_LIMIT = 30
DB_UPPER_LIMIT = 105

def _local_timestamp(value,timezone_name: str) -> pd.Timestamp:

    timestamp = pd.Timestamp(value)

    if pd.isna(timestamp): raise ValueError(f"La agregación contiene start_time vacío.")
    if timestamp.tzinfo is None: return timestamp.tz_localize(ZoneInfo(timezone_name))

    return timestamp.tz_convert(ZoneInfo(timezone_name))

def _build_frame(aggregations: Iterable[AlarmAggregation], * , oca_type: str, timezone_name: str) -> pd.DataFrame:

    rows: list[dict[str,object]] = []

    for aggregation in aggregations: 
        
        if aggregation.la_db is None or pd.isna(aggregation.la_db): continue

        source_timestamp = pd.Timestamp(aggregation.start_time)

        if pd.isna(source_timestamp): raise ValueError(f"La agregación contiene start_time vacío.")

        evaluation_timestamp = (source_timestamp.tz_localize(ZoneInfo(timezone_name)) if source_timestamp.tzinfo is None else source_timestamp)
        timestamp = _local_timestamp(source_timestamp,timezone_name)
        laeq = float(aggregation.la_db)
        threshold = float(get_oca_limit(evaluation_timestamp.to_pydatetime(),oca_type=oca_type))

        rows.append(
            {
                "timestamp":timestamp,
                "laeq":laeq,
                "oca":threshold,
                "is_alarm": laeq > threshold
            }
        )

    if not rows: return pd.DataFrame(columns=['laeq','oca','is_alarm'])

    return pd.DataFrame(rows).sort_values("timestamp").drop_duplicates(subset=['timestamp'],keep='last').set_index('timestamp')

def _safe_plot_name(plot_name:str) -> str:

    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", plot_name).strip("_")

    if not safe_name: raise ValueError("plot_name debe contener al menos un carácter válido")

    return safe_name

def _save_oca_plot(frame: pd.DataFrame, * , output_path: Path, plot_name: str, timezone_name: str, title_suffix: str = 'Alarm') -> Path:

    output_path.parent.mkdir(parents=True,exist_ok=True)
    fig,ax = plt.subplots(figsize=(15,8))

    try:
        
        x_values = [timestamp.to_pydatetime() for timestamp in frame.index]
        ax.plot(x_values, frame["laeq"].to_numpy(), label="LAeq")
        exceedances = frame[frame["is_alarm"]]

        ax.plot([timestamp.to_pydatetime() for timestamp in exceedances.index],exceedances['laeq'].to_numpy(),'ro',label='LAeq Alarm')
        ax.plot(x_values, frame["oca"].to_numpy(), "r--", label="OCA", linewidth=2)
        ax.set_title(f"{plot_name} LAeq - OCA | {title_suffix}")
        ax.set_ylabel("dB(A)")

        if len(x_values) == 1:
            point = pd.Timestamp(x_values[0])
            ax.set_xlim(
                (point - pd.Timedelta(hours=2)).to_pydatetime(),
                (point + pd.Timedelta(hours=2)).to_pydatetime()
            )
        else:
            ax.set_xlim(x_values[0],x_values[-1])
        ax.set_ylim(DB_LOWER_LIMIT,DB_UPPER_LIMIT)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d %H:%M", tz=ZoneInfo(timezone_name)))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=4,tz=ZoneInfo(timezone_name)))
        ax.tick_params(axis="x", labelrotation=90)
        ax.grid(True)
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1))
        fig.tight_layout()
        fig.savefig(output_path, dpi=150)

    finally:
        plt.close(fig)

    return output_path


def render_oca_alarm_visualization(aggregations: Iterable[AlarmAggregation], output_dir: Path, * ,plot_name: str, oca_type: str, timezone_name: str = "Europe/Madrid") -> dict[str, Path | dict[str,Path]] | None:

    frame = _build_frame(aggregations,oca_type,timezone_name)

    if frame.empty: return None

    output_dir = Path(output_dir)
    safe_name = _safe_plot_name(plot_name)
    daily_path = _save_oca_plot(frame,output_path=output_dir / f"{safe_name}_OCA_Alarm.png",plot_name=plot_name,timezone_name=timezone_name)

    week_starts = pd.Series(frame.index,index=frame.index).map(lambda timestamp: timestamp.normalize() - pd.Timedelta(days=timestamp.weekday))

    weekly_paths: dict[str,Path] = []

    for week_start in sorted(week_starts.unique()):

        week_frame = frame.loc[week_starts[week_starts == week_start].index]
        week_label = week_start.strftime("%Y-%m-%d")

        weekly_paths[week_label] = _save_oca_plot(
            week_frame,
            output_path     = output_dir / f"week_{week_label}" / f"{safe_name}_OCA_Alarm.png",
            plot_name       = plot_name,
            timezone_name   = timezone_name,
            title_suffix    = f"Alarms | Week of {week_label}",
        )

    return {'daily_png': daily_path,'weekly_pngs': weekly_paths}