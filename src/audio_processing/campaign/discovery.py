"""
#-------------------------------------------------------------------------------------------------------------------------------------------------------#
Modulo discovery encargado de:

input_root
    ├── buscar puntos de medida
    ├── detectar AUDIOMOTH
    ├── detectar SONOMETRO
    ├── detectar CESVA u otros formatos
    └── devolver MeasurementPoint[]


#-------------------------------------------------------------------------------------------------------------------------------------------------------#

"""

from pathlib import Path
from audio_processing.campaign.models import MeasurementPoint

def _build_source_id(point_name: str, device_type: str) -> str:
    normalized_point = (
        point_name
        .strip()
        .replace(" ", "_")
        .replace("/", "_")
    )

    return f"{normalized_point}__{device_type}"

def discover_measurement_points(config) -> list[MeasurementPoint]:

    points: list[MeasurementPoint] = []

    input_root = Path(config.campaign.input_root)
    output_root = Path(config.campaign.output_root)

    filter_point = getattr(config.discovery,"filter_point",None)

    if not input_root.exists(): raise FileNotFoundError(f"No existe input_root {input_root}")
        
    filter_point = getattr(config.discovery, "filter_point", None)
    filter_device = getattr(config.discovery, "filter_device", None)

    for point_root in sorted(input_root.iterdir()):

        if filter_point and point_root.name != filter_point: continue
        
        if not point_root.is_dir(): continue
        

        audiomoth_cfg = config.devices.audiomoth
        sonometer_cfg = config.devices.sonometer

        audiomoth_path = point_root / config.devices.audiomoth.folder_name
        sonometer_path = point_root / config.devices.sonometer.folder_name

        if audiomoth_cfg.enabled and audiomoth_path.exists():
            if filter_device and filter_device != "audiomoth": continue
            points.append(
                MeasurementPoint(
                    name                    = point_root.name,
                    source_id               = _build_source_id(point_root.name,"audiomoth"),
                    root_path               = point_root,
                    device_type             = "audiomoth",
                    raw_data_path           = audiomoth_path,
                    output_path             = Path(config.campaign.output_root) / point_root.name,
                    needs_spl               = audiomoth_cfg.needs_spl,
                    needs_ai                = audiomoth_cfg.needs_ai,
                    needs_visualization     = audiomoth_cfg.visualize
                )
            )
        if sonometer_cfg.enabled and sonometer_path.exists():
            if filter_device and filter_device != "sonometer": continue
            points.append(
                MeasurementPoint(
                    name                    = point_root.name,
                    source_id               = _build_source_id(point_root.name,"sonometer"),
                    root_path               = point_root,
                    device_type             = "sonometer",
                    raw_data_path           = sonometer_path,
                    output_path             = Path(config.campaign.output_root) / point_root.name,
                    needs_spl               = sonometer_cfg.needs_spl,
                    needs_ai                = sonometer_cfg.needs_ai,
                    needs_visualization     = sonometer_cfg.visualize
                )
            )

    return points