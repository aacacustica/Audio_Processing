from pathlib import Path
import re

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OCA_LIMITS = {
    "OCA_RESIDENTIAL": {"ld": 65.0, "le": 65.0, "ln": 55.0},
    "OCA_LEISURE":     {"ld": 73.0, "le": 73.0, "ln": 63.0},
    "OCA_OFFICE":      {"ld": 70.0, "le": 70.0, "ln": 65.0},
    "OCA_INDUSTRIAL":  {"ld": 75.0, "le": 75.0, "ln": 65.0},
    "OCA_CULTURE":     {"ld": 60.0, "le": 60.0, "ln": 50.0},
}

def _leq(levels: pd.Series) -> float:

    values = pd.to_numeric(levels,errors='coerce').dropna().to_numpy(dtype=float)

    if values.size == 0: return float("nan")

    return float(10.0 * np.log10(np.mean(np.power(10.0,values / 10.0))))


def _oca_limit(timestamp: pd.Timestamp, limits: dict[str,float]) -> float:

    hour = timestamp.hour
    
    if 7<=hour<19: return limits["ld"]
    if 19<=hour<23: return limits['le']

    return limits['ln']

def _safe_filename(name: str) -> str:

    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_")

    return cleaned or "visualization"

def render_time_plot(measurements,output_dir: Path,plot_name: str, aggregation_seconds: int, percentiles: list[int],oca_type: str, correction_db: float = 0.0, timezone_name: str = "Europe/Madrid") -> tuple[Path,Path] | None:

    if aggregation_seconds <= 0: raise ValueError("aggregation_seconds debe de ser mayor que cero")

    if oca_type not in OCA_LIMITS: raise ValueError(f"Tipo OCA desconocido: {oca_type}")

    for percentile in percentiles: 
        if not 0 <= percentile <= 100: raise ValueError(f"Percentil fuera de rango: {percentile}")

    records = [ {
        "datetime" : row.datetime,
        "la_db"    : row.la_db,
        "la_max_db": row.la_max_db,
        "la_min_db": row.la_min_db
    } for row in measurements]

    if not records: return None

    df = pd.DataFrame(records)
    df['datetime'] = pd.to_datetime(df["datetime"],utc=True).dt.tz_convert(timezone_name)
    df = df.dropna(subset=['la_db']).sort_values("datetime")

    if df.empty: return None

    for column in ("la_db","la_max_db","la_min_db"):
        df[column] = df[column] + correction_db

    df = df.set_index("datetime")
    df['oca'] = [_oca_limit(timestamp,OCA_LIMITS[oca_type]) for timestamp in df.index]

    frequency = f"{aggregation_seconds}s"
    aggregated = df.resample(frequency).agg(
        {
            "la_db"     :   _leq,
            "la_max_db" :   "max",
            "la_min_db" :   "min",
            "oca"       :   "min"
        }
    )

    bin_times = aggregated.index + pd.to_timedelta(aggregation_seconds / 2, unit ="s")

    
    
    
    

    for percentile in percentiles:

        quantile = (100.0 - percentile) / 100.0
        aggregated[f"L{percentile}"] = (df['la_db'].resample(frequency).quantile(quantile))
        

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True,exist_ok=True)

    filename = _safe_filename(plot_name)
    png_path = output_dir / f"{filename}_{aggregation_seconds}s_time_plot.png"
    csv_path = output_dir / f"{filename}_{aggregation_seconds}s_time_plot.csv"

    fig,ax = plt.subplots(figsize=(20,10))

    try:
        ax.set_facecolor("white")

        series = [
            ("la_db",       "LAeq", "red", 3),
            ("la_max_db",   "Lmax", "#FF99FF", 1),
            ("la_min_db",   "Lmin", "#92D050", 1),
            ("oca",         "OCA", "#00B0F0", 1),
        ]

        for column, label, color, linewidth in series:
            ax.plot(
                bin_times,
                aggregated[column],
                marker="o",
                markersize=5,
                linewidth=linewidth,
                color=color,
                label=label,
            )

        for percentile in percentiles:
            column = f"L{percentile}"
            if column in aggregated.columns:
                ax.plot(
                    bin_times,
                    aggregated[column],
                    marker="o",
                    markersize=5,
                    linewidth=0.8,
                    label=column,
                )

        ax.set_ylim(30, 105)
        ax.set_ylabel("dB(A)")
        ax.set_xlabel("Hora")
        ax.set_title(
            f"{plot_name} - Nivel equivalente cada {aggregation_seconds}"
        )

        ax.set_xlim(
            aggregated.index.min(),
            aggregated.index.max() + pd.Timedelta(seconds=aggregation_seconds),
        )
        locator = mdates.AutoDateLocator(
            minticks=3, maxticks=8, tz=timezone_name
        )
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(
            mdates.ConciseDateFormatter(locator, tz=timezone_name)
        )
        ax.tick_params(axis="x", labelrotation=90)
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1))
        
        fig.tight_layout()
        fig.savefig(png_path,dpi=300)

        csv_data = aggregated.rename(columns=
                                     {
                                         "la_db"    : "LAeq",
                                         "la_max_db": "Lmax",
                                         "la_min_db": "Lmin",
                                         "oca"      : "OCA"
                                     })
        csv_data.to_csv(csv_path,index_label="datetime")

    finally:
        plt.close(fig)

    return png_path,csv_path


    