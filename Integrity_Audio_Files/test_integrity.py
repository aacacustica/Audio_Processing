
import configparser

def test_name_calibration(metadata: dict, calibration_file='calibration_constants.ini'):
    """
    Look for the name of the calibration file in the metadata.
    If it exists, map its calibration constant
    
    Args:
        metadata (dict): Dictionary with the metadata of the file or files.

    """
    tag = metadata["TAG"]
    print("\nTAG METADATA:")
    print(tag)
    print()

    filename = tag["artist"].split(" ")[1]
    print(f"\nThis is the artist tag of the file: {filename}")

    config = configparser.ConfigParser()
    config.read(calibration_file)
    calibration_dict = {k.upper() : v for k, v in config['CalibrationConstants'].items()}
    print(f"\nName of AudioMoths: {calibration_dict}")

    if filename in calibration_dict:
        print(f"\nFor {filename}, the calibration constants is {calibration_dict[filename]}")
    else:
        raise Exception(f"\n{filename} is not in the calibration constants file.")

def test_time_zone():
    pass

def test_channels(metadata: dict):
    channels = metadata["channels"]
    print(channels)
    pass

def test_batery_status():
    pass

def test_sample_rate(metadata: dict):
    sample_rate = metadata["sample_rate"]
    print(sample_rate)
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