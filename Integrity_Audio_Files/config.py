"""

config file for SETTING CONSTANTS according to the AAC device configuration guide.
This is set right before setting up, manually, the AudioMoth device.

This file contains the following:

SAMPLE_RATE: int -- 32KHz
GAIN: str -- "LOW"
RECORDING_DURATION: int -- 900 seconds. 15 minutes for audio and 5 seconds of sleeps
SLEEP_DURATION: int -- 5 seconds

"""

# CONSTANTS
SAMPLE_RATE = 32000
GAIN = "LOW"
RECORDING_DURATION = 900 # seconds
SLEEP_DURATION = 5 # seconds