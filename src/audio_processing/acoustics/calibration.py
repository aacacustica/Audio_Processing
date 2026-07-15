from pathlib import Path

import configparser
import logging
import yaml

def read_calibration_constants(path: str | Path) -> dict[str,float]:

    path = Path(path)

    with path.open("r",encoding='utf-8') as file: data = yaml.safe_load(file) or {}

    constants = data.get("calibration_constants",{})

    result: dict[str,float] = {}

    for device_id,device_data in constants.items(): result[device_id.lower()] = float(device_data['calibration_db'])

    return result