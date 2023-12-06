from pydub.utils import mediainfo
import os
import tqdm
# import argparse
# from test_integrity import *
from test_integrity_exiftool import *
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
                            # logger.info(f"{key}: {value}")

                    # TESTING INTEGRITY
                    # [1] filename, audiomoth_name and calibration
                    file_name, audiomoth_name, calibration = test_name_calibration(parsed_metadata, logger)
                    # [2] test file size
                    file_size = test_file_size(parsed_metadata, logger)
                    # [3] date
                    date, original_time_zone = test_timestamp(parsed_metadata, logger)
                    # [4] channels
                    channels = test_channels(parsed_metadata, logger)
                    # [5] sample rate
                    sample_rate = test_sample_rate(parsed_metadata, logger)
                    # [6] baterry status
                    battery_voltage = test_batery_status(parsed_metadata, logger)
                    # [7] gain
                    gain = test_gain(parsed_metadata, logger)
                    # [8] duration
                    duration = test_recording_duration(parsed_metadata, logger)
                    # [9] temperature
                    temperature = test_temperature(parsed_metadata, logger)

                    # save the metadata in a dictionary
                    integrity = {
                        "file_name": file_name,
                        "audiomoth_name": audiomoth_name,
                        "calibration": calibration,
                        "file_size": file_size,
                        "date_UTC1": date,
                        "original_UTC": original_time_zone,
                        "channels": channels,
                        "sample_rate": sample_rate,
                        "battery_v": battery_voltage,
                        "gain": gain,
                        "duration": duration,
                        "temperature": temperature
                    }
                    # save the dictionary
                    integrity_dict[file] = integrity

                except Exception as e:
                    print(f"Error processing file {file}: {e}")
        return integrity_dict
    
    else:
        try:
            # setting ExifTool
            result = subprocess.run(['exiftool', path], stdout=subprocess.PIPE, text=True)
            metadata = result.stdout

            parsed_metadata = {}
            for line in metadata.split('\n'):
                if ': ' in line:
                    key, value = line.split(': ', 1)
                    parsed_metadata[key.strip()] = value.strip()
                    # logger.info(f"{key}: {value}")

            # TESTING INTEGRITY
            # [1] filename, audiomoth_name and calibration
            file_name, audiomoth_name, calibration = test_name_calibration(parsed_metadata, logger)
            # [2] test file size
            file_size = test_file_size(parsed_metadata, logger)
            # [3] date
            date, original_time_zone = test_timestamp(parsed_metadata, logger)
            # [4] channels
            channels = test_channels(parsed_metadata, logger)
            # [5] sample rate
            sample_rate = test_sample_rate(parsed_metadata, logger)
            # [6] baterry status
            battery_voltage = test_batery_status(parsed_metadata, logger)
            # [7] gain
            gain = test_gain(parsed_metadata, logger)
            # [8] duration
            duration = test_recording_duration(parsed_metadata, logger)
            # [9] temperature
            temperature = test_temperature(parsed_metadata, logger)

            # save the metadata in a dictionary
            integrity = {
                "file_name": file_name,
                "audiomoth_name": audiomoth_name,
                "calibration": calibration,
                "file_size": file_size,
                "date_UTC1": date,
                "original_UTC": original_time_zone,
                "channels": channels,
                "sample_rate": sample_rate,
                "battery_v": battery_voltage,
                "gain": gain,
                "duration": duration,
                "temperature": temperature
            }
            # save the dictionary
            integrity_dict = integrity

        except Exception as e:
            print(f"Error processing file {file}: {e}")
    return integrity_dict