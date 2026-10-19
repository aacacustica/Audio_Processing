from pathlib import Path
import math
import re

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.patches import Patch
from matplotlib.colors import ListedColormap

from .configs import PORT_COLORS, URBAN_COLORS

def render_prediction_map(prediction_measurements,class_map_path: Path,taxonomy:str,output_dir: Path, plot_name: str, aggregation_seconds: int = 900, timezone_name: str = "Europe/Madrid") -> tuple[Path,Path] | None:

    if aggregation_seconds <=0: raise ValueError(f"aggregation_seconds debe ser mayor que cero. Actual: {aggregation_seconds}")

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
        if prediction.class_name and prediction.prediction_rank == 1: predictions_by_id[prediction.id_prediccion] = prediction

    if not predictions_by_id: return None


    df = pd.DataFrame(
        [
            {
                "class_name": prediction.class_name,
                "datetime": prediction.datetime_inicio,
                "probability": prediction.probability,
            }
            for prediction in predictions_by_id.values()
        ]
    )

    df["datetime"] = (
        pd.to_datetime(df["datetime"], utc=True)
        .dt.tz_convert(timezone_name)
    )
    df["interval"] = df["datetime"].dt.floor(f"{aggregation_seconds}s")

    class_map = pd.read_csv(class_map_path,sep=";")
    required_columns = {"display_name",category_column}
    missing = required_columns.difference(class_map.columns)

    if missing: raise ValueError(f"Faltan columnas en {class_map_path}  :  {sorted(missing)}")

    class_map = class_map[["display_name",category_column]].drop_duplicates(subset=['display_name'])

    df = df.merge(class_map,left_on="class_name",right_on="display_name",how='left')
    df[category_column] = df[category_column].replace("",pd.NA)
    df = df.dropna(subset=[category_column])

    if df.empty: return None


    # La categoría que más aparece gana el intervalo.
    # La probabilidad resuelve los empates.

    grouped = (df.groupby(['interval',category_column],as_index=False).agg(detections=("class_name","size"),probability=("probability","max")).sort_values(['interval','detections','probability',category_column],ascending=[True,False,False,True]).drop_duplicates(subset=['interval']))

    grouped['day'] = grouped['interval'].dt.strftime("%Y-%m-%d")
    grouped['time'] = grouped['interval'].dt.strftime("%H:%M")

    daily_map = grouped.pivot(index="day",columns='time',values=category_column).sort_index(axis=0).sort_index(axis=1)

    if daily_map.empty: return None

    categories = [category for category in color_map if category in set(daily_map.stack().dropna())]

    for category in daily_map.stack().dropna().unique():
        if category not in categories: categories.append(category)

    category_to_number = {category: index for index,category in enumerate(categories)}
    numeric_map = daily_map.replace(category_to_number).astype(float)

    colors = [color_map.get(category,"#999999") for category in categories]
    cmap = ListedColormap(colors)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", plot_name).strip("_")

    png_path = output_dir / f"{safe_name}_prediction_map.png"
    csv_path = output_dir / f"{safe_name}_prediction_map.csv"
    
    fig_width = max(14, min(30, numeric_map.shape[1] * 0.18))
    fig_height = max(5, min(24, numeric_map.shape[0] * 0.45))
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    try:
        sns.heatmap(numeric_map,cmap=cmap,vmin=-0.5,vmax=len(categories) - 0.5,mask=numeric_map.isna(),linewidths=0.2,linecolor="white",cbar=False,ax=ax)

        tick_step = max(1,math.ceil(len(numeric_map.columns) / 24))
        tick_positions = list(range(0,len(numeric_map.columns),tick_step))
        ax.set_xticks([position + 0.5 for position in tick_positions])
        ax.set_xticklabels([numeric_map.columns[position] for position in tick_positions],rotation=90)

        ax.set_xlabel("Hora local")
        ax.set_ylabel("Día")
        interval_minutes = aggregation_seconds // 60
        interval_label = (f"{interval_minutes} min" if aggregation_seconds % 60 == 0 else f"{aggregation_seconds} s")

        ax.set_title(f"{plot_name} | Clases predichas cada {interval_label}")

        ax.legend(handles=[Patch(facecolor=color_map.get(category,"#999999"),label = category) for category in categories],title='Classes',loc="center left",bbox_to_anchor=(1.01,0.5))

        fig.tight_layout()
        fig.savefig(png_path,dpi=200,bbox_inches="tight")

    finally:
        plt.close(fig)


    daily_map.to_csv(csv_path,index_label="day")

    return png_path,csv_path

