def test_integrity(metadata: dict, logger):
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