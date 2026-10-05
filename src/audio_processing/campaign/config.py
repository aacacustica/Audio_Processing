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
    "peaks",
    "visualization",
    "alarms",
    "points",
    "outputs",
    "database",
    "profiles"
    
}

DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parents[3]
    / "configs"
    / "campaign.example.yaml"
)

def validate_config(config) -> None:

    for key in REQUIRED_TOP_LEVEL_KEYS: 
        if not hasattr(config,key): raise ValueError(f"Falta la sección obligatoria {key} en campaign.yaml")
    
    input_root = Path(config.campaign.input_root)

    if not input_root.exists(): raise FileNotFoundError(f"No existe campaign.input_root: {input_root}")
    if not hasattr(config.devices,"audiomoth"): raise ValueError(f"Falta devices.audiomoth en la campaign.yaml")
    if not hasattr(config.devices,"sonometer"): raise ValueError(f"Falta devices.sonometer en la campaign.yaml")


def _to_namespace(value: Any) -> Any:

    if isinstance(value,dict): return SimpleNamespace(**{key: _to_namespace(item) for key,item in value.items()})
    if isinstance(value,list): return [_to_namespace(item) for item in value]

    return value

def _resolve_relative_path(base_dir,value):

    path = Path(value)

    if path.is_absolute(): return path

    return base_dir / path

def resolve_profile(config,profile_name: str | None = None):

    selected = (profile_name or config.execution.profile)

    if not hasattr(config.profiles,selected): raise ValueError(f"Perfil desconocido: {selected}")

    profile = getattr(config.profiles,selected)

    required_flags = ("run_spl","run_ai","run_peaks","run_alarms","run_basic_visualization","run_advanced_visualization")

    for flag in required_flags: 
        if not hasattr(profile,flag): raise ValueError(f"Falta profiles.{selected}.{flag}")

    config.runtime = profile
    config.execution.profile = selected

    return config


def load_config(path: str | Path = DEFAULT_CONFIG_PATH, profile_name: str | None = None):

    path = Path(path)

    with path.open("r",encoding="utf-8") as file: data = yaml.safe_load(file)

    if data is None: 
        raise ValueError(f"El archivo de configuración está vacío: {path}")

    config = _to_namespace(data)
    validate_config(config)

    config._config_path = path
    config._config_dir = path.parent

    return resolve_profile(config,profile_name)