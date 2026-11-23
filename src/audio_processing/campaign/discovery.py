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
from audio_processing.campaign.models import MeasurementSource

def _build_source_id(point_name: str, device_type: str) -> str:
    normalized_point = (
        point_name
        .strip()
        .replace(" ", "_")
        .replace("/", "_")
    )

    return f"{normalized_point}__{device_type}"

def _find_existing_folder(point_root: Path, folder_name: str) -> Path | None:
    
    
    candidate = point_root / folder_name
    if candidate.exists() and candidate.is_dir(): return candidate
    return None

def _device_allowed(filter_device: str | None, device_type: str) -> bool:
    return filter_device is None or filter_device == device_type


def _iter_manual_campaign_roots(config):

    input_root = Path(config.campaign.input_root)
    measures_name = config.outputs.subfolders.general.medidas_folder_name
    results_name = config.outputs.subfolders.general.resultados_folder_name

    if input_root.name == measures_name:
        yield(config.campaign.name,input_root,Path(config.campaign.output_root))
        return

    for campaign_dir in sorted(input_root.iterdir()):

        if not campaign_dir.is_dir(): continue
        measures_dir = campaign_dir / measures_name

        if not measures_dir.is_dir(): continue

        filter_campaign = getattr(config.discovery,"filter_campaign",None)

        if filter_campaign and campaign_dir.name != filter_campaign: continue

        yield(campaign_dir.name,measures_dir,campaign_dir / results_name)

def discover_manual_sources(config) -> list[MeasurementSource]:

    sources = []
    filter_point = getattr(config.discovery, "filter_point", None)
    filter_device = getattr(config.discovery, "filter_device", None)

    supported_devices = ("audiomoth","sonometer")

    for campaign_name, measures_dir, results_dir in _iter_manual_campaign_roots(config):
        for point_dir in sorted(measures_dir.iterdir()):

            if not point_dir.is_dir(): continue
            if filter_point and point_dir.name != filter_point: continue

            for device_type in supported_devices:
                device_config = getattr(config.devices, device_type, None)

                if device_config is None: continue
                if filter_device and filter_device != device_type: continue

                device_dir = point_dir / device_config.folder_name

                if not device_dir.is_dir(): continue

                sources.append(
                    MeasurementSource(
                        name = point_dir.name,
                        source_id=_build_source_id(point_dir.name,device_type),
                        campaign_name=campaign_name,
                        root_path=point_dir,
                        device_type=device_type,
                        raw_data_path=device_dir,
                        output_path=results_dir/point_dir.name,
                        needs_spl=device_config.default_needs_spl,
                        needs_ai=device_config.default_needs_ai,
                        needs_visualization=device_config.default_visualize 
                    )
                    )
    return sources

def discover_flat_measurement_points(config) -> list[MeasurementSource]:

    if config.execution.profile == 'manual': return 

    points: list[MeasurementSource] = []

    input_root = Path(config.campaign.input_root)
    output_root = Path(config.campaign.output_root)

    
    if not input_root.exists(): raise FileNotFoundError(f"No existe input_root {input_root}")
        
    filter_point = getattr(config.discovery, "filter_point", None)
    filter_device = getattr(config.discovery, "filter_device", None)

    for point_root in sorted(input_root.iterdir()):

        if not point_root.is_dir(): continue
        if filter_point and point_root.name != filter_point: continue
        
        audiomoth_cfg = config.devices.audiomoth
        sonometer_cfg = config.devices.sonometer

        audiomoth_path = _find_existing_folder(point_root,audiomoth_cfg.folder_name)
        sonometer_path = _find_existing_folder(point_root,sonometer_cfg.folder_name)

        if audiomoth_path is not None and _device_allowed(filter_device,"audiomoth"):
                  
            points.append(
                
                    MeasurementSource(
                        name                    = point_root.name,
                        source_id               = _build_source_id(point_root.name,"audiomoth"),
                        campaign_name           = config.campaign.name,                   
                        root_path               = point_root,
                        device_type             = "audiomoth",
                        raw_data_path           = audiomoth_path,
                        output_path             = output_root / point_root.name,
                        needs_spl               = audiomoth_cfg.default_needs_spl,
                        needs_ai                = audiomoth_cfg.default_needs_ai,
                        needs_visualization     = audiomoth_cfg.default_visualize
                    )
                )
            
        if sonometer_path is not None and _device_allowed(filter_device,"sonometer"):
                 
            points.append(

                    MeasurementSource(
                        name                    = point_root.name,
                        source_id               = _build_source_id(point_root.name,"sonometer"),
                        campaign_name           = config.campaign.name,
                        root_path               = point_root,
                        device_type             = "sonometer",
                        raw_data_path           = sonometer_path,
                        output_path             = Path(config.campaign.output_root) / point_root.name,
                        needs_spl               = sonometer_cfg.default_needs_spl,
                        needs_ai                = sonometer_cfg.default_needs_ai,
                        needs_visualization     = sonometer_cfg.default_visualize
                    )
                )
            

    return points


def discover_measurement_points(config) -> list[MeasurementSource]:

    if config.execution.profile == "manual": return discover_manual_sources(config)
    return discover_flat_measurement_points(config)