from pathlib import Path
import re

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from .configs import LEGACY_CMAP, WEEKDAYS_ES,LE_SECONDS,INDICATOR_ORDER
from .time_plot import _leq

def render_indicator_heatmap(measurements,output_dir: Path, plot_name: str, timezone_name: str = "Europe/Madrid", correction_db: float = 0.0) -> tuple[Path,Path,Path] | None:

    records = [{'datetime':row.datetime, 'la_db':row.la_db + correction_db} for row in measurements if row.datetime is not None and row.la_db is not None]

    if not records: return None

    df = pd.DataFrame(records)

    df['datetime'] = (pd.to_datetime(df['datetime'],utc=True).dt.tz_convert(timezone_name))
    df['la_db'] = pd.to_numeric(df['la_db'],errors='coerce')

    df = df.dropna(subset=['datetime','la_db'])

    if df.empty: return None

    dt = df['datetime']

    df['date'] = dt.dt.date
    df['weekday'] = dt.dt.dayofweek.map(lambda day: WEEKDAYS_ES[day])
    df['date_weekday'] = dt.dt.strftime("%Y-%m-%d") + " " + df["weekday"]
    df['hour'] = dt.dt.hour
    df['period'] = 'Ln'
    df.loc[df['hour'].between(7,18), 'period'] = 'Ld'
    df.loc[df['hour'].between(19,22),'period'] = 'Le'

    durations = (df.groupby(['date','period'])['datetime'].agg(first='min',last='max'))

    durations['seconds'] = (durations['last'] - durations['first']).dt.total_seconds()

    boundary_dates = {df['date'].min(), df['date'].max()}
    excluded = [ (date,period) for (date,period), row in durations.iterrows() if date in boundary_dates and row['seconds'] <= LE_SECONDS]

    for date,period in excluded:
        df = df[~((df["date"] == date) & (df["period"] == period))]

    table = pd.pivot_table(df,values='la_db',index='date_weekday',columns='period',aggfunc=_leq).reindex(columns=INDICATOR_ORDER).round(1)

    if table.empty or table.notna().sum().sum() == 0: return None

    general = table.apply(_leq).round(1).to_frame().T

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True,exist_ok=True)
    safe_name = re.sub( r"[^A-Za-z0-9._-]+", "_", plot_name).strip("_")

    png_path = output_dir / f"{safe_name}_indicadores.png"
    csv_path = output_dir / f"{safe_name}_indicadores.csv"
    general_csv_path = output_dir / f"{safe_name}_indicadores_generales.csv"

    fig,ax = plt.subplots(figsize=(15,8))

    try:
        sns.heatmap(table,annot=True,fmt=".1f",linewidth=0.5,cmap=LEGACY_CMAP,vmin=30,vmax=85,annot_kws={"size":12},ax=ax)

        ax.set_ylabel("Día", fontsize=22)
        ax.set_xlabel("Indicador", fontsize=22)
        ax.set_title(f"{plot_name} Indicadores", fontsize=22)
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=22)
        ax.set_xticklabels(ax.get_xticklabels(), rotation=0, fontsize=22)
        ax.collections[0].colorbar.ax.tick_params(labelsize=22)

        fig.tight_layout()
        fig.savefig(png_path)
        table.to_csv(csv_path, index=True, index_label="date_weekday")
        general.to_csv(general_csv_path, index=False)

    finally:
        plt.close(fig=fig)

    return png_path,csv_path,general_csv_path