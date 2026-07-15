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

    points = []

    input_root = Path(config.campaign.input_root)

    for point_root in input_root.iterdir():

        if not point_root.is_dir(): continue

        audiomoth_path = point_root / config.devices.audiomoth.folder_name
        sonometer_path = point_root / config.devices.sonometer.folder_name

        if audiomoth_path.exists():

            points.append(
                MeasurementPoint(
                    name                    = point_root.name,
                    root_path               = point_root,
                    device_type             = "audiomoth",
                    raw_data_path           = audiomoth_path,
                    output_path             = Path(config.campaign.output_root) / point_root.name,
                    needs_spl               = config.devices.audiomoth.needs_spl,
                    needs_ai                = config.devices.audiomoth.needs_ai,
                    needs_visualization     = config.devices.audiomoth.visualize
                )
            )
        if sonometer_path.exists():

            points.append(
                MeasurementPoint(
                    name                    = point_root.name,
                    root_path               = point_root,
                    device_type             = "sonometer",
                    raw_data_path           = sonometer_path,
                    output_path             = Path(config.campaign.output_root) / point_root.name,
                    needs_spl               = config.devices.sonometer.needs_spl,
                    needs_ai                = config.devices.sonometer.needs_ai,
                    needs_visualization     = config.devices.sonometer.visualize
                )
            )

    return points