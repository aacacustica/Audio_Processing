from pathlib import Path
import re

import pandas as pd
import plotly.express as px

from audio_processing.visualization.configs import PORT_COLORS, URBAN_COLORS

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