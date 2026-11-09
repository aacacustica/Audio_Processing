from pathlib import Path
import re

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


from .configs import *



def _leq(levels: pd.Series) -> float:

    values = pd.to_numeric(levels,errors='coerce').dropna().to_numpy(dtype=float)

    if values.size == 0: return float("nan")

    return float(10.0 * np.log10(np.mean(np.power(10.0,values / 10.0))))


def render_day_evolution(measurements,output_dir: Path,plot_name: str, timezone_name: str = "Europe/Madrid") -> tuple[Path,Path] | None:

    records = [{"datetime": row.datetime,"la_db":row.la_db} for row in measurements if row.la_db is not None]

    if not records: return None

    df = pd.DataFrame(records)
    
    df['datetime'] = (pd.to_datetime(df['datetime'],utc=True).dt.tz_convert(timezone_name))
    df['la_db'] = pd.to_numeric(df['la_db'],errors='coerce')
    
    df = df.dropna(subset=['datetime','la_db'])

    if df.empty: return None

    df['weekday'] = df['datetime'].dt.dayofweek
    df['hour'] = df['datetime'].dt.hour

    profile = (df.groupby(['weekday','hour'],as_index=False).agg(LAeq=("la_db",_leq),mediciones=('la_db','count')))

    profile['día'] = profile['weekday'].map(lambda weekday: WEEKDAYS_ES[weekday])

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True,exist_ok=True)

    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", plot_name).strip("_")
    
    png_path = output_dir / f"{safe_name}_day_evolution.png"
    csv_path = output_dir / f"{safe_name}_day_evolution.csv"

    fig,ax = plt.subplots(figsize=(14,7))

    try:

        for weekday,day_name in enumerate(WEEKDAYS_ES):
            day_data = profile[profile['weekday'] == weekday]

            if day_data.empty: continue

            ax.plot(day_data['hour'],day_data['LAeq'],marker='o',markersize=5,label=day_name)

        for hour in (7,19,23):
            ax.axvline(hour,color='gray',linestyle='--',linewidth=0.8)

        ax.set(xlim=(-0.5,23.5),ylim=(30,105),xlabel='Hora',ylabel='dB(A)',title=f"Evolución diaria - {plot_name}")
        ax.set_xticks(range(24))
        ax.set_xticklabels([f"{hour:02d}:00" for hour in range(24)],rotation=90)
        ax.grid(True,axis="y",alpha=0.3)
        ax.legend(title='Día')
        
        fig.tight_layout()
        fig.savefig(png_path,dpi=150)

        profile.to_csv(csv_path,index=False)

    finally:
        plt.close(fig)

    return png_path,csv_path


def render_period_evolution(measurements,output_dir: Path, plot_name: str, timezone_name: str = "Europe/Madrid") -> dict[str,tuple[Path,Path]]:

    records = [{"datetime":row.datetime,"la_db":row.la_db} for row in measurements if row.la_db is not None]

    if not records: return {}

    df = pd.DataFrame(records)

    df['datetime'] = (pd.to_datetime(df['datetime'],utc=True).dt.tz_convert(timezone_name))

    df['la_db'] = pd.to_numeric(df['la_db'],errors='coerce')

    df = df.dropna(subset=['datetime','la_db'])

    if df.empty: return {}

    df["weekday"]   = df["datetime"].dt.dayofweek
    df["hour"]      = df["datetime"].dt.hour
    df["period"]    = "Ln"
    
    df.loc[df["hour"].between(7, 18), "period"] = "Ld"
    df.loc[df["hour"].between(19, 22), "period"] = "Le"
    
    df              = df[df["period"].isin(["Ld", "Le"])]

    profile = (df.groupby(['period','weekday','hour'],as_index=False).agg(LAeq=("la_db",_leq),mediciones=("la_db",'count')))

    if profile.empty: return {}

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True,exist_ok=True)

    safe_name = re.sub( r"[^A-Za-z0-9._-]+", "_", plot_name).strip("_")

    period_settings = {
        "Ld": (range(7,19),6.5,18.5),
        "Le": (range(19,23),18.5,22.5)}

    outputs = {}

    for period, (hours,x_min,x_max) in period_settings.items():

        period_data = profile[profile['period'] == period].copy()

        if period_data.empty: continue

        png_path = output_dir / f"{safe_name}_{period}_evolution.png"
        csv_path = output_dir / f"{safe_name}_{period}_evolution.csv"

        fig,ax = plt.subplots(figsize=(12,7))

        try:
            for weekday,day_name in enumerate(WEEKDAYS_ES):

                day_data = period_data[period_data['weekday'] == weekday]

                if day_data.empty: continue

                ax.plot(day_data['hour'],day_data['LAeq'],marker='o',markersize=5,label=day_name)

            ax.set_xlim(x_min,x_max)
            ax.set_xticks(list(hours))
            ax.set_xticklabels([f"{hour:02d}:00" for hour in hours])
            ax.set_ylim(30, 105)
            ax.set_xlabel("Hora")
            ax.set_ylabel("dB(A)")
            ax.set_title(f"Evolución {period} - {plot_name}")
            ax.grid(True, axis="y", alpha=0.3)
            ax.legend(title="Día")

            fig.tight_layout()
            fig.savefig(png_path,dpi=150)
            period_data.to_csv(csv_path,index=False)

        finally:
            plt.close(fig)

        outputs[period] = (png_path,csv_path)

    return outputs

