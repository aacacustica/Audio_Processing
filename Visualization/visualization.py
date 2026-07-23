from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence, Tuple

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
import plotly.express as px
import seaborn as sns
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

from config import *
from utils import (
    PlotContext,
    SkipPlot,
    add_datetime_features,
    aggregate_spl,
    align_spl_predictions,
    categorize_time_of_day,
    categorize_time_of_day_4,
    dominant_category_per_bin,
    energy_mean,
    map_taxonomy,
    mode_or_na,
    normalize_predictions,
    prepare_dataframe,
    prepare_spectrogram_data,
    safe_plot,
    select_night_data,
)


plt.rc("font", size=MEDIUM_SIZE)
plt.rc("axes", titlesize=MEDIUM_SIZE)
plt.rc("axes", labelsize=MEDIUM_SIZE)
plt.rc("xtick", labelsize=MEDIUM_SIZE)
plt.rc("ytick", labelsize=MEDIUM_SIZE)
plt.rc("legend", fontsize=MEDIUM_SIZE)
plt.rc("figure", titlesize=BIGGER_SIZE)


cmap_dict = sns.color_palette( palette=[ "#C8FFC8","#00C800","#007800","#FFFF00","#FFC878","#FF9600","#FF0000","#780000","#FF00FF","#8C3CFF","#000078"],n_colors=11,)

hex_colors = [mcolors.to_hex(color) for color in cmap_dict]
custom_color_scale = [[index / len(hex_colors), color] for index, color in enumerate(hex_colors)]
custom_color_scale.append([1, hex_colors[-1]])

WEEKDAY_ORDER = [ "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

WEEKDAY_TRANSLATION = {
    "Monday": "Lunes",
    "Tuesday": "Martes",
    "Wednesday": "Miércoles",
    "Thursday": "Jueves",
    "Friday": "Viernes",
    "Saturday": "Sábado",
    "Sunday": "Domingo",
}





# ---------------------------------------------------------------------------
# AUXILIARES ESPECÍFICOS DE VISUALIZACIÓN
# ---------------------------------------------------------------------------

def _context( folder_output_dir: str, plotname: str, logger: Any, agg_period: int = 900) -> PlotContext:

    return PlotContext(
        output_dir          = Path(folder_output_dir),
        plotname            = plotname,
        logger              = logger,
        agg_period_seconds  = int(agg_period),
    )
    

def _prepare_time_dataframe(dataframe: pd.DataFrame,name: str,required_columns: Sequence[str],numeric_columns: Sequence[str] = (),dropna_columns: Sequence[str] = (),) -> pd.DataFrame:

    """
    Normaliza un DataFrame temporal sin modificar el objeto original.

    Prioridad de fecha:
    1. columna datetime;
    2. índice datetime;
    3. columna Fecha;
    4. columna Date hour;
    5. columna Time;
    6. columna date.
    """
    date_column: Optional[str] = None

    if "datetime" in dataframe.columns: date_column = "datetime"        
    elif isinstance(dataframe.index, pd.DatetimeIndex): date_column = None
    else:
        for candidate in ("Fecha", "Date hour", "Time", "date"):
            if candidate in dataframe.columns:
                date_column = candidate
                break

    data = prepare_dataframe(
        dataframe           = dataframe,
        name                = name,
        required_columns    = required_columns,
        datetime_column     = date_column,
        set_datetime_index  = True,
        numeric_columns     = numeric_columns,
        dropna_columns      = dropna_columns,
        min_rows            = 1,
    )

    if not isinstance(data.index, pd.DatetimeIndex): raise SkipPlot(f"{name} no tiene un índice temporal válido")
        

    return data.sort_index()


def _with_time_features(dataframe: pd.DataFrame) -> pd.DataFrame:
    
    data = add_datetime_features(dataframe)

    data["day_name"] = data["weekday"]
    data["Día"] = data["weekday_es"]
    data["Día"] = pd.Categorical( data["Día"], categories=WEEKDAY_ORDER,ordered=True)

    data["fullday"] = (data["day"].astype(str).str.zfill(2) + " " + data["weekday_es"].astype(str))
    
    return data


def _resolve_agg_func(agg_func: Any) -> Any:
    
    if agg_func is None: return energy_mean
    
    if isinstance(agg_func, str):
        if agg_func.lower() in {"leq", "energy_mean"}:
            return energy_mean
        return agg_func

    if callable(agg_func) and getattr(agg_func, "__name__", "") == "leq": return energy_mean
        

    return agg_func


def _taxonomy_settings( taxonomy_map: Mapping[str, str], dataframe: pd.DataFrame,logger: Any,) -> Tuple[str, Mapping[str, str]]:


    """
    Mantiene el criterio original para urban/port, pero evita fallar cuando
    la columna de la ontología no está disponible.
    """

    if "Siren" in set(taxonomy_map.values()):
        desired_column  = "NoisePort_Level_1"
        palette         = COLOR_PALLET_PORT_L1
        logger.info("Using 'NoisePort_Level_1' class for plotting")
    else:
        desired_column  = "Brown_Level_2"
        palette         = COLOR_PALLET_URBAN
        logger.info("Using 'Brown_Level_2' class for plotting")

    if desired_column in dataframe.columns: return desired_column, palette
        
    if "mapped_class" in dataframe.columns:
        logger.warning("No existe %s en los datos enriquecidos; " "se utilizará mapped_class",desired_column)
        return "mapped_class", palette

    raise SkipPlot( f"No existe ni {desired_column!r} ni 'mapped_class'")
        

def _enrich_predictions( predictions: pd.DataFrame,yamnet_csv: pd.DataFrame,taxonomy_map,logger) -> pd.DataFrame:
    

    data = predictions.copy()

    if not isinstance(data.index, pd.DatetimeIndex):
        data.index = pd.to_datetime(data.index,errors="coerce")
        data = data[~data.index.isna()]

    if data.empty:raise SkipPlot("No quedan predicciones con índice temporal válido")
        

    data["display_name"] = data["class"]

    ontology = yamnet_csv.copy()
    ontology = ontology.loc[:,~ontology.columns.str.contains("^Unnamed",regex=True,)]


    if "display_name" not in ontology.columns:raise SkipPlot("yamnet_csv no contiene display_name")

    # Evita multiplicar filas si hay nombres duplicados.
    ontology = ontology.drop_duplicates(subset=["display_name"],keep="first")
    ontology = ontology.set_index("display_name")

    # join(on=...) conserva el DatetimeIndex de data.
    enriched = data.join(
        ontology,
        on              = "display_name",
        how             = "left",
        rsuffix         = "_yamnet",
    )

    enriched = map_taxonomy(
        predictions     = enriched,
        taxonomy_map    = taxonomy_map,
        logger          = logger,
        class_column    = "class",
        output_column   = "mapped_class",
    )

    enriched["probability"] = pd.to_numeric( enriched["probability"],errors="coerce")
    enriched = enriched.dropna(subset=["class","probability",])

    if enriched.empty:raise SkipPlot("No quedan predicciones después ""del enriquecimiento YAMNet")

    if not isinstance(enriched.index,pd.DatetimeIndex):raise SkipPlot("El enriquecimiento YAMNet perdió ""el DatetimeIndex")


    logger.info("Predicciones enriquecidas: %s filas; índice=%s; probability=%s",len(enriched),type(enriched.index).__name__,enriched["probability"].dtype,)

    return enriched.sort_index()


def _prepare_aligned_predictions(df: pd.DataFrame,df_pred: pd.DataFrame,yamnet_csv: Optional[pd.DataFrame],taxonomy_map: Mapping[str, str],laeq_column: str,logger: Any)-> pd.DataFrame:

    aligned = align_spl_predictions(
        spl_dataframe           = df,
        prediction_dataframe    = df_pred,
        laeq_column             = laeq_column,
        logger                  = logger,
        spl_date_column         = "datetime",
        prediction_date_column  = "date",
        tolerance               = "1s",
    )

    aligned['probability']  = pd.to_numeric(aligned['probability'],errors='coerce')
    aligned                 = aligned.dropna(subset=[laeq_column,'class','probability'])
    aligned.index           = pd.to_datetime(aligned.index,errors='coerce')
    aligned                 = aligned[ ~aligned.index.isna()].sort_index()

    if not isinstance(aligned.index,pd.DatetimeIndex): raise SkipPlot("Las predicciones alineadas no tienen un DatetimeIndex.")
    logger.info("Datos preparados: filas=%s, índice=%s, probabilidad=%s",len(aligned),type(aligned.index).__name__,aligned['probability'].dtype) 

    return _enrich_predictions(predictions=aligned,taxonomy_map=taxonomy_map,logger=logger,yamnet_csv=yamnet_csv)


def _palette_color(palette: Mapping[str, str],category: Any) -> str:
    
    try:return palette.get(category, "#808080")
    except AttributeError:return "#808080"
        


# ---------------------------------------------------------------------------
# 1. EVOLUCIÓN NOCTURNA HORARIA
# ---------------------------------------------------------------------------

@safe_plot
def plot_night_evolution(df,folder_output_dir: str,logger,laeq_column: str,plotname: str, indicador_noche: str):
    

    context = _context(
        folder_output_dir   = folder_output_dir,
        plotname            = plotname,
        logger              = logger,
    )

    data = _prepare_time_dataframe(
        dataframe           = df,
        name                = "Night SPL dataframe",
        required_columns    = [laeq_column, "night_str"],
        numeric_columns     = [laeq_column],
        dropna_columns      = [laeq_column, "night_str"],
    )

    data = _with_time_features(data)
    data["Día"] = data["night_str"]

    night_data = select_night_data(
        dataframe          = data,
        complete_night     = True,
        start_hour         = 23,
        end_hour           = 7,
    )

    # Conserva el comportamiento original: una posición por hora.
    night_data["plot_hour"] = (night_data.index.hour.astype(int))
    night_data.loc[night_data["plot_hour"] == 23,"plot_hour"] = -1
    night_data = night_data.sort_values(["night_date", "plot_hour"])
        
    fig = sns.relplot(
        data            = night_data,
        x               = "plot_hour",
        y               = laeq_column,
        kind            = "line",
        hue             = "Día",
        estimator       = energy_mean,
        aspect          = 1.3,
        palette         = C_MAP_WEEKDAY_NIGHT,
    )

    axis = fig.axes.flat[0]
    axis.set_xticks(range(-1, 7))
    axis.set_xticklabels(["23:00","00:00","01:00","02:00", "03:00","04:00","05:00","06:00"])
    axis.set_yticks(range(DB_RANGE_BOTTOM,DB_RANGE_TOP,BD_RANGE_STEP))
    axis.set_xlim(-1.5, 6.5)
    axis.set_title(f"Evolución {indicador_noche}")
    axis.set_ylabel("dB(A)")
    axis.set_xlabel("Hora")
    axis.spines["top"].set_visible(True)
    axis.spines["right"].set_visible(True)

    suffix = f"{indicador_noche}_evolution"

    context.save_dataframe(night_data,suffix=suffix,index=False)
    context.save_matplotlib(fig.figure,suffix=suffix,dpi=150,)


# ---------------------------------------------------------------------------
# 2. EVOLUCIÓN NOCTURNA DE 15 MINUTOS
# ---------------------------------------------------------------------------

@safe_plot
def plot_night_evolution_15_min(df, folder_output_dir: str, logger, name_extension, laeq_column: str, plotname: str, indicador_noche: str,):
    context = _context(
        folder_output_dir,
        plotname,
        logger,
        agg_period=900,
    )

    data = _prepare_time_dataframe(
        dataframe        = df,
        name             = "Night 15-minute SPL dataframe",
        required_columns = [laeq_column, "night_str"],
        numeric_columns  = [laeq_column],
        dropna_columns   = [laeq_column, "night_str"],
    )

    data["Día"] = data["night_str"]

    laeq_15min = (data[laeq_column].resample("15min").apply(energy_mean))

    night_label_15min = (data["Día"].resample("15min").agg(mode_or_na))

    resampled = pd.DataFrame({laeq_column: laeq_15min, "Día": night_label_15min,}).dropna(subset=[laeq_column, "Día"])
    context.require(not resampled.empty, "El remuestreo nocturno de 15 minutos no produjo datos",)

    night_data = select_night_data(
        dataframe      = resampled,
        complete_night = True,
        start_hour     = 23,
        end_hour       = 7,
    )

    night_data["date"] = night_data.index.date
    night_data["time"] = night_data.index.time

    # Mantiene el eje original: el timestamp representa el comienzo del bloque,
    # pero la etiqueta se desplaza 15 minutos.
    night_data["plot_time"] = [((time_value.hour * 60 + time_value.minute - 15) - (23 * 60)) if time_value.hour >= 23 else (time_value.hour * 60 + time_value.minute - 15 + 60) for time_value in night_data["time"]]

    fig = sns.relplot(
        data      = night_data,
        x         = "plot_time",
        y         = laeq_column,
        kind      = "line",
        errorbar  = None,
        hue       = "Día",
        estimator = energy_mean,
        aspect    = 1.3,
        palette   = C_MAP_WEEKDAY_NIGHT,
    )

    axis = fig.axes.flat[0]

    x_labels = [f"{hour:02d}:{minute:02d}" for hour in range(23, 24) for minute in range(0, 60, 15)] + [f"{hour:02d}:{minute:02d}" for hour in range(0, 7) for minute in range(0, 60, 15)]

    x_ticks = list(range(-15, 465, 15))

    axis.set_xticks(x_ticks)
    axis.set_xticklabels(x_labels, rotation=90)
    axis.set_yticks(range(DB_RANGE_BOTTOM, DB_RANGE_TOP, BD_RANGE_STEP,))
    axis.set_xlim(-30, 465)
    axis.set_title(f"Evolución {indicador_noche} cada 15 minutos")
    axis.set_ylabel("dB(A)")
    axis.set_xlabel("Hora")
    axis.spines["top"].set_visible(True)
    axis.spines["right"].set_visible(True)

    suffix = (f"{indicador_noche}_evolution_{name_extension}")

    context.save_dataframe(night_data, suffix=suffix, index=False,)
    context.save_matplotlib(fig.figure, suffix=suffix, dpi=150,)


# ---------------------------------------------------------------------------
# 3. LAEQ POR CLASE
# ---------------------------------------------------------------------------

@safe_plot
def plot_predic_laeq_15_min(df: pd.DataFrame, yamnet_csv: pd.DataFrame, taxonomy_map, df_Pred: pd.DataFrame, folder_output_dir: str, logger, columns_dict: dict, agg_period: int, plotname: str,):
    context = _context(
        folder_output_dir,
        plotname,
        logger,
        agg_period=agg_period,
    )

    laeq_column = columns_dict["LAEQ_COLUMN_COEFF"]

    aligned = _prepare_aligned_predictions(
        df           = df,
        df_pred      = df_Pred,
        yamnet_csv   = yamnet_csv,
        taxonomy_map = taxonomy_map,
        laeq_column  = laeq_column,
        logger       = logger,
    )

    class_to_plot, color_palette = _taxonomy_settings(taxonomy_map, aligned, logger,)

    grouped_df = (aligned.dropna(subset=[class_to_plot, laeq_column]).groupby(class_to_plot, observed=True).agg(number=("class", "size"), LAeq=(laeq_column, energy_mean), probability_mean=("probability", "mean"),).reset_index())

    context.require(not grouped_df.empty, "No quedan clases para calcular LAeq",)

    fig = px.treemap(
        grouped_df,
        path               = [class_to_plot],
        values             = "number",
        color              = class_to_plot,
        color_discrete_map = color_palette,
        custom_data        = ["LAeq", "probability_mean"],
    )

    fig.update_layout(title=(f"{plotname} | Promedio Energético " "(LAeq) por Clases"))
    fig.update_traces(hovertemplate=("<b>%{label}</b><br>" "LAeq: %{customdata[0]:.2f} dB<br>" "Probabilidad media: %{customdata[1]:.3f}<br>" "Count: %{value}" "<extra></extra>"), texttemplate=("%{label}<br><br>" "LAeq: %{customdata[0]:.2f} dB"),)

    context.save_plotly(fig, suffix="LAeq_class_mean",)
    context.save_dataframe(grouped_df, suffix="LAeq_class_mean", index=False,)


# ---------------------------------------------------------------------------
# 4. LAEQ POR CLASE Y PERIODO LD/LE/LN
# ---------------------------------------------------------------------------

@safe_plot
def plot_predic_laeq_15_min_period(df: pd.DataFrame, yamnet_csv: pd.DataFrame, taxonomy_map, df_Pred: pd.DataFrame, folder_output_dir: str, logger, columns_dict: dict, agg_period: int, plotname: str,):
    period_output = (Path(folder_output_dir) / "Prediction_LAeq_15_min_Period")

    context = _context(
        str(period_output),
        plotname,
        logger,
        agg_period=agg_period,
    )

    laeq_column = columns_dict["LAEQ_COLUMN_COEFF"]

    aligned = _prepare_aligned_predictions(
        df           = df,
        df_pred      = df_Pred,
        yamnet_csv   = yamnet_csv,
        taxonomy_map = taxonomy_map,
        laeq_column  = laeq_column,
        logger       = logger,
    )

    class_to_plot, color_palette = _taxonomy_settings(taxonomy_map, aligned, logger,)

    aligned["time_of_day"] = [categorize_time_of_day(hour) for hour in aligned.index.hour]

    period_order = ["Ld", "Le", "Ln"]
    aligned["time_of_day"] = pd.Categorical(aligned["time_of_day"], categories=period_order, ordered=True,)

    grouped_df = (aligned.dropna(subset=[class_to_plot, "time_of_day", laeq_column,]).groupby([class_to_plot, "time_of_day"], observed=True,).agg(number=("class", "size"), LAeq=(laeq_column, energy_mean), probability_mean=("probability", "mean"),).reset_index())

    context.require(not grouped_df.empty, "No hay datos agrupados por periodo",)

    for period in period_order:
        period_df = grouped_df.loc[grouped_df["time_of_day"] == period].copy()

        if period_df.empty:
            logger.info("No hay datos para el periodo %s. Se omite.", period,)
            continue

        fig = px.treemap(
            period_df,
            path               = [px.Constant(period), class_to_plot],
            values             = "number",
            color              = class_to_plot,
            color_discrete_map = color_palette,
            custom_data        = ["LAeq", "probability_mean"],
        )

        fig.update_layout(title=(f"{plotname} | Promedio Energético " f"(LAeq) distribución por Periodo " f"{period} por Clases"))
        fig.update_traces(hovertemplate=("<b>%{label}</b><br>" "LAeq: %{customdata[0]:.2f} dB<br>" "Probabilidad media: " "%{customdata[1]:.3f}<br>" "Count: %{value}" "<extra></extra>"), texttemplate=("%{label}<br><br>" "LAeq: %{customdata[0]:.2f} dB"),)

        suffix = f"LAeq_class_period_{period}"

        context.save_plotly(fig, suffix=suffix)
        context.save_dataframe(period_df, suffix=suffix, index=False,)


# ---------------------------------------------------------------------------
# 5. LAEQ POR CLASE Y PERIODOS DE 4 HORAS
# ---------------------------------------------------------------------------

@safe_plot
def plot_predic_laeq_15_min_4h(df: pd.DataFrame, yamnet_csv: pd.DataFrame, taxonomy_map, df_Pred: pd.DataFrame, folder_output_dir: str, logger, columns_dict: dict, agg_period: int, plotname: str,):
    period_output = (Path(folder_output_dir) / "Prediction_LAeq_15_min_4h")

    context = _context(
        str(period_output),
        plotname,
        logger,
        agg_period=agg_period,
    )

    laeq_column = columns_dict["LAEQ_COLUMN_COEFF"]

    aligned = _prepare_aligned_predictions(
        df           = df,
        df_pred      = df_Pred,
        yamnet_csv   = yamnet_csv,
        taxonomy_map = taxonomy_map,
        laeq_column  = laeq_column,
        logger       = logger,
    )

    class_to_plot, color_palette = _taxonomy_settings(taxonomy_map, aligned, logger,)

    aligned["time_of_day"] = [categorize_time_of_day_4(hour) for hour in aligned.index.hour]

    period_order = ["Ld_1", "Ld_2", "Ld_3", "Le", "Ln_1", "Ln_2",]

    aligned["time_of_day"] = pd.Categorical(aligned["time_of_day"], categories=period_order, ordered=True,)

    grouped_df = (aligned.dropna(subset=[class_to_plot, "time_of_day", laeq_column,]).groupby([class_to_plot, "time_of_day"], observed=True,).agg(number=("class", "size"), LAeq=(laeq_column, energy_mean), probability_mean=("probability", "mean"),).reset_index())

    context.require(not grouped_df.empty, "No hay datos agrupados en periodos de 4 horas",)

    for period in period_order:
        period_df = grouped_df.loc[grouped_df["time_of_day"] == period].copy()

        if period_df.empty:
            logger.info("No hay datos para el periodo %s. Se omite.", period,)
            continue

        fig = px.treemap(
            period_df,
            path               = [px.Constant(period), class_to_plot],
            values             = "number",
            color              = class_to_plot,
            color_discrete_map = color_palette,
            custom_data        = ["LAeq", "probability_mean"],
        )

        fig.update_layout(title=(f"{plotname} | Promedio Energético " f"(LAeq) distribución por Periodo " f"{period} por Clases"))
        fig.update_traces(hovertemplate=("<b>%{label}</b><br>" "LAeq: %{customdata[0]:.2f} dB<br>" "Probabilidad media: " "%{customdata[1]:.3f}<br>" "Count: %{value}" "<extra></extra>"), texttemplate=("%{label}<br><br>" "LAeq: %{customdata[0]:.2f} dB"),)

        suffix = f"LAeq_class_period_{period}"

        context.save_plotly(fig, suffix=suffix)
        context.save_dataframe(period_df, suffix=suffix, index=False,)


# ---------------------------------------------------------------------------
# 6. BARRAS APILADAS DE PREDICCIONES POR DÍA
# ---------------------------------------------------------------------------

@safe_plot
def plot_prediction_stack_bar(df_Pred: pd.DataFrame, yamnet_csv, taxonomy_map, folder_output_dir: str, logger, plotname: str,):
    context = _context(
        folder_output_dir,
        plotname,
        logger,
    )

    predictions = normalize_predictions(
        dataframe          = df_Pred,
        logger             = logger,
        date_column        = "date",
        class_column       = "class",
        probability_column = "probability",
    )

    enriched = _enrich_predictions(
        predictions  = predictions,
        taxonomy_map = taxonomy_map,
        logger       = logger,
        yamnet_csv   = yamnet_csv,
    )

    enriched = _with_time_features(enriched)
    enriched["Día"] = enriched["date_day"]

    class_to_plot, color_palette = _taxonomy_settings(taxonomy_map, enriched, logger,)

    grouped = (enriched.dropna(subset=[class_to_plot, "Día"]).groupby(["Día", class_to_plot], observed=True,).size().reset_index(name="Distribución de clases"))

    context.require(not grouped.empty, "No hay predicciones para la barra apilada",)

    day_order = list(pd.unique(enriched["Día"]))
    grouped["Día"] = pd.Categorical(grouped["Día"], categories=day_order, ordered=True,)

    fig = px.bar(grouped, x="Día", y="Distribución de clases", color=class_to_plot, title=f"{plotname} | Clases por Día", color_discrete_sequence=px.colors.qualitative.Alphabet, color_discrete_map=color_palette, height=900, width=2000,)

    context.save_plotly(fig, suffix="prediction_stack_map",)
    context.save_dataframe(grouped, suffix="prediction_stack_map", index=False,)


# ---------------------------------------------------------------------------
# 7. MAPA TEMPORAL DE LA TAXONOMÍA DOMINANTE
# ---------------------------------------------------------------------------

@safe_plot
def plot_prediction_map(df_Pred: pd.DataFrame, taxonomy_map, agg_period, folder_output_dir: str, logger, plotname: str,):
    context = _context(
        folder_output_dir,
        plotname,
        logger,
        agg_period=int(agg_period),
    )

    predictions = normalize_predictions(
        dataframe          = df_Pred,
        logger             = logger,
        date_column        = "date",
        class_column       = "class",
        probability_column = "probability",
    )

    predictions = map_taxonomy(predictions=predictions, taxonomy_map=taxonomy_map, logger=logger, class_column="class", output_column="mapped_class",)

    dominant = dominant_category_per_bin(dataframe=predictions, category_column="mapped_class", rule=context.resample_rule,)

    dominant = _with_time_features(dominant)

    category_order = list(pd.unique(dominant["mapped_class"]))

    context.require(bool(category_order), "No quedan categorías para el mapa",)

    class_to_num = {category: index + 1 for index, category in enumerate(category_order)}

    dominant["class_num"] = (dominant["mapped_class"].map(class_to_num))

    day_class = pd.pivot_table(
        data    = dominant,
        columns = dominant.index.time,
        index   = ["year", "month", "fullday"],
        values  = "class_num",
        aggfunc = mode_or_na,
    )

    context.require(not day_class.empty and not day_class.isna().all().all(), "La tabla del mapa de predicciones está vacía",)

    if "Siren" in set(taxonomy_map.values()):
        color_palette = COLOR_PALLET_PORT_L1
    else:
        color_palette = COLOR_PALLET_URBAN

    colors = [_palette_color(color_palette, category) for category in category_order]

    cmap = ListedColormap(colors)

    legend_elements = [Patch(facecolor=_palette_color(color_palette, category,), label=(f"Clase {class_to_num[category]} " f"- {category}"),) for category in category_order]

    fig, axis = plt.subplots(figsize=(45, 35))

    sns.heatmap(
        day_class.astype(float),
        annot      = False,
        cmap       = cmap,
        linewidths = 0.5,
        cbar       = False,
        vmin       = 0.5,
        vmax       = len(category_order) + 0.5,
        ax         = axis,
    )

    step = 2
    tick_indices = list(range(0, len(day_class.columns), step))

    axis.set_xticks([index + 0.5 for index in tick_indices])
    axis.set_xticklabels([day_class.columns[index].strftime("%H:%M:%S") for index in tick_indices], rotation=90, fontsize=50,)

    axis.set_yticklabels([f"{index[0]}-{index[1]}-{index[2]}" for index in day_class.index], rotation=0, fontsize=50,)

    axis.legend(handles=legend_elements, title="Clases", loc="center left", bbox_to_anchor=(1, 0.5), fontsize=40,)

    axis.set_title((f"{plotname} | Clase dominante cada " f"{context.period_label}"), fontsize=60,)

    context.save_matplotlib(fig, suffix="prediction_map", dpi=150,)
    context.save_dataframe(day_class, suffix="prediction_map", index=True,)


# ---------------------------------------------------------------------------
# 8. TREEMAP JERÁRQUICO DE PREDICCIONES
# ---------------------------------------------------------------------------

@safe_plot
def plot_tree_map(df_Pred: pd.DataFrame, taxonomy_map, folder_output_dir: str, logger, plotname: str,):
    tree_output = (Path(folder_output_dir) / "Prediction_Tree_Map")

    context = _context(
        str(tree_output),
        plotname,
        logger,
    )

    predictions = normalize_predictions(
        dataframe          = df_Pred,
        logger             = logger,
        date_column        = "date",
        class_column       = "class",
        probability_column = "probability",
    )

    # Se conserva la lectura del mapa YAMNet configurado en el proyecto.
    home_dir = Path.home()
    yamnet_path = (home_dir / RELATIVE_PATH_YAMNET_MAP.lstrip("\\/"))

    yamnet_csv: Optional[pd.DataFrame] = None

    if yamnet_path.is_file():
        yamnet_csv = pd.read_csv(yamnet_path, sep=";",)
    else:
        logger.warning("No existe el mapa YAMNet en %s; " "se usará taxonomy_map", yamnet_path,)

    enriched = _enrich_predictions(
        predictions  = predictions,
        taxonomy_map = taxonomy_map,
        logger       = logger,
        yamnet_csv   = yamnet_csv,
    )

    enriched = _with_time_features(enriched)

    class_to_plot, color_palette = _taxonomy_settings(taxonomy_map, enriched, logger,)

    plot_data = (enriched.dropna(subset=[class_to_plot, "class"]).groupby([class_to_plot, "class"], observed=True,).size().reset_index(name="number"))

    context.require(not plot_data.empty, "No hay datos para el treemap",)

    fig = px.treemap(
        plot_data,
        path               = [class_to_plot, "class"],
        values             = "number",
        color              = class_to_plot,
        color_discrete_map = color_palette,
    )
    fig.update_layout(title=f"{plotname} | Clases")

    context.save_plotly(fig, suffix="prediction_tree_map",)
    context.save_dataframe(enriched, suffix="prediction_tree_map", index=False,)

    for day in sorted(enriched["day"].dropna().unique()):
        day_source = enriched.loc[enriched["day"] == day].copy()

        if day_source.empty:
            continue

        day_plot_data = (day_source.dropna(subset=[class_to_plot, "class"]).groupby([class_to_plot, "class"], observed=True,).size().reset_index(name="number"))

        if day_plot_data.empty:
            logger.info("No hay datos de treemap para el día %s", day,)
            continue

        day_fig = px.treemap(
            day_plot_data,
            path               = [class_to_plot, "class"],
            values             = "number",
            color              = class_to_plot,
            color_discrete_map = color_palette,
        )

        first_row = day_source.iloc[0]

        day_fig.update_layout(title=(f"{plotname} | " f"{first_row['year']}-" f"{first_row['month']}-" f"{day}"))

        suffix = f"prediction_tree_map{day}"

        context.save_plotly(day_fig, suffix=suffix,)
        context.save_dataframe(day_source, suffix=suffix, index=False,)


# ---------------------------------------------------------------------------
# 9. TIME PLOT
# ---------------------------------------------------------------------------

@safe_plot
def make_time_plot(df: pd.DataFrame, folder_output_dir: str, logger, columns_dict: dict, agg_period: int, plotname: str, percentiles: list,):
    context = _context(
        folder_output_dir,
        plotname,
        logger,
        agg_period=agg_period,
    )

    laeq_column = columns_dict["LAEQ_COLUMN_COEFF"]
    max_column = columns_dict["LAMAX_COLUMN_COEFF"]
    min_column = columns_dict["LAMIN_COLUMN_COEFF"]

    required_columns = [laeq_column, max_column, min_column,]

    if SHOW_OCA and "oca" in df.columns:
        required_columns.append("oca")

    data = _prepare_time_dataframe(
        dataframe        = df,
        name             = "Time plot dataframe",
        required_columns = required_columns,
        numeric_columns  = required_columns,
        dropna_columns   = [laeq_column],
    )

    aggregated = aggregate_spl(dataframe=data, rule=context.resample_rule, laeq_column=laeq_column, max_column=max_column, min_column=min_column,)

    if SHOW_OCA and "oca" in data.columns:
        oca = (data["oca"].resample(context.resample_rule).min())
    else:
        oca = None

        if SHOW_OCA:
            logger.warning("SHOW_OCA está activo, pero no existe " "la columna oca")

    percentile_data = {}

    for percentile in percentiles:
        quantile_value = (100 - float(percentile)) / 100

        percentile_data[f"L{percentile}"] = (data[laeq_column].resample(context.resample_rule).quantile(quantile_value))

    try:
        plt.style.use("seaborn-v0_8-whitegrid")
    except OSError:
        plt.style.use("seaborn-whitegrid")

    fig, axis = plt.subplots(figsize=(20, 10))
    axis.set_facecolor("white")

    axis.plot(aggregated.index, aggregated[laeq_column], linewidth=3, color="red", label="LAeq",)
    axis.plot(aggregated.index, aggregated[max_column], linewidth=1, color="#FF99FF", label="Lmax",)
    axis.plot(aggregated.index, aggregated[min_column], linewidth=1, color="#92D050", label="Lmin",)

    if oca is not None:
        axis.plot(oca.index, oca, color="#00B0F0", label="OCA",)

    for percentile in percentiles:
        name = f"L{percentile}"
        series = percentile_data[name]

        color = None

        try:
            color = PERCENTIL_COLOUR[percentile]
        except (KeyError, TypeError, IndexError):
            logger.warning("No hay color configurado para %s", name,)

        plot_kwargs = {"linewidth": 0.5, "label": name,}

        if color is not None:
            plot_kwargs["color"] = color

        axis.plot(series.index, series,**plot_kwargs,)

    locator = mdates.AutoDateLocator(minticks=3, maxticks=12,)
    formatter = mdates.DateFormatter("%d-%m-%y %H:%M")

    axis.xaxis.set_major_locator(locator)
    axis.xaxis.set_major_formatter(formatter)
    axis.set_xlim(data.index.min(), data.index.max())
    axis.set_ylim(DB_LOWER_LIMIT, DB_UPPER_LIMIT)
    axis.set_ylabel("dB(A)", fontsize=BIGGEST_SIZE)
    axis.set_xlabel("Hora", fontsize=BIGGEST_SIZE)
    axis.set_title((f"{plotname} Nivel equivalente " f"{agg_period}s"), fontsize=BIGGEST_SIZE,)
    axis.tick_params(axis="x", rotation=90, labelsize=BIGGEST_SIZE,)
    axis.tick_params(axis="y", labelsize=BIGGEST_SIZE,)
    axis.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0.1, fancybox=True, framealpha=1, edgecolor="black", fontsize=BIGGEST_SIZE,)
    axis.grid(True, which="both", linestyle="--", linewidth=0.5,)

    fig.tight_layout()

    output_data = aggregated.copy()

    if oca is not None:
        output_data["oca"] = oca

    for name, series in percentile_data.items():
        output_data[name] = series

    suffix = f"{agg_period}s_time_plot"

    context.save_matplotlib(fig, suffix=suffix, dpi=350,)
    context.save_dataframe(output_data, suffix=suffix, index=True,)


# ---------------------------------------------------------------------------
# 10. HEATMAP HORARIO
# ---------------------------------------------------------------------------

@safe_plot
def plot_heatmap_evolution_hour(df, folder_output_dir: str, logger, values_column: str, agg_func: str, plotname: str,):
    context = _context(
        folder_output_dir,
        plotname,
        logger,
    )

    data = _prepare_time_dataframe(
        dataframe        = df,
        name             = "Hourly heatmap dataframe",
        required_columns = [values_column],
        numeric_columns  = [values_column],
        dropna_columns   = [values_column],
    )

    data = _with_time_features(data)
    aggregation = _resolve_agg_func(agg_func)

    leq_day_hour = pd.pivot_table(
        data,
        values  = values_column,
        index   = ["date_day"],
        columns = ["hour"],
        aggfunc = aggregation,
    ).round(1)

    context.require(not leq_day_hour.empty and not leq_day_hour.isna().all().all(), "El heatmap horario no contiene datos",)

    leq_day_hour.columns = [f"{int(hour):02d}:00" for hour in leq_day_hour.columns]

    fig, axis = plt.subplots(figsize=(20, 10))

    heatmap = sns.heatmap(
        leq_day_hour,
        vmin      = 30,
        vmax      = 85,
        cmap      = cmap_dict,
        annot     = True,
        annot_kws = {"size": BIGGER_SIZE},
        ax        = axis,
    )

    axis.set_xlabel("Hora", fontsize=BIGGEST_SIZE,)
    axis.set_ylabel("Día", fontsize=BIGGEST_SIZE,)
    axis.set_title(f"{plotname} Nivel equivalente", fontsize=BIGGEST_SIZE,)
    axis.tick_params(axis="y", rotation=0, labelsize=BIGGEST_SIZE,)
    axis.tick_params(axis="x", rotation=90, labelsize=BIGGEST_SIZE,)

    colorbar = heatmap.collections[0].colorbar
    colorbar.ax.tick_params(labelsize=BIGGEST_SIZE)

    fig.tight_layout()

    context.save_matplotlib(fig, suffix="heatmap_evolucion", dpi=350,)
    context.save_dataframe(leq_day_hour, suffix="heatmap_evolucion", index=True,)


# ---------------------------------------------------------------------------
# 11. HEATMAP DE 15 MINUTOS
# ---------------------------------------------------------------------------

@safe_plot
def plot_heatmap_evolution_15_min(df, folder_output_dir: str, logger, values_column: str, agg_func: str, plotname: str,):
    context = _context(
        folder_output_dir,
        plotname,
        logger,
        agg_period=900,
    )

    data = _prepare_time_dataframe(
        dataframe        = df,
        name             = "15-minute heatmap dataframe",
        required_columns = [values_column],
        numeric_columns  = [values_column],
        dropna_columns   = [values_column],
    )

    data = _with_time_features(data)
    data["15min_interval"] = (data.index.floor("15min").strftime("%H:%M"))

    aggregation = _resolve_agg_func(agg_func)

    leq_day_15min = pd.pivot_table(
        data,
        values  = values_column,
        index   = ["date_day"],
        columns = ["15min_interval"],
        aggfunc = aggregation,
    ).round(1)

    context.require(not leq_day_15min.empty and not leq_day_15min.isna().all().all(), "El heatmap de 15 minutos no contiene datos",)

    fig, axis = plt.subplots(figsize=(20, 10))

    heatmap = sns.heatmap(
        leq_day_15min,
        vmin = 30,
        vmax = 85,
        cmap = cmap_dict,
        ax   = axis,
    )

    axis.set_xlabel("Hora", fontsize=BIGGEST_15_MIN_SIZE,)
    axis.set_ylabel("Día", fontsize=BIGGEST_15_MIN_SIZE,)
    axis.set_title(f"{plotname} Nivel equivalente 15 minutos", fontsize=30,)
    axis.tick_params(axis="y", rotation=0, labelsize=BIGGEST_15_MIN_SIZE,)
    axis.tick_params(axis="x", rotation=90, labelsize=BIGGEST_15_MIN_SIZE,)

    colorbar = heatmap.collections[0].colorbar
    colorbar.ax.tick_params(labelsize=BIGGEST_15_MIN_SIZE)

    fig.tight_layout()

    context.save_matplotlib(fig, suffix="heatmap_evolucion_15_min", dpi=150,)
    # Se conserva el índice, porque contiene el día de cada fila.
    context.save_dataframe(leq_day_15min, suffix="heatmap_evolucion_15_min", index=True,)


# ---------------------------------------------------------------------------
# 12. HEATMAP DE INDICADORES
# ---------------------------------------------------------------------------

@safe_plot
def plot_indicadores_heatmap(df, folder_output_dir: str, logger, plotname: str, ind_column: str,):
    context = _context(
        folder_output_dir,
        plotname,
        logger,
    )

    data = _prepare_time_dataframe(
        dataframe        = df,
        name             = "Indicators dataframe",
        required_columns = [ind_column, "indicador_str",],
        numeric_columns  = [ind_column],
        dropna_columns   = [ind_column, "indicador_str",],
    )

    data = _with_time_features(data)
    data["Fecha"] = data.index
    data["date"] = data.index.date

    durations = (data.groupby(["date", "indicador_str"], observed=True,)["Fecha"].agg(first="min", last="max"))

    durations["duration"] = (durations["last"] - durations["first"]).dt.total_seconds()

    threshold = (LE_SECONDS_MEDIDAS_CORTAS if MEDIDAS_CORTAS else LE_SECONDS)

    first_day = data["date"].min()
    last_day = data["date"].max()
    boundary_days = {first_day, last_day}

    for boundary_day in boundary_days:
        for indicator in ("Ld", "Le", "Ln"):
            key = (boundary_day, indicator)

            if key not in durations.index:
                continue

            duration = float(durations.loc[key, "duration"])

            logger.info("Duration of %s on %s: %s", indicator, boundary_day, duration,)

            if duration <= threshold:
                data = data.loc[~((data["date"] == boundary_day) & (data["indicador_str"] == indicator))]

                logger.info("%s indicator from %s removed, " "less than or equal to %s seconds", indicator, boundary_day, threshold,)

    context.require(not data.empty, "No quedan datos después del filtro de duración",)

    data["date_weekday"] = (data.index.strftime("%Y-%m-%d") + " " + data["weekday_es"].astype(str))

    indicators_table = pd.pivot_table(
        data    = data,
        index   = "date_weekday",
        columns = "indicador_str",
        values  = ind_column,
        aggfunc = energy_mean,
    ).round(1)

    indicators_table = indicators_table.reindex(columns=["Ln", "Ld", "Le"])

    indicators_table = indicators_table.dropna(how="all")

    context.require(not indicators_table.empty, "La tabla de indicadores está vacía",)

    fig, axis = plt.subplots(figsize=(15, 8))

    heatmap = sns.heatmap(
        indicators_table,
        annot      = True,
        fmt        = ".1f",
        linewidths = 0.5,
        cmap       = cmap_dict,
        vmin       = 30,
        vmax       = 85,
        annot_kws  = {"size": MEDIUM_SIZE},
        ax         = axis,
    )

    axis.set_yticklabels(axis.get_yticklabels(), rotation=0,)
    axis.set_ylabel("Día", fontsize=BIGGEST_SIZE,)
    axis.set_xlabel("Indicador", fontsize=BIGGEST_SIZE,)
    axis.set_title(f"{plotname} Indicadores", fontsize=BIGGEST_SIZE,)
    axis.tick_params(axis="y", rotation=0, labelsize=BIGGEST_SIZE,)
    axis.tick_params(axis="x", rotation=0, labelsize=BIGGEST_SIZE,)

    colorbar = heatmap.collections[0].colorbar
    colorbar.ax.tick_params(labelsize=BIGGEST_SIZE)

    fig.tight_layout()

    context.save_matplotlib(fig, suffix="indicadores", dpi=150,)
    context.save_dataframe(indicators_table, suffix="indicadores", index=True,)

    general_power_averages = (indicators_table.apply(energy_mean).round(1))

    general_power_averages_df = (general_power_averages.to_frame().transpose())

    context.save_dataframe(general_power_averages_df, suffix="indicadores_generales", index=False,)


# ---------------------------------------------------------------------------
# 13. EVOLUCIÓN DIARIA
# ---------------------------------------------------------------------------

@safe_plot
def plot_day_evolution(df, folder_output_dir: str, logger, laeq_column: str, plotname: str,):
    context = _context(
        folder_output_dir,
        plotname,
        logger,
    )

    data = _prepare_time_dataframe(
        dataframe        = df,
        name             = "Day evolution dataframe",
        required_columns = [laeq_column],
        numeric_columns  = [laeq_column],
        dropna_columns   = [laeq_column],
    )

    data = _with_time_features(data)
    data = data.drop_duplicates()

    context.require(not data.empty, "No hay datos para la evolución diaria",)

    fig = sns.relplot(
        data      = data,
        x         = "hour",
        y         = laeq_column,
        kind      = "line",
        hue       = "Día",
        estimator = energy_mean,
        aspect    = 1.3,
        palette   = C_MAP_WEEKDAY,
    )

    axis = fig.axes.flat[0]

    axis.set_xlim(-1, 24)
    axis.set_ylim(DB_RANGE_BOTTOM, DB_RANGE_TOP,)
    axis.set_xticks(range(24))
    axis.set_xticklabels([f"{hour:02d}:00" for hour in range(24)], rotation=90,)
    axis.set_yticks(range(DB_RANGE_BOTTOM, DB_RANGE_TOP, BD_RANGE_STEP,))

    axis.spines["top"].set_visible(True)
    axis.spines["right"].set_visible(True)

    axis.axvline(x=6.50, color=".7", dashes=(2, 1), zorder=0,)
    axis.axvline(x=18.50, color=".7", dashes=(2, 1), zorder=0,)
    axis.axvline(x=22.50, color=".7", dashes=(2, 1), zorder=0,)

    axis.text(0.13, 0.97, "Ln", transform=axis.transAxes, color="black", weight="bold",)
    axis.text(0.53, 0.97, "Ld", transform=axis.transAxes, color="black", weight="bold",)
    axis.text(0.85, 0.97, "Le", transform=axis.transAxes, color="black", weight="bold",)
    axis.text(0.96, 0.97, "Ln", transform=axis.transAxes, color="black", weight="bold",)

    first_date = data.index.min().date()
    last_date = data.index.max().date()

    axis.set_title((f"Evolución día {plotname} " f"Date {first_date} - {last_date}"), fontsize=14,)
    axis.set_ylabel("dB(A)")
    axis.set_xlabel("Hora")

    context.save_matplotlib(fig.figure, suffix="day_evolution", dpi=300,)
    context.save_dataframe(data, suffix="day_evolution", index=False,)


# ---------------------------------------------------------------------------
# 14. EVOLUCIÓN POR PERIODO
# ---------------------------------------------------------------------------

@safe_plot
def plot_period_evolution(df, folder_output_dir: str, logger, laeq_column: str, plotname: str,):
    context = _context(
        folder_output_dir,
        plotname,
        logger,
    )

    data = _prepare_time_dataframe(
        dataframe        = df,
        name             = "Period evolution dataframe",
        required_columns = [laeq_column, "indicador_str",],
        numeric_columns  = [laeq_column],
        dropna_columns   = [laeq_column, "indicador_str",],
    )

    data = _with_time_features(data)
    data = data.drop_duplicates()

    for indicator in pd.unique(
        data["indicador_str"].dropna()
    ):
        # Se conserva la decisión original de no dibujar Ln aquí.
        if indicator == "Ln":
            logger.info("El periodo Ln está excluido de " "plot_period_evolution")
            continue

        period_data = data.loc[data["indicador_str"] == indicator].copy()

        if period_data.empty:
            logger.info("No hay datos para %s. Se omite.", indicator,)
            continue

        fig = sns.relplot(
            data      = period_data,
            x         = "hour",
            y         = laeq_column,
            kind      = "line",
            hue       = "Día",
            estimator = energy_mean,
            aspect    = 1.3,
            palette   = C_MAP_WEEKDAY,
        )

        axis = fig.axes.flat[0]

        if indicator == "Ld":
            axis.set_xlim(6, 19)
            axis.set_xticks(range(7, 19))
            axis.set_xticklabels([f"{hour:02d}:00" for hour in range(7, 19)])

        elif indicator == "Le":
            axis.set_xlim(18.7, 22.3)
            axis.set_xticks([18.7, 19, 20, 21, 22, 22.3])
            axis.set_xticklabels(["", "19:00", "20:00", "21:00", "22:00", "",])

        axis.set_ylim(DB_RANGE_BOTTOM, DB_RANGE_TOP,)
        axis.set_yticks(range(DB_RANGE_BOTTOM, DB_RANGE_TOP, BD_RANGE_STEP,))
        axis.spines["top"].set_visible(True)
        axis.spines["right"].set_visible(True)
        axis.set_title(f"Evolución {indicator}")
        axis.set_ylabel("dB(A)")
        axis.set_xlabel("Hora")

        suffix = f"{indicator}_evolution"

        context.save_matplotlib(fig.figure, suffix=suffix, dpi=150,)
        context.save_dataframe(period_data, suffix=suffix, index=False,)


# ---------------------------------------------------------------------------
# 15. ESPECTROGRAMA
# ---------------------------------------------------------------------------

@safe_plot
def plt_spectrogram(df, folder_output_dir, sufix_string, logger, plotname,):
    spectrogram_output = (Path(folder_output_dir) / "Spectrogram")

    context = _context(
        str(spectrogram_output),
        plotname,
        logger,
    )

    if sufix_string == "SONOMETRO":
        raise SkipPlot("El espectrograma no está habilitado " "para SONOMETRO")

    datetime_column: Optional[str] = None

    if "datetime" in df.columns:
        datetime_column = "datetime"
    elif(not isinstance(df.index, pd.DatetimeIndex) and "date" in df.columns):
        datetime_column = "date"

    data, frequency_columns, frequencies = (prepare_spectrogram_data(dataframe=df, logger=logger, datetime_column=datetime_column,))

    spectrogram_data = (data[frequency_columns].to_numpy(dtype=float).T)

    spectrogram_data = np.clip(spectrogram_data, 20, 110,)

    fig, axis = plt.subplots(figsize=(20, 10))

    mesh = axis.pcolormesh(data.index, frequencies, spectrogram_data, shading="auto", cmap="inferno",)

    fig.colorbar(mesh, ax=axis, label="Magnitude (dB)",)

    axis.set_yticks(frequencies)
    axis.set_yticklabels([f"{frequency:g} Hz" for frequency in frequencies])
    axis.set_ylabel("Frequency (Hz)")
    axis.set_xlabel("Time")
    axis.set_title(f"Spectrogram: {plotname}")
    axis.set_yscale("log")
    axis.set_ylim(frequencies.min(), frequencies.max(),)

    locator = mdates.AutoDateLocator(minticks=3, maxticks=10,)
    axis.xaxis.set_major_locator(locator)
    axis.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
    axis.tick_params(axis="x", rotation=90,)
    axis.grid(False)

    fig.tight_layout()

    context.save_matplotlib(fig, suffix="spectrogram", dpi=150,)
