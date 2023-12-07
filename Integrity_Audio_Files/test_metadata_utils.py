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
        if float(file_size) < FILE_SIZE:
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
        if float(file_size) < FILE_SIZE:
            logger.error(f"File size is too small ({file_size}) in {file_name}")
            return "BAD"
        else:
            logger.info(f"File size is acceptable ({file_size}) in {file_name}")
            return file_size
# [2.3] date and time zone

# [2.4] channels

# [2.5] sample rate

# [2.6] baterry status

# [2.7] gain

# [2.8] duration

# [2.9] temperature