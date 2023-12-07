from test_metadata_integrity import *

# TESTING INTEGRITY

def calibration_test():
# [2.1] calibration check (if calibration is empty, it is BAD)
calibration = file_metadata.get('calibration', None)
if not calibration:
    logger.error(f"{file_name} - Missing or empty calibration value")

# [2.2] file size

# [2.3] date and time zone

# [2.4] channels

# [2.5] sample rate

# [2.6] baterry status

# [2.7] gain

# [2.8] duration

# [2.9] temperature