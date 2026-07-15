from dataclasses import dataclass
from pathlib import Path
from typing import Any
from types import SimpleNamespace
import yaml

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

    return _to_namespace(data)