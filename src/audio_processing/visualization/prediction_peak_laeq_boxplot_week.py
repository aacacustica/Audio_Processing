from pathlib import Path
import re

import pandas as pd
import plotly.express as px

from audio_processing.visualization.configs import PORT_COLORS, URBAN_COLORS


def render_prediction_peak_laeq_boxplot_week(peak_prediction_measurements, class_map_path: Path, taxonomy: str, output_dir: Path, plot_name: str, correction_db: float = 0.0) -> tuple[Path,Path] | None:

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

        if (not prediction.class_name or measurement.la_db is None or measurement.id_medicion is None): continue

        pair_key = (prediction.id_prediccion, measurement.id_prediccion)

        if pair_key in seen_pairs: continue

        seen_pairs.add(pair_key)

        records.append(
            {
                "id_medicion": measurement.id_medicion,
                "class_name": prediction.class_name,
                "la_db": measurement.la_db + correction_db
            }
        )

        if not records: return None

        class_map = pd.read_csv(class_map_path,sep=";")
        required_columns = {"display_name",category_column}
        missing = required_columns.difference(class_map.columns)

        if missing: raise ValueError(f"Faltan columnas en {class_map_path}: {sorted(missing)}")

        class_map = class_map[['display_name',category_column]].drop_duplicates(subset=['display_name'])

        data  = pd.DataFrame(records).merge(class_map,left_on='class_name',right_on='display_name',how='left')

        data[category_column] = data[category_column].replace("",pd.NA)
        data = data.dropna(subset=[category_column,'la_db'])

        if data.empty: return None

        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True,parents=True)
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", plot_name).strip("_")

        html_path = output_dir / f"{safe_name}_LAeq_peak_class_boxplot.html"
        csv_path = output_dir / f"{safe_name}_LAeq_peak_class_boxplot.csv"

        figure = px.box(data,x=category_column,y='la_db',color=category_column,color_discrete_map=color_map,points='outliers',labels={category_column:"Clase",'la_db': "LAeq del ápice (dB)"},hover_data=['class_name','id_medicion'])
        figure.update_layout(title=f"{plot_name} | Distribución de LAeq de picos por clase",xaxis_title='Clase',yaxis_title='LAeq del ápice (dB)',showlegend=False)

        figure.update_xaxes(tickangle=-35)
        figure.write_html(html_path)
        data[['id_medicion','class_name',category_column,'la_db']].to_csv(csv_path,index=False)

        return html_path,csv_path