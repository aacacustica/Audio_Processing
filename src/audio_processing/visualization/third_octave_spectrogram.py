from __future__ import annotations

from pathlib import Path
import re

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from configs import THIRD_OCTAVE_BANDS

def energy_mean(values: pd.Series) -> float:

    valid = values.dropna().to_numpy(dtype=float)

    if valid.size == 0: return np.nan

    return float(10.0 * np.log10(np.mean(np.power(10.0,valid/10.0))))

def render_third_octave_spectrogram(third_octave_measurements,output_dir: Path, plot_name: str, timezone_name: str = "Europe/Madrid") -> tuple[Path,Path] | None:

    rows: list[dict[str,object]] = []

    for measurement,bands in third_octave_measurements:
        timestamp = pd.Timestamp(measurement.datetime)

        if pd.isna(timestamp): continue
        
        if timestamp.tzinfo is None: timestamp = timestamp.tz_localize(timezone_name)
        else: timestamp = timestamp.tz_convert(timezone_name)

        row:  dict[str,object] = {'datetime':timestamp}
        has_level = False

        for frequency,attribute in THIRD_OCTAVE_BANDS:

            value = getattr(bands,attribute,None)

            if value is None or not np.isfinite(value): row[str(frequency)] = np.nan
            else:
                row[str(frequency)] = float(value)
                has_level = True

        if has_level: rows.append(row)

    if not rows: return None

    frame = pd.DataFrame(rows).sort_value('datetime')

    level_columns = [str(frequency) for frequency,_ in THIRD_OCTAVE_BANDS]

    frame = frame.groupby('datetime',as_index=False)[level_columns].agg(energy_mean)
    frame = frame.dropna(subset=level_columns,how='all')

    if frame.empty: return None

    frequencies = [float(column) for column in level_columns if frame[column].notna().any()]
    level_columns = [str(frequency) for frequency in frequencies]
    values = frame[level_columns].to_numpy(dtype=float).T
    values = np.clip(values,20.0,110.0)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", plot_name).strip("_") or "source"
    png_path = output_dir / f"{safe_name}_third_octave_spectrogram.png"
    csv_path = output_dir / f"{safe_name}_third_octave_spectrogram.csv"
    frame.to_csv(csv_path, index=False)

    times = pd.DatetimeIndex(frame["datetime"])
    fig, ax = plt.subplots(figsize=(16, 8))
    mesh = ax.pcolormesh(times, frequencies, values, shading="auto", cmap="inferno", vmin=20, vmax=110)
    fig.colorbar(mesh, ax=ax, label="Nivel de presión sonora (dB)")
    ax.set_yscale("log")
    ax.set_yticks(frequencies)
    ax.set_yticklabels([f"{frequency:g}" for frequency in frequencies])
    ax.set_ylabel("Frecuencia central de banda (Hz)")
    ax.set_xlabel(f"Hora ({timezone_name})")
    ax.set_title(f"Espectrograma de tercios de octava: {plot_name}")
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M", tz=times.tz))
    fig.autofmt_xdate(rotation=35, ha="right")
    fig.tight_layout()
    fig.savefig(png_path, dpi=150)
    plt.close(fig)

    return png_path, csv_path

