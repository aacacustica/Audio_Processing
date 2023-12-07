
import configparser
from config import *

def get_comment_section(metadata: dict):
    tag = metadata["TAG"]
    comment = tag["comment"]
    comment = comment.split(" ")
    return comment


def get_name_calibration(metadata: dict, logger, calibration_file='calibration_constants.ini'):
    """
    Look for the name of the calibration file in the metadata.
    If it exists, map its calibration constant
    
    Args:
        metadata (dict): Dictionary with the metadata of the file or files.

    """
    tag = metadata["TAG"]
    filename = metadata["filename"].split("/")[-1]
    audiomoth_name = tag["artist"].split(" ")[1]

    logger.info(f"Filename is {filename}")
    logger.info(f"AudioMoth name is {audiomoth_name}")

    config = configparser.ConfigParser()
    config.read(calibration_file)
    calibration_dict = {k.upper() : v for k, v in config['CalibrationConstants'].items()}
    file_calibration = calibration_dict.get(audiomoth_name, None)
    
    return filename, audiomoth_name, file_calibration


def get_channels(metadata: dict, logger):
    """Get the number of channels from the metadata."""
    channels = metadata["channels"]
    channels = int(channels)

    return channels


def get_sample_rate(metadata: dict, logger):
    """Get the sample rate from the metadata."""
    sample_rate = metadata["sample_rate"]

    return sample_rate


def get_time_zone(metadata: dict, logger):
    """Get the time zone from the metadata.
    desired time zone (UTC +1)
    """
    comment = get_comment_section(metadata)
    time_zone_metadata = comment[4]

    return time_zone_metadata


def get_batery_status(metadata: dict, logger):
    """Get the battery status from the metadata.
     3.5 V; battery voltage too low to reliably record.
     """
    comment = get_comment_section(metadata)
    battery_voltage = float(comment[14][:-1])

    return battery_voltage

def get_gain(metadata: dict, logger):
    """Get the gain from the metadata."""
    comment = get_comment_section(metadata)
    gain = comment[9]

    return gain

def get_recording_duration(metadata: dict, logger):
    duration = metadata["duration"]
    duration = round(float(duration), 2)

    return duration

def get_temperature(metadata: dict, logger):
    """Get the temperature from the metadata
    there is no temperature range in the configuration guide
    """
    comment = get_comment_section(metadata)
    temperature = comment[-1].split("C")[0]
    temperature = float(temperature)

    return temperature

def get_timestamp(metadata: dict, logger):
    """Get the timestamp from the metadata"""
    comment = get_comment_section(metadata)
    timestamp = comment[2:4]
    
    return timestamp
