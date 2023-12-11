from test_metadata_integrity import *
from config import *

# TESTING INTEGRITY

# [2.1] calibration check (if calibration is empty, it is BAD)
def test_calibration(file_metadata: str, file_name: str, logger):
    calibration = file_metadata["calibration"]
    # if calibration is empty, it is BAD
    if calibration == "" or calibration == None:
        logger.error(f"Calibration is empty in {file_name}")
        calibration = "BAD"
        return calibration
    else:
        logger.info(f"Calibration is {calibration} in {file_name}")
        return calibration

# [2.2] file size
def test_file_size(file_metadata: str, file_name: str, logger):
    file_size = file_metadata["file_size"]
    
    # logger.info(FILE_SIZE)
    # logger.info(type(FILE_SIZE))
    # logger.info(file_size)
    # logger.info(type(file_size))

    # if file size is empty or less than 29.0, it is BAD
    if file_metadata["sample_rate"] == "16000":
        if file_size is None or file_size == "":
            logger.error(f"File size is missing or empty in {file_name}")
            return "BAD"
        # Check if file size is less than the minimum acceptable size
        if float(file_size) < FILE_SIZE_16:
            logger.error(f"File size is too small ({file_size}) in {file_name}")
            return "BAD"
        else:
            logger.info(f"File size is acceptable ({file_size}) in {file_name}")
            return file_size

    elif file_metadata["sample_rate"] == "32000":
        if file_size is None or file_size == "":
            logger.error(f"File size is missing or empty in {file_name}")
            return "BAD"
        # Check if file size is less than the minimum acceptable size
        if float(file_size) < FILE_SIZE_32:
            logger.error(f"File size is too small ({file_size}) in {file_name}")
            return "BAD"
        else:
            logger.info(f"File size is acceptable ({file_size}) in {file_name}")
            return file_size


# [2.3] date and time zone
def test_time_zone(file_metadata: str, file_name: str, logger):
    utc1 = file_metadata["original_UTC"]

    if utc1 == "+0100":
        logger.info(f"UTC time zone set to {utc1}")
        return utc1
    else:
        logger.warning(f"UTC time zone wrong: {utc1}")
        return utc1

# [2.4] channels
def test_channels(file_metadata: str, file_name: str, logger):
    channels = file_metadata["channels"]

    if channels == 1:
        logger.info(f"Channels properly setup to {channels}")
        return channels
    else:
        logger.warning(f"Channel wrong setup to {channels}")
        return channels

# [2.5] sample rate
def test_sample_rate(file_metadata: str, file_name: str, logger):
    sample_rate = file_metadata["sample_rate"]

    if sample_rate == 16000:
        logger.info(f"Channels properly setup to {sample_rate}")
        return sample_rate
    elif sample_rate == 32000:
        logger.info(f"Channels properly setup to {sample_rate}")
        return sample_rate
    else:
        logger.warning(f"Channel wrong setup to {sample_rate}")
        return sample_rate

# [2.6] baterry status
def test_battery(file_metadata: str, file_name: str, logger):
    test_battery = file_metadata["battery_v"]
    pass

# [2.7] gain
def test_gain(file_metadata: str, file_name: str, logger):
    pass

# [2.8] duration
def test_duration(file_metadata: str, file_name: str, logger):
    pass

# [2.9] temperature
def test_temperature(file_metadata: str, file_name: str, logger):
    pass