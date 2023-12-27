import os
import shutil
import tqdm


def make_json_audio_directory(path: str, logger):
    test = "_test"
    # current directory less the last folder
    logger.info(f"Analyzing: {path}")
    
    current_directory = os.path.abspath(path).split("\\")[:-1]
    if current_directory == []:
        current_directory = os.path.abspath(path).split("/")[:-1]

    logger.info(f"Current directory: {current_directory}")
    
    # get the location name
    location_name = current_directory[-1]
    logger.info(f"Location name: {location_name}")
    
    current_directory = "/".join(current_directory)
    logger.info(f"make current dir at: {current_directory}")
    
    # make a directory for the json files
    audiomoth_metadata_dir = os.path.join(current_directory, f"METADATA{test}")
    os.makedirs(audiomoth_metadata_dir, exist_ok=True)
    logger.info(f"make audiomoth_metadata_dir at: {audiomoth_metadata_dir}")

    # make a directory for the json files
    json_directory = os.path.join(audiomoth_metadata_dir, f"JSON{test}")
    os.makedirs(json_directory, exist_ok=True)
    logger.info(f"make JSON_{test} folder at: {json_directory}")

    # make a directory for the txt files
    txt_directory = os.path.join(audiomoth_metadata_dir, f"AUDIOMOTH_CLEAN{test}")
    os.makedirs(txt_directory, exist_ok=True)
    logger.info(f"make TXT{test} folder at: {txt_directory}")

    return json_directory, txt_directory, location_name

def copy_valid_audio_files(path: str, audio_directory: str, valid_audio_files: list, logger):
    # copy valid audio files to a new folder
    for file in tqdm.tqdm(valid_audio_files):
        logger.info(f"Copying {file}...")
        try:
            shutil.copy(os.path.join(path, file), audio_directory)
            logger.info(f"{file} copied to {audio_directory}")
        except Exception as e:
            logger.error(f"Error: {e}")