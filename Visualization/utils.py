import numpy as np
import pandas as pd

import subprocess
import os

import ast
import inspect
import logging

from dataclasses import dataclass
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple
from datetime import datetime, time

import matplotlib.pyplot as plt

from config import *


class SkipPlot(RuntimeError):
    """Interrupción esperada: no hay datos válidos para crear una gráfica."""

def calculate_duration(start_time, end_time):
    duration = end_time - start_time
    return duration.total_seconds()


def evaluation_period_str(hour_column):
    period = ''
    if hour_column >= 7 and hour_column < 19:
        period = 'Ld'
    elif hour_column >= 19 and hour_column < 23:
        period = 'Le'
    else:
        period = 'Ln'
    return period


def evaluation_period_str_valencia(hour_column):
    period = ''
    if hour_column >= 8 and hour_column < 22:
        period = 'Ld_valencia'
    else:
        period = 'Ln_valencia'
    return period


def add_night_column(hour_column, day_col):
    night_list=["Lunes-Martes","Martes-Miércoles","Miércoles-Jueves","Jueves-Viernes","Viernes-Sábado","Sábado-Domingo","Domingo-Lunes"]
    night = ''
    if hour_column >= 23:
        night=night_list[day_col]
    elif hour_column < 7:
        night=night_list[day_col-1]
    return night


def add_datetime_columns(df,logging, date_col):
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

    if df[date_col].dtype == 'datetime64[ns]':
        df['date'] = df[date_col].dt.date
        df['day'] = df[date_col].dt.day
        df['hour'] = df[date_col].dt.hour
        df['weekday'] = df[date_col].dt.weekday
        df['day_name'] = df[date_col].dt.day_name()
    else: logging.error(f"Failed to convert {date_col} to datetime in some rows.")
        

    logging.info(f"Columna temporal añadida correctamente")
    return df


def add_datetime_columns_pred(df,logging, date_col):

    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

    if df[date_col].dtype == 'datetime64[ns]':
        df['datetime'] = df[date_col].dt.date
        df['day'] = df[date_col].dt.day
        df['hour'] = df[date_col].dt.hour
        df['weekday'] = df[date_col].dt.weekday
        df['day_name'] = df[date_col].dt.day_name()
    else: logging.error(f"Failed to convert {date_col} to datetime in some rows.")
        
    logging.info(f"Columna temporal predicciones añadida correctamente")
    return df


def db_limit(hour_column,ld_limit,le_limit,ln_limit):
    limit = 0
    if hour_column >= 7 and hour_column < 19:
        limit = ld_limit
    elif hour_column >= 19 and hour_column < 23:
        limit = le_limit
    else:
        limit = ln_limit
    return limit


def categorize_time_of_day(hour):
    # hour = time_obj.hour
    if 7 <= hour < 19:
        return 'Ld'
    elif 19 <= hour < 23:
        return 'Le'
    else:
        return 'Ln'
    

def categorize_time_of_day_4(hour):
    if 7 <= hour < 11:
        return 'Ld_1'
    elif 11 <= hour < 15:
        return 'Ld_2'
    elif 15 <= hour < 19:
        return 'Ld_3'
    elif 19 <= hour < 23:
        return 'Le'
    elif 23 <= hour or hour < 3:
        return 'Ln_1'
    elif 3 <= hour < 7:
        return 'Ln_2'


def leq(levels):
    levels = levels[~np.isnan(levels)]
    l = np.array(levels)
    return 10*np.log10(np.mean(np.power(10,l/10)))


def get_day_levels(df,laeq_column):
    df['indicador_str'] = df.apply(lambda x: evaluation_period_str(x['hour']),axis=1)
    indicadores = df.groupby('indicador_str').agg({laeq_column:[leq]}).round(1)
    return indicadores
    

def get_day_levels_valencia(df,laeq_column):
    df['indicador_valencia'] = df.apply(lambda x: evaluation_period_str_valencia(x['hour']),axis=1)
    indicadores = df.groupby('indicador_valencia').agg({laeq_column:[leq]}).round(1)
    return indicadores




def remove_unnamed_columns(df_preds):
    
    df_preds = df_preds.loc[:, ~df_preds.columns.str.contains('^Unnamed')]
    df_preds = df_preds.drop(columns=['Brown_Level_1'])
    df_preds = df_preds.drop(columns=['index'])
    
    return df_preds


def yamnet_class_map_csv():
    
    home_dir = os.path.expanduser('~')
    cwd_dir = os.getcwd()
    cwd_dir = cwd_dir.replace("Visualization","")
    yammnet_class_map_path = os.path.join(cwd_dir, YAMNET_CLASS_MAP_FILE_NAME)
    df_audioset = pd.read_csv(yammnet_class_map_path,sep=';')
    #df_audioset = remove_unnamed_columns(df_audioset)
    
    return df_audioset


def taxonomy_json():
    home_dir = os.path.expanduser('~')
    cwd_dir = os.getcwd()
    cwd_dir = cwd_dir.replace("Visualization","")

    urban_taxonomy_map_path = os.path.join(cwd_dir, URBAN_TAXONOMY_FILE_NAME)
    urban_taxonomy_map = pd.read_json(urban_taxonomy_map_path, typ='series').to_dict()
    
    
    port_taxonomy_map_path = os.path.join(cwd_dir, PORT_TAXONOMY_FILE_NAME)
    port_taxonomy_map = pd.read_json(port_taxonomy_map_path, typ='series').to_dict()
    return urban_taxonomy_map, port_taxonomy_map

def align_spl_predictions_1s(df,df_pred,laeq_column,logger):

    if df is None or df.empty:
        logger.warning("SPL dataframe is empty")
        return pd.DataFrame()
    if df_pred is None or df_pred.empty:
        logger.warning("AI dataframe is empty")
        return pd.DataFrame()
    
    spl = df.copy()
    pred = df.copy()

    spl.index = pd.to_datetime(spl.index,errors="coerce").floor('s')
    pred.index = pd.to_datetime(pred.index,errors='coerce').floor('s')

    spl = spl[~spl.index.isna()]
    pred = pred[~pred.index.isna()]

    if 'class' not in pred.columns: 
        logger.warning(f"Prediction dataframe has no 'class' column")
        return pd.DataFrame()
    if "probability" not in pred.columns:
        logger.warning(
            "Prediction dataframe has no 'probability' column"
        )
        return pd.DataFrame()
    
    pred['class']=(pred['class'.astype("string").str.strip().replace("[]",pd.NA)])
    pred['probability'] = pd.to_numeric(pred['probability'],errors='coerce')

    start_date = max(spl.index.min(),pred.index.max())
    end_date = min(spl.index.max(),pred.index.max())

    logger.info(f"SPL range: {spl.index.min()} -> {spl.index.max()}")
    logger.info(f"AI range: {pred.index.min()} -> {pred.index.max()}")
    logger.info(f"Common range: {start_date} -> {end_date}")

    spl = spl.loc[start_date:end_date]
    pred = spl.loc[start_date:end_date]

    aligned = spl.merge(pred,how='inner',left_index=True,right_index=True,suffixes=('_x','_y'))
    required_columns = [laeq_column,'class','probability']

    aligned = aligned.dropna(subset=required_columns)
    logger.info(f"Aligned SPL/prediction rows: {len(aligned)}")

    if aligned.empty: logger.warning("SPL/prediction merge produced no valid rows")
    return aligned

def prediction_csv(path_input):
    df_prediction = pd.read_csv(path_input, parse_dates=['date'])
    columns_to_check = ["classes_custom", "probabilities_custom", "sum_probs_custom", "sum_probs_original"]
    
    for col in columns_to_check:
        if col in df_prediction.columns:
            df_prediction = df_prediction.drop(col, axis=1)
            
    # columns to rename
    columns_to_rename = ["classes_original", "probabilities_original"]
    new_columns = ["classes", "probabilities"]
    
    for i in range(len(columns_to_rename)):
        if columns_to_rename[i] in df_prediction.columns:
            df_prediction = df_prediction.rename(columns={columns_to_rename[i]: new_columns[i]})

    return df_prediction


def insert_dates(df):
    df["year"] = df.index.year
    df["month"] = df.index.month
    df["day"] = df.index.day
    df["hour"] = df.index.hour
    df["minute"] = df.index.minute
    df["second"] = df.index.second
    df["weekday"] = df.index.day_name()

    weekday_translation = {
        "Monday": " Lunes",
        "Tuesday": " Martes",
        "Wednesday": " Miércoles",
        "Thursday": " Jueves",
        "Friday": " Viernes",
        "Saturday": " Sábado",
        "Sunday": " Domingo"
    }
    df["weekday"] = df["weekday"].replace(weekday_translation)
    df["weekday"] = df["weekday"].astype(str)
    df["day"] = df["day"].astype(str).str.zfill(2)
    df["fullday"] = df["day"] + df["weekday"]
    return df


def remove_row_out_timespan(df_LAeq, df_Pred):
    df_LAeq.index = pd.to_datetime(df_LAeq.index)
    df_Pred['datetime'] = pd.to_datetime(df_Pred['datetime'])
    start_date = df_LAeq.index.min()
    end_date = df_LAeq.index.max()
    df_Pred_filtered = df_Pred[(df_Pred['datetime'] >= start_date) & (df_Pred['datetime'] <= end_date)]
    
    return df_Pred_filtered



def apply_db_correction(df, coefficient, logger):

    if 'LA' in df.columns:
        logger.info('Corrección --> LA')
        df['LA_corrected'] = df['LA'] - coefficient
        df['LAmax_corrected'] = df['LAmax'] - coefficient
        df['LAmin_corrected'] = df['LAmin'] - coefficient
    
    elif 'LC-LA' in df.columns:
        logger.info('Entering --> LC-LA')
        df['LC-LA_corrected'] = df['LC-LA'] - coefficient

    elif 'LAeq' in df.columns:
        logger.info('Corrección --> LAeq')
        df['LA_corrected'] = df['LAeq'] - coefficient
        df['LAmax_corrected'] = df['LAFmax'] - coefficient
        df['LAmin_corrected'] = df['LAFmin'] - coefficient
        # df['LC_corrected'] = df['LCeq'] - coefficient

    elif 'LAFeq' in df.columns:
        logger.info('Corrección --> LAeq')
        df['LA_corrected'] = df['LAFeq'] - coefficient
        df['LAmax_corrected'] = df['LAFmax'] - coefficient
        df['LAmin_corrected'] = df['LAFmin'] - coefficient

    elif 'Value' in df.columns:
        logger.info('Corrección --> Value')
        df['LA_corrected'] = df['Value'] - coefficient

    elif '' in df.columns:
        logger.info('Corrección --> ?')
        df['LA_corrected'] = df[''] - coefficient

    else:
        logger.error('No column found to apply the correction')


    return df



def change_date_and_time(df, new_date, new_time, new_threshold_date, new_threshold_time, logger):
    try:
        df = df.sort_values(by='datetime')
        ####################################################################################
        ####################################################################################
        # if new_date and new_time are provided
        if new_date is not None and new_time is not None:
            logger.info("new_date and new_time are provided")
            start_datetime = pd.Timestamp(f"{new_date} {new_time}")
            df['datetime'] = [start_datetime + pd.Timedelta(seconds=i) for i in range(len(df))]
            logger.info(f"New datetime column created with new date and time: {start_datetime}")
        

        # new_date is provided but new_time is None
        elif new_date is not None and new_time is None:
            logger.info("new_date is provided but new_time is None")
            # get the first item in 'datetime' column
            first_time = df.iloc[0]['datetime'] 
            logger.info(f"First time in 'datetime' column: {first_time}")

            # string if necessary
            if not isinstance(first_time, str):
                first_time = first_time.strftime("%H:%M:%S")
            logger.info(f"First time in 'datetime' column: {first_time}")
            
            start_datetime = pd.Timestamp(f"{new_date} {first_time}")
            df['datetime'] = [start_datetime + pd.Timedelta(seconds=i) for i in range(len(df))]
            logger.info(f"New datetime column created with new date: {start_datetime}")


        # new_time is provided but new_date is None
        elif new_time is not None and new_date is None:
            logger.info("new_time is provided but new_date is None")
            # get the first item in 'datetime' column
            first_date = df.iloc[0]['datetime']
            logger.info(f"First date in 'datetime' column: {first_date}")

            #  string if necessary
            if not isinstance(first_date, str):
                first_date = first_date.strftime("%Y-%m-%d")
            logger.info(f"First date in 'datetime' column: {first_date}")

            start_datetime = pd.Timestamp(f"{first_date} {new_time}")
            df['datetime'] = [start_datetime + pd.Timedelta(seconds=i) for i in range(len(df))]


        else:
            logger.info("No new date or time provided.")



        
        ####################################################################################
        ## If there is a limit threshold date or time, trim the df with this information ##
        ####################################################################################
        if new_threshold_date is not None and new_threshold_time is not None:
            logger.info("[0] new_threshold_date and new_threshold_time are provided")

            threshold_datetime = pd.Timestamp(f"{new_threshold_date} {new_threshold_time}")
            df = df[df['datetime'] <= threshold_datetime]

            logger.info(f"Trimming the dataframe with threshold date: {threshold_datetime}")
            

        elif new_threshold_date is not None and new_threshold_time is None:
            logger.info("[1] new_threshold_date is provided but new_threshold_time is None")

            thr_first_time = df.iloc[0]['datetime']
            logger.info(f"First time in 'datetime' column: {thr_first_time}")
            
            if not isinstance(thr_first_time, str):
                thr_first_time = thr_first_time.strftime("%H:%M:%S")
            logger.info(f"First time in 'datetime' column: {thr_first_time}")

            threshold_datetime = pd.Timestamp(f"{new_threshold_date} {thr_first_time}")
            df = df[df['datetime'] <= threshold_datetime]
            logger.info(f"Trimming the dataframe with threshold date: {threshold_datetime}")


        elif new_threshold_date is None and new_threshold_time is not None:
            logger.info("[2] new_threshold_time is provided but new_threshold_date is None")

            thr_first_date = df.iloc[0]['datetime']
            logger.info(f"First date in 'datetime' column: {thr_first_date}")

            if not isinstance(thr_first_date, str):
                thr_first_date = thr_first_date.strftime("%Y-%m-%d")
            logger.info(f"First date in 'datetime' column: {thr_first_date}")

            threshold_datetime = pd.Timestamp(f"{thr_first_date} {new_threshold_time}")
            df = df[df['datetime'] <= threshold_datetime]
            logger.info(f"Trimming the dataframe with threshold date: {threshold_datetime}")



        else:
            logger.info("No threshold limit date or time provided.")


    except Exception as e:
        logger.error(f"Error: {e}")
        return None
    return df



def list_git_tags():
    try:
        tags = tags = subprocess.check_output(["git", "tag"]).strip().decode()
        return tags.split('\n')
    except subprocess.CalledProcessError:
        return None


def select_tag(tags, logger):
    for i, tag in enumerate(tags):
        logger.info(f"{i}: {tag}")
    
    choice = int(input("Select the tag to use: "))
    tag_selected = tags[choice]
    tag_selected = tag_selected.replace(".", "_")
    return tag_selected


def get_stable_version(logger):
    tags = list_git_tags()
    # get the latest stable version
    tag_selected = tags[-1]
    logger.info(f"Latest stable version: {tag_selected}")
    
    tag_selected = tag_selected.replace(".", "_")
    logger.info(f"Latest stable version string: {tag_selected}")
    return tag_selected


def trim_dataframe(dataframe,start_timestamp,end_timestamp,requested_start_seconds,requested_end_seconds,logger,dataframe_name="Dataframe",max_trim_fraction=0.10):

    if dataframe is None: return None
    if dataframe.empty:
        logger.warning(f"{dataframe_name} is empty before trimming")
        return dataframe.copy()
    
    duration_seconds                = ( end_timestamp - start_timestamp).total_seconds()

    if duration_seconds <= 0:
        logger.warning(f"{dataframe_name} tiene duracion invalida de: {duration_seconds} degundos. Se utilizará la tabla completa ...")
        return dataframe.copy()

    max_trim_seconds                = duration_seconds * max_trim_fraction
    actual_start_trim               = min(max(0,requested_start_seconds),max_trim_seconds)
    actual_end_trim                 = min(max(0,requested_end_seconds),max_trim_seconds)
    trim_start                      = start_timestamp + pd.Timedelta(actual_start_trim,unit="seconds")
    trim_end                        = end_timestamp - pd.Timedelta(actual_end_trim,unit="seconds")
    
    if trim_start >= trim_end:
        logger.warning(f"{dataframe_name} rango de recorte es inválido. Se utilizará la tabla completa ...")
        return dataframe.copy()
    
    trimmed_dataframe               = dataframe.loc[trim_start:trim_end].copy()

    if trimmed_dataframe.empty:
        logger.warning(f"{dataframe_name} está vacío despues de recortar. Esto puede indicar que el indice del dataframe es incorrecto. Se utilizará la tabla completa ...")
        return dataframe.copy()
    
    return trimmed_dataframe

def normalize_path(path):
    return os.path.normcase(os.path.normpath(path))

def safe_plot(function: Callable) -> Callable:
    """
    Decorador para todas las funciones de gráficas.

    - Registra omisiones esperadas como warning.
    - Registra errores inesperados con traceback completo.
    - Cierra figuras de Matplotlib aunque haya error.
    """

    signature = inspect.signature(function)

    @wraps(function)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        bound = signature.bind_partial(*args, **kwargs)
        logger = bound.arguments.get("logger")
        plotname = bound.arguments.get("plotname",function.__name__)

        if logger is None: logger = logging.getLogger(function.__module__)

        try: return function(*args, **kwargs)
        except SkipPlot as exc: 
            logger.warning("%s: %s", plotname, exc)
            return None
        except Exception:
            logger.exception(f"Error inesperado en {function.__name__} para {plotname}")
            return None
        finally:
            plt.close('all')

    return wrapper

@dataclass
class PlotContext:
    """
    Configuración y operaciones comunes de una gráfica.
    """

    output_dir: Path
    plotname: str
    logger: Any
    agg_period_seconds: int = 900

    def __post_init__(self) -> None:
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(parents=True,exist_ok=True)

        if not isinstance(self.agg_period_seconds, int): raise TypeError("agg_period_seconds debe ser un entero")
        if self.agg_period_seconds <= 0: raise ValueError("agg_period_seconds debe ser mayor que cero")

    @property
    def resample_rule(self) -> str: return "{}s".format(self.agg_period_seconds)

    @property
    def period_label(self) -> str:
        seconds = self.agg_period_seconds

        if seconds % 3600 == 0:
            hours = seconds / 3600
            return "{:g} h".format(hours)
        
        if seconds & 60 == 0:
            minutes = seconds / 60
            return "{:g} min".format(minutes)
        
    def path(self, suffix: str, extension:str) -> Path:
        clean_extension = extension.lstrip(".")
        return self.output_dir / "{}_{}.{}".format(self.plotname,suffix,clean_extension)
    
    def require(self,condition:bool, message:str) -> None:

        if not condition: raise SkipPlot(message)

    def require_dataframe(self, dataframe: Optional[pd.DataFrame], name: str, required_columns: Sequence[str]= (), min_rows: int = 1, datetime_index: bool = False) -> None:
        validate_dataframe(dataframe,name,required_columns,min_rows,datetime_index)
    
    def save_dataframe(self,dataframe: pd.DataFrame,suffix:str,index:bool =True) -> Path:
        path = self.path(suffix,'csv')
        dataframe.to_csv(path,index=index)
        self.logger.info("CSV guardado en %s",path)
        return path
    
    def save_matplotlib(self, figure: Any, suffix: str, dpi: int = 150, bbox_inches: Optional[str]="tight") -> Path:
        path = self.path(suffix,"png")
        figure.savefig(path,dpi=dpi,bbox_inches=bbox_inches)
        plt.close(figure)
        self.logger.info("Imagen guardada en %s",path)
        return path

    def save_plotly(self, figure:Any, suffix: str) -> Path:
        path = self.path(suffix,"html")
        figure.write_html(str(path))
        self.logger.info("HTML guardado en %s",path)
        return path

def validate_dataframe(dataframe: Optional[pd.DataFrame], name: str, required_columns: Sequence[str] = (), min_rows: int = 1, datetime_index: bool = False) -> None:

    missing = sorted(set(required_columns) - set(dataframe.columns))

    if dataframe is None: raise SkipPlot("{} es None".format(name))
    if not isinstance(dataframe,pd.DataFrame): raise TypeError("{} debe ser pd.DataFrame, no {}".format(name,type(dataframe).__name__))
    if dataframe.empty: raise SkipPlot("{} está vacío".format(name))

    

    if missing: raise SkipPlot("{} no contiene las columnas: {}".format(name,missing))
    if len(dataframe) < min_rows: raise SkipPlot("{} tiene {} filas; se requiren al menos {}".format(name,len(dataframe),min_rows))
    if datetime_index and not isinstance(dataframe.index,pd.DatetimeIndex): raise SkipPlot("{} necesita un DatetimeIndex".format(name))

def prepare_dataframe(dataframe: pd.DataFrame, name: str,min_rows: int = 1,deduplicate_index: bool = False, required_columns: Sequence[str] = (),numeric_columns: Sequence[str] = (),dropna_columns: Sequence[str] = (), datetime_column: Optional[str] = None, set_datetime_index: bool = False) -> pd.DataFrame:

    """
    Copia valida y normaliza un dataframe. Nunca modifica el objeto recibido.
    """

    validate_dataframe(
        dataframe           = dataframe,
        name                = name,
        required_columns    = required_columns,
        min_rows            = min_rows)

    prepared = dataframe.copy()

    if datetime_column is not None:
        if datetime_column not in prepared.columns: raise SkipPlot("{} no contiene la fecha {}".format(name,datetime_column))

        prepared[datetime_column] = pd.to_datetime(prepared[datetime_column],errors='coerce')
        prepared = prepared.dropna(subset=[datetime_column])

        if set_datetime_index: prepared = prepared.set_index(datetime_column,drop=False)
    
    elif set_datetime_index:
        try: prepared.index = pd.to_datetime(prepared.index, errors='coerce')
        except Exception as exc: raise SkipPlot("No se pudo convertir el índice de {} a fecha: {}".format(name,exc))

        prepared = prepared[~prepared.index.isna()]

    for column in numeric_columns: 
        if column not in prepared.columns: raise SkipPlot("{} no contiene la columna numérica {}".format(name,column))

        prepared[column] = pd.to_numeric(prepared[column],errors='coerce')

    
    valid_dropna_columns = [column for column in dropna_columns if column in prepared.columns]

    if valid_dropna_columns: prepared = prepared.dropna(subset=valid_dropna_columns)

    if isinstance(prepared.index, pd.DatetimeIndex):
        prepared = prepared.sort_index()

        if deduplicate_index: prepared = prepared[~prepared.index.duplicated(keep='first')]
        if prepared.empty: raise SkipPlot("{} quedó vacío después de normalizar".format(name))

        return prepared

def estimate_sampling_period(dataframe_or_index: Any) -> Optional[pd.Timedelta]:
    """
    Calcula la cadencia mediana
    """

    if isinstance(dataframe_or_index,pd.DataFrame): index = dataframe_or_index.index
    else: index = dataframe_or_index

    if not isinstance(index, pd.DatetimeIndex): index = pd.to_datetime(index,erros='coerce')

    index = pd.DatetimeIndex(index).dropna().sort_values().unique()

    if len(index) < 2: return None

    differences  = (pd.Series(index).diff().dropna())
    differences  = differences[differences > pd.Timedelta(0)]

    if differences.empty: return None

    return differences.median()

def mode_or_na(series: pd.Series) -> Any:
    """
    Moda segura para columnas categóricas
    """

    clean = series.dropna()

    if clean.empty: return pd.NA

    mode = clean.mode()

    if mode.empty: return clean.iloc[0]

    return mode.iloc[0]

def _cell_to_list(value: Any) -> List[Any]:

    """
    Convierte valores escalares o listas serializadas a una lista real.
    Admite:
        - "Silence"
        - 0.91
        - ["Speech", "Dog"]
        - "['Speech', 'Dog']"
        - "[]" y valores vacíos
    """

    if value is None: return []

    if isinstance(value,(list,tuple,np.ndarray,pd.Series)): return list(value)
    
    if isinstance(value, str): 
        stripped = value.strip()

        if stripped in {"", "[]", "None","none","nan","NaN"}: return []

        if stripped.startswith("[") and stripped.endswith("]"):

            try: parsed = ast.literal_eval(stripped)
            except (ValueError,SyntaxError): return [stripped]

            if isinstance(parsed, (list,tuple)): return list(parsed)

            return [parsed]
        
        return [stripped]
    
    try: 
        if pd.isna(value): return []
    except (TypeError,ValueError): pass

    return [value]

def normalize_predictions(dataframe: pd.DataFrame,logger: Any, date_column: str = 'date',class_column: str = 'class',probability_column: str = 'probability'
                          ) -> pd.DataFrame:
    """
    Devuelve una fila por predicción, con:
    - índice datetime
    - class como texto escalar
    - probability como float

    Funciona tanto si class/probability son escalares como listas.
    """

    predictions = prepare_dataframe(
        dataframe               = dataframe,
        name                    = "Prediction dataframe",
        required_columns        = [date_column,class_column,probability_column],
        datetime_column         = date_column,
        set_datetime_index      = True,
        min_rows                = 1
    )
   
    predictions['_classes'] = predictions[class_column].apply(_cell_to_list)
    predictions['_probabilities'] = predictions[probability_column].apply(_cell_to_list)

    def build_pairs(row: pd.Series) -> List[Tuple[Any,Any]]:

        classes = row['_classes']
        probabilities = row["_probabilities"]

        if not classes: return []
        if len(probabilities) == 1 and len(classes) > 1: probabilities = probabilities * len(classes)
        if len(classes) != len(probabilities):
            logger.warning("Se descartauna fila de predicciones:" "%s de clases y %s probabilidades en %s",len(classes),len(probabilities),row.name)
            return []
        return list(zip(classes,probabilities))

    predictions['_class_probability'] = predictions.apply(build_pairs,axis=1)

    predictions = predictions.explode("_class_probability")
    predictions = predictions.dropna(subset=['_class_probability'])

    if predictions.empty: raise SkipPlot("No quedan predicciones después de expandir clases")

    predictions[class_column] = predictions["_class_probability"].apply(lambda value: value[0])

    predictions[probability_column] = predictions['_class_probability'].apply(lambda value: value[1])

    predictions[class_column] = (predictions[class_column].astype('string').str.strip().replace({
        "":pd.NA,
        "[]":pd.NA,
        "None":pd.NA,
        "nan":pd.NA
    }))

    predictions[probability_column] = pd.to_numeric(predictions[probability_column],errors='coerce')

    predictions = predictions.dropna(subset=[class_column,probability_column])
    predictions = predictions.drop(columns=["_classes","_probabilities","_class_probability"])

    if predictions.empty: raise SkipPlot("No quedan clases y probabilidades válidas")

    cadence = estimate_sampling_period(predictions.index)
    logger.info("Predicciones normalizadas: %s filas; cadencia mediana: %s",len(predictions),cadence)
    logger.info("Tipo de probability tras normalización: %s",predictions[probability_column].dtype)
    logger.info("Ejemplo probability: %s",predictions[probability_column].head().tolist())
    
    return predictions.sort_index()


def map_taxonomy(predictions: pd.DataFrame, taxonomy_map: Mapping[str,str], logger: Any, class_column: str = 'class', output_column: str = 'mapped_class') -> pd.DataFrame:

    validate_dataframe(dataframe=predictions,name='Prediction dataframe',required_columns=[class_column])
    if not isinstance(taxonomy_map, Mapping): raise TypeError("taxonomy_map debe ser un diccionario o mapping")

    mapped = predictions.copy()
    mapped[output_column] = mapped[class_column].map(taxonomy_map)

    unmapped = (mapped.loc[mapped[output_column].isna(),class_column])

    if not unmapped.empty: logger.warning("%s detecciones no están en taxonomy_map. " "Ejemplos: %s", int(unmapped.sum()),unmapped.head(10).to_dict())

    mapped = mapped.dropna(subset=[output_column])

    if mapped.empty: raise SkipPlot("Ninguna clase se pudo mapear a la taxonomía")

    logger.info("Predicciones mapeadas a taxonomía:  %s de %s",len(mapped),len(predictions))
    return mapped

def add_datetime_features(dataframe: pd.DataFrame) -> pd.DataFrame:

    if not isinstance(dataframe.index, pd.DatetimeIndex):
        raise SkipPlot("add_datetime_features necesita DatetimeIndex")
    
    result = dataframe.copy()
    index = result.index

    result["year"] = index.year
    result["month"] = index.month
    result["day"] = index.day
    result["hour"] = index.hour
    result["minute"] = index.minute
    result["second"] = index.second
    result["date"] = index.date
    result["weekday"] = index.day_name()

    translations = {
        "Monday": "Lunes",
        "Tuesday": "Martes",
        "Wednesday": "Miércoles",
        "Thursday": "Jueves",
        "Friday": "Viernes",
        "Saturday": "Sábado",
        "Sunday": "Domingo",
    }

    result["weekday_es"] = result["weekday"].map( translations ).fillna(result["weekday"])
    result["date_day"] = ( index.strftime("%Y-%m-%d") + " " + result["weekday_es"].astype(str))

    return result



def align_spl_predictions(spl_dataframe: pd.DataFrame, prediction_dataframe: pd.DataFrame, laeq_column: str, logger: Any, spl_date_column: str = 'datetime', prediction_date_column: str = 'date',tolerance: str = '1s') -> pd.DataFrame:
    
    """
    Alinea SPL y predicciones por timestamp con merge_asof.

    No desplaza automáticamente horas. La corrección de zona horaria
    debe aplicarse a ambos DataFrames antes de llamar a esta función.
    """
    spl = prepare_dataframe(        
        dataframe                   = spl_dataframe,
        name                        = 'SPL dataframe',
        required_columns            = [laeq_column],
        datetime_column             = (spl_date_column if spl_date_column in spl_dataframe.columns else None),
        set_datetime_index          = True,
        numeric_columns             = [laeq_column],
        dropna_columns              = [laeq_column],
        deduplicate_index           = True)

    

    predictions = normalize_predictions(
        dataframe                   = prediction_dataframe,
        logger                      = logger,
        date_column                 = prediction_date_column
    )

    spl_start = spl.index.min()
    spl_end = spl.index.max()
    pred_start = predictions.index.min()
    pred_end = predictions.index.max()

    logger.info("Rango SPL : %s -> %s", spl_start, spl_end)
    logger.info("Rango predicciones : %s -> %s", pred_start,pred_end)

    common_start = max(spl_start,pred_start)
    common_end = min(spl_end,pred_end)

    if common_start > common_end: raise SkipPlot("SPL y predicciones no tienen solapamiento espectral")

    spl = spl.loc[common_start:common_end].copy()
    predictions = predictions.loc[common_start:common_end].copy()

    if spl.empty or predictions.empty: raise SkipPlot("No quedan datos en el intervalo temporal común")

    spl_index_name = "__spl_timestmap"
    pred_index_name = "__prediction_timestamp"

    spl_reset = spl.rename_axis(spl_index_name).reset_index().sort_values(by=spl_index_name)
    pred_reset = predictions.rename_axis(pred_index_name).reset_index().sort_values(by=pred_index_name)

    spl_reset = spl_reset.sort_values(spl_index_name)
    pred_reset = pred_reset.sort_values(pred_index_name)

    aligned = pd.merge_asof(
        spl_reset,
        pred_reset,
        left_on = spl_index_name,
        right_on = pred_index_name,
        direction='nearest',
        tolerance=pd.Timedelta(tolerance),
        suffixes=('_spl','_pred')
    )

    aligned = aligned.dropna(subset = [laeq_column,'class','probability'])

    if aligned.empty: raise SkipPlot("La alineación SPL/predicciones no produjo filas")

    aligned = aligned.set_index(spl_index_name)
    aligned.index.name = 'datetime'

    logger.info("Filas SPL/predicciones alineadas: %s", len(aligned))

    return aligned.sort_index()


def dominant_category_per_bin(dataframe: pd.DataFrame, category_column: str, rule: str, weight_column: Optional[str] = None) -> pd.DataFrame:
    """
    Obtiene la categoría dominante en cada intervalo.

    No usa "first" ni medias de códigos categóricos.
    """  

    validate_dataframe(
        dataframe = dataframe,
        name = "Categorical dataframe",
        required_columns = [category_column],
        datetime_index = True
    )

    data = dataframe.dropna(subset=[category_column]).copy()

    if data.empty: raise SkipPlot("No hay categorías válidas para agregar")

    data['time_bin'] = data.index.floor(rule)

    if weight_column is None: counts = (data.groupby(['time_bin',category_column],observed=True)).size().reset_index(name='weight')
    else:
        if weight_column not in data.columns:
            raise SkipPlot("No existe la columna de peso {}".format(weight_column))
            
        counts = (data.groupby(['time_bin',category_column],observed=True)[weight_column].sum().reset_index(name='weight'))
    
    if counts.empty: raise SkipPlot("No hay datos después de agrupar categorías")

    dominant_rows = (counts.groupby('time_bin')["weight"]).idxmax()
    dominant = counts.loc[dominant_rows].copy()
    
    totals = (counts.groupby('time_bin')["weight"]).sum().rename("total_weight")
    
    dominant = dominant.join(totals,on='time_bin')
    dominant['dominance_share'] = (dominant['weight'] / dominant['total_weight'])

    dominant = dominant.set_index('time_bin')
    dominant.index.name = 'datetime'

    return dominant.sort_index()


def energy_mean(values: Iterable[float]) -> float:
    """Promedio energético robusto para niveles en dB."""

    numeric = pd.to_numeric(pd.Series(values),errors='coerce').dropna()

    if numeric.empty: return float('nan')

    array = numeric.to_numpy(dtype=float)

    return float(10.0 * np.log10(np.mean(np.power(10.0, array / 10.0))))

def aggregate_spl(
        dataframe: pd.DataFrame,
        rule: str,
        laeq_column: str,
        max_column: Optional[str] = None,
        min_column: Optional[str] = None) -> pd.DataFrame:
    
    """Agregación acústica coherente por intervalo."""

    required = [laeq_column]

    if max_column: required.append(max_column)
    if min_column: required.append(min_column)

    validate_dataframe(
        dataframe           = dataframe,
        name                = 'SPL dataframe',
        required_columns    = required,
        datetime_index      = True
    )

    aggregations: Dict[str, Any] = {laeq_column: energy_mean}

    if max_column: aggregations[max_column] = 'max'
    if min_column: aggregations[min_column] = 'min'

    aggregated = dataframe.resample(rule).agg(aggregations)
    aggregated = aggregated.dropna(how='all')

    if aggregated.empty: raise SkipPlot("La agregación SPL no produjo datos.")

    return aggregated


def find_frequency_columns(
    dataframe: pd.DataFrame,
) -> List[str]:
    """
    Detecta columnas de frecuencia por nombre.

    Ejemplos admitidos:
        20Hz, 31.5Hz, 1kHz, 1.25kHz, 1000Hz
    """
    import re

    pattern = re.compile(r"^\d+(?:\.\d+)?(?:k)?Hz$",re.IGNORECASE,)

    columns = [str(column) for column in dataframe.columns if pattern.fullmatch(str(column).strip())]

    if not columns: raise SkipPlot( "El DataFrame no contiene columnas de bandas de frecuencia")

    return columns


def frequency_to_hz(column_name: str) -> float:
    """Convierte 31.5Hz o 1.25kHz a un valor numérico en Hz."""

    text = str(column_name).strip().lower()

    if not text.endswith("hz"): raise ValueError( "{} no es una frecuencia válida".format( column_name ) )
        
    value = text[:-2]

    if value.endswith("k"): return float(value[:-1]) * 1000.0
        
    return float(value)

def prepare_spectrogram_data( dataframe: pd.DataFrame, logger: Any, datetime_column: Optional[str] = None ) -> Tuple[pd.DataFrame, List[str], np.ndarray]:
    
    """
    Prepara un DataFrame para el espectrograma y devuelve:
        datos, nombres de bandas, frecuencias numéricas.
    """

    data = prepare_dataframe(
        dataframe           = dataframe,
        name                = "Spectrogram dataframe",
        datetime_column     = datetime_column,
        set_datetime_index  = True,
    )

    frequency_columns = find_frequency_columns(data)

    for column in frequency_columns: data[column] = pd.to_numeric( data[column], errors="coerce")
        
    data = data.dropna( subset=frequency_columns, how="all")


    if data.empty: raise SkipPlot( "No quedan valores válidos en las bandas de frecuencia" )
        
    frequencies = np.array([frequency_to_hz(column)for column in frequency_columns],dtype=float)
    order = np.argsort(frequencies)
    frequencies = frequencies[order]
    frequency_columns = [ frequency_columns[index] for index in order ]
        
    logger.info( "Bandas detectadas: %s", frequency_columns)
        
    return data, frequency_columns, frequencies


def select_night_data( dataframe: pd.DataFrame, complete_night: bool = False, start_hour: int = 23, end_hour: int = 7) -> pd.DataFrame:
    
    """
    Selecciona datos nocturnos.

    complete_night=False:
        Devuelve cualquier fragmento disponible entre 23:00 y 07:00.

    complete_night=True:
        Solo conserva noches que contienen datos antes y después de
        medianoche. Es apropiado para gráficas de noche completa.
    """

    validate_dataframe(
        dataframe       = dataframe,
        name            = "Night dataframe",
        datetime_index  = True,
    )

    data = dataframe.copy()
    mask = ((data.index.hour >= start_hour) | (data.index.hour < end_hour))

    data = data.loc[mask]

    if data.empty: raise SkipPlot("No existen datos dentro del periodo nocturno")

    # La fecha de noche es el día en que comienza el periodo a las 23:00.
    night_date = pd.Series( data.index.normalize(), index=data.index,)

    after_midnight = data.index.hour < end_hour
    night_date.loc[after_midnight] = ( night_date.loc[after_midnight ]- pd.Timedelta(days=1) )
    data["night_date"] = night_date.dt.date

    if not complete_night: return data
        

    valid_nights: List[Any] = []

    for current_night, group in data.groupby("night_date"):

        has_before_midnight = ( group.index.hour >= start_hour ).any()
        has_after_midnight = ( group.index.hour < end_hour ).any()
            
        if has_before_midnight and has_after_midnight: valid_nights.append(current_night)
            
    data = data[ data["night_date"].isin(valid_nights)]

    if data.empty: raise SkipPlot( "No hay ninguna noche completa que cruce medianoche")

    return data







