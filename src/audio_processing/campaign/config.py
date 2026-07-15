from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

@dataclass
class AppConfig:
    raw: dict[str, Any]

def load_config(path: str | Path) -> AppConfig:
    path = Path(path)

    with path.open("r",encoding="utf-8") as file:
        data = yaml.safe_load(file)

    return AppConfig(raw=data)