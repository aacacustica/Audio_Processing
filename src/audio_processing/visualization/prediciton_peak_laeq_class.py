from pathlib import Path
import re

import pandas as pd
import plotly.express as px

from audio_processing.visualization.time_plot import _leq
from audio_processing.visualization.configs import PORT_COLORS, URBAN_COLORS

def render_prediction_peak_laeq_class(peak_prediction_measurements,class_map_path: Path, taxonomy: str, output_dir: Path, plot_name: str, correction_db: float = 0.0) -> tuple[Path,Path] | None:

    if taxonomy == "urban":
        category_column = "Brown_Level_2"
        color_map = URBAN_COLORS
    elif taxonomy == "port":
        category_column = "NoisePort_Level_1"
        color_map = PORT_COLORS
    else:
        raise ValueError(f"Taxonomía no compatible con este gráfico: {taxonomy}")

    records = [
        {
            "class_name" : prediction.class_name,
            "la_db": measurement.la_db + correction_db
        }
        for prediction,measurement in peak_prediction_measurements if prediction.class_name and measurement.la_db is not None
    ]

    if not records: return None

    class_map = pd.read_csv(class_map_path,sep=";")
    required_columns = {"display_name",category_column}
    missing = required_columns.difference(class_map.columns)

    if missing: raise ValueError(f"Faltan columnas en {class_map_path}: {sorted(missing)}")

    class_map = (class_map[["display_name",category_column]].drop_duplicates(subset=["display_name"]))

    data = pd.DataFrame(records).merge(class_map,left_on="class_name",right_on="display_name",how="left")

    data[category_column] = data[category_column].replace("",pd.NA)
    data = data.dropna(subset=[category_column,"la_db"])

    if data.empty: return None

    grouped = (data.groupby(category_column).agg(number=("class_name","size"),LAeq=("la_db",_leq)).reset_index())

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", plot_name).strip("_")

    html_path = output_dir / f"{safe_name}_LAeq_peak_class_mean.html"
    csv_path = output_dir / f"{safe_name}_LAeq_peak_class_mean.csv"

    fig = px.treemap(grouped,path=[category_column],values='number',color=category_column,color_discrete_map=color_map,custom_data=['LAeq'])

    fig.update_layout(title=f"{plot_name} | LAeq promedio de picos por clase")

    fig.update_traces(hovertemplate=("<b>%{label}</b><br>""LAeq: %{customdata[0]:.2f} dB<br>""Picos: %{value}"),texttemplate="%{label}<br>LAeq: %{customdata[0]:.2f} dB")

    fig.write_html(html_path)
    grouped.to_csv(csv_path,index=False)

    return html_path,csv_path

