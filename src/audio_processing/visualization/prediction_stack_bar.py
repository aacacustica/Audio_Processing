from pathlib import Path
import re

import pandas as pd
import plotly.express as px

from .configs import PORT_COLORS, URBAN_COLORS


def render_prediciton_stack_bar(prediction_measurements, class_map_path: Path, taxonomy: str, output_dir: Path, plot_name: str, timezone_name: str = "Europe/Madrid",correction_db: float = 0.0) -> tuple[Path,Path] | None:

    if taxonomy == "urban":
        category_column = "Brown_Level_2"
        color_map = URBAN_COLORS
    elif taxonomy == "port":
        category_column = "NoisePort_Level_1"
        color_map = PORT_COLORS
    else:
        raise ValueError(f"Taxonomía no compatible con este gráfico: {taxonomy}")

    
    predictions_by_id = {}

    for prediction, _measurement in prediction_measurements:
        if prediction.class_name: predictions_by_id[prediction.id_prediccion] = prediction

    if not predictions_by_id: return None

    records = [{
        "class_name"    : prediction.class_name,
        "datetime"      : prediction.datetime_inicio
    } for prediction in predictions_by_id.values()]

    df = pd.DataFrame(records)

    df['datetime'] = pd.to_datetime(df['datetime'],utc=True).dt.tz_convert(timezone_name)
    df['day'] = df['datetime'].dt.strftime("%Y-%m-%d")

    class_map = pd.read_csv(class_map_path,sep=";")
    required_columns = {"display_name",category_column}
    missing = required_columns.difference(class_map.columns)

    if missing: raise ValueError(f"Faltan columnas en {class_map_path}: {sorted(missing)}")

    class_map = class_map[["display_name",category_column]].drop_duplicates(subset="display_name")

    df = df.merge(class_map,left_on="class_name",right_on="display_name",how='left')
    df[category_column] = df[category_column].replace("",pd.NA)
    df = df.dropna(subset=[category_column])

    if df.empty: return None

    grouped = (df.groupby(['day',category_column]).size().reset_index(name="detections").sort_values(['day',category_column]))

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True,exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", plot_name).strip("_")

    html_path = output_dir / f"{safe_name}_prediction_stack_bar.html"
    csv_path = output_dir / f"{safe_name}_prediction_stack_bar.csv" 

    fig = px.bar(grouped,x="day",y="detections",color=category_column,color_discrete_map=color_map,barmode="stack",title=f"{plot_name} | Clases por Día",labels={"day":"Día","detections":"Número de detecciones",category_column:"Clase"},height=900,width=2000)

    fig.update_layout(xaxis_title="Día",yaxis_title="Número de detecciones")

    fig.write_html(html_path)
    grouped.to_csv(csv_path,index=False)

    return html_path,csv_path
    