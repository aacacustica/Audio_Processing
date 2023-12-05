
import configparser

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

def test_time_zone():
    pass

def test_channels(logger,metadata: dict):
    channels = metadata["channels"]
    logger.debu(channels)
    pass

def test_batery_status():
    pass

def test_sample_rate(logger, metadata: dict):
    sample_rate = metadata["sample_rate"]
    logger.debug(sample_rate)
    pass

def test_gain():
    pass

def test_recording_duration():
    pass

def test_sleep_duration():
    pass

def get_first_timestamp():
    pass

def get_last_timestamp():
    pass

def get_duration():
    pass