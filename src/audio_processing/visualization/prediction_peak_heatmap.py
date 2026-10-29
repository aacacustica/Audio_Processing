from __future__ import annotations

from datetime import timedelta
from pathlib import Path
import re

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from audio_processing.visualization.configs import LAEQ_BINS,LAEQ_BIN_LABELS


def render_prediction_peak_heatmap_week(peak_prediction_measurements, class_map_path: Path, taxonomy: str , output_dir: Path, plot_name: str, correction_db: float = 0.0, timezone_name: str = "Europe/Madrid") -> dict[str,Path] | None:


    if taxonomy == "urban":
        category_column = "Brown_Level_2"
    elif taxonomy == "port":
        category_column = "NoisePort_Level_1"
    else:
        raise ValueError(f"Taxonomía no compatible con este gráfico: {taxonomy}")

    records = []
    seen_pairs = set()

    for prediction,measurement in peak_prediction_measurements:

        if not prediction.class_name or measurement.la_db is None: continue
        if measurement.datetime is None: continue

        pair_key = (prediction.id_prediccion, measurement.id_medicion)

        if pair_key in seen_pairs: continue

        seen_pairs.add(pair_key)

        timestamp = pd.Timestamp(measurement.datetime)

        if timestamp.tzinfo is None: timestamp = timestamp.tz_localize(timezone_name)
        else: timestamp = timestamp.tz_convert(timezone_name)

        local_date = timestamp.date()
        week_start = local_date - timedelta(days = local_date.weekday())

        try:
            laeq = float(measurement.la_db) + correction_db
        except (TypeError,ValueError): 
            continue

        records.append(
            {
                "class_name": prediction.class_name,
                "week_start": week_start.isoformat(),
                "laeq": laeq
            }
        )

    if not records: return

    class_map = pd.read_csv(class_map_path,sep=";")
    required_columns = {"display_name",category_column}
    missing = required_columns.difference(class_map.columns)

    if missing : raise ValueError(f"Faltan columnas en {class_map_path}: {sorted(missing)}")

    class_map_path = class_map[["display_name",category_column]].drop_duplicates(subset=['display_name'])

    data = pd.DataFrame(records).merge(class_map,left_on='class_name',right_on='display_name',how='left')

    data[category_column] = data[category_column].replace("",pd.NA)
    data = data.dropna(subset=[category_column,'laeq'])
    data['laeq_bin']  = pd.cut(data['laeq'],bins=LAEQ_BINS,labels=LAEQ_BIN_LABELS,include_lowest=True)

    data = data.dropna(subset=['laeq_bin'])

    if data.empty: return None

    output_dir = Path(output_dir)
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", plot_name).strip("_") or "source"
    outputs: dict[str,Path] = {}

    for week_start in sorted(data['week_start'].unique()):

        week_data = data[data['week_start'] == week_start]
        heatmap_data = pd.crosstab(week_data['laeq_bin'],week_data[category_column]).reindex(index=LAEQ_BIN_LABELS[::-1],fill_value=0)

        week_dir = output_dir / f"week_{week_start}"
        week_dir.mkdir(parents=True, exist_ok=True)
        png_path = week_dir / f"{safe_name}_peak_heatmap_{week_start}.png"

        fig, ax = plt.subplots(figsize=(15, 8))

        try:
            sns.heatmap(heatmap_data, annot=True, fmt=".0f", cmap="Blues", ax=ax)
            ax.set_title(f"{plot_name} | Heatmap de Clases y LAeq | Semana {week_start}")
            ax.set_xlabel("")
            ax.set_ylabel("")
            ax.tick_params(axis="y", labelrotation=0)
            ax.tick_params(axis="x", labelrotation=90)
            fig.tight_layout()
            fig.savefig(png_path, dpi=150)
        finally:
            plt.close(fig)

        outputs[week_start] = png_path

    return outputs or None