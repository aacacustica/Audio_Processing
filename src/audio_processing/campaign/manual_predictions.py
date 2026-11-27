import ast
from pathlib import Path

import pandas as pd 

_COLUMNS_TO_DROP = ("classes_custom","probabilities_custom","sum_probs_custom","sum_probs_original")
_COLUMNS_RENAMES = {"classes_original":"classes","probabilities_original":"probabilities"}

def _parse_serialized_value(value):

    if not isinstance(value,str): return value

    try:
        return ast.literal_eval(value)
    except (SyntaxError, ValueError) as exc: raise ValueError(f"No se puede interpretar el valor de predicción: {value!r}") from exc

def read_manual_predictions(path: str | Path) -> pd.DataFrame:

    path = Path(path)

    if not path.is_file(): raise FileNotFoundError(f"No existe el CSV de predicciones: {path}")
    dataframe = pd.read_csv(path)