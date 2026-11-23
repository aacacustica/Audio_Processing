from dataclasses import dataclass
from pathlib import Path

from audio_processing.campaign.models import MeasurementSource

@dataclass(frozen=True,slots=True)
class ManualInputFiles:
    measurements: tuple[Path, ...]
    predictions: tuple[Path, ...]

def discover_manual_input_files(source: MeasurementSource, config) -> ManualInputFiles: 
    measurement_dir = Path(source.raw_data_path)

    if not measurement_dir.is_dir(): raise FileNotFoundError(f"No existe la carpeta de entrada manual: {measurement_dir}")

    if source.device_type == 'audiomoth': measurement_extensions = {".csv"}
    elif source.device_type == 'sonnometer': measurement_extensions = {".csv",".xlsx"}
    else: raise ValueError(f"Dispositivo manual no soportado: {source.device_type}")

    measurements = tuple(sorted(path for path in measurement_dir.rglob("*") if path.is_file() and path.suffix.lower() in measurement_extensions))

    if not measurements: raise FileNotFoundError(f"No se encontraron archivos de medida en {measurement_dir}")

    ai_outputs = config.outputs.subfolders.ai
    predictions_dir = (Path(source.output_path) / ai_outputs.general_folder_name / ai_outputs.predictions_folder_name)

    predictions = (tuple(sorted(predictions_dir.glob("*.csv"))) if predictions_dir.is_dir() else ())

    return ManualInputFiles(measurements=measurements,predictions=predictions)

def discover_manual_input_files(source: MeasurementSource, config) -> ManualInputFiles:

    measurement_dir = Path(source.raw_data_path)

    if not measurement_dir.is_dir(): raise FileNotFoundError(f"No existe la carpeta de entrada: {measurement_dir}")

    if source.device_type == 'audiomoth': measurement_extensions = {".csv"}
    elif source.device_type == 'sonometer': measurement_extensions = {".csv",".xlsx"}
    else: raise ValueError(f"Dispositivo manual no soportado: {source.device_type}")

    measurements = tuple(sorted(path for path in measurement_dir.rglob("*") if path.is_file() and path.suffix.lower() in measurement_extensions))

    if not measurements: raise FileNotFoundError(f"No se encontraron archivos de medida en: {measurement_dir}")

    ai_outputs = config.outputs.subfolders.ai
    predictions_dir = (Path(source.output_path) / ai_outputs.general_folder_name / ai_outputs.predictions_folder_name)
    predictions = (tuple(sorted(predictions_dir.glob("*.csv")))) if predictions_dir.is_dir() else ()

    return ManualInputFiles(measurements=measurements,predictions=predictions)
