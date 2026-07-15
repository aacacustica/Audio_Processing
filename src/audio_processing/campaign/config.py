from dataclasses import dataclass
from pathlib import Path
from typing import Any
from types import SimpleNamespace
import yaml


REQUIRED_TOP_LEVEL_KEYS = {
    "campaign",
    "execution",
    "discovery",
    "devices",
    "spl",
    "ai",
    "visualization",
    "points"
}

def validate_config(config) -> None:

    for key in REQUIRED_TOP_LEVEL_KEYS: 
        if not hasattr(config,key): raise ValueError(f"Falta la sección obligatoria {key} en campaign.yaml")
    
    input_root = Path(config.campaign.input_root)

    if not input_root.exists(): raise FileNotFoundError(f"No existe campaign.input_root: {input_root}")
    if not hasattr(config.devices,"audiomoth"): raise ValueError(f"Falta devices.audiomoth en la campaign.yaml")
    if not hasattr(config.devices,"sonometer"): raise ValueError(f"Falta devices.sonometer en la campaign.yaml")

        

@dataclass
class AppConfig:
    raw: dict[str, Any]

def _to_namespace(value: Any) -> Any:
    if isinstance(value, dict):
        return SimpleNamespace(
            **{
                key: _to_namespace(item)
                for key, item in value.items()
            }
        )

    if isinstance(value, list):
        return [
            _to_namespace(item)
            for item in value
        ]

    return value

def load_config(path: str | Path) -> AppConfig:
    path = Path(path)

    with path.open("r",encoding="utf-8") as file:
        data = yaml.safe_load(file)

    if data is None:
        raise ValueError(f"El archivo de configuración está vacío: {path}")
    
    config = _to_namespace(data)
    validate_config(config)

    return config