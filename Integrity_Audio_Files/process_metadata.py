from pydub.utils import mediainfo
import os
import tqdm
# import argparse
from test_integrity import *

def get_metadata(path: str, logger):
    """Returns a dictionary with the metadata of the file or files in the path.
    Args: 
        path (str): Path to the file or folder.
    Returns:
        metadata_dict (dict): Dictionary with the metadata of the file or files.
    """
    # if path exists
    if not os.path.exists(path):
        raise Exception("Path does not exist.")
    
    # if path is a file or a folder
    if os.path.isdir(path):
        metadata_dict = {}

        # STORE METADTA

    
        # for files in folder
        for file in tqdm.tqdm(os.listdir(path)):
            full_path = os.path.join(path, file)
            if os.path.isfile(full_path):
    
                try:
                    # metadata
                    metadata = mediainfo(full_path)
                    # metadata_dict[file] = metadata
                    for k, v in metadata.items():
                        print(f"{k}: {v}")

                    # testing integrity
                    # [1] calibration
                    filename, file_calibration = test_name_calibration(metadata, logger)

                    # [2] test channels
                    channels = test_channels(metadata, logger)

                    # [3] test sample rate
                    sample_rate = test_sample_rate(metadata, logger)

                    # [4] test time zone
                    time_zone_metadata = test_time_zone(metadata, logger)

                    # [5] test battery status
                    battery_voltage = test_batery_status(metadata, logger)

                    # [6] test gain
                    gain = test_gain(metadata, logger)

                    # [7] test recording duration
                    duration = test_recording_duration(metadata, logger)

                    # [8] test temperature
                    temperature = test_temperature(metadata, logger)

                    # [9] test timestamp
                    timestamp = test_timestamp(metadata, logger)
                
                except Exception as e:
                    print(f"Error processing file {file}: {e}")
    
        return metadata_dict
    
    else:
        try:
            # metadata
            metadata = mediainfo(path)

            # testing integrity
            # [1] calibration
            test_name_calibration(metadata, logger)

            # [2] test channels
            test_channels(metadata, logger)

            # [3] test sample rate
            test_sample_rate(metadata, logger)

            # [4] test time zone
            test_time_zone(metadata, logger)

            # [5] test battery status
            test_batery_status(metadata, logger)

            # [6] test gain
            test_gain(metadata, logger)

            # [7] test recording duration
            test_recording_duration(metadata, logger)
            
        
        except Exception as e:
            raise Exception(f"Error processing file: {e}")
        