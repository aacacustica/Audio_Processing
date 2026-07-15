import configparser
import logging


def read_calibration_constants(ini_file):
    config = configparser.ConfigParser()
    config.read(ini_file)
    logging.info(f"Reading calibration constants from {ini_file}")
    return {key: float(value) for key, value in config['CalibrationConstants'].items()}