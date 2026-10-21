from pathlib import Path
import re

import matplotlib.pyplot as plt
import pandas as pd

def _save_heatmap(matrix: pd.DataFrame, * , output_dir: Path, filename: str, title: str, x_labels: list[str]) -> tuple[Path,Path]:

    png_path = output_dir / f"{filename}.png"
    csv_path = output_dir / f"{filename}.csv"

    matrix.to_csv(csv_path,index_label="fecha_local")

    height = min(max(5,len(matrix) * 0.35),18)
    fig,ax = plt.subplots(figsize=(14,height))

    try:
        image = ax.imshow(matrix.to_numpy(),aspect="auto",cmap="viridis")
        ax.set_title(title)
        ax.set_xlabel("Hora local")
        ax.set_ylabel("Fecha local")
        ax.set_xticks(range(len(x_labels)))
        ax.set_xticklabels(x_labels)

        step = max(1,len(matrix) // 20)
        y_positions = list(range(0,len(matrix),step))
        ax.set_yticks(y_positions)
        ax.set_yticklabels([str(matrix.index[i]) for i in y_positions])

        fig.colorbar(image,ax=ax,label="Número de picos")
        fig.tight_layout()
        fig.savefig(png_path,dpi=150)

    finally:
        plt.close(fig)

    return png_path,csv_path

def render_peak_frequency_heatmaps(peaks,output_dir: Path, plot_name: str, timezone_name: str = "Europe/Madrid") -> dict[str, tuple[Path,Path]] | None:

    records = [{"datetime": peak.datetime_pico} for peak in peaks if peak.datetime_pico is not None]

    if not records: return None

    data = pd.DataFrame(records)
    data['datetime'] = (pd.to_datetime(data['datetime'],utc=True).dt.tz_convert(timezone_name))
    data['fecha_local'] = data['datetime'].dt.date
    data['hora'] = data['datetime'].dt.hour

    dates               = pd.date_range(start=min(data['fecha_local']),end=max(data['fecha_local']),freq="D").date
    hourly_counts       = data.groupby(['fecha_local','hora']).size()
    hourly              = (hourly_counts.reindex(pd.MultiIndex.from_product([dates,range(24)],names=['fecha_local','hora']),fill_value=0).unstack("hora"))
    four_hour_data      = data.assign(franja_4h=(data['hora'] // 4)*4)
    four_hour_counts    = four_hour_data.groupby(['fecha_local','franja_4h']).size()
    four_hour           = (four_hour_counts.reindex(pd.MultiIndex.from_product([dates,range(0,24,4)],names=['fecha_local','franja_4h']),fill_value=0).unstack("franja_4h"))

    output_dir          = Path(output_dir)
    safe_name           = re.sub(r"[^A-Za-z0-9._-]+", "_", plot_name).strip("_")

    output_dir.mkdir(parents=True,exist_ok=True)

    return {
        "horario" : _save_heatmap(
            matrix          = hourly,
            output_dir      = output_dir,
            filename        = f"{safe_name}_peak_frequency_hourly",
            title           = f"{plot_name} | Picos por día y hora",
            x_labels        = [f"{hour:02d}:00" for hour in range(24)]),
        "cada_4_h": _save_heatmap(
            matrix          = four_hour,
            output_dir      = output_dir,
            filename        = f"{safe_name}_peak_frequency_4h",
            title           = f"{plot_name} | Picos por día y franjas de 4h",
            x_labels        = [f"{hour:02d}:00–{hour + 4:02d}:00" for hour in range(0, 24, 4)],
        )
        
    }

def render_peak_frequency_heatmaps_week(peaks,output_dir: Path, plot_name: str, timezone_name: str = "Europe/Madrid") -> dict[str,tuple[Path,Path]] | None :

    records = [
        {'datetime' : peak.datetime_pico}
        for peak in peaks if peak.datetime_pico is not None
    ]

    if not records: return None

    data = pd.DataFrame(records)

    data['datetime'] = (pd.to_datetime(data['datetime'],utc=True).dt.tz_convert(timezone_name))

    data['fecha_local'] = data['datetime'].dt.date
    data['hora'] = data['datetime'].dt.hour
    data['franja_4h'] = (data['hora'] // 4 ) * 4

    data['semana_inicio'] = (data['datetime'].dt.normalize() - pd.to_timedelta(data['datetime'].dt.dayofweek,unit="D")).dt.date

    output_dir = Path(output_dir)
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", plot_name).strip("_")
    weekly_outputs = {}

    for week_start,week_data in data.groupby('semana_inicio',sort=True):
        
        week_start = pd.Timestamp(week_start)
        week_dates = pd.date_range(week_start,periods=7,freq='D').date
        week_folder = output_dir / f"week_{week_start:%Y-%m-%d}"
        week_folder.mkdir(parents=True,exist_ok=True)

        hourly = (week_data.groupby(['fecha_local','hora']).size().reindex(pd.MultiIndex.from_product([week_dates,range(24)],names=['fecha_local','hora']),fill_value=0).unstack('hora'))

        four_hour = (week_data.groupby(['fecha_local','hora']).size().reindex(pd.MultiIndex.from_product([week_dates,range(0,24,4)],names=['fecha_local','franja_4h']),fill_value=0).unstack('franja_4h'))

        weekly_outputs[week_start.date().isoformat()] = {
            'horario': _save_heatmap(
                matrix      = hourly,
                output_dir  = week_folder,
                filename    = f"{safe_name}_peak_frequency_hourly",
                title       = f"{plot_name} | Picos por día y hora | Semana {week_start:%Y-%m-%d}",
                x_labels    = [f"{hour:02d}:00" for hour in range(24)]
            ),
            'cada_4h':_save_heatmap(
                matrix      = four_hour,
                output_dir  = week_folder,
                filename    = f"{safe_name}_peak_frequency_4h",
                title       = f"{plot_name} | Picos por día y franjas de 4 h | Semana {week_start:%Y-%m-%d}",
                x_labels    = [f"{hour:02d}:00–{hour + 4:02d}:00" for hour in range(0,24,4)]
            )
        }

    return weekly_outputs