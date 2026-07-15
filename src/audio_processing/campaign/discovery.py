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

def discover_measurement_points(config) -> list[MeasurementPoint]:

    points: list[MeasurementPoint] = []

    input_root = Path(config.campaign.input_root)
    output_root = Path(config.campaign.output_root)

    filter_point = getattr(config.discovery,"filter_point",None)

    if not input_root.exists(): raise FileNotFoundError(f"No existe input_root {input_root}")
        

    for point_root in sorted(input_root.iterdir()):

        if not point_root.is_dir(): continue
        if filter_point and point_root.name != filter_point: continue

        audiomoth_cfg = config.devices.audiomoth
        sonometer_cfg = config.devices.sonometer

        audiomoth_path = point_root / config.devices.audiomoth.folder_name
        sonometer_path = point_root / config.devices.sonometer.folder_name

        if audiomoth_cfg.enabled and audiomoth_path.exists():

            points.append(
                MeasurementPoint(
                    name                    = point_root.name,
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

            points.append(
                MeasurementPoint(
                    name                    = point_root.name,
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