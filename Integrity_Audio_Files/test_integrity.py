
import configparser
from config import *

def get_comment_section(metadata: dict):
    tag = metadata["TAG"]
    comment = tag["comment"]
    comment = comment.split(" ")
    return comment

def test_name_calibration(metadata: dict, logger, calibration_file='calibration_constants.ini'):
    """
    Look for the name of the calibration file in the metadata.
    If it exists, map its calibration constant
    
    Args:
        metadata (dict): Dictionary with the metadata of the file or files.

    """
    tag = metadata["TAG"]
    filename = tag["artist"].split(" ")[1]

    config = configparser.ConfigParser()
    config.read(calibration_file)
    calibration_dict = {k.upper() : v for k, v in config['CalibrationConstants'].items()}

    if filename in calibration_dict:
        logger.debug(f"For {filename}, the calibration constants is {calibration_dict[filename]}")
    else:
        logger.warning(f"For {filename}, there is no calibration constant")



def test_time_zone(metadata: dict, logger):
    """Get the time zone from the metadata."""
    comment = get_comment_section(metadata)

    if comment[4] == "(UTC +1)":
        logger.debug("Time zone is properly set to UTC +1")
    else:
        logger.warning(f"Time zone is not properly set to UTC +1 -> [ {comment[4]} ]") 


def test_channels(metadata: dict, logger):
    """Get the number of channels from the metadata."""
    channels = metadata["channels"]
    
    if channels == 1:
        logger.debug("Number of channels is properly set to 1")
    else:
        logger.debug(f"Number of channels set to {channels}, not to 1")

def test_batery_status(metadata: dict, logger):
    """Get the battery status from the metadata."""
    comment = get_comment_section(metadata)
    comment_float = float(comment[14][:-1])

    if comment_float < 5.0 and comment_float > 0.0:
        logger.debug(f"Battery status is okay: {comment_float}V")
    else:
        logger.warning(f"Battery status is not ok {comment_float}V")


def test_sample_rate(metadata: dict, logger):
    """Get the sample rate from the metadata."""
    sample_rate = metadata["sample_rate"]
    
    if sample_rate == SAMPLE_RATE:
        logger.debug(f"Sample rate is properly set to {sample_rate}")
    else:
        logger.warning(f"Sample rate is not set to {SAMPLE_RATE}, but to {sample_rate}")


def test_gain(metadata: dict, logger):
    """Get the gain from the metadata."""
    comment = get_comment_section(metadata)
    gain = comment[9]
    if gain == GAIN:
        logger.debug(f"Gain is properly set to {gain}")
    else:
        logger.warning(f"Gain is not set to {GAIN}, but to {gain}")


def test_recording_duration(metadata: dict, logger):
    duration = metadata["duration"]
    duration = round(float(duration), 2)
    # round duration

    if duration == RECORDING_DURATION:
        logger.debug(f"Recording duration is properly set to {duration}s")
    else:
        logger.warning(f"Recording duration is not properly set to {RECORDING_DURATION}s, but to {duration}s")

def test_sleep_duration(logger,metadata: dict):
    pass

def get_first_timestamp(logger,metadata: dict):
    pass

def get_last_timestamp(logger,metadata: dict):
    pass