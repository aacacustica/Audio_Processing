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
    logger.info(metadata)

    # [0] initialize the txt file
    txt_name = f"test_integrity_{location}.txt"

    # [0] initialize valid audio file list
    valid_audio_files = []
    total_audio_files = len(metadata)

    # [1] go through the metadata
    for file_name, file_metadata in metadata.items():
        logger.info(f"Testing audio file {file_name}")

        # TESTING INTEGRITY

        # [2.1] calibration check (if calibration is empty, it is BAD)
        calibration = test_calibration(file_metadata, file_name, logger)

        # [2.2] file size
        file_size = test_file_size(file_metadata, file_name, logger)

        # [2.4] channels
        time_zone = test_time_zone(file_metadata, file_name, logger)

        # [2.5] channels
        channels = test_channels(file_metadata, file_name, logger)

        # [2.6] sample rate
        sample_rate = test_sample_rate(file_metadata, file_name, logger)

        # [2.7] baterry status
        battery_status = test_battery(file_metadata, file_name, logger)

        # [2.8] gain
        gain = test_gain(file_metadata, file_name, logger)

        # [2.9] duration
        duration = test_duration(file_metadata, file_name, logger)

        # [2.10] temperature
        temperature = test_temperature(file_metadata, file_name, logger)

        # [2.10] check if the audio file is valid
        if calibration == "BAD" or file_size == "BAD" or time_zone == "BAD" or channels == "BAD" or sample_rate == "BAD" or battery_status == "BAD" or gain == "BAD" or duration == "BAD" or temperature == "BAD":
            logger.warning(f"Audio file {file_name} is not valid")
        else:
            logger.info(f"Audio file {file_name} is valid")
            valid_audio_files.append(file_name)
    
    logger.info(f"Total audio files: {total_audio_files}")
    logger.info(f"Valid audio files: {len(valid_audio_files)}")

    
    return valid_audio_files