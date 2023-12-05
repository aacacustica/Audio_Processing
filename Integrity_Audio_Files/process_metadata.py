from pydub.utils import mediainfo
import os
import tqdm
# import argparse
from test_integrity import *
import subprocess

def get_metadata(path: str, logger):
    """Returns a dictionary with the metadata of the file or files in the path."""
    integrity_dict = {}

    if not os.path.exists(path):
        raise Exception("Path does not exist.")

    # if it is a dir
    if os.path.isdir(path):
        for file in tqdm.tqdm(os.listdir(path)):
            # get the full path
            full_path = os.path.join(path, file)
            # check if it is a file
            if os.path.isfile(full_path):
                try:
                    # setting ExifTool
                    result = subprocess.run(['exiftool', full_path], stdout=subprocess.PIPE, text=True)
                    metadata = result.stdout
        
                    parsed_metadata = {}
                    for line in metadata.split('\n'):
                        if ': ' in line:
                            key, value = line.split(': ', 1)
                            parsed_metadata[key.strip()] = value.strip()

                    print(parsed_metadata)
                
                except Exception as e:
                    print(f"Error processing file {file}: {e}")
                #     # getting metadata
                #     metadata = mediainfo(full_path)
                #     # for k, v in metadata.items():
                #     #     print(f"{k}: {v}")

                #     # testing integrity
                #     # [1] calibration
                #     filename, audiomoth_name, file_calibration = test_name_calibration(metadata, logger)
                #     # [2] test channels
                #     channels = test_channels(metadata, logger)
                #     # [3] test sample rate
                #     sample_rate = test_sample_rate(metadata, logger)
                #     # [4] test time zone
                #     time_zone_metadata = test_time_zone(metadata, logger)
                #     # [5] test battery status
                #     battery_voltage = test_batery_status(metadata, logger)
                #     # [6] test gain
                #     gain = test_gain(metadata, logger)
                #     # [7] test recording duration
                #     duration = test_recording_duration(metadata, logger)
                #     # [8] test temperature
                #     temperature = test_temperature(metadata, logger)
                #     # [9] test timestamp
                #     timestamp = test_timestamp(metadata, logger)

                #     # save the metadata in a dictionary
                #     integrity = {
                #         "filename": filename,
                #         "audiomoth_name": audiomoth_name,
                #         "file_calibration": file_calibration,
                #         "channels": channels,
                #         "sample_rate": sample_rate,
                #         "time_zone_metadata": time_zone_metadata,
                #         "battery_voltage": battery_voltage,
                #         "gain": gain,
                #         "duration": duration,
                #         "temperature": temperature,
                #         "timestamp": timestamp
                #     }
                #     # save the dictionary
                #     integrity_dict[file] = integrity
                
                # except Exception as e:
                #     print(f"Error processing file {file}: {e}")
        return integrity_dict
    
    else:
        try:
            # metadata
            metadata = mediainfo(path)
            # for k, v in metadata.items():
            #     print(f"{k}: {v}")

            # testing integrity
            # [1] calibration
            filename, audiomoth_name, file_calibration = test_name_calibration(metadata, logger)
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

            # save the metadata in a dictionary
            integrity = {
                "filename": filename,
                "audiomoth_name": audiomoth_name,
                "file_calibration": file_calibration,
                "channels": channels,
                "sample_rate": sample_rate,
                "time_zone_metadata": time_zone_metadata,
                "battery_voltage": battery_voltage,
                "gain": gain,
                "duration": duration,
                "temperature": temperature,
                "timestamp": timestamp
            }
            # save the dictionary
            integrity_dict[file] = integrity
        
        except Exception as e:
            print(f"Error processing file {file}: {e}")
    return integrity_dict