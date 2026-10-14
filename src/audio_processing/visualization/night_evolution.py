from pathlib import Path
import re

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from .day_evolution import _leq
from .configs import * 

def _prepare_complete_nights(measurements,timezone_name):

    records = [{"datetime": row.datetime, "la_db": row.la_db} for row in measurements if row.datetime is not None and row.la_db is not None]

    if not records: return pd.DataFrame()

    df = pd.DataFrame(records)
    
    df['datetime'] = pd.to_datetime(df['datetime'],utc=True).dt.tz_convert(timezone_name)
    df['la_db'] = pd.to_numeric(df['la_db'],errors='coerce')

    df = df.dropna(subset=['datetime','la_db']).set_index('datetime').sort_index()

    df = df.loc[(df.index.hour  >= 23) | (df.index.hour < 7)].copy()

    if df.empty: return df

    df['night_date'] = df.index.normalize()

    after_midnight = df.index.hour < 7

    df.loc[after_midnight, 'night_date'] -= pd.Timedelta(days=1)

    weekday = df['night_date'].dt.dayofweek

    df['Día'] = weekday.map(lambda day: NIGHT_LABELS[day])

    complete_dates = []

    for night_date,night in df.groupby("night_date"):

        has_before_midnight = (night.index.hour >= 23).any()
        has_after_midnight = (night.index.hour < 7).any()

        if has_before_midnight and has_after_midnight: complete_dates.append(night_date)

    df = df[df['night_date'].isin(complete_dates)].copy()

    if df.empty: return df

    df['datetime'] = df.index
    
    return df


def _save_plot(data,grid,output_dir,plot_name,suffix):

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True,exist_ok=True)

    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", plot_name).strip("_")

    png_path = output_dir / f"{safe_name}_{suffix}.png"
    csv_path = output_dir / f"{safe_name}_{suffix}.csv"

    data.to_csv(csv_path,index=False)
    grid.figure.savefig(png_path,dpi=150,bbox_inches='tight')
    
    plt.close(grid.figure)
    return png_path,csv_path


def render_night_evolution(measurements,output_dir: Path, plot_name: str, timezone_name: str = "Europe/Madrid"):

    data = _prepare_complete_nights(measurements,timezone_name)

    if data.empty: return

    data['plot_hour'] = data.index.hour.astype(int)
    data.loc[data['plot_hour'] == 23, 'plot_hour'] = -1
    data = data.sort_values(['night_date','plot_hour'])

    grid = sns.relplot(
        data        = data,
        x           = 'plot_hour',
        y           = 'la_db',
        kind        = 'line',
        hue         = 'Día',
        estimator   =_leq,
        aspect      = 1.3,
        palette     = NIGHT_PALETTE
    )

    axis = grid.axes.flat[0]
    axis.set_xticks(range(-1, 7))

    axis.set_xticklabels(["23:00", "00:00", "01:00", "02:00","03:00", "04:00", "05:00", "06:00"])

    axis.set_yticks(range(30, 105, 5))
    axis.set_xlim(-1.5, 6.5)
    axis.set_title("Evolución Ln")
    axis.set_ylabel("dB(A)")
    axis.set_xlabel("Hora")
    axis.spines["top"].set_visible(True)
    axis.spines["right"].set_visible(True)

    return _save_plot(data,grid,output_dir,plot_name,"Ln_evolution")

def _mode_or_na(series): 
    values = series.dropna()

    if values.empty: return None

    modes = values.mode()
    return modes.iloc[0] if not modes.empty else values.iloc[0]


def render_night_evolution_15min(measurements, output_dir: Path, plot_name: str, timezone_name: str = "Europe/Madrid"):

    data = _prepare_complete_nights(measurements,timezone_name)

    if data.empty: return None

    levels = data['la_db'].resample("15min").apply(_leq)
    labels = data['Día'].resample("15min").agg(_mode_or_na)

    night_data = pd.DataFrame({
        "la_db" : levels,
        "Día"   : labels
    }).dropna(subset=['la_db','Día'])

    if night_data.empty: return None

    night_data['datetime']  = night_data.index   
    night_data['date']      = night_data.index.date
    night_data['time']      = night_data.index.time
    night_data['plot_time'] = [((time.hour * 60 + time.minute - 15) - (23 * 60)) if time.hour >= 23 else (time.hour * 60 + time.minute - 15 + 60) for time in night_data['time']]

    grid = sns.relplot(
        data        = night_data,
        x           = "plot_time",
        y           = "la_db",
        kind        = "line",
        errorbar    = None,
        hue         = "Día",
        estimator   = _leq,
        aspect      = 1.3,
        palette     = NIGHT_PALETTE
    )

    axis = grid.axes.flat[0]

    x_labels = ([f"20:{minute:02d}" for minute in range(0,60,15)] + [f"{hour:02d}:{minute:02d}" for hour in range(7) for minute in range(0,60,15)])

    axis.set_xticks(list(range(-15, 465, 15)))
    axis.set_xticklabels(x_labels, rotation=90)
    axis.set_yticks(range(30, 105, 5))
    axis.set_xlim(-30, 465)
    axis.set_title("Evolución Ln cada 15 minutos")
    axis.set_ylabel("dB(A)")
    axis.set_xlabel("Hora")
    axis.spines["top"].set_visible(True)
    axis.spines["right"].set_visible(True)

    return _save_plot(night_data.reset_index(drop=True),grid,output_dir,plot_name,"Ln_evolution_15_min")



