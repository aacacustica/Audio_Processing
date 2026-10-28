from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from audio_processing.visualization.day_evolution import _leq
from audio_processing.visualization.night_evolution import _mode_or_na,_prepare_complete_nights
from audio_processing.visualization.configs import NIGHT_LABELS,NIGHT_PALETTE

def _safe_name(plot_name: str) -> str:

    return re.sub(r"[^A-Za-z0-9._-]+", "_", plot_name).strip("_") or "source"


def render_night_evolution_week(measurements,output_dir: Path,plot_name: str, timezone_name: str = "Europe/Madrid") -> dict[str,Path] | None:

    data = _prepare_complete_nights(measurements,timezone_name)

    if data.empty: return None

    data = data.copy()
    data['plot_hour'] = data.index.hour.astype(int)
    data.loc[data['plot_hour'] == 23,'plot_hour'] = -1

    local_dates = data.index.normalize()

    data['week_start'] = local_dates - pd.to_timedelta(local_dates.dayofweek, unit='D')

    output_dir = Path(output_dir)
    safe_name = _safe_name(plot_name)   
    outputs: dict[str,Path] = {}

    for week_start,week_data in data.groupby("week_start",sort=True):
        
        week_label = week_start.date().isoformat()
        
        grid = sns.relplot(data=week_data,x='plot_hour',y='la_db',kind='line',hue='Día',estimator=_leq,aspect=1.3,palette=NIGHT_PALETTE)

        try:
            axis = grid.axes.flat[0]
            axis.set_xticks(range(-1,7))
            axis.set_xticklabels(["23:00", "00:00", "01:00", "02:00", "03:00", "04:00", "05:00", "06:00"])
            axis.set_yticks(range(30,105,5))
            axis.set_xlim(-1.5,6.5)
            axis.set_title(f"Evolución Ln - Semana {week_label}")
            axis.set_ylabel("dB(A)")
            axis.set_xlabel("Hora")
            axis.spines["top"].set_visible(True)
            axis.spines['right'].set_visible(True)

            week_dir = output_dir / f"week_{week_label}"
            week_dir.mkdir(parents=True, exist_ok=True)
            output_path = week_dir / f"{safe_name}_Ln_evolution_week_{week_label}.png"
            grid.figure.savefig(output_path, dpi=150, bbox_inches="tight")
            outputs[week_label] = output_path

        finally:
            plt.close(grid.figure)

    return outputs or None

def render_night_evolution_15min_week(measurements,output_dir:Path,plot_name:str,timezone_name:str = "Europe/Madrid") -> dict[str,Path] | None:

    data = _prepare_complete_nights(measurements,timezone_name)

    if data.empty: return None

    levels = data['la_db'].resample("15min").apply(_leq)
    weekdays = data['Día'].resample("15min").agg(_mode_or_na)
    night_dates = data['night_date'].resample("15min").first()
    night_data = pd.DataFrame({"la_db":levels,"Día":weekdays,"night_date":night_dates}).dropna(subset=['la_db',"Día","night_date"])

    if night_data.empty: return None

    night_data['plot_time'] = [((timestamp.hour * 60 + timestamp.minute - 15) - (23*60)) if timestamp.hour >= 23 else (timestamp.hour * 60 + timestamp.minute - 15 + 60) for timestamp in night_data.index]
    
    local_dates = night_data.index.normalize()

    night_data['week_start'] = local_dates - pd.to_timedelta(local_dates.dayofweek, unit = "D")

    output_dir = Path(output_dir)
    safe_name = _safe_name(plot_name)
    outputs: dict[str,Path] = {}
    x_labels = [f"23:{minute:02d}" for minute in range(0,60,15)] + [f"{hour:02d}:{minute:02d}" for hour in range(7) for minute in range(0,60,15)]

    for week_start, week_data in night_data.groupby("week_start",sort=True):

        week_label = week_start.date().isoformat()

        grid = sns.relplot(data=week_data,x='plot_time',y='la_db',kind='line',errorbar=None,hue='Día',estimator=_leq,aspect=1.3,palette=NIGHT_PALETTE)

        try:

            axis = grid.axes.flat[0]
            axis.set_xticks(range(-15, 465, 15))
            axis.set_xticklabels(x_labels, rotation=90)
            axis.set_yticks(range(30, 105, 5))
            axis.set_xlim(-30, 465)
            axis.set_title(f"Evolución Ln cada 15 minutos - Semana {week_label}")
            axis.set_ylabel("dB(A)")
            axis.set_xlabel("Hora")
            axis.spines["top"].set_visible(True)
            axis.spines["right"].set_visible(True)

            week_dir = output_dir / f"week_{week_label}"
            week_dir.mkdir(parents=True, exist_ok=True)
            output_path = (
                week_dir
                / f"{safe_name}_Ln_evolution_15_min_week_{week_label}.png"
            )
            grid.figure.savefig(output_path, dpi=150, bbox_inches="tight")
            outputs[week_label] = output_path

        finally:
            plt.close(grid.figure)

    return outputs or None
