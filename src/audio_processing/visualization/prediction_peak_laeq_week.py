from datetime import timedelta
from pathlib import Path
import re

import pandas as pd
import plotly.express as px

from audio_processing.visualization.time_plot import _leq
from audio_processing.visualization.configs import PORT_COLORS, URBAN_COLORS

def render_prediciton_peak_laeq_week(peak_prediction_measurements,class_map_path: Path, taxonomy: str, output_dir: Path, plot_name: str, correction_db: float = 0.0, timezone_name: str = "Europe/Madrid") -> dict[str,tuple[Path,Path]] | None:

    if taxonomy == "urban":
        category_column = "Brown_Level_2"
        color_map = URBAN_COLORS
    elif taxonomy == "port":
        category_column = "NoisePort_Level_1"
        color_map = PORT_COLORS
    else:
        raise ValueError(f"Taxonomía no compatible con este gráfico: {taxonomy}")

    records = []
    seen_pairs = set()

    for prediction,measurement in peak_prediction_measurements:

        if (not prediction.class_name or measurement.la_db is None or measurement.datetime is None): continue

        pair_key = (prediction.id_prediccion,measurement.id_medicion)

        if pair_key in seen_pairs: continue

        seen_pairs.add(pair_key)

        timestamp = pd.Timestamp(measurement.datetime)

        if timestamp.tzinfo is None: timestamp = timestamp.tz_localize(timezone_name)
        else: timestamp = timestamp.tz_convert(timezone_name)

        local_date = timestamp.date()
        week_start = local_date - timedelta(days = local_date.weekday())

        records.append(
            {
                "class_name" : prediction.class_name,
                "week_start" : week_start.isoformat(),
                "la_db" : measurement.la_db + correction_db
            }
        )

    if not records: return None

    class_map = pd.read_csv(class_map_path,sep=";")
    required_columns = {"display_name",category_column}
    missing = required_columns.difference(class_map.columns)

    if missing: raise ValueError(f"Faltan columnas en {class_map_path}: {sorted(missing)}")

    class_map = class_map[['display_name',category_column]].drop_duplicates(subset=['display_name'])

    data = pd.DataFrame(records).merge(class_map,left_on='class_name',right_on='display_name',how='left')

    data[category_column] = data[category_column].replace("",pd.NA)
    data = data.dropna(subset=[category_column,'la_db'])

    if data.empty: return None

    grouped = data.groupby(['week_start',category_column]).agg(number=('class_name','size'),LAeq=('la_db',_leq)).reset_index()

    output_dir = Path(output_dir)
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", plot_name).strip("_")
    outputs = {}

    for week_start in sorted(grouped['week_start'].unique()):

        week_data = grouped[grouped['week_start'] == week_start].copy()
        week_folder = output_dir / f"week_{week_start}"
        week_folder.mkdir(parents=True,exist_ok=True)

        html_path = week_folder / f"{safe_name}_LAeq_peak_class_mean_{week_start}.html"
        csv_path = week_folder / f"{safe_name}_LAeq_peak_class_mean_{week_start}.csv"

        figure = px.treemap(week_data,path=[category_column],values='number',color=category_column,color_discrete_map=color_map,custom_data=['LAeq'])

        figure.update_layout(title=f"{plot_name} | LAeq de picos por clase | Semana {week_start}")
        figure.update_traces(hovertemplate=("<b>%{label}</b><br>""LAeq: %{customdata[0]:.2f} dB<br>""Picos: %{value}"),texttemplate="%{label}<br>LAeq: %{customdata[0]:.2f} dB")

        figure.write_html(html_path)
        week_data.to_csv(csv_path,index=False)
        outputs[week_start] = (html_path,csv_path)

    return outputs or None

