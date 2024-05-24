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
# GENERAL 32000
SAMPLE_RATE = 32000
# TRAFFIC = 16000

# CALIBRATION

# GAIN
GAIN = "low"

# FILE SIZE
FILE_SIZE_16 = 29.0 # MB
FILE_SIZE_32 = 58.0 # MB

# TIME ANALYSIS
SLEEP_DURATION = 5 # seconds
DURATION = 900 # seconds
# to test the UTC time zone, it must not be empty: date_UTC1

# CHANNELS
CHANNELS = 1

# BATTERY
BATERRY_VOLTAGE = 3.5 # V

# TEMPERATURE
MAX_TEMP = 50 # C
MIN_TEMP = -10 # C