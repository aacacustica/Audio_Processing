from pathlib import Path

import numpy as np

import configparser
import logging
import yaml
import datetime

from pyfilterbank.splweighting import a_weighting_coeffs_design,c_weighting_coeffs_design

def read_calibration_constants(path: str | Path) -> dict[str,float]:

    path = Path(path)

    with path.open("r",encoding='utf-8') as file: data = yaml.safe_load(file) or {}

    constants = data.get("calibration_constants",{})

    result: dict[str,float] = {}

    for device_id,device_data in constants.items(): result[device_id.lower()] = float(device_data['calibration_db'])

    return result


def get_db_level(x, C):
    """
    Args:
        x (numpy.ndarray): A multi-dimensional array of audio signal values.
        C (float): A calibration constant for the audio recording device.
        axis (int): The axis along which the means are computed. By default, it computes the mean over the last axis.

    Returns:
        numpy.ndarray or float: The Sound Pressure Level (SPL) of the given audio signal in decibels. If the input 'x' is a multi-dimensional array, then an array of SPL values is returned, otherwise a single float value is returned.

    """
    pref = 0.000002
    mean_square = np.mean(x ** 2)

    if mean_square <= 0: return -np.inf
    
    return 10 * np.log10(mean_square / pref ** 2) + C

def get_audiofiles(path: Path) -> list[Path]:

    return sorted(file for file in path.iterdir() if file.is_file() and file.suffix.lower() == '.wav')

def get_device_id(metadata) -> str:

    artists_tags = metadata.tags.get('artist',['songmeter'])

    if not artists_tags: return 'songmeter'

    parts = artists_tags[0].split(" ")

    if len(parts) < 2: return 'songmeter'

    return parts[1].lower()

def timestamp_from_filename(path: Path) -> datetime.datetime:

    return datetime.datetime.strptime(path.stem, "%Y%m%d_%H%M%S")

def design_a_weighting(fs):
    return a_weighting_coeffs_design(fs)

def design_c_weighting(fs):
    return c_weighting_coeffs_design(fs)