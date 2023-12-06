
from config import *
import configparser
from datetime import datetime
import pytz

def get_comment_section(metadata: dict):
    comment = metadata["Comment"]
    comment = comment.split(" ")
    return comment


def test_name_calibration(metadata: dict, logger, calibration_file='calibration_constants.ini'):
    """
    Look for the name of the calibration file in the metadata.
    If it exists, map its calibration constant
    
    Args:
        metadata (dict): Dictionary with the metadata of the file or files.

    """
    filename = metadata["File Name"]
    audiomoth_name = metadata["Artist"].split(" ")[1]

    logger.info(f"Filename is {filename}")
    logger.info(f"AudioMoth name is {audiomoth_name}")

    config = configparser.ConfigParser()
    config.read(calibration_file)

    calibration_dict = {k.upper() : v for k, v in config['CalibrationConstants'].items()}

    file_calibration = calibration_dict.get(audiomoth_name, None)
    
    # logger.info(f"Calibration constant is {file_calibration}")
    
    return filename, audiomoth_name, file_calibration


def test_file_size(metadata: dict, logger,):
    """Get the file size from the metadata in MB."""
    file_size = metadata["File Size"].split(" ")[0]
    file_size = float(file_size)
    
    # logger.info(f"File size is {file_size} MB")

    return file_size


def test_timestamp(metadata: dict, logger):
    """
    Getting the times from the metadata. it is in this format
    
    File Modification Date/Time     : 2021:05:28 13:16:54-04:00
    File Access Date/Time           : 2021:05:28 00:00:00-04:00
    File Inode Change Date/Time     : 2021:05:28 13:16:54-04:00

    the last two digits are the time zone
    """
    date = metadata["File Modification Date/Time"]
    # convert to datetime format
    date = datetime.strptime(date, "%Y:%m:%d %H:%M:%S%z")
    logger.info(f"Date is {date}")

    # Set timezone to UTC+1
    utc_plus_one = pytz.timezone('Etc/GMT-1')
    date = date.astimezone(utc_plus_one)

    # get the original time zone in the UTC+x format
    original_time_zone = date.strftime("%z")
    original_time_zone = "UTC " + original_time_zone
    logger.info(f"Original time zone is {original_time_zone}")
    
    logger.info(f"Date (UTC+1) is {date}")

    return date


def test_channels(metadata: dict, logger):
    """Get the number of channels from the metadata."""
    channels = metadata["Num Channels"]
    channels = int(channels)
    # logger.info(f"Number of channels is {channels}")

    return channels


def test_sample_rate(metadata: dict, logger):
    """Get the sample rate from the metadata."""
    sample_rate = metadata["Sample Rate"]

    # logger.info(f"Sample rate is {sample_rate}")

    return sample_rate


def test_batery_status(metadata: dict, logger):
    """Get the battery status from the metadata.
     3.5 V; battery voltage too low to reliably record.
     """
    comment = get_comment_section(metadata)
    battery_voltage = float(comment[14][:-1])

    # logger.info(f"Battery voltage is {battery_voltage}V")

    return battery_voltage


def test_gain(metadata: dict, logger):
    """Get the gain from the metadata."""
    comment = get_comment_section(metadata)
    gain = comment[9]

    # logger.info(f"Gain is {gain}")

    return gain


def test_recording_duration(metadata: dict, logger):
    """Get the recording duration from the metadata and convert it to seconds.
       The format is like this: 0:15:00 (hours:minutes:seconds)
    """
    h, m, s = metadata["Duration"].split(":")
    duration = int(h) * 3600 + int(m) * 60 + int(s)
    
    # logger.info(f"Duration in seconds is {duration}s")

    return duration


def test_temperature(metadata: dict, logger):
    """Get the temperature from the metadata
    there is no temperature range in the configuration guide
    """
    comment = get_comment_section(metadata)
    temperature = comment[-1].split("C")[0]
    temperature = float(temperature)

    # logger.info(f"Temperature is {temperature}C")

    return temperature
