from pathlib import Path
import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from .configs import *
from .time_plot import _leq
from matplotlib.colors import ListedColormap

def heatmap(matrix,suffix,title,annotate,output_dir,safe_name,axis_fontsize,title_fontsize,dpi,csv_index): 

    png_path = output_dir / f"{safe_name}_{suffix}.png"
    csv_path = output_dir / f"{safe_name}_{suffix}.csv"

    sns.set_style('white')
    fig,ax = plt.subplots(figsize=(20,10))

    try:

        options = {'annot': annotate}

        if annotate:
            options['fmt'] = '.1f'
            options['annot_kws'] = {'size':20}

        plot = sns.heatmap(matrix,vmin=30,vmax=85,cmap=LEGACY_CMAP,ax=ax,**options)

        ax.set_xlabel("Hora",fontsize=axis_fontsize)
        ax.set_ylabel("Día",fontsize=axis_fontsize)
        ax.set_title(title,fontsize=title_fontsize)
        ax.set_yticklabels(ax.get_yticklabels(),rotation=0,fontsize=axis_fontsize)
        ax.set_xticklabels(ax.get_xticklabels(),rotation=90,fontsize=axis_fontsize)

        plot.collections[0].colorbar.ax.tick_params(labelsize=axis_fontsize)

        fig.tight_layout()
        fig.savefig(png_path,dpi=dpi)

        matrix.to_csv(csv_path,index=csv_index,index_label='date_day' if csv_index else None)

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
    df['quarter_label'] = (dt.dt.strftime("%H:") + (dt.dt.minute // 15* 15).map(lambda minute: f"{minute:02d}"))

    hourly = (pd.pivot_table(df,values='la_db',index='date_day',columns='hour_label',aggfunc=_leq).round(1))
    quarter_hourly = (pd.pivot_table(df,values='la_db',index='date_day',columns='quarter_label',aggfunc=_leq).round(1))
    

    

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True,exist_ok=True)

    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", plot_name).strip("_")

    return {
        "hourly": heatmap(
            matrix          = hourly,
            suffix          = "heatmap_evolución",
            title           = f"{plot_name} Nivel equivalente",
            annotate        = True,
            output_dir      =output_dir,
            safe_name       =safe_name,
            axis_fontsize   = 22,
            title_fontsize  = 22,
            dpi             = 350,
            csv_index       = True  
        ),

        "15_min": heatmap(
            matrix          = quarter_hourly,
            suffix          = "heatmap_evolución_15min",
            title           = f"{plot_name} Nivel equivalente 15 minutos",
            annotate        = True
            output_dir      = output_dir,
            safe_name       = safe_name,
            axis_fontsize   = 24,
            title_fontsize  = 30,
            dpi             = 350,
            csv_index       = False 
        )
    }



    