import os
import shutil
import tqdm
import pandas as pd


def make_json_audio_directory(path: str, logger):
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
    audiomoth_metadata_dir = os.path.join(current_directory, f"PREPROCESSING")
    os.makedirs(audiomoth_metadata_dir, exist_ok=True)
    logger.info(f"make PREPROCESSING folder at: {audiomoth_metadata_dir}")

    # make a directory for the json files
    json_directory = os.path.join(audiomoth_metadata_dir, f"METADATA")
    os.makedirs(json_directory, exist_ok=True)
    logger.info(f"make METADATA folder at: {json_directory}")

    # make a directory for the txt files
    txt_directory = os.path.join(audiomoth_metadata_dir, f"AUDIOMOTH")
    os.makedirs(txt_directory, exist_ok=True)
    logger.info(f"make AUDIOMOTH_CLEAN folder at: {txt_directory}")

    return json_directory, txt_directory, location_name



def copy_valid_audio_files_with_metadata(path: str, audio_directory: str, valid_audio_files: list, logger):
    # copy valid audio files to a new folder along with their metadata
    logger.info(f"\n\nCopying valid audio files to {audio_directory} along with metadata")

    print(f"\nCopying valid audio files to {audio_directory}")
    for file in tqdm.tqdm(valid_audio_files):
        logger.info(f"Copying {file} with metadata...")

        try:
            shutil.copy2(os.path.join(path, file), audio_directory)
            logger.info(f"{file} copied to {audio_directory} with metadata")

        except Exception as e:
            logger.error(f"Error: {e}")



def df_results(metadata: dict, metadata_result_path: str, location: str, logger):
    """
    Plotting the results
    """
    matadata_folder = "METADATA"

    # remove the last folder from the path
    metadata_result_path = os.path.dirname(metadata_result_path)

    # get the path of the metadata folder
    metadata_folder_path = os.path.join(metadata_result_path, matadata_folder)

    # create a df
    df = pd.DataFrame.from_dict(metadata, orient='index')

    # convert 'date_UTC1' to datetime
    df['date_UTC1'] = pd.to_datetime(df['date_UTC1'])
    
    # set index to 'date_UTC1'
    df.set_index('date_UTC1', inplace=True)
    
    # sort the index
    df.sort_index(inplace=True)

    # save the df to a csv file
    df.to_csv(f"{metadata_folder_path}/{location}_metadata_clean.csv")
    logger.info(f"\n{location}_metadata_clean.csv saved in {metadata_folder_path}")

    return df, metadata_folder_path