from __future__ import annotations

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from audio_processing.visualization.configs import OCA_LIMITS
from audio_processing.visualization.time_plot import _leq, _oca_limit, _safe_filename


def render_time_plot_week(measurements,output_dir:Path,plot_name:str,aggregation_seconds:int,percentiles:list[int],oca_type:str,correction_db:float=0.0,timezone_name:str="Europe/Madrid") -> dict[str,Path] | None:

    if aggregation_seconds <= 0 : raise ValueError(f"Aggregation_seconds debe de ser mayor que cero: {aggregation_seconds}")
    if oca_type not in OCA_LIMITS: raise ValueError(f"Tipo de OCA desconocido: {oca_type}")

    for percentile in percentiles: 
        if not 0 <= percentile <= 100: raise ValueError(f"Percentil fuera de rango: {percentile}")

    records = [
        {
            "datetime": row.datetime,
            "la_db": row.la_db,
            "la_max_db": row.la_max_db,
            "la_min_db": row.la_min_db
        }
        for row in measurements if row.datetime is not None
    ]

    if not records: return None

    data = pd.DataFrame(records)
    data['datetime'] = pd.to_datetime(data['datetime'],utc=True).dt.tz_convert(timezone_name)

    for column in ('la_db','la_max_db','la_min_db'):
        data[column] = pd.to_numeric(data[column],errors='coerce') + correction_db

    data = data.dropna(subset=['datetime','la_db']).sort_values('datetime')

    if data.empty: return None

    data = data.set_index('datetime')
    data['oca'] = [_oca_limit(timestamp,OCA_LIMITS[oca_type]) for timestamp in data.index]
    local_dates = data.index.normalize()
    data['week_start'] = local_dates - pd.to_timedelta(local_dates.dayofweek,unit='D')

    frequency = f"{aggregation_seconds}s"
    output_dir = Path(output_dir)
    safe_name = _safe_filename(plot_name)
    outputs: dict[str,Path] = {}

    for week_start,week_data in data.groupby("week_start",sort=True):
        week_label = week_start.date().isoformat()
        weekly = week_data.drop(columns="week_start").resample(frequency).agg(
            {
                "la_db":_leq,
                "la_max_db":"max",
                "la_min_db":"min",
                "oca":"min"
            }
        )

        for percentile in percentiles:
            quantile = (100.0 - percentile) / 100
            weekly[f"L{percentile}"] = week_data['la_db'].resample(frequency).quantile(quantile)

        weekly = weekly.dropna(subset='la_db')

        if weekly.empty: continue

        week_dir = output_dir / f"week_{week_label}"
        week_dir.mkdir(parents=True, exist_ok=True)

        png_path = (week_dir / f"{safe_name}_{aggregation_seconds}s_time_plot_week_{week_label}.png")

        fig,ax = plt.subplots(figsize=(20,10))

        try:
            ax.set_facecolor("white")
            ax.plot(weekly.index,weekly['la_db'],linewidth=3,color='red',label='LAeq')
            ax.plot(weekly.index,weekly['la_max_db'],linewidth=1,color="#FF99FF",label='Lmax')
            ax.plot(weekly.index,weekly['la_min_db'],linewidth=1,color="#92D050",label='Lmin')
            ax.plot(weekly.index,weekly['oca'],linewidth=1,color="#00B0F0",label='OCA')

            for percentile in percentiles:
                ax.plot(weekly.index,weekly[f"L{percentile}"],linewidth=0.8,label=f"L{percentile}")

            locator = mdates.AutoDateLocator(minticks=4, maxticks=10, tz=timezone_name)
            ax.xaxis.set_major_locator(locator)
            ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator,tz=timezone_name))
            ax.set_ylim(30, 105)
            ax.set_ylabel("dB(A)")
            ax.set_xlabel("Hora")
            ax.set_title(f"{plot_name} Nivel equivalente {aggregation_seconds}s - Semana {week_label}")
            ax.tick_params(axis='x',labelrotation=90)
            ax.set_xlim(weekly.index.min(),weekly.index.max() + pd.Timedelta(seconds=aggregation_seconds))

            ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1))
            ax.grid(True, which="both", linestyle="--", linewidth=0.5)
            fig.tight_layout()
            fig.savefig(png_path, dpi=300)

        finally:
            plt.close(fig)

        outputs[week_label] = png_path

    return outputs or None