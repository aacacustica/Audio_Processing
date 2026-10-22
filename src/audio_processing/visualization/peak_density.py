from pathlib import Path
import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from scipy.stats import gaussian_kde
from collections import defaultdict

def render_peak_density(peaks,output_dir:Path,plot_name:str,timezone_name: str = "Europe/Madrid") -> dict[str,tuple[Path,Path]] | None:

    timestamps = [peak.datetime_pico for peak in peaks if peak.datetime_pico is not None]

    if not timestamps: return None

    local_times = (pd.to_datetime(pd.Series(timestamps),utc=True).dt.tz_convert(timezone_name))

    hours = (local_times.dt.hour + local_times.dt.minute / 60 + local_times.dt.second / 3600)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True,exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", plot_name).strip("_")

    outputs = {}

    counts = (np.floor(hours).astype(int).value_counts().reindex(range(24),fill_value=0).sort_index())

    counts_df = pd.DataFrame({
        "hora_local":range(24),
        "numero_picos":counts.to_numpy()
    })

    counts_png = output_dir / f"{safe_name}_peak_frequency_by_hour.png"
    counts_csv = output_dir / f"{safe_name}_peak_frequency_by_hour.csv"
    counts_df.to_csv(counts_csv, index=False)

    fig, ax = plt.subplots(figsize=(12, 6))

    try:
        ax.bar(counts_df['hora_local'],counts_df['numero_picos'])
        ax.set(title=f"{plot_name} | Número de picos por hora",
               xlabel = "Hora local",
               ylabel = "Número de picos",
               xticks = range(24),
               xlim = (-0.5,23.5))
        ax.grid(axis='y',alpha=0.3)
        fig.tight_layout()
        fig.savefig(counts_png,dpi=150)

    finally:
        plt.close(fig)

    outputs["frecuencia"] = (counts_png, counts_csv)

    if hours.nunique() >= 2:
        hours_array = hours.to_numpy(dtype=float)
        wrapped_hours = np.concatenate([hours_array - 24, hours_array, hours_array + 24])
        grid = np.linspace(0,24,481)
        density_png = output_dir / f"{safe_name}_peak_density_by_hour.png"
        density_csv = output_dir / f"{safe_name}_peak_density_by_hour.csv"

        try:
            density = gaussian_kde(wrapped_hours)(grid) * 3
            density_df = pd.DataFrame(
                {
                    "hora_local":grid,
                    "densidad":density
                }
            )

            density_df.to_csv(density_csv,index=False)
            fig,ax = plt.subplots(figsize=(12,6))

            try:
                ax.plot(grid,density)
                ax.set(title    = f"{plot_name} | Densidad horaria de picos",
                    xlabel   = "Hora local",
                    ylabel   = "Densidad",
                    xlim     = (0,24),
                    xticks   = range(0,25,2))
                ax.grid(alpha=0.3)
                fig.tight_layout()
                fig.savefig(density_png,dpi=150)
            finally:
                plt.close(fig)

            outputs['densidad'] = (density_png,density_csv)
        except (ValueError,np.linalg.LinAlgError):
            pass

    return outputs

def render_peak_density_week(peaks,output_dir: Path, plot_name: str, timezone_name: str = "Europe/Madrid") ->dict[str, dict[str,tuple[Path,Path]]] | None:

    peaks_by_week = defaultdict(list)
    
    for peak in peaks:
        if peak.datetime_pico is None: continue

        local_datetime = pd.to_datetime(peak.datetime_pico,utc=True).tz_convert(timezone_name)

        week_start = (local_datetime.normalize() - pd.Timedelta(days = local_datetime.dayofweek)).date()
        peaks_by_week[week_start].append(peak)

    if not peaks_by_week: return None

    output_dir = Path(output_dir)
    weekly_outputs = {}

    for week_start, week_peaks in sorted(peaks_by_week.items()):
        week_folder = output_dir / f"week_{week_start:%Y-%m-%d}"
        week_folder.mkdir(parents=True,exist_ok=True)

        outputs = render_peak_density(peaks = week_peaks,output_dir=week_folder,plot_name = f"{plot_name}_{week_start:%Y-%m-%d}",timezone_name=timezone_name)

        if outputs: weekly_outputs[week_start.isoformat()] = outputs

    return weekly_outputs or None