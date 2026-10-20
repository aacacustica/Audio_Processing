from datetime import timedelta
from pathlib import Path
import re

import pandas as pd
import plotly.express as px

from .configs import PORT_COLORS, URBAN_COLORS
from .time_plot import _leq


def render_prediction_laeq_week(prediction_measurements,class_map_path: Path, taxonomy: str, output_dir: Path, plot_name: str, correction_db: float = 0.0, timezone_name: str = "Europe/Madrid") -> dict[str,tuple[Path,Path]] | None:
    
    if taxonomy == "urban":
        category_column = "Brown_Level_2"
        color_map = URBAN_COLORS
    elif taxonomy == "port":
        category_column = "NoisePort_Level_1"
        color_map = PORT_COLORS
    else:
        raise ValueError(f"Taxonomía no compatible con este gráfico: {taxonomy}")

    by_prediction = {}

    for prediction,measurement in prediction_measurements: 
        if not prediction.class_name or measurement.la_db is None: continue

        entry = by_prediction.setdefault(prediction.id_prediccion, {"prediction":prediction, "levels":{}})
        entry['levels'][measurement.id_medicion] = measurement.la_db

    records = []

    for entry in by_prediction.values():
        
        prediction = entry['prediction']
        levels = pd.Series([level + correction_db for level in entry['levels'].values()],dtype='float64')
        
        if levels.empty: continue

        timestamp = pd.Timestamp(prediction.datetime_inicio)

        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize(timezone_name)
        else:
            timestamp = timestamp.tz_convert(timezone_name)

        local_date = timestamp.date()
        week_start = local_date - timedelta(days=local_date.weekday())

        records.append(
            {
                "class_name": prediction.class_name,
                "week_start": week_start.isoformat(),
                "laeq_window": _leq(levels)
            }
        )

    if not records: return

    class_map = pd.read_csv(class_map_path,sep=';')
    required_columns = {"display_name",category_column}
    missing = required_columns.difference(class_map.columns)

    if missing: raise ValueError(f"Faltan columnas en {class_map_path}: {sorted(missing)}")

    class_map = class_map[['display_name',category_column]].drop_duplicates(subset=['display_name'])

    df = pd.DataFrame(records).merge(class_map,left_on='class_name',right_on='display_name',how='left')

    df[category_column] = df[category_column].replace("",pd.NA)
    df = df.dropna(subset=[category_column,'laeq_window'])

    if df.empty: return None

    grouped = (df.groupby(["week_start",category_column]).agg(number=('class_name','size'),LAeq=('laeq_window',_leq)).reset_index())

    output_dir = Path(output_dir)
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", plot_name).strip("_")
    outputs = {}

    for week_start in sorted(grouped['week_start'].unique()):

        week_df = grouped[grouped["week_start"] == week_start].copy()
        week_folder = output_dir / f"week_{week_start}"
        week_folder.mkdir(parents=True, exist_ok=True)

        html_path = week_folder / f"{safe_name}_LAeq_class_mean_{week_start}.html"
        csv_path = week_folder / f"{safe_name}_LAeq_class_mean_{week_start}.csv"    

        fig = px.treemap(week_df,path=[category_column],values='number',color=category_column,color_discrete_map=color_map,hover_data={"LAeq":True,'number':True},custom_data=['LAeq'])

        fig.update_layout(title=f"{plot_name} | Promedio Energético (LAeq) por Clases | Semana {week_start}")  
        fig.update_traces(hovertemplate=("<b>%{label}</b><br>""LAeq: %{customdata[0]:.2f} dB<br>""Count: %{value}"),texttemplate="%{label}<br><br>LAeq: %{customdata[0]:.2f} dB") 

        fig.write_html(html_path)
        week_df.to_csv(csv_path,index=False)
        outputs[week_start] = (html_path,csv_path)

    return outputs or None
