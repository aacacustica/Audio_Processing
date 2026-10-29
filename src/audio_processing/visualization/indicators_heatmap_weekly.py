from __future__ import annotations

from pathlib import Path
import re

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from audio_processing.visualization.configs import INDICATOR_ORDER,LE_SECONDS,LEGACY_CMAP,WEEKDAYS_ES
from audio_processing.visualization.time_plot import _leq

def render_indicator_heatmap_week(measurements,output_dir:Path,plot_name:str,timezone_name:str = "Europe/Madrid",correction_db:float=0.0) -> dict[str,tuple[Path,Path,Path]] | None:

    records = [{"datetime":row.datetime,"la_db":row.la_db + correction_db} for row in measurements if row.datetime is not None and row.la_db is not None]

    if not records: return None

    data = pd.DataFrame(records)
    data['datetime'] = pd.to_datetime(data['datetime'],utc=True).tz.tz_convert(timezone_name)
    data['la_db'] = pd.to_numeric(data['la_db'],errors='coerce')
    if data.empty: return None

    timestamps = data['timestamp']

    data["date"] = timestamps.dt.date
    weekday_numbers = timestamps.dt.dayofweek
    data["weekday"] = weekday_numbers.map(lambda day: WEEKDAYS_ES[day])
    data["date_weekday"] = timestamps.dt.strftime("%Y-%m-%d") + " " + data["weekday"]
    data["period"] = "Ln"
    data.loc[timestamps.dt.hour.between(7, 18), "period"] = "Ld"
    data.loc[timestamps.dt.hour.between(19, 22), "period"] = "Le"
    data['week_start'] = timestamps.dt.normalize() - pd.to_timedelta(weekday_numbers,unit='D')
    output_dir = Path(output_dir)
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", plot_name).strip("_") or "source"
    outputs: dict[str,tuple[Path,Path,Path]] = {}

    for week_start,week_data in data.groupby("week_start",sort=True):

        week_label = week_start.date().isoformat()
        week_data = week_data.copy()

        # Preserve legacy behavior: discard short Ld/Le/Ln segments on the
        # first and last observed days of each week.

        durations = week_data.groupby(['date','period'])['datetime'].agg(first='min',last='max')

        durations['seconds'] = (durations['last'] - durations['first']).dt.total_seconds()
        boundary_dates = {week_data['date'].min(),week_data['date'].ax()}

        for (day,period), row in durations.iterrows():
            if day in boundary_dates and row['seconds'] <= LE_SECONDS: week_data = week_data[~((week_data["date"] == day) & (week_data["period"] == period))]

        table = pd.pivot_table(week_data,index='date_weekday',columns='period',values='la_db',aggfunc=_leq).reindex(columns=INDICATOR_ORDER).round(1)

        if table.empty or table.notna().sum().sum() == 0: continue

        general = table.apply(_leq).round(1).to_frame().T
        week_dir = output_dir / f"week_{week_label}"
        week_dir.mkdir(parents=True, exist_ok=True)
        stem = f"{safe_name}_indicadores_week_{week_label}"
        png_path = week_dir / f"{stem}.png"
        csv_path = week_dir / f"{stem}.csv"
        general_csv_path = week_dir / f"{stem}_generales.csv"

        fig,ax = plt.subplots(figsize=(15,8))

        try:
            sns.heatmap(table,annot=True,fmt=".1f",linewidth=0.5,cmap=LEGACY_CMAP,vmin=30,vmax=85,annot_kws={"size":12},ax=ax)
            ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
            ax.set_ylabel("Día", fontsize=22)
            ax.set_xlabel("Indicador", fontsize=22)
            ax.set_title(f"{plot_name} Indicadores - Semana {week_label}", fontsize=22)
            ax.tick_params(axis="both", labelsize=22)
            ax.collections[0].colorbar.ax.tick_params(labelsize=22)
            fig.tight_layout()
            fig.savefig(png_path)
        finally: 
            plt.close(fig)

        table.to_csv(csv_path, index=True, index_label="date_weekday")
        general.to_csv(general_csv_path, index=False)
        outputs[week_label] = (png_path, csv_path, general_csv_path)

    return outputs or None






