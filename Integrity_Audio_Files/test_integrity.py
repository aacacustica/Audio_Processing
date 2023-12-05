
import configparser
from config import *

def get_comment_section(metadata: dict):
    tag = metadata["TAG"]
    comment = tag["comment"]
    comment = comment.split(" ")
    return comment

def test_name_calibration(logger, metadata: dict, calibration_file='calibration_constants.ini'):
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



def test_time_zone(logger, metadata: dict):
    """Get the time zone from the metadata."""
    comment = get_comment_section(metadata)

    if comment[4] == "(UTC +1)":
        logger.debug("Time zone is properly set to UTC +1")
    else:
        logger.warning(f"Time zone is not properly set to UTC +1 -> [ {comment[4]} ]") 


def test_channels(logger,metadata: dict):
    """Get the number of channels from the metadata."""
    channels = metadata["channels"]
    
    if channels == 1:
        logger.debug("Number of channels is properly set to 1")
    else:
        logger.debug(f"Number of channels set to {channels}, not to 1")

def test_batery_status(logger,metadata: dict):
    """Get the battery status from the metadata."""
    comment = get_comment_section(metadata)
    comment_float = float(comment[14][:-1])

    if comment_float < 5.0 and comment_float > 0.0:
        logger.debug(f"Battery status is okay: {comment_float}V")
    else:
        logger.warning(f"Battery status is not okay: {comment_float}V")


def test_sample_rate(logger, metadata: dict):
    """Get the sample rate from the metadata."""
    sample_rate = metadata["sample_rate"]
    
    if sample_rate == SAMPLE_RATE:
        logger.debug(f"Sample rate is properly set to {sample_rate}")
    else:
        logger.warning(f"Sample rate is not properly set to {SAMPLE_RATE}, but to {sample_rate}")


def test_gain(logger,metadata: dict):
    """Get the gain from the metadata."""
    comment = get_comment_section(metadata)
    gain = comment[9]
    if gain == GAIN:
        logger.debug(f"Gain is properly set to {gain}")
    else:
        logger.warning(f"Gain is not properly set to {GAIN}, but to {gain}")


def test_recording_duration(logger,metadata: dict):
    pass

def test_sleep_duration(logger,metadata: dict):
    pass

def get_first_timestamp(logger,metadata: dict):
    pass

def get_last_timestamp(logger,metadata: dict):
    pass

def get_duration():
    pass