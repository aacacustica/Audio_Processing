from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

def _local_timestamp(value,timezone_name: str) -> pd.Timestamp | None:

    if value is None or pd.isna(value): return None

    timestamp = pd.Timestamp(value)

    if timestamp.tzinfo is None: return timestamp.tz_localize(timezone_name)

    return timestamp.tz_convert(timezone_name)

def render_alarm_visualizations(alarms,output_dir: Path, plot_name: str, timezone_name: str = "Europe/Madrid") -> dict[str,Path] | None:

    records: list[dict[str,object]] = []

    for alarm in alarms:

        start = _local_timestamp(alarm.start_time,timezone_name)
        end = _local_timestamp(alarm.end_time,timezone_name)

        if start is None or end is None: continue

        details = alarm.details
        
        records.append(
            {
                "alarm_id":alarm.id_alarma,
                "alarm_type":str(alarm.alarm_type or 'unknown'),
                "start_time": start,
                "end_time": end,
                "local_date": start.strftime("%Y-%m-%d"),
                "value": alarm.value,
                "threshold": alarm.threshold,
                "category": alarm.category,
                "aggregation_seconds":alarm.aggregation_seconds,
                "details":json.dumps(details,ensure_ascii=False,sort_keys=True,default=str)
                if details is not None else ""
            }
        )

    if not records: return None

    frame = pd.DataFrame(records).sort_values(['start_time',"alarm_type","alarm_id"])
    daily_counts = (frame.groupby(['local_date','alarm_type'],as_index=False)).size().rename(columns={"size":"alarm_count"}).sort_values(['local_date','alarm_type'])

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True,exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", plot_name).strip("_") or "source"
    detail_csv = output_dir / f"{safe_name}_alarms_detail.csv"
    daily_csv = output_dir / f"{safe_name}_alarms_daily_by_type.csv"
    daily_png = output_dir / f"{safe_name}_alarms_daily_by_type.png"

    frame.to_csv(detail_csv,index=False)
    daily_counts.to_csv(daily_csv,index=False)

    pivot = daily_counts.pivot(index="local_date", columns="alarm_type", values="alarm_count").fillna(0)
    fig_width = max(10, min(24, 0.65 * len(pivot.index) + 6))
    fig, ax = plt.subplots(figsize=(fig_width, 6))
    pivot.plot(kind="bar", stacked=True, ax=ax, colormap="tab20")
    ax.set_title(f"Alarmas acústicas por día y tipo: {plot_name}")
    ax.set_xlabel(f"Día local ({timezone_name})")
    ax.set_ylabel("Número de alarmas")
    ax.legend(title="Tipo de alarma", bbox_to_anchor=(1.02, 1), loc="upper left")
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(daily_png, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return {"daily_png": daily_png, "daily_csv": daily_csv, "detail_csv": detail_csv} 
