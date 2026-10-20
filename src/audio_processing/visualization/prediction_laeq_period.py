from pathlib import Path
import re

import pandas as pd
import plotly.express as px

from .configs import PORT_COLORS, URBAN_COLORS,PERIOD_ORDER,PERIOD_ORDER_4H
from .time_plot import _leq




def _period_for_hour(hour: int,period_scheme:str) -> str:

    if period_scheme == "day_parts":
        
        if 7 <= hour < 19: return "Ld"
        if 19 <= hour < 23: return "Le"
        return "Ln"

    if period_scheme == "four_hour":

        if 7 <= hour < 11: return "Ld_1"
        if 11 <= hour < 15: return "Ld_2"
        if 15 <= hour < 19: return "Ld_3"
        if 19 <= hour < 23: return "Le"
        if hour >= 23 or hour < 3: return "Ln_1"
        return "Ln_2"

    raise ValueError(f"Esquema de periodos desconocido: {period_scheme}")


def render_prediction_laeq_period(prediction_measurements,class_map_path: Path, taxonomy: str, output_dir:Path,plot_name: str, correction_db: float = 0.0, timezone_name: str = "Europe/Madrid",period_scheme:str = "dayparts") -> dict[str , tuple[Path,Path]] | None:

    if taxonomy == "urban":
        category_column = "Brown_Level_2"
        color_map = URBAN_COLORS
    elif taxonomy == "port":
        category_column = "NoisePort_Level_1"
        color_map = PORT_COLORS
    else:
        raise ValueError(f"Taxonomía no compatible con este gráfico: {taxonomy}")

    # Agrupa las mediciones únicas enlazadas a cada predicción.
    by_prediction = {}
    for prediction,measurement in prediction_measurements:

        if not prediction.class_name or measurement.la_db is None: continue

        entry = by_prediction.setdefault(prediction.id_prediccion, {"prediction":prediction,"levels":{}})
        entry['levels'][measurement.id_medicion] = measurement.la_db

    records = []

    for entry in by_prediction.values():
        
        prediction = entry['prediction']
        levels = pd.Series([level + correction_db for level in entry['levels'].values()],dtype="float32")
        if levels.empty: continue

        timestamp = pd.Timestamp(prediction.datetime_inicio)

        if timestamp.tzinfo is None: timestamp = timestamp.tz_localize(timezone_name)
        else: timestamp = timestamp.tz_convert(timezone_name)

        records.append(
            {
                "class_name": prediction.class_name,
                "period":_period_for_hour(timestamp.hour),
                "laeq_window":_leq(levels),
                "period": _period_for_hour(timestamp.hour,period_scheme)
            }
        )

    if not records: return None

    class_map = pd.read_csv(class_map_path,sep=";")
    required_columns = {"display_name",category_column}
    missing = required_columns.difference(class_map.columns)

    if missing: raise ValueError(f"Faltan columnas en {class_map_path}: {sorted(missing)}")

    class_map = class_map[['display_name',category_column]].drop_duplicates(subset=['display_name'])

    df = pd.DataFrame(records).merge(class_map,left_on='class_name',right_on='display_name',how='left')

    df[category_column] = df[category_column].replace("",pd.NA)
    df = df.dropna(subset=[category_column,"laeq_window"])

    if df.empty: return None

    grouped = (df.groupby(['period',category_column]).agg(number=('class_name','size'),LAeq=('laeq_window',_leq)).reset_index())

    output_dir = Path(output_dir) / "Prediction_LAeq_15_min_Period"
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", plot_name).strip("_")

    outputs = {}

    if period_scheme == "dayparts":
        period_order = PERIOD_ORDER
        folder_name = "Prediction_LAeq_15_min_Period"
    else:
        period_order = PERIOD_ORDER_4H
        folder_name = "Prediction_LAeq_15_min_4h"

    output_dir = Path(output_dir) / folder_name

    for period in period_order:
        period_df = grouped[grouped['period'] == period].copy()

        if period_df.empty: continue

        html_path = output_dir / f"{safe_name}_LAeq_class_period_{period}.html"
        csv_path = output_dir / f"{safe_name}_LAeq_class_period_{period}.csv"

        html_path = output_dir / f"{safe_name}_LAeq_class_period_{period}.html"
        csv_path = output_dir / f"{safe_name}_LAeq_class_period_{period}.csv"

        fig = px.treemap(period_df,path=[px.Constant(period), category_column],values="number",color=category_column,color_discrete_map=color_map,hover_data={"LAeq": True, "number": True},custom_data=["LAeq"],)
        fig.update_layout(title=(f"{plot_name} | Promedio Energético (LAeq) "f"por Periodo {period} por Clases"))
        fig.update_traces(hovertemplate=("<b>%{label}</b><br>""LAeq: %{customdata[0]:.2f} dB<br>""Count: %{value}"),texttemplate="%{label}<br><br>LAeq: %{customdata[0]:.2f} dB",)

        fig.write_html(html_path)
        period_df.to_csv(csv_path, index=False)
        outputs[period] = (html_path, csv_path)

    return outputs or None