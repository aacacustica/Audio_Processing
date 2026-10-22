from datetime import timedelta
from pathlib import Path
from collections import defaultdict
import re

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

def configure_axis(ax,df,timezone_name):

        ax.plot(df["datetime"], df["LAeq"], marker="o", color="red")
        ax.set_xlabel("Tiempo")
        ax.set_ylabel("LAeq (dB)")
        ax.set_xlim(df["datetime"].min(), df["datetime"].max())

        ax.xaxis.set_major_locator(mdates.HourLocator(interval=4, tz=timezone_name))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M", tz=timezone_name))
        ax.tick_params(axis="x", labelrotation=90)
        ax.grid(True)

        return ax

def render_peak_distribution(peaks, output_dir:Path, plot_name:str, correction_db:float=0.0, timezone_name:str="Europe/Madrid")-> tuple[Path,Path,Path] | None:

    records = [
        {
            "datetime"          : peak.datetime_pico,
            "LAeq"              : peak.leq_db + correction_db,
            "Lpeak"             : peak.peak_la_db + correction_db,
            "duration_seconds"  : peak.duration_seconds,
            "prominence_db"     : peak.prominence_db
        }
        for peak in peaks 
        if peak.datetime_pico is not None and peak.leq_db is not None
    ]

    if not records: return None

    df = pd.DataFrame(records)

    df['datetime'] = (pd.to_datetime(df['datetime'],utc=True).dt.tz_convert(timezone_name))

    df = df.sort_values("datetime")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True,exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", plot_name).strip("_")

    csv_path = output_dir / f"{safe_name}_peak_distribution.csv"
    standard_png = output_dir / f"{safe_name}_peak_distribution.png"
    night_png = output_dir / f"{safe_name}_peak_distribution_night.png"
    df.to_csv(csv_path, index=False)

    fig,ax = plt.subplots(figsize=(25,9))

    try:
        ax = configure_axis(ax,df,timezone_name)
        ax.set_title(f"{plot_name} Valores LAeq a lo largo del tiempo")
        fig.tight_layout()
        fig.savefig(standard_png,dpi=150)
    finally:
         plt.close(fig)

    fig,ax = plt.subplots(figsize=(25,9))

    try:

        ax = configure_axis(ax,df,timezone_name)
        ax.set_title(f"{plot_name} Valores LAeq a lo alrgo del tiempo con periodo nocturno")
        
        current_day = df['datetime'].min().date()
        last_day    = df['datetime'].max().date()

        while current_day <= last_day:

            next_day    = current_day + timedelta(days=1)
            night_start = pd.Timestamp(f"{current_day} 20:00",tz=timezone_name)
            night_end   = pd.Timestamp(f"{next_day} 07:00",tz = timezone_name)

            ax.axvspan(night_start,night_end,color='grey',alpha=0.3)
            current_day = next_day

        fig.tight_layout()
        fig.savefig(night_png,dpi=150)

    finally:
         plt.close(fig)

    return standard_png,night_png,csv_path

def render_peak_distribution_week(peaks,output_dir:Path, plot_name: str, correction_db: float = 0.0, timezone_name: str = "Europe/Madrid") -> dict[str,tuple[Path,Path,Path]] | None:

    valid_peaks = [ peak for peak in peaks if peak.datetime_pico is not None and peak.leq_db is not None]

    if not valid_peaks: return None

    peaks_by_week = defaultdict(list)

    for peak in valid_peaks:

        local_datetime  = pd.to_datetime(peak.datetime_pico,utc=True).tz_convert(timezone_name)
        week_start      = (local_datetime.normalize() - pd.Timedelta(days=local_datetime.dayofweek)).date()
        
        peaks_by_week[week_start].append(peak)

    output_dir = Path(output_dir)
    weekly_outputs = {}

    for week_start,week_peaks in sorted(peaks_by_week.items()):
        
        week_folder = output_dir / f"week_{week_start:%Y-%m-%d}"
        week_folder.mkdir(parents= True,exist_ok=True)

        weekly_outputs[week_start.isoformat()] = render_peak_distribution(
            peaks           = week_peaks,
            output_dir      = week_folder,
            plot_name       = f"{plot_name}_{week_start:%Y-%m-%d}",
            correction_db   = correction_db,
            timezone_name   = timezone_name
        )

    return weekly_outputs



    