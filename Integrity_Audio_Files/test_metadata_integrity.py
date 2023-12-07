from test_metadata_integrity import *
from test_metadata_utils import *

def test_integrity(metadata: dict, location: str, logger):
    """Test the integrity of the metadata.
    We are goint to compare the metadata with the configuration guide.
    So, we have to check if the values from the metadata are the same as the values from the configuration guide.

    SAMPLE_RATE = 32000
    GAIN = "low"
    RECORDING_DURATION = 900 # seconds
    SLEEP_DURATION = 5 # seconds
    CHANNELS = 1
    BATERRY_VOLTAGE = 3.5 # V

    """
    # [0] initialize the txt file
    txt_name = f"test_integrity_{location}.txt"

    # [1] go through the metadata
    for file_name, file_metadata in metadata.items():
        logger.info(f"Testing audio file {file_name}")

        # TESTING INTEGRITY

        # [2.1] calibration check (if calibration is empty, it is BAD)
        calibration = test_calibration(file_metadata, file_name, logger)

        # [2.2] file size
        file_size = test_file_size(file_metadata, file_name, logger)

        # [2.3] date and time zone

        # [2.4] channels

        # [2.5] sample rate

        # [2.6] baterry status

        # [2.7] gain

        # [2.8] duration

        # [2.9] temperature

    # [3] save the results in a txt file
