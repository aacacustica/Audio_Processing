from pathlib import Path
import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .configs import *
from .time_plot import _leq

def heatmap(matrix,suffix,labels,title,annotate,output_dir,safe_name): 

    png_path = output_dir / f"{safe_name}_{suffix}.png"
    csv_path = output_dir / f"{safe_name}_{suffix}.csv"

    values = matrix.to_numpy(dtype=float)

    fig,ax = plt.subplots(figsize=(max(14,len(labels) * 0.25),max(4,len(matrix) * 0.45)))

    try:

        image = ax.imshow(np.ma.masked_invalid(values),aspect='auto',interpolation='nearest', cmap="RdYlBu_r",vmin=30,vmax=85)

        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=90)
        ax.set_yticks(range(len(matrix.index)))
        ax.set_yticklabels(matrix.index)
        ax.set_xlabel("Hora")
        ax.set_ylabel("Día")
        ax.set_title(title)
        fig.colorbar(image, ax=ax, label="dB(A)")

        if annotate:
            for row,column in zip(*np.where(np.isfinite(values))):
                ax.text(column,row,f"{values[row,column]:.1f}",ha='center',va='center',fontsize=8)

        fig.tight_layout()
        fig.savefig(png_path,dpi=150)
        matrix.to_csv(csv_path,index_label='fecha_día')

    finally:
        plt.close(fig)

    return png_path,csv_path

def render_acoustic_heatmaps(measurements,output_dir: Path, plot_name: str, timezone_name: str = "Europe/Madrid") -> dict[str, tuple[Path,Path]]:

    records = [{"datetime": row.datetime,"la_db": row.la_db} for row in measurements if row.la_db is not None]

    if not records: return {}

    df = pd.DataFrame(records)

    df['datetime']  = (pd.to_datetime(df['datetime'],utc=True).dt.tz_convert(timezone_name))
    df['la_db']     = pd.to_numeric(df['la_db'],errors='coerce')

    df = df.dropna(subset=['datetime','la_db'])

    if df.empty: return {}

    dt = df['datetime']

    df['Día'] = dt.dt.dayofweek.map(lambda day: WEEKDAYS_ES[day])
    df['date_day'] = dt.dt.strftime("%Y-%m-%d") + " " + df["Día"]
    
    df['hour_label'] = dt.dt.strftime("%H:00")
    df['quarter_label'] = (dt.dt.strftime("%H:") + (dt.dt.minute // 16 * 15).map(lambda minute: f"{minute:02d}"))

    hourly = (pd.pivot_table(df,values='la_db',index='date_day',columns='hour_label',aggfunc=_leq).round(1))
    quarter_hourly = (pd.pivot_table(df,values='la_db',index='date_day',columns='quarter_label',aggfunc=_leq).round(1))
    

    

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True,exist_ok=True)

    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", plot_name).strip("_")

    return {
        "hourly": heatmap(
            matrix      = hourly,
            suffix      = "heatmap_evolución",
            labels      = [f"{hour:02d}:00" for hour in range(24)],
            title       = f"{plot_name} - Nivel equivalente por hora",
            annotate    = True,
            output_dir  = output_dir,
            safe_name   = safe_name
        ),
        "15_min": heatmap(
            matrix      = quarter_hourly,
            suffix      = "heatmap_evolución_15min",
            labels      = [f"{slot // 4:02d}:{(slot % 4) * 15:02d}" for slot in range(96)],
            title       = f"{plot_name} - Nivel equivalente cada 15 minutos",
            annotate    = False,
            output_dir  = output_dir,
            safe_name   = safe_name
        )
    }



    