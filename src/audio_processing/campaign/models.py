from dataclasses import dataclass
from pathlib import Path
from typing import Literal



DeviceType = Literal[
    "audiomoth",
    "sonometer",
    "cesva",
    "sv307",
    "larson_814",
    "larson_824",
    "bruel_kjaer",
    "unknown"
]


@dataclass
class MeasurementPoint:
    name: str
    source_id: str
    root_path: Path
    device_type: DeviceType
    raw_data_path: Path
    output_path: Path
    needs_spl: bool
    needs_ai: bool
    needs_visualization: bool
    