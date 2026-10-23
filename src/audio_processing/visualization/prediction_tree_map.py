from pathlib import Path
import re

import pandas as pd
import plotly.express as px

from audio_processing.visualization.configs import PORT_COLORS, URBAN_COLORS

def write_treemap(outputs,category_column,output_dir,safe_name,color_map,plot_name,frame: pd.DataFrame, output_key: str, title_suffix: str) -> None:

    grouped = (frame.groupby([category_column,'class_name'],as_index=False).agg(number=('number','sum')).sort_values([category_column,'class_name']))

    html_path = output_dir / f"{safe_name}_prediction_tree_map_{output_key}.html"
    csv_path = output_dir / f"{safe_name}_prediction_tree_map_{output_key}.csv"

    figure = px.treemap(grouped,path=[category_column,'class_name'],values="number",color=category_column,color_discrete_map=color_map,custom_data=['number'])
    figure.update_layout(title=f"{plot_name} |  Frecuencia de predicciones | {title_suffix}")
    figure.update_traces(hovertemplate=("<b>%{label}</b><br>""Predicciones: %{customdata[0]}""<extra></extra>"),texttemplate="%{label}<br>%{value}")

    figure.write_html(html_path)
    grouped.to_csv(csv_path,index=False)
    outputs[output_key] = (html_path,csv_path)

def render_prediction_tree_map(prediction_measurements, class_map_path: Path, taxonomy: str, output_dir: Path, plot_name: str, timezone_name: str = "Europe/Madrid") -> dict[str, tuple[Path,Path]] | None:

    if taxonomy == "urban":
        category_column = "Brown_Level_2"
        color_map = URBAN_COLORS
    elif taxonomy == "port":
        category_column = "NoisePort_Level_1"
        color_map = PORT_COLORS
    else:
        raise ValueError(f"Taxonomía no compatible con este gráfico: {taxonomy}")

    predictions_by_id = {}

    for prediction,_measurement in prediction_measurements:
        if prediction.class_name and prediction.datetime_inicio is not None:
            predictions_by_id[prediction.id_prediccion] = prediction

    if not predictions_by_id: return None

    records = []

    for predictions in predictions_by_id.values():
        timestamp = pd.Timestamp(prediction.datetime_inicio)

        if timestamp.tzinfo is None: timestamp = timestamp.tz_localize(timezone_name)
        else: timestamp = timestamp.tz_convert(timezone_name)

        records.append(
            {
                "class_name": prediction.class_name,
                "local_date": timestamp.strftime("%Y-%m-%d"),
                "number":1
            }
        )

    class_map = pd.read_csv(class_map_path,sep=";")
    required_columns = {"display_name",category_column}
    missing = required_columns.difference(class_map.columns)

    if missing :  raise ValueError(f"Faltan columnas en {class_map_path}: {sorted(missing)}")

    class_map = class_map[["display_name",category_column]].drop_duplicates(subset=['display_name'])

    data = pd.DataFrame(records).merge(class_map,left_on='class_name',right_on='display_name',how='left')

    data[category_column] = data[category_column].replace("",pd.NA)
    data = data.dropna(subset=[category_column,'class_name'])

    if data.empty: return None


    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", plot_name).strip("_")
    outputs = {}

    write_treemap(
        outputs         = outputs,
        category_column = category_column,
        output_dir      = output_dir,
        safe_name       = safe_name,
        color_map       = color_map,
        plot_name       = plot_name,
        frame           = data,
        output_key      = 'global',
        title_suffix    = 'Global')

    for local_date in sorted(data['local_date'].unique()):
        daily_data = data[data['local_date'] == local_date]
        write_treemap(
            outputs         = outputs,
            category_column = category_column,
            output_dir      = output_dir,
            safe_name       = safe_name,
            color_map       = color_map,
            plot_name       = plot_name,
            frame           = daily_data,
            output_key      = f"dat_{local_date}",
            title_suffix    = f"Día {local_date}")

    return outputs or None

