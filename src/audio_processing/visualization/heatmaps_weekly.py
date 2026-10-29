from __future__ import annotations

from pathlib import Path
import re

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from audio_processing.visualization.configs import LEGACY_CMAP, WEEKDAYS_ES
from audio_processing.visualization.time_plot import _leq


def save_weekly_heatmap(matrix:pd.DataFrame,*,output_path: Path,title: str, annotate: bool, axis_fontsize: int, title_fontsize:int,dpi:int) -> Path:

    fig,ax = plt.subplots(figsize=(20,10))

    try:
        options = {"annot": annotate}

        if annotate: options.update(fmt=".1f",annot_kws={"size":20})

        plot = sns.heatmap(matrix,vmin=30,vmax=85,cmap=LEGACY_CMAP,ax=ax,**options)

        ax.set_xlabel("Hora", fontsize=axis_fontsize)
        ax.set_ylabel("Día", fontsize=axis_fontsize)
        ax.set_title(title, fontsize=title_fontsize)
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=axis_fontsize)
        ax.set_xticklabels(ax.get_xticklabels(), rotation=90, fontsize=axis_fontsize)
        plot.collections[0].colorbar.ax.tick_params(labelsize=axis_fontsize)

        fig.tight_layout()
        fig.savefig(output_path, dpi=dpi)

    finally:
        plt.close(fig)

    return output_path


def render_acoustic_heatmaps_week(measurements,output_dir:Path,plot_name:str,timezone_name: str = "Europe/Madrid") -> dict[str,dict[str,Path]] | None:

    records = [{"datetime":row.datetime,"la_db":row.la_db} for row in measurements if row.datetime is not None and row.la_db is not None]

    if not records: return None

    data = pd.DataFrame(records)
    data['datetime'] = pd.to_datetime(data['datetime'],utc=True).dt.tz_convert(timezone_name)

    data['la_db'] = pd.to_numeric(data['la_db'],errors='coerce')
    data['la_db'] = pd.to_numeric(data['la_db'],errors='coerce')
    data = data.dropna(subset=['datetime','la_db'])

    if data.empty: return None

    timestamps = data["datetime"]
    weekday_numbers = timestamps.dt.dayofweek
    data["Día"] = weekday_numbers.map(lambda day: WEEKDAYS_ES[day])
    data["date_day"] = timestamps.dt.strftime("%Y-%m-%d") + " " + data["Día"]
    data["hour_label"] = timestamps.dt.strftime("%H:00")
    data['quarter_label'] = timestamps.dt.strftime("%H:") + (timestamps.dt.minute // 15 * 15).map(lambda minute: f"{minute:02d}")

    local_dates = timestamps.dt.normalize()
    data['week_start'] = local_dates - pd.to_timedelta(weekday_numbers,unit='D')

    output_dir = Path(output_dir)
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", plot_name).strip("_") or "source"
    outputs: dict[str,dict[str,Path]] = {}

    for week_start,week_data in data.groupby("week_start",sort=True):
        week_label = week_start.date().isoformat()

        hourly = pd.pivot_table(week_data,values='la_db',index='date_day',columns='hour_label',aggfunc=_leq).round(1)
        quarter_hourly = pd.pivot_table(week_data,values='la_db',index='date_day',columns='quarter_label',aggfunc=_leq).round(1)

        if hourly.empty and quarter_hourly.empty: continue

        week_dir = output_dir / f"week_{week_label}"
        week_dir.mkdir(parents=True, exist_ok=True)
        week_outputs: dict[str, Path] = {}

        if not hourly.empty:
            week_outputs['hourly'] = save_weekly_heatmap(hourly,output_path=week_dir/f"{safe_name}_heatmap_evolucion_week_{week_label}.png",title=f"{plot_name} Nivel equivalente  - Semana {week_label}",annotate=True,axis_fontsize=22,title_fontsize=22,dpi=350)
        if not quarter_hourly.empty:
            week_outputs['15min'] = save_weekly_heatmap(quarter_hourly,output_path=week_dir/f"{safe_name}_heatmap_evolucion_week_{week_label}.png",title=f"{plot_name} Nivel equivalente cada 15 minutos  - Semana {week_label}",annotate=False,axis_fontsize=22,title_fontsize=22,dpi=350)

        outputs[week_label] = week_outputs

    return outputs or None

